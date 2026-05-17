# SANA 项目 PPT 与学术报告大纲

更新时间：2026-05-17

本文档用于后续制作课程汇报 PPT 和正式书面报告。它是页级/章节级大纲，不是最终报告正文。

## 1. 推荐汇报题目

中文题目：

> 基于 SANA 的高效文生图复现与 Prompt 复杂度自适应采样策略研究

英文题目：

> Reproduction and Prompt-Complexity Adaptive Sampling for Efficient Text-to-Image Generation with SANA

一句话摘要：

> 本项目复现 SANA-0.6B 文生图推理流程，并提出预算约束下的 Prompt-Complexity Adaptive Sampling，在保持 CLIPScore 接近的同时减少平均推理时间。

## 2. PPT 叙事主线

建议整场汇报不要按“每天做了什么”平铺，而是按研究故事组织：

1. 高分辨率文生图需要效率。
2. SANA 是高效 backbone，但实际推理仍常用固定采样参数。
3. 不同 prompt 难度不同，固定 steps 会浪费或不足。
4. 我们提出 PCAS：按 prompt 复杂度自适应分配 steps/guidance。
5. 原始 PCAS 有两个问题：整体速度收益小，DeepSeek 过保守。
6. 我们提出 Balanced-PCAS 和 DeepSeek-Balanced，使方法真正符合预算约束。
7. 自动质量指标提升不明显，因此将贡献定位为效率-质量权衡，而非质量上限提升。
8. LoRA 个性化作为扩展实验，展示 SANA pipeline 的可扩展性和小样本个性化局限。

## 3. PPT 页级大纲

建议 15-18 页，适合 8-12 分钟课程汇报。

### Slide 1：标题页

标题：

```text
基于 SANA 的高效文生图复现与 Prompt 复杂度自适应采样策略研究
```

内容：

- 课程名称
- 姓名/组员
- 日期
- 关键词：SANA, Text-to-Image, Adaptive Sampling, Efficient Inference

备注：

- 标题页不放复杂图，可以放 2-3 张生成图小样例作为背景或底部 strip。

### Slide 2：研究背景：高分辨率文生图的效率问题

核心信息：

- Diffusion/DiT 文生图模型效果强，但推理成本高。
- 高分辨率生成中 latent token 数量和 attention 计算带来压力。
- 实际应用常希望在质量可接受的前提下减少推理时间。

建议图：

- 可用简单流程图：Text prompt -> Diffusion model -> Image。
- 或引用 SANA 论文中的效率动机，但若不准备截图，可用自绘示意。

讲述重点：

- 本项目不是从头训练模型，而是在高效 backbone 上做推理调度优化。

### Slide 3：经典工作：SANA 简介

核心信息：

- SANA 是 ICLR 2025 高效高分辨率文生图模型。
- 关键设计：Deep Compression Autoencoder、Linear Diffusion Transformer、decoder-only text encoder、Flow-DPM-Solver。
- 适合单卡复现实验。

建议内容：

| 模块 | 作用 |
| --- | --- |
| Deep Compression Autoencoder | 减少 latent tokens |
| Linear DiT | 降低高分辨率 attention 开销 |
| Decoder-only Text Encoder | 增强文本理解 |
| Flow-DPM-Solver | 提高采样效率 |

讲述重点：

- SANA 已经高效，但固定推理参数仍可能浪费。

### Slide 4：项目问题：固定采样参数不适合所有 prompt

核心信息：

| Prompt 类型 | 示例 | 固定 steps 的问题 |
| --- | --- | --- |
| 简单 | a red apple on a wooden table | 20/28 steps 可能浪费 |
| 中等 | robot chef cooking pasta | 需要稳定对齐 |
| 复杂 | cyberpunk street market with many objects | 低步数可能缺细节 |

主问题：

> 能否根据 prompt 复杂度动态调整采样参数，使简单 prompt 更快，复杂 prompt 更稳？

建议图：

- 使用 `results/figures/day2_baseline_grid_full_prompts.png` 展示固定步数效果。

### Slide 5：项目整体技术路线

