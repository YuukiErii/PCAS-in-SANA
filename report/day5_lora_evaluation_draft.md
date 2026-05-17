# DAY5：基于个人耳机照片的 SANA-LoRA 个性化微调

## 实验目标

DAY5 的目标是在前四天完成 SANA 推理复现、PCAS 策略和质量评估之后，进一步尝试 SANA 的 DreamBooth LoRA 个性化微调流程。该部分不是主线方法 PCAS 的必要组成，而是作为课程项目的可选增强：使用少量个人耳机照片训练一个轻量 LoRA adapter，使模型在包含触发词 `zzmearphone headphones` 的 prompt 中更倾向于生成该耳机主体。

## 数据集与训练设置

本实验使用 9 张个人耳机照片作为 DreamBooth 数据集。原始图片位于 `ZZM Earphone/`，经过脚本 `src/prepare_lora_dataset.py` 处理为 9 张 768x768 的方形图像，并保存到 `data/dreambooth/zzmearphone/`。预处理方式保留主体并用模糊背景填充方形画布，以减少裁剪带来的主体缺失。

训练使用 `Efficient-Large-Model/Sana_600M_512px_diffusers` 作为基础模型，实例 prompt 为：

```text
a photo of zzmearphone headphones
```

LoRA 训练设置为 rank=8、alpha=8、最大训练步数 200、分辨率 512、bf16 mixed precision，并启用 CPU offload。最终权重保存为 `outputs/day5_lora_zzmearphone/pytorch_lora_weights.safetensors`，同时保留了 `checkpoint-100` 和 `checkpoint-200`。

在初始结果显示“能够生成但主体一致性不够稳定”后，本项目又补充训练了一版增强 LoRA。增强版保持同一批 9 张训练图，但将 rank/alpha 提高到 16/16，训练步数提高到 500，并把实例 prompt 改得更明确：

```text
a photo of zzmearphone black over-ear headphones with large oval ear cups and a padded headband
```

增强版权重保存到 `outputs/day5_lora_zzmearphone_enhanced/pytorch_lora_weights.safetensors`，并保留了 `checkpoint-250` 和 `checkpoint-500`。这样做的目的不是重新定义主线方法，而是针对第五个问题“LoRA 主体一致性不稳定”做低成本补强实验。

此外，本项目又补充了一版 clean-captioned LoRA：从 9 张训练图中筛掉主体不完整或视角较容易误导的图片，保留 7 张较干净样本，并为每张图添加单独 caption，描述其视角、耳罩、头梁和材质。该版本使用 rank=16、alpha=16、400 steps，输出到 `outputs/day5_lora_zzmearphone_clean_captioned_400/`。该实验用于判断在不补拍新图片的情况下，仅靠数据筛选和 caption 改进能否缓解主体不稳定。

## 验证方式

为了验证 LoRA 是否学到耳机主体，本实验构造了 6 条包含 `zzmearphone headphones` 的验证 prompt，并使用相同随机种子分别生成 Base SANA、LoRA scale=1.0 和 LoRA scale=2.0 的结果。除了定性可视化对比之外，还计算了一个参考图相似度指标：使用 `openai/clip-vit-base-patch32` 提取 9 张训练图片的图像 embedding，取平均后作为参考中心，再计算每张生成图与参考中心的余弦相似度并乘以 100。

需要强调的是，该指标只能粗略反映生成图是否接近“耳机图片”这一视觉概念，不能精确衡量产品身份、品牌细节或局部结构是否一致。因此 DAY5 结论主要依赖定性图像对比，并将自动指标作为辅助观察。

## 实验结果

| 方法 | 图像数 | 去除预热后的平均时间 | 平均峰值显存 | 平均参考图 CLIP 相似度 | 平均 prompt CLIPScore |
| --- | ---: | ---: | ---: | ---: | ---: |
| Base SANA | 6 | 0.884s | 6.979GB | 80.680 | 32.681 |
| LoRA scale 1.0 | 6 | 1.218s | 6.985GB | 79.724 | 32.779 |
| LoRA scale 2.0 | 6 | 1.230s | 6.985GB | 78.423 | 32.472 |

从定性结果看，LoRA scale=1.0 与 Base SANA 的差异较小，说明 200-step 轻量训练得到的 adapter 强度偏弱。当将 LoRA scale 提高到 2.0 后，部分 prompt 中的生成图明显更接近训练图片中的黑色头戴耳机外观，例如产品摄影、微距、桌面场景和产品渲染 prompt 中，耳机颜色和包耳式结构更稳定地向训练主体靠拢。

不过，自动指标并没有显示 LoRA 相比 Base 有整体优势。尤其在背包场景 prompt 中，LoRA 生成结果受到复杂场景约束影响，耳机主体不够突出，导致参考图相似度下降。这说明少量图片、轻量步数的 LoRA 微调虽然可以引入一定主体风格，但稳定控制复杂场景仍然困难。

