import os
import sqlite3
from dotenv import load_dotenv

load_dotenv()


def get_db() -> sqlite3.Connection:
    db_path = os.getenv("DB_PATH", "novel.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS novels (
            novel_id         TEXT PRIMARY KEY,
            characters_json  TEXT NOT NULL,
            acts_json        TEXT NOT NULL,
            created_at       DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS rooms (
            room_id              TEXT PRIMARY KEY,
            novel_id             TEXT NOT NULL,
            intimacy_json        TEXT NOT NULL,
            choices_json         TEXT NOT NULL DEFAULT '[]',
            unlocked_plots_json  TEXT NOT NULL DEFAULT '[]',
            status               TEXT NOT NULL DEFAULT 'active',
            created_at           DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS messages (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id      TEXT NOT NULL,
            role         TEXT NOT NULL,
            character_id TEXT,
            content      TEXT NOT NULL,
            node_id      TEXT,
            created_at   DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    conn.close()
