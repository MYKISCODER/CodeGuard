"""
Generate cross-model comparison bar chart for Figure 3 (right panel).
Shows ASR and FBR for 6 models, highlighting that strong models all achieve 0% ASR.
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

# Data from cross-model validation (SR60v2, STRICT-EXEMPT)
models = ['GPT-4o', 'Claude\n3.5 Son.', 'DS-V3', 'GPT-4.1\nmini', 'GPT-4o\nmini', 'Gemini\n2.0 Flash']
asr =    [0.0,      0.0,              0.0,     10.0,          6.7,           23.3]
fbr =    [6.7,      13.3,             40.0,    20.0,          40.0,          0.0]

fig, ax = plt.subplots(figsize=(4.2, 3.2))

x = np.arange(len(models))
width = 0.35

bars_asr = ax.bar(x - width/2, asr, width, label='ASR (%)', color='#d62728', alpha=0.85, edgecolor='white', linewidth=0.5)
bars_fbr = ax.bar(x + width/2, fbr, width, label='FBR (%)', color='#1f77b4', alpha=0.85, edgecolor='white', linewidth=0.5)

# Add a horizontal dashed line at 0% for reference
ax.axhline(y=0, color='gray', linewidth=0.5)

# Highlight strong models region
ax.axvspan(-0.5, 2.5, alpha=0.06, color='green')
ax.text(1.0, 42, 'Strong models\n(ASR = 0%)', ha='center', va='bottom', fontsize=7,
        color='green', fontstyle='italic', fontweight='bold')

ax.set_ylabel('Rate (%)', fontsize=9)
ax.set_xticks(x)
ax.set_xticklabels(models, fontsize=7)
ax.set_ylim(0, 52)
ax.legend(fontsize=6, loc='upper right', borderpad=0.2, labelspacing=0.2, handlelength=1.0,
          bbox_to_anchor=(1.0, 1.0))
ax.set_title('Cross-Model Validation (SR60v2)', fontsize=9, fontweight='bold')

# Add value labels on bars
for bar in bars_asr:
    h = bar.get_height()
    if h > 0:
        ax.text(bar.get_x() + bar.get_width()/2., h + 0.8, f'{h:.1f}',
                ha='center', va='bottom', fontsize=6.5)

for bar in bars_fbr:
    h = bar.get_height()
    if h > 0:
        ax.text(bar.get_x() + bar.get_width()/2., h + 0.8, f'{h:.1f}',
                ha='center', va='bottom', fontsize=6.5)

ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

plt.tight_layout()
plt.savefig('D:/paper/论文写作助手/论文写作助手/正文/fig_crossmodel.pdf', bbox_inches='tight', dpi=300)
print("Saved fig_crossmodel.pdf")