建议画成 pipeline：

```text
Prompt
  -> Complexity Estimation
  -> Adaptive Policy
  -> SANA Pipeline
  -> Image
  -> Speed / CLIPScore / Visual Evaluation
```

核心信息：

- 不改 SANA 主模型参数。
- 创新集中在 inference-time adaptive computation。
- 评估同时包含速度、显存、CLIPScore、定性图。

### Slide 6：Prompt-Complexity Adaptive Sampling 方法

核心信息：

- Rule-PCAS 使用 prompt 长度/结构粗略估计复杂度。
- 初始策略：

| Group | Steps | Guidance |
| --- | ---: | ---: |
| short / 10 words | 10 | 4.0 |
| medium / 30 words | 20 | 4.5 |
| long / 50 words | 28 | 5.0 |

建议讲述：

- 简单 prompt 少给 steps，复杂 prompt 多给 steps。
- 这符合 adaptive computation 的直觉。

### Slide 7：实验设置

核心信息：

- Backbone：`Efficient-Large-Model/Sana_600M_512px_diffusers`
- 硬件：RTX 5080 Laptop GPU, 16GB VRAM
- Resolution：512x512
- Benchmark：30 prompts，10/30/50 words 各 10 条
- Baselines：Fixed-10, Fixed-20, Fixed-28
- Metrics：average inference time, peak VRAM, average steps, CLIPScore

建议图：

- 简单表格即可。
- 可插入 `results/figures/day2_speed_summary_chart.png`。

### Slide 8：Baseline 结果：固定步数的速度-质量关系

核心表：

| Method | Avg steps | Avg time no-warmup | Avg CLIPScore |
| --- | ---: | ---: | ---: |
| Fixed-10 | 10.000 | 0.525s | 35.689 |
| Fixed-20 | 20.000 | 0.996s | 35.762 |
| Fixed-28 | 28.000 | 1.335s | 35.890 |

建议图：

- `results/figures/day4_speed_quality_tradeoff.png`

讲述重点：

- 采样步数增加会略微提高 CLIPScore，但提升幅度有限。
- Fixed-20 是主要参考点。

### Slide 9：问题 1：原始 Rule-PCAS 整体加速不明显

核心信息：

- Rule-PCAS 在 short prompt 上节省明显。
- 但 long prompt 使用 28 steps，抵消总体收益。

核心表：

| Method | Avg steps | Avg time no-warmup | Saving vs Fixed-20 |
| --- | ---: | ---: | ---: |
| Fixed-20 | 20.000 | 0.996s | 0.0% |
| Rule-PCAS 7.2 | 19.333 | 0.977s | 1.9% |

建议图：

- `results/figures/day3_pcas_vs_fixed20_chart.png`

讲述重点：

- 这是项目中第一个“不尽人意”的结果，引出 Balanced-PCAS。

### Slide 10：改进 1：Balanced-PCAS

核心策略：

| Group | Rule-PCAS | Balanced-PCAS |
| --- | ---: | ---: |
| 10 words | 10 | 8 |
| 30 words | 20 | 16 |
| 50 words | 28 | 24 |

核心结果：

| Method | Avg steps | Avg time no-warmup | Saving vs Fixed-20 | Avg CLIPScore |
| --- | ---: | ---: | ---: | ---: |
| Fixed-20 | 20.000 | 0.996s | 0.0% | 35.762 |
| Balanced-PCAS | 16.000 | 0.751s | 24.6% | 35.772 |

建议图：

- `results/figures/day3_pcas_balanced_speed_chart.png`
- `results/figures/day3_pcas_balanced_speed_quality_tradeoff.png`

讲述重点：

- Balanced-PCAS 是最终主推的效率版本。

### Slide 11：问题 2：DeepSeek-PCAS 语义判断强，但过于保守

核心信息：

- DeepSeek 将 19/30 条 prompt 判为 high。
- 原始 policy high=28 steps。
- 平均 steps=23.4，导致比 Fixed-20 慢 30.8%。

表格：

