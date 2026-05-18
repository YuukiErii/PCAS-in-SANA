# SANA 课程项目工作总结与后续交接

更新时间：2026-05-18

本文档用于给后续对话、正式报告写作和 PPT 制作快速接上项目上下文。它不是最终书面报告，而是从原始大纲、实际实施、遇到的问题、补救实验到当前结论的完整工作总结。

## 0. 最新对话更新：正式报告整合、版式与叙事重构

本轮对话已经把前期实验、Day6 Calibrated-PCAS 扩展和报告修改意见整合进正式 LaTeX 报告，并在原项目目录下重新编译出 PDF。

最新正式报告文件：

| 文件 | 状态 |
| --- | --- |
| `report/latex/sana_pcas_report.tex` | 已更新，包含最终报告正文、表格、图、参考文献和附录 |
| `report/latex/sana_pcas_report.pdf` | 已重新编译，当前为 A4、42 页 |

本轮完成的报告层面工作：

- 参考用户提供的 LaTeX 报告 PDF，调整正式报告前三页格式：第一页为中英文标题与作者 `钟子铭 2200012104`，第二页为“摘要”，第三页开始为“目录”。
- 将全文字体统一为参考报告风格：中文使用 FandolSong/FandolKai，英文使用 Latin Modern Roman；正文标题也已从无衬线字体改为与正文同源的宋体/Latin Modern 体系，颜色保持原来的红/蓝方案。
- 全局处理表格居中：表格本体和 caption 都已居中。
- 将 Day6 Calibrated-PCAS 的新图表、标签分布、约束满足率和新版结论写入正式报告。
- 根据用户反馈，删除了引言中单独列出的“前一版不足与本文补强”板块，不再把新版结论机械拆成一张表。
- 重新组织第 5 章“实验结果”的叙事逻辑，使其自然体现“提出问题 -> 初步探索 -> 发现问题 -> 进一步深化”：
  - Fixed-step baseline 提出固定预算冗余问题。
  - Rule-PCAS 做初步探索，证明 prompt-aware 分配可行。
  - 原始 Rule-PCAS 暴露平均预算失控、复杂度估计过粗的问题。
  - Balanced-PCAS 用预算约束解决整体加速不足。
  - DeepSeek-PCAS 暴露 LLM 标签未校准的问题。
  - DeepSeek-Balanced 说明语义复杂度可以进入策略，但必须经过预算约束。
  - Calibrated-PCAS 进一步把手工 policy 推进为 Fixed-20 质量约束下的最小充分 steps 预测。

最新正式报告目录如下：

```text
1 引言
  1.1 高分辨率文生图的推理效率问题
  1.2 从原始 SANA 到 prompt-aware SANA 推理
  1.3 本文贡献
2 相关工作
  2.1 扩散模型与 Diffusion Transformer
  2.2 SANA 的高效生成设计
  2.3 自适应推理与动态计算
  2.4 LoRA 与 DreamBooth 个性化
3 方法
  3.1 问题定义
  3.2 Prompt 复杂度估计
  3.3 Adaptive Sampling Policy
  3.4 Calibrated-PCAS：最小充分 steps 预测
  3.5 SANA-LoRA 个性化扩展
4 实验设置
  4.1 硬件与软件环境
  4.2 Prompt Benchmark
  4.3 评价指标
5 实验结果
  5.1 固定步数 SANA baseline
  5.2 原始 Rule-PCAS：计算重分配有效但整体收益不足
  5.3 Balanced-PCAS：相对于固定 SANA 推理的主要效率优势
  5.4 DeepSeek-Balanced：从语义复杂度到预算约束调度
  5.5 Calibrated-PCAS：从手工规则到数据校准 policy
  5.6 质量评价：PCAS 保持质量而非显著提高质量
  5.7 Guidance scale 消融
  5.8 Hard prompt 定性分析与视觉差异
  5.9 LoRA 个性化实验
6 讨论
7 结论
A 补充图表
```

## 1. 项目来源与原始大纲

项目来自深度生成课程项目，原始大纲文件为 `SANA课程项目详细大纲.docx`。大纲给出的题目方向是：

> 基于 SANA 的高效高分辨率文生图复现与 Prompt 复杂度自适应采样策略研究

英文题目：

> Reproduction and Prompt-Complexity Adaptive Sampling for Efficient Text-to-Image Generation with SANA

大纲中的核心定位是：在单张 RTX5080 显卡、约一周时间的约束下，不从头训练大型文生图模型，而是选择“经典工作复现 + 轻量推理策略创新”的路线。经典工作是 SANA: Efficient High-Resolution Image Synthesis with Linear Diffusion Transformers, ICLR 2025。项目主线是复现 SANA 推理流程，并提出 Prompt-Complexity Adaptive Sampling，简称 PCAS。

