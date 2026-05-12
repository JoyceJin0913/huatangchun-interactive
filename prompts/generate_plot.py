from typing import Optional

WORLD_BACKGROUND = """时代背景：架空封建王朝后宫，皇权至上，等级森严。
核心人物：温棠（温贵人，心软隐忍）、裴容（皇帝，理性凉薄）、裴琰（三皇子，早熟知恩）、裴瑜（四皇子，骄纵傲慢）。
核心规则：温棠不可黑化，裴容不可过度宠爱，剧情不偏离原著基调。"""

def build_system_prompt() -> str:
    return f"""你是《画堂春》互动文游的剧情生成引擎。
{WORLD_BACKGROUND}
输出要求：
1. 严格按 JSON 格式输出，不输出任何 JSON 外的内容
2. plot_html 为剧情叙述，≤300字，用古言风格，支持 <p> 标签
3. next_node 的 type 只能是 single_choice、free_input、cutscene 之一
4. intimacy_delta 只包含本段剧情影响到的角色
5. system_message 简洁，≤20字"""

def build_user_prompt(
    act_id: int,
    characters: list,
    last_choice: Optional[dict],
    intimacy: dict,
    unlocked_plots: list,
    history_summary: str,
) -> str:
    char_info = "\n".join(
        f"- {c['name']}（{c['id']}）：{'、'.join(c['personality'])}" for c in characters
    )
    choice_text = (
        f"玩家上一个选择：节点 {last_choice['node_id']}，选择了 {last_choice['selected']}"
        if last_choice
        else "这是本幕开始，尚无选择记录"
    )
    intimacy_text = "、".join(f"{k}亲密度{v}" for k, v in intimacy.items())

    return f"""当前状态：
- 第 {act_id} 幕
- 角色列表：
{char_info}
- {choice_text}
- 当前亲密度：{intimacy_text}
- 已解锁剧情：{', '.join(unlocked_plots) if unlocked_plots else '无'}
- 对话历史摘要：{history_summary if history_summary else '无'}

请生成下一段剧情，严格按以下 JSON 输出：
{{
  "plot_html": "<p>剧情内容</p>",
  "next_node": {{
    "node_id": "节点id",
    "type": "single_choice 或 free_input 或 cutscene",
    "prompt": "展示给玩家的问题"
  }},
  "intimacy_delta": {{"角色id": 变化值}},
  "system_message": "系统提示（≤20字）"
}}"""
