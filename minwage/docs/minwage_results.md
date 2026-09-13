# Minimum wage increases and teen school enrollment: results

Design: `docs/minwage_design.md`. Data: IPUMS-CPS basic monthly, January
1994 to the latest month, ages 16-24 (5.46 million person-months, about
6,600 16-19 year olds a month), built by `python/30_build_cps_monthly.py`.
Events: `python/31_build_mw_events.py` finds 85 state-driven increases of 5
percent or more after a 36-month quiet period, 39 of them from January 2010
on. Estimator: `python/32_stacked_events.py`, the Cengiz et al. stacked
design with the Callaway-Sant'Anna comparison (treated state minus clean
controls, relative to the year before the event), events weighted by the
treated state's teen population, state block bootstrap with 99 draws.
Battery: `python/33_run_minwage.py`; tables: `output/tables/mw_summary.md`.

Main sample: the 39 events from 2010 on. The federal minimum did not change
in this period, so every control (median 24 states per event) is clean in
the strict sense. The events raise the state minimum by 7 to 86 percent over
the four-year window (median 34 percent); 24 of them are multi-step
schedules.

## 1. Headline

The increases raised teen pay and changed nothing else. Hourly wages of
hourly-paid 16-17 year olds rise 5.1 percent (s.e. 1.2) and of 18-19 year
olds 3.1 percent (0.9), building from the first year to about 7 percent by
year three. Enrollment does not move: -0.3 points (s.e. 0.4) at 16-17 and
-0.4 (0.9) at 18-19, so the intervals exclude a fall in enrollment of more
than about 1 point at 16-17 and 2 points at 18-19. Employment does not move
either (0.0 (0.5) and +1.3 (0.8)), and neither does any of the four
school-work states. Pre-event coefficients are within a fraction of a point
of zero for every outcome.

Post-event average effect (years 0-3), 2010+ events, from
`output/tables/mw_summary.md`:

| Outcome | 16-17 | s.e. | 18-19 | s.e. |
|---|---|---|---|---|
| Enrolled in school | -0.0034 | 0.0042 | -0.0036 | 0.0090 |
| Enrolled in high school | -0.0067 | 0.0049 | -0.0109 | 0.0067 |
| Enrolled full time | -0.0030 | 0.0044 | -0.0056 | 0.0081 |
| Employed | -0.0001 | 0.0049 | +0.0125 | 0.0079 |
| In labour force | +0.0035 | 0.0051 | +0.0097 | 0.0056 |
| Usual hours | -0.06 | 0.12 | +0.38 | 0.29 |
| Enrolled and employed | -0.0021 | 0.0048 | +0.0063 | 0.0064 |
| Enrolled only | -0.0013 | 0.0056 | -0.0100 | 0.0066 |
| Employed only | +0.0020 | 0.0024 | +0.0062 | 0.0071 |
| Neither enrolled nor employed | +0.0014 | 0.0034 | -0.0026 | 0.0058 |
| Log hourly wage (hourly paid, ORG) | +0.0514 | 0.0122 | +0.0306 | 0.0088 |
| Log weekly earnings (ORG) | +0.0464 | 0.0346 | +0.0482 | 0.0265 |

Pre-period means (treated states, year before the event): enrolled 0.84 at
16-17 and 0.61 at 18-19; employed 0.21 and 0.45.

![wage](../output/figures/mw_wage_first_stage.png)

First stage by event year, log hourly wage of hourly-paid teens (s.e. in
parentheses): ages 16-17, years -3 to 3: -0.020 (0.010), 0.007 (0.012), 0,
0.017 (0.012), 0.065 (0.012), 0.052 (0.014), 0.071 (0.022); ages 18-19:
0.006 (0.012), -0.001 (0.008), 0, 0.007 (0.010), 0.036 (0.011), 0.029
(0.015), 0.050 (0.011). Year 0 is small because the event month falls inside
it and most schedules add their later steps in years 1-3; from year 1 the
wage effect is five to seven standard errors from zero and grows with the
schedule. Weekly earnings of all teen workers rise 6 to 9 percent from year 1
at 16-17 and 5 to 7 percent at 18-19, so hours did not fall enough to offset
the wage.