## 主体一致性补充实验

为避免“背包”“爆炸视图”等复杂场景遮挡主体，本项目进一步构造了 8 条 subject-focused 验证 prompt，要求耳机主体居中、无遮挡，并明确包含黑色头戴式耳机、椭圆耳罩、厚头梁等属性。该实验比较 Base SANA、原始 LoRA x2、增强 LoRA x1.5/x2，以及 clean-captioned LoRA x1.25/x1.5/x1.75。

| 方法 | 图像数 | 参考图相似度 | 相比 Base | 胜过 Base 次数 | 主体描述 CLIP | 相比 Base | 胜过 Base 次数 | prompt CLIPScore |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Base | 8 | 83.659 | 0.000 | 0/8 | 28.487 | 0.000 | 0/8 | 31.525 |
| 原始 LoRA x2 | 8 | 83.839 | 0.180 | 4/8 | 29.141 | 0.654 | 7/8 | 32.620 |
| 增强 LoRA x1.5 | 8 | 81.560 | -2.099 | 2/8 | 30.053 | 1.566 | 6/8 | 34.040 |
| 增强 LoRA x2 | 8 | 76.666 | -6.993 | 0/8 | 27.874 | -0.613 | 3/8 | 32.855 |
| Clean-caption x1.25 | 8 | 83.281 | -0.378 | 5/8 | 28.982 | 0.495 | 5/8 | 33.084 |
| Clean-caption x1.5 | 8 | 81.778 | -1.882 | 4/8 | 28.646 | 0.159 | 4/8 | 32.752 |
| Clean-caption x1.75 | 8 | 79.343 | -4.317 | 2/8 | 28.401 | -0.086 | 5/8 | 32.887 |

这个结果说明增强训练并不是“scale 越大越好”。原始 LoRA x2 与训练图片参考中心最接近，但提升很小；增强 LoRA x1.5 在主体描述 CLIP 和 prompt CLIPScore 上最好，说明更明确的触发词和更高 rank/步数确实增强了“黑色头戴式耳机”的语义绑定；但增强 LoRA x2 过强，部分结果会把完整耳机结构压成耳垫、零件或过度简化的黑色形状。Clean-caption x1.25 虽然没有超过增强 LoRA x1.5 的主体描述 CLIP，但它更保守，参考图相似度接近 Base，并且在 5/8 条 prompt 上高于 Base，视觉上也更少出现高 scale 的结构坍塌。

因此，Day5 的更合理结论是：LoRA 主体一致性可以通过更明确的 caption、更高 rank、更长训练和更干净的数据得到改善，但必须配合合适的 adapter scale。当前自动指标最佳工作点是增强 LoRA x1.5，clean-caption x1.25 则是更稳的保守方案。由于 CLIP 仍然只是粗粒度代理指标，最终汇报应同时展示 `results/figures/day5_lora_subject_consistency_grid.png` 的多列对比图。

## 可写入报告的结论

DAY5 复现了 SANA-LoRA DreamBooth 的轻量个性化流程，并成功训练、加载和验证了一个基于个人耳机照片的 LoRA adapter。该实验说明，在单张 RTX5080 Laptop GPU 上，使用 SANA-0.6B 进行小样本 LoRA 个性化是可行的；但在当前 9 张图片的设置下，主体保持能力依赖 prompt 设计、训练强度和 LoRA scale。

因此，本项目应将 Day5 定位为可选增强和案例分析：LoRA 可以让模型在部分场景中更偏向个人耳机的黑色头戴式外观；增强 LoRA x1.5 在无遮挡主体 prompt 上给出了更好的主体描述匹配和 prompt 对齐，clean-caption x1.25 说明仅靠筛选数据和逐图 caption 也能得到更保守的稳定方案。但自动指标和复杂场景结果仍不足以支持“稳定身份复制”的强结论。当前结果已经足够支撑课程汇报；如果后续要把个性化效果做得更漂亮，再补拍多角度产品图会更有价值。

## 图表引用

- LoRA scale=1.0 对比图：`results/figures/day5_lora_base_vs_lora_scale1_grid.png`
- LoRA scale=2.0 对比图：`results/figures/day5_lora_base_vs_lora_scale2_grid.png`
- LoRA scale=1.0 指标图：`results/figures/day5_lora_validation_scale1_metrics.png`
- LoRA scale=2.0 指标图：`results/figures/day5_lora_validation_scale2_metrics.png`
- 主体一致性对比图：`results/figures/day5_lora_subject_consistency_grid.png`
- 主体一致性指标表：`results/day5_lora_subject_consistency_summary.md`
