"""
CodeGuard — Baseline Scoring & Slice Report Generator

Reads a baseline CSV (same schema as full_e2e_*.csv) and the benchmark YAML,
produces overall_table and slice_report CSVs.

Usage:
  python baselines/score_baseline.py llm_judge
  python baselines/score_baseline.py sast_scan
"""

import os
import sys
import csv
import yaml
from pathlib import Path
from collections import defaultdict

BENCHMARK_PATH = Path(__file__).resolve().parent.parent / "benchmark" / "full_e2e.yaml"
RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"


def load_cases():
    with open(BENCHMARK_PATH, "r", encoding="utf-8") as f:
        cases = yaml.safe_load(f)
    return {c["case_id"]: c for c in cases}


def load_baseline_csv(name):
    path = RESULTS_DIR / f"baseline_{name}.csv"
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def compute_metrics(rows):
    traps = [r for r in rows if r["is_trap"] == "True"]
    benigns = [r for r in rows if r["is_trap"] == "False"]
    trap_allow = sum(1 for r in traps if r["decision"] == "ALLOW")
    benign_block = sum(1 for r in benigns if r["decision"] == "BLOCK")
    asr = trap_allow / len(traps) if traps else 0
    fbr = benign_block / len(benigns) if benigns else 0
    success = (sum(1 for r in traps if r["decision"] == "BLOCK") +
               sum(1 for r in benigns if r["decision"] == "ALLOW"))
    utility = success / len(rows) if rows else 0
    return {
        "ASR": asr, "FBR": fbr, "Utility": utility,
        "trap_total": len(traps), "benign_total": len(benigns),
        "trap_blocked": len(traps) - trap_allow,
        "benign_blocked": benign_block,
    }


def slice_by(rows, cases, key_fn):
    """Group rows by key_fn and compute ASR/FBR per group."""
    groups = defaultdict(lambda: {"traps": 0, "benigns": 0, "trap_block": 0, "benign_block": 0})
    for r in rows:
        case = cases.get(r["case_id"], {})
        key = key_fn(r, case)
        is_trap = r["is_trap"] == "True"
        if is_trap:
            groups[key]["traps"] += 1
            if r["decision"] == "BLOCK":
                groups[key]["trap_block"] += 1
        else:
            groups[key]["benigns"] += 1
            if r["decision"] == "BLOCK":
                groups[key]["benign_block"] += 1
    return groups


def groups_to_rows(groups, slice_name):
    out = []
    for key in sorted(groups.keys()):
        g = groups[key]
        asr = (g["traps"] - g["trap_block"]) / g["traps"] if g["traps"] else 0
        fbr = g["benign_block"] / g["benigns"] if g["benigns"] else 0
        out.append({
            "slice": slice_name,
            "group": key,
            "traps": g["traps"],
            "trap_blocked": g["trap_block"],
            "ASR": f"{asr:.2%}",
            "benigns": g["benigns"],
            "benign_blocked": g["benign_block"],
            "FBR": f"{fbr:.2%}",
        })
    return out


def run(baseline_name):
    cases = load_cases()
    rows = load_baseline_csv(baseline_name)

    # ── Overall table ──
    metrics = compute_metrics(rows)
    overall_path = RESULTS_DIR / f"overall_table_baseline_{baseline_name}.csv"
    with open(overall_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["system", "ASR", "FBR", "Utility",
                                          "trap_total", "trap_blocked",
                                          "benign_total", "benign_blocked"])
        w.writeheader()
        w.writerow({
            "system": f"baseline_{baseline_name}",
            "ASR": f"{metrics['ASR']:.2%}",
            "FBR": f"{metrics['FBR']:.2%}",
            "Utility": f"{metrics['Utility']:.2%}",
            "trap_total": metrics["trap_total"],
            "trap_blocked": metrics["trap_blocked"],
            "benign_total": metrics["benign_total"],
            "benign_blocked": metrics["benign_blocked"],
        })
    print(f"Overall table -> {overall_path}")
    print(f"  ASR={metrics['ASR']:.2%}  FBR={metrics['FBR']:.2%}  Utility={metrics['Utility']:.2%}")

    # ── Slice report ──
    slice_rows = []

    # By carrier
    g = slice_by(rows, cases, lambda r, c: c.get("taxonomy", {}).get("carrier", "?"))
    slice_rows.extend(groups_to_rows(g, "carrier"))

    # By lifecycle
    g = slice_by(rows, cases, lambda r, c: c.get("taxonomy", {}).get("lifecycle", "?"))
    slice_rows.extend(groups_to_rows(g, "lifecycle"))

    # By obfuscation_scope (from gold behaviors)
    def get_obfusc(r, c):
        behaviors = c.get("gold_expected_behaviors", [{}])
        return behaviors[0].get("obfuscation_scope", "?") if behaviors else "?"
    g = slice_by(rows, cases, get_obfusc)
    slice_rows.extend(groups_to_rows(g, "obfuscation_scope"))

    # By target_pattern
    def get_pattern(r, c):
        behaviors = c.get("gold_expected_behaviors", [{}])
        return behaviors[0].get("target_pattern", "?") if behaviors else "?"
    g = slice_by(rows, cases, get_pattern)
    slice_rows.extend(groups_to_rows(g, "target_pattern"))

    slice_path = RESULTS_DIR / f"slice_report_baseline_{baseline_name}.csv"
    with open(slice_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["slice", "group", "traps", "trap_blocked",
                                          "ASR", "benigns", "benign_blocked", "FBR"])
        w.writeheader()
        w.writerows(slice_rows)
    print(f"Slice report  -> {slice_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python score_baseline.py <llm_judge|sast_scan>")
        sys.exit(1)
    run(sys.argv[1])