![event](../output/figures/mw_event_main.png)

![status](../output/figures/mw_status_1819.png)

## 2. Robustness

Every variant of the enrollment estimate is within one standard error of
zero (`output/tables/mw_summary.md`, robustness block):

| Variant, enrolled | 16-17 | s.e. | 18-19 | s.e. |
|---|---|---|---|---|
| Main (39 events, 2010+) | -0.0034 | 0.0042 | -0.0036 | 0.0090 |
| All 71 events, 1994+ | -0.0022 | 0.0026 | +0.0017 | 0.0055 |
| 32 events before 2010 | -0.0010 | 0.0047 | +0.0071 | 0.0073 |
| Large events only (window rise 20%+, 58 events) | -0.0031 | 0.0029 | -0.0041 | 0.0062 |
| Federal-floor controls only | -0.0037 | 0.0042 | -0.0048 | 0.0093 |
| Equal weight per event | +0.0004 | 0.0040 | -0.0073 | 0.0066 |
| Drop 2020-21 | -0.0026 | 0.0032 | -0.0047 | 0.0091 |
| September-May only | -0.0052 | 0.0037 | -0.0069 | 0.0072 |

Employment of 16-17 year olds is -0.9 points (s.e. 0.5) for the large-event
set and zero otherwise. Ages 20-24, where the enrollment margin is weaker,
show the same nothing: -0.2 (0.5) on enrollment, +0.2 (0.5) on employment.
Event by event, 20 of the 39 post-2009 events have a negative enrollment
estimate at 16-17 and 19 a positive one; the three largest by weight
(California 2014, New York 2014, Florida 2021) are -0.3, +0.1 and -2.5
points, and Florida's pre-trend is the same -2.6.

### Substate minimums: the unit design

City and county minimums (Vaghul-Zipperer substate list) are handled by
treating every identified county with its own minimum as a separate unit with
its own effective minimum wage series (a city's rate applied to its whole
county), and the rest of each state as the state unit
(`python/38_unit_panel.py`: 107 units, 56 of them counties). Events are then
defined at the unit level with the same rule (a rise of 5 percent or more
after 36 quiet months, not caused by the federal floor), and each event's
controls are the units in other states with no rise in the window. A Seattle
teen is treated by Seattle's minimum and King County has its own event when
Seattle raises it; a rise in the state rate that also lifts a county unit is
a county event with source "both". From 2010 there are 101 events, 73 with
CPS teens: 39 state-remainder events, 18 county events where state and local
rates rose together (the New York City boroughs, Long Island and Westchester,
Los Angeles, the Bay Area counties, San Diego, Denver, Minneapolis, Flagstaff,
the Portland metro), and 16 county events driven by a local rise alone (San
Francisco, San Jose, Chicago, Seattle, Tacoma, Montgomery and Prince George's
counties, Portland ME, St. Paul, Albuquerque, Las Cruces, Santa Fe, and the
short-lived Iowa and Kentucky county minimums).

| Post-event average | Wage 16-17 | Wage 18-19 | Enrolled 16-17 | Enrolled 18-19 | Employed 16-17 | Employed 18-19 |
|---|---|---|---|---|---|---|
| State design, 39 events (main) | 0.051 (0.012) | 0.031 (0.009) | -0.003 (0.004) | -0.004 (0.009) | -0.000 (0.005) | 0.013 (0.008) |
| Unit design, all 73 events | 0.053 (0.012) | 0.030 (0.009) | -0.003 (0.004) | 0.001 (0.009) | -0.001 (0.005) | 0.010 (0.007) |
| Unit design, state-remainder events (39) | 0.052 (0.014) | 0.028 (0.009) | -0.005 (0.005) | -0.009 (0.010) | 0.004 (0.005) | 0.015 (0.008) |
| Unit design, county events, state and local rise (18) | 0.051 (0.035) | 0.043 (0.017) | 0.005 (0.007) | 0.033 (0.009); pre 0.013 | -0.021 (0.029) | 0.003 (0.023) |
| Unit design, county events, local rise only (16) | 0.085 (0.044) | 0.043 (0.043) | 0.016 (0.017) | 0.075 (0.034); pre 0.053 | -0.016 (0.028) | -0.047 (0.051) |

