"""
CodeGuard — Slice Report Generator for 50-case E2E

Produces per-obfuscation and per-carrier/lifecycle slice tables
for all 4 policy modes.
"""

import os
import sys
import csv
import json
from pathlib import Path
from collections import defaultdict
import yaml

RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"
BENCHMARK_PATH = Path(__file__).resolve().parent.parent / "benchmark" / "full_e2e.yaml"
MODES = ["STRICT", "STRICT-EXEMPT", "MODERATE", "PERMISSIVE"]


def load_csv(mode):
    fname = f"full_e2e_{mode.lower().replace('-','_')}.csv"
    path = RESULTS_DIR / fname
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_cases():
    with open(BENCHMARK_PATH, "r", encoding="utf-8") as f:
        cases = yaml.safe_load(f)
    return {c["case_id"]: c for c in cases}


def slice_by_field(rows, cases, field_fn, label):
    """Group rows by a field and compute ASR/FBR per group."""
    groups = defaultdict(lambda: {"traps": 0, "benigns": 0, "trap_block": 0, "benign_block": 0})
    for r in rows:
        key = field_fn(r, cases.get(r["case_id"], {}))
        is_trap = r["is_trap"] == "True"
        if is_trap:
            groups[key]["traps"] += 1
            if r["decision"] == "BLOCK":
                groups[key]["trap_block"] += 1
        else:
            groups[key]["benigns"] += 1
            if r["decision"] == "BLOCK":
                groups[key]["benign_block"] += 1
    return groups


def print_slice(title, groups):
    print(f"\n  {title}")
    print(f"  {'Group':<20s} {'Traps':>6s} {'T-BLK':>6s} {'ASR':>7s} {'Benign':>7s} {'B-BLK':>6s} {'FBR':>7s}")
    print(f"  {'-'*20} {'-'*6} {'-'*6} {'-'*7} {'-'*7} {'-'*6} {'-'*7}")
    for key in sorted(groups.keys()):
        g = groups[key]
        asr = (g["traps"] - g["trap_block"]) / g["traps"] if g["traps"] else 0
        fbr = g["benign_block"] / g["benigns"] if g["benigns"] else 0
        print(f"  {key:<20s} {g['traps']:>6d} {g['trap_block']:>6d} {asr:>6.1%} {g['benigns']:>7d} {g['benign_block']:>6d} {fbr:>6.1%}")


def run():
    cases = load_cases()

    for mode in MODES:
        rows = load_csv(mode)
        print("=" * 80)
        print(f"  MODE: {mode}  (n={len(rows)})")
        print("=" * 80)

        # Slice by obfuscation_scope
        groups = slice_by_field(rows, cases,
            lambda r, c: r.get("gold_obfuscation", "?"),
            "obfuscation_scope")
        print_slice("By obfuscation_scope", groups)

        # Slice by carrier
        groups = slice_by_field(rows, cases,
            lambda r, c: c.get("taxonomy", {}).get("carrier", "?"),
            "carrier")
        print_slice("By carrier", groups)

        # Slice by lifecycle
        groups = slice_by_field(rows, cases,
            lambda r, c: c.get("taxonomy", {}).get("lifecycle", "?"),
            "lifecycle")
        print_slice("By lifecycle", groups)

        # Slice by target_pattern
        groups = slice_by_field(rows, cases,
            lambda r, c: c.get("gold_expected_behaviors", [{}])[0].get("target_pattern", "?"),
            "target_pattern")
        print_slice("By target_pattern", groups)

        print()

    # Failure case detail for STRICT-EXEMPT (should be empty) and PERMISSIVE
    print("\n" + "=" * 80)
    print("FAILURE CASE DETAILS")
    print("=" * 80)
    for mode in MODES:
        rows = load_csv(mode)
        failures = []
        for r in rows:
            is_trap = r["is_trap"] == "True"
            if is_trap and r["decision"] != "BLOCK":
                failures.append((r["case_id"], "LEAKED_TRAP", r["reasons"]))
            elif not is_trap and r["decision"] == "BLOCK":
                failures.append((r["case_id"], "FALSE_BLOCK", r["reasons"]))
        if failures:
            print(f"\n  {mode}:")
            for cid, ftype, reason in failures:
                c = cases.get(cid, {})
                obfusc = c.get("gold_expected_behaviors", [{}])[0].get("obfuscation_scope", "?")
                print(f"    {cid:<20s} {ftype:<14s} obfusc={obfusc:<16s} {reason[:60]}")
        else:
            print(f"\n  {mode}: NO FAILURES")


if __name__ == "__main__":
    run()
