# DAY3 补充：DeepSeek-PCAS 的预算约束版本

## 问题动机

原始 DeepSeek-PCAS 7.3 的出发点是使用 LLM 对 prompt 进行语义复杂度分析，而不是只依赖词数。DeepSeek 会估计对象数量、关系数量、风格约束和文字生成需求，并输出 low / medium / high 三类复杂度。该方法更符合“语义复杂度估计”的目标，但原始策略过于保守：low / medium / high 分别对应 10 / 20 / 28 steps。

在当前 30 条 benchmark 中，DeepSeek 将 19 条 prompt 判为 high，6 条判为 medium，5 条判为 low。因此原始 DeepSeek-PCAS 的平均采样步数达到 23.4，no-warmup 平均时间为 1.303s，比 Fixed-20 慢约 30.8%。这说明问题不在于 DeepSeek 语义标签本身，而在于标签到采样步数的映射过于激进。

## 改进策略

为解决该问题，本项目加入 DeepSeek-Balanced PCAS。该方法保留同一批 DeepSeek 语义标签，不重新调用 API，只修改决策策略：

| DeepSeek label | Original DeepSeek-PCAS | DeepSeek-Balanced |
| --- | ---: | ---: |
| low | 10 steps, guidance 4.0 | 8 steps, guidance 4.0 |
| medium | 20 steps, guidance 4.5 | 16 steps, guidance 4.4 |
| high | 28 steps, guidance 5.0 | 22 steps, guidance 4.8 |

由于 high 标签占比很高，DeepSeek-Balanced 将 high prompt 的额外采样预算控制在 Fixed-20 附近，而不是直接提升到 28 steps。这样可以保留语义复杂度排序，同时避免整体推理时间显著变慢。

## 速度结果

| Method | Avg steps | Avg time no-warmup | Time saving vs Fixed-20 |
| --- | ---: | ---: | ---: |
| Fixed-20 | 20.000 | 0.996s | 0.0% |
| DeepSeek-PCAS 7.3 | 23.400 | 1.303s | -30.8% |
| DeepSeek-Balanced | 18.467 | 0.844s | 15.3% |

DeepSeek-Balanced 将原始 DeepSeek-PCAS 的平均步数从 23.4 降到 18.467，并将平均时间从 1.303s 降到 0.844s。相比 Fixed-20，它不再变慢，而是获得了约 15.3% 的速度提升。

## CLIPScore 检查

| Method | Avg steps | Avg time no-warmup | Avg CLIPScore |
| --- | ---: | ---: | ---: |
| Fixed-20 | 20.000 | 0.996s | 35.762 |
| DeepSeek-PCAS 7.3 | 23.400 | 1.303s | 35.829 |
| DeepSeek-Balanced | 18.467 | 0.844s | 35.813 |
| Balanced-PCAS | 16.000 | 0.751s | 35.772 |

DeepSeek-Balanced 的 CLIPScore 为 35.813，略低于原始 DeepSeek-PCAS 的 35.829，但仍高于 Fixed-20 的 35.762。考虑到这些差异非常小，本项目不应声称 DeepSeek-Balanced 显著提升质量；更合理的结论是，它在保持接近原 DeepSeek-PCAS 自动对齐指标的同时，显著降低了推理时间。

## 可写入报告的结论

原始 DeepSeek-PCAS 证明了 LLM 可以提供更细粒度的语义复杂度分析，但其策略过于保守，导致整体变慢。DeepSeek-Balanced 通过对 low / medium / high 标签施加更温和的采样预算，把 DeepSeek 从“质量保守型策略”转化为“预算约束下的语义调度策略”。最终结果显示，DeepSeek-Balanced 相比 Fixed-20 快 15.3%，同时 CLIPScore 基本保持在同一水平。

因此，最终报告可以将 DeepSeek-PCAS 分成两个版本：原始 7.3 用于展示语义复杂度判断能力，DeepSeek-Balanced 用于解决实时推理中过于保守的问题。

## 图表引用

- DeepSeek-Balanced 速度图：`results/figures/day3_deepseek_balanced_speed_chart.png`
- DeepSeek-Balanced 速度-质量权衡图：`results/figures/day3_deepseek_balanced_speed_quality_tradeoff.png`
