"""
CodeGuard — Main Comparison Table Generator

Combines CodeGuard (STRICT/MODERATE/PERMISSIVE) + LLM Judge + SAST Scan
into one main_table_codeguard_vs_baselines.csv
"""

import csv
from pathlib import Path

RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"


def compute_from_csv(path):
    with open(path, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    traps = [r for r in rows if r["is_trap"] == "True"]
    benigns = [r for r in rows if r["is_trap"] == "False"]
    trap_allow = sum(1 for r in traps if r["decision"] == "ALLOW")
    benign_block = sum(1 for r in benigns if r["decision"] == "BLOCK")
    asr = trap_allow / len(traps) if traps else 0
    fbr = benign_block / len(benigns) if benigns else 0
    success = (sum(1 for r in traps if r["decision"] == "BLOCK") +
               sum(1 for r in benigns if r["decision"] == "ALLOW"))
    utility = success / len(rows) if rows else 0
    return {
        "ASR": asr, "FBR": fbr, "Utility": utility,
        "n": len(rows),
        "trap_total": len(traps), "trap_blocked": len(traps) - trap_allow,
        "benign_total": len(benigns), "benign_blocked": benign_block,
    }


SYSTEMS = [
    ("Baseline: LLM Judge (gpt-4o-mini)", "baseline_llm_judge.csv"),
    ("Baseline: SAST Rule Scan", "baseline_sast_scan.csv"),
    ("CodeGuard Policy-only (STRICT)", "full_e2e_strict.csv"),
    ("CodeGuard Policy-only (STRICT-EXEMPT)", "full_e2e_strict_exempt.csv"),
    ("CodeGuard Policy-only (MODERATE)", "full_e2e_moderate.csv"),
    ("CodeGuard Policy-only (PERMISSIVE)", "full_e2e_permissive.csv"),
]


def run():
    out_rows = []
    for name, fname in SYSTEMS:
        path = RESULTS_DIR / fname
        if not path.exists():
            print(f"  SKIP (not found): {fname}")
            continue
        m = compute_from_csv(path)
        out_rows.append({
            "System": name,
            "ASR": f"{m['ASR']:.2%}",
            "FBR": f"{m['FBR']:.2%}",
            "Utility": f"{m['Utility']:.2%}",
            "n": m["n"],
            "Traps_Blocked": f"{m['trap_blocked']}/{m['trap_total']}",
            "Benign_Blocked": f"{m['benign_blocked']}/{m['benign_total']}",
        })

    out_path = RESULTS_DIR / "main_table_codeguard_vs_baselines.csv"
    fieldnames = ["System", "ASR", "FBR", "Utility", "n", "Traps_Blocked", "Benign_Blocked"]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(out_rows)

    print(f"\nMain comparison table -> {out_path}\n")
    # Pretty print
    print(f"{'System':<42s} {'ASR':>7s} {'FBR':>7s} {'Util':>7s} {'Trap BLK':>10s} {'Ben BLK':>10s}")
    print("-" * 90)
    for r in out_rows:
        print(f"{r['System']:<42s} {r['ASR']:>7s} {r['FBR']:>7s} {r['Utility']:>7s} {r['Traps_Blocked']:>10s} {r['Benign_Blocked']:>10s}")


if __name__ == "__main__":
    run()
