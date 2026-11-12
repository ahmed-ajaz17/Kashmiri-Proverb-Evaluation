"""Summarise MCQ results: accuracy per model and script, with a 95% interval.

Run from the repo root:
  python analysis/score.py              count every clear answer (follow-up answers included)
  python analysis/score.py --no-rescue  first reply only: answers that needed a follow-up count as no answer
Writes results/summary_mcq.csv and prints a table.
"""
import csv
import glob
import math
from collections import defaultdict

CHANCE = 25.0
NO_RESCUE = "--no-rescue" in __import__("sys").argv
rows = defaultdict(lambda: [0, 0, 0, 0])  # (model, mode) -> [correct, total, unparsed, rescued]
for path in sorted(glob.glob("results/mcq_*.csv")):
    with open(path, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            k = (r["model"], r["mode"])
            resc = r["raw_answer"].startswith("[rescued]")
            drop = NO_RESCUE and resc
            rows[k][0] += 0 if drop else int(r["is_correct"])
            rows[k][1] += 1
            rows[k][2] += int(r["predicted"] == "" or drop)
            rows[k][3] += int(resc)

if not rows:
    raise SystemExit("No results/mcq_*.csv files found. Run from the repo root.")

out = []
print(f"{'model':32} {'script':9} {'correct':>9} {'accuracy':>9} {'95% CI':>15} {'no answer':>10} {'rescued':>8}")
for (model, mode), (c, n, u, rs) in sorted(rows.items()):
    p = c / n
    # Wilson 95% interval
    z = 1.96
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    lo, hi = 100 * (centre - half), 100 * (centre + half)
    print(f"{model:32} {mode:9} {c:>4}/{n:<4} {100*p:8.1f}% {lo:6.1f}-{hi:5.1f}% {u:>10} {rs:>8}")
    out.append({"model": model, "script": mode, "correct": c, "total": n,
                "accuracy_pct": round(100 * p, 1), "ci_low": round(lo, 1),
                "ci_high": round(hi, 1), "unparsed": u, "rescued": rs})
print(f"\nRandom guessing = {CHANCE:.0f}%")
if NO_RESCUE:
    print("First reply only: follow-up answers are counted as no answer.")

with open("results/summary_mcq.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0]))
    w.writeheader()
    w.writerows(out)
print("Saved results/summary_mcq.csv")
