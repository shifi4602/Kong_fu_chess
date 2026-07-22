CREATE TABLE IF NOT EXISTS accounts (
    username        TEXT PRIMARY KEY,
    password_hash   BLOB NOT NULL,
    password_salt   BLOB NOT NULL,
    elo_rating      INTEGER NOT NULL DEFAULT 1200,
    created_at_utc  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE TABLE IF NOT EXISTS games (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id           TEXT NOT NULL UNIQUE,
    white_username       TEXT NOT NULL REFERENCES accounts(username),
    black_username       TEXT NOT NULL REFERENCES accounts(username),
    winner_color         TEXT NOT NULL CHECK (winner_color IN ('white', 'black')),
    white_rating_before  INTEGER NOT NULL,
    black_rating_before  INTEGER NOT NULL,
    white_rating_after   INTEGER NOT NULL,
    black_rating_after   INTEGER NOT NULL,
    recorded_at_utc      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_games_white ON games(white_username);
CREATE INDEX IF NOT EXISTS idx_games_black ON games(black_username);
