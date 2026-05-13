import json
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ai_client import call_deepseek
from database import get_db
from mock_data import DEMO_ACTS
from prompts.generate_plot import build_system_prompt, build_user_prompt
from prompts.handle_input import build_system_prompt as input_system_prompt
from prompts.handle_input import build_user_prompt as input_user_prompt

router = APIRouter(prefix="/interactive", tags=["interactive"])


class GenerateRequest(BaseModel):
    room_id: str
    act_id: int
    characters: list[str]
    last_choice: Optional[dict] = None
    intimacy: dict
    unlocked_plots: list[str] = []
    user_character_id: str = "wentang"


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

    # Read flags before closing first connection
    flags_row = conn.execute(
        "SELECT flags_json FROM rooms WHERE room_id = ?", (req.room_id,)
    ).fetchone()
    pre_flags = json.loads(flags_row["flags_json"]) if flags_row else []

    conn.close()

    # Enrich last_choice with actual option text for better AI context
    enriched_last_choice = req.last_choice
    if req.last_choice:
        chosen_node_id = req.last_choice.get("node_id")
        chosen_option_id = req.last_choice.get("selected")
        for act in DEMO_ACTS:
            for node in act.get("nodes", []):
                if node["node_id"] == chosen_node_id:
                    options_pool = (
                        node.get("options_by_char", {}).get(req.user_character_id)
                        or node.get("options", [])
                    )
                    for opt in options_pool:
                        if opt["id"] == chosen_option_id:
                            enriched_last_choice = {
                                **req.last_choice,
                                "text": opt.get("text", ""),
                            }
                            break
                    break

    # Call AI to generate plot
    system_prompt = build_system_prompt()
    user_prompt = build_user_prompt(
        act_id=req.act_id,
        characters=characters,
        last_choice=enriched_last_choice,
        intimacy=req.intimacy,
        unlocked_plots=req.unlocked_plots,
        history_summary=history_summary,
        user_character_id=req.user_character_id,
        flags=pre_flags,
    )
    raw = call_deepseek(system_prompt=system_prompt, user_prompt=user_prompt)

    raw = raw.strip()
    if raw.startswith("```"):
        parts = raw.split("\n", 1)
        if len(parts) > 1:
            raw = parts[1].rsplit("```", 1)[0]
        # else: malformed fence, leave raw unchanged — json.loads will raise the proper 500 below

    try:
        result = json.loads(raw)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"AI 返回格式错误: {e}")

    if not isinstance(result, dict):
        raise HTTPException(status_code=500, detail="AI 返回结构错误: 期望 JSON 对象")

    # Re-open connection to read authoritative intimacy and write updates
    conn = get_db()

    # Read authoritative intimacy from DB (not client-sent req.intimacy)
    room_row = conn.execute(
        "SELECT intimacy_json, unlocked_plots_json, flags_json FROM rooms WHERE room_id = ?",
        (req.room_id,),
    ).fetchone()
    if not room_row:
        conn.close()
        raise HTTPException(status_code=404, detail="房间不存在")

    current_intimacy = json.loads(room_row["intimacy_json"])
    current_unlocked = json.loads(room_row["unlocked_plots_json"])
    current_flags = json.loads(room_row["flags_json"])

    # Apply intimacy deltas (clamped to [0, 100])
    for char_id, delta in result.get("intimacy_delta", {}).items():
        current_intimacy[char_id] = min(100, max(0, current_intimacy.get(char_id, 50) + delta))

    # Track newly unlocked plot node
    next_node = result.get("next_node")
    next_node_id = next_node.get("node_id") if isinstance(next_node, dict) else None
    if next_node_id and next_node_id not in current_unlocked:
        current_unlocked.append(next_node_id)

    # Write flags from last_choice's add_flags
    if req.last_choice:
        chosen_node_id = req.last_choice.get("node_id")
        chosen_option_id = req.last_choice.get("selected")
        for act in DEMO_ACTS:
            for node in act.get("nodes", []):
                if node["node_id"] == chosen_node_id:
                    # Look in options_by_char first, then fallback to options
                    options_pool = (
                        node.get("options_by_char", {}).get(req.user_character_id)
                        or node.get("options", [])
                    )
                    for opt in options_pool:
                        if opt["id"] == chosen_option_id:
                            for flag in opt.get("add_flags", []):
                                if flag not in current_flags:
                                    current_flags.append(flag)
                            break
                    break

    # Persist updates
    conn.execute(
        "UPDATE rooms SET intimacy_json = ?, unlocked_plots_json = ?, flags_json = ? WHERE room_id = ?",
        (
            json.dumps(current_intimacy, ensure_ascii=False),
            json.dumps(current_unlocked, ensure_ascii=False),
            json.dumps(current_flags, ensure_ascii=False),
            req.room_id,
        ),
    )
    conn.execute(
        "INSERT INTO messages (room_id, role, content, node_id) VALUES (?, ?, ?, ?)",
        (
            req.room_id,
            "assistant",
            result.get("plot_html", ""),
            next_node_id,
        ),
    )
    conn.commit()
    conn.close()

    # Inject options for single_choice nodes from DEMO_ACTS static data
    injected_node = result.get("next_node")
    if isinstance(injected_node, dict) and injected_node.get("type") == "single_choice":
        node_id = injected_node.get("node_id")
        matched_options = None

        # First try exact node_id match
        for act in DEMO_ACTS:
            for node in act.get("nodes", []):
                if node["node_id"] == node_id:
                    # Prefer per-character options if available
                    options_by_char = node.get("options_by_char", {})
                    matched_options = options_by_char.get(req.user_character_id) or node.get("options", [])
                    break
            if matched_options is not None:
                break

        # Fallback: match by act_id — use first single_choice node in that act
        if matched_options is None:
            for act in DEMO_ACTS:
                if act.get("act_id") == req.act_id:
                    for node in act.get("nodes", []):
                        if node.get("type") == "single_choice":
                            options_by_char = node.get("options_by_char", {})
                            matched_options = options_by_char.get(req.user_character_id) or node.get("options", [])
                            # Also align node_id so front-end tracking is consistent
                            injected_node["node_id"] = node["node_id"]
                            break
                    break

        if matched_options:
            injected_node["options"] = matched_options

    return result