原始大纲中设定的研究问题是：SANA 已经显著提高了高分辨率文生图效率，但实际推理仍常用固定采样步数和固定 guidance scale。不同 prompt 的生成难度明显不同，简单 prompt 使用固定 20 或 28 steps 可能造成计算浪费，复杂 prompt 使用过低步数可能导致主体缺失、关系错误或细节不稳。因此项目关注：能否在不重新训练 SANA 主模型的前提下，根据 prompt 复杂度动态调整推理参数，使简单 prompt 更快，复杂 prompt 更稳。

原始技术路线如下：

```text
Prompt
  -> Prompt 复杂度分析模块
  -> 复杂度分数 C(prompt)
  -> 自适应参数选择器
  -> SANA Pipeline
  -> 生成图像
  -> 速度 / 质量 / 文本对齐评估
```

大纲中的计划安排为：

| 阶段 | 原始目标 | 当前实现状态 |
| --- | --- | --- |
| Day 1 | 配置环境，跑通 SANA diffusers inference | 已完成 |
| Day 2 | 构建 prompt benchmark，跑固定 steps baseline | 已完成 |
| Day 3 | 实现 PCAS 和可选 LLM-based PCAS | 已完成，并追加 Balanced 版本 |
| Day 4 | 计算 CLIPScore，做 steps/guidance 消融 | 已完成，并追加 hard prompt 定性分析 |
| Day 5 | 可选 Sana-LoRA DreamBooth 或失败案例补充 | 已完成 LoRA，并围绕主体一致性做多轮补强 |
| Day 6-7 | 写报告，做 PPT，整理最终提交材料 | 已追加 Calibrated-PCAS 扩展；正式 LaTeX 报告已整合、版式优化并重新编译；PPT 大纲已更新 |

## 2. 项目目录与关键文件

当前项目根目录：

```text
C:\Users\Mahiru\Desktop\ERII\PKU\Semester8\DL\项目汇报\SANA
```

主要目录：

| 路径 | 作用 |
| --- | --- |
| `configs/` | 不同实验的 YAML 配置 |
| `prompts/` | benchmark prompts 和 LoRA 验证 prompts |
| `src/` | 复现、PCAS、评估、可视化脚本 |
| `outputs/` | 生成图像和每张图的 JSON metadata |
| `results/` | CSV、Markdown 结果、日志 |
| `results/figures/` | 论文/PPT 可用图表 |
| `report/` | 现有报告草稿、补充说明、本文档 |
| `data/dreambooth/` | Day5 LoRA 训练数据 |

建议后续对话优先读取以下文件：

| 文件 | 用途 |
| --- | --- |
| `README.md` | 当前项目总进度索引 |
| `report/WORK_SUMMARY_HANDOFF.md` | 当前交接总结 |
| `report/PPT_ACADEMIC_REPORT_OUTLINE.md` | PPT 和正式报告结构草案 |
| `report/latex/sana_pcas_report.tex` | 当前正式 LaTeX 报告源文件 |
| `report/latex/sana_pcas_report.pdf` | 当前正式报告 PDF |
| `report/day3_balanced_pcas_draft.md` | Balanced-PCAS 中文解释 |
| `report/day3_deepseek_balanced_draft.md` | DeepSeek-Balanced 中文解释 |
| `report/day4_quality_evaluation_draft.md` | Day4 质量评价草稿 |
| `report/day4_hard_prompt_evaluation_draft.md` | Hard prompt 视觉打平结论 |
| `report/day5_lora_evaluation_draft.md` | Day5 LoRA 个性化草稿 |
| `report/CALIBRATED_PCAS_OUTLINE.md` | Calibrated-PCAS 研究大纲 |
| `report/day6_calibrated_pcas_draft.md` | Day6 Calibrated-PCAS 报告草稿 |
| `results/day5_lora_subject_consistency_summary.md` | 最新 Day5 主体一致性结论 |
| `results/day6_calibrated_pcas_summary.md` | Rule-feature Calibrated-PCAS 结果 |
| `results/day6_calibrated_pcas_llm_features_summary.md` | LLM-feature Calibrated-PCAS 结果 |

## 3. 已完成工作总览

### 3.1 Day 1：环境配置与 SANA 推理复现

完成内容：

- 创建 Python 3.11 虚拟环境。
- 安装 PyTorch CUDA、Diffusers、Transformers、Accelerate 等依赖。
- 确认 GPU：NVIDIA GeForce RTX 5080 Laptop GPU，16GB VRAM。
- 跑通 SANA-0.6B / 512px diffusers 推理。
- 生成 smoke baseline 图像与 metadata。
- 保存环境报告到 `results/day1_environment.md`。

关键文件：

- `src/day1_env_check.py`
- `src/run_sana_baseline.py`
- `configs/day1_smoke.yaml`
- `configs/day1_tiny_debug.yaml`
- `results/day1_environment.md`
- `outputs/day1_baseline/`

遇到的问题：

- 系统 `python` alias 指向 Microsoft Store，因此需要使用 `.venv\Scripts\python.exe` 或明确 Python 3.11 路径。
- SANA 模型文件较大，下载中需要考虑 Hugging Face mirror/cache。
- 本机 `git` 不在 PATH，无法用 `git status` 检查版本状态。

