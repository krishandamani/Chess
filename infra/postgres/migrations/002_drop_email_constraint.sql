-- Drop email requirement: solo dogfooding needs no account
alter table users
  alter column email drop not null,
  alter column email set default null;

-- Allow upsert by chess username
create unique index if not exists users_chesscom_uq on users(chesscom_username) where chesscom_username is not null;
create unique index if not exists users_lichess_uq  on users(lichess_username)  where lichess_username  is not null;
