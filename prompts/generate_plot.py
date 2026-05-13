from typing import Optional

WORLD_BACKGROUND = """时代背景：架空封建王朝后宫，皇权至上，等级森严。
核心人物：温棠（温贵人，心软隐忍）、裴容（皇帝，理性凉薄）、裴琰（三皇子，早熟知恩）、裴瑜（四皇子，骄纵傲慢）。
核心规则：温棠不可黑化，裴容不可过度宠爱，剧情不偏离原著基调。"""

# 每个可玩角色的叙事视角与目标
CHARACTER_NARRATIVE = {
    "wentang": {
        "pov": "温棠",
        "goal": "在宫廷倾轧中以善良与隐忍守护裴琰，同时赢得裴容的信任，求得一份安稳与认可",
        "style": "旁观者视角，感受细腻，语气温柔克制，在意他人情绪，善用生活细节（枣花糕、针线）传递温情",
    },
    "peiyan": {
        "pov": "裴琰",
        "goal": "从警惕的观察者到真心依赖温棠，在察言观色中学会信任，守护那个第一次真正疼他的人",
        "style": "孩童视角，早熟敏锐，善于察言观色，内心独白多于言辞，行动往往比话语更能表达心意",
    },
}

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
    user_character_id: str = "wentang",
    flags: list = [],
) -> str:
    char_info = "\n".join(
        f"- {c['name']}（{c['id']}）：{'、'.join(c['personality'])}" for c in characters
    )
    choice_text = (
        f"玩家上一个选择：节点 {last_choice['node_id']}，选择了「{last_choice.get('text') or last_choice['selected']}」"
        if last_choice
        else "这是本幕开始，尚无选择记录"
    )
    intimacy_text = "、".join(f"{k}亲密度{v}" for k, v in intimacy.items())
    flags_text = "、".join(flags) if flags else "无"

    # 注入当前玩家角色的叙事视角
    narrative = CHARACTER_NARRATIVE.get(user_character_id, CHARACTER_NARRATIVE["wentang"])
    pov_text = (
        f"当前玩家扮演角色：{narrative['pov']}\n"
        f"角色叙事目标：{narrative['goal']}\n"
        f"叙事风格：{narrative['style']}"
    )

    # 注意：next_node 不含 options 字段，single_choice 的选项由调用方从 DEMO_ACTS 静态数据中注入
    return f"""当前状态：
- 第 {act_id} 幕
- 角色列表：
{char_info}
- {pov_text}
- {choice_text}
- 当前亲密度：{intimacy_text}
- 已发生的关键事件（flags）：{flags_text}
- 已解锁剧情：{', '.join(unlocked_plots) if unlocked_plots else '无'}
- 对话历史摘要：{history_summary if history_summary else '无'}

请以【{narrative['pov']}】的视角生成下一段剧情，严格按以下 JSON 输出：
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
