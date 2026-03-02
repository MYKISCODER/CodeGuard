#!/usr/bin/env python3
"""
Compare Gold baseline vs E2E results for SemiReal-60 v2
Generate diff report showing cases where decisions differ
"""

import csv
from pathlib import Path
from collections import defaultdict

RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"
MODES = ["STRICT", "STRICT-EXEMPT", "MODERATE", "PERMISSIVE"]


def load_results(filepath):
    """Load results from CSV file"""
    results = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results[row['case_id']] = row
    return results


def compare_mode(mode):
    """Compare Gold vs E2E for a specific mode"""
    mode_slug = mode.lower().replace('-', '_')

    gold_file = RESULTS_DIR / f"sr60v2_gold_{mode_slug}.csv"
    e2e_file = RESULTS_DIR / f"sr60v2_e2e_v4_{mode_slug}.csv"

    if not gold_file.exists():
        print(f"  [SKIP] {mode}: Gold file not found")
        return None

    if not e2e_file.exists():
        print(f"  [SKIP] {mode}: E2E file not found")
        return None

    gold = load_results(gold_file)
    e2e = load_results(e2e_file)

    diffs = []
    for case_id in gold.keys():
        if case_id not in e2e:
            diffs.append({
                'case_id': case_id,
                'issue': 'MISSING_IN_E2E',
                'gold_decision': gold[case_id]['decision'],
                'e2e_decision': 'N/A',
            })
            continue

        gold_decision = gold[case_id]['decision']
        e2e_decision = e2e[case_id]['decision']

        if gold_decision != e2e_decision:
            diffs.append({
                'case_id': case_id,
                'is_trap': gold[case_id]['is_trap'],
                'intent': gold[case_id]['intent_max_allowed'],
                'gold_decision': gold_decision,
                'gold_derived': gold[case_id]['derived_privilege'],
                'e2e_decision': e2e_decision,
                'e2e_derived': e2e[case_id]['derived_privilege'],
                'gold_obfuscation': gold[case_id]['gold_obfuscation'],
                'e2e_behaviors_count': e2e[case_id]['predicted_behaviors_count'],
            })

    return diffs


def main():
    print("=" * 80)
    print("GOLD vs E2E COMPARISON (SemiReal-60 v2)")
    print("=" * 80)

    all_diffs = {}
    total_diffs = 0

    for mode in MODES:
        print(f"\n{mode}:")
        diffs = compare_mode(mode)

        if diffs is None:
            continue

        all_diffs[mode] = diffs
        total_diffs += len(diffs)

        if len(diffs) == 0:
            print(f"  OK: Perfect alignment (0 differences)")
        else:
            print(f"  DIFF: {len(diffs)} differences found")

            # Count by type
            trap_diffs = [d for d in diffs if d.get('is_trap') == 'True']
            benign_diffs = [d for d in diffs if d.get('is_trap') == 'False']

            if trap_diffs:
                print(f"    - Trap cases: {len(trap_diffs)}")
            if benign_diffs:
                print(f"    - Benign cases: {len(benign_diffs)}")

    # Save detailed diff report
    if total_diffs > 0:
        diff_file = RESULTS_DIR / "sr60v2_gold_vs_e2e_v4_diff.csv"
        with open(diff_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'mode', 'case_id', 'is_trap', 'intent',
                'gold_decision', 'gold_derived',
                'e2e_decision', 'e2e_derived',
                'gold_obfuscation', 'e2e_behaviors_count'
            ])

            for mode, diffs in all_diffs.items():
                for d in diffs:
                    if 'issue' in d:
                        writer.writerow([mode, d['case_id'], '?', '?',
                                       d['gold_decision'], '?',
                                       d['e2e_decision'], '?', '?', '?'])
                    else:
                        writer.writerow([
                            mode, d['case_id'], d['is_trap'], d['intent'],
                            d['gold_decision'], d['gold_derived'],
                            d['e2e_decision'], d['e2e_derived'],
                            d['gold_obfuscation'], d['e2e_behaviors_count']
                        ])

        print(f"\nDetailed diff saved to {diff_file.name}")

    print("\n" + "=" * 80)
    print(f"SUMMARY: {total_diffs} total differences across all modes")
    print("=" * 80)

    # Validation
    if total_diffs <= 3:
        print("\nPASS: Diff <= 3 (acceptable for 60 cases)")
    else:
        print(f"\nWARNING: Diff = {total_diffs} > 3 (may need investigation)")


if __name__ == '__main__':
    main()
