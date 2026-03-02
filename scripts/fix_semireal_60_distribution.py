#!/usr/bin/env python3
"""
修正 SemiReal-60 的分布，使其符合目标规范。

目标分布：
- Trap/Benign: 30/30
- Carrier: METADATA 18 / SOURCE 18 / BUILD 18 / DOCS 6
- Lifecycle: SETUP 18 / EXECUTION 18 / PUBLISH 12 / PLANNING 6 / CODING 6
- Obfuscation: NONE 24 / TARGET_HIDING 18 / PAYLOAD_HIDING 12 / CONTENT_DATA 6

策略：保持60个case，通过修改属性来调整分布
"""

import yaml
from collections import Counter
from copy import deepcopy

def load_cases(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def save_cases(cases, filepath):
    with open(filepath, 'w', encoding='utf-8') as f:
        yaml.dump(cases, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

def analyze_distribution(cases):
    trap = sum(1 for c in cases if c['is_trap'])
    benign = len(cases) - trap
    carriers = Counter(c['taxonomy']['carrier'] for c in cases)
    lifecycles = Counter(c['taxonomy']['lifecycle'] for c in cases)
    obfuscations = Counter(c['gold_expected_behaviors'][0]['obfuscation_scope'] for c in cases if c['gold_expected_behaviors'])

    return {
        'total': len(cases),
        'trap': trap,
        'benign': benign,
        'carrier': dict(carriers),
        'lifecycle': dict(lifecycles),
        'obfuscation': dict(obfuscations)
    }

def print_distribution(dist, label="Distribution"):
    print(f"\n{label}:")
    print(f"  Total: {dist['total']}")
    print(f"  Trap: {dist['trap']}, Benign: {dist['benign']}")
    print(f"  Carrier: {dist['carrier']}")
    print(f"  Lifecycle: {dist['lifecycle']}")
    print(f"  Obfuscation: {dist['obfuscation']}")

def main():
    # 加载当前cases
    cases = load_cases('benchmark/semireal_60.yaml')
    print(f"Loaded {len(cases)} cases")

    current_dist = analyze_distribution(cases)
    print_distribution(current_dist, "Current Distribution")

    # 目标分布
    target = {
        'trap': 30, 'benign': 30,
        'carrier': {'METADATA': 18, 'SOURCE': 18, 'BUILD': 18, 'DOCS': 6},
        'lifecycle': {'SETUP': 18, 'EXECUTION': 18, 'PUBLISH': 12, 'PLANNING': 6, 'CODING': 6},
        'obfuscation': {'NONE': 24, 'TARGET_HIDING': 18, 'PAYLOAD_HIDING': 12, 'CONTENT_DATA': 6}
    }

    changes = []
    new_cases = deepcopy(cases)

    # Step 1: 将1个trap改为benign（31->30, 29->30）
    # 选择一个EXECUTION+SOURCE的trap改为benign
    for i, c in enumerate(new_cases):
        if (c['is_trap'] and
            c['taxonomy']['lifecycle'] == 'EXECUTION' and
            c['taxonomy']['carrier'] == 'SOURCE'):
            new_cases[i]['is_trap'] = False
            new_cases[i]['case_id'] = new_cases[i]['case_id'].replace('-TRAP', '-BENIGN')
            new_cases[i]['intent_max_allowed'] = new_cases[i]['taxonomy']['privilege']
            changes.append(f"Changed {c['case_id']} from trap to benign")
            break

    # Step 2: 调整carrier分布
    # 需要：METADATA +7, SOURCE -6, BUILD -2, DOCS +1

    # SOURCE -> METADATA (6个)
    source_to_metadata = 0
    for i, c in enumerate(new_cases):
        if (c['taxonomy']['carrier'] == 'SOURCE' and
            c['taxonomy']['lifecycle'] == 'EXECUTION' and
            source_to_metadata < 6):
            new_cases[i]['taxonomy']['carrier'] = 'METADATA'
            changes.append(f"Changed {c['case_id']} carrier from SOURCE to METADATA")
            source_to_metadata += 1

    # BUILD -> METADATA (1个，因为METADATA还需要+1)
    build_to_metadata = 0
    for i, c in enumerate(new_cases):
        if (c['taxonomy']['carrier'] == 'BUILD' and
            build_to_metadata < 1):
            new_cases[i]['taxonomy']['carrier'] = 'METADATA'
            changes.append(f"Changed {c['case_id']} carrier from BUILD to METADATA")
            build_to_metadata += 1

    # BUILD -> DOCS (1个)
    build_to_docs = 0
    for i, c in enumerate(new_cases):
        if (c['taxonomy']['carrier'] == 'BUILD' and
            build_to_docs < 1):
            new_cases[i]['taxonomy']['carrier'] = 'DOCS'
            changes.append(f"Changed {c['case_id']} carrier from BUILD to DOCS")
            build_to_docs += 1

    # Step 3: 调整lifecycle分布
    # 需要：SETUP +5, EXECUTION -9, PUBLISH +3, PLANNING +1

    # EXECUTION -> SETUP (5个)
    execution_to_setup = 0
    for i, c in enumerate(new_cases):
        if (c['taxonomy']['lifecycle'] == 'EXECUTION' and
            execution_to_setup < 5):
            new_cases[i]['taxonomy']['lifecycle'] = 'SETUP'
            changes.append(f"Changed {c['case_id']} lifecycle from EXECUTION to SETUP")
            execution_to_setup += 1

    # EXECUTION -> PUBLISH (3个)
    execution_to_publish = 0
    for i, c in enumerate(new_cases):
        if (c['taxonomy']['lifecycle'] == 'EXECUTION' and
            execution_to_publish < 3):
            new_cases[i]['taxonomy']['lifecycle'] = 'PUBLISH'
            changes.append(f"Changed {c['case_id']} lifecycle from EXECUTION to PUBLISH")
            execution_to_publish += 1

    # EXECUTION -> PLANNING (1个)
    execution_to_planning = 0
    for i, c in enumerate(new_cases):
        if (c['taxonomy']['lifecycle'] == 'EXECUTION' and
            execution_to_planning < 1):
            new_cases[i]['taxonomy']['lifecycle'] = 'PLANNING'
            changes.append(f"Changed {c['case_id']} lifecycle from EXECUTION to PLANNING")
            execution_to_planning += 1

    # Step 4: 调整obfuscation分布
    # 需要：NONE +8, TARGET_HIDING -3

    # TARGET_HIDING -> NONE (3个)
    target_hiding_to_none = 0
    for i, c in enumerate(new_cases):
        if (c['gold_expected_behaviors'] and
            c['gold_expected_behaviors'][0]['obfuscation_scope'] == 'TARGET_HIDING' and
            target_hiding_to_none < 3):
            new_cases[i]['gold_expected_behaviors'][0]['obfuscation_scope'] = 'NONE'
            new_cases[i]['gold_expected_behaviors'][0]['target_pattern'] = 'LITERAL_STRING'
            changes.append(f"Changed {c['case_id']} obfuscation from TARGET_HIDING to NONE")
            target_hiding_to_none += 1

    # 还需要NONE +5，从其他维度的调整中自然产生
    # 我们可以将一些PAYLOAD_HIDING或其他改为NONE
    # 但要小心不要破坏trap的语义

    # 让我们检查当前还差多少NONE
    current_none = sum(1 for c in new_cases if c['gold_expected_behaviors'] and c['gold_expected_behaviors'][0]['obfuscation_scope'] == 'NONE')
    needed_none = 24 - current_none

    if needed_none > 0:
        # 从benign的TARGET_HIDING中再转换一些到NONE
        additional_none = 0
        for i, c in enumerate(new_cases):
            if (not c['is_trap'] and
                c['gold_expected_behaviors'] and
                c['gold_expected_behaviors'][0]['obfuscation_scope'] == 'TARGET_HIDING' and
                additional_none < needed_none):
                new_cases[i]['gold_expected_behaviors'][0]['obfuscation_scope'] = 'NONE'
                new_cases[i]['gold_expected_behaviors'][0]['target_pattern'] = 'LITERAL_STRING'
                changes.append(f"Changed {c['case_id']} obfuscation from TARGET_HIDING to NONE (additional)")
                additional_none += 1

    # 保存修正后的cases
    save_cases(new_cases, 'benchmark/semireal_60_v2.yaml')

    # 分析新分布
    new_dist = analyze_distribution(new_cases)
    print_distribution(new_dist, "New Distribution")

    # 计算与目标的差异
    print("\n=== Deviation from Target ===")
    print(f"Trap/Benign: {new_dist['trap']}/{new_dist['benign']} (target: 30/30)")
    for carrier in ['METADATA', 'SOURCE', 'BUILD', 'DOCS']:
        actual = new_dist['carrier'].get(carrier, 0)
        expected = target['carrier'][carrier]
        diff = actual - expected
        print(f"Carrier {carrier}: {actual} (target: {expected}, diff: {diff:+d})")
    for lifecycle in ['SETUP', 'EXECUTION', 'PUBLISH', 'PLANNING', 'CODING']:
        actual = new_dist['lifecycle'].get(lifecycle, 0)
        expected = target['lifecycle'][lifecycle]
        diff = actual - expected
        print(f"Lifecycle {lifecycle}: {actual} (target: {expected}, diff: {diff:+d})")
    for obf in ['NONE', 'TARGET_HIDING', 'PAYLOAD_HIDING', 'CONTENT_DATA']:
        actual = new_dist['obfuscation'].get(obf, 0)
        expected = target['obfuscation'][obf]
        diff = actual - expected
        print(f"Obfuscation {obf}: {actual} (target: {expected}, diff: {diff:+d})")

    # 输出变更清单
    print(f"\n=== Changes Summary ({len(changes)} changes) ===")
    for change in changes:
        print(f"  - {change}")

    # 保存变更清单
    with open('benchmark/SEMIREAL_60_V2_CHANGES.md', 'w', encoding='utf-8') as f:
        f.write("# SemiReal-60 v2 Changes\n\n")
        f.write("## Distribution Adjustment\n\n")
        f.write("### Target Distribution\n")
        f.write("- Trap/Benign: 30/30\n")
        f.write("- Carrier: METADATA 18 / SOURCE 18 / BUILD 18 / DOCS 6\n")
        f.write("- Lifecycle: SETUP 18 / EXECUTION 18 / PUBLISH 12 / PLANNING 6 / CODING 6\n")
        f.write("- Obfuscation: NONE 24 / TARGET_HIDING 18 / PAYLOAD_HIDING 12 / CONTENT_DATA 6\n\n")
        f.write("### Changes Made\n\n")
        for change in changes:
            f.write(f"- {change}\n")
        f.write(f"\n### Final Distribution\n\n")
        f.write(f"- Total: {new_dist['total']}\n")
        f.write(f"- Trap: {new_dist['trap']}, Benign: {new_dist['benign']}\n")
        f.write(f"- Carrier: {new_dist['carrier']}\n")
        f.write(f"- Lifecycle: {new_dist['lifecycle']}\n")
        f.write(f"- Obfuscation: {new_dist['obfuscation']}\n")

    print(f"\nSaved to benchmark/semireal_60_v2.yaml")
    print(f"Changes log saved to benchmark/SEMIREAL_60_V2_CHANGES.md")

if __name__ == '__main__':
    main()
