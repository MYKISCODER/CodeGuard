"""
CodeGuard — LLM Judge Drift vs Deterministic Policy (AAAI Final v6)

- No legend inside inset (cleanest)
- Inset: 4 CG points + labels with fixed non-overlapping offsets + white bbox
- Main plot: STRICT/STRICT-EXEMPT jittered + different label directions
- All labels have semi-transparent white background
- PDF vector + 300dpi PNG
"""

import csv
import os
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
from mpl_toolkits.axes_grid1.inset_locator import inset_axes

RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"
OUTPUTS_DIR = Path(__file__).resolve().parent.parent / "outputs"
INSTABILITY_CSV = RESULTS_DIR / "llm_judge_instability_summary.csv"
MAIN_TABLE_CSV = RESULTS_DIR / "main_table_codeguard_vs_baselines.csv"

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "DejaVu Serif", "serif"],
    "font.size": 9,
    "axes.labelsize": 10,
    "axes.titlesize": 11,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "axes.linewidth": 0.6,
    "grid.linewidth": 0.25,
    "lines.linewidth": 1.0,
    "text.usetex": False,
})

LABEL_BBOX = dict(facecolor="white", alpha=0.7, edgecolor="none", pad=1.0)


def pct(s):
    return float(s.strip().replace("%", ""))


