"""
CodeGuard Baseline — Bandit (Real SAST) on SemiReal-120 v1

Extracts code from repo_snapshot, runs Bandit, maps findings to privilege levels,
and compares against intent_max_allowed for ALLOW/BLOCK decisions.
"""

import os
import sys
import re
import csv
import json
import tempfile
import subprocess
from pathlib import Path
import yaml

PRIV_RANK = {"L0": 0, "L1": 1, "L2": 2, "L3": 3, "L4": 4}
RANK_TO_LABEL = {v: k for k, v in PRIV_RANK.items()}

BENCHMARK_PATH = Path(__file__).resolve().parent.parent / "benchmark" / "semireal_120_v1.yaml"
RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"

# Map Bandit severity/confidence + test_id to privilege levels
# High severity issues related to command execution -> L4
# Network/credential issues -> L3
# File write/download -> L2
# Everything else -> L1
BANDIT_PRIV_MAP = {
    # B102: exec_used, B103: set_bad_file_permissions
    # B301: pickle, B302: marshal, B303: md5/sha1
    # B304-B305: ciphers, B306: mktemp
    # B307: eval, B308: mark_safe
    # B310: urllib_urlopen
    # B311: random
    # B312: telnetlib
    # B313-B320: xml parsers
    # B321: ftplib
    # B323: unverified_context
    # B324: hashlib
    # B401-B415: imports
    # B501-B510: crypto/ssl
    # B601-B609: shell/exec/sql
    # B610-B612: django
    # B701-B703: jinja2
    "B601": "L4",  # paramiko_calls
    "B602": "L4",  # subprocess_popen_with_shell_equals_true
    "B603": "L4",  # subprocess_without_shell_equals_true
    "B604": "L4",  # any_other_function_with_shell_equals_true
    "B605": "L4",  # start_process_with_a_shell
    "B606": "L4",  # start_process_with_no_shell
    "B607": "L4",  # start_process_with_partial_path
    "B102": "L4",  # exec_used
    "B307": "L4",  # eval
    "B310": "L3",  # urllib_urlopen
    "B321": "L3",  # ftplib
    "B312": "L3",  # telnetlib
    "B108": "L3",  # hardcoded_tmp_directory (potential sensitive path)
    "B105": "L3",  # hardcoded_password_string
    "B106": "L3",  # hardcoded_password_funcarg
    "B107": "L3",  # hardcoded_password_default
}

def extract_python_files(repo_snapshot):
    """Extract Python file contents from repo_snapshot string."""
    if not repo_snapshot:
        return []
    lines = repo_snapshot.strip().split("\n")
    in_files = False
    in_file_content = False
    files = []
    current_file = ""
    current_content = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("files:"):
            in_files = True
            continue
        if stripped.startswith("notes:") or stripped.startswith("README:"):
            if in_file_content and current_content:
                files.append((current_file, "\n".join(current_content)))
                current_content = []
                in_file_content = False
            in_files = False
            continue
        if in_files:
            m = re.match(r"^\s*-\s+(.+?):\s*\|?\s*$", line)
            if m:
                if in_file_content and current_content:
                    files.append((current_file, "\n".join(current_content)))
                current_file = m.group(1).strip()
                current_content = []
                in_file_content = True
            elif in_file_content:
                current_content.append(line)

    if in_file_content and current_content:
        files.append((current_file, "\n".join(current_content)))

    # Only return Python files
    return [(f, c) for f, c in files if f.endswith(".py")]


def run_bandit_on_code(python_files):
    """Write files to temp dir, run bandit, return findings."""
    if not python_files:
        return []

    with tempfile.TemporaryDirectory() as tmpdir:
        for fname, content in python_files:
            # Handle subdirectory paths
            fpath = Path(tmpdir) / fname
            fpath.parent.mkdir(parents=True, exist_ok=True)
            # Dedent content (repo_snapshot often has extra indentation)
            dedented = "\n".join(
                l[4:] if l.startswith("    ") else l
                for l in content.split("\n")
            )
            fpath.write_text(dedented, encoding="utf-8")

        try:
            result = subprocess.run(
                ["bandit", "-r", tmpdir, "-f", "json", "-q"],
                capture_output=True, text=True, timeout=30,
            )
            if result.stdout.strip():
                data = json.loads(result.stdout)
                return data.get("results", [])
        except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception) as e:
            print(f"  [WARN] Bandit error: {e}")
    return []

