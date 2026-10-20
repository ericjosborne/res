# Instructor materials (do not distribute)

- `people_clean.csv` is the answer key: the true values for the 120
  respondents, before any errors were added. It uses text labels rather than
  the codebook's numeric codes and the original column names.
- `injected_errors.csv` lists every error added to `../people_raw.csv`,
  one row per problem: respondent id, variable, true value, raw value and
  what went wrong.
- `make_raw.py` rebuilds `people_raw.csv` and `injected_errors.csv` from the
  answer key (`python make_raw.py`, run from this folder). It uses a fixed
  random seed, so it gives the same output every time.

## Types of errors in the raw file

| Problem | Count | Expected handling |
|---|---|---|
| Categorical entered as text instead of a code (`M`, `Married`, `BA`, `Latino`, …) | 53 | Recode to the numeric code |
| Missing coded `-8`, `-9` or left blank | 21 | Set to missing |
| Income formatted as `$52,300`, `52300.00` or `52.3k` | 25 | Strip the formatting, convert to dollars |
| Parents' income entered in thousands (e.g. `183`) | 8 | Multiply by 1,000 (values below ~1,000 are not plausible) |
| Age with `yrs` text | 3 | Remove the text |
| Out-of-range typos: age ×10, age with a digit dropped, age 999, IQ 999, IQ 0, IQ with a digit dropped or added, negative income, income with an extra zero | 9 | Set to missing, or fix if the true value is obvious (e.g. remove the minus sign); students should justify their choice |
| Doctorate at age 23, widowed at age 22 | 2 | Flag. The doctorate is very likely an error; the widow is unusual but possible |
| Exact duplicate rows | 4 | Drop the copies (raw file has 124 rows; the clean file should have 120) |
| ID collision: two different people share an ID | 1 | ID 23 was typed as 32, so 32 appears twice and 23 is missing. Students can spot the gap, but should flag it rather than guess |

Some problems are deliberately hard to settle from the codebook alone,
especially the income with an extra zero, which can still fall inside the
valid range. These are good for discussing how much a researcher should
"fix" data versus set it to missing.
