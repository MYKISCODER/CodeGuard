"""
CodeGuard Baseline — Semgrep (Real SAST) on SemiReal-120 v1

Extracts code from repo_snapshot, runs Semgrep with Python security rules,
maps findings to privilege levels, and produces ALLOW/BLOCK decisions.
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
RULES_PATH = Path(__file__).resolve().parent / "semgrep_rules.yml"

# Map Semgrep rule IDs / categories to privilege levels
# Semgrep python security rules use patterns like:
#   python.lang.security.audit.subprocess-shell-true
#   python.lang.security.audit.exec-used
SEMGREP_PRIV_KEYWORDS = {
    # L4: command execution
    "subprocess": "L4",
    "exec": "L4",
    "eval": "L4",
    "os-system": "L4",
    "popen": "L4",
    "command-injection": "L4",
    "code-injection": "L4",
    # L3: network / credentials / sensitive
    "request": "L3",
    "urllib": "L3",
    "http": "L3",
    "hardcoded-password": "L3",
    "hardcoded-secret": "L3",
    "credential": "L3",
    "ssrf": "L3",
    # L2: file ops / misc
    "path-traversal": "L2",
    "file": "L2",
    "write": "L2",
    "pickle": "L2",
    "marshal": "L2",
    "yaml-load": "L2",
    "deserialization": "L2",
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

    return [(f, c) for f, c in files if f.endswith(".py")]


def rule_id_to_privilege(rule_id):
    """Map a Semgrep rule ID to a privilege level via keyword matching."""
    rid_lower = rule_id.lower()
    for keyword, priv in SEMGREP_PRIV_KEYWORDS.items():
        if keyword in rid_lower:
            return priv
    return "L1"


def run_semgrep_on_code(python_files):
    """Write files to temp dir, run semgrep, return findings."""
    if not python_files:
        return []

    with tempfile.TemporaryDirectory() as tmpdir:
        for fname, content in python_files:
            fpath = Path(tmpdir) / fname
            fpath.parent.mkdir(parents=True, exist_ok=True)
            dedented = "\n".join(
                l[4:] if l.startswith("    ") else l
                for l in content.split("\n")
            )
            fpath.write_text(dedented, encoding="utf-8")

        try:
            result = subprocess.run(
                ["semgrep", "scan", "--config", str(RULES_PATH),
                 "--json", "--quiet", "--no-git-ignore", tmpdir],
                capture_output=True, text=True, timeout=60,
            )
            if result.stdout.strip():
                data = json.loads(result.stdout)
                return data.get("results", [])
        except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception) as e:
            print(f"  [WARN] Semgrep error: {e}")
    return []


def findings_to_privilege(findings):
    """Map Semgrep findings to max privilege level."""
    max_priv = 0
    triggered = []
    for f in findings:
        rule_id = f.get("check_id", "")
        severity = f.get("extra", {}).get("severity", "INFO")

        priv_label = rule_id_to_privilege(rule_id)
        priv = PRIV_RANK[priv_label]

        if priv > max_priv:
            max_priv = priv
        short_id = rule_id.split(".")[-1] if "." in rule_id else rule_id
        triggered.append(f"SG:{short_id}={priv_label}")

    return RANK_TO_LABEL.get(max_priv, "L0"), triggered


def scan_case(case):
    """Scan a single case with Semgrep."""
    repo_snapshot = case.get("repo_snapshot", "")
    py_files = extract_python_files(repo_snapshot)
    if not py_files:
        return "L0", []
    findings = run_semgrep_on_code(py_files)
    return findings_to_privilege(findings)


def run():
    print("Semgrep SAST Baseline on SemiReal-120 v1\n")

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
    out_path = RESULTS_DIR / "sr120v1_baseline_semgrep.csv"
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
