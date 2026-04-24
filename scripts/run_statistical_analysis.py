"""
CodeGuard Statistical Significance Analysis on SemiReal-120 v1

1. 95% Bootstrap CI for ASR/FBR/Utility
2. McNemar test (CodeGuard vs each baseline)
3. CI upper bound for real-world zero-FP
"""

import os
import sys
import csv
import json
import numpy as np
from pathlib import Path
from scipy import stats

PRIV_RANK = {"L0": 0, "L1": 1, "L2": 2, "L3": 3, "L4": 4}
RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"

# Result files
RESULT_FILES = {
    "CodeGuard": RESULTS_DIR / "sr120v1_e2e_v4_1_strict_exempt.csv",
    "Strong LLM Judge (gpt-4o)": RESULTS_DIR / "sr120v1_baseline_strong_llm_judge_gpt_4o.csv",
    "LLM Judge (gpt-4o-mini)": RESULTS_DIR / "sr120v1_baseline_llm_judge.csv",
    "Semgrep": RESULTS_DIR / "sr120v1_baseline_semgrep.csv",
    "Bandit": RESULTS_DIR / "sr120v1_baseline_bandit.csv",
}


def load_results(path):
    """Load CSV results, return list of dicts."""
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def get_decisions(rows):
    """Extract (is_trap, decision) pairs."""
    results = []
    for r in rows:
        is_trap = r["is_trap"] == "True"
        decision = r["decision"]
        results.append((is_trap, decision))
    return results


def bootstrap_ci(data, metric_fn, n_boot=10000, alpha=0.05):
    """Compute bootstrap confidence interval for a metric."""
    rng = np.random.RandomState(42)
    n = len(data)
    boot_vals = []
    for _ in range(n_boot):
        idx = rng.randint(0, n, size=n)
        sample = [data[i] for i in idx]
        boot_vals.append(metric_fn(sample))
    boot_vals = sorted(boot_vals)
    lo = boot_vals[int(n_boot * alpha / 2)]
    hi = boot_vals[int(n_boot * (1 - alpha / 2))]
    point = metric_fn(data)
    return point, lo, hi


def asr_fn(data):
    traps = [d for d in data if d[0]]
    if not traps:
        return 0.0
    return sum(1 for _, dec in traps if dec == "ALLOW") / len(traps)


def fbr_fn(data):
    benigns = [d for d in data if not d[0]]
    if not benigns:
        return 0.0
    return sum(1 for _, dec in benigns if dec == "BLOCK") / len(benigns)


def utility_fn(data):
    if not data:
        return 0.0
    wrong = sum(1 for is_trap, dec in data
                if (is_trap and dec == "ALLOW") or (not is_trap and dec == "BLOCK"))
    return 1 - wrong / len(data)


def mcnemar_test(decisions_a, decisions_b):
    """McNemar test comparing two systems' correctness.
    Correct = trap BLOCKED or benign ALLOWED."""
    n = len(decisions_a)
    # b = A correct, B wrong; c = A wrong, B correct
    b, c = 0, 0
    for (trap_a, dec_a), (trap_b, dec_b) in zip(decisions_a, decisions_b):
        correct_a = (trap_a and dec_a == "BLOCK") or (not trap_a and dec_a == "ALLOW")
        correct_b = (trap_b and dec_b == "BLOCK") or (not trap_b and dec_b == "ALLOW")
        if correct_a and not correct_b:
            b += 1
        elif not correct_a and correct_b:
            c += 1
    # McNemar with continuity correction
    if b + c == 0:
        return 1.0, b, c
    chi2 = (abs(b - c) - 1) ** 2 / (b + c)
    p_value = 1 - stats.chi2.cdf(chi2, df=1)
    return p_value, b, c


def zero_fp_ci_upper(n_total, n_fp=0, confidence=0.95):
    """Clopper-Pearson upper bound for zero false positives."""
    alpha = 1 - confidence
    if n_fp == 0:
        upper = 1 - (alpha) ** (1 / n_total)
    else:
        upper = stats.beta.ppf(1 - alpha / 2, n_fp + 1, n_total - n_fp)
    return upper


def run():
    print("CodeGuard Statistical Significance Analysis\n")
    print("=" * 75)

    # Load all results
    all_decisions = {}
    for name, path in RESULT_FILES.items():
        if path.exists():
            rows = load_results(path)
            all_decisions[name] = get_decisions(rows)
            print(f"  Loaded {name}: {len(rows)} cases")
        else:
            print(f"  [SKIP] {name}: file not found")

    # 1. Bootstrap CI
    print(f"\n{'='*75}")
    print("1. 95% Bootstrap Confidence Intervals (10,000 resamples)")
    print(f"{'='*75}")
    print(f"{'System':<35s} {'ASR':>18s} {'FBR':>18s} {'Utility':>18s}")
    print("-" * 92)

    ci_results = {}
    for name, decisions in all_decisions.items():
        asr_pt, asr_lo, asr_hi = bootstrap_ci(decisions, asr_fn)
        fbr_pt, fbr_lo, fbr_hi = bootstrap_ci(decisions, fbr_fn)
        util_pt, util_lo, util_hi = bootstrap_ci(decisions, utility_fn)
        ci_results[name] = {
            "asr": (asr_pt, asr_lo, asr_hi),
            "fbr": (fbr_pt, fbr_lo, fbr_hi),
            "utility": (util_pt, util_lo, util_hi),
        }
        print(f"{name:<35s} "
              f"{asr_pt:>5.1%} [{asr_lo:.1%},{asr_hi:.1%}] "
              f"{fbr_pt:>5.1%} [{fbr_lo:.1%},{fbr_hi:.1%}] "
              f"{util_pt:>5.1%} [{util_lo:.1%},{util_hi:.1%}]")

    # 2. McNemar tests
    print(f"\n{'='*75}")
    print("2. McNemar Tests (CodeGuard vs each baseline)")
    print(f"{'='*75}")

    if "CodeGuard" in all_decisions:
        cg = all_decisions["CodeGuard"]
        print(f"{'Comparison':<45s} {'b':>4s} {'c':>4s} {'p-value':>10s} {'Sig?':>6s}")
        print("-" * 72)
        for name, decisions in all_decisions.items():
            if name == "CodeGuard":
                continue
            p_val, b, c = mcnemar_test(cg, decisions)
            sig = "***" if p_val < 0.001 else "**" if p_val < 0.01 else "*" if p_val < 0.05 else "ns"
            print(f"CodeGuard vs {name:<31s} {b:>4d} {c:>4d} {p_val:>10.4f} {sig:>6s}")

    # 3. Zero-FP CI upper bound
    print(f"\n{'='*75}")
    print("3. Zero False-Positive CI Upper Bound (Clopper-Pearson)")
    print(f"{'='*75}")
    # Real-world: 0/50 files, 0/10 repos
    for desc, n_total, n_fp in [("Real-world files (0/50)", 50, 0),
                                 ("Real-world repos (0/10)", 10, 0),
                                 ("SR120 benign (2/60)", 60, 2)]:
        upper = zero_fp_ci_upper(n_total, n_fp)
        print(f"  {desc:<35s}: upper bound = {upper:.1%} (95% CI)")

    # Save summary
    out_path = RESULTS_DIR / "sr120v1_statistical_analysis.json"
    summary = {
        "bootstrap_ci": {name: {k: [round(v, 4) for v in vals]
                                for k, vals in ci.items()}
                         for name, ci in ci_results.items()},
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to {out_path}")


if __name__ == "__main__":
    run()
