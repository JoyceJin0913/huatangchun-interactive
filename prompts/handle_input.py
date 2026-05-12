CHARACTER_PERSONALITIES = {
    "wentang": {
        "name": "温棠",
        "style": "温和隐忍，语气缓柔，偶尔结巴，不会主动激进或强势",
        "forbidden": ["激进对抗", "主动争宠", "强硬拒绝皇帝"],
    },
    "peirong": {
        "name": "裴容",
        "style": "沉稳威严，语气平淡，带压迫感，说话简洁",
        "forbidden": ["撒娇", "过度温柔", "主动示好"],
    },
    "peiyan": {
        "name": "裴琰",
        "style": "乖巧小心翼翼，偶尔磕巴，语气依赖温棠",
        "forbidden": ["傲慢", "强势", "无视温棠"],
    },
}

def build_system_prompt(character_id: str) -> str:
    char = CHARACTER_PERSONALITIES.get(
        character_id,
        {"name": "角色", "style": "正常对话风格", "forbidden": []},
    )
    forbidden_text = "、".join(char["forbidden"]) if char["forbidden"] else "无特别限制"
    return f"""你是《画堂春》互动文游的对话处理引擎。
当前玩家扮演角色：{char['name']}
角色说话风格：{char['style']}
不允许出现的行为：{forbidden_text}

任务：
1. 判断用户输入的情绪风格（从：温柔、克制、试探、激进、委屈、傲慢 中选一个）
2. 若输入风格偏离角色性格，将输入调整为符合角色风格的表达
3. 以对方角色的口吻生成回应
4. 严格按 JSON 格式输出，不输出 JSON 以外的内容"""

def build_user_prompt(
    user_input: str,
    user_character_id: str,
    node_prompt: str,
    intimacy: dict,
    history_summary: str,
) -> str:
    intimacy_text = "、".join(f"{k}亲密度{v}" for k, v in intimacy.items())
    return f"""当前情境：{node_prompt}
当前亲密度：{intimacy_text}
历史摘要：{history_summary if history_summary else '无'}

玩家输入：「{user_input}」

请按以下 JSON 格式输出：
{{
  "emotion_tag": "情绪标签（温柔/克制/试探/激进/委屈/傲慢之一）",
  "adjusted_input": "调整后的玩家发言（保留原意，调整为符合角色风格）",
  "character_reply": "对方角色的回应（古言风格，≤100字）",
  "intimacy_delta": {{"角色id": 变化值（-20到+20的整数）}},
  "next_node": {{
    "node_id": "下一节点id或null",
    "type": "cutscene 或 free_input 或 single_choice"
  }}
}}"""