class InputRequest(BaseModel):
    room_id: str
    user_character_id: str
    node_id: Optional[str] = None
    user_input: str


@router.post("/input")
async def handle_input(req: InputRequest):
    conn = get_db()

    # Load room state
    room_row = conn.execute(
        "SELECT intimacy_json, unlocked_plots_json, flags_json, novel_id FROM rooms WHERE room_id = ?",
        (req.room_id,),
    ).fetchone()
    if not room_row:
        conn.close()
        raise HTTPException(status_code=404, detail="房间不存在")

    intimacy = json.loads(room_row["intimacy_json"])
    current_unlocked = json.loads(room_row["unlocked_plots_json"])
    current_flags = json.loads(room_row["flags_json"])

    # Find the node prompt text from the novel's acts
    novel_row = conn.execute(
        "SELECT acts_json FROM novels WHERE novel_id = ?",
        (room_row["novel_id"],),
    ).fetchone()
    acts = json.loads(novel_row["acts_json"]) if novel_row else []
    node_prompt = ""
    for act in acts:
        for node in act.get("nodes", []):
            if node["node_id"] == req.node_id:
                node_prompt = node.get("prompt", "")
                break

    # Build history summary from recent messages
    recent = conn.execute(
        "SELECT content FROM messages WHERE room_id = ? ORDER BY created_at DESC LIMIT 5",
        (req.room_id,),
    ).fetchall()
    history_summary = " | ".join(row["content"][:50] for row in reversed(recent))

    conn.close()

    # Call AI to process user input
    system_prompt = input_system_prompt(req.user_character_id)
    user_prompt = input_user_prompt(
        user_input=req.user_input,
        node_prompt=node_prompt,
        intimacy=intimacy,
        history_summary=history_summary,
        flags=current_flags,
    )
    raw = call_deepseek(system_prompt=system_prompt, user_prompt=user_prompt)

    raw = raw.strip()
    if raw.startswith("```"):
        parts = raw.split("\n", 1)
        if len(parts) > 1:
            raw = parts[1].rsplit("```", 1)[0]

    try:
        result = json.loads(raw)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"AI 返回格式错误: {e}")

    if not isinstance(result, dict):
        raise HTTPException(status_code=500, detail="AI 返回结构错误: 期望 JSON 对象")

    # Apply intimacy deltas from DB-authoritative values
    conn = get_db()
    # Re-read to get the most up-to-date intimacy
    fresh_row = conn.execute(
        "SELECT intimacy_json, unlocked_plots_json FROM rooms WHERE room_id = ?",
        (req.room_id,),
    ).fetchone()
    if not fresh_row:
        conn.close()
        raise HTTPException(status_code=404, detail="房间不存在")
    current_intimacy = json.loads(fresh_row["intimacy_json"])
    current_unlocked = json.loads(fresh_row["unlocked_plots_json"])

    for char_id, delta in result.get("intimacy_delta", {}).items():
        current_intimacy[char_id] = min(100, max(0, current_intimacy.get(char_id, 50) + delta))

    # Track newly unlocked plot node
    next_node = result.get("next_node", {})
    next_node_id = next_node.get("node_id") if isinstance(next_node, dict) else None
    if next_node_id and next_node_id not in current_unlocked:
        current_unlocked.append(next_node_id)

    # Save user message and AI reply to messages table
    conn.execute(
        "INSERT INTO messages (room_id, role, character_id, content, node_id) VALUES (?, ?, ?, ?, ?)",
        (req.room_id, "user", req.user_character_id, req.user_input, req.node_id),
    )
    conn.execute(
        "INSERT INTO messages (room_id, role, content, node_id) VALUES (?, ?, ?, ?)",
        (req.room_id, "assistant", result.get("character_reply", ""), req.node_id),
    )
    conn.execute(
        "UPDATE rooms SET intimacy_json = ?, unlocked_plots_json = ? WHERE room_id = ?",
        (
            json.dumps(current_intimacy, ensure_ascii=False),
            json.dumps(current_unlocked, ensure_ascii=False),
            req.room_id,
        ),
    )
    conn.commit()
    conn.close()

    return result
