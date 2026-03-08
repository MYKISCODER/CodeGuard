#!/usr/bin/env python3
"""Verify SR120v1 experiment status"""
import yaml
import csv
from pathlib import Path
from collections import Counter

print("=" * 80)
print("SR120v1 实验状态全面验证")
print("=" * 80)

# Step 1: Verify benchmark
print("\n[1/5] 验证 Benchmark")
print("-" * 80)

benchmark_path = Path('benchmark/semireal_120_v1.yaml')
if not benchmark_path.exists():
    print("ERROR: benchmark/semireal_120_v1.yaml 不存在!")
    exit(1)

with open(benchmark_path, 'r', encoding='utf-8') as f:
    cases = yaml.safe_load(f)

traps = [c for c in cases if c['is_trap']]
benigns = [c for c in cases if not c['is_trap']]

print(f"总案例数: {len(cases)}")
print(f"Trap: {len(traps)}")
print(f"Benign: {len(benigns)}")

carriers = Counter(c['taxonomy']['carrier'] for c in cases)
lifecycles = Counter(c['taxonomy']['lifecycle'] for c in cases)

print(f"Carrier分布: {dict(carriers)}")
print(f"Lifecycle分布: {dict(lifecycles)}")

if len(cases) != 120 or len(traps) != 60 or len(benigns) != 60:
    print("ERROR: 案例数量不正确!")
    exit(1)

benchmark_ids = set(c['case_id'] for c in cases)
print("OK: Benchmark验证通过")

# Step 2: Verify result files
print("\n[2/5] 验证实验结果文件")
print("-" * 80)

result_files = {
    'CodeGuard': 'results/sr120v1_e2e_v4_1_strict_exempt.csv',
    'LLM Judge': 'results/sr120v1_baseline_llm_judge.csv',
    'SAST': 'results/sr120v1_baseline_sast.csv'
}

all_results = {}
all_complete = True

for name, filepath in result_files.items():
    filepath = Path(filepath)
    if not filepath.exists():
        print(f"ERROR: {name} 结果文件不存在: {filepath}")
        all_complete = False
        continue

    with open(filepath, 'r', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))

    result_ids = set(r['case_id'] for r in rows)
    missing = benchmark_ids - result_ids
    extra = result_ids - benchmark_ids

    traps_in_result = [r for r in rows if r['is_trap'] == 'True']
    benigns_in_result = [r for r in rows if r['is_trap'] == 'False']

    trap_blocked = sum(1 for r in traps_in_result if r['decision'] == 'BLOCK')
    benign_blocked = sum(1 for r in benigns_in_result if r['decision'] == 'BLOCK')

    all_results[name] = {
        'total': len(rows),
        'traps': len(traps_in_result),
        'benigns': len(benigns_in_result),
        'trap_blocked': trap_blocked,
        'benign_blocked': benign_blocked
    }

    print(f"\n{name}:")
    print(f"  总行数: {len(rows)}")
    print(f"  Trap: {len(traps_in_result)}, Benign: {len(benigns_in_result)}")
    print(f"  Trap blocked: {trap_blocked}/{len(traps_in_result)}")
    print(f"  Benign blocked: {benign_blocked}/{len(benigns_in_result)}")

    if missing:
        print(f"  ERROR: 缺失 {len(missing)} 个案例")
        all_complete = False
    elif extra:
        print(f"  ERROR: 多出 {len(extra)} 个案例")
        all_complete = False
    elif len(rows) != 120:
        print(f"  ERROR: 总数不是120")
        all_complete = False
    else:
        print(f"  OK: 完整")

if not all_complete:
    print("\nERROR: 实验结果不完整，需要重新运行!")
    exit(1)

print("\nOK: 所有实验结果完整")

# Step 3: Calculate metrics
print("\n[3/5] 计算指标")
print("-" * 80)

metrics = {}
for name, data in all_results.items():
    asr = (data['traps'] - data['trap_blocked']) / data['traps'] * 100
    fbr = data['benign_blocked'] / data['benigns'] * 100
    correct = data['trap_blocked'] + (data['benigns'] - data['benign_blocked'])
    utility = correct / data['total'] * 100

    metrics[name] = {
        'asr': asr,
        'fbr': fbr,
        'utility': utility
    }

    print(f"{name}: ASR={asr:.1f}% FBR={fbr:.1f}% Utility={utility:.1f}%")

# Step 4: Check output files
print("\n[4/5] 检查输出文件")
print("-" * 80)

output_files = {
    'Main table': 'outputs/semireal120_main_table.csv',
    'Trend report': 'outputs/semireal_trend_consistency.md'
}

outputs_exist = True
for name, filepath in output_files.items():
    if Path(filepath).exists():
        print(f"OK: {name} 存在: {filepath}")
    else:
        print(f"MISSING: {name} 不存在: {filepath}")
        outputs_exist = False

# Step 5: Summary
print("\n[5/5] 总结")
print("=" * 80)

if all_complete and outputs_exist:
    print("状态: 所有实验和输出文件都完整 ✓")
    print("\n下一步: 验证趋势一致性")
else:
    print("状态: 需要生成输出文件")
    print("\n下一步: 运行生成脚本")

print("=" * 80)
