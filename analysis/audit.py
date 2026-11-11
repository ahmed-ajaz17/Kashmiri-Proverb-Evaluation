"""Check every saved answer with the strict answer parser.

  python analysis/audit.py          only report what would change
  python analysis/audit.py --fix    apply the changes to results/mcq_*.csv

An answer counts only if the model clearly states one final letter (A/B/C/D).
Rambling replies with no clear final choice become "no answer" (empty), never a guess.
Run from the repo root. Afterwards re-run the model command: the script redoes
empty answers by itself, then run  python analysis/score.py  again.
"""
import csv
import glob
import sys

sys.path.insert(0, "scripts")
from run_eval import parse_letter  # noqa: E402

fix = "--fix" in sys.argv
total_changed = 0
print(f"{'file':52} {'rows':>5} {'long replies':>13} {'changed':>8}")
for path in sorted(glob.glob("results/mcq_*.csv")):
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    fields = list(rows[0].keys()) if rows else []
    long_n = changed = 0
    for r in rows:
        raw = r["raw_answer"]
        if len(raw.strip()) > 12:
            long_n += 1
        new = parse_letter(raw)
        if new != r["predicted"]:
            changed += 1
            if fix:
                r["predicted"] = new
                r["is_correct"] = int(new == r["correct"])
    total_changed += changed
    print(f"{path[8:]:52} {len(rows):>5} {long_n:>13} {changed:>8}")
    if fix and changed:
        with open(path, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(rows)
print("\n" + ("Changes applied." if fix else "Nothing changed yet. Add --fix to apply.")
      + f"  Rows affected: {total_changed}")
