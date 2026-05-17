# DAY3 补充：面向整体加速的 Balanced-PCAS

## 问题动机

原始 Rule-PCAS 7.2 的目标是根据 prompt 长度重新分配采样预算：10-word prompt 使用 10 steps，30-word prompt 使用 20 steps，50-word prompt 使用 28 steps。该策略在短 prompt 上节省明显，但在长 prompt 上会比 Fixed-20 使用更多采样步数。因此，在当前 10/30/50 words 各 10 条的均衡 benchmark 上，短 prompt 的速度收益被长 prompt 的额外开销部分抵消，整体 no-warmup 时间只比 Fixed-20 快约 1.9%。

为了解决这一问题，本项目补充设计了一个效率优先的 Balanced-PCAS 策略。它仍然保留 prompt-aware 的思想，但增加了平均计算预算约束，使三个 prompt 组的采样步数都围绕 Fixed-20 向下调整。

## 策略设置

| Prompt group | Rule-PCAS 7.2 | Balanced-PCAS |
| --- | ---: | ---: |
| 10 words | 10 steps, guidance 4.0 | 8 steps, guidance 4.0 |
| 30 words | 20 steps, guidance 4.5 | 16 steps, guidance 4.4 |
| 50 words | 28 steps, guidance 5.0 | 24 steps, guidance 4.8 |

Balanced-PCAS 的平均采样步数为 16 steps，相比 Fixed-20 降低 20%。它的定位不是质量保守策略，而是效率导向的自适应推理策略。

## 速度结果

| Method | Avg steps | Avg time no-warmup | Time saving vs Fixed-20 |
| --- | ---: | ---: | ---: |
| Fixed-20 | 20.000 | 0.996s | 0.0% |
| Rule-PCAS 7.2 | 19.333 | 0.977s | 1.9% |
| Balanced-PCAS | 16.000 | 0.751s | 24.6% |

分组结果显示，Balanced-PCAS 在 10-word prompt 上节省 54.3% 时间，在 30-word prompt 上节省 24.2% 时间。50-word prompt 因仍使用 24 steps，比 Fixed-20 慢约 2.2%，但相比原始 Rule-PCAS 的 28 steps 已明显缓和。

## CLIPScore 检查

为了避免 Balanced-PCAS 只是单纯牺牲质量换速度，本项目额外计算了 CLIPScore：

| Method | Avg steps | Avg time no-warmup | Avg CLIPScore |
| --- | ---: | ---: | ---: |
| Fixed-20 | 20.000 | 0.996s | 35.762 |
| Rule-PCAS 7.2 | 19.333 | 0.977s | 35.750 |
| Balanced-PCAS | 16.000 | 0.751s | 35.772 |

三者的 CLIPScore 差异仍然非常小，说明在当前 benchmark 和 CLIP 自动指标下，Balanced-PCAS 没有明显破坏文本-图像对齐。由于 CLIPScore 对局部细节不敏感，报告中仍应避免声称 Balanced-PCAS 显著提升质量；更稳妥的表述是：Balanced-PCAS 在保持接近 Fixed-20 的自动对齐指标的同时，显著降低了平均推理时间。

## 可写入报告的结论

原始 Rule-PCAS 更像计算重分配策略，适合说明 prompt-aware sampling 的思想；Balanced-PCAS 则解决了整体加速不明显的问题，适合作为最终主推的效率版本。在 30 条均衡 prompt benchmark 上，Balanced-PCAS 将平均采样步数从 20 降到 16，no-warmup 平均时间从 0.996s 降到 0.751s，整体加速约 24.6%，同时 CLIPScore 保持在几乎相同水平。

因此，最终报告可以将 PCAS 写成两个版本：Rule-PCAS 7.2 用于展示复杂度自适应分配机制，Balanced-PCAS 用于展示在预算约束下的实际效率收益。

## 图表引用

- Balanced-PCAS 速度对比图：`results/figures/day3_pcas_balanced_speed_chart.png`
- Balanced-PCAS 速度-质量权衡图：`results/figures/day3_pcas_balanced_speed_quality_tradeoff.png`
