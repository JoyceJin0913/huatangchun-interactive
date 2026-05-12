import json
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from main import app
from database import init_db, get_db
from mock_data import DEMO_NOVEL_ID, DEMO_CHARACTERS, DEMO_ACTS, DEMO_ROOM_ID

client = TestClient(app)

MOCK_SETTLE_RESPONSE = json.dumps({
    "ending_text": "温棠封妃，裴琰健康成长，采桑宫终成后宫一方净土。",
    "relationship_graph": [
        {"from": "wentang", "to": "peiyan", "final_intimacy": 88, "label": "母子情深"},
        {"from": "wentang", "to": "peirong", "final_intimacy": 72, "label": "帝宠渐深"},
    ],
    "highlight_report": {
        "top_character": "裴琰",
        "best_choice": "欣然应允收养裴琰",
        "keyword": "最温柔的守护者",
        "total_interactions": 12,
        "unlocked_plots": 3,
    },
})

SETTLE_INTIMACY = {"peiyan": 80, "peirong": 75, "peiyu": 25}
SETTLE_CHOICES = [{"node_id": "act1_node1", "selected": "A"}]
SETTLE_UNLOCKED = ["采桑宫温居"]


@pytest.fixture(autouse=True)
def setup_db(tmp_path, monkeypatch):
    db_path = str(tmp_path / "test.db")
    monkeypatch.setenv("DB_PATH", db_path)
    init_db()
    conn = get_db()
    # Seed novel
    conn.execute(
        "INSERT INTO novels (novel_id, characters_json, acts_json) VALUES (?, ?, ?)",
        (DEMO_NOVEL_ID, json.dumps(DEMO_CHARACTERS), json.dumps(DEMO_ACTS)),
    )
    # Seed room with high intimacy values
    conn.execute(
        "INSERT INTO rooms (room_id, novel_id, intimacy_json, choices_json, unlocked_plots_json) VALUES (?, ?, ?, ?, ?)",
        (
            DEMO_ROOM_ID,
            DEMO_NOVEL_ID,
            json.dumps(SETTLE_INTIMACY),
            json.dumps(SETTLE_CHOICES),
            json.dumps(SETTLE_UNLOCKED),
        ),
    )
    # Seed 5 user messages
    for i in range(5):
        conn.execute(
            "INSERT INTO messages (room_id, role, content) VALUES (?, ?, ?)",
            (DEMO_ROOM_ID, "user", f"用户消息 {i + 1}"),
        )
    conn.commit()
    conn.close()


def test_settle_returns_ending_and_report():
    with patch("routers.room.call_deepseek", return_value=MOCK_SETTLE_RESPONSE):
        response = client.post("/room/settle", json={"room_id": DEMO_ROOM_ID})
    assert response.status_code == 200
    data = response.json()
    assert "ending_type" in data
    assert "ending_text" in data
    assert "relationship_graph" in data
    assert "highlight_report" in data
    assert data["ending_type"] in ("perfect", "regret", "hidden")
    assert "top_character" in data["highlight_report"]


def test_settle_marks_room_as_settled():
    with patch("routers.room.call_deepseek", return_value=MOCK_SETTLE_RESPONSE):
        client.post("/room/settle", json={"room_id": DEMO_ROOM_ID})
    conn = get_db()
    row = conn.execute(
        "SELECT status FROM rooms WHERE room_id = ?", (DEMO_ROOM_ID,)
    ).fetchone()
    conn.close()
    assert row["status"] == "settled"


def test_settle_perfect_ending_when_high_intimacy():
    # peiyan=80, peirong=75 → both >= 70, peirong < 85 → "perfect"
    with patch("routers.room.call_deepseek", return_value=MOCK_SETTLE_RESPONSE):
        response = client.post("/room/settle", json={"room_id": DEMO_ROOM_ID})
    assert response.status_code == 200
    assert response.json()["ending_type"] == "perfect"
