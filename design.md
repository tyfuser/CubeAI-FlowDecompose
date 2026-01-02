# CubeAI – Generative Video Coach
## Reference-based Director Agent Architecture (Implementation Spec)
> 本文档描述 CubeAI 在 **不训练新模型** 的前提下，
> 如何通过 **参考资料库（Reference Library）+ 多模态大模型决策**，
> 实现“像导演一样实时指导普通人拍视频”的系统。
---

## 1. 核心设计共识（必须遵守）

### 1.1 Reference Library 的定位

* Reference Library **不是规则系统**
* Reference Library **不是约束引擎**
* Reference Library 是：

  > **供多模态大模型在决策时检索的“经验记忆 / 案例库”**

📌 **所有“要不要用 / 什么时候用 / 用多少”的决策，全部由 MLLM 完成。**

---

### 1.2 系统中只有一个“做决定的角色”

* ✅ **Director Agent（多模态大模型）**：
  负责判断当前拍摄状态 → 决定下一步拍摄意图
* ❌ 不存在：

  * 规则引擎自动触发运镜
  * Reference 卡片直接驱动 UI
  * 固定 SOP / 时间轴脚本

---

## 2. 整体工作流（高层）

```text
Reference Library (经验卡片)
        ↓ (检索)
Director Agent (MLLM 决策)
        ↓ (结构化 Action)
UI / AR Layer (执行 + 插值)
        ↓
Camera State Update
        ↓ (回馈)
Director Agent (Plan → Act → Critique)
```

这是一个 **闭环导演调度系统**，不是一次性推理。

---

## 3. Reference Library 设计（核心）

### 3.1 为什么不用“参数拆解”

* 参数（速度、角度、时间）在真实拍摄中不可复用
* 创作是情境驱动的，不是数值驱动的

👉 **Reference Library 存的是“经验模式”，不是“执行参数”**

---

### 3.2 Reference Card 类型（MVP 版）

#### 3.2.1 Intent Card（意图卡）【最重要】

> 描述“这类镜头想让观众感觉什么”

```json
{
  "id": "intent_gentle_cat",
  "type": "intent",
  "audience_feel": ["gentle", "affectionate", "calm"],
  "used_when": ["pets", "quiet_subject"],
  "avoid": ["sudden_speed", "violent_movement"]
}
```

---

#### 3.2.2 Signature Move Card（打法卡）

> 描述“老导演在类似情况下常用的解决方式”

```json
{
  "id": "move_slow_push",
  "type": "signature_move",
  "description": "Very slow forward approach",
  "works_best_when": [
    "subject_is_calm",
    "camera_is_stable"
  ],
  "variants": [
    "pure_forward",
    "forward_with_micro_reframe"
  ],
  "why_it_works": "Feels natural and non-intrusive"
}
```

---

#### 3.2.3 Adapter Card（现场适配）

> 当原方案不可执行时，如何保持“意图不变”换招

```json
{
  "id": "adapter_subject_moves",
  "type": "adapter",
  "problem": "subject moves unexpectedly",
  "alternative_moves": [
    "stop_and_hold",
    "reframe_without_moving"
  ],
  "keep_intent": "gentle"
}
```

---

#### 3.2.4 Failure Pattern Card（失败经验）

> 用于 Director 自我纠偏（Critique）

```json
{
  "id": "failure_shaky",
  "type": "failure_pattern",
  "symptom": "footage looks amateur",
  "possible_causes": ["camera_shake", "too_fast"],
  "fix_directions": ["slow_down", "hold_position"]
}
```

---

### 3.3 Reference Library 的规模建议

* Demo / MVP：

  * 3–5 个 Intent
  * 每个 Intent 2–3 个 Signature Move
  * 每个 Intent 1 个 Adapter
* 总量 **< 30 张卡片即可非常有效**

---

## 4. Director Agent（决策核心）

### 4.1 Director Agent 的职责

Director Agent 是一个 **高层决策者**，而不是控制器。

它负责：

* 理解当前拍摄状态（State）
* 从 Reference Library 中检索相关经验
* 决定 **下一步 0.5–1 秒的拍摄意图**
* 输出 **结构化 Action**

它不负责：

* 连续控制（插值）
* 每帧数值计算
* UI 绘制细节

---

### 4.2 输入给 Director Agent 的 State（极简）

```json
{
  "camera_motion": {
    "speed": "none | slow | medium | fast",
    "direction": "forward | lateral | rotate | none"
  },
  "stability": "stable | slightly_shaky | shaky",
  "subject": {
    "centered": true,
    "distance": "far | medium | close"
  }
}
```

📌 **State 可以是估计值，不要求高精度。**

---

### 4.3 Director Agent 输出的 Action Schema

```json
{
  "action": "hold | move_forward | move_lateral | reframe | slow_down | speed_up",
  "intention": "human-readable intention",
  "ui_hint": "arrow / speed_bar / center_mask",
  "dialogue": "short coaching sentence",
  "reason": "brief reasoning for debugging"
}
```

📌 **Action 是离散的、高层的**
连续效果由前端插值完成。

---

### 4.4 Director Agent System Prompt（关键约束）

必须明确告诉模型：

