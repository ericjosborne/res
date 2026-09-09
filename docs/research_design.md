# Research design memo

## 1. Question

How much does an additional child reduce mothers' labour supply in the United
States today, compared with 1980, and along which margins? Female participation
rose for a century and flattened after 2000 (Figure F1). Over the same period
completed fertility fell, childcare markets and paid-leave policies expanded, and
mothers' attachment to work at the extensive margin rose sharply. The causal
"child penalty" literature (event studies around first births) documents large,
persistent earnings losses, but event studies cannot separate the effect of an
extra child from the timing of the first one. The sibling-sex instrument does.

## 2. Identification

Angrist and Evans (1998, AER) use the sex mix of the first two children as an
instrument for having a third: parents with two children of the same sex are
about 6-7 percentage points more likely to have another. The instrument is
as-good-as-randomly assigned (sex at birth), strong (first-stage F above 1,000 in
1980), and its exclusion restriction (sex mix affects labour supply only through
fertility) is the main threat.

For mother i in year t with first two children of the same sex Z_i:

    morekids_i = pi_t Z_i + X_i gamma_t + v_i                 (first stage)
    y_i        = beta_t morekids_i + X_i delta_t + u_i        (structural)

with X = mother's age, age squared, age at first birth (where available), sex of
the first child, race and ethnicity. beta_t is the LATE for compliers in year t.
We estimate it separately by period and test beta_1980 = beta_2020s in a pooled
model where both the endogenous regressor and the instrument are interacted with
a period dummy (Table T8).

## 3. What the preliminary results establish (details in `preliminary_results.md`)

1. **Exact replication.** With the 1980 Census sample the first stage (0.068),
   the 2SLS effect on employment (-0.120 with the two-instrument specification)
   and on weeks worked (-5.5) match Angrist and Evans' published married-women
   estimates. The estimator is verified against `pyfixest`.
2. **The instrument still works in the 2020s, but is weaker.** In the 2021-23 CPS
   the same-sex first stage is 0.048 (F = 18), versus 0.068 in 1980. The
   difference (0.020, s.e. 0.011) is marginally significant.
3. **The modern LATE is unidentified at this sample size.** With 9,171 mothers the
   minimum detectable effect on P(worked) is 0.73, six times the 1980 effect.
   This is the case for the IPUMS ACS extract: 2005-2023 1-year files contain
   roughly 70,000 mothers per year in the target group, giving a pooled standard
   error near 0.013.
4. **Two boys and two girls do not identify the same parameter in 1980.** The LATE
   for compliers induced by two boys is -0.217 (s.e. 0.047) against -0.063
   (s.e. 0.036) for two girls; the Sargan test rejects (p = 0.008). Either the
   complier populations differ (Mogstad, Torgovitsky and Walters 2021 use exactly
   this example) or the sex composition affects labour supply directly
   (Rosenzweig and Wolpin 2000). This is a substantive finding to develop.
5. **Validity inequalities hold.** The Kitagawa (2015) testable implication of the
   LATE assumptions is satisfied in every bin of the weeks distribution.
6. **Effects are concentrated at the extensive margin and among high-school
   graduates.** The distributional LATE on P(weeks >= k) is flat near -0.13 for
   k up to about 40 and shrinks at full-year work (Figure F2). In the
   Black/Hispanic subsample the employment effect is -0.43 for mothers with
   exactly 12 years of schooling and near zero below and above.

## 4. Contribution relative to the literature (to be verified against the papers; no web access when this memo was written)

* Angrist and Evans (1998) report 1980 and 1990; Bisbee, Dehejia, Pop-Eleches and
  Samii (2017) replicate across 100+ country-years. A United States time series
  through 2023 with a consistent design, margins (extensive, hours, earnings) and
  the decomposition by instrument type appears not to exist.
* The two-instrument heterogeneity connects to Mogstad, Torgovitsky and Walters
  (2021) on 2SLS with multiple instruments and to the son-preference literature
  (Dahl and Moretti 2008; Blau, Kahn, Brummund, Cook and Larson-Koester 2020).
* Complier characterisation (Abadie 2003) shows 1980 compliers are older, more
  likely white, and less likely to be in the bottom income tercile, which frames
  external validity.

## 5. Threats and planned checks

| Threat | Check |
|---|---|
| Exclusion: sex mix affects costs of children (shared rooms, clothes) or parental time directly | Compare two-boys vs two-girls LATEs (done); estimate effects on outcomes that fertility should not move (spouse labour supply of fathers) once IPUMS data are in; bound with Conley-Hansen-Rossi plausibly exogenous |
| Monotonicity across instrument types | Partial-monotonicity tests of Mogstad et al. (2021); report just-identified estimates |
| Sample selection: children must live with the mother | Restrict to mothers 21-35 whose oldest child is under 18 (as AE98); ACS allows checks with fertility questions (FER) |
| CPS proof-of-concept: PolicyEngine renaming, household weights, no parent pointers | 92% exact-count linkage retained (Table `cps_pe_linkage.csv`); replaced by IPUMS pointers (MOMLOC) in the paper |
| Weeks worked intervalled in ACS after 2007 | Use interval midpoints and the binary employment margin as the headline |

## 6. Next steps

1. Run `code/90_ipums_extract.py` with an IPUMS key, then `91_clean_ipums.py`
   and `03_analysis.py` on the full 1980-2023 series.
2. Add fathers' labour supply and household earnings as outcomes.
3. Add the twins-at-second-birth instrument (available in labsup and ACS) as a
   second identification strategy and compare LATEs.
4. Heterogeneity by state childcare cost and paid-leave adoption in the ACS
   years, which turns the design into a test of policy moderators.
5. Draft the paper around Table T8 (period comparison) and Table T5 (instrument-
   specific LATEs).
