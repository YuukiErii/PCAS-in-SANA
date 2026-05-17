# DAY4 补充：Hard Prompt 定性评价与视觉打平结论

## 动机

DAY4 的 CLIPScore 结果显示，各种采样策略的平均文本-图像对齐分数非常接近。进一步观察 hard prompt 对照图后，不同策略在语义内容、主体完整性和整体构图上也很难分出稳定优劣。因此本项目不再强行加入人工 1-5 分评分，而是把“多数结果视觉上基本打平”作为更稳妥的定性结论。

## Hard Prompt 子集

本子集从原 30 条 benchmark 中选出 8 条更困难的 prompt，覆盖复杂场景、多主体、多关系、文字生成和密集构图。对应 prompt index 为：18、19、21、22、23、26、28、30。

比较方法包括 Fixed-20、Fixed-28、Rule-PCAS、Balanced-PCAS 和 DeepSeek-Balanced。

## Hard Subset CLIPScore

| Method | Images | Avg steps | Avg time no-warmup | Avg CLIPScore |
| --- | ---: | ---: | ---: | ---: |
| fixed_20 | 8 | 20.000 | 0.978s | 36.522 |
| fixed_28 | 8 | 28.000 | 1.357s | 36.718 |
| rule_pcas_7_2 | 8 | 26.000 | 1.225s | 36.748 |
| balanced_pcas | 8 | 22.000 | 0.953s | 36.526 |
| deepseek_balanced_pcas | 8 | 22.000 | 0.955s | 36.440 |

从 hard subset 的自动指标看，各方法仍然处在很窄的 CLIPScore 区间内。结合对照图观察，差异主要体现在纹理、光照、边缘和局部小物体细节，而不是语义、构图或关系表达的明显改善。

## 结论写法

Day4 不应声称 PCAS 显著提升图像质量。更准确的结论是：PCAS / Balanced-PCAS 在减少推理步数和时间的同时，基本保持了与 Fixed-20 相当的 CLIPScore 和肉眼观感。因此，方法的主要价值是改善效率-质量权衡，而不是提升质量上限。

## 图表引用

- Hard prompt 对比图：`results/figures/day4_hard_prompt_qualitative_grid.png`
- Hard subset CLIPScore 表：`results/day4_hard_prompt_clipscore_summary.csv`
- 与 Fixed-20 的视觉差异热图：`results/figures/day4_hard_prompt_difference_heatmap_vs_fixed20.png`
