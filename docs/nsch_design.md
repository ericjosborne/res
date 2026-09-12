# Paid family leave and parents' mental health beyond the leave: NSCH design

## 1. Question and contribution

Wells et al. (2026, AJE) show with PRAMS and Callaway-Sant'Anna that state
paid family leave lowers postpartum depressive symptoms by about one point,
measured two to six months after birth, in six states through 2021. Whether
that gain outlasts the leave, whether fathers share in it, and whether it
reaches the second-generation programmes (Massachusetts 2021, Connecticut
2022, Oregon 2023, Colorado 2024) is unknown. The National Survey of
Children's Health asks the responding parent's own mental health for a
sampled child of any age, so exposure can be defined at the child's birth and
the parent observed one to five years later. Companion results from this
repository: no labour-supply or fertility response in the CPS.

## 2. Design: exposure at birth, birth-cohort event study

Unit: sampled child (one per household), survey years 2016-2024. Treatment:
the child was born in a state-year with PFML benefits available. Time index
for the estimator: the child's birth year; cohort: the state's first birth
year with at least six months of benefits. ATT(g, b) compares parents of
children born in year b in cohort-g states with parents of children born in
year b in never-treated states, each relative to births in year g-1. Because
children of several ages are observed in each survey year, the design has
within-state variation across birth cohorts at a fixed survey date, which
PRAMS lacks; the event study in years since the cohort's first treated
birth year is the headline.

Two ways to hold the survey date fixed: (i) run within child-age bands (0-1,
2-3, 4-5), so birth year and survey year move together and the estimate is a
comparison across survey years as in PRAMS; (ii) pool ages and include survey
year and child age as covariates in the doubly-robust step (`csdid`
`drimp`). Report both; (i) is the cleaner one.

Samples: respondent is the child's mother (main), father (secondary),
children aged 0-5 (main) and 0-1 (closest to PRAMS). Placebo: parents of
children aged 6-17 born before any policy in their state but observed after
it, who are exposed to the state's post-policy environment but not to leave
at birth; a within-state contemporaneous effect on them would indicate a
state shock rather than a leave effect.

## 3. Outcomes

* Mother's mental health, 1-5 (excellent to poor); indicators for fair/poor
  and for excellent; mean score.
* Mother's physical health (channel check).
* Parenting stress items (handling demands; child hard to care for;
  bothered; angry) and emotional support.
* Father's mental health when the father is the respondent or the second
  adult.
* Child: general health, preventive visit, ever breastfed and duration
  (0-5), for comparison with PRAMS.
* Employment of the responding parent (replication of the CPS null).

## 4. Data

`data/raw/NSCH_SPEC.md`: nine topical files, about 30,000-55,000 children a
year, of which roughly one third are aged 0-5. State identifiers and child
weights are public. Birth year is survey year minus age in years; the
June-January field period makes the birth-year assignment uncertain by about
half a year for a share of children, which argues for the six-month cohort
rule and a robustness run dropping the boundary birth year.

## 5. Threats

| Threat | Response |
|---|---|
| Thin pre-period for New York (2016-2017 surveys, births from 2011 on for 5-year-olds) | births observed retrospectively extend the pre-period: 2016 survey covers births 2011-2016 |
| Mental health is a single self-rated item | show all categories; fair/poor and excellent margins; parenting-stress index as a second measure |
| Respondent selection (who answers) | condition on respondent relation; run the second-adult outcome |
| Pandemic (2020-2021 surveys) | drop; survey-year covariate; placebo group |
| Migration since birth | NSCH has no state-of-birth; treat as attenuation, note ACS check |
| Few treated clusters | wild cluster bootstrap in Stata; randomisation inference over placebo cohorts |

## 6. Files

`python/20_build_nsch.py` (build, logs the variable mapping per year),
`stata/20_build_nsch.do`, `stata/21_csdid_nsch.do`, and
`python/02_csdid.py --data nsch` once the file exists.