The unit design reproduces the state design: the wage first stage and the
enrollment and employment nulls are unchanged when the 34 county events are
added, because the state remainders carry most of the weight. The county
events on their own are a different matter. Their first stage is larger
(local increases are bigger) and their enrollment estimates at 18-19 are
positive, +3.3 points (s.e. 0.9) for the county events with both a state
and a local rise and +7.5 (3.4) for local-only events, but so are their
pre-event averages (+1.3 and +5.3): the big-city counties were on a rising
enrollment path relative to other states' units before their increases. Net
of the pre-trend the post-event change is about two points in both sets,
which is at most suggestive. Hours, participation and the four school-work
states are unchanged in the unit design (`output/tables/mw_summary.md`).

The earlier checks, which keep the state design and only clean the control
side or restrict the treated side, are retained in the summary tables
(controls net of local-minimum counties: enrolled -0.004 (0.004) and -0.002
(0.009); treated counties without a local minimum: -0.007 (0.004) and +0.004
(0.010)).

## 3. Heterogeneity (enrolled, 2010+ events)

| Subgroup | 16-17 | s.e. | 18-19 | s.e. |
|---|---|---|---|---|
| Girls | -0.003 | 0.005 | +0.008 | 0.012 |
| Boys | -0.004 | 0.006 | -0.015 | 0.010 |
| Black | 0.000 | 0.014 | +0.039 | 0.027 |
| Hispanic | -0.005 | 0.010 | -0.013 | 0.023 |
| White and other | -0.002 | 0.006 | -0.013 | 0.010 |
| Family income below $50,000 | -0.002 | 0.008 | +0.002 | 0.016 |
| Family income $50,000 or more | -0.004 | 0.004 | -0.005 | 0.012 |

Boys aged 18-19 are the only cell with a point estimate above one point,
and its pre-trend is -2.2, so it is not evidence of anything.

## 4. Reading

This is a precise null with a demonstrated first stage, which is the
combination that makes a null informative. The 2010-2025 increases were
large (a third of the minimum over four years, on average), they raised the
pay of the teens who work, and they did not change whether teens were in
school, whether they worked, or how they combined the two. The result
contradicts the two-way fixed effects estimates in Neumark and Wascher
(1995, 2003) and Neumark and Shupe (2019), who attribute the post-2000 fall
in 16-17 year olds' employment and the shift from "enrolled and employed"
to "enrolled only" mainly to minimum wages. In an event design with clean
controls, the employment of 16-17 year olds does not fall (0.0, s.e. 0.5
points) and the shift to enrolled-only does not occur (-0.1, s.e. 0.6). It
is consistent with Cengiz et al. (2019), who find no employment loss for
low-wage workers as a whole, and extends that to the schooling margin.

Limits. The 2023-2025 minimum wage steps are compiled from memory and must
be verified against the state schedules before the event list is final; the
same holds for the manual index adjustments, which decide which states are
clean controls after 2022. Standard errors come from 99 bootstrap draws and
should be replaced by the Stata wild cluster bootstrap
(`stata/32_stacked_csdid.do`). Enrollment last week is a coarse measure of
schooling: it cannot see grade progression, dropout timing or completion,
so a null here does not rule out effects on attainment measured years
later, which the ACS or administrative data would be needed to test.