| Method | Low | Medium | High | Avg steps | Avg time |
| --- | ---: | ---: | ---: | ---: | ---: |
| DeepSeek-PCAS | 5 | 6 | 19 | 23.400 | 1.303s |

讲述重点：

- DeepSeek 的语义标签有意义，但动作策略太激进。

### Slide 12：改进 2：DeepSeek-Balanced

核心策略：

| Label | Original | Balanced |
| --- | ---: | ---: |
| low | 10 | 8 |
| medium | 20 | 16 |
| high | 28 | 22 |

核心结果：

| Method | Avg steps | Avg time no-warmup | Saving vs Fixed-20 | Avg CLIPScore |
| --- | ---: | ---: | ---: | ---: |
| DeepSeek-PCAS | 23.400 | 1.303s | -30.8% | 35.829 |
| DeepSeek-Balanced | 18.467 | 0.844s | 15.3% | 35.813 |

建议图：

- `results/figures/day3_deepseek_balanced_speed_chart.png`
- `results/figures/day3_deepseek_balanced_speed_quality_tradeoff.png`

讲述重点：

- 这证明 LLM complexity 可以用于调度，但必须有预算约束。

### Slide 13：质量评估：CLIPScore 差异很小

核心信息：

- 各方法 CLIPScore 差距很小。
- 不应声称 PCAS 显著提升质量。
- 更稳妥结论：PCAS 保持自动对齐指标，同时改善计算预算分配。

建议图：

- `results/figures/day4_clipscore_by_group.png`
- `results/figures/day4_speed_quality_tradeoff.png`

讲述重点：

- 主贡献从“提升质量”调整为“效率-质量权衡”。

### Slide 14：Guidance Scale 消融

核心表：

| Guidance | Avg CLIPScore |
| ---: | ---: |
| 1.5 | 34.705 |
| 3.5 | 35.856 |
| 4.5 | 35.762 |
| 5.5 | 35.848 |
| 6.5 | 35.892 |
| 8.5 | 36.027 |

建议图：

- `results/figures/day4_guidance_ablation_clipscore.png`
- 可选：`results/figures/day4_guidance_stress_qualitative_grid.png`

讲述重点：

- 3.5-6.5 中等区间不敏感。
- 1.5 明显较弱。
- 8.5 有轻微 CLIPScore 偏好，但不等于视觉质量显著提升。

### Slide 15：Hard Prompt 定性分析

核心信息：

- 选 8 条复杂 prompt。
- Fixed-20、Fixed-28、Rule-PCAS、Balanced-PCAS、DeepSeek-Balanced 视觉上多数难分稳定优劣。
- 差异更多体现在纹理、光照、局部细节。

建议图：

- `results/figures/day4_hard_prompt_qualitative_grid.png`
- `results/figures/day4_hard_prompt_difference_heatmap_vs_fixed20.png`

讲述重点：

- 这进一步支持“质量基本保持，而非显著提升”的表述。

### Slide 16：扩展实验：SANA-LoRA 个性化

核心信息：

- 目标：用少量个人耳机照片训练 LoRA adapter。
- Subject：`zzmearphone` 黑色头戴耳机。
- 初始设置：9 张图，rank8/alpha8，200 steps。
- 后续补强：enhanced LoRA rank16/500 steps，clean-captioned LoRA rank16/400 steps。

建议图：

- `results/figures/day5_lora_base_vs_lora_scale2_grid.png`
- `results/figures/day5_lora_training_images_contact_sheet.png`

讲述重点：

- LoRA 是可选增强，不是 PCAS 主线。

### Slide 17：Day5 主体一致性分析

核心表：

| Method | Ref sim | Subject CLIP | Prompt CLIPScore |
| --- | ---: | ---: | ---: |
| Base | 83.659 | 28.487 | 31.525 |
| Original LoRA x2 | 83.839 | 29.141 | 32.620 |
| Enhanced LoRA x1.5 | 81.560 | 30.053 | 34.040 |
| Clean-caption x1.25 | 83.281 | 28.982 | 33.084 |

建议图：

- `results/figures/day5_lora_subject_consistency_grid.png`

