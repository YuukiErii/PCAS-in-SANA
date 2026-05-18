# SANA 项目 PPT 与正式报告最新大纲

更新时间：2026-05-18

本文档用于后续制作课程汇报 PPT，并同步记录当前正式 LaTeX 报告的大纲。最新正式报告已经位于：

- `report/latex/sana_pcas_report.tex`
- `report/latex/sana_pcas_report.pdf`

## 1. 推荐汇报题目

中文题目：

> 基于 SANA 的高效文生图复现与 Prompt 复杂度自适应采样策略研究

英文题目：

> Reproduction and Prompt-Complexity Adaptive Sampling for Efficient Text-to-Image Generation with SANA

一句话摘要：

> 本项目复现 SANA-0.6B 文生图推理流程，并提出 prompt-aware 的自适应采样策略：Balanced-PCAS 在保持 CLIPScore 接近的同时获得约 24.6% 平均加速，Calibrated-PCAS 进一步将手工策略推进为 Fixed-20 质量约束下的最小充分 steps 预测。

## 2. 最新 PPT 叙事主线

建议整场汇报按研究推进逻辑组织，而不是按“每天做了什么”平铺：

```text
提出问题
  固定 20/28 steps 是否对所有 prompt 都合理？

初步探索
  Rule-PCAS 根据 prompt 长度重分配 steps，证明 prompt-aware 思路可行。

发现问题
  Rule-PCAS 整体加速不足；DeepSeek-PCAS 语义判断更强但过于保守；质量指标差异很小。

进一步深化
  Balanced-PCAS 控制平均预算；
  DeepSeek-Balanced 校准 LLM 标签到采样动作；
  Calibrated-PCAS 用真实 calibration grid 学习最小充分 steps。

扩展验证
  Guidance / hard prompt / LoRA 说明方法边界和 SANA pipeline 可扩展性。
```

核心讲述口径：

- 不要宣称 PCAS 显著提升图像质量。
- 要强调 PCAS 的价值是改善效率-质量权衡：在自动文本对齐指标和视觉观感基本相近的情况下，减少固定预算浪费。
- Balanced-PCAS 是主结果，Calibrated-PCAS 是方法深化，LoRA 是扩展实验。

## 3. 最新 PPT 页级大纲

建议 17-19 页，适合 8-12 分钟课程汇报。若时间更短，可删去 Slide 15 或合并 Slide 16-17。

### Slide 1：标题页

内容：

- 中文标题与英文标题。
- 作者：钟子铭 2200012104。
- 关键词：SANA, Text-to-Image, Adaptive Sampling, Efficient Inference。

建议视觉：

- 可在底部放 3-4 张 SANA 生成图小样例。

### Slide 2：研究背景：文生图质量强，但推理仍贵

核心信息：

- 扩散模型和 DiT 推动了高质量文生图。
- 高分辨率生成依赖多步采样，推理延迟仍是实际约束。
- 课程项目目标不是从头训练大模型，而是在已有高效 backbone 上做推理阶段优化。

### Slide 3：经典工作复现对象：SANA

核心信息：

| 模块 | 作用 |
| --- | --- |
| Deep Compression Autoencoder | 减少 latent tokens |
| Linear Diffusion Transformer | 降低高分辨率 attention 开销 |
| Decoder-only Text Encoder | 增强文本理解 |
| Flow-DPM-Solver | 提高采样效率 |

讲述重点：

- SANA 已经是高效 backbone，但实际推理仍常用固定 steps / guidance。

### Slide 4：提出问题：固定采样预算不适合所有 prompt

核心信息：

| Prompt 类型 | 示例 | 固定 steps 的问题 |
| --- | --- | --- |
| 简单 | red apple on a wooden table | 20/28 steps 可能浪费 |
| 中等 | robot chef cooking pasta | 需要稳定对齐 |
| 复杂 | cyberpunk street market with many objects | 低步数可能不足 |

主问题：

> 能否不改 SANA 主模型，只根据 prompt 复杂度动态选择推理预算？

### Slide 5：总体技术路线

建议画成 pipeline：

```text
Prompt
  -> Complexity Estimation
  -> Adaptive Policy
  -> SANA Pipeline
  -> Image
  -> Time / CLIPScore / Visual Evaluation
```

核心信息：

