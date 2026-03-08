"""
SAST Baseline for SemiReal-120 v1

Uses regex-based pattern matching to detect security issues.
"""

import re
import csv
from pathlib import Path
import yaml

BENCHMARK_PATH = Path(__file__).resolve().parent.parent / "benchmark" / "semireal_120_v1.yaml"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "results"

# SAST rules (regex patterns)
SAST_RULES = {
    "NET_UPLOAD": r"requests\.(post|put|patch)",
    "NET_DOWNLOAD": r"requests\.(get|head)",
    "EXEC_CMD": r"subprocess\.(run|call|Popen|check_output)|os\.system",
    "FILE_WRITE": r"open\([^)]+['\"]w['\"]|open\([^)]+['\"]a['\"]",
    "FILE_DELETE": r"os\.remove|os\.unlink|shutil\.rmtree",
    "ENV_ACCESS": r"os\.environ\[|os\.getenv",
    "BASE64": r"base64\.(b64decode|b64encode)",
}

# Privilege mapping
RULE_PRIVILEGE = {
    "NET_UPLOAD": "L3",
    "NET_DOWNLOAD": "L2",
    "EXEC_CMD": "L4",
    "FILE_WRITE": "L2",
    "FILE_DELETE": "L4",
    "ENV_ACCESS": "L3",
    "BASE64": "L2",  # Obfuscation indicator
}


def _extract_files_section(repo_snapshot):
    if not repo_snapshot:
        return ""
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
    return "\n".join(result).strip() if result else ""


def scan_case(case):
    files_content = _extract_files_section(case.get("repo_snapshot", ""))

    # Scan for patterns
    matched_rules = []
    for rule_name, pattern in SAST_RULES.items():
        if re.search(pattern, files_content):
            matched_rules.append(rule_name)

    # Determine derived privilege (max of all matched rules)
    if not matched_rules:
        derived_priv = "L0"
    else:
        privs = [RULE_PRIVILEGE[r] for r in matched_rules]
        priv_rank = {"L0": 0, "L1": 1, "L2": 2, "L3": 3, "L4": 4}
        max_priv = max(privs, key=lambda p: priv_rank[p])
        derived_priv = max_priv

    # Decision
    intent = case["intent_max_allowed"]
    priv_rank = {"L0": 0, "L1": 1, "L2": 2, "L3": 3, "L4": 4}
    if priv_rank[derived_priv] > priv_rank[intent]:
        decision = "BLOCK"
    else:
        decision = "ALLOW"

    return {
        "derived_privilege": derived_priv,
        "decision": decision,
        "matched_rules": matched_rules,
    }


def run():
    with open(BENCHMARK_PATH, "r", encoding="utf-8") as f:
        cases = yaml.safe_load(f)
    print(f"Loaded {len(cases)} cases from {BENCHMARK_PATH.name}")
    print(f"Using SAST (regex-based pattern matching)\n")

    OUTPUT_DIR.mkdir(exist_ok=True)

    # Scan all cases
    results = []
    for i, case in enumerate(cases):
        cid = case["case_id"]
        print(f"  [{i+1}/{len(cases)}] SAST: {cid} ...")
        scan_result = scan_case(case)
        results.append({
            "case": case,
            **scan_result,
        })

    # Save results
    csv_path = OUTPUT_DIR / "sr120v1_baseline_sast.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "case_id", "is_trap", "intent_max_allowed",
            "derived_privilege", "decision", "matched_rules",
        ])
        for r in results:
            case = r["case"]
            writer.writerow([
                case["case_id"],
                case["is_trap"],
                case["intent_max_allowed"],
                r["derived_privilege"],
                r["decision"],
                ",".join(r["matched_rules"]),
            ])
    print(f"\nResults saved to {csv_path}")

    # Summary
    print("\n" + "=" * 80)
    print("SAST SUMMARY (SemiReal-120 v1)")
    print("=" * 80)
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
    traps = [r for r in reader if r["is_trap"] == "True"]
    benigns = [r for r in reader if r["is_trap"] == "False"]
    trap_blocked = sum(1 for r in traps if r["decision"] == "BLOCK")
    benign_blocked = sum(1 for r in benigns if r["decision"] == "BLOCK")
    asr = (len(traps) - trap_blocked) / len(traps) if traps else 0
    fbr = benign_blocked / len(benigns) if benigns else 0
    utility = 1 - (asr + fbr) / 2
    print(f"  ASR={asr:.2%}  FBR={fbr:.2%}  Utility={utility:.2%}")
    print(f"  (trap BLOCK={trap_blocked}/{len(traps)}, benign BLOCK={benign_blocked}/{len(benigns)})")
    print("=" * 80)


if __name__ == "__main__":
    run()
