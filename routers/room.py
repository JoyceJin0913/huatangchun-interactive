import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ai_client import call_deepseek
from database import get_db
from prompts.settle_ending import (
    determine_ending_type,
    build_system_prompt,
    build_user_prompt,
)

router = APIRouter(prefix="/room", tags=["room"])


class SettleRequest(BaseModel):
    room_id: str


@router.post("/settle")
async def settle_room(req: SettleRequest):
    conn = get_db()

    # Step 1: Read room from DB
    row = conn.execute(
        "SELECT intimacy_json, choices_json, unlocked_plots_json, status "
        "FROM rooms WHERE room_id = ?",
        (req.room_id,),
    ).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="房间不存在")

    # Idempotency: prevent re-settling an already-settled room
    if row["status"] == "settled":
        conn.close()
        raise HTTPException(status_code=409, detail="房间已结算")

    # Step 2: Parse all three JSON fields
    try:
        intimacy = json.loads(row["intimacy_json"])
        choices = json.loads(row["choices_json"])
        unlocked_plots = json.loads(row["unlocked_plots_json"])
    except json.JSONDecodeError:
        conn.close()
        raise HTTPException(status_code=500, detail="房间数据格式损坏")

    # Step 3: Count total_interactions from messages table
    count_row = conn.execute(
        "SELECT COUNT(*) as cnt FROM messages WHERE room_id = ?",
        (req.room_id,),
    ).fetchone()
    total_interactions = count_row["cnt"]

    conn.close()

    # Step 4: Determine ending type
    ending_type = determine_ending_type(intimacy)

    # Step 5: Build prompts
    system_prompt = build_system_prompt()
    user_prompt = build_user_prompt(
        ending_type=ending_type,
        intimacy=intimacy,
        choices=choices,
        total_interactions=total_interactions,
        unlocked_plots=unlocked_plots,
    )

    # Step 6: Call DeepSeek AI
    raw = call_deepseek(system_prompt, user_prompt)

    # Step 7: Strip markdown fences
    raw = raw.strip()
    if raw.startswith("```"):
        parts = raw.split("\n", 1)
        if len(parts) > 1:
            raw = parts[1].rsplit("```", 1)[0].strip()

    # Step 8: Parse JSON
    try:
        result = json.loads(raw)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"AI 返回格式错误: {e}")

    if not isinstance(result, dict):
        raise HTTPException(status_code=500, detail="AI 返回结构错误: 期望 JSON 对象")

    # Step 9 & 10: Update room status and commit
    conn = get_db()
    try:
        conn.execute(
            "UPDATE rooms SET status = 'settled' WHERE room_id = ?",
            (req.room_id,),
        )
        conn.commit()
    finally:
        conn.close()

    # Step 11: Return response
    return {
        "ending_type": ending_type,
        "ending_text": result.get("ending_text", ""),
        "relationship_graph": result.get("relationship_graph", []),
        "highlight_report": result.get("highlight_report", {}),
    }