结论：

- 环境和推理链路已跑通，后续所有实验基于 SANA-0.6B / 512px diffusers 进行。

### 3.2 Day 2：固定步数 Baseline 与 Prompt Benchmark

完成内容：

- 构建 30 条 controlled prompt benchmark。
- 按 prompt 长度分为 10-word、30-word、50-word 三组，每组 10 条。
- 运行固定采样步数 baseline：10 steps、20 steps、28 steps。
- 保存速度结果、生成图像和对比网格。

关键文件：

- `prompts/day2_benchmark_prompts.txt`
- `prompts/day2_10word_prompts.txt`
- `prompts/day2_30word_prompts.txt`
- `prompts/day2_50word_prompts.txt`
- `configs/day2_baseline_10steps.yaml`
- `configs/day2_baseline_20steps.yaml`
- `configs/day2_baseline_28steps.yaml`
- `results/day2_speed_results.csv`
- `results/day2_speed_summary.md`
- `results/figures/day2_baseline_grid_full_prompts.png`
- `results/figures/day2_speed_summary_chart.png`

核心结果：

- Fixed-10 最快，但可能对复杂 prompt 不稳。
- Fixed-20 作为主要 baseline。
- Fixed-28 更慢，CLIPScore 后续显示只略有提升。

结论：

- Day2 为 PCAS 提供了公平 baseline 和受控 prompt 集合。

### 3.3 Day 3：Rule-PCAS 与 DeepSeek-PCAS

原始方法：

- 实现 `src/prompt_complexity.py` 和 `src/run_sana_pcas.py`。
- Rule-PCAS 根据 prompt 长度分配采样参数：

| Prompt group | Steps | Guidance |
| --- | ---: | ---: |
| 10 words | 10 | 4.0 |
| 30 words | 20 | 4.5 |
| 50 words | 28 | 5.0 |

关键文件：

- `src/prompt_complexity.py`
- `src/run_sana_pcas.py`
- `configs/day3_pcas.yaml`
- `outputs/day3_pcas/`
- `results/day3_pcas_summary.md`
- `results/day3_pcas_vs_fixed20.csv`
- `results/figures/day3_pcas_vs_fixed20_chart.png`

DeepSeek-PCAS：

- 实现 `src/prompt_complexity_deepseek.py` 和 `src/run_sana_pcas_deepseek.py`。
- DeepSeek 输出 low / medium / high 语义复杂度。
- API key 从 `DEEPSEEK_API_KEY` 或本地 `API_DEEPSEEK.txt` 读取。
- 缓存 DeepSeek 复杂度结果，避免重复调用。

关键文件：

- `src/prompt_complexity_deepseek.py`
- `src/run_sana_pcas_deepseek.py`
- `configs/day3_pcas_deepseek.yaml`
- `results/day3_deepseek_complexity_cache.json`
- `results/day3_deepseek_pcas_summary.md`
- `results/day3_7_2_7_3_summary.csv`

原始困难 1：PCAS 整体速度收益不大。

- Rule-PCAS 对短 prompt 很有效，但对长 prompt 使用 28 steps。
- 当前 benchmark 是 10/30/50 words 各 10 条，长 prompt 的额外耗时抵消了短 prompt 的节省。
- 总体只比 Fixed-20 快约 1.9%。

解决方案：Balanced-PCAS。

- 新增 8/16/24 steps 策略。
- 保留 prompt-aware 思想，但加入平均预算约束。

| Method | Avg steps | Avg time no-warmup | Time saving vs Fixed-20 | Avg CLIPScore |
| --- | ---: | ---: | ---: | ---: |
| Fixed-20 | 20.000 | 0.996s | 0.0% | 35.762 |
| Rule-PCAS 7.2 | 19.333 | 0.977s | 1.9% | 35.750 |
| Balanced-PCAS | 16.000 | 0.751s | 24.6% | 35.772 |

关键文件：

- `configs/day3_pcas_balanced.yaml`
- `src/make_pcas_balanced_figures.py`
- `results/day3_pcas_balanced_summary.md`
- `results/day3_pcas_balanced_clipscore_summary.md`
- `report/day3_balanced_pcas_draft.md`
- `results/figures/day3_pcas_balanced_speed_chart.png`
- `results/figures/day3_pcas_balanced_speed_quality_tradeoff.png`

结论：

- Rule-PCAS 更像“计算重分配策略”。
- Balanced-PCAS 才是最终可主推的效率版本：平均步数从 20 降到 16，平均时间从 0.996s 降到 0.751s，约 24.6% 加速，同时 CLIPScore 基本不变。

原始困难 2：DeepSeek-PCAS 太保守、整体变慢。

- DeepSeek 将 30 条 prompt 中 19 条判为 high、6 条 medium、5 条 low。
- 原始 low/medium/high = 10/20/28 steps 使平均 steps 达到 23.4。
- 平均时间 1.303s，比 Fixed-20 慢约 30.8%。

