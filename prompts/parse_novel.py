SYSTEM_PROMPT = """你是一个专业的小说改编助手，擅长将古言小说改编为互动剧本杀格式。
请严格按照 JSON 格式输出，不要输出任何 JSON 以外的内容。"""

def build_user_prompt(novel_id: str, content: str) -> str:
    return f"""请解析以下小说内容，提取角色信息和分幕剧情，严格按照以下 JSON schema 输出：

{{
  "novel_id": "{novel_id}",
  "characters": [
    {{
      "id": "角色英文id（小写字母）",
      "name": "角色中文名",
      "role": "角色类型",
      "personality": ["性格标签1", "性格标签2"],
      "skills": ["技能1", "技能2"],
      "initial_intimacy": 亲密度初始值(0-100整数)
    }}
  ],
  "acts": [
    {{
      "act_id": 幕次编号(整数),
      "title": "幕次标题",
      "content_html": "<p>幕次内容</p>",
      "nodes": [
        {{
          "node_id": "act编号_node编号",
          "type": "single_choice 或 free_input",
          "trigger": "触发条件描述",
          "prompt": "向玩家展示的问题或情境",
          "options": [
            {{
              "id": "A",
              "text": "选项文字",
              "intimacy_delta": {{"角色id": 变化值}}
            }}
          ]
        }}
      ]
    }}
  ]
}}

要求：
- 提取核心角色，最多6个
- 分为3幕，每幕内容≤1000字
- 每幕设置2-3个互动节点
- free_input 类型的节点 options 为空数组 []

小说内容：
{content}"""
