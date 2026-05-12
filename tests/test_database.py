import os
import pytest
from database import init_db, get_db


def test_init_db_creates_tables(tmp_path, monkeypatch):
    db_path = str(tmp_path / "test.db")
    monkeypatch.setenv("DB_PATH", db_path)
    init_db()
    conn = get_db()
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    )
    tables = {row[0] for row in cursor.fetchall()}
    assert "novels" in tables
    assert "rooms" in tables
    assert "messages" in tables
    conn.close()
