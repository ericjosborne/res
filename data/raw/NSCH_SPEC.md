# NSCH files for the parental mental-health design

Source: U.S. Census Bureau, National Survey of Children's Health, public-use
microdata: https://www.census.gov/programs-surveys/nsch/data/datasets.html

For each survey year **2016 through 2024** (2024 if released), open the year's
page and download the **Topical** data file (one sampled child per household,
full questionnaire). Take the **Stata** version if offered (`.dta` inside a zip;
Python reads it too), otherwise CSV or SAS. Skip the Screener file.

| Year | File (inside the zip) | Size |
|---|---|---|
| 2016 | `nsch_2016_topical.dta` | ~25 MB |
| 2017 | `nsch_2017_topical.dta` | ~20 MB |
| 2018 | `nsch_2018_topical.dta` | ~25 MB |
| 2019 | `nsch_2019_topical.dta` | ~25 MB |
| 2020 | `nsch_2020_topical.dta` | ~35 MB |
| 2021 | `nsch_2021_topical.dta` | ~40 MB |
| 2022 | `nsch_2022_topical.dta` | ~45 MB |
| 2023 | `nsch_2023_topical.dta` | ~45 MB |
| 2024 | `nsch_2024_topical.dta` | if available |

Also download each year's **codebook / data dictionary** (PDF) from the same
page; the build logs which source variable it used for each concept so a
renamed variable is visible, but the codebook is the authority.

Place the unzipped files in `data/raw/nsch/` (not committed) or attach them
to a release tagged `data-nsch`. Total is under 400 MB.

## Variables the build uses (names as in the NSCH topical files)

| Concept | Variable(s) | Notes |
|---|---|---|
| State, weight, design | `FIPSST`, `FWC`, `STRATUM`, `HHID` | child weight `FWC` |
| Child age, sex | `SC_AGE_YEARS`, `SC_SEX` | age 0-17 at interview |
| Birth year | derived: survey year minus age, adjusted for the June-January field period | exposure at birth |
| Respondent adult (A1) | `A1_RELATION` (1 = biological/adoptive parent), `A1_SEX`, `A1_AGE`, `A1_MARITAL`, `A1_EMPLOYED`, `A1_GRADE` | identifies mothers and fathers |
| Adult 1 mental health | `A1_MENTHEALTH` (1 excellent … 5 poor) | primary outcome |
| Adult 1 physical health | `A1_PHYSHEALTH` | placebo channel |
| Second adult (A2) | `A2_RELATION`, `A2_SEX`, `A2_MENTHEALTH`, `A2_PHYSHEALTH` | fathers when A1 is the mother |
| Parenting stress | `K8Q30` (handling demands of parenting), `K8Q31` (child hard to care for), `K8Q32`, `K8Q34` | 1-4 scales |
| Emotional support | `K8Q35` (someone to turn to) | |
| Child health | `K2Q01` (general health), `K6Q20` (preventive visit) | |
| Breastfeeding (0-5) | `EVERBREASTFED`, `BREASTFEDEND_MO_S`, `BREASTFEDEND_WK_S` | comparison with PRAMS |
| Income | `FPL_I1`…`FPL_I6` (imputed poverty ratio, %), `FAMILY_R` | mean of imputations |
| Race/ethnicity | `SC_RACE_R`, `SC_HISPANIC_R` | child's |
| Insurance | `CURRCOV`, `INSTYPE` | |
