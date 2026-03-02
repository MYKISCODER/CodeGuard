"""
Compare SemiReal-20 Gold v2 vs E2E v3 results and generate diff report.
"""

import csv
from pathlib import Path

RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"
OUTPUTS_DIR = Path(__file__).resolve().parent.parent / "outputs"
MODE = "STRICT-EXEMPT"  # Focus on the best mode

def load_results(csv_path):
    """Load results from CSV into a dict keyed by case_id."""
    results = {}
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            results[row["case_id"]] = row
    return results

def main():
    # Load Gold v2 and E2E v3 results
    gold_path = RESULTS_DIR / f"sr20v2_gold_{MODE.lower().replace('-','_')}.csv"
    e2e_path = RESULTS_DIR / f"sr20v2_e2e_v3_{MODE.lower().replace('-','_')}.csv"

    gold_results = load_results(gold_path)
    e2e_results = load_results(e2e_path)

    # Find divergences
    divergences = []
    for case_id in gold_results:
        gold = gold_results[case_id]
        e2e = e2e_results[case_id]

        if gold["decision"] != e2e["decision"]:
            divergences.append({
                "case_id": case_id,
                "is_trap": gold["is_trap"],
                "intent": gold["intent_max_allowed"],
                "gold_decision": gold["decision"],
                "gold_derived": gold["derived_privilege"],
                "e2e_decision": e2e["decision"],
                "e2e_derived": e2e["derived_privilege"],
                "e2e_behaviors_count": e2e["predicted_behaviors_count"],
                "divergence_type": "FALSE_NEGATIVE" if gold["is_trap"] == "True" and e2e["decision"] == "ALLOW" else "FALSE_POSITIVE",
            })

    # Save diff report
    OUTPUTS_DIR.mkdir(exist_ok=True)
    diff_path = OUTPUTS_DIR / "semireal20_gold_vs_e2e_v3_diff.csv"

    with open(diff_path, "w", newline="", encoding="utf-8") as f:
        if divergences:
            writer = csv.DictWriter(f, fieldnames=divergences[0].keys())
            writer.writeheader()
            writer.writerows(divergences)
        else:
            # Empty file with header only
            writer = csv.writer(f)
            writer.writerow(["case_id", "is_trap", "intent", "gold_decision", "gold_derived",
                           "e2e_decision", "e2e_derived", "e2e_behaviors_count", "divergence_type"])

    # Print summary
    print("=" * 80)
    print(f"SEMIREAL-20 GOLD V2 VS E2E V3 COMPARISON ({MODE} mode)")
    print("=" * 80)
    print(f"Total cases: {len(gold_results)}")
    print(f"Divergences: {len(divergences)}")

    if divergences:
        false_negatives = [d for d in divergences if d["divergence_type"] == "FALSE_NEGATIVE"]
        false_positives = [d for d in divergences if d["divergence_type"] == "FALSE_POSITIVE"]

        print(f"  - False Negatives (trap leaked): {len(false_negatives)}")
        for d in false_negatives:
            print(f"    * {d['case_id']}: Gold BLOCK -> E2E ALLOW (derived: {d['gold_derived']} -> {d['e2e_derived']})")

        print(f"  - False Positives (benign blocked): {len(false_positives)}")
        for d in false_positives:
            print(f"    * {d['case_id']}: Gold ALLOW -> E2E BLOCK (derived: {d['gold_derived']} -> {d['e2e_derived']})")
    else:
        print("✓ Perfect alignment! E2E v3 matches Gold v2 exactly.")

    print(f"\nDiff report saved to: {diff_path}")
    print("=" * 80)

    # Return exit code based on divergence count
    return len(divergences)

if __name__ == "__main__":
    import sys
    divergence_count = main()
    sys.exit(0 if divergence_count <= 1 else 1)  # Accept ≤1 divergence
