import json
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

MOCK_AI_RESPONSE = json.dumps({
    "novel_id": "test_novel_001",
    "characters": [
        {
            "id": "wentang",
            "name": "温棠",
            "role": "protagonist",
            "personality": ["温和隐忍"],
            "skills": ["枣花糕"],
            "initial_intimacy": 50,
        }
    ],
    "acts": [
        {
            "act_id": 1,
            "title": "雪夜",
            "content_html": "<p>测试内容</p>",
            "nodes": [
                {
                    "node_id": "act1_node1",
                    "type": "single_choice",
                    "trigger": "测试触发",
                    "prompt": "测试问题",
                    "options": [
                        {"id": "A", "text": "选项A", "intimacy_delta": {"wentang": 10}}
                    ],
                }
            ],
        }
    ],
})


def test_novel_parse_returns_characters_and_acts():
    with patch("routers.novel.call_deepseek", return_value=MOCK_AI_RESPONSE):
        response = client.post(
            "/novel/parse",
            json={"novel_id": "test_novel_001", "content": "测试小说内容"},
        )
    assert response.status_code == 200
    data = response.json()
    assert data["novel_id"] == "test_novel_001"
    assert len(data["characters"]) >= 1
    assert data["characters"][0]["id"] == "wentang"
    assert len(data["acts"]) >= 1


def test_novel_parse_saves_to_db():
    with patch("routers.novel.call_deepseek", return_value=MOCK_AI_RESPONSE):
        response = client.post(
            "/novel/parse",
            json={"novel_id": "test_novel_save_001", "content": "测试内容"},
        )
        assert response.status_code == 200
        # 再次请求相同 novel_id，确认 INSERT OR REPLACE 不报错
        response2 = client.post(
            "/novel/parse",
            json={"novel_id": "test_novel_save_001", "content": "不同内容"},
        )
    assert response2.status_code == 200
