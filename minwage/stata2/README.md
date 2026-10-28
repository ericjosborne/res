# stata2: one self-contained do-file per table or figure

The `stata/` folder runs the whole design in one pass. This folder does the same work in small steps so each
number in the paper can be traced to one short, commented file. Run Stata with the working directory set to
`minwage/` (the folder that contains `stata2/`). Outputs go to `output/stata2/` as `.csv` (tables, one row per
cell, printed to the screen as well) and `.png` (figures).

Packages: `ssc install reghdfe ftools estout grc1leg`.

## 1. Build the data (run once, in this order)

| File | Makes | Notes |
|---|---|---|
| `00_setup.do` | paths | called by every other file |
| `01_build_cps.do` | `data/clean/cps2.dta` | the analysis file: ages 16-24, January 2010 - December 2025; outcomes, demographics, unit assignment |
| `02_build_events.do` | `events2.dta`, `mwpanel2.dta` | the 70 events with their clean controls; the unit x month log minimum wage |
| `03_build_stacked.do` | `stacked2.dta`, `cells2.dta` | unit x month x age cells, stacked over the 70 events (84 months each) |
| `03b_build_stacked_groups.do <group>` | `stacked2_<group>.dta` | the same for a subgroup: `lowses highses female male white nonwhite lowsesrel highsesrel school school_lowses school_highses school_lowsesrel school_highsesrel` |
| `04_build_stacked_fine.do` | `stacked_fine2.dta` | cells also split by sex, race and income category, for the regressions with controls (Tables 2-12) |

The unit and event files in `data/raw/minwage/` (`unit_mw_monthly.csv`, `unit_events.csv`, `mw_events.csv`) are
built by the Python scripts 31, 36 and 38 from the Vaghul-Zipperer minimum wage lists; they are plain CSVs and
are read as given here.

## 2. Tables and figures (each file stands alone once the data above exist)

| Paper item | File | Needs |
|---|---|---|
| Figure 1 trends 1995-2025 | `fig01_trends.do` | raw extract |
| Figure 2 minimum wage calendar | `fig02_minwage.do` | cps2, events2 |
| Table 1 means before the event | `tab01_means.do` | cps2, events2 |
| Table 2 stacked DiD with controls, shares, all teens | `tab02_stacked_controls.do` | stacked_fine2 |
| Table 3 / 4 / 5 by income / sex / race | `tab03_…_ses.do`, `tab04_…_sex.do`, `tab05_…_race.do` | stacked_fine2 |
| Table 6 wages, all teens | `tab06_stacked_controls_wage.do` | stacked_fine2 |
| Tables 8 / 10 / 12 wages by income / sex / race | `tab08_…`, `tab10_…`, `tab12_…` | stacked_fine2 |
| Tables 7 / 9 / 11 post-event wage averages by group, and Appendix Tables 15-22 | `tabA_post_all.do`, `tabA_post_ses.do`, `tabA_post_sex.do`, `tabA_post_race.do` | stacked2, stacked2_<group> |
| Figures 3-6 shares by age / income / sex / race | `fig03_groups_by_age.do`, `fig04_groups_ses.do`, `fig05_groups_sex.do`, `fig06_groups_race.do` | stacked2, stacked2_<group> |
| Figures 7-10 wages by age / income / sex / race | `fig07_wage_by_age.do`, `fig08_wage_ses.do`, `fig09_wage_sex.do`, `fig10_wage_race.do` | stacked2, stacked2_<group> |
| Table 13 robustness | `tab13_robustness.do` | stacked2, cells2, events2, stacked2_school |
| Table 13 state-design row; Figures 11-12 | `tab13b_state_design.do` | cps2, mw_events.csv |
| Table 14 event-time coefficients | `tab14_eventtime.do` | stacked2 |
| Event-by-event figure | `fig_byevent.do` | stacked2, events2 |
| Appendix Tables 24-31 TWFE | `tabB_twfe.do` | cps2, mwpanel2 |
| Appendix Table 32 TWFE diagnostics | `tabB_twfe_diag.do` | cps2, mwpanel2 |
| Appendix D within-year median split (Tables 33-34, Figure 14) | `tabD_sesrel.do` | stacked2_lowsesrel, stacked2_highsesrel |
| Appendix E dropout (Table 35) | `tabE_dropout.do` | stacked2, stacked2_school*, |

## 3. How the estimator in these files relates to the paper's numbers

The event-study figures and the post-event averages here come from the stacked regression of Cengiz et al. (2019):
cell mean on relative-year dummies x treated, with event x unit and event x month fixed effects, weighted by the
cell's teen population, clustered by state, base year -1. The Python code behind the paper computes the same
relative-year effects event by event as differences of weighted means, weights events by their treated teen
population, and gets standard errors from a block bootstrap over states. The two agree closely but not exactly:
the regression weights observations rather than events. Tables 2-12 (post x treated with individual controls)
are the same specification in both, and should match to the third decimal.

These files have not been executed here (no Stata in the build environment); syntax was kept to plain
`collapse`, `reghdfe`, `lincom`, `postfile` and `twoway`, so errors, if any, should be small.
