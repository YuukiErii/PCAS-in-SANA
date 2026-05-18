# DAY6 补充：Calibrated PCAS

## 1. 动机

现有 Balanced-PCAS 证明固定 20-step 推理存在冗余，但它仍是手工规则：10/30/50-word prompt 固定映射到 8/16/24 steps。Calibrated PCAS 的目标是把这个策略进一步数据化：先对每条 prompt 在多档 steps 下实际生成结果，再用相对 Fixed-20 的 CLIPScore 约束定义每条 prompt 的最小充分采样步数。

本文使用的 calibration grid 为：

```text
steps = {8, 12, 16, 20, 24, 28}
reference = Fixed-20
epsilon = 0.2 CLIPScore
```

最小充分 steps 标签定义为：

```text
s* = min{s | CLIPScore(s) >= CLIPScore(Fixed-20) - 0.2}
```

## 2. Calibration Dataset

对 30 条 benchmark prompt 共生成 180 张图像，并记录生成时间、CLIPScore、seed、显存和完整 metadata。得到的最小充分 steps 分布如下：

| Minimal sufficient steps | Prompts |
| ---: | ---: |
| 8 | 18 |
| 12 | 4 |
| 16 | 6 |
| 20 | 2 |

这个分布说明，在当前 30 条 prompt 和 CLIPScore 容忍阈值下，很多 prompt 并不需要 Fixed-20 才能达到相近自动文本对齐指标。但这也暴露出 CLIPScore 的非单调性：更多 steps 不一定带来更高 CLIPScore，因此 policy 不能简单地认为“预测更高 steps 一定更安全”。

## 3. Prompt Features

Rule-feature 版本使用可复现的文本解析特征：

```text
word_count, content_word_count, comma_count,
object_count, attribute_count, relation_count,
spatial_relation_count, action_count, style_constraint_count,
text_rendering_flag, scene_density_score, rare_concept_score,
lexical_complexity_score, rule_complexity_score
```

同时补充了 DeepSeek JSON feature 版本。DeepSeek 输出对象数、属性数、关系数、动作数、场景密度、稀有概念分数和 estimated difficulty 等字段。本次 30 条 prompt 的 LLM difficulty 分布为：

| LLM difficulty | Prompts |
| --- | ---: |
| low | 10 |
| medium | 7 |
| high | 13 |

## 4. Predictor

轻量预测器使用纯 Python 实现的可解释 decision tree，不依赖 scikit-learn。目标标签是 `minimal_sufficient_steps`，输出映射到 calibration grid 中可用的 steps。最终使用 `max_depth=5, min_samples_leaf=1`，主要是因为当前数据只有 30 条，较浅的树会明显欠拟合并漏掉约束。

Rule-feature tree 的留一诊断：

| Metric | Value |
| --- | ---: |
| exact label accuracy | 40.0% |
| under-budget rate | 30.0% |
| over-budget rate | 30.0% |

LLM-feature tree 的留一诊断：

| Metric | Value |
| --- | ---: |
| exact label accuracy | 43.3% |
| under-budget rate | 30.0% |
| over-budget rate | 26.7% |

## 5. Main Results

下表使用当前 worktree 中重跑的 Fixed-20、Balanced-PCAS、DeepSeek-Balanced、Calibrated-PCAS 和 LLM-feature Calibrated-PCAS。需要注意，本轮 wall-clock latency 存在一定波动，因此应同时看 average steps、CLIPScore delta 和 constraint satisfaction。

| Method | Avg steps | Avg time no-warmup | Speedup vs Fixed-20 | Avg CLIPScore | CLIP delta | Satisfaction |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Fixed-20 | 20.000 | 1.537s | 0.0% | 35.762 | 0.000 | 100.0% |
| Balanced-PCAS | 16.000 | 1.740s | -13.2% | 35.772 | 0.010 | 73.3% |
| DeepSeek-Balanced | 18.467 | 2.023s | -31.6% | 35.813 | 0.051 | 73.3% |
| Oracle minimum | 10.933 | 1.112s | 27.6% | 36.276 | 0.513 | 100.0% |
| Calibrated-PCAS | 10.667 | 0.675s | 56.1% | 36.234 | 0.472 | 96.7% |
| LLM-feature Calibrated-PCAS | 11.333 | 1.093s | 28.9% | 36.230 | 0.467 | 96.7% |

Calibrated-PCAS 的主要优势不是平均 CLIPScore 本身更高，而是它把目标从“平均值接近”推进到“每条 prompt 尽量满足 Fixed-20 约束”。在当前阈值下，rule-feature 和 LLM-feature 版本都达到 96.7% constraint satisfaction，明显高于 Balanced-PCAS 和 DeepSeek-Balanced 的 73.3%。

## 6. Interpretation

Calibrated-PCAS 将 PCAS 从手工 policy 推进为数据校准 policy。它显式回答了“每条 prompt 到 Fixed-20 附近需要多少 steps”这个问题，并用一个可解释决策树近似 oracle 最小预算。

同时需要保守解释：

- 数据只有 30 条，decision tree 有小样本过拟合风险。
- CLIPScore 对局部结构和视觉质量不敏感，而且对 steps 并不单调。
- LLM features 提供了更丰富语义特征，但当前相对 rule features 没有稳定拉开差距。
- Balanced-PCAS 的原 Day3 结果仍是主报告中稳定的效率基线；Day6 calibrated 结果更像进一步研究扩展。

## 7. Key Files

- `src/run_sana_calibration_grid.py`
- `src/build_calibration_dataset.py`
- `src/prompt_features.py`
- `src/prompt_features_deepseek.py`
- `src/train_calibrated_pcas_predictor.py`
- `src/run_sana_calibrated_pcas.py`
- `configs/day6_calibrated_pcas.yaml`
- `results/day6_calibration_labels.csv`
- `results/day6_deepseek_prompt_features.csv`
- `results/day6_calibrated_pcas_summary.md`
- `results/day6_calibrated_pcas_llm_features_summary.md`
