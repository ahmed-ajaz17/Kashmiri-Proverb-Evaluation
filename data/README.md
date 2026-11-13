# Data

## `kashmiri_proverbs.csv`

120 Kashmiri proverbs from J. Hinton Knowles, *A Dictionary of Kashmiri Proverbs and Sayings* (Bombay, 1885), which is in the public domain.

| Column | Description |
|---|---|
| `id` | Proverb number in this dataset |
| `proverb_nastaliq` | The proverb in Nastaliq script |
| `transliteration` | Roman transliteration with diacritics, adapted from Knowles's romanization |
| `english_translation` | Literal English translation |
| `meaning_english` | English meaning and idiomatic context |
| `source` | Source work |
| `page` | Page in the source |

## `mcq_test_set.csv`

The four-option multiple-choice test built from the dataset. The three wrong options are the meanings of other proverbs, chosen with a fixed random seed (42). Random baseline: 25%.

| Column | Description |
|---|---|
| `id` | Proverb number |
| `proverb_nastaliq` | Proverb in Nastaliq |
| `transliteration` | Proverb in Roman transliteration |
| `option_a` to `option_d` | The four answer options |
| `correct_letter` | The correct option (A, B, C or D) |

## Notes

- The Nastaliq text, English meanings and idiomatic context were prepared by one person and have not been independently reviewed. Corrections are welcome.
- Licence: CC BY 4.0. Please also cite Knowles (1885).
- Archive: https://doi.org/10.5281/zenodo.24169347
