"""Rebuild result files that lost rows, from older copies.

  python analysis/restore.py ../results_backup [more_folders ...]

For every file name found in results/ or in the given folders, the rows are
merged by question id. Priority for each id:
  1. the current results/ row, if it has a clear answer
  2. an older row (re-checked with the strict parser), if it has a clear answer
  3. otherwise a blank row, which run_eval.py will redo
Nothing is deleted from older copies. Run from the repo root, then:
  python analysis/score.py
"""
import csv
import glob
import os
import sys

sys.path.insert(0, "scripts")
from run_eval import parse_letter  # noqa: E402

FIELDS = ["id", "mode", "model", "predicted", "correct", "is_correct", "raw_answer"]


def read(path):
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8-sig", newline="") as f:
        return {r["id"]: r for r in csv.DictReader(f)}


folders = sys.argv[1:]
if not folders:
    raise SystemExit("Give at least one older folder, e.g.  python analysis/restore.py ../results_backup")

names = set(os.path.basename(p) for p in glob.glob("results/mcq_*.csv"))
for d in folders:
    names |= set(os.path.basename(p) for p in glob.glob(os.path.join(d, "mcq_*.csv")))

os.makedirs("results", exist_ok=True)
for name in sorted(names):
    current = read(os.path.join("results", name))
    old = {}
    for d in folders:                                   # earlier folders win
        for i, r in read(os.path.join(d, name)).items():
            old.setdefault(i, [])
            old[i].append(r)
    merged = {}
    for i in set(current) | set(old):
        cur = current.get(i)
        if cur and cur["predicted"] != "" and cur["raw_answer"] != "ERROR":
            merged[i] = cur
            continue
        pick = None
        for r in old.get(i, []):
            p = parse_letter(r["raw_answer"])
            if p:
                pick = dict(r, predicted=p, is_correct=int(p == r["correct"]))
                break
        if pick is None:
            base = cur or (old[i][0] if i in old else None)
            pick = dict(base, predicted="", is_correct=0)
        merged[i] = pick
    rows = [merged[i] for i in sorted(merged, key=int)]
    had = len(current)
    with open(os.path.join("results", name), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r[k] for k in FIELDS})
    clear = sum(1 for r in rows if r["predicted"] != "")
    print(f"{name:52} before={had:>3}  now={len(rows):>3}  with clear answer={clear:>3}")
print("\nDone. Run: python analysis/score.py")
