-- ── Enable RLS on all user-scoped tables ───────────────────────────────────────
alter table profiles          enable row level security;
alter table games             enable row level security;
alter table mistakes          enable row level security;
alter table puzzles           enable row level security;
alter table patterns          enable row level security;
alter table pattern_mistakes  enable row level security;
alter table pattern_dismissals enable row level security;
alter table reviews           enable row level security;
alter table review_logs       enable row level security;
alter table analysis_jobs     enable row level security;

-- position_evals is a global shared cache — no RLS, service role writes it.


-- ── profiles ──────────────────────────────────────────────────────────────────
create policy "Users can read own profile"
  on profiles for select using (auth.uid() = id);

create policy "Users can update own profile"
  on profiles for update using (auth.uid() = id);


-- ── games ──────────────────────────────────────────────────────────────────────
create policy "Users can read own games"
  on games for select using (auth.uid() = user_id);

create policy "Users can insert own games"
  on games for insert with check (auth.uid() = user_id);


-- ── mistakes ───────────────────────────────────────────────────────────────────
create policy "Users can read own mistakes"
  on mistakes for select using (auth.uid() = user_id);


-- ── puzzles ────────────────────────────────────────────────────────────────────
create policy "Users can read own puzzles"
  on puzzles for select using (auth.uid() = user_id);


-- ── patterns ───────────────────────────────────────────────────────────────────
create policy "Users can read own patterns"
  on patterns for select using (auth.uid() = user_id);

create policy "Users can dismiss patterns"
  on pattern_dismissals for all using (auth.uid() = user_id);

create policy "Users can read pattern_mistakes for their patterns"
  on pattern_mistakes for select using (
    exists (
      select 1 from patterns p
      where p.id = pattern_id and p.user_id = auth.uid()
    )
  );


-- ── reviews ────────────────────────────────────────────────────────────────────
create policy "Users can read own reviews"
  on reviews for select using (auth.uid() = user_id);

create policy "Users can update own reviews"
  on reviews for update using (auth.uid() = user_id);

create policy "Users can insert own review_logs"
  on review_logs for insert with check (
    exists (
      select 1 from reviews r
      where r.id = review_id and r.user_id = auth.uid()
    )
  );

create policy "Users can read own review_logs"
  on review_logs for select using (
    exists (
      select 1 from reviews r
      where r.id = review_id and r.user_id = auth.uid()
    )
  );


-- ── analysis_jobs ──────────────────────────────────────────────────────────────
create policy "Users can read own jobs"
  on analysis_jobs for select using (auth.uid() = user_id);

-- Workers bypass RLS via service role key; no client-side write policies needed.
