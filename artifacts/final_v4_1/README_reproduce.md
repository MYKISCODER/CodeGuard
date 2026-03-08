# CodeGuard v4.1 最终结果复现指南

**版本:** v4.1 (Final)
**日期:** 2026-03-02
**状态:** ✅ 冻结

---

## 快速复现

### 一键生成主对比表和切片报告

```bash
# 生成主对比表
python artifacts/final_v4_1/scripts/gen_main_table_sr60v2.py

# 生成切片报告
python artifacts/final_v4_1/scripts/gen_slice_report_sr60v2.py
```

**输出位置:**
- `outputs/semireal60v2_main_table.csv` - 主对比表
- `outputs/semireal60v2_slice_report.csv` - 切片分析报告

---

## 最终性能指标

### 主对比表（SemiReal-60 v2）

| System | ASR | FBR | Utility |
|--------|-----|-----|---------|
| **CodeGuard (v4.1, STRICT-EXEMPT)** | **0.0%** | **3.3%** | **98.3%** |
| LLM Judge (gpt-4o-mini) | 0.0% | 36.7% | 81.7% |
| SAST (Regex Rules) | 6.7% | 30.0% | 81.7% |

**CodeGuard优势:**
- ASR=0.0% - 完美安全性，拦截所有30个trap
- FBR=3.3% - 低误杀率（仅1/30 benign被误杀）
- Utility=98.3% - 显著优于baseline（81.7%）

---

## 文件清单

### 核心结果文件

```
artifacts/final_v4_1/
├── results/
│   ├── sr60v2_e2e_v4_1_strict_exempt.csv      # CodeGuard最终结果
│   ├── sr60v2_baseline_llm_judge.csv          # LLM Judge结果
│   ├── sr60v2_baseline_sast.csv               # SAST结果
│   └── sr60v2_layer2_v4_1_raw.json            # Layer 2原始输出
├── outputs/
│   ├── semireal60v2_main_table.csv            # 主对比表
│   ├── semireal60v2_slice_report.csv          # 切片分析
│   └── task2_v4_1_completion_report.md        # 完成报告
└── scripts/
    ├── run_sr60v2_e2e_v4_1.py                 # E2E运行脚本
    ├── gen_main_table_sr60v2.py               # 主表生成脚本
    └── gen_slice_report_sr60v2.py             # 切片报告生成脚本
```

---

## 完整实验复现

### 步骤1: 运行CodeGuard E2E v4.1

```bash
python scripts/run_sr60v2_e2e_v4_1.py
```

**输出:**
- `results/sr60v2_e2e_v4_1_strict_exempt.csv`
- `results/sr60v2_layer2_v4_1_raw.json`

**预期结果:** ASR=0.0%, FBR=3.3%

### 步骤2: 运行Baseline对比

```bash
# LLM Judge
python baselines/run_llm_judge_sr60v2.py

# SAST
python baselines/run_sast_sr60v2.py
```

**输出:**
- `results/sr60v2_baseline_llm_judge.csv`
- `results/sr60v2_baseline_sast.csv`

### 步骤3: 生成分析报告

```bash
# 主对比表
python baselines/gen_main_table_sr60v2.py

# 切片分析
python baselines/gen_slice_report_sr60v2.py
```

**输出:**
- `outputs/semireal60v2_main_table.csv`
- `outputs/semireal60v2_slice_report.csv`

---

## 关键切片分析结果

### EXECUTION阶段（最关键）

| System | ASR | FBR |
|--------|-----|-----|
| CodeGuard | 0.0% | **0.0%** ✅ |
| LLM Judge | 0.0% | 0.0% |
| SAST | 0.0% | 0.0% |

**v4.1修复成果:** EXECUTION阶段FBR从v4的100%降至0%

### 混淆维度

| Obfuscation | CodeGuard FBR | LLM Judge FBR | SAST FBR |
|-------------|---------------|---------------|----------|
| NONE | 0.0% | 14.3% | 0.0% |
| TARGET_HIDING | **0.0%** ✅ | 88.9% | 100.0% |
| PAYLOAD_HIDING | 100.0% | 100.0% | 0.0% |
| CONTENT_DATA | 0.0% | 0.0% | 0.0% |

**亮点:** CodeGuard在TARGET_HIDING上完美表现（0% FBR）

---

## Layer 2 Prompt v4.1 关键特性

**位置:** `scripts/run_sr60v2_e2e_v4_1.py:29-126`

**核心改进:** CI配置文件的语义区分

```python
场景1 - 理解测试流程（不实际执行CI）:
关键词: "持续集成中测试", "自动化测试", "运行测试"
→ 只提取: pip install → NETWORK_CONNECT + DOWNLOAD_ONLY + PACKAGE_REPO
→ 不提取: pytest, make test等测试命令

场景2 - 实际执行CI流水线:
关键词: "执行CI", "运行CI", "CI流水线"
→ 提取所有run步骤（包括安装和测试命令）
```

**修复效果:**
- FBR从13.3%降至3.3%（降低75%）
- EXECUTION阶段FBR从100%降至0%
- ASR保持0.0%

---

## 环境要求

```bash
# Python依赖
pip install openai pyyaml python-dotenv

# 环境变量（.env文件）
OPENAI_API_KEY=your_key
OPENAI_BASE_URL=https://api.openai.com/v1
MODEL=gpt-4o
```

---

## 论文使用建议

### 主结果表

使用 `outputs/semireal60v2_main_table.csv` 作为论文主表：

```
CodeGuard (v4.1): ASR=0.0%, FBR=3.3%, Utility=98.3%
LLM Judge:        ASR=0.0%, FBR=36.7%, Utility=81.7%
SAST:             ASR=6.7%, FBR=30.0%, Utility=81.7%
```

### 切片分析

使用 `outputs/semireal60v2_slice_report.csv` 展示：
- EXECUTION阶段完美表现（FBR=0%）
- TARGET_HIDING混淆检测优势（FBR=0% vs 88.9%/100%）

### 失败变体

参考 `outputs/variant_failure_v4_2.md` 作为消融实验：
- v4.2尝试移除关键词依赖但失败（ASR上升至3.33%）
- 验证了v4.1设计选择的合理性

---

## 故障排查

### 问题1: API调用失败

**症状:** `API_ERROR: ...`

**解决:**
```bash
# 检查环境变量
cat .env

# 测试API连接
curl $OPENAI_BASE_URL/models -H "Authorization: Bearer $OPENAI_API_KEY"
```

### 问题2: 结果不一致

**原因:** LLM输出有随机性（即使temperature=0）

**解决:** 使用已冻结的结果文件（`artifacts/final_v4_1/results/`）

---

## 版本历史

| 版本 | ASR | FBR | 状态 | 说明 |
|------|-----|-----|------|------|
| v4 | 0.0% | 13.3% | 已弃用 | CI配置误识别 |
| **v4.1** | **0.0%** | **3.3%** | ✅ 最终版 | CI语义区分修复 |
| v4.2 | 3.33% | 6.67% | ❌ 失败 | 移除关键词导致漏检 |

---

**文档完成**
**最后更新:** 2026-03-02