- 方法只作用于 inference-time policy。
- 不重新训练 SANA 主模型。
- 评估包括速度、显存、平均 steps、CLIPScore、定性图。

### Slide 6：实验设置

核心信息：

| 项目 | 设置 |
| --- | --- |
| Model | `Efficient-Large-Model/Sana_600M_512px_diffusers` |
| Hardware | NVIDIA GeForce RTX 5080 Laptop GPU, 16GB VRAM |
| Resolution | 512x512 |
| Benchmark | 30 prompts, 10/30/50 words 各 10 条 |
| Main reference | Fixed-20 |
| Metrics | time, peak VRAM, avg steps, CLIPScore, qualitative comparison |

建议图：

- `results/figures/day2_speed_summary_chart.png`

### Slide 7：Baseline：固定步数的速度-质量关系

核心表：

| Method | Avg steps | Avg time no-warmup | Avg CLIPScore |
| --- | ---: | ---: | ---: |
| Fixed-10 | 10.000 | 0.525s | 35.689 |
| Fixed-20 | 20.000 | 0.996s | 35.762 |
| Fixed-28 | 28.000 | 1.335s | 35.890 |

讲述重点：

- 步数增加会带来轻微 CLIPScore 提升，但时间成本明显上升。
- 这提出了固定预算冗余问题。

### Slide 8：初步探索：Rule-PCAS

初始策略：

| Group | Steps | Guidance |
| --- | ---: | ---: |
| 10-word | 10 | 4.0 |
| 30-word | 20 | 4.5 |
| 50-word | 28 | 5.0 |

核心信息：

- 简单 prompt 少给 steps，复杂 prompt 多给 steps。
- 这是 prompt-aware adaptive sampling 的第一版。

建议图：

- `results/figures/day3_pcas_vs_fixed20_chart.png`

### Slide 9：发现问题 1：Rule-PCAS 整体收益不足

核心表：

| Method | Avg steps | Avg time no-warmup | Saving vs Fixed-20 |
| --- | ---: | ---: | ---: |
| Fixed-20 | 20.000 | 0.996s | 0.0% |
| Rule-PCAS | 19.333 | 0.977s | 1.9% |

讲述重点：

- 短 prompt 的加速是真实的。
- 但长 prompt 的 28 steps 抵消了总体收益。
- 结论：prompt-aware 不自动等于 faster，还必须 budget-aware。

### Slide 10：改进 1：Balanced-PCAS

策略对比：

| Group | Rule-PCAS | Balanced-PCAS |
| --- | ---: | ---: |
| 10-word | 10 | 8 |
| 30-word | 20 | 16 |
| 50-word | 28 | 24 |

主结果：

| Method | Avg steps | Avg time no-warmup | Saving vs Fixed-20 | Avg CLIPScore |
| --- | ---: | ---: | ---: | ---: |
| Fixed-20 | 20.000 | 0.996s | 0.0% | 35.762 |
| Balanced-PCAS | 16.000 | 0.751s | 24.6% | 35.772 |

建议图：

- `results/figures/day3_pcas_balanced_speed_chart.png`
- `results/figures/day3_pcas_balanced_speed_quality_tradeoff.png`

讲述重点：

- Balanced-PCAS 是最稳健的主效率结果。
- 它证明关键不只是分配预算，而是在平均预算下降的前提下分配预算。

### Slide 11：发现问题 2：DeepSeek-PCAS 更懂语义，但策略过保守

核心信息：

- DeepSeek 将 30 条 prompt 判为 low/medium/high = 5/6/19。
- 原始 policy 使用 10/20/28 steps。
- high 标签过多导致平均 steps=23.4，平均时间比 Fixed-20 慢 30.8%。

讲述重点：

- LLM 标签不是没有用，问题在于“标签到动作”的映射没有校准。

### Slide 12：改进 2：DeepSeek-Balanced

策略对比：

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

- 语义复杂度可以用于调度，但必须纳入预算约束。

### Slide 13：进一步深化：Calibrated-PCAS

动机：

- Balanced-PCAS 和 DeepSeek-Balanced 仍是手工 policy。
- 它们没有回答每条 prompt 到 Fixed-20 附近究竟需要多少 steps。

定义：

```text
steps = {8, 12, 16, 20, 24, 28}
s* = min{s | CLIPScore(s) >= CLIPScore(Fixed-20) - 0.2}
```

