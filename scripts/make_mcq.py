"""Build a multiple-choice test set from data/kashmiri_proverbs.csv.

For each proverb, the correct answer is its own meaning_english and the three
distractors are meanings of other randomly chosen proverbs.
"""
import csv
import random

SEED = 42
INPUT = "data/kashmiri_proverbs.csv"
OUTPUT = "data/mcq_test_set.csv"

random.seed(SEED)

with open(INPUT, encoding="utf-8-sig", newline="") as f:
    rows = list(csv.DictReader(f))

if len(rows) < 4:
    raise SystemExit("Need at least 4 proverbs to build 4-option questions.")

letters = ["A", "B", "C", "D"]
fieldnames = [
    "id", "proverb_nastaliq", "transliteration",
    "option_a", "option_b", "option_c", "option_d", "correct_letter",
]

with open(OUTPUT, "w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        correct = row["meaning_english"]
        others = [r["meaning_english"] for r in rows
                  if r["id"] != row["id"] and r["meaning_english"] != correct]
        options = random.sample(others, 3) + [correct]
        random.shuffle(options)
        writer.writerow({
            "id": row["id"],
            "proverb_nastaliq": row["proverb_nastaliq"],
            "transliteration": row["transliteration"],
            "option_a": options[0],
            "option_b": options[1],
            "option_c": options[2],
            "option_d": options[3],
            "correct_letter": letters[options.index(correct)],
        })

print(f"Wrote {len(rows)} questions to {OUTPUT}")
