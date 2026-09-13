# Paid family leave and maternal mental health: design memo

## 1. Question and contribution

Does state paid family and medical leave improve mothers' mental health, and
does it do so without changing their labour supply? Bullinger (2019, Journal
of Health Economics; verify) found that California's 2004 programme reduced
days of poor mental health among mothers in the BRFSS, using one treated
state. Since then eight more states and DC have adopted programmes with
longer leave and higher replacement rates. This paper estimates the effect
across all nine cohorts with Callaway and Sant'Anna (2021), separating cohorts
and horizons, with the CPS labour-supply and fertility results of this
repository as the companion finding: the welfare gain from paid leave, if it
exists, is a health gain rather than a labour-market gain.

## 2. Data

BRFSS 1993-2024, adults 18-44 (`python/10_build_brfss.py`,
`stata/10_build_brfss.do`; spec in `data/raw/BRFSS_SPEC.md`). About 40,000
women with children in the household per year, four times the CPS sample.

Outcomes, all from the core questionnaire in every year:
* `mentdays`: "for how many days during the past 30 days was your mental
  health not good" (0-30), the Bullinger outcome;
* `fmd`: frequent mental distress, 14 or more days, the CDC's standard
  cutoff;
* `fairpoor`: general health fair or poor; `physdays`, `poordays`: physical
  health and activity-limitation days, which test whether the channel is
  mental rather than physical health;
* `employed`, `unable_work`: a within-survey replication of the CPS
  labour-supply null.

Samples: women 18-44 with children in the household (main); women 18-34 with
children (closer to recent births); pregnant women (from 1997, women 18-44);
placebos: childless women, childless men. Fathers are covered by PFML and are
a secondary treated group, not a placebo.

Treatment: state PFML cohorts from `data/raw/pfml_policy_dates.csv`; annual
cohort = first calendar year with at least six months of benefits
(interview year is the outcome year in BRFSS), and a monthly cohort from the
interview month for a 24-month event study.

## 3. Estimation

Identical to the CPS design: group-time ATTs with never-treated controls
(not-yet-treated as robustness), aggregated to event time, cohort and
calendar time; `csdid` with doubly-robust adjustment for age group, marital
status, race/ethnicity and education, wild cluster bootstrap by state; in
Python, `python/02_csdid.py --data brfss` with the state block bootstrap.

Robustness specific to BRFSS: drop survey years 2010-2011 around the
cell-phone and raking redesign; monthly cohorts; mothers 18-34; pregnant
women; landline-only subsample before and after 2011 for comparability.

## 4. What would count as a result

Bullinger's estimate (from memory) was on the order of half a day fewer of
poor mental health per month for mothers, about 10-15 percent of the mean.
With 40,000 mothers a year and a standard deviation near 8 days, the
state-clustered standard error on the pooled simple ATT should be around
0.15-0.25 days, so effects of that size are detectable, and the event study
can show whether they fade or persist. Frequent mental distress (mean about
13 percent) gives a second margin. A null here, with flat placebos, would
itself contradict the single-state finding and be reportable; but the
prior is a modest improvement, larger for the second-generation programmes.

## 5. Heterogeneity

Income (`inc_lt25k`, household income below $25,000), marital status,
race/ethnicity, education, and cohort generation; and mothers versus fathers,
since fathers' leave-taking is where the newer programmes differ most from
California's.

## 6. Steps

1. Download the 32 BRFSS transport files (`data/raw/BRFSS_SPEC.md`), upload
   them as release assets or run the build locally and upload the output.
2. `python python/10_build_brfss.py`, then
   `python python/02_csdid.py --data brfss --sample mothers --outcome mentdays`
   and the placebo and robustness runs (a driver script will follow the
   first look at the data).
3. `do stata/11_csdid_brfss.do` for the covariate-adjusted estimates and
   tables.