解决方案：DeepSeek-Balanced。

- 不重新调用 API，复用缓存标签。
- 修改 policy 为 low=8、medium=16、high=22。

| Method | Avg steps | Avg time no-warmup | Time saving vs Fixed-20 | Avg CLIPScore |
| --- | ---: | ---: | ---: | ---: |
| Fixed-20 | 20.000 | 0.996s | 0.0% | 35.762 |
| DeepSeek-PCAS 7.3 | 23.400 | 1.303s | -30.8% | 35.829 |
| DeepSeek-Balanced | 18.467 | 0.844s | 15.3% | 35.813 |

关键文件：

- `configs/day3_pcas_deepseek_balanced.yaml`
- `src/make_deepseek_balanced_figures.py`
- `results/day3_deepseek_balanced_summary.md`
- `report/day3_deepseek_balanced_draft.md`
- `results/figures/day3_deepseek_balanced_speed_chart.png`
- `results/figures/day3_deepseek_balanced_speed_quality_tradeoff.png`

结论：

- 原始 DeepSeek-PCAS 适合展示 LLM 语义复杂度判断能力，但更像质量保守策略。
- DeepSeek-Balanced 将其改造成预算约束下的语义调度策略。

### 3.4 Day 4：质量评价、Guidance 消融与 Hard Prompt 分析

完成内容：

- 实现 `src/evaluate_clipscore.py`。
- 使用 `openai/clip-vit-base-patch32` 对 Fixed-10、Fixed-20、Fixed-28、Rule-PCAS 7.2、DeepSeek-PCAS 7.3 做 CLIPScore 评估。
- 生成速度-质量权衡图和分组 CLIPScore 图。

关键结果：

| Method | Avg steps | Avg time no-warmup | Avg CLIPScore |
| --- | ---: | ---: | ---: |
| Fixed-10 | 10.000 | 0.525s | 35.689 |
| Fixed-20 | 20.000 | 0.996s | 35.762 |
| Fixed-28 | 28.000 | 1.335s | 35.890 |
| Rule-PCAS 7.2 | 19.333 | 0.977s | 35.750 |
| DeepSeek-PCAS 7.3 | 23.400 | 1.303s | 35.829 |

原始困难 3：Day4 质量指标提升不明显。

- Fixed-10/20/28 与 PCAS 的 CLIPScore 差距都很小。
- CLIPScore 对局部细节、主体完整性和复杂关系错误不敏感。

解决方案：

- 保守解释：不声称 PCAS 显著提高图像质量。
- 把结论改为：在相近 CLIPScore 下，PCAS 重新分配计算预算。
- 增加 hard prompt 子集和定性视觉对比。
- 增加视觉差异热图，说明许多方法视觉上基本打平。

Hard prompt 结果：

| Method | Images | Avg steps | Avg time no-warmup | Avg CLIPScore |
| --- | ---: | ---: | ---: | ---: |
| fixed_20 | 8 | 20.000 | 0.978s | 36.522 |
| fixed_28 | 8 | 28.000 | 1.357s | 36.718 |
| rule_pcas_7_2 | 8 | 26.000 | 1.225s | 36.748 |
| balanced_pcas | 8 | 22.000 | 0.953s | 36.526 |
| deepseek_balanced_pcas | 8 | 22.000 | 0.955s | 36.440 |

关键文件：

- `src/evaluate_clipscore.py`
- `src/make_day4_figures.py`
- `src/make_day4_hard_eval_assets.py`
- `src/make_day4_visual_difference_assets.py`
- `results/day4_clipscore_summary.md`
- `results/day4_hard_prompt_visual_tie_summary.md`
- `results/day4_hard_prompt_difference_vs_fixed20.csv`
- `report/day4_quality_evaluation_draft.md`
- `report/day4_hard_prompt_evaluation_draft.md`
- `results/figures/day4_speed_quality_tradeoff.png`
- `results/figures/day4_clipscore_by_group.png`
- `results/figures/day4_hard_prompt_qualitative_grid.png`
- `results/figures/day4_hard_prompt_difference_heatmap_vs_fixed20.png`

原始困难 4：Guidance scale 消融不明显。

- 3.5、4.5、5.5、6.5 的 CLIPScore 差距很小。
- 难以支持“更高 guidance 更好”。

解决方案：

- 扩大到低/高 stress points：1.5 和 8.5。
- 将结论改写为“中等 guidance 区间不敏感，低 guidance 会削弱对齐，高 guidance 只显示轻微 CLIPScore 偏好，不等价于视觉质量显著提升”。

Guidance 结果：

| Guidance | Avg time no-warmup | Avg CLIPScore |
| ---: | ---: | ---: |
| 1.5 | 0.897s | 34.705 |
| 3.5 | 1.190s | 35.856 |
| 4.5 | 0.996s | 35.762 |
| 5.5 | 1.124s | 35.848 |
| 6.5 | 1.088s | 35.892 |
| 8.5 | 0.887s | 36.027 |

