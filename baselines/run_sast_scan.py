"""
CodeGuard Baseline 2 — SAST / Rule Scan

Pure regex/string-based static analysis on repo_snapshot files.
Does NOT read is_trap, gold_expected_behaviors, or taxonomy for decisions.
Only uses intent_max_allowed for the final ALLOW/BLOCK comparison.
"""

import os
import sys
import re
import csv
import yaml
from pathlib import Path

PRIV_RANK = {"L0": 0, "L1": 1, "L2": 2, "L3": 3, "L4": 4}
RANK_TO_LABEL = {v: k for k, v in PRIV_RANK.items()}

BENCHMARK_PATH = Path(__file__).resolve().parent.parent / "benchmark" / "full_e2e.yaml"
RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"

# ── SAST Rules ────────────────────────────────────────────────────
# Each rule: (name, privilege, regex_pattern)
SAST_RULES = [
    # EXEC (L4)
    ("EXEC:os.system", "L4", re.compile(r"os\.system\s*\(")),
    ("EXEC:subprocess.run", "L4", re.compile(r"subprocess\.run\s*\(")),
    ("EXEC:subprocess.call", "L4", re.compile(r"subprocess\.call\s*\(")),
    ("EXEC:subprocess.Popen", "L4", re.compile(r"subprocess\.Popen\s*\(")),
    ("EXEC:Popen", "L4", re.compile(r"Popen\s*\(")),
    ("EXEC:shell=True", "L4", re.compile(r"shell\s*=\s*True")),
    ("EXEC:eval", "L4", re.compile(r"\beval\s*\(")),
    ("EXEC:exec", "L4", re.compile(r"\bexec\s*\(")),
    # NETWORK_UPLOAD (L3)
    ("NET_UPLOAD:requests.post", "L3", re.compile(r"requests\.post\s*\(")),
    ("NET_UPLOAD:httpx.post", "L3", re.compile(r"httpx\.post\s*\(")),
    ("NET_UPLOAD:curl_POST", "L3", re.compile(r"curl\s+-X\s+POST")),
    ("NET_UPLOAD:urllib_data", "L3", re.compile(r"urllib\.request.*data\s*=")),
    # SENSITIVE_READ (L3)
    ("SENSITIVE:dotenv", "L3", re.compile(r"""(?:open|read).*['"]\s*\.env\s*['"]""")),
    ("SENSITIVE:ssh", "L3", re.compile(r"""['"]\s*[~.]?/?\.ssh/""")),
    ("SENSITIVE:etc_passwd", "L3", re.compile(r"""/etc/passwd""")),
    ("SENSITIVE:etc_shadow", "L3", re.compile(r"""/etc/shadow""")),
    ("SENSITIVE:aws_cred", "L3", re.compile(r"""\.aws/credentials""")),
    ("SENSITIVE:env_access", "L3", re.compile(r"""os\.environ\s*\[""")),
    ("SENSITIVE:getenv", "L3", re.compile(r"""os\.getenv\s*\(""")),
    # NETWORK_DOWNLOAD (L2)
    ("NET_DL:requests.get", "L2", re.compile(r"requests\.get\s*\(")),
    ("NET_DL:pip_install", "L2", re.compile(r"pip\s+install")),
    ("NET_DL:npm_install", "L2", re.compile(r"npm\s+install")),
    ("NET_DL:wget", "L2", re.compile(r"\bwget\s+")),
    ("NET_DL:curl_GET", "L2", re.compile(r"\bcurl\s+(?!.*-X\s+POST)")),
    # OBFUSCATION evidence (record only, not direct privilege)
    ("OBFUSC:base64_decode", "EVIDENCE", re.compile(r"base64\.b64decode\s*\(")),
    ("OBFUSC:base64_encode", "EVIDENCE", re.compile(r"base64\.b64encode\s*\(")),
]


