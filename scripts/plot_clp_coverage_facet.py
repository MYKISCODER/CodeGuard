#!/usr/bin/env python3
"""
Generate 2D faceted small-multiples of RepoTrap Coverage in C-L-P Threat Space.
Faceted by Privilege level (P), with Carrier on x-axis and Lifecycle on y-axis.

Usage:
    python scripts/plot_clp_coverage_facet.py [--style tight|roomy|all]

Output:
    figures/clp_coverage_facet.pdf / .png        (default)
    figures/clp_coverage_facet_tight.pdf / .png   (tight)
    figures/clp_coverage_facet_roomy.pdf / .png    (roomy)

Data source: benchmark/semireal_120_v1.yaml
"""

import yaml, argparse
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
BENCHMARK = ROOT / "benchmark" / "semireal_120_v1.yaml"
OUTDIR = ROOT / "figures"
OUTDIR.mkdir(exist_ok=True)

# ── Fixed axis orders ─────────────────────────────────────────────
CARRIERS = ["BUILD", "SOURCE", "DOCS", "METADATA"]
LIFECYCLES = ["SETUP", "PLANNING", "CODING", "EXECUTION", "PUBLISH"]
PRIVILEGES = ["L4", "L3", "L2", "L1", "L0"]

# Shortened tick labels (task 3C)
CARRIER_SHORT = ["BUILD", "SOURCE", "DOCS", "META"]
LIFECYCLE_SHORT = ["SETUP", "PLAN", "CODE", "EXEC", "PUBLISH"]

# ── Parse benchmark ───────────────────────────────────────────────
def load_cases(path):
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return [{
        "case_id": c["case_id"],
        "carrier": c["taxonomy"]["carrier"],
        "lifecycle": c["taxonomy"]["lifecycle"],
        "privilege": c["taxonomy"]["privilege"],
        "is_trap": bool(c["is_trap"]),
    } for c in data]

# ── Jitter helper ─────────────────────────────────────────────────
def jitter_points(n, rng, spread=0.20):
    if n <= 1:
        return np.zeros(n), np.zeros(n)
    return rng.uniform(-spread, spread, n), rng.uniform(-spread, spread, n)

# ── Style presets ─────────────────────────────────────────────────
STYLE = {
    "default": dict(
        figsize=(7.0, 5.2), fs_title=10, fs_tick=7, fs_legend=7.5,
        fs_panel=7.5, ms_trap=4.8, ms_benign=5.0, lw_benign=1.0,
        alpha_benign=0.8,
        wspace=0.26, hspace=0.32, top=0.90, bottom=0.09, left=0.10, right=0.97,
        strip_h=0.045,
    ),
    "tight": dict(
        figsize=(7.0, 4.8), fs_title=9.5, fs_tick=6.5, fs_legend=7,
        fs_panel=7, ms_trap=4.5, ms_benign=4.8, lw_benign=0.95,
        alpha_benign=0.8,
        wspace=0.22, hspace=0.26, top=0.90, bottom=0.09, left=0.09, right=0.98,
        strip_h=0.042,
    ),
    "roomy": dict(
        figsize=(7.2, 5.8), fs_title=10.5, fs_tick=7.5, fs_legend=8,
        fs_panel=8, ms_trap=5.2, ms_benign=5.5, lw_benign=1.1,
        alpha_benign=0.8,
        wspace=0.32, hspace=0.40, top=0.90, bottom=0.08, left=0.11, right=0.96,
        strip_h=0.050,
    ),
}

