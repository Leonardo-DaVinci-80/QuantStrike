import sqlite3
from contextlib import contextmanager
from backend.config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS portfolio_transactions (
 id INTEGER PRIMARY KEY AUTOINCREMENT, portfolio_id TEXT NOT NULL, asset_id TEXT NOT NULL,
 asset_name TEXT NOT NULL, side TEXT NOT NULL CHECK(side IN ('BUY','SELL')),
 quantity REAL NOT NULL CHECK(quantity > 0), unit_price REAL NOT NULL CHECK(unit_price >= 0),
 fees REAL NOT NULL DEFAULT 0 CHECK(fees >= 0), currency TEXT NOT NULL DEFAULT 'USD',
 transacted_at TEXT NOT NULL, note TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_feature_tx ON portfolio_transactions(portfolio_id,asset_id,transacted_at);
CREATE TABLE IF NOT EXISTS watchlist (
 id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL DEFAULT 'local', asset_id TEXT NOT NULL,
 asset_name TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, UNIQUE(user_id,asset_id)
);
CREATE TABLE IF NOT EXISTS alert_rules (
 id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL DEFAULT 'local', asset_id TEXT NOT NULL,
 metric TEXT NOT NULL CHECK(metric IN ('price','return_pct')), operator TEXT NOT NULL CHECK(operator IN ('>','>=','<','<=')),
 threshold REAL NOT NULL, cooldown_minutes INTEGER NOT NULL DEFAULT 60, enabled INTEGER NOT NULL DEFAULT 1,
 last_triggered_at TEXT
);
CREATE TABLE IF NOT EXISTS alert_events (
 id INTEGER PRIMARY KEY AUTOINCREMENT, rule_id INTEGER NOT NULL REFERENCES alert_rules(id),
 observed_value REAL NOT NULL, message TEXT NOT NULL, triggered_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS market_observations (
 id INTEGER PRIMARY KEY AUTOINCREMENT, asset_id TEXT NOT NULL, asset_name TEXT NOT NULL, marketplace TEXT NOT NULL,
 observed_at TEXT NOT NULL, price REAL NOT NULL CHECK(price >= 0), currency TEXT NOT NULL,
 condition_name TEXT NOT NULL DEFAULT '', volume REAL, source_ref TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_feature_market ON market_observations(asset_id,observed_at);
CREATE TABLE IF NOT EXISTS research_entries (
 id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL DEFAULT 'local', title TEXT NOT NULL,
 hypothesis TEXT NOT NULL DEFAULT '', body TEXT NOT NULL DEFAULT '', asset_ids_json TEXT NOT NULL DEFAULT '[]',
 evidence_json TEXT NOT NULL DEFAULT '{}', strategy_run_json TEXT NOT NULL DEFAULT '{}',
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn=sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory=sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA foreign_keys=ON')
    conn.executescript(SCHEMA)
    return conn

@contextmanager
def db_session():
    conn=connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