def findings_to_privilege(findings):
    """Map Bandit findings to max privilege level."""
    max_priv = 0
    triggered = []
    for f in findings:
        test_id = f.get("test_id", "")
        severity = f.get("issue_severity", "LOW")
        confidence = f.get("issue_confidence", "LOW")
        test_name = f.get("test_name", "")

        # Use specific mapping first
        if test_id in BANDIT_PRIV_MAP:
            priv = PRIV_RANK[BANDIT_PRIV_MAP[test_id]]
        elif severity == "HIGH" and confidence == "HIGH":
            priv = PRIV_RANK["L3"]
        elif severity == "HIGH":
            priv = PRIV_RANK["L2"]
        elif severity == "MEDIUM":
            priv = PRIV_RANK["L2"]
        else:
            priv = PRIV_RANK["L1"]

        if priv > max_priv:
            max_priv = priv
        triggered.append(f"B:{test_id}({test_name})={RANK_TO_LABEL[priv]}")

    return RANK_TO_LABEL.get(max_priv, "L0"), triggered


def scan_case(case):
    """Scan a single case with Bandit."""
    repo_snapshot = case.get("repo_snapshot", "")
    py_files = extract_python_files(repo_snapshot)
    if not py_files:
        return "L0", []
    findings = run_bandit_on_code(py_files)
    return findings_to_privilege(findings)


def run():
    print("Bandit SAST Baseline on SemiReal-120 v1\n")

    with open(BENCHMARK_PATH, "r", encoding="utf-8") as f:
        cases = yaml.safe_load(f)
    print(f"Loaded {len(cases)} cases")

    os.makedirs(RESULTS_DIR, exist_ok=True)
    rows = []

    for i, case in enumerate(cases):
        case_id = case["case_id"]
        is_trap = case.get("is_trap", False)
        intent = case.get("intent_max_allowed", "L1")

        print(f"  [{i+1}/{len(cases)}] {case_id} ...", end=" ", flush=True)
        derived, rules = scan_case(case)

        intent_rank = PRIV_RANK.get(intent, 1)
        derived_rank = PRIV_RANK.get(derived, 0)
        decision = "BLOCK" if derived_rank > intent_rank else "ALLOW"

        print(f"-> {decision} (derived={derived}, findings={len(rules)})")
        rows.append({
            "case_id": case_id,
            "is_trap": str(is_trap),
            "intent_max_allowed": intent,
            "predicted_behaviors_count": len(rules),
            "derived_privilege": derived,
            "decision": decision,
            "reasons": "; ".join(rules[:5]),
        })

    # Write CSV
    out_path = RESULTS_DIR / "sr120v1_baseline_bandit.csv"
    fieldnames = ["case_id", "is_trap", "intent_max_allowed",
                  "predicted_behaviors_count", "derived_privilege", "decision", "reasons"]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nResults written to {out_path}")

    # Metrics
    traps = [r for r in rows if r["is_trap"] == "True"]
    benigns = [r for r in rows if r["is_trap"] == "False"]
    trap_allow = sum(1 for r in traps if r["decision"] == "ALLOW")
    benign_block = sum(1 for r in benigns if r["decision"] == "BLOCK")
    asr = trap_allow / len(traps) if traps else 0
    fbr = benign_block / len(benigns) if benigns else 0
    utility = 1 - (trap_allow + benign_block) / len(rows) if rows else 0

    print(f"\n{'='*60}")
    print(f"  ASR     = {asr:.1%}  ({trap_allow}/{len(traps)} leaked)")
    print(f"  FBR     = {fbr:.1%}  ({benign_block}/{len(benigns)} false-blocked)")
    print(f"  Utility = {utility:.1%}")
    print(f"{'='*60}")


if __name__ == "__main__":
    run()
