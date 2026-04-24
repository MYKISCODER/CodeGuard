"""
Cross-Model Validation v2 — Using the actual v4.1 prompt

Runs SemiReal-60 v2 through Layer 2 with multiple LLMs using the same
v4.1 prompt that achieved 0% ASR / 3.3% FBR with GPT-4o-mini.
"""

import os
import sys
import json
import csv
import time
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
import yaml

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "policy"))
from policy_engine import arbitrate_case

BENCHMARK_PATH = Path(__file__).resolve().parent.parent / "benchmark" / "semireal_60_v2.yaml"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "results"

MODELS = [
    {"name": "gpt-4o-mini", "model_id": "gpt-4o-mini"},
    {"name": "gpt-4o", "model_id": "gpt-4o"},
    {"name": "claude-3.5-sonnet", "model_id": "claude-3-5-sonnet-20241022"},
]

# Import the exact v4.1 prompt from the original script
sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_sr60v2_e2e_v4_1 import LAYER2_PROMPT_V4_1, _extract_files_section


def call_layer2(client, model_id, case):
    files_content = _extract_files_section(case.get("repo_snapshot", ""))
    prompt = LAYER2_PROMPT_V4_1.format(
        task_text=case["task_text"],
        files_content=files_content,
    )
    try:
        comp = client.chat.completions.create(
            model=model_id,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
        )
        raw = comp.choices[0].message.content.strip()
    except Exception as e:
        print(f"    [ERROR] {case['case_id']}: {e}")
        return [], f"API_ERROR: {e}"

    text = raw
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)

    try:
        parsed = json.loads(text)
        return parsed.get("behaviors", []), raw
    except json.JSONDecodeError:
        print(f"    [WARN] JSON parse failed: {case['case_id']}")
        return [], f"JSON_PARSE_ERROR: {raw[:300]}"


def run_model(client, model_info, cases):
    model_name = model_info["name"]
    model_id = model_info["model_id"]
    mode = "STRICT-EXEMPT"

    print(f"\n{'='*60}")
    print(f"Model: {model_name} ({model_id}) — v4.1 prompt")
    print(f"{'='*60}")

    results = []
    start_time = time.time()

    for i, case in enumerate(cases):
        cid = case["case_id"]
        behaviors, raw = call_layer2(client, model_id, case)
        result = arbitrate_case(behaviors, case["intent_max_allowed"], mode)

        correct = (case["is_trap"] and result["decision"] == "BLOCK") or \
                  (not case["is_trap"] and result["decision"] == "ALLOW")

        results.append({
            "case_id": cid,
            "is_trap": case["is_trap"],
            "behaviors_count": len(behaviors),
            "decision": result["decision"],
            "derived": result["derived"],
            "correct": correct,
        })

        if not correct:
            print(f"  [{i+1:2d}/60] MISS {cid}: {result['decision']} (priv={result['derived']})")
        elif (i + 1) % 20 == 0:
            print(f"  [{i+1:2d}/60] progress ok...")

    elapsed = time.time() - start_time

    traps = [r for r in results if r["is_trap"]]
    benigns = [r for r in results if not r["is_trap"]]
    trap_blocked = sum(1 for r in traps if r["decision"] == "BLOCK")
    benign_blocked = sum(1 for r in benigns if r["decision"] == "BLOCK")

    asr = (len(traps) - trap_blocked) / len(traps) * 100
    fbr = benign_blocked / len(benigns) * 100
    utility = 100 - (asr + fbr) / 2

    print(f"\n  ASR={asr:.1f}%, FBR={fbr:.1f}%, Utility={utility:.1f}%")
    print(f"  Traps: {trap_blocked}/{len(traps)}, Benigns blocked: {benign_blocked}/{len(benigns)}")
    print(f"  Time: {elapsed:.1f}s")

    leaked = [r for r in traps if r["decision"] != "BLOCK"]
    if leaked:
        print(f"  Leaked: {[r['case_id'] for r in leaked]}")
    false_blocks = [r for r in benigns if r["decision"] == "BLOCK"]
    if false_blocks:
        print(f"  False blocks: {[r['case_id'] for r in false_blocks]}")

    return {
        "model": model_name,
        "asr": asr, "fbr": fbr, "utility": utility,
        "trap_blocked": f"{trap_blocked}/{len(traps)}",
        "benign_blocked": f"{benign_blocked}/{len(benigns)}",
        "time_sec": elapsed,
    }


def main():
    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL"),
    )

    with open(BENCHMARK_PATH, "r", encoding="utf-8") as f:
        cases = yaml.safe_load(f)
    print(f"Loaded {len(cases)} cases")

    OUTPUT_DIR.mkdir(exist_ok=True)
    all_results = []

    for model_info in MODELS:
        try:
            result = run_model(client, model_info, cases)
            all_results.append(result)
        except Exception as e:
            print(f"\n  [SKIP] {model_info['name']}: {e}")

    # Save CSV
    csv_path = OUTPUT_DIR / "cross_model_v2.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Model", "ASR (%)", "FBR (%)", "Utility (%)",
                         "Trap Blocked", "Benign Blocked", "Time (s)"])
        for r in all_results:
            writer.writerow([r["model"], f"{r['asr']:.1f}", f"{r['fbr']:.1f}",
                             f"{r['utility']:.1f}", r["trap_blocked"],
                             r["benign_blocked"], f"{r['time_sec']:.1f}"])
    print(f"\nSaved to {csv_path}")

    # Summary
    print(f"\n{'='*75}")
    print("CROSS-MODEL VALIDATION (v4.1 prompt, SemiReal-60 v2, STRICT-EXEMPT)")
    print(f"{'='*75}")
    print(f"{'Model':<22} {'ASR':>6} {'FBR':>6} {'Util':>6} {'Traps':>8} {'FalseB':>8}")
    print("-" * 75)
    for r in all_results:
        print(f"{r['model']:<22} {r['asr']:>5.1f}% {r['fbr']:>5.1f}% "
              f"{r['utility']:>5.1f}% {r['trap_blocked']:>8} {r['benign_blocked']:>8}")


if __name__ == "__main__":
    main()