关键文件：

- `src/evaluate_day4_guidance_ablation.py`
- `src/make_day4_guidance_figures.py`
- `src/make_day4_guidance_stress_assets.py`
- `results/day4_guidance_ablation_summary.md`
- `results/day4_guidance_stress_analysis.md`
- `results/figures/day4_guidance_ablation_clipscore.png`
- `results/figures/day4_guidance_stress_qualitative_grid.png`

结论：

- Day4 的主线不是证明 PCAS 提高质量，而是证明 PCAS 在保持自动对齐指标和视觉观感基本相近的情况下改善效率-质量权衡。

### 3.5 Day 5：SANA-LoRA 个性化微调与主体一致性问题

完成内容：

- 使用用户提供的 9 张耳机照片，构建 DreamBooth 数据集。
- 预处理到 `data/dreambooth/zzmearphone/`，每张为 768x768 方形图。
- 复现 SANA DreamBooth LoRA 训练。
- 生成 Base vs LoRA 对比图。
- 计算训练图参考中心的 CLIP 图像相似度和 prompt CLIPScore。

原始 LoRA 设置：

| 项目 | 设置 |
| --- | --- |
| 数据 | 9 张耳机图片 |
| base model | `Efficient-Large-Model/Sana_600M_512px_diffusers` |
| instance prompt | `a photo of zzmearphone headphones` |
| rank / alpha | 8 / 8 |
| steps | 200 |
| resolution | 512 |
| mixed precision | bf16 |
| 输出 | `outputs/day5_lora_zzmearphone/` |

原始验证结果：

| Method | Images | Avg time no-warmup | Avg peak VRAM | Avg reference CLIP similarity | Avg prompt CLIPScore |
| --- | ---: | ---: | ---: | ---: | ---: |
| Base SANA | 6 | 0.884s | 6.979GB | 80.680 | 32.681 |
| LoRA scale 1.0 | 6 | 1.218s | 6.985GB | 79.724 | 32.779 |
| LoRA scale 2.0 | 6 | 1.230s | 6.985GB | 78.423 | 32.472 |

原始困难 5：Day5 LoRA 主体一致性不稳定。

- LoRA 能加载并生成。
- scale=1.0 差异较小。
- scale=2.0 在产品照和微距图上更像黑色头戴耳机，但自动 CLIP 参考相似度没有超过 Base。
- 复杂 prompt，尤其背包场景，容易遮挡或吞掉耳机主体。
- CLIP 图像相似度是粗指标，不能精确衡量产品身份和局部结构。

解决方案 1：subject-focused 验证。

- 新增 8 条 prompt，要求耳机居中、无遮挡、明确黑色包耳式、椭圆耳罩、厚头梁。
- 不再用“背包”这类天然遮挡 prompt 当主指标。

关键文件：

- `prompts/day5_lora_subject_consistency_prompts.txt`
- `configs/day5_lora_subject_original_scale2.yaml`
- `src/evaluate_day5_lora_subject_consistency.py`

解决方案 2：增强版 LoRA。

- 保持 9 张图。
- rank/alpha 提高到 16/16。
- 训练步数提高到 500。
- instance prompt 改成：

```text
a photo of zzmearphone black over-ear headphones with large oval ear cups and a padded headband
```

输出：

- `outputs/day5_lora_zzmearphone_enhanced/`
- `checkpoint-250/`
- `checkpoint-500/`

解决方案 3：clean-captioned LoRA。

- 先观察训练图 contact sheet：`results/figures/day5_lora_training_images_contact_sheet.png`。
- 从 9 张图中筛出 7 张 cleaner subset，去掉更容易误导的局部/远景图。
- 数据目录：`data/dreambooth/zzmearphone_clean_captioned/`。
- 给每张训练图添加同名 `.txt` sidecar caption。
- 修改训练脚本 `src/external/train_dreambooth_lora_sana.py`，支持从同目录同名 `.txt` 自动读取逐图 caption。
- 训练 rank16 / alpha16 / 400 steps。
- 输出：`outputs/day5_lora_zzmearphone_clean_captioned_400/`。

subject consistency 最新结果：

| Method | Images | Ref similarity | Ref delta vs Base | Ref wins | Subject CLIP | Subject delta vs Base | Subject wins | Prompt CLIPScore |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Base | 8 | 83.659 | 0.000 | 0/8 | 28.487 | 0.000 | 0/8 | 31.525 |
| Original LoRA x2 | 8 | 83.839 | 0.180 | 4/8 | 29.141 | 0.654 | 7/8 | 32.620 |
| Enhanced LoRA x1.5 | 8 | 81.560 | -2.099 | 2/8 | 30.053 | 1.566 | 6/8 | 34.040 |
| Enhanced LoRA x2 | 8 | 76.666 | -6.993 | 0/8 | 27.874 | -0.613 | 3/8 | 32.855 |
| Clean-caption x1.25 | 8 | 83.281 | -0.378 | 5/8 | 28.982 | 0.495 | 5/8 | 33.084 |
| Clean-caption x1.5 | 8 | 81.778 | -1.882 | 4/8 | 28.646 | 0.159 | 4/8 | 32.752 |
| Clean-caption x1.75 | 8 | 79.343 | -4.317 | 2/8 | 28.401 | -0.086 | 5/8 | 32.887 |