讲述重点：

- Enhanced x1.5 在主体描述和 prompt 对齐上最好。
- Clean-caption x1.25 是更保守的稳定方案。
- Scale 过强会导致结构坍塌。
- 当前足够支撑汇报；补拍不是必须。

### Slide 18：总结与未来工作

建议总结：

1. 成功复现 SANA-0.6B 文生图推理流程。
2. 提出 PCAS，将固定推理参数改为 prompt-aware adaptive computation。
3. Balanced-PCAS 在保持 CLIPScore 接近的同时实现约 24.6% 平均加速。
4. DeepSeek-Balanced 将 LLM 复杂度判断转化为预算约束下的语义调度，实现约 15.3% 加速。
5. Day4 评估表明质量差异不明显，因此 PCAS 应定位为效率-质量权衡策略。
6. Day5 LoRA 复现证明小样本个性化可行，但主体一致性仍受数据、caption 和 scale 影响。

未来工作：

- 增加人工评分或 VQA-based 评估。
- 尝试 adaptive resolution。
- 在真实用户 prompt 分布上评估。
- 使用更强 backbone 或更多 LoRA 产品图。

## 4. 正式书面报告大纲

建议报告采用论文式结构。

### 摘要

内容要点：

- 复现 SANA。
- 提出 PCAS。
- Balanced-PCAS 主要结果：24.6% 加速，CLIPScore 基本保持。
- DeepSeek-Balanced 主要结果：15.3% 加速。
- LoRA 作为可选增强，展示小样本个性化可行但不稳定。

### 1. Introduction

建议写：

- 高分辨率文生图效率问题。
- SANA 的意义。
- 固定采样参数的不足。
- 本文贡献。

贡献列表可写：

1. 复现 SANA-0.6B diffusers 推理。
2. 构建 30 条 prompt benchmark 和固定步数 baseline。
3. 提出 Rule-PCAS、Balanced-PCAS、DeepSeek-PCAS、DeepSeek-Balanced。
4. 系统评估速度、CLIPScore、guidance scale 和 hard prompt。
5. 复现 SANA-LoRA DreamBooth 并分析主体一致性问题。

### 2. Related Work

可分小节：

- Diffusion Models and Diffusion Transformers
- Efficient Text-to-Image Generation
- SANA
- Adaptive Inference / Dynamic Computation
- DreamBooth and LoRA Personalization

### 3. Method

建议结构：

#### 3.1 SANA Backbone

简述：

- Deep compression autoencoder
- Linear DiT
- Decoder-only text encoder
- Flow-DPM-Solver

#### 3.2 Prompt Complexity Estimation

Rule-based：

- prompt 长度
- 主体数量/属性/关系/风格/文字需求

DeepSeek-based：

- LLM 输出 low / medium / high
- 使用 cache 降低成本

#### 3.3 Adaptive Sampling Policy

写四个策略：

| 方法 | 作用 |
| --- | --- |
| Rule-PCAS | 展示基础自适应机制 |
| Balanced-PCAS | 效率优先主推版本 |
| DeepSeek-PCAS | 展示语义复杂度判断 |
| DeepSeek-Balanced | 预算约束下的语义调度 |

#### 3.4 Optional LoRA Personalization

说明：

- 不是主线方法。
- 用于验证 SANA pipeline 可扩展性。
- 聚焦小样本个性化和主体一致性。

### 4. Experiments

建议结构：

#### 4.1 Experimental Setup

- Hardware：RTX5080 Laptop GPU, 16GB VRAM。
- Model：SANA-0.6B 512px diffusers。
- Prompt benchmark：30 prompts，10/30/50 words 各 10 条。
- Metrics：time, VRAM, average steps, CLIPScore, qualitative grid。

#### 4.2 Fixed-Step Baselines

放 Fixed-10/20/28 表格。

#### 4.3 PCAS Results

先写原始 Rule-PCAS，再写 Balanced-PCAS。

重点：

- 原始 Rule-PCAS 总体加速小。
- Balanced-PCAS 解决问题。

