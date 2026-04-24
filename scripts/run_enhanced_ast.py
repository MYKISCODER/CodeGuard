"""
Run Enhanced AST Parser on SemiReal-60 v2 and SemiReal-120 v1.
Compare with rule-based and LLM-based Layer2.
"""

import sys
import csv
import json
from pathlib import Path
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "policy"))
from policy_engine import arbitrate_case
from layer2_enhanced_ast import EnhancedASTLayer2

BENCHMARK_DIR = Path(__file__).resolve().parent.parent / "benchmark"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "results"


def _extract_files_section(repo_snapshot):
    if not repo_snapshot:
        return "(no files)"
    lines = repo_snapshot.strip().split("\n")
    result = []
    in_files = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("files:"):
            in_files = True
            continue
        if stripped.startswith("README:") or stripped.startswith("notes:"):
            in_files = False
            continue
        if in_files:
            result.append(line)
    return "\n".join(result).strip() if result else "(no files)"


def run_benchmark(benchmark_name, benchmark_path):
    with open(benchmark_path, "r", encoding="utf-8") as f:
        cases = yaml.safe_load(f)
    print(f"\n{'='*60}")
    print(f"Enhanced AST Parser on {benchmark_name} ({len(cases)} cases)")
    print(f"{'='*60}")

    extractor = EnhancedASTLayer2()
    OUTPUT_DIR.mkdir(exist_ok=True)
    mode = "STRICT-EXEMPT"

    # Extract and evaluate
    results = []
    for i, case in enumerate(cases):
        cid = case["case_id"]
        files_content = _extract_files_section(case.get("repo_snapshot", ""))
        task_text = case.get("task_text", "")

        behaviors = extractor.extract_behaviors(files_content, task_text)
        result = arbitrate_case(behaviors, case["intent_max_allowed"], mode)

        results.append({
            "case_id": cid,
            "is_trap": case["is_trap"],
            "intent_max_allowed": case["intent_max_allowed"],
            "predicted_behaviors_count": len(behaviors),
            "derived_privilege": result["derived"],
            "decision": result["decision"],
            "reasons": " | ".join(result["reasons"]),
            "behaviors": behaviors,
        })

        status = "OK" if (case["is_trap"] and result["decision"] == "BLOCK") or \
                        (not case["is_trap"] and result["decision"] == "ALLOW") else "MISS"
        print(f"  [{i+1:3d}/{len(cases)}] {status:4s} {cid}: {result['decision']} "
              f"(priv={result['derived']}, behaviors={len(behaviors)})")

    # Save CSV
    csv_path = OUTPUT_DIR / f"{benchmark_name}_enhanced_ast.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "case_id", "is_trap", "intent_max_allowed",
            "predicted_behaviors_count", "derived_privilege", "decision", "reasons",
        ])
        for r in results:
            writer.writerow([
                r["case_id"], r["is_trap"], r["intent_max_allowed"],
                r["predicted_behaviors_count"], r["derived_privilege"],
                r["decision"], r["reasons"],
            ])
    print(f"\nResults saved to {csv_path}")

    # Save raw behaviors JSON
    json_path = OUTPUT_DIR / f"{benchmark_name}_enhanced_ast_raw.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump([{
            "case_id": r["case_id"],
            "behaviors": r["behaviors"],
            "decision": r["decision"],
        } for r in results], f, indent=2, ensure_ascii=False)

    # Compute metrics
    traps = [r for r in results if r["is_trap"]]
    benigns = [r for r in results if not r["is_trap"]]
    trap_blocked = sum(1 for r in traps if r["decision"] == "BLOCK")
    benign_blocked = sum(1 for r in benigns if r["decision"] == "BLOCK")
    trap_total = len(traps)
    benign_total = len(benigns)

    asr = (trap_total - trap_blocked) / trap_total * 100 if trap_total else 0
    fbr = benign_blocked / benign_total * 100 if benign_total else 0
    utility = 100 - (asr + fbr) / 2

    print(f"\n{'='*60}")
    print(f"RESULTS: Enhanced AST Parser on {benchmark_name} ({mode})")
    print(f"{'='*60}")
    print(f"  Traps:   {trap_blocked}/{trap_total} blocked (ASR = {asr:.1f}%)")
    print(f"  Benigns: {benign_blocked}/{benign_total} blocked (FBR = {fbr:.1f}%)")
    print(f"  Utility: {utility:.1f}%")

    # Leaked traps
    leaked = [r for r in traps if r["decision"] == "ALLOW"]
    if leaked:
        print(f"\n  Leaked traps ({len(leaked)}):")
        for r in leaked:
            print(f"    - {r['case_id']}: behaviors={r['predicted_behaviors_count']}, "
                  f"priv={r['derived_privilege']}")

    # False blocks
    false_blocks = [r for r in benigns if r["decision"] == "BLOCK"]
    if false_blocks:
        print(f"\n  False blocks ({len(false_blocks)}):")
        for r in false_blocks:
            print(f"    - {r['case_id']}: behaviors={r['predicted_behaviors_count']}, "
                  f"priv={r['derived_privilege']}")

    return {
        "benchmark": benchmark_name,
        "system": "Enhanced AST Parser",
        "asr": asr,
        "fbr": fbr,
        "utility": utility,
        "trap_blocked": f"{trap_blocked}/{trap_total}",
        "benign_blocked": f"{benign_blocked}/{benign_total}",
    }


def main():
    all_results = []

    # SemiReal-60 v2
    sr60_path = BENCHMARK_DIR / "semireal_60_v2.yaml"
    if sr60_path.exists():
        all_results.append(run_benchmark("sr60v2", sr60_path))

    # SemiReal-120 v1
    sr120_path = BENCHMARK_DIR / "semireal_120_v1.yaml"
    if sr120_path.exists():
        all_results.append(run_benchmark("sr120v1", sr120_path))

    # Summary table
    if all_results:
        print(f"\n\n{'='*70}")
        print("SUMMARY: Enhanced AST Parser vs Baselines")
        print(f"{'='*70}")
        print(f"{'Benchmark':<12} {'System':<25} {'ASR':>6} {'FBR':>6} {'Util':>6}")
        print("-" * 70)
        for r in all_results:
            print(f"{r['benchmark']:<12} {r['system']:<25} "
                  f"{r['asr']:>5.1f}% {r['fbr']:>5.1f}% {r['utility']:>5.1f}%")


if __name__ == "__main__":
    main()
