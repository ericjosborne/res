# Codebook: `people_raw.csv`

## About the data

This is a small cross-sectional survey of adults. Each row is meant to be
one respondent, interviewed once. Interviewers entered answers by hand into a
spreadsheet, and not everyone followed the coding rules in this codebook.
**The file has not been cleaned.** Before you analyze it, check every
variable against the definitions below and fix or flag anything that does
not match.

- **File:** `people_raw.csv` (comma-separated, header row, UTF-8)
- **Unit of observation:** one adult respondent
- **Target sample:** 120 respondents, aged 18 and older
- **Reference period:** income questions refer to the previous calendar year

## Missing-value codes

These codes apply to every variable.

| Code | Meaning |
|---|---|
| `-8` | Refused to answer |
| `-9` | Don't know |
| blank | Not recorded |

No other missing-value codes were authorized. In your clean file, store
all missing values as a true missing value (`NA` in R, `.` in Stata,
`NaN` in pandas), not as a number.

## Variables

The file's column headers are listed first. The **clean name** is the
variable name you should use in your cleaned dataset.

### `ID` → clean name `id`
Respondent identifier assigned by the survey office.

- Type: integer
- Valid values: 1–120
- Each respondent has exactly one ID, and each ID belongs to exactly one respondent.

### `Age` → `age`
Age in completed years at the time of the interview.

- Type: integer
- Valid range: 18–90
- Units: years (number only)

### `Sex` → `female`
Respondent's sex.

| Code | Label |
|---|---|
| 1 | Male |
| 2 | Female |

For analysis, recode into a 0/1 indicator `female` (1 = female, 0 = male).

### `Race` → `race`
Respondent's self-identified race/ethnicity (single response).

| Code | Label |
|---|---|
| 1 | White (non-Hispanic) |
| 2 | Black (non-Hispanic) |
| 3 | Asian (non-Hispanic) |
| 4 | Hispanic (any race) |
| 5 | Other / multiple |

### `Marital` → `marital`
Current legal marital status.

| Code | Label |
|---|---|
| 1 | Never married |
| 2 | Married |
| 3 | Divorced or separated |
| 4 | Widowed |

### `Educ` → `educ`
Highest level of education completed.

| Code | Label | Approx. years of schooling |
|---|---|---|
| 1 | Less than high school | 10 |
| 2 | High school diploma or GED | 12 |
| 3 | Some college, no 4-year degree (includes associate's) | 14 |
| 4 | Bachelor's degree | 16 |
| 5 | Master's or professional degree | 18 |
| 6 | Doctorate (PhD, EdD, etc.) | 21 |

Construct `educ_years` from the last column.

### `Income` → `income`
Respondent's own total pre-tax income from all sources in the previous
calendar year.

- Type: numeric
- Units: **whole U.S. dollars** (no `$`, commas, decimals or abbreviations)
- Valid range: 0–1,000,000
- Zero is a valid answer (no income) and is not a missing value.

### `Parents' Income` → `parents_income`
Total pre-tax household income of the respondent's parents when the
respondent was 16, as reported by the respondent, in current dollars.

- Type: numeric
- Units: **whole U.S. dollars**
- Valid range: 0–2,000,000

### `IQ` → `iq`
Score on a short standardized cognitive test given at the end of the
interview, scaled to a population mean of 100 and SD of 15.

- Type: integer
- Valid range: 40–160

## Checks to run

At a minimum, your cleaning should:

1. Rename columns to the clean names above.
2. Find and handle duplicate records and IDs that don't uniquely identify a person.
3. Convert every documented missing-value code to a true missing value.
4. Turn every numeric variable into an actual number. That means removing
   text, symbols and formatting, and putting each variable in the units
   stated above.
5. Recode every categorical variable to the numeric codes in this codebook.
6. Flag values outside the valid range. Decide whether each one can be
   corrected with confidence or should be set to missing, and record your
   reasoning.
7. Check that variables make sense together (for example, age vs. education
   or marital status).
8. Keep a log of every change you make, so someone else can reproduce your
   clean file from the raw file.

Once the data are clean, construct `ln_income = log(income)` for
respondents with positive income.