最新结论：

- Enhanced LoRA x1.5 是自动 subject-prompt CLIP 和 prompt CLIPScore 最好的设置。
- Original LoRA x2 最接近训练图参考中心，但提升很小。
- Enhanced LoRA x2 和 clean-caption x1.75 都偏强，容易出现结构坍塌或过度简化。
- Clean-caption x1.25 是更保守、更稳的 clean-data compromise：参考相似度接近 Base，并且 5/8 条 prompt 高于 Base。
- 当前结果足够用于课程汇报，不需要立即补拍；如果目标是更强的产品身份复制和展示效果，再补拍更多干净产品图会有价值。

关键文件：

- `src/prepare_lora_dataset.py`
- `src/run_sana_lora_validation.py`
- `src/evaluate_day5_lora_subject_similarity.py`
- `src/evaluate_day5_lora_subject_consistency.py`
- `src/make_day5_lora_figures.py`
- `src/external/train_dreambooth_lora_sana.py`
- `configs/day5_lora_subject_clean_captioned_scale1_25.yaml`
- `configs/day5_lora_subject_clean_captioned_scale1_5.yaml`
- `configs/day5_lora_subject_clean_captioned_scale1_75.yaml`
- `results/day5_lora_summary.md`
- `results/day5_lora_subject_consistency_summary.md`
- `report/day5_lora_evaluation_draft.md`
- `results/figures/day5_lora_subject_consistency_grid.png`

### 3.6 Day 6：Calibrated-PCAS 扩展

完成内容：

- 将 Balanced-PCAS 从手工 8/16/24 policy 扩展为实验校准 policy。
- 对 30 条 benchmark prompt 构建 6 档 steps calibration grid：8、12、16、20、24、28，共 180 张图像。
- 使用 Fixed-20 作为参考，定义最小充分 steps 标签：`CLIPScore(s) >= CLIPScore(Fixed-20) - 0.2`。
- 实现 rule-feature prompt 解析、DeepSeek JSON prompt feature 提取、纯 Python decision tree 训练和 Calibrated-PCAS 推理入口。
- 重跑 Fixed-20、Balanced-PCAS、DeepSeek-Balanced、Calibrated-PCAS 和 LLM-feature Calibrated-PCAS 的可比较输出，并用同一 CLIPScore 评估流程汇总。

核心标签分布：

| Minimal sufficient steps | Prompts |
| ---: | ---: |
| 8 | 18 |
| 12 | 4 |
| 16 | 6 |
| 20 | 2 |

主要结果：

| Method | Avg steps | Avg time no-warmup | Avg CLIPScore | Constraint satisfaction |
| --- | ---: | ---: | ---: | ---: |
| Fixed-20 | 20.000 | 1.537s | 35.762 | 100.0% |
| Balanced-PCAS | 16.000 | 1.740s | 35.772 | 73.3% |
| DeepSeek-Balanced | 18.467 | 2.023s | 35.813 | 73.3% |
| Oracle minimum | 10.933 | 1.112s | 36.276 | 100.0% |
| Calibrated-PCAS | 10.667 | 0.675s | 36.234 | 96.7% |
| LLM-feature Calibrated-PCAS | 11.333 | 1.093s | 36.230 | 96.7% |

关键文件：

- `src/run_sana_calibration_grid.py`
- `src/build_calibration_dataset.py`
- `src/prompt_features.py`
- `src/prompt_features_deepseek.py`
- `src/train_calibrated_pcas_predictor.py`
- `src/run_sana_calibrated_pcas.py`
- `configs/day6_calibrated_pcas.yaml`
- `results/day6_calibration_summary.md`
- `results/day6_calibrated_pcas_summary.md`
- `results/day6_calibrated_pcas_llm_features_summary.md`
- `results/day6_calibrated_pcas_final_comparison_summary.md`
- `report/day6_calibrated_pcas_draft.md`

结论：

- Calibrated-PCAS 把 PCAS 从“按经验分配 steps”推进到“在 Fixed-20 质量约束下预测最小预算”。
- 当前 30 条 prompt 的结果显示，rule-feature 和 LLM-feature 两个 learned policy 都达到 96.7% 约束满足率，明显高于 Balanced-PCAS 和 DeepSeek-Balanced 的 73.3%。
- 由于数据规模小、CLIPScore 对 steps 非单调且 wall-clock latency 有波动，正式报告中应把 Day6 作为 PCAS 的进一步研究扩展，而不是替代 Day3 Balanced-PCAS 主结果。

