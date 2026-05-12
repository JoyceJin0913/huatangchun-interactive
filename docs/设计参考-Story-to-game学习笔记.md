# 设计参考：Story-to-Game 学习笔记

> 来源：https://github.com/Shanyin-ai/Story-to-game
> 整理时间：2026-05-13
> 用途：为《画堂春》互动文游提供设计借鉴

---

## 一、他们在做什么

一个「AI-to-JSON-to-Engine」三层管道：

```
原始小说
  ↓  AI 提示词工程
JSON 剧本文件（自定义 DSL）
  ↓  HTML 单文件引擎
可玩的文字游戏
```

核心思路：**AI 负责创作，JSON 负责结构，引擎负责运行**。三者完全解耦。

---

## 二、最值得借鉴的 3 个设计

### 1. Flag + Val 双轨状态系统 ⭐⭐⭐

| 类型 | 数据类型 | 决定什么 |
|------|---------|---------|
| `val`（情感值） | 连续数值 0-100 | 文字细节、措辞语气 |
| `flags`（事件标记） | 布尔集合 | 结局走向、剧情分叉 |

**为什么重要：**
- 纯数值系统（只有亲密度）的问题：选了 A 和选了 B，后续 AI 感知不到区别，选择没有「语义记忆」
- Flag 是对关键叙事事件的永久烙印，比如「chose_adopt_peiyan」「rejected_emperor」

**我们现在缺什么：** 只有亲密度，没有 flags。关键选择没有被真正记住。

**结局设计原则：** 结局不依赖单一数值，而靠 **flag 组合** 触发——比如：
```
结局「母子情深」= flag:chose_adopt_peiyan AND peiyan_intimacy >= 70
结局「圣宠加身」= flag:accepted_emperor AND peirong_intimacy >= 60 AND NOT flag:refused_twice
```

---

### 2. routes（隐式跳转）vs choices（显式选项）分离 ⭐⭐

```json
// choices：玩家可见，主动做选择
"choices": [
  { "text": "欣然应允", "next": "act2_warm", "addFlag": "chose_adopt" }
]

// routes：玩家不可见，引擎自动按条件路由
"routes": [
  { "condition": { "flag": "chose_adopt", "var": "peiyan_intimacy >= 70" }, "next": "ending_perfect" },
  { "condition": "default", "next": "ending_normal" }
]
```

**为什么重要：** 结局分叉可以悄悄发生，不需要在最后一刻弹出奇怪的「你解锁了 XXX 结局」——玩家的路径在过程中就已经悄悄偏向了某个方向。

**对我们的启发：** 结局不应该只在 `/room/settle` 时由 AI 一次性判断，而是在整个游戏过程中，flags 已经决定了方向，最后只是揭晓。

---

### 3. 进度值与节点数量解耦 ⭐

每个节点有手动设置的 `progress: 0-100`，而不是「第几幕/总幕数」。

**效果：** 作者可以控制节奏——关键选择后进度条跳得慢，铺垫场景快速略过。玩家有节奏感但不知道剩多少内容，保持悬念。

---

## 三、我们 vs 他们的本质差异

| 维度 | Story-to-game | 我们（画堂春） |
|------|--------------|-------------|
| 剧情生成 | 人工写 JSON，AI 辅助 | 实时 AI 生成 |
| 状态记忆 | flags + 多维变量 | 亲密度数值 |
| 分支逻辑 | 确定性 DSL | AI 即兴推断 |
| 结局触发 | 条件组合精确匹配 | AI 一次性生成 |
| 可重玩性 | 高（路径确定，体验稳定） | 高（每次都不同） |

**两个方向都成立。** 他们的优势是叙事结构稳定可控；我们的优势是门槛低、每次体验不同。

---

## 四、可以落地的改进方向

### 短期（调试阶段）

**给数据库加 flags 表，记录关键叙事事件：**

```python
# 在 rooms 表里已有 unlocked_plots_json，可以扩展语义
# 把「解锁剧情」从纯 node_id 列表升级为「带语义的 flag 集合」

# 比如：
flags = [
  "chose_adopt_peiyan",   # 答应抚育裴琰
  "given_snack_to_peiyan", # 给裴琰做了枣花糕
  "accepted_emperor_visit" # 接受了皇帝驾临
]
```

**把 flags 传给 AI 生成接口：** 在 `build_user_prompt` 里加入 flags 上下文，让 AI 知道玩家走过哪条路，生成对应语气的剧情。

### 中期（版本迭代）

- **结局判断逻辑前移**：不在最后让 AI 猜结局，而是根据 flags 组合预先定义 3-5 个结局条件，settle 时做精确匹配
- **进度条**：给 3 幕加手动 progress 值（act1=0~30, act2=30~65, act3=65~100），显示在顶栏
- **成就系统**：每个 flag 触发时解锁一个成就（比如「第一次给裴琰做糕点」），增加收集感

### 长期（产品化）

- **条件 DSL**：把结局判断从硬编码变成可配置的条件表达式，支持 `all/any/not` 嵌套
- **作者工具**：上传小说 → AI 自动提取关键事件 → 生成 flags 体系建议

---

## 五、他们的 JSON Schema 精华（备用参考）

```json
{
  "meta": { "title": "...", "variableName": "信任度" },
  "variables": { "intimacy_peiyan": 50, "intimacy_peirong": 30 },
  "nodes": {
    "act1_node1": {
      "progress": 15,
      "segments": [
        { "text": "裴容放下书卷……", "speaker": "旁白" },
        { "text": "「朕问你，想不想抚育三皇子？」", "speaker": "裴容" }
      ],
      "choices": [
        {
          "text": "欣然应允",
          "next": "act1_node2",
          "changes": { "intimacy_peiyan": 15, "intimacy_peirong": 10 },
          "addFlag": "chose_adopt_peiyan"
        }
      ]
    },
    "ending_perfect": {
      "isEnding": true,
      "routes": [
        {
          "condition": {
            "all": [
              { "flag": "chose_adopt_peiyan" },
              { "var": "intimacy_peiyan", "op": ">=", "value": 70 }
            ]
          },
          "next": "ending_perfect"
        }
      ]
    }
  }
}
```

---

*下次调试时可以从「给 flags 加进数据库」开始，改动不大但对叙事深度提升很明显。*
