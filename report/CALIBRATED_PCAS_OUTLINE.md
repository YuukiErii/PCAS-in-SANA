# Calibrated PCAS：当前问题与下一步研究大纲

## 1. 当前 PCAS 的问题

当前报告中的 PCAS 已经证明了一个核心现象：原始 SANA 固定 20-step 推理并不总是最优，Balanced-PCAS 可以在保持 CLIPScore 基本不变的前提下显著降低平均推理时间。但现有方法仍然比较规则化，主要存在以下问题。

### 1.1 复杂度估计过粗

Rule-PCAS 主要依赖 prompt 长度或分组，默认 10-word、30-word、50-word 分别对应低、中、高复杂度。但 prompt 难度并不完全由词数决定。短 prompt 也可能包含文字渲染、稀有概念或困难构图；长 prompt 也可能只是冗长描述。

### 1.2 LLM 标签没有校准

DeepSeek-PCAS 能提供语义复杂度判断，但原始 low/medium/high 标签直接映射到 steps 后过于保守，导致平均 steps 和推理时间上升。说明“复杂度标签”和“采样动作”不能简单绑定，需要用实验结果校准。

### 1.3 缺少最小充分预算概念

当前策略只比较固定 steps 或手工 steps 组合，没有系统回答：对每个 prompt 而言，达到 Fixed-20 质量附近所需的最小 steps 是多少。

### 1.4 优化目标不够明确

Balanced-PCAS 实际上隐含了“尽量加速，同时保持质量接近”的目标，但还没有形式化为约束优化问题，也没有明确质量容忍阈值。

### 1.5 难以泛化到真实 prompt 分布

规则策略在当前 30 条 benchmark 上有效，但如果 prompt 分布变化，手工 8/16/24 policy 未必仍然最优。

## 2. Calibrated PCAS 的核心思路

Calibrated PCAS 的目标是把现有 PCAS 从“手工规则调度”升级为“经过实验校准的推理预算预测器”。核心问题可以定义为：

> 对每个 prompt，预测在质量接近 Fixed-20 的前提下所需的最小采样步数。

形式化目标：

```math
\min_{\pi} \mathbb{E}_{p \sim D}[T(\pi(p))]
```

约束为：

```math
Q(\pi(p)) \geq Q(\text{Fixed-20}, p) - \epsilon
```

其中：

- `p` 表示 prompt；
- `π(p)` 表示自适应策略输出的 steps/guidance；
- `T` 表示推理时间；
- `Q` 表示质量指标；
- `ε` 表示允许的质量下降阈值。

## 3. 方法设计大纲

### 3.1 构建 calibration dataset

对每条 prompt 运行多个采样步数，例如：

```text
steps ∈ {8, 12, 16, 20, 24, 28}
```

每个 step 记录：

- 生成时间；
- CLIPScore；
- 图像路径；
- seed；
- 峰值显存；
- 完整配置。

### 3.2 定义最小充分 steps 标签

以 Fixed-20 作为参考，对每个 prompt 找到最小的 step `s*`，使得：

```text
CLIPScore(s*) >= CLIPScore(Fixed-20) - epsilon
```

`epsilon` 可以先设为 `0.1` 或 `0.2`。最终得到标签：

```text
prompt -> minimal_sufficient_steps
```

### 3.3 提取复杂度特征

为每个 prompt 提取结构化特征：

```text
word_count
object_count
attribute_count
relation_count
spatial_relation_count
action_count
style_constraint_count
text_rendering_flag
scene_density_score
rare_concept_score
```

特征可以用两种方式获得：

- 规则解析：基于词数、介词、逗号、常见对象词、风格词、文字渲染关键词等；
- LLM JSON：让 DeepSeek 或其他 LLM 输出结构化复杂度描述。

一个可能的 LLM 输出格式：

```json
{
  "objects": 5,
  "relations": 4,
  "text_rendering": true,
  "scene_density": "high",
  "style_constraints": 3,
  "estimated_difficulty": 0.82
}
```

### 3.4 训练轻量预测器

输入 prompt 特征，输出最小充分 steps。可选模型包括：

```text
decision tree
random forest
gradient boosting
ridge/logistic regression
small MLP
```

课程项目里优先推荐 decision tree 或 random forest，因为它们可解释性强，也更适合小规模数据。

### 3.5 生成 Calibrated-PCAS policy

预测器输出连续或离散 steps 后，映射到允许集合：

```text
predicted_steps ∈ {8, 12, 16, 20, 24}
```

guidance scale 可以暂时固定，也可以后续做联合策略：

```text
simple prompt: steps=8/12, guidance=4.0
medium prompt: steps=16, guidance=4.5
hard prompt: steps=20/24, guidance=5.0
```

### 3.6 评估 Calibrated-PCAS

与以下方法比较：

```text
Fixed-10
Fixed-20
Fixed-28
Rule-PCAS
Balanced-PCAS
DeepSeek-Balanced
Calibrated-PCAS
```

核心指标：

```text
average latency
average steps
CLIPScore delta vs Fixed-20
percentage of prompts satisfying quality constraint
speedup vs Fixed-20
hard prompt failure cases
```

## 4. 预期贡献

Calibrated PCAS 可以把当前报告的贡献推进一步：

1. 从词数规则走向结构化复杂度估计。
2. 从手工 policy 走向数据校准 policy。
3. 从“平均 CLIPScore 接近”走向“每个 prompt 尽量满足 Fixed-20 质量约束”。
4. 从经验调参走向明确的效率-质量约束优化。
5. 保持不训练 SANA 主模型的优势，只增加一个轻量级推理调度器。

## 5. 新对话任务说明

建议在新对话中直接使用如下任务说明：

> 请基于当前 SANA 项目实现 Calibrated PCAS。目标是构建 calibration dataset，对每个 prompt 在 `steps={8,12,16,20,24,28}` 下生成结果，计算相对 Fixed-20 的最小充分 steps 标签，提取 prompt 复杂度特征，训练一个可解释的轻量预测器，并与 Fixed-20、Balanced-PCAS、DeepSeek-Balanced 比较速度与 CLIPScore。最终更新报告中的方法、实验和讨论部分。
