import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ai_client import call_deepseek
from database import get_db
from prompts.parse_novel import SYSTEM_PROMPT, build_user_prompt

router = APIRouter(prefix="/novel", tags=["novel"])


class ParseRequest(BaseModel):
    novel_id: str
    content: str


@router.post("/parse")
async def parse_novel(req: ParseRequest):
    # 调用 DeepSeek 解析
    user_prompt = build_user_prompt(req.novel_id, req.content)
    raw = call_deepseek(system_prompt=SYSTEM_PROMPT, user_prompt=user_prompt)

    # 清理可能的 markdown 代码块包裹
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
        raw = raw.rsplit("```", 1)[0]

    try:
        result = json.loads(raw)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"AI 返回格式错误: {e}")

    # 写入数据库（已存在则覆盖）
    conn = get_db()
    conn.execute(
        """
        INSERT OR REPLACE INTO novels (novel_id, characters_json, acts_json)
        VALUES (?, ?, ?)
        """,
        (
            req.novel_id,
            json.dumps(result.get("characters", []), ensure_ascii=False),
            json.dumps(result.get("acts", []), ensure_ascii=False),
        ),
    )
    conn.commit()
    conn.close()

    return result
