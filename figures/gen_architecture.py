#!/usr/bin/env python3
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 8,
    "text.color": "#1a1a1a",
    "figure.facecolor": "white",
    "savefig.facecolor": "white",
    "savefig.dpi": 350,
})

C_INPUT = dict(fill="#E8EAF6", border="#3F51B5", header="#3F51B5", text_h="white")
C_L1 = dict(fill="#E3F2FD", border="#1565C0", header="#1565C0", text_h="white")
C_L2 = dict(fill="#FFF3E0", border="#E65100", header="#E65100", text_h="white")
C_JSON = dict(fill="#FFF8E1", border="#F9A825", header="#F9A825", text_h="white")
C_L3 = dict(fill="#E8F5E9", border="#2E7D32", header="#2E7D32", text_h="white")
C_ALLOW = dict(fill="#C8E6C9", border="#2E7D32", header="#2E7D32", text_h="white")
C_BLOCK = dict(fill="#FFCDD2", border="#C62828", header="#C62828", text_h="white")
C_ARROW = "#455A64"
C_ARROW_ALLOW = "#2E7D32"
C_ARROW_BLOCK = "#C62828"
NL = chr(10)

def draw_box(ax, x, y, w, h, colors, header_text=None, header_h=0.32,
             body_lines=None, fontsize_header=8.5, fontsize_body=7,
             subtitle=None, corner_radius=0.06, body_align="left",
             bold_header=True, header_fontsize_sub=7, zorder=2):
    body = FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad=0,rounding_size={corner_radius}",
        facecolor=colors["fill"], edgecolor=colors["border"],
        linewidth=1.3, zorder=zorder)
    ax.add_patch(body)
    if header_text:
        hdr_y = y + h - header_h
        hdr = FancyBboxPatch(
            (x, hdr_y), w, header_h,
            boxstyle=f"round,pad=0,rounding_size={corner_radius}",
            facecolor=colors["header"], edgecolor=colors["border"],
            linewidth=1.3, zorder=zorder + 1)
        ax.add_patch(hdr)
        mask = plt.Rectangle(
            (x + 0.005, hdr_y), w - 0.01, header_h * 0.55,
            facecolor=colors["header"], edgecolor="none", zorder=zorder + 1)
        ax.add_patch(mask)
        weight = "bold" if bold_header else "normal"
        ax.text(x + w/2, hdr_y + header_h/2 + (0.04 if subtitle else 0),
                header_text, ha="center", va="center",
                fontsize=fontsize_header, fontweight=weight,
                color=colors["text_h"], zorder=zorder + 2)
        if subtitle:
            ax.text(x + w/2, hdr_y + header_h/2 - 0.1,
                    subtitle, ha="center", va="center",
                    fontsize=header_fontsize_sub, fontstyle="italic",
                    color=colors["text_h"], zorder=zorder + 2, alpha=0.92)
    if body_lines:
        line_h = 0.17
        top_margin = 0.12
        start_y = y + h - header_h - top_margin - line_h * 0.5
        ha = body_align
        x_text = x + 0.12 if ha == "left" else x + w / 2
        for i, line in enumerate(body_lines):
            ly = start_y - i * line_h
            if ly < y + 0.04:
                break
            ax.text(x_text, ly, line, ha=ha, va="center",
                    fontsize=fontsize_body, color="#263238",
                    zorder=zorder + 2, family="sans-serif")
    return body

def draw_arrow(ax, x0, y0, x1, y1, color=C_ARROW, style="-|>",
               lw=1.4, connectionstyle="arc3,rad=0", zorder=5):
    arrow = FancyArrowPatch(
        (x0, y0), (x1, y1),
        arrowstyle=style, color=color,
        linewidth=lw, connectionstyle=connectionstyle,
        zorder=zorder, mutation_scale=12)
    ax.add_patch(arrow)
    return arrow

def draw_small_label(ax, x, y, text, fontsize=6.5, color="#455A64"):
    ax.text(x, y, text, ha="center", va="center", fontsize=fontsize,
            color=color, fontstyle="italic", zorder=10)
# === Main figure ===
fig, ax = plt.subplots(figsize=(14.5, 6.2))
ax.set_xlim(-0.3, 14.8)
ax.set_ylim(-0.5, 6.0)
ax.set_aspect("equal")
ax.axis("off")

# 0) INPUT
inp_x, inp_y, inp_w, inp_h = 0.0, 1.6, 2.0, 2.8
draw_box(ax, inp_x, inp_y, inp_w, inp_h, C_INPUT,
    header_text="Agent Input", header_h=0.34,
    body_lines=["Agent generates a", "tool call based on", "repository content:", "",
        " • Shell commands", " • File operations", " • Network requests"],
    fontsize_header=9, fontsize_body=7.2)