### 3.7 Day 7：正式报告整合、格式优化与叙事重构

完成内容：

- 将 Day2-Day6 的实验结果整合成完整论文式 LaTeX 报告。
- 按参考报告格式重做前三页：标题页、摘要页、目录页。
- 统一全文中英文字体，并将正文标题字体改成与正文一致的参考报告风格。
- 保留原来的红/蓝配色，不改变整体视觉识别。
- 全局修正表格居中和表题居中。
- 将 Calibrated-PCAS 的最新结论、表格和讨论写入正文。
- 按用户反馈重写结果部分的逻辑，不再单独列“前一版不足”表，而是在每个结果小节中自然解释：
  - 为什么要从 fixed-step baseline 进入 PCAS；
  - 为什么原始 Rule-PCAS 不够；
  - 为什么需要 Balanced-PCAS；
  - 为什么 LLM 标签不能直接映射为更多 steps；
  - 为什么需要 Calibrated-PCAS；
  - 为什么质量结论应保守表述为“保持质量并改善效率-质量权衡”。

关键文件：

- `report/latex/sana_pcas_report.tex`
- `report/latex/sana_pcas_report.pdf`
- `report/PPT_ACADEMIC_REPORT_OUTLINE.md`

当前报告结论定位：

- Balanced-PCAS 仍是最稳健、最容易讲清楚的主效率结果：约 24.6% 平均加速，CLIPScore 基本保持。
- DeepSeek-Balanced 是语义复杂度调度的预算约束版本：说明 LLM feature 有价值，但标签到动作必须校准。
- Calibrated-PCAS 是新版方法深化：把 PCAS 从经验规则推进到 Fixed-20 质量约束下的最小预算预测。
- 质量分析不宣称 PCAS 显著提高图像质量，而强调保持自动文本对齐指标和视觉观感基本相近。
- LoRA 是扩展实验，用于展示 SANA pipeline 可扩展性和小样本个性化的局限。

## 4. 五个“不尽人意”问题及最终处理

先前对话中把项目中“不尽人意”的地方拆成五类。当前状态如下。

| 问题 | 原因 | 已采取方案 | 当前结论 |
| --- | --- | --- | --- |
| 1. PCAS 整体速度收益不大 | 长 prompt 使用 28 steps 抵消短 prompt 收益 | Balanced-PCAS 8/16/24 | 整体加速从 1.9% 提升到 24.6%，可主推 |
| 2. DeepSeek-PCAS 太保守 | 19/30 判 high，平均 steps=23.4 | DeepSeek-Balanced 8/16/22 | 从比 Fixed-20 慢 30.8% 变成快 15.3% |
| 3. Day4 质量指标提升不明显 | CLIPScore 对局部质量不敏感，各方法差距很小 | 改报告定位，补 hard prompt 和视觉差异分析 | 不说提升质量，改说保持质量并改善效率-质量权衡 |
| 4. Guidance 消融不明显 | 3.5-6.5 是平稳区间 | 加 1.5/8.5 stress points | 结论改为中等 guidance 不敏感，低 guidance 不推荐 |
| 5. LoRA 主体一致性不稳定 | 数据少、caption 粗、scale 过强会形变 | enhanced LoRA、clean-captioned LoRA、subject-focused 验证 | 足够支撑汇报，最佳自动设置 enhanced x1.5，保守设置 clean-caption x1.25 |

Day6 的 Calibrated-PCAS 不是原五个问题之一，而是对问题 1 和问题 2 的进一步扩展：用真实 calibration grid 校准“prompt 复杂度标签”和“采样 steps 动作”之间的关系。

## 5. 方法贡献应如何表述

建议正式报告中使用以下贡献点：

1. 复现了 SANA-0.6B diffusers 推理流程，在单张 RTX5080 Laptop GPU 上完成 512x512 文生图实验。
2. 构建了 30 条受控 prompt benchmark，按 10/30/50 words 分组，系统比较 Fixed-10、Fixed-20、Fixed-28。
3. 提出并实现 Prompt-Complexity Adaptive Sampling，包括 rule-based PCAS 和 DeepSeek-assisted PCAS。
4. 针对原始 PCAS 整体加速不足和 DeepSeek-PCAS 过于保守的问题，提出 Balanced-PCAS 与 DeepSeek-Balanced，在保持 CLIPScore 接近的同时显著降低平均推理时间。
5. 追加 Calibrated-PCAS，将自适应采样建模为 Fixed-20 质量约束下的最小 steps 预测，并用可解释 decision tree 近似 oracle 最小预算。
6. 系统评估 steps、guidance scale、prompt complexity 对速度和 CLIPScore 的影响，并通过 hard prompt 定性分析给出更稳健解释。
7. 作为可选增强，复现 SANA DreamBooth LoRA 个性化流程，并围绕主体一致性不稳定问题设计 enhanced LoRA、clean-captioned LoRA 和 subject-focused 验证。

## 6. 最终核心结论

可以写进报告摘要/结论的核心版本：

