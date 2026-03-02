"""
Generate slice analysis report for SemiReal-60 v2

Analyzes performance by Carrier, Lifecycle, and Obfuscation dimensions.
"""

import csv
import yaml
from pathlib import Path
from collections import defaultdict

BENCHMARK_PATH = Path(__file__).resolve().parent.parent / "benchmark" / "semireal_60_v2.yaml"
RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"
OUTPUTS_DIR = Path(__file__).resolve().parent.parent / "outputs"

def load_benchmark():
    """Load benchmark with metadata."""
    with open(BENCHMARK_PATH, 'r', encoding='utf-8') as f:
        cases = yaml.safe_load(f)

    case_meta = {}
    for case in cases:
        taxonomy = case.get('taxonomy', {})
        behaviors = case.get('gold_expected_behaviors', [])
        obfuscation = behaviors[0].get('obfuscation_scope', 'NONE') if behaviors else 'NONE'

        case_meta[case['case_id']] = {
            'is_trap': case.get('is_trap', False),
            'carrier': taxonomy.get('carrier', 'UNKNOWN'),
            'lifecycle': taxonomy.get('lifecycle', 'UNKNOWN'),
            'obfuscation': obfuscation,
        }
    return case_meta

def load_results(csv_path):
    """Load results from CSV."""
    with open(csv_path, 'r', encoding='utf-8') as f:
        return {r['case_id']: r for r in csv.DictReader(f)}

def compute_metrics(cases, results):
    """Compute ASR/FBR for a subset of cases."""
    traps = [c for c in cases if c['is_trap']]
    benigns = [c for c in cases if not c['is_trap']]

    trap_blocked = sum(1 for c in traps if results.get(c['case_id'], {}).get('decision') == 'BLOCK')
    benign_blocked = sum(1 for c in benigns if results.get(c['case_id'], {}).get('decision') == 'BLOCK')

    asr = (len(traps) - trap_blocked) / len(traps) if traps else 0
    fbr = benign_blocked / len(benigns) if benigns else 0

    return {
        'total': len(cases),
        'traps': len(traps),
        'benigns': len(benigns),
        'asr': asr,
        'fbr': fbr,
    }

def main():
    OUTPUTS_DIR.mkdir(exist_ok=True)

    case_meta = load_benchmark()

    # Load all results
    codeguard = load_results(RESULTS_DIR / "sr60v2_e2e_v4_1_strict_exempt.csv")
    llm_judge = load_results(RESULTS_DIR / "sr60v2_baseline_llm_judge.csv")
    sast = load_results(RESULTS_DIR / "sr60v2_baseline_sast.csv")

    systems = [
        ('CodeGuard', codeguard),
        ('LLM Judge', llm_judge),
        ('SAST', sast),
    ]

    # Prepare slices
    slices = defaultdict(list)
    for case_id, meta in case_meta.items():
        slices[('Carrier', meta['carrier'])].append({'case_id': case_id, **meta})
        slices[('Lifecycle', meta['lifecycle'])].append({'case_id': case_id, **meta})
        slices[('Obfuscation', meta['obfuscation'])].append({'case_id': case_id, **meta})

    # Generate report
    out_path = OUTPUTS_DIR / "semireal60v2_slice_report.csv"
    with open(out_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'Dimension', 'Value', 'System', 'Total', 'Traps', 'Benigns',
            'ASR (%)', 'FBR (%)'
        ])

        for (dim, val), cases in sorted(slices.items()):
            for sys_name, sys_results in systems:
                metrics = compute_metrics(cases, sys_results)
                writer.writerow([
                    dim, val, sys_name,
                    metrics['total'], metrics['traps'], metrics['benigns'],
                    f"{metrics['asr']*100:.1f}", f"{metrics['fbr']*100:.1f}"
                ])

    print(f"Slice report written to {out_path}")
    print()
    print("=" * 80)
    print("SEMIREAL-60 V2 SLICE ANALYSIS")
    print("=" * 80)

    # Print summary by dimension
    for dim in ['Carrier', 'Lifecycle', 'Obfuscation']:
        print(f"\n{dim}:")
        print("-" * 80)
        dim_slices = [(k, v) for k, v in slices.items() if k[0] == dim]
        for (_, val), cases in sorted(dim_slices):
            print(f"  {val} ({len(cases)} cases):")
            for sys_name, sys_results in systems:
                metrics = compute_metrics(cases, sys_results)
                print(f"    {sys_name:<15} ASR={metrics['asr']*100:>5.1f}%  FBR={metrics['fbr']*100:>5.1f}%")

if __name__ == "__main__":
    main()
