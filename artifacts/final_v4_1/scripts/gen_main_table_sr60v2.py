"""
Generate main comparison table for SemiReal-60 v2: CodeGuard vs Baselines

Compares CodeGuard E2E v4 (STRICT-EXEMPT) against LLM Judge and SAST baselines.
"""

import csv
from pathlib import Path

RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"
OUTPUTS_DIR = Path(__file__).resolve().parent.parent / "outputs"

def load_results(csv_path):
    """Load results from CSV and compute metrics."""
    with open(csv_path, 'r', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))

    traps = [r for r in rows if r['is_trap'] == 'True']
    benigns = [r for r in rows if r['is_trap'] == 'False']

    trap_blocked = sum(1 for r in traps if r['decision'] == 'BLOCK')
    benign_blocked = sum(1 for r in benigns if r['decision'] == 'BLOCK')

    asr = (len(traps) - trap_blocked) / len(traps) if traps else 0
    fbr = benign_blocked / len(benigns) if benigns else 0
    utility = 1 - (asr + fbr) / 2

    return {
        'total': len(rows),
        'traps': len(traps),
        'benigns': len(benigns),
        'trap_blocked': trap_blocked,
        'benign_blocked': benign_blocked,
        'asr': asr,
        'fbr': fbr,
        'utility': utility,
    }

def main():
    OUTPUTS_DIR.mkdir(exist_ok=True)

    # Load results
    codeguard = load_results(RESULTS_DIR / "sr60v2_e2e_v4_1_strict_exempt.csv")
    llm_judge = load_results(RESULTS_DIR / "sr60v2_baseline_llm_judge.csv")
    sast = load_results(RESULTS_DIR / "sr60v2_baseline_sast.csv")

    # Generate comparison table
    out_path = OUTPUTS_DIR / "semireal60v2_main_table.csv"
    with open(out_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'System', 'ASR (%)', 'FBR (%)', 'Utility (%)',
            'Trap Blocked', 'Benign Blocked', 'Total Cases'
        ])

        for name, results in [
            ('CodeGuard (E2E v4, STRICT-EXEMPT)', codeguard),
            ('LLM Judge (gpt-4o-mini)', llm_judge),
            ('SAST (Regex Rules)', sast),
        ]:
            writer.writerow([
                name,
                f"{results['asr']*100:.1f}",
                f"{results['fbr']*100:.1f}",
                f"{results['utility']*100:.1f}",
                f"{results['trap_blocked']}/{results['traps']}",
                f"{results['benign_blocked']}/{results['benigns']}",
                results['total'],
            ])

    print(f"Main comparison table written to {out_path}")
    print()
    print("=" * 80)
    print("SEMIREAL-60 V2 MAIN COMPARISON TABLE")
    print("=" * 80)
    print(f"{'System':<40} {'ASR':>8} {'FBR':>8} {'Utility':>10}")
    print("-" * 80)
    print(f"{'CodeGuard (E2E v4, STRICT-EXEMPT)':<40} {codeguard['asr']*100:>7.1f}% {codeguard['fbr']*100:>7.1f}% {codeguard['utility']*100:>9.1f}%")
    print(f"{'LLM Judge (gpt-4o-mini)':<40} {llm_judge['asr']*100:>7.1f}% {llm_judge['fbr']*100:>7.1f}% {llm_judge['utility']*100:>9.1f}%")
    print(f"{'SAST (Regex Rules)':<40} {sast['asr']*100:>7.1f}% {sast['fbr']*100:>7.1f}% {sast['utility']*100:>9.1f}%")
    print("=" * 80)

if __name__ == "__main__":
    main()