# ── Main drawing function ─────────────────────────────────────────
def draw_figure(cases, style_name="default", suffix=""):
    S = STYLE[style_name]
    rng = np.random.default_rng(42)

    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": ["Times New Roman", "DejaVu Serif", "serif"],
        "mathtext.fontset": "cm",
        "axes.linewidth": 0.35,
        "xtick.major.width": 0.3,
        "ytick.major.width": 0.3,
        "xtick.major.size": 2.0,
        "ytick.major.size": 2.0,
    })

    fig, axes = plt.subplots(2, 3, figsize=S["figsize"])
    fig.subplots_adjust(
        wspace=S["wspace"], hspace=S["hspace"],
        top=S["top"], bottom=S["bottom"],
        left=S["left"], right=S["right"],
    )

    priv_pos = {"L4": (0,0), "L3": (0,1), "L2": (0,2),
                "L1": (1,0), "L0": (1,1)}
    c_idx = {c: i for i, c in enumerate(CARRIERS)}
    l_idx = {l: i for i, l in enumerate(LIFECYCLES)}

    by_priv = {p: [] for p in PRIVILEGES}
    for c in cases:
        by_priv[c["privilege"]].append(c)

    for priv in PRIVILEGES:
        r, col = priv_pos[priv]
        ax = axes[r][col]
        panel = by_priv[priv]

        # Axes setup
        ax.set_xlim(-0.5, len(CARRIERS) - 0.5)
        ax.set_ylim(-0.5, len(LIFECYCLES) - 0.5)
        ax.set_xticks(range(len(CARRIERS)))
        ax.set_xticklabels(CARRIER_SHORT, fontsize=S["fs_tick"])
        ax.set_yticks(range(len(LIFECYCLES)))
        ax.set_yticklabels(LIFECYCLE_SHORT, fontsize=S["fs_tick"])
        ax.grid(True, color="#f4f4f4", linewidth=0.25, zorder=0)  # #3: lighter/thinner
        ax.set_axisbelow(True)
        ax.tick_params(axis="both", length=2, pad=2)

        # #1: ggplot-style facet strip ABOVE the panel
        label = f"P = {priv}  (n={len(panel)})"
        strip_y = 1.0  # top edge of axes in axes coords
        ax.annotate(label, xy=(0.5, strip_y), xycoords="axes fraction",
                    xytext=(0, 6), textcoords="offset points",
                    fontsize=S["fs_panel"], fontweight="bold",
                    ha="center", va="bottom",
                    bbox=dict(boxstyle="round,pad=0.25", facecolor="#eeeeee",
                              edgecolor="#cccccc", linewidth=0.4))

        # #6: L1 empty panel — slightly darker text
        if len(panel) == 0:
            ax.text(0.5, 0.45, "No cases at P = L1\n(by benchmark design)",
                    transform=ax.transAxes, ha="center", va="center",
                    fontsize=S["fs_tick"] + 0.5, color="#777777", style="italic")
            continue

        # Plot points
        cells = {}
        for c in panel:
            cells.setdefault((c["carrier"], c["lifecycle"]), []).append(c)

        for (car, lif), cc in cells.items():
            cx, cy = c_idx[car], l_idx[lif]
            dx, dy = jitter_points(len(cc), rng, spread=0.22)
            for i, c in enumerate(cc):
                if c["is_trap"]:
                    # #2: filled, solid, slightly smaller
                    ax.plot(cx+dx[i], cy+dy[i], "o", color="#1a1a1a",
                            markersize=S["ms_trap"], zorder=5, markeredgewidth=0)
                else:
                    # #2: hollow, thinner edge, alpha for overplot
                    ax.plot(cx+dx[i], cy+dy[i], "o", markerfacecolor="none",
                            markeredgecolor="#444444", markersize=S["ms_benign"],
                            markeredgewidth=S["lw_benign"], zorder=5,
                            alpha=S["alpha_benign"])

    # ── Legend panel (axes[1][2]) ──────────────────────────────────
    ax_leg = axes[1][2]
    ax_leg.axis("off")

    # #1: strip for legend panel too (consistency)
    ax_leg.annotate("Legend", xy=(0.5, 1.0), xycoords="axes fraction",
                    xytext=(0, 6), textcoords="offset points",
                    fontsize=S["fs_panel"], fontweight="bold",
                    ha="center", va="bottom",
                    bbox=dict(boxstyle="round,pad=0.25", facecolor="#eeeeee",
                              edgecolor="#cccccc", linewidth=0.4))

    # #5: improved legend labels
    elems = [
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#1a1a1a",
               markersize=6.5, label="Trap (filled)", markeredgewidth=0),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="none",
               markeredgecolor="#444444", markersize=6.5, label="Benign (hollow)",
               markeredgewidth=1.0),
    ]
    leg = ax_leg.legend(handles=elems, loc="center",
                        fontsize=S["fs_legend"], frameon=True,
                        edgecolor="#e0e0e0", fancybox=False,
                        handletextpad=0.5, borderpad=0.9)
    leg.get_frame().set_linewidth(0.35)

    # #5: N = 120 centered below legend
    ax_leg.text(0.5, 0.20, f"N = {len(cases)} cases",
                transform=ax_leg.transAxes, ha="center", va="center",
                fontsize=S["fs_legend"] - 0.5, color="#999999")

    # Suptitle
    fig.suptitle("RepoTrap Coverage in C\u2013L\u2013P Threat Space",
                 fontsize=S["fs_title"], fontweight="bold",
                 y=S["top"] + 0.07)

    # Save
    tag = f"_{suffix}" if suffix else ""
    pdf = OUTDIR / f"clp_coverage_facet{tag}.pdf"
    png = OUTDIR / f"clp_coverage_facet{tag}.png"
    fig.savefig(pdf, dpi=300, bbox_inches="tight")
    fig.savefig(png, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  {pdf}")
    print(f"  {png}")


# ── Sanity check ──────────────────────────────────────────────────
def print_sanity(cases):
    print(f"\nData: {BENCHMARK}  |  Total: {len(cases)}")
    for p in PRIVILEGES:
        sub = [c for c in cases if c["privilege"] == p]
        t = sum(1 for c in sub if c["is_trap"])
        print(f"  {p}: {len(sub)} (trap={t}, benign={len(sub)-t})")
    print()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--style", choices=["default","tight","roomy","all"], default="all")
    args = ap.parse_args()

    cases = load_cases(BENCHMARK)
    print_sanity(cases)

    styles = ["default","tight","roomy"] if args.style == "all" else [args.style]
    for s in styles:
        tag = "" if s == "default" else s
        print(f"[{s}]")
        draw_figure(cases, style_name=s, suffix=tag)
    print("Done.")
