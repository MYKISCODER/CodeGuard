#!/usr/bin/env python3
"""Generate main comparison table for SemiReal-120 v1"""
import csv
from pathlib import Path

def calc_metrics(csv_path):
    """Calculate ASR, FBR, Utility from result CSV"""
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    traps = [r for r in rows if r['is_trap'] == 'True']
    benigns = [r for r in rows if r['is_trap'] == 'False']

    trap_blocked = sum(1 for r in traps if r['decision'] == 'BLOCK')
    benign_blocked = sum(1 for r in benigns if r['decision'] == 'BLOCK')

    # ASR = leaked traps / total traps
    asr = (len(traps) - trap_blocked) / len(traps) * 100 if traps else 0

    # FBR = false blocked benigns / total benigns
    fbr = benign_blocked / len(benigns) * 100 if benigns else 0

    # Utility = (correct decisions) / total
    correct = trap_blocked + (len(benigns) - benign_blocked)
    utility = correct / len(rows) * 100 if rows else 0

    return {
        'asr': asr,
        'fbr': fbr,
        'utility': utility,
        'trap_blocked': trap_blocked,
        'trap_total': len(traps),
        'benign_blocked': benign_blocked,
        'benign_total': len(benigns),
        'total': len(rows)
    }

def main():
    base = Path('.')

    # Calculate metrics for each system
    codeguard = calc_metrics(base / 'results/sr120v1_e2e_v4_1_strict_exempt.csv')
    llm_judge = calc_metrics(base / 'results/sr120v1_baseline_llm_judge.csv')
    sast = calc_metrics(base / 'results/sr120v1_baseline_sast.csv')

    # Generate table
    output = base / 'outputs/semireal120_main_table.csv'
    output.parent.mkdir(exist_ok=True)

    with open(output, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['System', 'ASR (%)', 'FBR (%)', 'Utility (%)',
                        'Trap Blocked', 'Benign Blocked', 'Total Cases'])

        writer.writerow([
            'CodeGuard (E2E v4, STRICT-EXEMPT)',
            f'{codeguard["asr"]:.1f}',
            f'{codeguard["fbr"]:.1f}',
            f'{codeguard["utility"]:.1f}',
            f'{codeguard["trap_blocked"]}/{codeguard["trap_total"]}',
            f'{codeguard["benign_blocked"]}/{codeguard["benign_total"]}',
            codeguard["total"]
        ])

        writer.writerow([
            'LLM Judge (gpt-4o-mini)',
            f'{llm_judge["asr"]:.1f}',
            f'{llm_judge["fbr"]:.1f}',
            f'{llm_judge["utility"]:.1f}',
            f'{llm_judge["trap_blocked"]}/{llm_judge["trap_total"]}',
            f'{llm_judge["benign_blocked"]}/{llm_judge["benign_total"]}',
            llm_judge["total"]
        ])

        writer.writerow([
            'SAST (Regex Rules)',
            f'{sast["asr"]:.1f}',
            f'{sast["fbr"]:.1f}',
            f'{sast["utility"]:.1f}',
            f'{sast["trap_blocked"]}/{sast["trap_total"]}',
            f'{sast["benign_blocked"]}/{sast["benign_total"]}',
            sast["total"]
        ])

    print(f"Generated: {output}")
    print(f"\nSR120v1 Results:")
    print(f"  CodeGuard: ASR={codeguard['asr']:.1f}% FBR={codeguard['fbr']:.1f}% Utility={codeguard['utility']:.1f}%")
    print(f"  LLM Judge: ASR={llm_judge['asr']:.1f}% FBR={llm_judge['fbr']:.1f}% Utility={llm_judge['utility']:.1f}%")
    print(f"  SAST:      ASR={sast['asr']:.1f}% FBR={sast['fbr']:.1f}% Utility={sast['utility']:.1f}%")

if __name__ == '__main__':
    main()
