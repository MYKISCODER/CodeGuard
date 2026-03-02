# CodeGuard 项目文件清单

**生成时间:** 2026-03-02
**项目:** CodeGuard - 代码智能体仓库级投毒防御系统
**目标会议:** AAAI-27

---

## 📋 目录结构概览

```
CodeGuard/
├── benchmark/          # 测试集（YAML格式）
├── policy/            # Layer 3策略引擎
├── runner/            # 基础运行器
├── scripts/           # 实验脚本
├── baselines/         # Baseline对比脚本
├── results/           # 实验结果（CSV/JSON）
├── outputs/           # 分析报告和图表
├── docs/              # 项目文档
├── figures/           # 图表生成脚本
└── [根目录文件]       # 规格说明、笔记等
```

---

## 1. 核心规格文档（根目录）

### 1.1 规格说明

| 文件 | 作用 | 状态 |
|------|------|------|
| `spec.md` | 英文版研究规格说明（冻结版本） | ✅ 最终版 |
| `spec_cn.md` | 中文版研究规格说明（冻结版本） | ✅ 最终版 |
| `spec_cn - 副本.md` | 中文规格备份 | 📦 备份 |

**内容：** C-L-P威胁空间、Layer 2 Schema、Layer 3策略规则、评测指标定义

### 1.2 项目文档

| 文件 | 作用 |
|------|------|
| `论文讲解.md` | 论文完整讲解文档（面向零基础读者） |
| `论文讨论_extracted.md` | 与GPT/Gemini讨论记录的提取版 |
| `notes.md` | 项目开发笔记 |
| `mvp_cases.csv` | MVP阶段的测试用例 |

### 1.3 任务文档（Word格式）

| 文件 | 作用 |
|------|------|
| `任务.docx` | 任务1文档 |
| `任务2.docx` | 任务2文档（CI配置修复任务） |
| `讲解.docx` | 项目讲解文档 |
| `讲解2.docx` | 项目讲解文档v2 |
| `目前已完成任务.docx` | 已完成任务记录 |

---

## 2. Benchmark测试集（benchmark/）

### 2.1 主要测试集

| 文件 | 规模 | 用途 | 状态 |
|------|------|------|------|
| `mini.yaml` | 20 cases | MVP验证 | ✅ 完成 |
| `mini_e2e.yaml` | 20 cases | MVP端到端测试 | ✅ 完成 |
| `full_e2e.yaml` | 50 cases | 完整端到端测试 | ✅ 完成 |
| `semi_real_20.yaml` | 20 cases | 半真实场景测试集 | ✅ 完成 |
| `semi_real_20_v2.yaml` | 20 cases | SemiReal-20 v2版本 | ✅ 完成 |
| `semireal_60.yaml` | 60 cases | 扩展测试集 | ✅ 完成 |
| `semireal_60_v2.yaml` | 60 cases | **当前主力测试集** | ✅ 最终版 |

**SemiReal-60 v2特点：**
- 60个cases（30 trap + 30 benign）
- 覆盖4种载体（METADATA, DOCS, SOURCE, BUILD）
- 覆盖5个生命周期阶段（SETUP, PLANNING, CODING, EXECUTION, PUBLISH）
- 包含混淆测试（TARGET_HIDING, PAYLOAD_HIDING, CONTENT_DATA）

### 2.2 Hard测试集（回归测试）

| 文件 | 规模 | 用途 |
|------|------|------|
| `semireal_hard3.yaml` | 3 cases | 最小Hard集 |
| `semireal_hard10.yaml` | 10 cases | Hard-10回归测试 |
| `semireal_hard13.yaml` | 13 cases | Hard-13扩展集 |
| `semireal_hard16.yaml` | 16 cases | Hard-16扩展集 |
| `semireal_sr60v2_hard12.yaml` | 12 cases | SR60v2专用Hard集（CI测试） |

**用途：** 快速验证Layer 2 prompt改进，防止回归

### 2.3 模板和文档

| 文件 | 作用 |
|------|------|
| `semireal_60_template.yaml` | SemiReal-60生成模板 |
| `SEMIREAL_60_V2_CHANGES.md` | v2版本变更记录 |

---

## 3. 策略引擎（policy/）

| 文件 | 作用 | 关键功能 |
|------|------|----------|
| `policy_engine.py` | Layer 3确定性策略引擎 | 权限映射、白名单、混淆惩罚、决策仲裁 |

**核心功能：**
- 权限映射规则（R1-R7）
- SAFE_HOSTS白名单（pypi.org, github.com等）
- SENSITIVE_PATHS敏感路径检测
- 4种策略模式（STRICT, STRICT-EXEMPT, MODERATE, PERMISSIVE）
- 确定性决策（ALLOW/BLOCK）