> 本项目在单张 RTX5080 Laptop GPU 上复现了 SANA-0.6B 的 diffusers 推理流程，并围绕固定采样参数造成的计算浪费问题提出 Prompt-Complexity Adaptive Sampling。实验表明，原始 Rule-PCAS 能在短 prompt 上显著节省推理时间，但在均衡 benchmark 中会被长 prompt 的额外步数抵消。为此，本项目提出 Balanced-PCAS，将 10/30/50-word prompt 的采样步数调整为 8/16/24，使平均步数从 Fixed-20 的 20 降到 16，平均推理时间从 0.996s 降到 0.751s，整体加速约 24.6%，同时 CLIPScore 基本保持不变。对于 LLM-based prompt complexity，本项目发现原始 DeepSeek-PCAS 由于过度保守而变慢，因此提出 DeepSeek-Balanced，在复用同一批语义复杂度标签的基础上将平均时间从 1.303s 降到 0.844s，相比 Fixed-20 快 15.3%。进一步的 Calibrated-PCAS 用 6 档 steps calibration grid 定义每条 prompt 的最小充分预算，在当前 calibration set 上以约 10--11 个平均 steps 达到 96.7% 的 Fixed-20 约束满足率。质量评估显示，各方法 CLIPScore 差距较小，因此 PCAS 更适合定位为一种保持自动对齐指标并改善效率-质量权衡的自适应推理策略，而不是显著提升图像质量的方法。最后，项目复现了 SANA-LoRA DreamBooth 个性化流程，证明小样本 LoRA 在该硬件条件下可行，但主体一致性受数据、caption 和 adapter scale 影响明显，应作为探索性增强而非强定量结论。

## 7. 报告写作时的注意事项

不要这样写：

- “PCAS 显著提升生成质量。”
- “DeepSeek-PCAS 比所有方法更好。”
- “LoRA 已经稳定复制耳机身份。”
- “Guidance 越高越好。”

建议这样写：

- “PCAS 在保持相近 CLIPScore 的同时改善计算预算分配。”
- “Balanced-PCAS 是效率导向版本，DeepSeek-Balanced 是语义调度的预算约束版本。”
- “CLIPScore 差异很小，因此结合定性图和 hard prompt 分析更稳妥。”
- “LoRA 实验证明个性化流程可行，但主体一致性仍依赖训练数据、caption 和 adapter scale。”
- “Guidance 在 3.5-6.5 中等区间较不敏感，低 guidance 明显不利于文本对齐。”

## 8. 当前最值得放进 PPT 的图

| 图 | 路径 | 用途 |
| --- | --- | --- |
| Day2 baseline 网格 | `results/figures/day2_baseline_grid_full_prompts.png` | 展示 fixed-step 复现结果 |
| Day3 PCAS 对比图 | `results/figures/day3_pcas_vs_fixed20_chart.png` | 展示原始 PCAS |
| Balanced-PCAS 速度图 | `results/figures/day3_pcas_balanced_speed_chart.png` | 展示解决问题 1 |
| Balanced-PCAS 速度-质量图 | `results/figures/day3_pcas_balanced_speed_quality_tradeoff.png` | 主结果图 |
| DeepSeek-Balanced 速度图 | `results/figures/day3_deepseek_balanced_speed_chart.png` | 展示解决问题 2 |
| DeepSeek-Balanced 速度-质量图 | `results/figures/day3_deepseek_balanced_speed_quality_tradeoff.png` | LLM-PCAS 主结果图 |
| Day4 速度-质量图 | `results/figures/day4_speed_quality_tradeoff.png` | 解释质量差异不明显 |
| Guidance 消融图 | `results/figures/day4_guidance_ablation_clipscore.png` | 解释 guidance 不敏感 |
| Hard prompt 网格 | `results/figures/day4_hard_prompt_qualitative_grid.png` | 支持视觉打平 |
| Day5 LoRA 对比图 | `results/figures/day5_lora_subject_consistency_grid.png` | 展示 LoRA 主体一致性分析 |
| Day6 Calibrated-PCAS 表 | `results/day6_calibrated_pcas_final_comparison_summary.md` | 展示数据校准 policy、最小充分 steps 与约束满足率 |

## 9. 如果后续继续扩展

优先级从高到低：

1. 制作 PPT，根据 `report/PPT_ACADEMIC_REPORT_OUTLINE.md` 的最新 17-19 页大纲逐页填图。
2. 对正式报告 PDF 做最终人工通读，重点检查图表编号、表格跨页、图片清晰度和中文表达。
3. 如果时间允许，补一个小型人工评分表，尤其用于 hard prompt 和 LoRA 主体一致性。
4. 如果希望 LoRA 展示更强，再补拍 10-15 张干净耳机产品图，覆盖正面、侧面、45 度、平放、立放、折叠、耳罩特写、头梁特写。
5. 如显存和时间允许，可尝试 SANA 1.6B 或更高分辨率作为扩展，不建议作为当前主线。