# 1) LAYER 1
l1_x, l1_y, l1_w, l1_h = 2.8, 0.7, 2.8, 4.6
draw_box(ax, l1_x, l1_y, l1_w, l1_h, C_L1,
    header_text="Layer 1 — Sanitization", header_h=0.38,
    subtitle="Input Boundary",
    body_lines=["AST-based stripping:", "  • Remove comments", "  • Remove docstrings", "",
        "Content separation:", "  Trusted:", "    code logic, tool params,", "    system policy",
        "  Untrusted:", "    README, issues,", "    comments, user text", "",
        "Only trusted content", "passes to Layer 2.", "",
        "Note: upstream agent", "still reads all repo", "content; L1 only filters", "Layer 2 input."],
    fontsize_header=9, fontsize_body=6.8)

t_x, t_y, t_w, t_h = l1_x + 0.15, l1_y + 1.55, 1.15, 0.85
draw_box(ax, t_x, t_y, t_w, t_h,
    dict(fill="#BBDEFB", border="#1565C0", header="#1976D2", text_h="white"),
    header_text="Trusted", header_h=0.26,
    body_lines=["code logic", "tool params", "system policy"],
    fontsize_header=7.5, fontsize_body=6.2, corner_radius=0.04, zorder=3)

u_x = t_x + t_w + 0.2
draw_box(ax, u_x, t_y, t_w, t_h,
    dict(fill="#FFCCBC", border="#BF360C", header="#D84315", text_h="white"),
    header_text="Untrusted", header_h=0.26,
    body_lines=["README", "issues", "comments"],
    fontsize_header=7.5, fontsize_body=6.2, corner_radius=0.04, zorder=3)

ax.text(u_x + t_w/2, t_y - 0.18, "XXX blocked",
    ha="center", va="center", fontsize=6, color="#BF360C", fontweight="bold", zorder=4)
ax.text(t_x + t_w/2, t_y - 0.18, "PASS >>>",
    ha="center", va="center", fontsize=6, color="#1565C0", fontweight="bold", zorder=4)
# 2) LAYER 2
l2_x, l2_y, l2_w, l2_h = 6.4, 0.7, 2.6, 4.6
draw_box(ax, l2_x, l2_y, l2_w, l2_h, C_L2,
    header_text="Layer 2 — Audit Parser", header_h=0.38,
    subtitle='"The Coroner"  (LoRA Fine-tuned)',
    body_lines=["Input: sanitized code +", "  tool call parameters", "",
        "Output: structured JSON", "with objective behavior", "facts (no safety judgment):", "",
        " • action", " • target_type", " • target_pattern",
        " • obfuscation_scope", " • data_flow", " • target_value", "",
        '"Describes WHAT the', ' code does, not WHETHER', ' it is safe."'],
    fontsize_header=9, fontsize_body=6.8)

# 2.5) JSON BOX
js_x, js_y, js_w, js_h = 9.35, 1.65, 1.55, 2.7
draw_box(ax, js_x, js_y, js_w, js_h, C_JSON,
    header_text="Behavior JSON", header_h=0.30,
    body_lines=["{",
        '  "action":', "    FILE_WRITE,",
        '  "target_type":', "    LOCAL_PATH,",
        '  "target_pattern":', "    LITERAL_STRING,",
        '  "obfuscation":', "    NONE,",
        '  "data_flow":', "    LOCAL_OP",
        "}"],
    fontsize_header=7.5, fontsize_body=5.8, corner_radius=0.04)

# 3) LAYER 3
l3_x, l3_y, l3_w, l3_h = 11.25, 0.7, 2.6, 4.6
draw_box(ax, l3_x, l3_y, l3_w, l3_h, C_L3,
    header_text="Layer 3 — Policy Engine", header_h=0.38,
    subtitle='"The Judge"  (Deterministic)',
    body_lines=["Sub-components:", "",
        " 1. Privilege Mapping", "    behavior → L0–L4", "",
        " 2. Allowlist Check", "    SAFE_HOSTS → L1", "",
        " 3. Obfuscation Penalty", "    hiding → escalate", "",
        " 4. Unresolvable Target", "    unknown → +1 level", "",
        " 5. Intent Alignment", "    derived vs. allowed"],
    fontsize_header=9, fontsize_body=6.8)
# 4) OUTPUT
out_x = 14.2
allow_y, allow_h = 3.4, 0.9
block_y, block_h = 1.7, 0.9

ax.add_patch(FancyBboxPatch((out_x-0.45, allow_y), 0.9, allow_h,
    boxstyle="round,pad=0,rounding_size=0.08",
    facecolor=C_ALLOW["fill"], edgecolor=C_ALLOW["border"], linewidth=2.0, zorder=3))
ax.text(out_x, allow_y+allow_h/2+0.12, "ALLOW",
    ha="center", va="center", fontsize=11, fontweight="bold", color="#1B5E20", zorder=4)
