#!/usr/bin/env python3
"""
Generate a professional 3D taxonomy diagram for the CodeGuard P-L-C threat model.
Suitable for AAAI paper submission.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d import art3d
import numpy as np

# Dimension definitions
carriers = [
    "Metadata",
    "Documentation",
    "Source Code",
    "Build Artifacts",
]

lifecycles = [
    "Setup",
    "Planning",
    "Coding",
    "Execution",
    "Publish",
]

privileges = [
    "L0: Safe",
    "L1: Read-Only",
    "L2: Write-Local",
    "L3: Network/Exfil",
    "L4: System/Root",
]

priv_colors = [
    "#2ca02c",
    "#7ec850",
    "#f0c040",
    "#e8601c",
    "#c41e3a",
]

attack_examples = [
    (0, 0, 2, "Dep. confusion\n(install script)"),
    (2, 3, 4, "RCE via\ninjected code"),
    (1, 1, 1, "Prompt injection\nin README"),
    (3, 0, 3, "Makefile\nexfiltration"),
    (2, 2, 2, "Trojan in\nrefactored code"),
    (0, 4, 3, "Credential leak\non push"),
    (3, 3, 4, "CI config\nshell escape"),
]

fig = plt.figure(figsize=(7.5, 6.2), dpi=300, facecolor="white")
ax = fig.add_subplot(111, projection="3d", facecolor="white")
ax.view_init(elev=22, azim=-52)

nC = len(carriers)
nL = len(lifecycles)
nP = len(privileges)

# Draw light grid planes at each privilege level
for p_idx in range(nP):
    xx = [0, nC - 1, nC - 1, 0]
    yy = [0, 0, nL - 1, nL - 1]
    zz = [p_idx] * 4
    verts = [list(zip(xx, yy, zz))]
    poly = art3d.Poly3DCollection(verts, alpha=0.06, facecolor=priv_colors[p_idx],
                                   edgecolor=priv_colors[p_idx], linewidth=0.4)
    ax.add_collection3d(poly)

# Draw grid lines
grid_color = "#cccccc"
grid_lw = 0.3
grid_alpha = 0.5

for c in range(nC):
    for l in range(nL):
        ax.plot([c, c], [l, l], [0, nP - 1],
                color=grid_color, lw=grid_lw, alpha=grid_alpha, zorder=0)

for l in range(nL):
    for p in range(nP):
        ax.plot([0, nC - 1], [l, l], [p, p],
                color=grid_color, lw=grid_lw, alpha=grid_alpha, zorder=0)

for c in range(nC):
    for p in range(nP):
        ax.plot([c, c], [0, nL - 1], [p, p],
                color=grid_color, lw=grid_lw, alpha=grid_alpha, zorder=0)

# Draw axis spines
spine_color = "#333333"
spine_lw = 1.5
ax.plot([0, nC - 1], [0, 0], [0, 0], color=spine_color, lw=spine_lw, zorder=5)
ax.plot([0, 0], [0, nL - 1], [0, 0], color=spine_color, lw=spine_lw, zorder=5)
ax.plot([0, 0], [0, 0], [0, nP - 1], color=spine_color, lw=spine_lw, zorder=5)

arrow_ext = 0.35
ax.plot([nC - 1, nC - 1 + arrow_ext], [0, 0], [0, 0], color=spine_color, lw=spine_lw, zorder=5)
ax.plot([0, 0], [nL - 1, nL - 1 + arrow_ext], [0, 0], color=spine_color, lw=spine_lw, zorder=5)
ax.plot([0, 0], [0, 0], [nP - 1, nP - 1 + arrow_ext], color=spine_color, lw=spine_lw, zorder=5)

# Tick labels
label_fontsize = 5.5
axis_label_fontsize = 8

for i, name in enumerate(carriers):
    ax.text(i, -0.6, -0.15, name, fontsize=label_fontsize,
            ha="center", va="top", color="#333333", fontweight="normal",
            rotation=15)

for i, name in enumerate(lifecycles):
    ax.text(-0.55, i, -0.15, name, fontsize=label_fontsize,
            ha="right", va="top", color="#333333", fontweight="normal")

for i, name in enumerate(privileges):
    ax.text(-0.15, -0.55, i, name, fontsize=label_fontsize,
            ha="right", va="center", color=priv_colors[i], fontweight="bold")

# Axis dimension labels
ax.text((nC - 1) / 2, -1.5, -0.5,
        "Dimension C: Carrier", fontsize=axis_label_fontsize,
        ha="center", va="center", color="#222222", fontweight="bold",
        style="italic")

ax.text(-1.6, (nL - 1) / 2, -0.5,
        "Dimension L: Lifecycle", fontsize=axis_label_fontsize,
        ha="center", va="center", color="#222222", fontweight="bold",
        style="italic")

ax.text(-0.6, -1.4, (nP - 1) / 2,
        "Dimension P:\nPrivilege", fontsize=axis_label_fontsize,
        ha="center", va="center", color="#222222", fontweight="bold",
        style="italic")

# Small dots at every grid intersection
for c in range(nC):
    for l in range(nL):
        for p in range(nP):
            ax.scatter(c, l, p, s=4, color=priv_colors[p], alpha=0.25, zorder=2,
                       edgecolors="none")

# Plot attack example points
for (c, l, p, label) in attack_examples:
    color = priv_colors[p]
    ax.scatter(c, l, p, s=90, color=color, alpha=0.85, zorder=10,
               edgecolors="#222222", linewidths=0.6, marker="o", depthshade=True)
    ax.scatter(c, l, p, s=160, color="none", alpha=0.6, zorder=9,
               edgecolors=color, linewidths=0.8, marker="o")
    ax.plot([c, c], [l, l], [0, p], color=color, lw=0.6, alpha=0.4,
            linestyle="--", zorder=1)
    ax.text(c + 0.18, l + 0.18, p + 0.18, label, fontsize=4.2,
            ha="left", va="bottom", color="#222222",
            bbox=dict(boxstyle="round,pad=0.15", facecolor="white",
                      edgecolor=color, alpha=0.88, linewidth=0.5),
            zorder=11)

# Axis limits and cleanup
ax.set_xlim(-0.3, nC - 0.3)
ax.set_ylim(-0.3, nL - 0.3)
ax.set_zlim(-0.1, nP - 0.3)

ax.set_xticks([])
ax.set_yticks([])
ax.set_zticks([])
ax.set_xlabel("")
ax.set_ylabel("")
ax.set_zlabel("")

ax.xaxis.pane.fill = False
ax.yaxis.pane.fill = False
ax.zaxis.pane.fill = False
ax.xaxis.pane.set_edgecolor("none")
ax.yaxis.pane.set_edgecolor("none")
ax.zaxis.pane.set_edgecolor("none")

ax.xaxis.line.set_color("none")
ax.yaxis.line.set_color("none")
ax.zaxis.line.set_color("none")

# Legend
legend_handles = []
for i, (name, color) in enumerate(zip(privileges, priv_colors)):
    legend_handles.append(mpatches.Patch(facecolor=color, edgecolor="#555555",
                                          linewidth=0.4, label=name))

legend_handles.append(plt.Line2D([0], [0], marker="o", color="w",
                                  markerfacecolor="#888888",
                                  markeredgecolor="#222222",
                                  markersize=6, label="Example attack",
                                  linewidth=0))

leg = ax.legend(handles=legend_handles, loc="upper left",
                bbox_to_anchor=(0.0, 0.95), fontsize=5.5,
                frameon=True, fancybox=True, framealpha=0.92,
                edgecolor="#aaaaaa", title="Privilege Level",
                title_fontsize=6.5, handlelength=1.2, handleheight=0.9,
                borderpad=0.5, labelspacing=0.35)
leg.get_title().set_fontweight("bold")

fig.suptitle("P-L-C Three-Dimensional Threat Taxonomy",
             fontsize=10.5, fontweight="bold", color="#111111", y=0.96)

plt.tight_layout(rect=[0.0, 0.0, 1.0, 0.94])

out_path = r"D:\CodeGuard\figures\taxonomy_plc.png"
fig.savefig(out_path, dpi=300, bbox_inches="tight", facecolor="white",
            pad_inches=0.15)
plt.close(fig)
print(f"Saved: {out_path}")
