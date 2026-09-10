# Research design: state paid family and medical leave and mothers' labour supply

## 1. Question

Nine states and DC now pay wage-replacement benefits to parents of newborns
and, in most cases, to workers caring for family members: California (2004),
New Jersey (2009), Rhode Island (2014), New York (2018), Washington and DC
(2020), Massachusetts (2021), Connecticut (2022), Oregon (2023), Colorado
(2024), with Delaware, Minnesota (2026) and Maryland to follow. The programmes
differ in duration (4 to 20 weeks), replacement rates (50 to 95 percent) and job
protection. The question is whether paid leave raises mothers' labour force
attachment, on which margin (participation, employment, hours, full-time), for
whom (mothers of infants, of pre-schoolers, by education and marital status),
and whether the second-generation programmes, which are more generous than
California's, have larger effects.

The existing evidence rests mostly on California and New Jersey and disagrees:
short-run increases in leave-taking and employment continuity around births
(Rossin-Slater, Ruhm and Waldfogel 2013; Baum and Ruhm 2016), versus lower
employment and earnings six to ten years later for first-time mothers
(Bailey, Byker, Patel and Ramnath 2019). A design that uses every cohort with
a common estimator, separates cohorts, and measures the response month by
month is the contribution. (Citations from memory; verify before use.)

## 2. Identification: staggered adoption, Callaway and Sant'Anna (2021)

Treatment is the availability of PFML benefits in the mother's state of
residence, timed to the month benefits became payable. Cohorts are defined by
that month (or, in the yearly specification, by the first calendar year with at
least six months of benefits). Two-way fixed effects with a single treatment
dummy are biased with staggered adoption and dynamic effects, since already-
treated cohorts serve as controls for later ones (Goodman-Bacon 2021). We
therefore estimate group-time average treatment effects

    ATT(g, t) = E[Y_t − Y_{g−1} | G = g] − E[Y_t − Y_{g−1} | C]

with C the never-treated states (main) or the not-yet-treated states
(robustness), and aggregate them to event-time, cohort and calendar-time
effects with cohort-size weights. Estimation is doubly robust (`csdid`,
`method(drimp)`) with covariates age group, marital status, race and
ethnicity, and education, on repeated cross sections of the CPS; inference uses
a wild bootstrap clustered by state.

Comparison groups within states matter because state shocks (the pandemic,
minimum wage increases, Medicaid expansion) hit all women. We estimate the same
event studies for women without children as a placebo and estimate a triple
difference (mothers of under-6s minus childless women) as the preferred
specification when the placebo shows movement.

## 3. Data

* **Paper (in hand):** IPUMS-CPS ASEC extract `cps_00090`, survey years
  1990-2025, women aged 18-44: 1,216,812 person-years, about 10,500 mothers of
  under-6s per reference year. Variables: worked / weeks / hours last year,
  March labour-force status, presence and age of own children (NCHILD, YNGCH,
  NCHLT5), demographics, state, ASEC weights. Builds:
  `python/01_build_ipums_asec.py`, `stata/01_build_cps_asec.do`.
  A basic-monthly extract (optional, `01_build_cps_monthly.do`) would add
  month-level timing.
* **Policy panel:** `data/raw/pfml_policy_dates.csv`, enactment,
  contribution and benefit start dates for every programme, compiled without
  web access and to be verified against the Department of Labor summary and
  state statutes.

## 4. Specification for the paper

1. Sample: women 18-44 with an own child under 6 (main); under 1; all mothers;
   childless women (placebo).
2. Outcomes: in labour force, employed, at work, usual hours (zero for
   non-workers), full time; earnings in the ORG subsample.
3. Cohorts: benefit-start month; window −24 to +24 months for the monthly
   event study, −6 to +6 years for the yearly.
4. `csdid` with never-treated controls, drimp, covariates, state-clustered
   wild bootstrap; `estat event`, `estat group`, `estat calendar`,
   `estat pretrend`.
5. Robustness: not-yet-treated controls; triple difference; alternative cohort
   timing (first full benefit year); Sun and Abraham; Borusyak, Jaravel and
   Spiess imputation; de Chaisemartin and D'Haultfoeuille; Rambachan and Roth
   sensitivity on the event-study coefficients; TWFE for reference.
6. Heterogeneity: cohort generation (CA/NJ/RI vs 2018 and later), programme
   generosity (weeks times replacement rate), job protection, education,
   marital status, state minimum wage and Medicaid status as moderators.

## 5. Threats

| Threat | Response |
|---|---|
| State-specific shocks coincide with adoption (COVID in 2020-22 for WA, DC, MA, CT) | Placebo on childless women; triple difference; calendar-time aggregation; drop 2020-21 in a robustness run |
| Anticipation from enactment to benefits (1-3 years) | Set anticipation periods in `csdid`; event study relative to enactment |
| Few treated clusters for inference | Wild cluster bootstrap; randomisation inference over placebo adoption dates; report cohort-specific estimates |
| Composition: who becomes a mother changes with leave policy | Condition on age at first birth; fertility as an outcome |
| Contamination by earlier state programmes (TDI in CA/NJ/RI/NY) | Cohort-specific effects; early vs late generation comparison |

## 6. Status

The full-window estimation on the IPUMS-CPS ASEC extract is done in Python
(`results.md`); the Stata pipeline reproduces it with covariates and the
wild cluster bootstrap and adds the robustness set.