---

## 4. 运行器（runner/）

| 文件 | 作用 |
|------|------|
| `run_policy_only.py` | 仅策略引擎运行器（用于Gold baseline） |

**用途：** 使用gold标签直接测试策略引擎，不涉及Layer 2

---

## 5. 实验脚本（scripts/）

### 5.1 端到端（E2E）运行脚本

**命名规范：** `run_<benchmark>_e2e[_version].py`

#### Mini测试集
- `run_layer2_baseline.py` - Layer 2 baseline（prompt-only）

#### Full测试集
- `run_full_e2e.py` - Full E2E运行器
- `run_full_gold_baseline.py` - Full Gold baseline

#### SemiReal-20测试集
- `run_sr20_e2e.py` - SR20 E2E v1
- `run_sr20v2_e2e.py` - SR20 E2E v2
- `run_sr20v2_e2e_v3.py` - SR20 E2E v3（lifecycle gate）
- `run_sr20v2_e2e_v4.py` - SR20 E2E v4（evidence-first）

#### SemiReal-60测试集
- `run_sr60_e2e.py` - SR60 E2E v1
- `run_sr60v2_e2e_v4.py` - SR60v2 E2E v4
- `run_sr60v2_e2e_v4_1.py` - **SR60v2 E2E v4.1（CI修复版，当前最终版）**

### 5.2 Gold Baseline脚本

**用途：** 使用gold标签测试策略引擎上限

- `run_gold_baseline.py` - Mini Gold baseline
- `run_sr20_gold_baseline.py` - SR20 Gold baseline
- `run_sr20v2_gold_baseline.py` - SR20v2 Gold baseline
- `run_sr60_gold_baseline.py` - SR60 Gold baseline
- `run_sr60v2_gold_baseline.py` - SR60v2 Gold baseline

### 5.3 Hard集回归测试

- `run_hard3.py` - Hard-3回归测试
- `run_hard10.py` - Hard-10回归测试
- `run_hard13.py` - Hard-13回归测试
- `run_hard16.py` - Hard-16回归测试

### 5.4 对比和分析脚本

| 文件 | 作用 |
|------|------|
| `compare_gold_vs_e2e_v3.py` | SR20v2 Gold vs E2E v3差异分析 |
| `compare_sr60v2_gold_vs_e2e_v4.py` | SR60v2 Gold vs E2E v4差异分析 |
| `gen_slice_report_sr20.py` | SR20切片分析报告生成 |
| `gen_ablation_sr20.py` | SR20消融实验表生成 |
| `gen_auditability_comparison_sr20.py` | SR20可审计性对比 |
| `gen_efficiency_cost_sr20.py` | SR20效率成本分析 |

### 5.5 Benchmark生成脚本

| 文件 | 作用 |
|------|------|
| `gen_semireal_60.py` | 生成SemiReal-60测试集 |
| `gen_semireal_60_complete.py` | 生成完整版SR60 |
| `gen_semireal_60_full.py` | 生成全量SR60 |
| `fix_semireal_60_distribution.py` | 修复SR60分布问题 |

### 5.6 可视化脚本

| 文件 | 作用 |
|------|------|
| `plot_llm_judge_drift.py` | 绘制LLM Judge不稳定性图表 |
| `slice_report.py` | 生成切片分析报告 |
| `smoke_test.py` | 冒烟测试 |

---

## 6. Baseline对比脚本（baselines/）

### 6.1 LLM Judge Baseline

| 文件 | 测试集 | 作用 |
|------|--------|------|
| `run_llm_judge.py` | Full | LLM Judge baseline（gpt-4o-mini） |
| `run_llm_judge_sr20.py` | SR20 | SR20 LLM Judge |
| `run_llm_judge_sr60v2.py` | SR60v2 | **SR60v2 LLM Judge（最终版）** |
| `run_llm_instability.py` | Full | LLM Judge不稳定性测试 |
| `run_llm_judge_instability_sr20.py` | SR20 | SR20 LLM Judge不稳定性 |

### 6.2 SAST Baseline

| 文件 | 测试集 | 作用 |
|------|--------|------|
| `run_sast_scan.py` | Full | SAST regex规则扫描 |
| `run_sast_sr20.py` | SR20 | SR20 SAST扫描 |
| `run_sast_sr60v2.py` | SR60v2 | **SR60v2 SAST扫描（最终版）** |

### 6.3 结果汇总脚本

