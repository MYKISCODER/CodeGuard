#!/usr/bin/env python3
"""
Run Gold baseline on SemiReal-60 v2 (all 4 modes)
"""

import yaml
import json
from pathlib import Path
from collections import Counter

# Import policy engine
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from policy.engine import PolicyEngine

def load_cases(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def run_gold_baseline(cases, mode):
    """Run gold baseline: use gold_expected_behaviors directly"""
    engine = PolicyEngine(mode=mode)
    results = []

    for case in cases:
        case_id = case['case_id']
        intent = case['intent_max_allowed']
        behaviors = case.get('gold_expected_behaviors', [])

        # Run policy engine
        decision, derived_priv, reason = engine.evaluate(behaviors, intent)

        results.append({
            'case_id': case_id,
            'is_trap': case['is_trap'],
            'intent_max_allowed': intent,
            'derived_privilege': derived_priv,
            'decision': decision,
            'reason': reason,
            'carrier': case['taxonomy']['carrier'],
            'lifecycle': case['taxonomy']['lifecycle'],
            'obfuscation': behaviors[0]['obfuscation_scope'] if behaviors else 'NONE'
        })

    return results

def compute_metrics(results):
    """Compute ASR, FBR, Utility"""
    trap_cases = [r for r in results if r['is_trap']]
    benign_cases = [r for r in results if not r['is_trap']]

    # ASR: trap cases that were ALLOW
    asr = sum(1 for r in trap_cases if r['decision'] == 'ALLOW') / len(trap_cases) if trap_cases else 0

    # FBR: benign cases that were BLOCK
    fbr = sum(1 for r in benign_cases if r['decision'] == 'BLOCK') / len(benign_cases) if benign_cases else 0

    # Utility: all cases where decision is correct
    utility = sum(1 for r in results if (r['is_trap'] and r['decision'] == 'BLOCK') or
                  (not r['is_trap'] and r['decision'] == 'ALLOW')) / len(results)

    return {
        'ASR': f'{asr:.1%}',
        'FBR': f'{fbr:.1%}',
        'Utility': f'{utility:.1%}',
        'total': len(results),
        'trap': len(trap_cases),
        'benign': len(benign_cases)
    }

def save_results(results, mode, output_dir):
    """Save results to CSV"""
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)

    csv_path = output_dir / f'sr60_gold_{mode.lower()}.csv'

    with open(csv_path, 'w', encoding='utf-8') as f:
        # Header
        f.write('case_id,is_trap,intent,derived_priv,decision,reason,carrier,lifecycle,obfuscation\n')

        # Rows
        for r in results:
            f.write(f'{r["case_id"]},{r["is_trap"]},{r["intent_max_allowed"]},{r["derived_privilege"]},'
                   f'{r["decision"]},"{r["reason"]}",{r["carrier"]},{r["lifecycle"]},{r["obfuscation"]}\n')

    print(f'Saved {mode} results to {csv_path}')
    return csv_path

def main():
    # Load SemiReal-60 v2
    cases = load_cases('benchmark/semireal_60_v2.yaml')
    print(f'Loaded {len(cases)} cases from SemiReal-60 v2')

    modes = ['STRICT', 'MODERATE', 'PERMISSIVE', 'STRICT-EXEMPT']
    all_metrics = {}

    for mode in modes:
        print(f'\n=== Running Gold Baseline: {mode} ===')
        results = run_gold_baseline(cases, mode)
        metrics = compute_metrics(results)
        all_metrics[mode] = metrics

        print(f'ASR: {metrics["ASR"]}, FBR: {metrics["FBR"]}, Utility: {metrics["Utility"]}')

        # Save results
        save_results(results, mode, 'results')

    # Summary
    print(f'\n=== Gold Baseline Summary (SemiReal-60 v2) ===')
    print(f'{"Mode":<15} {"ASR":<10} {"FBR":<10} {"Utility":<10}')
    print('-' * 45)
    for mode in modes:
        m = all_metrics[mode]
        print(f'{mode:<15} {m["ASR"]:<10} {m["FBR"]:<10} {m["Utility"]:<10}')

if __name__ == '__main__':
    main()
