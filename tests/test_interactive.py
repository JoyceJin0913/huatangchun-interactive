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
        "INSERT INTO rooms (room_id, novel_id, intimacy_json, choices_json) VALUES (?, ?, ?, ?)",
        (DEMO_ROOM_ID, DEMO_NOVEL_ID, json.dumps(DEMO_INITIAL_INTIMACY), "[]"),
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