| 文件 | 作用 |
|------|------|
| `gen_main_table.py` | 生成Full主对比表 |
| `gen_main_table_sr20.py` | 生成SR20主对比表 |
| `gen_main_table_sr60v2.py` | **生成SR60v2主对比表（最终版）** |
| `gen_slice_report_sr60v2.py` | **生成SR60v2切片报告（最终版）** |
| `score_baseline.py` | Baseline评分脚本 |

---

## 7. 实验结果（results/）

### 7.1 结果文件命名规范

**格式：** `<benchmark>_<type>_<mode>.csv` 或 `<benchmark>_<type>_raw.json`

**类型：**
- `e2e` - 端到端结果（Layer 2 + Layer 3）
- `gold` - Gold baseline结果（仅Layer 3）
- `baseline_llm_judge` - LLM Judge baseline
- `baseline_sast` - SAST baseline
- `layer2_raw` - Layer 2原始输出（JSON）

**模式：**
- `strict` - STRICT模式
- `strict_exempt` - STRICT-EXEMPT模式
- `moderate` - MODERATE模式
- `permissive` - PERMISSIVE模式

### 7.2 当前最终结果（SR60v2 v4.1）

**核心结果文件：**
- `sr60v2_e2e_v4_1_strict_exempt.csv` - **CodeGuard最终结果（ASR=0.0%, FBR=3.3%）**
- `sr60v2_baseline_llm_judge.csv` - LLM Judge结果（ASR=0.0%, FBR=36.7%）
- `sr60v2_baseline_sast.csv` - SAST结果（ASR=6.7%, FBR=30.0%）
- `sr60v2_layer2_v4_1_raw.json` - Layer 2 v4.1原始输出

### 7.3 其他重要结果

**SR20结果：**
- `sr20v2_e2e_v4_strict_exempt.csv` - SR20 E2E v4结果
- `semireal20_baseline_llm_judge.csv` - SR20 LLM Judge
- `semireal20_baseline_sast.csv` - SR20 SAST

**Full结果：**
- `full_e2e_strict_exempt.csv` - Full E2E结果
- `full_gold_strict_exempt.csv` - Full Gold baseline

**Hard集结果：**
- `hard10_results.json` - Hard-10测试结果
- `hard13_results.json` - Hard-13测试结果
- `hard16_results.json` - Hard-16测试结果

**不稳定性测试：**
- `llm_judge_instability.csv` - LLM Judge不稳定性汇总
- `llm_judge_instability_detail.csv` - 详细记录
- `llm_judge_instability_summary.csv` - 统计摘要

### 7.4 对比分析结果

- `sr60v2_gold_vs_e2e_v4_diff.csv` - Gold vs E2E差异分析
- `main_table_codeguard_vs_baselines.csv` - 主对比表

---

## 8. 分析报告（outputs/）

### 8.1 主对比表

| 文件 | 测试集 | 内容 |
|------|--------|------|
| `semireal60v2_main_table.csv` | SR60v2 | **最终主对比表（CodeGuard vs LLM Judge vs SAST）** |
| `semireal20_main_table.csv` | SR20 | SR20主对比表 |
| `overall_table.csv` | Full | Full主对比表 |

**SR60v2主对比表内容：**
```
CodeGuard (v4.1): ASR=0.0%, FBR=3.3%, Utility=98.3%
LLM Judge:        ASR=0.0%, FBR=36.7%, Utility=81.7%
SAST:             ASR=6.7%, FBR=30.0%, Utility=81.7%
```

### 8.2 切片分析报告

| 文件 | 维度 |
|------|------|
| `semireal60v2_slice_report.csv` | **SR60v2按Carrier/Lifecycle/Obfuscation切片** |
| `semireal20_slice_report.csv` | SR20切片分析 |
| `slice_report.csv` | Full切片分析 |
| `slice_report_STRICT.csv` | STRICT模式切片 |
| `slice_report_MODERATE.csv` | MODERATE模式切片 |
| `slice_report_PERMISSIVE.csv` | PERMISSIVE模式切片 |

### 8.3 专项分析报告

| 文件 | 内容 |
|------|------|
| `semireal20_ablation.csv` | SR20消融实验 |
| `semireal20_auditability_comparison.csv` | SR20可审计性对比 |
| `semireal20_efficiency_cost.csv` | SR20效率成本 |
| `failure_analysis.csv` | 失败案例分析 |

### 8.4 任务执行报告

| 文件 | 内容 |
|------|------|
| `task2_v4_1_completion_report.md` | **任务2完成报告（CI修复验证）** |
| `task2_execution_report.md` | 任务2执行记录 |
| `semireal60v2_execution_fbr_debug.md` | **EXECUTION阶段FBR=100%调试报告** |
| `semireal20_remaining_issues.md` | SR20剩余问题 |
| `semireal20_gold_vs_e2e_v3_diff.csv` | SR20 Gold vs E2E差异 |

