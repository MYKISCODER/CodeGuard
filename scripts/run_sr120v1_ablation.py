"""
CodeGuard SR120v1 Full Ablation Study

Runs all ablation variants on SemiReal-120 v1 using existing Layer2 v4.1 results.
Ablations:
  1. Full System (baseline)
  2. No Layer 1 (skip sanitization — use raw repo_snapshot)
  3. No Schema Normalization
  4. No CI mapping (treat CI commands as EXEC_CMD)
  5. No ENV distinction (ENV_ACCESS -> L1 instead of L3)
  6. No Allowlist (no SAFE_HOSTS exemption)
  7. No Obfuscation Penalty (STRICT -> PERMISSIVE for obfuscation)
  8. STRICT mode (vs STRICT-EXEMPT)
  9. MODERATE mode
  10. PERMISSIVE mode
"""

import os
import sys
import csv
import json
import copy
from pathlib import Path
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "policy"))
from policy_engine import (
    arbitrate_case, arbitrate_behavior, normalize_behaviors,
    PRIV_RANK, RANK_TO_LABEL, _base_privilege, _host_in_allowlist, _is_sensitive,
)

BENCHMARK_PATH = Path(__file__).resolve().parent.parent / "benchmark" / "semireal_120_v1.yaml"
RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"
RAW_PATH = RESULTS_DIR / "sr120v1_layer2_v4_1_raw.json"


def load_data():
    with open(BENCHMARK_PATH, "r", encoding="utf-8") as f:
        cases = yaml.safe_load(f)
    with open(RAW_PATH, "r", encoding="utf-8") as f:
        raw = json.load(f)
    layer2 = {r["case_id"]: r["predicted_behaviors"] for r in raw}
    return cases, layer2


def compute_metrics(rows):
    traps = [r for r in rows if r["is_trap"]]
    benigns = [r for r in rows if not r["is_trap"]]
    trap_allow = sum(1 for r in traps if r["decision"] == "ALLOW")
    benign_block = sum(1 for r in benigns if r["decision"] == "BLOCK")
    asr = trap_allow / len(traps) if traps else 0
    fbr = benign_block / len(benigns) if benigns else 0
    utility = 1 - (trap_allow + benign_block) / len(rows) if rows else 0
    return asr, fbr, utility, trap_allow, benign_block


# ── Ablation variants ────────────────────────────────────────────

def run_full_system(cases, layer2):
    """Baseline: full CodeGuard STRICT-EXEMPT."""
    rows = []
    for c in cases:
        behaviors = layer2.get(c["case_id"], [])
        result = arbitrate_case(behaviors, c["intent_max_allowed"], "STRICT-EXEMPT")
        rows.append({"is_trap": c["is_trap"], "decision": result["decision"]})
    return rows


def run_no_normalization(cases, layer2):
    """Skip schema normalization before policy."""
    rows = []
    for c in cases:
        behaviors = layer2.get(c["case_id"], [])
        # Skip normalize_behaviors — pass raw behaviors directly
        if not behaviors:
            rows.append({"is_trap": c["is_trap"], "decision": "ALLOW"})
            continue
        results = [arbitrate_behavior(b, c["intent_max_allowed"], "STRICT-EXEMPT") for b in behaviors]
        decision = "BLOCK" if any(r["decision"] == "BLOCK" for r in results) else "ALLOW"
        rows.append({"is_trap": c["is_trap"], "decision": decision})
    return rows


def run_no_env_distinction(cases, layer2):
    """Treat ENV_ACCESS as L1 instead of L3 (remove R6)."""
    rows = []
    for c in cases:
        behaviors = layer2.get(c["case_id"], [])
        # Patch behaviors: change ENV_ACCESS to FILE_READ (maps to L1 via R5b)
        patched = []
        for b in behaviors:
            bp = dict(b)
            if bp.get("action") == "ENV_ACCESS":
                bp["action"] = "FILE_READ"
                bp["target_type"] = "LOCAL_PATH"
                bp["target_value"] = "env_var"
            patched.append(bp)
        result = arbitrate_case(patched, c["intent_max_allowed"], "STRICT-EXEMPT")
        rows.append({"is_trap": c["is_trap"], "decision": result["decision"]})
    return rows


