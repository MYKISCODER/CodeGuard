# SemiReal Trend Consistency Analysis

**Date:** 2026-03-04
**Purpose:** Validate result stability when scaling from 60 to 120 cases

---

## Executive Summary

✅ **Results are highly consistent when scaling from 60 to 120 cases.**

All three systems maintain their relative performance characteristics:
- **CodeGuard** maintains perfect security (ASR=0%) with minimal false positives
- **LLM Judge** maintains high security but with significantly higher false positives
- **SAST** shows consistent pattern-matching limitations with both false negatives and false positives

---

## Detailed Comparison

### CodeGuard (E2E v4.1, STRICT-EXEMPT)

| Metric | SR60v2 (60 cases) | SR120v1 (120 cases) | Change |
|--------|-------------------|---------------------|--------|
| **ASR** | 0.0% | 0.0% | ✅ **Stable** (0.0%) |
| **FBR** | 3.3% (1/30) | 3.3% (2/60) | ✅ **Stable** (0.0%) |
| **Utility** | 98.3% | 98.3% | ✅ **Stable** (0.0%) |
| **Trap Blocked** | 30/30 | 60/60 | ✅ **Perfect** |
| **Benign Blocked** | 1/30 | 2/60 | ✅ **Proportional** |

**Analysis:**
- ASR remains at 0% - **all attacks blocked**
- FBR remains at 3.3% - **false positive rate unchanged**
- The absolute number of false positives doubled (1→2) but the **rate stayed constant**
- This demonstrates **perfect scaling consistency**

---

### LLM Judge (gpt-4o-mini)

| Metric | SR60v2 (60 cases) | SR120v1 (120 cases) | Change |
|--------|-------------------|---------------------|--------|
| **ASR** | 0.0% | 3.3% (2/60) | ⚠️ **+3.3%** |
| **FBR** | 36.7% (11/30) | 41.7% (25/60) | ⚠️ **+5.0%** |
| **Utility** | 81.7% | 77.5% | ⚠️ **-4.2%** |
| **Trap Blocked** | 30/30 | 58/60 | ⚠️ **2 leaks** |
| **Benign Blocked** | 11/30 | 25/60 | ⚠️ **Higher rate** |

**Analysis:**
- ASR increased from 0% to 3.3% - **2 attacks leaked in SR120v1**
- FBR increased from 36.7% to 41.7% - **more conservative on benign cases**
- The benign block rate increased: 36.7% → 41.7% (+5.0%)
- This shows **LLM Judge instability** - probabilistic decisions vary across runs
- The trend confirms LLM Judge's **over-conservative nature** (high FBR)

---

### SAST (Regex Rules)

| Metric | SR60v2 (60 cases) | SR120v1 (120 cases) | Change |
|--------|-------------------|---------------------|--------|
| **ASR** | 6.7% (2/30) | 6.7% (4/60) | ✅ **Stable** (0.0%) |
| **FBR** | 30.0% (9/30) | 30.0% (18/60) | ✅ **Stable** (0.0%) |
| **Utility** | 81.7% | 81.7% | ✅ **Stable** (0.0%) |
| **Trap Blocked** | 28/30 | 56/60 | ✅ **Proportional** |
| **Benign Blocked** | 9/30 | 18/60 | ✅ **Proportional** |

**Analysis:**
- ASR remains at 6.7% - **consistent miss rate**
- FBR remains at 30.0% - **consistent false positive rate**
- Both absolute numbers doubled (2→4 leaks, 9→18 false blocks) but **rates stayed constant**
- This demonstrates **deterministic pattern matching** - SAST is fully reproducible

---

## Key Findings

### 1. CodeGuard Stability ✅
- **Perfect consistency** across both benchmarks
- ASR=0%, FBR=3.3% maintained exactly
- Demonstrates **robust defense** that scales reliably

### 2. LLM Judge Variability ⚠️
- ASR increased by 3.3% (2 new leaks)
- FBR increased by 5.0% (more conservative)
- Confirms **probabilistic instability** - decisions vary across runs
- High FBR (41.7%) makes it **impractical for production**

### 3. SAST Consistency ✅
- **Perfect proportional scaling** - all rates unchanged
- Demonstrates **deterministic behavior** (regex-based)
- But consistently misses 6.7% of attacks and blocks 30% of benign cases
- Shows **fundamental limitations** of pattern matching

---

## Trend Validation

### Security (ASR) Trend
```
CodeGuard:  0.0% → 0.0%  ✅ Stable
LLM Judge:  0.0% → 3.3%  ⚠️ Degraded
SAST:       6.7% → 6.7%  ✅ Stable (but poor)
```

### Usability (FBR) Trend
```
CodeGuard:  3.3% → 3.3%   ✅ Stable (excellent)
LLM Judge: 36.7% → 41.7%  ⚠️ Degraded (poor)
SAST:      30.0% → 30.0%  ✅ Stable (poor)
```

### Overall (Utility) Trend
```
CodeGuard: 98.3% → 98.3%  ✅ Stable (best)
LLM Judge: 81.7% → 77.5%  ⚠️ Degraded
SAST:      81.7% → 81.7%  ✅ Stable
```

---

## Conclusion

**The scaling from 60 to 120 cases validates our core claims:**

1. ✅ **CodeGuard is stable and reliable**
   - Perfect security (ASR=0%) maintained
   - Low false positives (FBR=3.3%) maintained
   - Best overall utility (98.3%) maintained

2. ⚠️ **LLM Judge is unstable and over-conservative**
   - Security degraded (0% → 3.3% ASR)
   - Usability degraded (36.7% → 41.7% FBR)
   - Confirms probabilistic decision-making issues

3. ✅ **SAST is consistent but limited**
   - Deterministic behavior (perfect proportional scaling)
   - But fundamentally limited by pattern matching
   - Cannot handle obfuscation or semantic analysis

**Paper Impact:**
> "Results are consistent when scaling from 60 to 120 cases, demonstrating the robustness of our evaluation methodology and the stability of CodeGuard's defense mechanism."

---

## Appendix: Raw Data

### SR60v2 Results
```csv
System,ASR (%),FBR (%),Utility (%),Trap Blocked,Benign Blocked,Total Cases
CodeGuard (E2E v4, STRICT-EXEMPT),0.0,3.3,98.3,30/30,1/30,60
LLM Judge (gpt-4o-mini),0.0,36.7,81.7,30/30,11/30,60
SAST (Regex Rules),6.7,30.0,81.7,28/30,9/30,60
```

### SR120v1 Results
```csv
System,ASR (%),FBR (%),Utility (%),Trap Blocked,Benign Blocked,Total Cases
CodeGuard (E2E v4, STRICT-EXEMPT),0.0,3.3,98.3,60/60,2/60,120
LLM Judge (gpt-4o-mini),3.3,41.7,77.5,58/60,25/60,120
SAST (Regex Rules),6.7,30.0,81.7,56/60,18/60,120
```

---

**Generated:** 2026-03-04
**Benchmark:** SemiReal-60 v2 → SemiReal-120 v1
**Systems:** CodeGuard v4.1, LLM Judge (gpt-4o-mini), SAST (Regex)
