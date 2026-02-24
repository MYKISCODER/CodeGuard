"""
CodeGuard — Policy-only Gold Baseline

Reads mini_e2e.yaml, uses gold_expected_behaviors directly (no LLM),
feeds them into policy_engine, outputs CSV results for comparison.
"""

import os
import sys
import csv
from pathlib import Path
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "policy"))
from policy_engine import arbitrate_case

BENCHMARK_PATH = Path(__file__).resolve().parent.parent / "benchmark" / "mini_e2e.yaml"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "results"
MODES = ["STRICT", "MODERATE", "PERMISSIVE"]


def run():
    with open(BENCHMARK_PATH, "r", encoding="utf-8") as f:
        cases = yaml.safe_load(f)
    print(f"Loaded {len(cases)} cases from {BENCHMARK_PATH}")

    OUTPUT_DIR.mkdir(exist_ok=True)

    for mode in MODES:
        csv_path = OUTPUT_DIR / f"gold_{mode.lower()}.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "case_id", "is_trap", "intent_max_allowed",
                "gold_obfuscation", "behaviors_count",
                "derived_privilege", "decision", "reasons",
            ])
            for case in cases:
                behaviors = case["gold_expected_behaviors"]
                result = arbitrate_case(behaviors, case["intent_max_allowed"], mode)
                gold_obfusc = behaviors[0].get("obfuscation_scope", "?")
                writer.writerow([
                    case["case_id"],
                    case["is_trap"],
                    case["intent_max_allowed"],
                    gold_obfusc,
                    len(behaviors),
                    result["derived"],
                    result["decision"],
                    " | ".join(result["reasons"]),
                ])
        print(f"Results saved to {csv_path}")

    # Summary
    print("\n" + "=" * 80)
    print("POLICY-ONLY GOLD BASELINE SUMMARY")
    print("=" * 80)
    for mode in MODES:
        csv_path = OUTPUT_DIR / f"gold_{mode.lower()}.csv"
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = list(csv.DictReader(f))
        traps = [r for r in reader if r["is_trap"] == "True"]
        benigns = [r for r in reader if r["is_trap"] == "False"]
        trap_blocked = sum(1 for r in traps if r["decision"] == "BLOCK")
        benign_blocked = sum(1 for r in benigns if r["decision"] == "BLOCK")
        asr = (len(traps) - trap_blocked) / len(traps) if traps else 0
        fbr = benign_blocked / len(benigns) if benigns else 0
        print(f"  {mode:12s}  ASR={asr:.2%}  FBR={fbr:.2%}  "
              f"(trap BLOCK={trap_blocked}/{len(traps)}, benign BLOCK={benign_blocked}/{len(benigns)})")
    print("=" * 80)


if __name__ == "__main__":
    run()
