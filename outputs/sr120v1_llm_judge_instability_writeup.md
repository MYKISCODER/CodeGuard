# LLM Judge Instability Analysis (SR120v1)

**Date:** 2026-03-04
**Model:** gpt-4o-mini
**Experiment:** 5 prompt variants × 2 temperatures = 10 runs

---

## Drift Range Summary

**ASR (Attack Success Rate):**
- Min: 0.0%
- Max: 5.0%
- Mean: 1.8%
- Std: 2.29%
- **Range: 5.0%**

**FBR (False Block Rate):**
- Min: 8.3%
- Max: 100.0%
- Mean: 52.0%
- Std: 32.40%
- **Range: 91.7%**

**Utility:**
- Min: 50.0%
- Max: 93.3%
- Mean: 73.1%
- Std: 15.18%
- **Range: 43.3%**

---

## Key Findings

1. **LLM Judge exhibits significant drift** across different prompts and temperatures, with ASR ranging from 0.0% to 5.0% and FBR ranging from 8.3% to 100.0%.

2. **Probabilistic instability** is evidenced by non-zero standard deviations (ASR σ=2.29%, FBR σ=32.40%), indicating that LLM Judge's decisions vary unpredictably based on prompt phrasing and sampling parameters.

3. **In contrast, CodeGuard maintains σ=0** for all metrics across scales (SR60v2 → SR120v1), demonstrating deterministic and auditable behavior suitable for production deployment.

4. **Production risk:** The drift range of 5.0% in ASR and 91.7% in FBR makes LLM Judge unsuitable for security-critical applications where consistent enforcement is required.

---

## Paper-Ready Text

> To quantify LLM Judge's probabilistic instability, we conducted a drift analysis on SemiReal-120 v1 using 5 prompt variants and 2 temperature settings (10 runs total). Results show significant variation: ASR ranges from 0.0% to 5.0% (σ=2.29%), and FBR ranges from 8.3% to 100.0% (σ=32.40%). In contrast, CodeGuard exhibits zero variance (σ=0) across all metrics and scales, confirming its deterministic and auditable nature. This instability renders LLM Judge unsuitable for production security enforcement where consistent policy application is critical.

---

**Generated:** 2026-03-04
**Experiment:** LLM Judge Instability on SR120v1
**Total API Calls:** 1200
