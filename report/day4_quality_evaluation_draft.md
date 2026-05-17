# DAY4：质量评估与参数敏感性分析

## 评价设置

DAY4 的目标是在 DAY2 固定采样步数实验和 DAY3 PCAS 实验的基础上，评估不同采样策略是否会明显影响文本-图像对齐质量。本项目使用 `openai/clip-vit-base-patch32` 计算 CLIPScore，即图像特征与文本特征的余弦相似度乘以 100。该指标越高，表示生成图像与输入 prompt 的语义匹配程度越高。

需要注意的是，CLIPScore 只能作为自动化语义对齐指标，不能完全代表人眼主观质量、细节稳定性或局部对象正确性。因此，本节结论采用保守表述，重点观察不同策略在同一 prompt 集合上的相对变化。

## 固定步数与 PCAS 的质量对比

在 30 条 prompt 上，固定步数方法与两种 PCAS 方法的平均结果如下：

| 方法 | 平均采样步数 | 去除预热后的平均时间 | 平均 CLIPScore |
| --- | ---: | ---: | ---: |
| Fixed-10 | 10.000 | 0.525s | 35.689 |
| Fixed-20 | 20.000 | 0.996s | 35.762 |
| Fixed-28 | 28.000 | 1.335s | 35.890 |
| Rule-PCAS 7.2 | 19.333 | 0.977s | 35.750 |
| DeepSeek-PCAS 7.3 | 23.400 | 1.303s | 35.829 |

结果显示，各方法之间的 CLIPScore 差异很小。Fixed-28 的平均 CLIPScore 最高，为 35.890，但相对于 Fixed-20 的提升只有 0.128，同时平均推理时间从 0.996s 增加到 1.335s。Rule-PCAS 7.2 的平均 CLIPScore 为 35.750，与 Fixed-20 的 35.762 基本一致，但平均采样步数略低，平均时间也略低。DeepSeek-PCAS 7.3 的平均 CLIPScore 为 35.829，略高于 Fixed-20，但由于它更倾向于给复杂 prompt 分配高采样步数，平均时间也增加到 1.303s。

因此，本实验不能证明 PCAS 在 CLIPScore 上带来显著质量提升，但可以支持一个更稳妥的结论：PCAS 在改变计算资源分配的同时，基本保持了 CLIP 自动指标下的文本-图像对齐水平。其中，7.2 更偏向效率，7.3 更偏向语义复杂度识别和质量保守性。

## Guidance Scale 消融实验

为了进一步观察 classifier-free guidance scale 对生成结果的影响，本项目固定采样步数为 20。原始消融使用 3.5、4.5、5.5 和 6.5，结果非常接近；为了解释这种“不明显”的现象，本项目进一步加入低 guidance 压力点 1.5 和高 guidance 压力点 8.5。结果如下：

| Guidance scale | 去除预热后的平均时间 | 平均 CLIPScore |
| ---: | ---: | ---: |
| 1.5 | 0.897s | 34.705 |
| 3.5 | 1.190s | 35.856 |
| 4.5 | 0.996s | 35.762 |
| 5.5 | 1.124s | 35.848 |
| 6.5 | 1.088s | 35.892 |
| 8.5 | 0.887s | 36.027 |

扩展后的结果说明：原始 3.5-6.5 区间本来就是一个较稳定的正常工作区间，平均 CLIPScore 范围只有 0.130，因此难以观察到明显趋势是合理的。相比之下，guidance=1.5 相对默认 4.5 下降 1.057 分，说明过低 guidance 会削弱 prompt-image 对齐；guidance=8.5 相对默认 4.5 提高 0.264 分，尤其在 50-word prompts 上提升更明显，但该提升仍应解释为 CLIPScore 对高 guidance 的轻微偏好，而不是肉眼质量显著提升。

因此，本项目对 guidance scale 的结论是：SANA-0.6B 对中等 guidance 区间并不敏感，默认 4.5 适合作为公平比较设置；若目标是提高复杂 prompt 的自动语义对齐，可以尝试更高 guidance，但需要结合定性图检查是否引入过强对比、构图变化或局部细节取舍。

## 可写入报告的结论

DAY4 的主要结论是：在 SANA-0.6B、512x512 分辨率和当前 30 条 prompt benchmark 上，采样步数增加会带来轻微的 CLIPScore 提升，但提升幅度有限；PCAS 方法的价值主要体现在按 prompt 复杂度重新分配计算预算，而不是在自动指标上显著提高整体质量。Rule-PCAS 7.2 在保持接近 Fixed-20 的 CLIPScore 的同时略微降低平均时间；DeepSeek-PCAS 7.3 则通过更保守的语义复杂度判断给更多 prompt 分配高步数，CLIPScore 略高但运行更慢。

因此，报告中可以将 PCAS 定位为一种“质量基本保持、计算分配更自适应”的推理策略，而不应表述为已经证明能够显著提升图像质量的方法。对于 guidance scale，报告中应强调中等区间鲁棒、低 guidance 不推荐、高 guidance 可作为复杂 prompt 的可选设置，但不作为本项目主线优化方向。

## 图表引用

- 速度-质量权衡图：`results/figures/day4_speed_quality_tradeoff.png`
- 不同 prompt 长度组的 CLIPScore 对比：`results/figures/day4_clipscore_by_group.png`
- Guidance scale 消融图：`results/figures/day4_guidance_ablation_clipscore.png`
- Guidance stress-test 定性图：`results/figures/day4_guidance_stress_qualitative_grid.png`
- Guidance stress-test 分析表：`results/day4_guidance_stress_analysis.md`
