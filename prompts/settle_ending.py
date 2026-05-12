ENDING_RULES = {
    "perfect": "所有核心角色（peiyan、peirong）最终亲密度均 ≥ 70",
    "hidden": "裴容(peirong)最终亲密度 ≥ 85",
    "regret": "至少一个核心角色亲密度 < 40",
}

def determine_ending_type(intimacy: dict) -> str:
    peirong = intimacy.get("peirong", 0)
    peiyan = intimacy.get("peiyan", 0)
    if peirong >= 85:
        return "hidden"
    if peirong >= 70 and peiyan >= 70:
        return "perfect"
    if peirong < 40 or peiyan < 40:
        return "regret"
    # 中间段亲密度（40–69）也归为遗憾结局，无需单独结局分支
    return "regret"

def build_system_prompt() -> str:
    return """你是《画堂春》互动文游的结局生成引擎。
请根据玩家的选择路径和最终亲密度数据，生成专属结局。
输出要求：严格按 JSON 格式，不输出 JSON 以外的内容，结局文本古言风格≤200字。"""

def build_user_prompt(
    ending_type: str,
    intimacy: dict,
    choices: list,
    total_interactions: int,
    unlocked_plots: list,
) -> str:
    ending_desc = {
        "perfect": "圆满结局：温棠封妃，裴琰健康成长，采桑宫成为净土",
        "hidden": "隐藏结局：帝心已定，温棠获封贵妃，裴琰地位稳固",
        "regret": "遗憾结局：温棠未能赢得足够信任，采桑宫依旧冷清",
    }[ending_type]

    intimacy_text = "、".join(f"{k}最终亲密度{v}" for k, v in intimacy.items())
    choices_text = " → ".join(
        f"{c.get('node_id', '')}选{c.get('selected', '')}" for c in choices[-5:]
    )

    return f"""结局类型：{ending_type}（{ending_desc}）
最终亲密度：{intimacy_text}
最后5步选择路径：{choices_text}
总互动次数：{total_interactions}
已解锁剧情：{', '.join(unlocked_plots) if unlocked_plots else '无'}

请生成结局内容，严格按以下 JSON 输出：
{{
  "ending_text": "结局叙述文字（古言风格，≤200字）",
  "relationship_graph": [
    {{"from": "wentang", "to": "角色id", "final_intimacy": 数值, "label": "关系描述"}}
  ],
  "highlight_report": {{
    "top_character": "亲密度最高的角色中文名",
    "best_choice": "最关键的一次选择描述",
    "keyword": "3-5字的玩家风格关键词",
    "total_interactions": {total_interactions},
    "unlocked_plots": {len(unlocked_plots)}
  }}
}}"""