#### 4.4 DeepSeek-Assisted PCAS

重点：

- 原始 DeepSeek-PCAS 太保守。
- DeepSeek-Balanced 保留标签但降低预算。

#### 4.5 Quality Evaluation

重点：

- CLIPScore 差异很小。
- 不能声称质量显著提升。
- hard prompt 视觉上基本打平。

#### 4.6 Guidance Scale Ablation

重点：

- guidance 3.5-6.5 不敏感。
- 1.5 低 guidance 不推荐。
- 8.5 有轻微 CLIPScore 偏好但不是主线。

#### 4.7 LoRA Personalization

重点：

- 初始 LoRA 成功但主体不稳定。
- Enhanced x1.5 最佳自动指标。
- Clean-caption x1.25 是保守稳定方案。
- 当前足够支撑报告，补拍不是必须。

### 5. Discussion

建议讨论：

- PCAS 的价值是 adaptive computation，不是必然提高质量。
- CLIPScore 局限：对局部结构和关系错误不敏感。
- DeepSeek labels 有语义价值，但需要 policy 校准。
- LoRA 个性化受数据质量、caption 和 adapter scale 影响。

### 6. Conclusion

建议结论：

- 本项目完成 SANA 复现和系统实验。
- Balanced-PCAS 是主要成果。
- DeepSeek-Balanced 是语义复杂度调度的补充。
- Day4 说明自动指标提升有限，报告应保持保守。
- Day5 LoRA 是探索性增强。

### 7. Limitations and Future Work

建议写：

- Benchmark 规模仍较小。
- 主要使用 CLIPScore，缺少人工评分和 VQA-based 指标。
- 尚未系统测试 adaptive resolution。
- LoRA 数据量少，主体一致性仍不稳定。
- 未全面测试 SANA 1.6B 或更高分辨率。

## 5. 可直接用于摘要的版本

本项目围绕高效文生图模型 SANA 展开，首先在单张 RTX5080 Laptop GPU 上复现 SANA-0.6B 的 diffusers 推理流程，并构建 30 条按 prompt 长度分组的 benchmark。针对固定采样步数可能造成计算浪费的问题，项目提出 Prompt-Complexity Adaptive Sampling，根据 prompt 复杂度动态分配采样步数和 guidance scale。实验发现，原始 Rule-PCAS 在短 prompt 上节省明显，但在均衡 benchmark 中整体收益有限；因此进一步提出 Balanced-PCAS，将采样预算调整为 8/16/24 steps，使平均推理时间相比 Fixed-20 降低约 24.6%，同时 CLIPScore 保持在几乎相同水平。对于 LLM-based 复杂度估计，项目实现 DeepSeek-PCAS，并发现其原始策略过于保守；通过 DeepSeek-Balanced 策略，平均推理时间相比 Fixed-20 降低约 15.3%。质量评估表明，各方法 CLIPScore 差异较小，PCAS 更适合定位为一种改善效率-质量权衡的自适应推理策略。最后，项目复现 SANA-LoRA DreamBooth 个性化流程，并通过 enhanced LoRA 与 clean-captioned LoRA 分析主体一致性问题，展示了小样本个性化的可行性与局限。

## 6. 推荐最终图表组合

正式报告建议放：

1. SANA/PCAS pipeline 示意图，自绘。
2. Fixed-step baseline 速度表。
3. Balanced-PCAS speed-quality 图：`results/figures/day3_pcas_balanced_speed_quality_tradeoff.png`
4. DeepSeek-Balanced speed-quality 图：`results/figures/day3_deepseek_balanced_speed_quality_tradeoff.png`
5. Day4 speed-quality 图：`results/figures/day4_speed_quality_tradeoff.png`
6. Guidance ablation 图：`results/figures/day4_guidance_ablation_clipscore.png`
7. Hard prompt qualitative grid：`results/figures/day4_hard_prompt_qualitative_grid.png`
8. LoRA subject consistency grid：`results/figures/day5_lora_subject_consistency_grid.png`

PPT 建议少放大表，多放图；书面报告可以放完整表。

