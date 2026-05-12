import json
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ai_client import call_deepseek
from database import get_db
from prompts.generate_plot import build_system_prompt, build_user_prompt

router = APIRouter(prefix="/interactive", tags=["interactive"])


class GenerateRequest(BaseModel):
    room_id: str
    act_id: int
    characters: list[str]
    last_choice: Optional[dict] = None
    intimacy: dict
    unlocked_plots: list[str] = []


@router.post("/generate")
async def generate_plot(req: GenerateRequest):
    conn = get_db()

    # Load character details from novels table via the room's novel_id
    novel_row = conn.execute(
        "SELECT characters_json FROM novels WHERE novel_id = "
        "(SELECT novel_id FROM rooms WHERE room_id = ?)",
        (req.room_id,),
    ).fetchone()
    if not novel_row:
        conn.close()
        raise HTTPException(status_code=404, detail="房间或小说不存在")

    all_characters = json.loads(novel_row["characters_json"])
    characters = [c for c in all_characters if c["id"] in req.characters]

    # Build history summary from recent messages
    recent_messages = conn.execute(
        "SELECT content FROM messages WHERE room_id = ? ORDER BY created_at DESC LIMIT 5",
        (req.room_id,),
    ).fetchall()
    history_summary = " | ".join(row["content"][:50] for row in reversed(recent_messages))

    conn.close()

    # Call AI to generate plot
    system_prompt = build_system_prompt()
    user_prompt = build_user_prompt(
        act_id=req.act_id,
        characters=characters,
        last_choice=req.last_choice,
        intimacy=req.intimacy,
        unlocked_plots=req.unlocked_plots,
        history_summary=history_summary,
    )
    raw = call_deepseek(system_prompt=system_prompt, user_prompt=user_prompt)

    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
        raw = raw.rsplit("```", 1)[0]

    try:
        result = json.loads(raw)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"AI 返回格式错误: {e}")

    if not isinstance(result, dict):
        raise HTTPException(status_code=500, detail="AI 返回结构错误: 期望 JSON 对象")

    # Update intimacy in DB
    current_intimacy = dict(req.intimacy)
    for char_id, delta in result.get("intimacy_delta", {}).items():
        current_intimacy[char_id] = min(100, max(0, current_intimacy.get(char_id, 50) + delta))

    # Record message and update room
    conn = get_db()
    conn.execute(
        "UPDATE rooms SET intimacy_json = ? WHERE room_id = ?",
        (json.dumps(current_intimacy, ensure_ascii=False), req.room_id),
    )
    conn.execute(
        "INSERT INTO messages (room_id, role, content, node_id) VALUES (?, ?, ?, ?)",
        (
            req.room_id,
            "assistant",
            result.get("plot_html", ""),
            result.get("next_node", {}).get("node_id"),
        ),
    )
    conn.commit()
    conn.close()

    return result
