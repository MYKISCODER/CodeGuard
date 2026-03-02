"""
Generate slice report for SemiReal-20

Analyzes CodeGuard E2E v4 performance by:
- Carrier (DOCS, METADATA, SOURCE, BUILD)
- Lifecycle (PLANNING, SETUP, CODING, EXECUTION, PUBLISH)
- Obfuscation (NONE, TARGET_HIDING, PAYLOAD_HIDING, CONTENT_DATA)
- Target Pattern (LITERAL_STRING, BASE64, CONCATENATION, etc.)
"""

import csv
import yaml
from pathlib import Path
from collections import defaultdict

RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"
BENCHMARK_PATH = Path(__file__).resolve().parent.parent / "benchmark" / "semi_real_20_v2.yaml"
OUTPUTS_DIR = Path(__file__).resolve().parent.parent / "outputs"

def load_benchmark():
    """Load benchmark with taxonomy info."""
    with open(BENCHMARK_PATH, 'r', encoding='utf-8') as f:
        cases = yaml.safe_load(f)
    return {c['case_id']: c for c in cases}

def load_results(csv_path):
    """Load results from CSV."""
    with open(csv_path, 'r', encoding='utf-8') as f:
        return {r['case_id']: r for r in csv.DictReader(f)}

def compute_metrics(cases_subset):
    """Compute ASR/FBR for a subset of cases."""
    traps = [c for c in cases_subset if c['is_trap'] == 'True']
    benigns = [c for c in cases_subset if c['is_trap'] == 'False']

    if not traps and not benigns:
        return {'asr': 0, 'fbr': 0, 'count': 0}

    trap_blocked = sum(1 for c in traps if c['decision'] == 'BLOCK')
    benign_blocked = sum(1 for c in benigns if c['decision'] == 'BLOCK')

    asr = (len(traps) - trap_blocked) / len(traps) if traps else 0
    fbr = benign_blocked / len(benigns) if benigns else 0

    return {
        'asr': asr,
        'fbr': fbr,
        'count': len(cases_subset),
        'traps': len(traps),
        'benigns': len(benigns),
    }

def main():
    OUTPUTS_DIR.mkdir(exist_ok=True)

    benchmark = load_benchmark()
    results = load_results(RESULTS_DIR / "sr20v2_e2e_v4_strict_exempt.csv")

    # Merge benchmark taxonomy with results
    merged = []
    for case_id, result in results.items():
        case = benchmark[case_id]
        merged.append({
            **result,
            'carrier': case['taxonomy']['carrier'],
            'lifecycle': case['taxonomy']['lifecycle'],
            'obfuscation': case['gold_expected_behaviors'][0].get('obfuscation_scope', 'NONE') if case['gold_expected_behaviors'] else 'NONE',
            'target_pattern': case['gold_expected_behaviors'][0].get('target_pattern', 'NONE') if case['gold_expected_behaviors'] else 'NONE',
        })

    # Slice by carrier
    carrier_slices = defaultdict(list)
    for case in merged:
        carrier_slices[case['carrier']].append(case)

    # Slice by lifecycle
    lifecycle_slices = defaultdict(list)
    for case in merged:
        lifecycle_slices[case['lifecycle']].append(case)

    # Slice by obfuscation
    obfusc_slices = defaultdict(list)
    for case in merged:
        obfusc_slices[case['obfuscation']].append(case)

    # Slice by target_pattern
    pattern_slices = defaultdict(list)
    for case in merged:
        pattern_slices[case['target_pattern']].append(case)

    # Write slice report
    out_path = OUTPUTS_DIR / "semireal20_slice_report.csv"
    with open(out_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Dimension', 'Value', 'Count', 'Traps', 'Benigns', 'ASR (%)', 'FBR (%)'])

        # Carrier slices
        for carrier in sorted(carrier_slices.keys()):
            metrics = compute_metrics(carrier_slices[carrier])
            writer.writerow([
                'Carrier', carrier, metrics['count'], metrics['traps'], metrics['benigns'],
                f"{metrics['asr']*100:.1f}", f"{metrics['fbr']*100:.1f}"
            ])

        writer.writerow([])  # Empty row

        # Lifecycle slices
        for lifecycle in sorted(lifecycle_slices.keys()):
            metrics = compute_metrics(lifecycle_slices[lifecycle])
            writer.writerow([
                'Lifecycle', lifecycle, metrics['count'], metrics['traps'], metrics['benigns'],
                f"{metrics['asr']*100:.1f}", f"{metrics['fbr']*100:.1f}"
            ])

        writer.writerow([])  # Empty row

        # Obfuscation slices
        for obfusc in sorted(obfusc_slices.keys()):
            metrics = compute_metrics(obfusc_slices[obfusc])
            writer.writerow([
                'Obfuscation', obfusc, metrics['count'], metrics['traps'], metrics['benigns'],
                f"{metrics['asr']*100:.1f}", f"{metrics['fbr']*100:.1f}"
            ])

        writer.writerow([])  # Empty row

        # Target pattern slices
        for pattern in sorted(pattern_slices.keys()):
            metrics = compute_metrics(pattern_slices[pattern])
            writer.writerow([
                'Target Pattern', pattern, metrics['count'], metrics['traps'], metrics['benigns'],
                f"{metrics['asr']*100:.1f}", f"{metrics['fbr']*100:.1f}"
            ])

    print(f"Slice report written to {out_path}")
    print()
    print("=" * 80)
    print("SEMIREAL-20 SLICE REPORT (CodeGuard E2E v4, STRICT-EXEMPT)")
    print("=" * 80)

    print("\nBy Carrier:")
    for carrier in sorted(carrier_slices.keys()):
        metrics = compute_metrics(carrier_slices[carrier])
        print(f"  {carrier:12s}: ASR={metrics['asr']*100:5.1f}%, FBR={metrics['fbr']*100:5.1f}%, n={metrics['count']}")

    print("\nBy Lifecycle:")
    for lifecycle in sorted(lifecycle_slices.keys()):
        metrics = compute_metrics(lifecycle_slices[lifecycle])
        print(f"  {lifecycle:12s}: ASR={metrics['asr']*100:5.1f}%, FBR={metrics['fbr']*100:5.1f}%, n={metrics['count']}")

    print("\nBy Obfuscation:")
    for obfusc in sorted(obfusc_slices.keys()):
        metrics = compute_metrics(obfusc_slices[obfusc])
        print(f"  {obfusc:16s}: ASR={metrics['asr']*100:5.1f}%, FBR={metrics['fbr']*100:5.1f}%, n={metrics['count']}")

    print("\nBy Target Pattern:")
    for pattern in sorted(pattern_slices.keys()):
        metrics = compute_metrics(pattern_slices[pattern])
        print(f"  {pattern:16s}: ASR={metrics['asr']*100:5.1f}%, FBR={metrics['fbr']*100:5.1f}%, n={metrics['count']}")

    print("=" * 80)

if __name__ == "__main__":
    main()