ax.text(out_x, allow_y+allow_h/2-0.15, "Tool call" + NL + "executes",
    ha="center", va="center", fontsize=6.5, color="#2E7D32", zorder=4)

ax.add_patch(FancyBboxPatch((out_x-0.45, block_y), 0.9, block_h,
    boxstyle="round,pad=0,rounding_size=0.08",
    facecolor=C_BLOCK["fill"], edgecolor=C_BLOCK["border"], linewidth=2.0, zorder=3))
ax.text(out_x, block_y+block_h/2+0.12, "BLOCK",
    ha="center", va="center", fontsize=11, fontweight="bold", color="#B71C1C", zorder=4)
ax.text(out_x, block_y+block_h/2-0.15, "Rejected +" + NL + "audit log",
    ha="center", va="center", fontsize=6.5, color="#C62828", zorder=4)

# ARROWS
mid_y = 3.0
draw_arrow(ax, inp_x+inp_w, mid_y, l1_x, mid_y, color=C_ARROW, lw=1.6)
draw_small_label(ax, (inp_x+inp_w+l1_x)/2, mid_y+0.18, "tool call")
draw_arrow(ax, l1_x+l1_w, mid_y, l2_x, mid_y, color=C_ARROW, lw=1.6)
draw_small_label(ax, (l1_x+l1_w+l2_x)/2, mid_y+0.18, "trusted only")
draw_arrow(ax, l2_x+l2_w, mid_y, js_x, mid_y, color=C_ARROW, lw=1.6)
draw_small_label(ax, (l2_x+l2_w+js_x)/2, mid_y+0.18, "structured")
draw_arrow(ax, js_x+js_w, mid_y, l3_x, mid_y, color=C_ARROW, lw=1.6)
draw_small_label(ax, (js_x+js_w+l3_x)/2, mid_y+0.18, "facts")
draw_arrow(ax, l3_x+l3_w, allow_y+allow_h/2, out_x-0.45, allow_y+allow_h/2,
    color=C_ARROW_ALLOW, lw=1.8, connectionstyle="arc3,rad=-0.15")
draw_arrow(ax, l3_x+l3_w, block_y+block_h/2, out_x-0.45, block_y+block_h/2,
    color=C_ARROW_BLOCK, lw=1.8, connectionstyle="arc3,rad=0.15")

# Layer badges
badge_y = 5.55
for bx, label, clr in [(l1_x+l1_w/2, "L1", C_L1["header"]),
                        (l2_x+l2_w/2, "L2", C_L2["header"]),
                        (l3_x+l3_w/2, "L3", C_L3["header"])]:
    ax.add_patch(plt.Circle((bx, badge_y), 0.22, facecolor=clr, edgecolor="white", linewidth=1.5, zorder=6))
    ax.text(bx, badge_y, label, ha="center", va="center", fontsize=8, fontweight="bold", color="white", zorder=7)

ax.text(7.25, 5.85, "CodeGuard: Three-Layer Defense-in-Depth Architecture",
    ha="center", va="center", fontsize=13, fontweight="bold", color="#1a1a1a", zorder=10)

ax.add_patch(FancyBboxPatch((2.55, 0.4), 11.55, 5.0,
    boxstyle="round,pad=0,rounding_size=0.12",
    facecolor="none", edgecolor="#90A4AE", linewidth=1.0, linestyle=(0,(5,3)), zorder=1))
ax.text(8.3, 0.2, "Defense-in-Depth Pipeline",
    ha="center", va="center", fontsize=7, color="#78909C", fontstyle="italic", zorder=2)

legend_items = [
    ("Actions:", "FILE_READ, FILE_WRITE, FILE_DELETE, NETWORK_CONNECT, EXEC_CMD, ENV_ACCESS"),
    ("Target types:", "LOCAL_PATH, PACKAGE_REPO, EXTERNAL_DOMAIN, SYSTEM_ENV, UNKNOWN"),
    ("Privilege levels:", "L0 (read-only) → L1 (local write) → L2 (install) → L3 (network) → L4 (exfiltration)"),
]
for i, (label, desc) in enumerate(legend_items):
    yp = -0.25 - i * 0.22
    ax.text(0.0, yp, label, ha="left", va="center", fontsize=6, fontweight="bold", color="#37474F", zorder=10)
    ax.text(1.2, yp, desc, ha="left", va="center", fontsize=5.8, color="#546E7A", zorder=10)

plt.tight_layout(pad=0.3)
out_path = os.path.join("D:" + os.sep, "CodeGuard", "figures", "codeguard_architecture.png")
fig.savefig(out_path, dpi=350, bbox_inches="tight", facecolor="white", edgecolor="none")
plt.close(fig)
print("Saved: " + out_path)