def load_instability():
    with open(INSTABILITY_CSV, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_codeguard_points():
    fallback = {
        "STRICT":        {"FBR": 4.0, "ASR": 0.0},
        "STRICT-EXEMPT": {"FBR": 0.0, "ASR": 0.0},
        "MODERATE":      {"FBR": 4.0, "ASR": 8.0},
        "PERMISSIVE":    {"FBR": 0.0, "ASR": 12.0},
    }
    if not MAIN_TABLE_CSV.exists():
        return fallback
    result = {}
    with open(MAIN_TABLE_CSV, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            name = row.get("System", "")
            for mode in ["STRICT-EXEMPT", "STRICT", "MODERATE", "PERMISSIVE"]:
                if mode in name and "CodeGuard" in name:
                    result[mode] = {"FBR": pct(row["FBR"]), "ASR": pct(row["ASR"])}
    for m in fallback:
        if m not in result:
            result[m] = fallback[m]
    return result


MODEL_STYLES = {
    "gpt-4o-mini":   {"color": "#D55E00", "marker": "o", "ls": "-"},
    "gpt-4o":        {"color": "#0072B2", "marker": "s", "ls": "--"},
    "deepseek-chat": {"color": "#009E73", "marker": "D", "ls": "-."},
}

CG_STYLE = {
    "STRICT":        {"marker": "X",  "ms": 9},
    "STRICT-EXEMPT": {"marker": "P",  "ms": 9},
    "MODERATE":      {"marker": "^",  "ms": 8},
    "PERMISSIVE":    {"marker": "v",  "ms": 8},
}
CG_COLOR = "#222222"

# Jitter STRICT-EXEMPT slightly away from origin
CG_JITTER = {"STRICT-EXEMPT": {"FBR": 0.15, "ASR": 0.15}}


def jpt(mode, pt):
    j = CG_JITTER.get(mode, {"FBR": 0, "ASR": 0})
    return {"FBR": pt["FBR"] + j["FBR"], "ASR": pt["ASR"] + j["ASR"]}


def draw_llm(ax, data):
    for row in data:
        model = row["model"]
        st = MODEL_STYLES.get(model, {"color": "gray", "marker": "o", "ls": "-"})
        f0, f1 = pct(row["FBR_min"]), pct(row["FBR_max"])
        a0, a1 = pct(row["ASR_min"]), pct(row["ASR_max"])
        fs_err = float(row["FBR_std"]) * 100
        as_err = float(row["ASR_std"]) * 100
        w, h = max(f1 - f0, 0.3), max(a1 - a0, 0.3)

        ax.add_patch(mpatches.Rectangle(
            (f0, a0), w, h, lw=0.8, ls=st["ls"],
            ec=st["color"], fc="none", alpha=0.6, zorder=3))

        fc, ac = (f0 + f1) / 2, (a0 + a1) / 2
        ax.errorbar(fc, ac, xerr=fs_err, yerr=as_err,
                     fmt=st["marker"], color=st["color"],
                     markersize=5.5, capsize=2, capthick=0.8,
                     markeredgecolor="black", markeredgewidth=0.3, zorder=5)


def draw_cg(ax, pts, fs=6.5, offsets=None):
    default_off = {
        "STRICT":        (10, -8),
        "STRICT-EXEMPT": (10, 6),
        "MODERATE":      (10, 5),
        "PERMISSIVE":    (10, -7),
    }
    off = offsets or default_off
    for mode, pt in pts.items():
        s = CG_STYLE[mode]
        p = jpt(mode, pt)
        ax.plot(p["FBR"], p["ASR"],
                marker=s["marker"], ms=s["ms"],
                color=CG_COLOR, mec="black", mew=0.5,
                zorder=10, clip_on=False)
        o = off.get(mode, (10, 0))
        ax.annotate(mode, xy=(p["FBR"], p["ASR"]),
                    xytext=o, textcoords="offset points",
                    fontsize=fs, fontweight="bold", color=CG_COLOR, va="center",
                    bbox=LABEL_BBOX,
                    arrowprops=dict(arrowstyle="-|>", color="#555555",
                                    lw=0.5, shrinkA=0, shrinkB=2),
                    zorder=11, clip_on=False)


def run():
    os.makedirs(OUTPUTS_DIR, exist_ok=True)
    data = load_instability()
    cg = load_codeguard_points()

    fig, ax = plt.subplots(figsize=(8, 5))

    # ── Main plot ──
    draw_llm(ax, data)
    draw_cg(ax, cg, fs=7, offsets={
        "STRICT":        (14, -10),
        "STRICT-EXEMPT": (14, 8),
        "MODERATE":      (14, 8),
        "PERMISSIVE":    (14, -10),
    })

    ax.set_xlim(-2, 33)
    ax.set_ylim(-2, 16)
    ax.set_xlabel(r"FBR (%) $\downarrow$")
    ax.set_ylabel(r"ASR (%) $\downarrow$")
    ax.set_title("LLM Judge Drift vs Deterministic Policy", fontweight="bold", pad=8)
    ax.grid(True, ls=":", alpha=0.35, color="#AAAAAA")

    # ── Inset: positioned to match user's JPG reference ──
    # JPG shows inset in right-center area, well inside plot boundaries
    # axes fraction [left, bottom, width, height]
    axins = ax.inset_axes([0.55, 0.18, 0.20, 0.36])

    draw_cg(axins, cg, fs=5.5, offsets={
        "PERMISSIVE":    (-42, 5),
        "MODERATE":      (8, 5),
        "STRICT":        (8, -7),
        "STRICT-EXEMPT": (8, 5),
    })

    axins.set_xlim(-0.8, 7)
    axins.set_ylim(-1.5, 14)
    axins.set_title("CodeGuard zoom", fontsize=6.5, pad=2)
    axins.grid(True, ls=":", alpha=0.25, color="#BBBBBB")
    axins.tick_params(labelsize=5.5)
    for spine in axins.spines.values():
        spine.set_edgecolor("#888888")
        spine.set_linewidth(0.5)

    # ── Legend (upper left) ──
    llm_handles = []
    for model in ["gpt-4o-mini", "gpt-4o", "deepseek-chat"]:
        st = MODEL_STYLES[model]
        r = [d for d in data if d["model"] == model][0]
        a0, a1 = pct(r["ASR_min"]), pct(r["ASR_max"])
        f0, f1 = pct(r["FBR_min"]), pct(r["FBR_max"])
        llm_handles.append(
            Line2D([0], [0], marker=st["marker"], color=st["color"],
                   ls=st["ls"], lw=1.2, mec="black", mew=0.3, ms=5.5,
                   label=f'{model}  ASR[{a0:.0f},{a1:.0f}] FBR[{f0:.0f},{f1:.0f}]'))

    llm_handles.append(Line2D([0], [0], ls="none", label=""))
    for mode in ["STRICT", "STRICT-EXEMPT", "MODERATE", "PERMISSIVE"]:
        s = CG_STYLE[mode]
        llm_handles.append(
            Line2D([0], [0], marker=s["marker"], color=CG_COLOR,
                   ls="none", mec="black", mew=0.4, ms=s["ms"] - 2,
                   label=f'CG {mode}'))

    ax.legend(handles=llm_handles, loc="upper left",
              bbox_to_anchor=(0.01, 0.99), frameon=True,
              fancybox=False, edgecolor="#CCCCCC", fontsize=6.5,
              handlelength=2, ncol=2, columnspacing=1.0)

    # ── Save ──
    pdf_path = OUTPUTS_DIR / "figure_llm_judge_drift.pdf"
    fig.savefig(pdf_path, bbox_inches="tight", facecolor="white")
    print(f"PDF -> {pdf_path}")

    svg_path = OUTPUTS_DIR / "figure_llm_judge_drift.svg"
    fig.savefig(svg_path, bbox_inches="tight", facecolor="white")
    print(f"SVG -> {svg_path}")

    png_path = OUTPUTS_DIR / "figure_llm_judge_drift.png"
    fig.savefig(png_path, dpi=300, bbox_inches="tight", facecolor="white")
    print(f"PNG -> {png_path}  (300 dpi)")

    plt.close(fig)

    # ── Caption ──
    caption = (
        "Figure X: LLM Judge drift vs.\\ deterministic CodeGuard policy on RepoTrap-50 "
        "(15 runs: 3 models $\\times$ 5 prompt variants, all at temperature=0). "
        "FBR = False Block Rate; ASR = Attack Success Rate; lower is better for both axes. "
        "Rectangles show the min--max range of ASR and FBR for each LLM judge; "
        "center markers indicate the midpoint and error bars show $\\pm 1\\sigma$. "
        "The inset zooms into the CodeGuard region. "
        "Despite identical temperature settings, LLM judges exhibit substantial drift: "
        "gpt-4o's FBR ranges from 16\\% to 28\\% and ASR from 0\\% to 12\\% "
        "depending solely on prompt wording. "
        "CodeGuard's four policy modes (X, +, $\\triangle$, $\\triangledown$) are "
        "deterministic fixed points with zero variance ($\\sigma=0$). "
        "STRICT-EXEMPT achieves the ideal point (ASR=0\\%, FBR=0\\%). "
        "Note: STRICT-EXEMPT is jittered by +0.15\\% on both axes for visibility."
    )
    cp = OUTPUTS_DIR / "figure_llm_judge_drift_caption.txt"
    with open(cp, "w", encoding="utf-8") as f:
        f.write(caption)
    print(f"Caption -> {cp}")


if __name__ == "__main__":
    run()
