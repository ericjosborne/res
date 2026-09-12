# NSCH files for the parental mental-health design

Source: U.S. Census Bureau, National Survey of Children's Health, public-use
microdata: https://www.census.gov/programs-surveys/nsch/data/datasets.html

For each survey year **2016 through 2024** (2024 if released), open the year's
page and download the **Topical** data file (one sampled child per household,
full questionnaire). Take the **Stata** version if offered (`.dta` inside a zip;
Python reads it too), otherwise CSV or SAS. Skip the Screener file.

| Year | File (inside the zip) | Size |
|---|---|---|
| 2016 | `nsch_2016e_topical.dta` (Census names the Stata files with an `e`; the label do-file is `nsch_2016_topical.do`) | ~25 MB |
| 2017 | `nsch_2017e_topical.dta` | ~20 MB |
| 2018 | `nsch_2018e_topical.dta` | ~25 MB |
| 2019 | `nsch_2019e_topical.dta` | ~25 MB |
| 2020 | `nsch_2020e_topical.dta` | ~35 MB |
| 2021 | `nsch_2021e_topical.dta` | ~40 MB |
| 2022 | `nsch_2022e_topical.dta` | ~45 MB |
| 2023 | `nsch_2023e_topical.dta` | ~45 MB |
| 2024 | `nsch_2024e_topical.dta` | ~25 MB |

Also download each year's **codebook / data dictionary** (PDF) from the same
page; the build logs which source variable it used for each concept so a
renamed variable is visible, but the codebook is the authority.

Place the unzipped files in `data/raw/nsch/` (not committed). The nine zips
are attached to the GitHub release `data-nsch` of this repository
(https://github.com/ericjosborne/res/releases/tag/data-nsch); unzip them into
`data/raw/nsch/`. Total is about 190 MB.

## Variables the build uses (names as in the NSCH topical files)

| Concept | Variable(s) | Notes |
|---|---|---|
| State, weight, design | `FIPSST`, `FWC`, `STRATUM`, `HHID` | child weight `FWC` |
| Child age, sex | `SC_AGE_YEARS`, `SC_SEX` | age 0-17 at interview |
| Birth year | `BIRTH_YR`, `BIRTH_MO` (2019-2024 files); survey year minus age before 2019 | exposure at birth. Where both are available, survey year minus age equals the reported birth year for 60% of children and overstates it by one year for 38% |
| Respondent adult (A1) | `A1_RELATION` (1 = biological/adoptive parent), `A1_SEX`, `A1_AGE`, `A1_MARITAL`, `A1_EMPLOYED` (2020-2022) / `A1_EMPLOYED_R` (2023-2024; 1 FT, 2 PT, 3 without pay, 4 looking, 5 not looking, 6 retired), `A1_GRADE` (1-3 up to HS/GED, 4-6 vocational/some college/AA, 7-9 BA+) | identifies mothers and fathers; employment is absent 2016-2019 |
| Adult 1 mental health | `A1_MENTHEALTH` (1 excellent … 5 poor) | primary outcome |
| Adult 1 physical health | `A1_PHYSHEALTH` | placebo channel |
| Second adult (A2) | `A2_RELATION`, `A2_SEX`, `A2_MENTHEALTH`, `A2_PHYSHEALTH` | fathers when A1 is the mother |
| Parenting stress | `K8Q30` (handling demands, 1 very well - 4 not well at all), `K8Q31` (child hard to care for), `K8Q32` (child bothers you), `K8Q34` (angry with child), each 1 never - 5 always | higher = more stress |
| Emotional support | `K8Q35` (someone to turn to, 1 yes 2 no) | |
| Child health | `K2Q01` (general health 1-5), `K4Q20R` (preventive visits past 12 months: 1 none, 2 one, 3 two+) | `K6Q20` is care from others 10+ hours/week, not a visit |
| Breastfeeding (0-5) | `K6Q40` (ever breastfed), `BREASTFEDEND_MO_S`/`_WK_S`/`_DAY_S` (age when stopped), `K6Q41R_STILL` (still breastfeeding) | comparison with PRAMS; there is no `EVERBREASTFED` variable |
| Income | `FPL_I1`…`FPL_I6` (imputed poverty ratio, %), `FAMILY_R` | mean of imputations |
| Race/ethnicity | `SC_RACE_R`, `SC_HISPANIC_R` | child's |
| Insurance | `CURRCOV`, `INSTYPE` | |