标签分布：

| Minimal sufficient steps | Prompts |
| ---: | ---: |
| 8 | 18 |
| 12 | 4 |
| 16 | 6 |
| 20 | 2 |

讲述重点：

- 这一步把 PCAS 从经验规则推进到数据校准的最小预算预测。

### Slide 14：Calibrated-PCAS 结果

核心表：

| Method | Avg steps | Avg time no-warmup | Avg CLIPScore | Constraint satisfaction |
| --- | ---: | ---: | ---: | ---: |
| Fixed-20 | 20.000 | 1.537s | 35.762 | 100.0% |
| Balanced-PCAS | 16.000 | 1.740s | 35.772 | 73.3% |
| DeepSeek-Balanced | 18.467 | 2.023s | 35.813 | 73.3% |
| Oracle minimum | 10.933 | 1.112s | 36.276 | 100.0% |
| Calibrated-PCAS | 10.667 | 0.675s | 36.234 | 96.7% |
| LLM-feature Calibrated-PCAS | 11.333 | 1.093s | 36.230 | 96.7% |

讲述重点：

- 约束满足率从 73.3% 提升到 96.7%。
- 由于样本只有 30 条，Calibrated-PCAS 应表述为方法深化和 proof-of-concept，而不是完全替代 Balanced-PCAS 的主结果。

### Slide 15：质量评价：保持质量，而非显著提升质量

核心信息：

- 各方法 CLIPScore 差异较小。
- hard prompt 定性对比没有显示稳定的质量上限提升。
- 因此 PCAS 的贡献是保持自动对齐指标并改善效率-质量权衡。

建议图：

- `results/figures/day4_speed_quality_tradeoff.png`
- `results/figures/day4_clipscore_by_group.png`

### Slide 16：Guidance 与 hard prompt 补充分析

核心信息：

- Guidance 3.5-6.5 中等区间不敏感。
- 1.5 明显较弱。
- 8.5 有轻微 CLIPScore 偏好，但不等于视觉质量显著提升。
- Hard prompt 差异多体现在局部纹理、光照、小物体细节。

建议图：

- `results/figures/day4_guidance_ablation_clipscore.png`
- `results/figures/day4_hard_prompt_qualitative_grid.png`
- `results/figures/day4_hard_prompt_difference_heatmap_vs_fixed20.png`

### Slide 17：扩展实验：SANA-LoRA 个性化

核心信息：

- 使用个人耳机照片训练 DreamBooth LoRA。
- 初始 LoRA 能跑通，但主体一致性不稳定。
- 追加 enhanced LoRA、clean-captioned LoRA 和 subject-focused prompts。

关键结果：

| Method | Ref sim | Subject CLIP | Prompt CLIPScore |
| --- | ---: | ---: | ---: |
| Base | 83.659 | 28.487 | 31.525 |
| Original LoRA x2 | 83.839 | 29.141 | 32.620 |
| Enhanced LoRA x1.5 | 81.560 | 30.053 | 34.040 |
| Clean-caption x1.25 | 83.281 | 28.982 | 33.084 |

建议图：

- `results/figures/day5_lora_training_images_contact_sheet.png`
- `results/figures/day5_lora_subject_consistency_grid.png`

讲述重点：

- LoRA 是扩展实验，用于说明 SANA pipeline 可扩展，也说明小样本个性化受数据、caption 和 scale 影响明显。

### Slide 18：结论

建议总结：

1. 成功复现 SANA-0.6B diffusers 推理流程。
2. 构建 30 条受控 prompt benchmark，并完成固定步数 baseline。
3. Rule-PCAS 证明 prompt-aware 思路可行，但暴露整体预算问题。
4. Balanced-PCAS 在保持 CLIPScore 接近的同时实现约 24.6% 平均加速。
5. DeepSeek-Balanced 将 LLM 复杂度标签转化为预算约束下的语义调度，实现约 15.3% 加速。
6. Calibrated-PCAS 将 PCAS 推进为 Fixed-20 质量约束下的最小充分 steps 预测，达到 96.7% 约束满足率。
7. 质量评价表明 PCAS 应定位为效率-质量权衡策略，而不是显著质量提升方法。
8. LoRA 扩展实验说明小样本个性化流程可行，但主体一致性仍受数据和 scale 影响。

### Slide 19：未来工作