def run_no_allowlist(cases, layer2):
    """No SAFE_HOSTS exemption — use STRICT mode (blocks all obfuscation)."""
    rows = []
    for c in cases:
        behaviors = layer2.get(c["case_id"], [])
        result = arbitrate_case(behaviors, c["intent_max_allowed"], "STRICT")
        rows.append({"is_trap": c["is_trap"], "decision": result["decision"]})
    return rows


def run_no_obfuscation_penalty(cases, layer2):
    """No obfuscation penalty — use PERMISSIVE mode."""
    rows = []
    for c in cases:
        behaviors = layer2.get(c["case_id"], [])
        result = arbitrate_case(behaviors, c["intent_max_allowed"], "PERMISSIVE")
        rows.append({"is_trap": c["is_trap"], "decision": result["decision"]})
    return rows


def run_mode(cases, layer2, mode):
    """Run with a specific policy mode."""
    rows = []
    for c in cases:
        behaviors = layer2.get(c["case_id"], [])
        result = arbitrate_case(behaviors, c["intent_max_allowed"], mode)
        rows.append({"is_trap": c["is_trap"], "decision": result["decision"]})
    return rows


def run_no_ci_mapping(cases, layer2):
    """Remove CI-aware mapping: treat all EXEC_CMD uniformly (no CI exemption).
    In practice, this means the v4.1 prompt's CI mapping is what we're ablating.
    Since Layer2 already extracted behaviors with CI awareness, we simulate
    'no CI mapping' by converting any benign CI case's empty behaviors to
    EXEC_CMD behaviors (as if the parser treated CI commands as executable)."""
    rows = []
    for c in cases:
        behaviors = layer2.get(c["case_id"], [])
        # For CI-related benign cases with no behaviors, add EXEC_CMD
        cid = c["case_id"]
        if "CI-TEST" in cid and not behaviors:
            behaviors = [{"action": "EXEC_CMD", "target_type": "LOCAL_PATH",
                         "target_pattern": "LITERAL_STRING", "obfuscation_scope": "NONE",
                         "data_flow": "NONE", "target_value": "pytest"}]
        result = arbitrate_case(behaviors, c["intent_max_allowed"], "STRICT-EXEMPT")
        rows.append({"is_trap": c["is_trap"], "decision": result["decision"]})
    return rows


def run():
    print("CodeGuard SR120v1 Full Ablation Study\n")
    cases, layer2 = load_data()
    print(f"Loaded {len(cases)} cases, {len(layer2)} Layer2 results\n")

    ablations = [
        ("Full System (STRICT-EXEMPT)", lambda: run_full_system(cases, layer2)),
        ("No Schema Normalization", lambda: run_no_normalization(cases, layer2)),
        ("No CI Mapping", lambda: run_no_ci_mapping(cases, layer2)),
        ("No ENV Distinction", lambda: run_no_env_distinction(cases, layer2)),
        ("No Allowlist (STRICT)", lambda: run_no_allowlist(cases, layer2)),
        ("No Obfusc. Penalty (PERMISSIVE)", lambda: run_no_obfuscation_penalty(cases, layer2)),
        ("MODERATE mode", lambda: run_mode(cases, layer2, "MODERATE")),
    ]

    print(f"{'Variant':<35s} {'ASR':>6s} {'FBR':>6s} {'Util':>6s} {'TrapLeak':>9s} {'BenBlk':>7s}")
    print("-" * 75)

    results_rows = []
    for name, fn in ablations:
        rows = fn()
        asr, fbr, util, tl, bb = compute_metrics(rows)
        print(f"{name:<35s} {asr:>5.1%} {fbr:>5.1%} {util:>5.1%} {tl:>4d}/60   {bb:>3d}/60")
        results_rows.append({
            "variant": name, "asr": f"{asr:.1%}", "fbr": f"{fbr:.1%}",
            "utility": f"{util:.1%}", "trap_leaked": tl, "benign_blocked": bb,
        })

    # Save CSV
    out_path = RESULTS_DIR / "sr120v1_ablation_full.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=results_rows[0].keys())
        writer.writeheader()
        writer.writerows(results_rows)
    print(f"\nResults saved to {out_path}")


if __name__ == "__main__":
    run()
