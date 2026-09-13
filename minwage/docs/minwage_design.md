# Minimum wage increases and teen school enrollment: design

## 1. Question

Does a large increase in the state minimum wage change whether 16-19 year
olds stay in school, and how they combine school and work? A higher wage
raises the opportunity cost of school, which lowers enrollment; if the
increase removes teen jobs instead, enrollment can rise. The older evidence
(Neumark and Wascher 1995, 2003; Chaplin, Turner and Pape 2003; Warren and
Hamrock 2010) disagrees on the sign, ends before the $12-$15 schedules of
2014-2025, and uses two-way fixed effects regressions of state-year shares on
the log minimum wage (most recently Neumark and Shupe 2019, Labour
Economics, CPS March 1986-2015). None of it uses the event designs the
minimum wage employment literature adopted after Cengiz, Dube, Lindner and
Zipperer (2019).

## 2. Design: stacked events with clean controls

Events (`python/31_build_mw_events.py`): a month in which a state's
effective minimum (the larger of state and federal) rises by at least 5
percent because of state law, with no such rise in the state in the
preceding 36 months. Later rises in the following 48 months belong to the
same event, so a multi-year schedule is one event whose dose is the
cumulative rise over the window. Federal-induced rises in floor states are
not events. Controls for an event: states with no state-driven qualifying
rise in the window from 36 months before to 47 months after ("clean"); a
stricter set also excludes states hit by a federal increase in the window.

The comparison for each event is the Callaway-Sant'Anna one: the treated
state's outcome in relative year k minus its outcome in the year before the
event, less the same change in the pooled clean controls, for k = -3, -2
(pre) and 0, 1, 2, 3 (post). Events are aggregated with weights equal to the
treated state's teen population (equal weights as a check). Inference: block
bootstrap over states, treated and control alike, 199 draws; in Stata,
`csdid` on the stacked file with the wild cluster bootstrap and the
Cengiz et al. stacked regression with event-by-state and event-by-time
effects (`stata/32_stacked_csdid.do`).

Main event set: the 39 state-driven events from January 2010 on, a period
with no federal change, so every control is clean in the strict sense too.
Extensions: the 1994-2009 events (federal increases in 1996-97 and 2007-09
contaminate control windows), large events only (window rise of 20 percent
or more), and de Chaisemartin and D'Haultfoeuille's estimator on the log
minimum wage as the continuous-treatment robustness.

## 3. Data

IPUMS-CPS basic monthly, January 1994 to the latest month, all persons in
the extract, ages 16-24 kept (`python/30_build_cps_monthly.py`; about 6,600
16-19 year olds a month). School enrollment last week (`SCHLCOLL`, asked of
16-24 year olds), employment status, hours, and for the outgoing rotation
groups the hourly wage and weekly earnings. Minimum wages: the
Vaghul-Zipperer change list through 2022, extended by hand for 2023-2025
(`data/raw/minwage/`, flagged for verification).

## 4. Outcomes

Ages 16-17 (compulsory schooling in most states) and 18-19 (free to leave),
then 16-19 pooled and 20-24 as a comparison group with a weaker enrollment
margin.

* Enrolled in school or college; enrolled in high school; enrolled full time.
* Employed; at work; in the labour force; usual hours (zero if not working).
* The four-way status Neumark and Shupe use: enrolled and employed, enrolled
  only, employed only, neither.
* First stage: log hourly wage of hourly-paid teens and log weekly earnings
  (outgoing rotation groups), which show that each event moved teen pay.

## 5. Threats

| Threat | Response |
|---|---|
| Treated states differ (richer, urban, Democratic) | event-specific pre-trends over three years; state-driven events only; control set variants |
| Pandemic (2020-21) inside the post-window of the 2017-2020 events | drop 2020-21 months; show the 2010-2016 events alone |
| Enrollment is measured last week, all year round | run school months (September-May) only |
| Indexed states never become clean controls after 2022 | manual list of index adjustments; federal-floor controls as the strict variant |
| Migration of teens with families | state of residence only; a within-family check is not possible in the CPS |
| Dose varies ($0.50 vs $5 over four years) | report by event; split by window rise; continuous estimator |

## 6. Files

`python/30_build_cps_monthly.py`, `python/31_build_mw_events.py`,
`python/32_stacked_events.py`, `python/33_run_minwage.py` (battery),
`python/34_summarise_minwage.py`; `stata/30_build_cps_monthly.do`,
`stata/32_stacked_csdid.do`. Results: `docs/minwage_results.md`.
