# P0：Flags 语义状态系统 — 设计方案

> 参考来源：https://github.com/Shanyin-ai/Story-to-game
> 整理时间：2026-05-13
> 状态：待实现

---

## 问题

`rooms.unlocked_plots_json` 只存节点 ID（如 `["act1_node1"]`），AI 无法感知玩家做了什么选择，每幕生成的剧情与上一幕的选择脱节。

---

## 目标

给每个关键选择绑定一个有语义的 flag 字符串，存入数据库，并在 AI prompt 中注入，让 AI 知道"这个玩家走的是哪条路"。

---

## 数据结构

### 新增数据库字段

```sql
ALTER TABLE rooms ADD COLUMN flags_json TEXT NOT NULL DEFAULT '[]';
```

`flags_json` 存字符串数组，例如：
```json
["chose_adopt_peiyan", "given_snack_to_peiyan", "accepted_emperor_visit"]
```

`unlocked_plots_json` 保留不动（记节点 ID，用于其他逻辑）。

### Flag 命名规范

格式：`动词_宾语_[角色]`，英文小写下划线。

| Flag | 触发时机 |
|---|---|
| `chose_adopt_peiyan` | 选 A：欣然应允抚育裴琰 |
| `hesitated_adopt` | 选 B：犹豫试探 |
| `refused_adopt` | 选 C：婉言拒绝 |
| `given_snack_to_peiyan` | act2 选 A：做枣花糕 |
| `sewn_clothes_for_peiyan` | act2 选 B：缝补冬衣 |
| `accepted_emperor_visit` | act3 接受皇帝驾临 |

---

## 改动清单（共 4 个文件，约 30 行新代码）

### 1. `database.py`
- `init_db()` 里加 `flags_json` 字段
- 用 `try/except` 包住 `ALTER TABLE`，兼容已有数据库

### 2. `mock_data.py`
- 每个选项加 `add_flags: list[str]` 字段
- 例：`{ "id": "A", "text": "...", "add_flags": ["chose_adopt_peiyan"] }`

### 3. `routers/interactive.py`
- `/generate` 接口：读取 `last_choice`，找到对应选项的 `add_flags`，写入 DB
- `/input` 接口：读取 `flags_json` 传给 prompt（自由输入暂不写入新 flag）

### 4. `prompts/generate_plot.py`
- `build_user_prompt()` 加 `flags: list = []` 参数
- prompt 里加一行：`已发生的关键事件：{flags_text}`

---

## 数据流（改后）

```
玩家选择 A：欣然应允
    ↓
前端 POST /generate { last_choice: { node_id: "act1_node1", selected: "A" } }
    ↓
后端：选项 A → add_flags: ["chose_adopt_peiyan"] → 写入 DB
    ↓
下次生成剧情：prompt 包含 "已发生的关键事件：chose_adopt_peiyan"
    ↓
AI 感知到选择，生成对应情节
```

---

## 后续扩展（P1 依赖此基础）

- **结局判断**：`settle` 时根据 flags 组合精确匹配结局类型，不再靠 AI 猜
- **成就系统**：每个 flag 触发时可解锁对应成就
- **自由输入触发 flag**：AI 返回结果里加 `add_flags` 字段，处理自由回复的语义记录
