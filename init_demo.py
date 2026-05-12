#!/usr/bin/env python3
"""
Demo seed script for the interactive novel game.
Populates the SQLite database with demo data for the Hackathon demo.
Idempotent: safe to run multiple times.
"""

import json
from database import init_db, get_db
from mock_data import (
    DEMO_NOVEL_ID,
    DEMO_CHARACTERS,
    DEMO_ACTS,
    DEMO_ROOM_ID,
    DEMO_INITIAL_INTIMACY,
)


def seed():
    """Populate the database with demo data (idempotent)."""
    # Ensure schema exists
    init_db()
    print("✅ 数据库架构已初始化")

    conn = get_db()

    # Check if DEMO_NOVEL_ID already exists
    novel_row = conn.execute(
        "SELECT novel_id FROM novels WHERE novel_id = ?",
        (DEMO_NOVEL_ID,),
    ).fetchone()

    if novel_row:
        print("✅ 小说数据已存在")
    else:
        # Insert novel data
        conn.execute(
            "INSERT INTO novels (novel_id, characters_json, acts_json) VALUES (?, ?, ?)",
            (
                DEMO_NOVEL_ID,
                json.dumps(DEMO_CHARACTERS, ensure_ascii=False),
                json.dumps(DEMO_ACTS, ensure_ascii=False),
            ),
        )
        print("✅ 小说数据写入成功")

    # Check if DEMO_ROOM_ID already exists
    room_row = conn.execute(
        "SELECT room_id FROM rooms WHERE room_id = ?",
        (DEMO_ROOM_ID,),
    ).fetchone()

    if room_row:
        print("✅ 房间数据已存在")
    else:
        # Insert room data
        conn.execute(
            "INSERT INTO rooms (room_id, novel_id, intimacy_json, choices_json, unlocked_plots_json) VALUES (?, ?, ?, ?, ?)",
            (
                DEMO_ROOM_ID,
                DEMO_NOVEL_ID,
                json.dumps(DEMO_INITIAL_INTIMACY, ensure_ascii=False),
                json.dumps([], ensure_ascii=False),
                json.dumps([], ensure_ascii=False),
            ),
        )
        print("✅ 房间数据写入成功")

    conn.commit()
    conn.close()
    print("✅ Demo 数据已准备完毕！")


if __name__ == "__main__":
    seed()