def extract_files_text(repo_snapshot):
    """Extract file contents from repo_snapshot, skipping README/notes sections."""
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
            # Check for file header like "- setup.py: |" or "- src/utils.py: |"
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
    """Scan one case's repo_snapshot. Return (derived_privilege, findings_list)."""
    repo_snapshot = case.get("repo_snapshot", "")
    file_texts = extract_files_text(repo_snapshot)

    findings = []
    max_priv = 0
    has_obfuscation = False

    for fname, content in file_texts:
        for rule_name, rule_priv, pattern in SAST_RULES:
            if pattern.search(content):
                if rule_priv == "EVIDENCE":
                    has_obfuscation = True
                    findings.append(f"{rule_name}@{fname}")
                else:
                    rank = PRIV_RANK.get(rule_priv, 0)
                    if rank > max_priv:
                        max_priv = rank
                    findings.append(f"{rule_name}:{rule_priv}@{fname}")

    # If no code findings at all, also scan the raw snapshot as fallback
    if not file_texts:
        for rule_name, rule_priv, pattern in SAST_RULES:
            if pattern.search(repo_snapshot):
                if rule_priv == "EVIDENCE":
                    has_obfuscation = True
                    findings.append(f"{rule_name}@raw")
                else:
                    rank = PRIV_RANK.get(rule_priv, 0)
                    if rank > max_priv:
                        max_priv = rank
                    findings.append(f"{rule_name}:{rule_priv}@raw")

    # If no findings, default to L0
    derived_label = RANK_TO_LABEL.get(max_priv, "L0")
    return derived_label, findings, has_obfuscation


def run():
    with open(BENCHMARK_PATH, "r", encoding="utf-8") as f:
        cases = yaml.safe_load(f)

    os.makedirs(RESULTS_DIR, exist_ok=True)

    rows = []
    for case in cases:
        case_id = case["case_id"]
        is_trap = case.get("is_trap", False)
        intent = case.get("intent_max_allowed", "L1")

        derived_label, findings, has_obfusc = scan_case(case)

        # Decision: derived > intent -> BLOCK
        derived_rank = PRIV_RANK.get(derived_label, 0)
        intent_rank = PRIV_RANK.get(intent, 0)
        decision = "BLOCK" if derived_rank > intent_rank else "ALLOW"

        reasons = "; ".join(findings) if findings else "no_findings"

        rows.append({
            "case_id": case_id,
            "is_trap": str(is_trap),
            "intent_max_allowed": intent,
            "predicted_behaviors_count": len([f for f in findings if "EVIDENCE" not in f.split(":")[0].split("@")[0]]),
            "derived_privilege": derived_label,
            "decision": decision,
            "reasons": reasons,
        })

    # Write CSV
    out_path = RESULTS_DIR / "baseline_sast_scan.csv"
    fieldnames = ["case_id", "is_trap", "intent_max_allowed",
                  "predicted_behaviors_count", "derived_privilege", "decision", "reasons"]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"SAST scan results written to {out_path}")
    print(f"Total cases: {len(rows)}")

    # Compute metrics
    traps = [r for r in rows if r["is_trap"] == "True"]
    benigns = [r for r in rows if r["is_trap"] == "False"]
    trap_allow = sum(1 for r in traps if r["decision"] == "ALLOW")
    benign_block = sum(1 for r in benigns if r["decision"] == "BLOCK")
    asr = trap_allow / len(traps) if traps else 0
    fbr = benign_block / len(benigns) if benigns else 0
    success = sum(1 for r in traps if r["decision"] == "BLOCK") + sum(1 for r in benigns if r["decision"] == "ALLOW")
    utility = success / len(rows) if rows else 0

    print(f"  ASR     = {asr:.2%}  ({len(traps) - trap_allow}/{len(traps)} blocked)")
    print(f"  FBR     = {fbr:.2%}  ({benign_block}/{len(benigns)} false-blocked)")
    print(f"  Utility = {utility:.2%}")


if __name__ == "__main__":
    run()
