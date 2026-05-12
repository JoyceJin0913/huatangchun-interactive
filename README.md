# 画堂春 · 互动文游

基于《画堂春》的 AI 驱动后宫互动小说游戏。玩家扮演温棠或裴琰，在宫廷倾轧中做出选择，影响亲密度与结局走向。

---

## 快速启动

### 环境要求

- Python 3.10+
- DeepSeek API Key

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env`，填入：

```
DEEPSEEK_API_KEY=sk-xxxxxxxx
DB_PATH=novel.db
```

### 3. 初始化数据库 + 写入 Demo 数据

```bash
python init_demo.py
```

输出示例：
```
✅ 数据库架构已初始化
✅ 小说数据写入成功
✅ 房间数据写入成功
✅ Demo 数据已准备完毕！
```

### 4. 启动服务

```bash
uvicorn main:app --reload --port 8000
```

### 5. 打开前端

用浏览器直接打开 `frontend.html`，或：

```bash
open frontend.html
```

> **注意**：从 `file://` 访问本地服务器可能触发 CORS，建议用 `python3 -m http.server 3000` 在本地起一个 HTTP 服务来托管 HTML 文件。

---

## 项目结构

```
.
├── main.py                  # FastAPI 入口
├── database.py              # SQLite 初始化与连接
├── mock_data.py             # Demo 角色、幕次、选项数据
├── init_demo.py             # 一键写入 Demo 数据
├── ai_client.py             # DeepSeek API 封装
├── frontend.html            # 纯 HTML 前端（无构建步骤）
├── routers/
│   ├── interactive.py       # 核心游戏接口
│   ├── room.py              # 结算接口
│   └── novel.py             # 小说解析接口
├── prompts/
│   ├── generate_plot.py     # 剧情生成 prompt
│   ├── handle_input.py      # 自由输入处理 prompt
│   └── settle_ending.py     # 结局生成 prompt
├── docs/
│   ├── 设计参考-Story-to-game学习笔记.md
│   └── P0-flags-设计方案.md
└── tests/
```

---

## 核心 API

### `POST /interactive/generate`

生成下一段剧情，适用于幕次推进和单选节点。

**Request**

```json
{
  "room_id": "demo_room_001",
  "act_id": 1,
  "characters": ["wentang", "peiyan", "peirong"],
  "last_choice": {
    "node_id": "act1_node1",
    "selected": "A"
  },
  "intimacy": { "peiyan": 50, "peirong": 30, "peiyu": 20 },
  "unlocked_plots": [],
  "user_character_id": "wentang"
}
```

| 字段 | 说明 |
|---|---|
| `room_id` | 房间 ID，Demo 固定用 `demo_room_001` |
| `act_id` | 当前幕次（1 起始） |
| `last_choice` | 上一个选择，首次调用时省略 |
| `user_character_id` | 可玩角色：`wentang`（温棠）或 `peiyan`（裴琰） |

**Response**

```json
{
  "plot_html": "<p>雪夜，皇帝驾临采桑宫……</p>",
  "next_node": {
    "node_id": "act1_node1",
    "type": "single_choice",
    "prompt": "裴容沉声问道：「想不想抚育三皇子？」",
    "options": [
      { "id": "A", "text": "欣然应允", "intimacy_delta": {"peiyan": 15} },
      { "id": "B", "text": "犹豫试探", "intimacy_delta": {"peiyan": 5} }
    ]
  },
  "intimacy_delta": { "peiyan": 5 },
  "system_message": "裴容驾临采桑宫"
}
```

| 字段 | 说明 |
|---|---|
| `plot_html` | 剧情正文，支持 `<p>` 标签 |
| `next_node.type` | `single_choice` / `free_input` / `cutscene` |
| `next_node.options` | 仅 `single_choice` 时存在，从静态数据注入 |
| `intimacy_delta` | 本段剧情引起的亲密度变化 |

---

### `POST /interactive/input`

处理玩家自由文字输入，返回角色回复。

**Request**

```json
{
  "room_id": "demo_room_001",
  "user_character_id": "wentang",
  "node_id": "act1_node2",
  "user_input": "我愿意留下来陪着琰儿"
}
```

**Response**

```json
{
  "character_reply": "<p>裴琰抬起头，眸中闪过一丝不确定……</p>",
  "emotion_tag": "动摇",
  "intimacy_delta": { "peiyan": 8 },
  "next_node": {
    "node_id": "act1_node2",
    "type": "free_input"
  }
}
```

| 字段 | 说明 |
|---|---|
| `character_reply` | 角色的回应文字 |
| `emotion_tag` | 角色当前情绪标签（可选） |

---

### `POST /room/settle`

结算游戏，生成结局与游戏报告。调用后房间状态变为 `settled`，不可再继续游戏。

**Request**

```json
{
  "room_id": "demo_room_001"
}
```

**Response**

```json
{
  "ending_type": "perfect",
  "ending_text": "<p>数年后，采桑宫的枣花糕香飘遍了整座宫城……</p>",
  "relationship_graph": [],
  "highlight_report": {
    "top_character": "裴琰",
    "best_choice": "欣然应允抚育琰儿",
    "keyword": "温柔守护",
    "total_interactions": 12,
    "unlocked_plots": 3
  }
}
```

| `ending_type` | 触发条件（当前逻辑） |
|---|---|
| `perfect` | 裴琰或裴容亲密度 ≥ 70 |
| `hidden` | 裴瑜亲密度 ≥ 60 |
| `regret` | 以上均不满足 |

---

### `POST /novel/parse`（可选）

上传小说原文，AI 解析为角色与幕次结构。Demo 阶段直接用 `init_demo.py` 写入静态数据，无需调用此接口。

---

## Demo 数据说明

| 字段 | 值 |
|---|---|
| `room_id` | `demo_room_001` |
| `novel_id` | `1725479677609644032` |
| 初始亲密度 | 裴琰 50 / 裴容 30 / 裴瑜 20 |
| 可玩角色 | 温棠（`wentang`）/ 裴琰（`peiyan`） |
| 剧情共 3 幕 | 雪夜承宠 → 抚育之诺 → 帝临采桑 |

重置 Demo（清空数据重新开始）：

```bash
rm novel.db && python init_demo.py
```

---

## 开发路线

| 优先级 | 任务 | 状态 |
|---|---|---|
| P0 | Flags 语义状态系统（让 AI 记住关键选择） | 📋 设计完成，待实现 |
| P1 | 结局判断改为 flag 条件精确匹配 | ⏳ 待做 |
| P1 | 顶栏进度条 | ⏳ 待做 |
| P2 | 对话段落加说话人标签 | ⏳ 待做 |
| P3 | 结局类型扩展（5-6 种） | ⏳ 待做 |

详见 `docs/P0-flags-设计方案.md`。
