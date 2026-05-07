-- ── profiles ──────────────────────────────────────────────────────────────────
-- Mirrors minimal data from auth.users; created on first sign-in via trigger.
create table profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  display_name text,
  email text not null,
  chesscom_username text,
  lichess_username text,
  stripe_customer_id text,
  subscription_status text not null default 'free',
  -- 'free' | 'trialing' | 'active' | 'past_due' | 'canceled'
  trial_ends_at timestamptz,
  timezone text not null default 'UTC',
  created_at timestamptz not null default now()
);

create index profiles_chesscom on profiles(chesscom_username) where chesscom_username is not null;
create index profiles_lichess  on profiles(lichess_username)  where lichess_username  is not null;

-- Auto-create profile on sign-up
create or replace function handle_new_user()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  insert into public.profiles (id, email)
  values (new.id, new.email);
  return new;
end;
$$;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure handle_new_user();


-- ── games ──────────────────────────────────────────────────────────────────────
create table games (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references profiles(id) on delete cascade,
  source text not null check (source in ('chesscom', 'lichess', 'pgn_upload')),
  external_id text,
  played_at timestamptz not null,
  time_control text not null,
  result text not null check (result in ('1-0', '0-1', '1/2-1/2')),
  user_color text not null check (user_color in ('white', 'black')),
  user_rating int,
  opponent_rating int,
  eco_code text,
  opening_name text,
  pgn text not null,
  headers jsonb not null default '{}',
  ingested_at timestamptz not null default now(),
  analyzed_at timestamptz,
  unique (user_id, source, external_id)
);

create index games_user_played on games(user_id, played_at desc);
create index games_user_eco    on games(user_id, eco_code);


-- ── position_evals — globally shared across all users ─────────────────────────
create table position_evals (
  fen_hash text primary key,
  fen text not null,
  depth int not null,
  eval_cp int,
  mate_in int,
  best_move text not null,
  best_line text not null,
  second_best_move text,
  second_best_eval_cp int,
  second_best_mate_in int,
  computed_at timestamptz not null default now()
);


-- ── mistakes ───────────────────────────────────────────────────────────────────
create table mistakes (
  id uuid primary key default gen_random_uuid(),
  game_id uuid not null references games(id) on delete cascade,
  user_id uuid not null references profiles(id) on delete cascade,
  ply int not null,
  move_number int not null,
  fen_before text not null,
  fen_before_hash text not null,
  played_move text not null,
  played_eval_cp int,
  played_mate_in int,
  best_move text not null,
  best_eval_cp int,
  best_mate_in int,
  delta_cp int not null,
  severity text not null check (severity in ('inaccuracy', 'mistake', 'blunder')),
  piece_moved text not null,
  from_square text not null,
  to_square text not null,
  was_capture boolean not null,
  remaining_clock_pct real,
  is_puzzle_worthy boolean not null default false,
  created_at timestamptz not null default now()
);

create index mistakes_user             on mistakes(user_id, created_at desc);
create index mistakes_user_game        on mistakes(user_id, game_id);
create index mistakes_user_piece_sq    on mistakes(user_id, piece_moved, from_square);


-- ── puzzles ────────────────────────────────────────────────────────────────────
create table puzzles (
  id uuid primary key default gen_random_uuid(),
  mistake_id uuid not null unique references mistakes(id) on delete cascade,
  user_id uuid not null references profiles(id) on delete cascade,
  fen text not null,
  side_to_move text not null check (side_to_move in ('white', 'black')),
  solution text not null,
  motifs text[] not null default '{}',
  difficulty_cp int not null,
  perspective text not null check (perspective in ('played_by_user', 'missed_by_user', 'opponent_blunder')),
  created_at timestamptz not null default now()
);

create index puzzles_user   on puzzles(user_id, created_at desc);
create index puzzles_motifs on puzzles using gin(motifs);


-- ── patterns ───────────────────────────────────────────────────────────────────
create table patterns (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references profiles(id) on delete cascade,
  kind text not null,
  title text not null,
  description text not null,
  severity_score real not null,
  evidence_count int not null,
  rating_impact_estimate int,
  first_seen_at timestamptz not null,
  last_seen_at timestamptz not null,
  signature text not null,
  unique (user_id, signature),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index patterns_user_severity on patterns(user_id, severity_score desc);

create table pattern_mistakes (
  pattern_id uuid not null references patterns(id) on delete cascade,
  mistake_id uuid not null references mistakes(id) on delete cascade,
  primary key (pattern_id, mistake_id)
);

create table pattern_dismissals (
  user_id    uuid not null references profiles(id) on delete cascade,
  pattern_id uuid not null references patterns(id) on delete cascade,
  dismissed_at timestamptz not null default now(),
  primary key (user_id, pattern_id)
);


-- ── reviews — FSRS state per puzzle per user ───────────────────────────────────
create table reviews (
  id uuid primary key default gen_random_uuid(),
  puzzle_id uuid not null references puzzles(id) on delete cascade,
  user_id uuid not null references profiles(id) on delete cascade,
  stability real not null,
  difficulty real not null,
  elapsed_days real not null default 0,
  scheduled_days real not null default 0,
  reps int not null default 0,
  lapses int not null default 0,
  state text not null default 'new',
  due_at timestamptz not null default now(),
  last_review_at timestamptz,
  unique (puzzle_id, user_id)
);

create index reviews_due on reviews(user_id, due_at) where state in ('learning', 'review', 'relapsed');

create table review_logs (
  id uuid primary key default gen_random_uuid(),
  review_id uuid not null references reviews(id) on delete cascade,
  rating int not null check (rating between 1 and 4),
  duration_ms int not null,
  reviewed_at timestamptz not null default now()
);


-- ── analysis_jobs — tracks ingest progress for UI polling ──────────────────────
create table analysis_jobs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references profiles(id) on delete cascade,
  kind text not null check (kind in ('initial_recent', 'historical_backfill', 'incremental')),
  status text not null default 'queued',
  games_total int not null default 0,
  games_done int not null default 0,
  positions_analyzed int not null default 0,
  cache_hits int not null default 0,
  error text,
  started_at timestamptz,
  finished_at timestamptz,
  created_at timestamptz not null default now()
);

create index analysis_jobs_user on analysis_jobs(user_id, created_at desc);
