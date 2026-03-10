CREATE TABLE IF NOT EXISTS players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    hendonmob_id TEXT UNIQUE,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS tournaments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL REFERENCES players(id),
    event_name TEXT NOT NULL,
    date TEXT,
    buy_in INTEGER,
    prize INTEGER,
    finish_position TEXT,
    source TEXT NOT NULL,
    source_url TEXT,
    scraped_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(player_id, event_name, date)
);

CREATE TABLE IF NOT EXISTS hand_histories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL REFERENCES players(id),
    tournament_id INTEGER REFERENCES tournaments(id),
    source TEXT NOT NULL,
    source_url TEXT,
    raw_text TEXT NOT NULL,
    parsed_json TEXT,
    parsed_at TEXT,
    scraped_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS raw_scrapes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL,
    content TEXT NOT NULL,
    content_type TEXT DEFAULT 'html',
    scraped_at TEXT NOT NULL DEFAULT (datetime('now'))
);