```text
The reference cards are NOT rules.
They are memories from past experience.

You may:
- Combine them
- Modify them
- Ignore them

Your goal is to achieve the intended feeling,
not to replicate exact movements.
```

---

## 5. 决策模式：Plan → Act → Critique

### 5.1 决策是循环的，不是一次性的

* 每 0.5–1 秒：

  1. 看当前 State
  2. 参考经验
  3. 输出下一步 Action

### 5.2 Critique（自我修正）

* 定期将：

  * 当前 State
  * 上一个 Action
* 回喂 Director Agent

让模型回答：

* 是否继续
* 是否微调
* 是否换招（Adapter / 新 Signature Move）

📌 这是“灵活感”的核心来源。

---

## 6. UI / AR Layer（执行层原则）

### 6.1 UI 是“导演意图的可视化”

UI 不做决策，只执行：

| Action       | UI 表现      |
| ------------ | ---------- |
| move_forward | 前进箭头 + 速度条 |
| hold         | 无箭头 + 稳定提示 |
| reframe      | 中心框 / 构图蒙版 |
| slow_down    | 速度条回缩 + 提示 |

---

### 6.2 连续控制由前端完成

* ease-in / ease-out
* 插值
* 抖动平滑

❌ 不要让 LLM 控制连续值

---

## 7. Demo 场景：爸爸拍小猫（参考实现）

### 7.1 Demo Intent

* Intent: `gentle_affectionate_approach`
* 目标：

  * 稳定
  * 不惊扰
  * 亲近感

### 7.2 Demo 成功标准

* 爸爸不需要懂摄影
* AI 会主动让他：

  * 停下来
  * 放慢
  * 稳住
* 而不是“强行推进”

---

## 8. 为什么这套方案可行（工程结论）

* 不训练新模型
* 不依赖复杂 CV
* 利用 MLLM 最擅长的能力：

  * 语义理解
  * 案例类比
  * 情境决策
* 通过结构化输入/输出，让系统 **可控、可调试、可演示**

---

## 9. 一句话总结（可写在 README）

> CubeAI does not teach users camera parameters.
> It gives AI the experience of a director,
> and lets the model decide what to do next in real time.

---

一、 产品核心定义
产品名称： CubeAI
核心功能：生成式视频教练 (Generative Video Coach) / 酷点拆解与迁移 (Cool Point Breakdown & Transfer) 
一句话价值： 把大师的“审美”拆解为小白能懂的“AR 辅助线”，并用 AI 将用户的拙劣实拍“渲染”成电影级大片。
核心差异化：
- 非单纯分析： 不止给报告，而是给工具（AR）和结果（AIGC）。
- 非单纯滤镜： 介入拍摄阶段的物理运镜指导，解决“原始素材太烂”的根本问题。

---
二、 技术架构共识：
我们放弃了堆砌复杂的传统 CV 模型，确立了以 多模态大模型 (MLLM) 为大脑，WebAR 为手眼的轻量化架构。
第一层：拆解层 (The Breakdown) —— “大脑”
- 任务： 从参考视频中提取“施工图纸”。
- 共识技术路线： One-Model-All-In (GPT-4o / Gemini)。
- 核心动作：
  - 不使用复杂的 CoTracker/SAM 2。
  - 通过 System Prompt 让大模型扮演“摄影指导”  “AR 工程师”。多agent合作工作流。
  - 利用 CoT (思维链) 先思考后输出，保证逻辑准确。
第二层：交互层 (The Interaction) —— “手眼”
- 任务： 解决用户“不知道怎么拍”的问题 。
- 共识技术路线： Mobile Web (H5) + 伪 AR。
- 核心动作：
  - 构图辅助： 屏幕显示半透明蒙版（如中心框），基于拆解出的 JSON 数据 (5)。
  - 运镜导航： 屏幕显示动态箭头和速度条。基于手机传感器或简单的光流判断，如果不达标就弹出大模型生成的“教练喊话”。
- 价值： 保证用户拍出的原始素材在物理轨迹上是及格的。
---
三、 黑客松演示故事线 (Demo Flow)
1. 痛点展示 (10s)： 展示一段普通人手抖、构图乱的视频。“这就是我们拍出来的东西，完全不酷。”
2. AI 拆解 (30s)：
  - 上传一个“大神级”参考视频。
  - 后台大屏展示 AI 的 JSON 思考过程（炫技点：展示 AI 像导演一样分析运镜意图）。
3. AR 实拍 (60s)：
  - 真机演示 H5 界面。
  - 关键交互： 屏幕上出现箭头，队友跟着箭头走。
  - 反馈： 故意走慢点，展示 AI 弹窗骂人：“太慢了！冲起来！”（体现“教练感”）。
4. AIGC 魔法 (30s)：
  - 点击“生成优化”。
  - 展示对比：左边是刚才的实拍，右边是融合了参考风格和加强运镜的最终大片。
  - 结论： “我们没有训练模型，但 AI 仿佛学会了这种风格。”


Node（核心）
session 管理
Reference cards 存储/检索
Director/Coach agent 调用
WebSocket 推送 action
上传/结果 URL 管理
缓存、超时、降级（hold/slow_down）
Python（可选旁路）
抽帧 / 关键帧挑选（ffmpeg）
简单稳定/滤镜处理（demo 级也行）
后续真要上光流/深度等再说