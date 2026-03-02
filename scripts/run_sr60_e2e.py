#!/usr/bin/env python3
"""
Run E2E (Layer2 + Policy) on SemiReal-60 v2 (all 4 modes)
Uses the latest Layer2 prompt (v4)
"""

import yaml
import json
from pathlib import Path
from collections import Counter

# Import components
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from policy.engine import PolicyEngine
from layer2.parser import Layer2Parser

def load_cases(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def run_e2e(cases, mode, layer2_version='v4'):
    """Run E2E: Layer2 extraction + Policy evaluation"""
    parser = Layer2Parser(version=layer2_version)
    engine = PolicyEngine(mode=mode)
    results = []

    for case in cases:
        case_id = case['case_id']
        intent = case['intent_max_allowed']
        repo_snapshot = case['repo_snapshot']
        task_text = case['task_text']
        lifecycle = case['taxonomy']['lifecycle']

        # Layer2: extract behaviors
        predicted_behaviors = parser.extract_behaviors(
            repo_snapshot=repo_snapshot,
            task_text=task_text,
            lifecycle=lifecycle
        )

        # Policy: evaluate
        decision, derived_priv, reason = engine.evaluate(predicted_behaviors, intent)

        results.append({
            'case_id': case_id,
            'is_trap': case['is_trap'],
            'intent_max_allowed': intent,
            'derived_privilege': derived_priv,
            'decision': decision,
            'reason': reason,
            'carrier': case['taxonomy']['carrier'],
            'lifecycle': case['taxonomy']['lifecycle'],
            'predicted_behaviors': predicted_behaviors,
            'gold_behaviors': case.get('gold_expected_behaviors', [])
        })

    return results

def compute_metrics(results):
    """Compute ASR, FBR, Utility"""
    trap_cases = [r for r in results if r['is_trap']]
    benign_cases = [r for r in results if not r['is_trap']]

    asr = sum(1 for r in trap_cases if r['decision'] == 'ALLOW') / len(trap_cases) if trap_cases else 0
    fbr = sum(1 for r in benign_cases if r['decision'] == 'BLOCK') / len(benign_cases) if benign_cases else 0
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

def save_results(results, mode, output_dir, version='v4'):
    """Save results to CSV"""
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)

    csv_path = output_dir / f'sr60_e2e_{version}_{mode.lower()}.csv'

    with open(csv_path, 'w', encoding='utf-8') as f:
        f.write('case_id,is_trap,intent,derived_priv,decision,reason,carrier,lifecycle\n')

        for r in results:
            f.write(f'{r["case_id"]},{r["is_trap"]},{r["intent_max_allowed"]},{r["derived_privilege"]},'
                   f'{r["decision"]},"{r["reason"]}",{r["carrier"]},{r["lifecycle"]}\n')

    print(f'Saved {mode} results to {csv_path}')
    return csv_path

def main():
    cases = load_cases('benchmark/semireal_60_v2.yaml')
    print(f'Loaded {len(cases)} cases from SemiReal-60 v2')

    modes = ['STRICT', 'MODERATE', 'PERMISSIVE', 'STRICT-EXEMPT']
    all_metrics = {}

    for mode in modes:
        print(f'\n=== Running E2E (v4): {mode} ===')
        results = run_e2e(cases, mode, layer2_version='v4')
        metrics = compute_metrics(results)
        all_metrics[mode] = metrics

        print(f'ASR: {metrics["ASR"]}, FBR: {metrics["FBR"]}, Utility: {metrics["Utility"]}')

        save_results(results, mode, 'results', version='v4')

    print(f'\n=== E2E (v4) Summary (SemiReal-60 v2) ===')
    print(f'{"Mode":<15} {"ASR":<10} {"FBR":<10} {"Utility":<10}')
    print('-' * 45)
    for mode in modes:
        m = all_metrics[mode]
        print(f'{mode:<15} {m["ASR"]:<10} {m["FBR"]:<10} {m["Utility"]:<10}')

if __name__ == '__main__':
    main()