建议内容：

- 扩大 prompt benchmark，纳入真实用户 prompt、中文 prompt、文字渲染 prompt。
- 引入人工偏好、VQA、OCR、ImageReward / PickScore 等更丰富指标。
- 将 PCAS 从 steps/guidance 扩展到 adaptive resolution、adaptive solver order 或 early stopping。
- 用更干净、多角度产品图加强 LoRA 主体一致性。
- 在 SANA 1.6B、更高分辨率或其他高效 backbone 上验证迁移性。

## 4. 当前正式报告大纲

正式报告目前已编译为 42 页 PDF，结构如下。

### Front Matter

1. 标题页：中英文标题 + 作者 `钟子铭 2200012104`
2. 摘要页：摘要 + 关键词
3. 目录页

### 1. 引言

- 1.1 高分辨率文生图的推理效率问题
- 1.2 从原始 SANA 到 prompt-aware SANA 推理
- 1.3 本文贡献

写作重点：

- 从固定采样预算的问题引出 PCAS。
- 摘要和引言中的核心结论是 Balanced-PCAS 加速与 Calibrated-PCAS 方法深化。

### 2. 相关工作

- 2.1 扩散模型与 Diffusion Transformer
- 2.2 SANA 的高效生成设计
- 2.3 自适应推理与动态计算
- 2.4 LoRA 与 DreamBooth 个性化

写作重点：

- 把 PCAS 放在 adaptive inference / dynamic computation 语境下，而不是宣称新 backbone。

### 3. 方法

- 3.1 问题定义
- 3.2 Prompt 复杂度估计
- 3.3 Adaptive Sampling Policy
- 3.4 Calibrated-PCAS：最小充分 steps 预测
- 3.5 SANA-LoRA 个性化扩展

写作重点：

- 先给固定推理和 adaptive policy 的形式化定义。
- 解释 rule features、DeepSeek features 和 calibration grid。
- LoRA 明确为扩展实验。

### 4. 实验设置

- 4.1 硬件与软件环境
- 4.2 Prompt Benchmark
- 4.3 评价指标

写作重点：

- 明确单张 RTX 5080 Laptop GPU、SANA-0.6B、512x512、30 prompts。
- 说明 CLIPScore 的局限，避免过度解释质量。

### 5. 实验结果

- 5.1 固定步数 SANA baseline
- 5.2 原始 Rule-PCAS：计算重分配有效但整体收益不足
- 5.3 Balanced-PCAS：相对于固定 SANA 推理的主要效率优势
- 5.4 DeepSeek-Balanced：从语义复杂度到预算约束调度
- 5.5 Calibrated-PCAS：从手工规则到数据校准 policy
- 5.6 质量评价：PCAS 保持质量而非显著提高质量
- 5.7 Guidance scale 消融
- 5.8 Hard prompt 定性分析与视觉差异
- 5.9 LoRA 个性化实验

写作重点：

- 这一章已经按“提出问题 -> 初步探索 -> 发现问题 -> 进一步深化”重写。
- 不再单独列“前一版不足”表，而是在对应结果小节中自然说明每一步改进。

### 6. 讨论

- 6.1 PCAS 相对于原始 SANA 固定推理的优势
- 6.2 为什么原始 PCAS 和 DeepSeek-PCAS 需要 Balanced 版本
- 6.3 Calibrated-PCAS 带来的新版结论
- 6.4 质量结论的边界
- 6.5 Guidance scale 的启示
- 6.6 LoRA 个性化实验的意义与限制
- 6.7 局限性
- 6.8 未来工作

写作重点：

- 讨论部分负责收束方法边界，不夸大结论。

### 7. 结论

写作重点：

- 用一段话总结复现、PCAS、Balanced、DeepSeek-Balanced、Calibrated-PCAS、质量边界和 LoRA。

### Appendix A. 补充图表

- A.1 固定步数生成结果网格
- A.2 原始 PCAS 与 DeepSeek-PCAS 补充图
- A.3 Guidance 与 hard prompt 补充图
- A.4 LoRA 个性化补充图

## 5. 可直接用于摘要/汇报开场的版本

