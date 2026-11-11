"""Draw the MCQ results chart from results/summary_mcq.csv.

Run from the repo root (after python analysis/score.py):
  pip install matplotlib      # once, if it is not installed
  python analysis/plot.py
Writes results/figure_mcq.png and results/figure_mcq.pdf
"""
import csv

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

NASTALIQ, ROMAN = "#2a78d6", "#eb6834"      # blue, orange
INK, MUTED, GRID, SURFACE = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"

rows = list(csv.DictReader(open("results/summary_mcq.csv", encoding="utf-8")))
models = {}
for r in rows:
    models.setdefault(r["model"], {})[r["script"]] = r
order = sorted(models, key=lambda m: models[m].get("nastaliq", {}).get("accuracy_pct", 0) and
               float(models[m]["nastaliq"]["accuracy_pct"]))
labels = [m.split("/")[-1] for m in order]

fig, ax = plt.subplots(figsize=(8, 0.9 * len(order) + 1.8), facecolor=SURFACE)
ax.set_facecolor(SURFACE)
h, gap = 0.34, 0.02
for i, m in enumerate(order):
    for j, (script, colour) in enumerate((("nastaliq", NASTALIQ), ("roman", ROMAN))):
        r = models[m].get(script)
        if not r:
            continue
        y = i + (0.5 - j) * (h + gap)
        v, lo, hi = float(r["accuracy_pct"]), float(r["ci_low"]), float(r["ci_high"])
        ax.barh(y, v, height=h, color=colour, zorder=3)
        ax.errorbar(v, y, xerr=[[v - lo], [hi - v]], color=INK, capsize=2.5,
                    lw=1, capthick=1, zorder=4)
        ax.text(hi + 1.2, y, f"{v:.0f}%", va="center", fontsize=9, color=INK)

ax.axvline(25, color=MUTED, ls="--", lw=1, zorder=2)
ax.text(25.8, len(order) - 0.45, "random guessing (25%)", fontsize=8.5, color=MUTED, va="bottom")
ax.set_yticks(range(len(order)))
ax.set_yticklabels(labels, fontsize=10, color=INK)
ax.set_xlim(0, 108)
ax.set_xlabel("Accuracy on 120 proverbs (%), bars show 95% interval", fontsize=9.5, color=MUTED)
ax.xaxis.grid(True, color=GRID, lw=0.8, zorder=0)
ax.set_axisbelow(True)
for s in ("top", "right", "left"):
    ax.spines[s].set_visible(False)
ax.spines["bottom"].set_color(GRID)
ax.tick_params(axis="both", length=0, colors=MUTED)
ax.set_title("Kashmiri proverb meaning (multiple choice)", loc="left", fontsize=12,
             color=INK, pad=26)
ax.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=NASTALIQ), plt.Rectangle((0, 0), 1, 1, color=ROMAN)],
          labels=["Nastaliq script", "Roman transliteration"], loc="lower left",
          bbox_to_anchor=(0, 1.0), ncol=2, frameon=False, fontsize=9.5, labelcolor=INK)
fig.tight_layout()
fig.savefig("results/figure_mcq.png", dpi=200, facecolor=SURFACE)
fig.savefig("results/figure_mcq.pdf", facecolor=SURFACE)
print("Saved results/figure_mcq.png and results/figure_mcq.pdf")
