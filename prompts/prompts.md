# Prompts

Use these exactly as written for every model. Start a fresh chat for each item
(or each batch, if you test several in one message) so earlier answers do not leak.
Replace the `{...}` placeholders with values from the CSV.

## Task 1: Multiple choice (Nastaliq)

```
The following is a Kashmiri proverb written in Nastaliq script:

{proverb_nastaliq}

Which of the following is the correct meaning of this proverb?

A) {option_a}
B) {option_b}
C) {option_c}
D) {option_d}

Answer with only the letter (A, B, C, or D).
```

## Task 1b: Multiple choice (Roman transliteration, optional extra condition)

```
The following is a Kashmiri proverb written in Roman script:

{transliteration}

Which of the following is the correct meaning of this proverb?

A) {option_a}
B) {option_b}
C) {option_c}
D) {option_d}

Answer with only the letter (A, B, C, or D).
```

## Task 2: Open-ended explanation (Nastaliq)

```
The following is a Kashmiri proverb written in Nastaliq script:

{proverb_nastaliq}

Explain the meaning of this proverb in one or two sentences in English.
```

## Scoring rubric for Task 2

- **Correct (1):** captures the core meaning in the CSV `meaning_english` column
- **Partial (0.5):** right general theme but misses or distorts the key point
- **Wrong (0):** unrelated, refuses, or only translates words literally with no meaning

Have a second Kashmiri speaker score a random 20% of answers, then report
agreement between the two of you in the paper.

## Models and settings log

Record here, for each run: model name, version/date, interface (web or API),
and temperature if known.