### 8.5 图表和可视化

| 文件 | 内容 |
|------|------|
| `figure_llm_judge_drift.png` | LLM Judge不稳定性图表（PNG） |
| `figure_llm_judge_drift.pdf` | LLM Judge不稳定性图表（PDF） |
| `figure_llm_judge_drift.svg` | LLM Judge不稳定性图表（SVG） |
| `figure_llm_judge_drift.jpg` | LLM Judge不稳定性图表（JPG） |
| `figure_llm_judge_drift_caption.txt` | 图表说明文字 |

### 8.6 策略预测结果

| 文件 | 模式 |
|------|------|
| `predictions_STRICT.csv` | STRICT模式预测 |
| `predictions_MODERATE.csv` | MODERATE模式预测 |
| `predictions_PERMISSIVE.csv` | PERMISSIVE模式预测 |

---

## 9. 文档（docs/）

| 文件 | 内容 |
|------|------|
| `项目讲解文档.md` | 完整项目讲解（Part 0-11） |

**内容包括：**
- Part 0: 项目全景图
- Part 1-8: 技术细节讲解
- Part 9: Benchmark演进
- Part 10: 三方对比实验
- Part 11: 论文级完成度评估

---

## 10. 图表生成（figures/）

| 文件 | 作用 |
|------|------|
| `gen_architecture.py` | 生成CodeGuard架构图 |
| `gen_taxonomy_plc.py` | 生成C-L-P三维分类学图 |

---

## 11. 关键指标总结

### 11.1 最终性能（SR60v2 v4.1）

| 系统 | ASR | FBR | Utility | 优势 |
|------|-----|-----|---------|------|
| **CodeGuard** | **0.0%** | **3.3%** | **98.3%** | 最佳综合性能 |
| LLM Judge | 0.0% | 36.7% | 81.7% | FBR高11倍 |
| SAST | 6.7% | 30.0% | 81.7% | 有安全漏洞 |

### 11.2 Benchmark演进

| 版本 | 规模 | 特点 | 状态 |
|------|------|------|------|
| Mini | 20 | MVP验证 | ✅ 完成 |
| Full | 50 | 完整测试 | ✅ 完成 |
| SemiReal-20 | 20 | 半真实场景 | ✅ 完成 |
| **SemiReal-60 v2** | **60** | **论文主力测试集** | ✅ 最终版 |

### 11.3 Layer 2 Prompt演进

| 版本 | 特点 | 问题 | 状态 |
|------|------|------|------|
| v1 | 基础版本 | 过度提取 | 已弃用 |
| v2 | 添加约束 | 仍有误杀 | 已弃用 |
| v3 | Lifecycle gate | 过于激进 | 已弃用 |
| v4 | Evidence-first | CI配置误识别 | 已弃用 |
| **v4.1** | **CI语义区分** | **FBR=3.3%** | ✅ 最终版 |

---

## 12. 论文就绪度检查清单

### 12.1 核心实验 ✅

- [x] 主对比表（CodeGuard vs LLM Judge vs SAST）
- [x] 切片分析（Carrier/Lifecycle/Obfuscation）
- [x] Gold vs E2E对比（验证Layer 2准确性）
- [x] 消融实验（Layer 1/2/3贡献）
- [x] 不稳定性测试（LLM Judge）

### 12.2 关键数据 ✅

- [x] ASR=0.0%（完美安全性）
- [x] FBR=3.3%（低误杀率）
- [x] Utility=98.3%（高效用）
- [x] EXECUTION阶段FBR=0%（关键阶段完美表现）

### 12.3 文档完整性 ✅

- [x] 规格说明（spec.md/spec_cn.md）
- [x] 项目讲解文档
- [x] 实验报告（task2_v4_1_completion_report.md）
- [x] 调试报告（semireal60v2_execution_fbr_debug.md）

---

## 13. 快速导航

### 运行最终实验

```bash
# SR60v2 E2E v4.1（最终版）
python scripts/run_sr60v2_e2e_v4_1.py

# LLM Judge baseline
python baselines/run_llm_judge_sr60v2.py

# SAST baseline
python baselines/run_sast_sr60v2.py

# 生成主对比表
python baselines/gen_main_table_sr60v2.py

# 生成切片报告
python baselines/gen_slice_report_sr60v2.py
```

### 查看最终结果

```bash
# 主对比表
cat outputs/semireal60v2_main_table.csv

# 切片分析
cat outputs/semireal60v2_slice_report.csv

# 完成报告
cat outputs/task2_v4_1_completion_report.md
```

---

**文档完成**
**最后更新:** 2026-03-02
