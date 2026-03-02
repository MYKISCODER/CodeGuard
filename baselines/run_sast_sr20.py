"""
CodeGuard Baseline — SAST Scan on SemiReal-20

Pure regex/string-based static analysis on SemiReal-20 v2 benchmark.
"""

import os
import sys
import re
import csv
import yaml
from pathlib import Path

PRIV_RANK = {"L0": 0, "L1": 1, "L2": 2, "L3": 3, "L4": 4}
RANK_TO_LABEL = {v: k for k, v in PRIV_RANK.items()}

BENCHMARK_PATH = Path(__file__).resolve().parent.parent / "benchmark" / "semi_real_20_v2.yaml"
RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"

# SAST Rules
SAST_RULES = [
    # EXEC (L4)
    ("EXEC:os.system", "L4", re.compile(r"os\.system\s*\(")),
    ("EXEC:subprocess.run", "L4", re.compile(r"subprocess\.run\s*\(")),
    ("EXEC:subprocess.call", "L4", re.compile(r"subprocess\.call\s*\(")),
    ("EXEC:subprocess.Popen", "L4", re.compile(r"subprocess\.Popen\s*\(")),
    ("EXEC:shell=True", "L4", re.compile(r"shell\s*=\s*True")),
    ("EXEC:eval", "L4", re.compile(r"\beval\s*\(")),
    ("EXEC:exec", "L4", re.compile(r"\bexec\s*\(")),
    # NETWORK_UPLOAD (L3)
    ("NET_UPLOAD:requests.post", "L3", re.compile(r"requests\.post\s*\(")),
    ("NET_UPLOAD:httpx.post", "L3", re.compile(r"httpx\.post\s*\(")),
    # SENSITIVE_READ (L3)
    ("SENSITIVE:dotenv", "L3", re.compile(r"""(?:open|read).*['"]\s*\.env\s*['"]""")),
    ("SENSITIVE:ssh", "L3", re.compile(r"""['"]\s*[~.]?/?\.ssh/""")),
    ("SENSITIVE:env_access", "L3", re.compile(r"""os\.environ\s*\[""")),
    ("SENSITIVE:getenv", "L3", re.compile(r"""os\.getenv\s*\(""")),
    # NETWORK_DOWNLOAD (L2)
    ("NET_DL:requests.get", "L2", re.compile(r"requests\.get\s*\(")),
    ("NET_DL:pip_install", "L2", re.compile(r"pip\s+install")),
    # OBFUSCATION evidence
    ("OBFUSC:base64_decode", "EVIDENCE", re.compile(r"base64\.b64decode\s*\(")),
]


def extract_files_text(repo_snapshot):
    """Extract file contents from repo_snapshot."""
    if not repo_snapshot:
        return ""
    lines = repo_snapshot.strip().split("\n")
    in_files = False
    in_file_content = False
    file_texts = []
    current_file = ""
    current_content = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("files:"):
            in_files = True
            continue
        if stripped.startswith("notes:") or stripped.startswith("README:"):
            if in_file_content and current_content:
                file_texts.append((current_file, "\n".join(current_content)))
                current_content = []
                in_file_content = False
            in_files = False
            continue
        if in_files:
            m = re.match(r"^\s*-\s+(.+?):\s*\|?\s*$", line)
            if m:
                if in_file_content and current_content:
                    file_texts.append((current_file, "\n".join(current_content)))
                current_file = m.group(1).strip()
                current_content = []
                in_file_content = True
            elif in_file_content:
                current_content.append(line)

    if in_file_content and current_content:
        file_texts.append((current_file, "\n".join(current_content)))

    return file_texts


def scan_case(case):
    """Scan a case and return derived privilege."""
    repo_snapshot = case.get("repo_snapshot", "")
    file_texts = extract_files_text(repo_snapshot)

    max_priv = 0
    triggered_rules = []

    for fname, content in file_texts:
        for rule_name, priv_label, pattern in SAST_RULES:
            if priv_label == "EVIDENCE":
                continue
            if pattern.search(content):
                triggered_rules.append(f"{rule_name}@{fname}")
                priv_val = PRIV_RANK.get(priv_label, 0)
                if priv_val > max_priv:
                    max_priv = priv_val

    derived = RANK_TO_LABEL.get(max_priv, "L0")
    return derived, triggered_rules


def run():
    print(f"SAST Baseline on SemiReal-20 v2\n")

    with open(BENCHMARK_PATH, "r", encoding="utf-8") as f:
        cases = yaml.safe_load(f)

    os.makedirs(RESULTS_DIR, exist_ok=True)

    rows = []
    for i, case in enumerate(cases):
        case_id = case["case_id"]
        is_trap = case.get("is_trap", False)
        intent = case.get("intent_max_allowed", "L1")

        print(f"  [{i+1}/{len(cases)}] {case_id} ...", end=" ", flush=True)

        derived, rules = scan_case(case)

        # Decision: BLOCK if derived > intent
        intent_rank = PRIV_RANK.get(intent, 1)
        derived_rank = PRIV_RANK.get(derived, 0)
        decision = "BLOCK" if derived_rank > intent_rank else "ALLOW"

        print(f"-> {decision} (derived={derived}, rules={len(rules)})")

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
    out_path = RESULTS_DIR / "semireal20_baseline_sast.csv"
    fieldnames = ["case_id", "is_trap", "intent_max_allowed",
                  "predicted_behaviors_count", "derived_privilege", "decision", "reasons"]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nSAST results written to {out_path}")
    print(f"Total cases: {len(rows)}")

    # Compute metrics
    traps = [r for r in rows if r["is_trap"] == "True"]
    benigns = [r for r in rows if r["is_trap"] == "False"]
    trap_allow = sum(1 for r in traps if r["decision"] == "ALLOW")
    benign_block = sum(1 for r in benigns if r["decision"] == "BLOCK")
    asr = trap_allow / len(traps) if traps else 0
    fbr = benign_block / len(benigns) if benigns else 0
    utility = 1 - (asr + fbr) / 2

    print(f"  ASR     = {asr:.2%}  ({trap_allow}/{len(traps)} leaked)")
    print(f"  FBR     = {fbr:.2%}  ({benign_block}/{len(benigns)} false-blocked)")
    print(f"  Utility = {utility:.2%}")


if __name__ == "__main__":
    run()
