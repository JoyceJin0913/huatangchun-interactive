import json
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from main import app
from database import init_db, get_db
from mock_data import DEMO_NOVEL_ID, DEMO_CHARACTERS, DEMO_ACTS, DEMO_ROOM_ID, DEMO_INITIAL_INTIMACY

client = TestClient(app)

MOCK_GENERATE_RESPONSE = json.dumps({
    "plot_html": "<p>裴容放下书卷，沉声道：「朕问你，想不想抚育三皇子？」</p>",
    "next_node": {
        "node_id": "act1_node2",
        "type": "free_input",
        "prompt": "裴琰望着你，轻声问道……",
    },
    "intimacy_delta": {"peiyan": 10, "peirong": 5},
    "system_message": "裴琰的戒备心下降了",
})


@pytest.fixture(autouse=True)
def setup_db(tmp_path, monkeypatch):
    db_path = str(tmp_path / "test.db")
    monkeypatch.setenv("DB_PATH", db_path)
    init_db()
    # Write test novel and room data
    conn = get_db()
    conn.execute(
        "INSERT INTO novels (novel_id, characters_json, acts_json) VALUES (?, ?, ?)",
        (DEMO_NOVEL_ID, json.dumps(DEMO_CHARACTERS), json.dumps(DEMO_ACTS)),
    )
    conn.execute(
        "INSERT INTO rooms (room_id, novel_id, intimacy_json, unlocked_plots_json, choices_json) VALUES (?, ?, ?, ?, ?)",
        (DEMO_ROOM_ID, DEMO_NOVEL_ID, json.dumps(DEMO_INITIAL_INTIMACY), "[]", "[]"),
    )
    conn.commit()
    conn.close()


def test_generate_returns_plot_and_next_node():
    with patch("routers.interactive.call_deepseek", return_value=MOCK_GENERATE_RESPONSE):
        response = client.post(
            "/interactive/generate",
            json={
                "room_id": DEMO_ROOM_ID,
                "act_id": 1,
                "characters": ["wentang", "peiyan", "peirong"],
                "last_choice": None,
                "intimacy": DEMO_INITIAL_INTIMACY,
                "unlocked_plots": [],
            },
        )
    assert response.status_code == 200
    data = response.json()
    assert "plot_html" in data
    assert "next_node" in data
    assert data["next_node"]["type"] in ("single_choice", "free_input", "cutscene")
    assert "intimacy_delta" in data


def test_generate_updates_intimacy_in_db():
    with patch("routers.interactive.call_deepseek", return_value=MOCK_GENERATE_RESPONSE):
        client.post(
            "/interactive/generate",
            json={
                "room_id": DEMO_ROOM_ID,
                "act_id": 1,
                "characters": ["wentang", "peiyan", "peirong"],
                "last_choice": {"node_id": "act1_node1", "selected": "A"},
                "intimacy": DEMO_INITIAL_INTIMACY,
                "unlocked_plots": [],
            },
        )
    conn = get_db()
    row = conn.execute(
        "SELECT intimacy_json FROM rooms WHERE room_id = ?", (DEMO_ROOM_ID,)
    ).fetchone()
    conn.close()
    intimacy = json.loads(row["intimacy_json"])
    # peiyan should go from 50 + 10 = 60
    assert intimacy["peiyan"] == 60


MOCK_INPUT_RESPONSE = json.dumps({
    "emotion_tag": "温柔",
    "adjusted_input": "温棠轻声道：「琰儿，你想吃枣花糕吗？」",
    "character_reply": "裴琰垂眸，良久才低声道：「……娘娘做的枣花糕，很甜。」",
    "intimacy_delta": {"peiyan": 12},
    "next_node": {"node_id": "act1_node3", "type": "cutscene"},
})


def test_input_returns_adjusted_and_reply():
    with patch("routers.interactive.call_deepseek", return_value=MOCK_INPUT_RESPONSE):
        response = client.post(
            "/interactive/input",
            json={
                "room_id": DEMO_ROOM_ID,
                "user_character_id": "wentang",
                "node_id": "act1_node2",
                "user_input": "琰儿，你想吃枣花糕吗？",
            },
        )
    assert response.status_code == 200
    data = response.json()
    assert "adjusted_input" in data
    assert "character_reply" in data
    assert "emotion_tag" in data
    assert data["emotion_tag"] in ("温柔", "克制", "试探", "激进", "委屈", "傲慢")
    assert "intimacy_delta" in data


def test_input_saves_to_messages():
    with patch("routers.interactive.call_deepseek", return_value=MOCK_INPUT_RESPONSE):
        client.post(
            "/interactive/input",
            json={
                "room_id": DEMO_ROOM_ID,
                "user_character_id": "wentang",
                "node_id": "act1_node2",
                "user_input": "琰儿，你想吃枣花糕吗？",
            },
        )
    conn = get_db()
    user_count = conn.execute(
        "SELECT COUNT(*) as cnt FROM messages WHERE room_id = ? AND role = 'user'",
        (DEMO_ROOM_ID,),
    ).fetchone()["cnt"]
    asst_count = conn.execute(
        "SELECT COUNT(*) as cnt FROM messages WHERE room_id = ? AND role = 'assistant'",
        (DEMO_ROOM_ID,),
    ).fetchone()["cnt"]
    conn.close()
    assert user_count >= 1
    assert asst_count >= 1


def test_input_updates_intimacy_in_db():
    with patch("routers.interactive.call_deepseek", return_value=MOCK_INPUT_RESPONSE):
        client.post(
            "/interactive/input",
            json={
                "room_id": DEMO_ROOM_ID,
                "user_character_id": "wentang",
                "node_id": "act1_node2",
                "user_input": "琰儿，你想吃枣花糕吗？",
            },
        )
    conn = get_db()
    row = conn.execute(
        "SELECT intimacy_json FROM rooms WHERE room_id = ?", (DEMO_ROOM_ID,)
    ).fetchone()
    conn.close()
    intimacy = json.loads(row["intimacy_json"])
    # peiyan should go from 50 + 12 = 62 (MOCK_INPUT_RESPONSE intimacy_delta)
    assert intimacy["peiyan"] == 62