本项目围绕高效文生图模型 SANA 展开，首先在单张 RTX 5080 Laptop GPU 上复现 SANA-0.6B 的 diffusers 推理流程，并构建 30 条按 prompt 长度分组的 benchmark。针对固定采样步数可能造成计算浪费的问题，项目提出 Prompt-Complexity Adaptive Sampling，根据 prompt 复杂度动态分配采样步数和 guidance scale。实验发现，原始 Rule-PCAS 在短 prompt 上节省明显，但在均衡 benchmark 中整体收益有限；因此进一步提出 Balanced-PCAS，将采样预算调整为 8/16/24 steps，使平均推理时间相比 Fixed-20 降低约 24.6%，同时 CLIPScore 保持在几乎相同水平。对于 LLM-based 复杂度估计，项目实现 DeepSeek-PCAS，并发现其原始策略过于保守；通过 DeepSeek-Balanced 策略，平均推理时间相比 Fixed-20 降低约 15.3%。进一步地，Calibrated-PCAS 用 6 档 steps calibration grid 定义每条 prompt 的最小充分预算，在当前 calibration set 上以约 10--11 个平均 steps 达到 96.7% 的 Fixed-20 约束满足率。质量评估表明，各方法 CLIPScore 差异较小，PCAS 更适合定位为一种改善效率-质量权衡的自适应推理策略。最后，项目复现 SANA-LoRA DreamBooth 个性化流程，并通过 enhanced LoRA 与 clean-captioned LoRA 分析主体一致性问题，展示了小样本个性化的可行性与局限。

## 6. 推荐最终图表组合

PPT 优先使用图，表格只保留关键数字。

| 图/表 | 路径 | 用途 |
| --- | --- | --- |
| Fixed-step baseline speed | `results/figures/day2_speed_summary_chart.png` | 提出固定预算问题 |
| Day2 baseline image grid | `results/figures/day2_baseline_grid_full_prompts.png` | 展示 SANA 复现效果 |
| Original Rule-PCAS chart | `results/figures/day3_pcas_vs_fixed20_chart.png` | 展示初步探索和问题 |
| Balanced-PCAS speed chart | `results/figures/day3_pcas_balanced_speed_chart.png` | 主效率结果 |
| Balanced-PCAS speed-quality | `results/figures/day3_pcas_balanced_speed_quality_tradeoff.png` | 速度-质量权衡主图 |
| DeepSeek-Balanced speed chart | `results/figures/day3_deepseek_balanced_speed_chart.png` | LLM 语义调度结果 |
| DeepSeek-Balanced speed-quality | `results/figures/day3_deepseek_balanced_speed_quality_tradeoff.png` | LLM-PCAS 权衡图 |
| Calibrated-PCAS summary | `results/day6_calibrated_pcas_final_comparison_summary.md` | 最小充分 steps 与约束满足率 |
| Day4 speed-quality | `results/figures/day4_speed_quality_tradeoff.png` | 说明质量差异小 |
| CLIPScore by group | `results/figures/day4_clipscore_by_group.png` | 分组质量评价 |
| Guidance ablation | `results/figures/day4_guidance_ablation_clipscore.png` | guidance 消融 |
| Hard prompt qualitative grid | `results/figures/day4_hard_prompt_qualitative_grid.png` | 定性分析 |
| Hard prompt difference heatmap | `results/figures/day4_hard_prompt_difference_heatmap_vs_fixed20.png` | 视觉差异边界 |
| LoRA training contact sheet | `results/figures/day5_lora_training_images_contact_sheet.png` | 解释数据限制 |
| LoRA subject consistency grid | `results/figures/day5_lora_subject_consistency_grid.png` | LoRA 扩展结果 |

## 7. 汇报中应避免的说法

不要这样讲：

- “PCAS 显著提升图像质量。”
- “DeepSeek-PCAS 本身比所有方法都好。”
- “Calibrated-PCAS 已经证明能泛化到真实用户 prompt。”
- “LoRA 已经稳定复制耳机身份。”
- “Guidance 越高越好。”

建议这样讲：

- “PCAS 在保持相近 CLIPScore 的同时改善计算预算分配。”
- “Balanced-PCAS 是当前最稳健的效率主结果。”
- “DeepSeek-Balanced 说明语义复杂度有价值，但标签到动作需要预算校准。”
- “Calibrated-PCAS 是把经验规则推进到数据校准 policy 的 proof-of-concept。”
- “LoRA 证明个性化流程可行，但主体一致性仍依赖数据、caption 和 adapter scale。”
