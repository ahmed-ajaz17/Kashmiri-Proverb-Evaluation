"""Check saved answers against the strict answer parser.

  python analysis/audit.py          report only
  python analysis/audit.py --fix    blank only the rows that are provably wrong

Each row is in one of three groups:
  ok            stored letter = what the parser finds in the saved reply
  unverifiable  the saved reply is cut short (first 300 characters only), so the final
                answer may be hidden. The letter was set when the full reply was parsed.
                These are NOT changed. Check their accuracy: a model that really answered
                should score well above 25% and use all four letters.
  mismatch      the saved reply is complete but disagrees with the stored letter (a real
                problem). --fix blanks these so run_eval.py redoes them.
"""
import collections
import csv
import glob
import sys

sys.path.insert(0, "scripts")
from run_eval import parse_letter  # noqa: E402

fix = "--fix" in sys.argv
print(f"{'file':50} {'rows':>4} {'ok':>4} {'unverif.':>8} {'acc(unv)':>8} {'A share':>7} {'mismatch':>8}")
bad_total = 0
for path in sorted(glob.glob("results/mcq_*.csv")):
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        continue
    fields = list(rows[0].keys())
    ok = mism = 0
    unv = []
    for r in rows:
        raw = r["raw_answer"]
        cut = len(raw) >= 300 or "[...]" in raw
        new = parse_letter(raw)
        if new == r["predicted"]:
            ok += 1
        elif cut:
            if r["predicted"]:
                unv.append(r)
            else:
                ok += 1                      # blank stays blank
        else:
            mism += 1
            if fix:
                r["predicted"] = new
                r["is_correct"] = int(new == r["correct"])
    bad_total += mism
    acc = (100 * sum(int(x["is_correct"]) for x in unv) / len(unv)) if unv else 0
    ash = (100 * sum(1 for x in unv if x["predicted"] == "A") / len(unv)) if unv else 0
    print(f"{path[8:]:50} {len(rows):>4} {ok:>4} {len(unv):>8} {acc:>7.0f}% {ash:>6.0f}% {mism:>8}")
    if fix and mism:
        with open(path, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(rows)
print("\nReal mismatches:", bad_total, "(applied)" if fix else "(add --fix to apply)")
print("Unverifiable rows are left as they are. Healthy sign: accuracy well above 25% and "
      "'A share' near 25-40%.")
