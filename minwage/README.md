# The fall in teen employment and the minimum wage

Stacked event studies of minimum wage increases and teenagers' school
enrollment, employment, hours and the four school-work states, in the IPUMS-CPS
basic monthly files 1994-2026. Units are the jurisdictions whose wage floor a
teen faces: every identified county with its own minimum, and the rest of each
state. Events are increases of 5 percent or more after 36 quiet months (73
since 2010 with CPS teens: 39 state remainders, 34 counties), each compared
with clean control units in other states in a Callaway-Sant'Anna comparison
relative to the year before the event (Cengiz, Dube, Lindner and Zipperer 2019
design). The state design (states as units, 39 events) is in the appendix.

* `paper/minwage_teens.tex` / `.pdf` – the draft paper: Smith-style introduction, two-period theory with the non-competitive case, data, empirical strategy (unit design), results ordered as school-work shares (all, then by family income) and wages (all, then by family income); robustness, sex/race heterogeneity, the within-year income split and the dropout outcome in the appendix. Tables and figures: `python/45_paper_v2_tables.py`; the regression tables (two-way fixed effects on the log minimum and stacked difference-in-differences) that precede each event-study figure: `python/46_regressions.py`.
* `docs/minwage_design.md`, `docs/minwage_results.md` – design memo and results memo.
* `output/tables/mw_summary.md` – all runs collected; `output/tables/mw_*` per-run event, simple and by-event CSVs; `output/figures/mw_*`.

## Headline

The increases raised the hourly wages of hourly-paid teens by 5.3 percent
(s.e. 1.2) at ages 16-17 and 3.0 percent (0.9) at 18-19, growing to 7 and 5
percent by the third year. Enrollment (-0.3 points, s.e. 0.4; +0.1, s.e. 0.9),
employment (-0.1, s.e. 0.5; +1.0, s.e. 0.7), hours, labour force participation
and the four school-work states did not change. Flat pre-trends; identical
with states as units; stable across 134 events since 1994, pre-2010 events,
large events, strict and federal-floor controls, without 2020-21, school
months only, and subgroups.
A precise null with a demonstrated first stage, contradicting the two-way fixed
effects finding of Neumark and Shupe (2019).

## Data

| File | What | Where it comes from |
|---|---|---|
| `data/raw/monthly/cps_00091.csv.gz` (1.45 GB, not committed) | IPUMS-CPS basic monthly 1994-2026, all persons; the variable list is in `docs/minwage_design.md` | GitHub release `data-cps-monthly`: `https://github.com/ericjosborne/res/releases/tag/data-cps-monthly` |
| `data/clean/cps_monthly_1624.csv.gz` (100 MB, not committed) | 5.46 million person-months aged 16-24 | `python/30_build_cps_monthly.py` |
| `data/raw/minwage/state_mw_changes_1974_2022.csv`, `federal_mw_changes.csv` | Vaghul-Zipperer change lists (converted from the repository's raw spreadsheets) | https://github.com/benzipperer/historicalminwage |
| `data/raw/minwage/state_mw_changes_2023plus_manual.csv` | 2023-2025 changes and index adjustments, **compiled from memory, verify** | state labour departments |
| `data/raw/minwage/state_mw_monthly.csv`, `mw_events.csv` | Monthly effective minimum by state; the event list with clean controls | `python/31_build_mw_events.py` |
| `data/raw/minwage/substate_mw_changes.csv`, `county_mw_monthly.csv`, `state_local_flags.csv`, `local_events.csv` | City and county minimums (same source), mapped to CPS county codes; contamination flags; county events | `python/36_substate.py` |
| `data/raw/minwage/unit_mw_monthly.csv`, `unit_events.csv` | Unit design: every county with its own minimum is a unit, the rest of each state another; unit-level events with source (state / local / both) and clean controls | `python/38_unit_panel.py` |

## How to run

From this directory (`minwage/`):

```bash
pip install -r requirements.txt
python python/30_build_cps_monthly.py        # streams the extract, keeps ages 16-24
python python/31_build_mw_events.py          # minimum wage panel and event list
python python/38_unit_panel.py               # unit-level panel and events (run before the battery)
python python/33_run_minwage.py --B 99 --P 4 # 105 unit-design runs, ~40 min; --design post2009 for the state design
python python/36_substate.py                 # county minimum wage panel (input to 38); contamination flags; local events
python python/37_run_substate.py 99          # optional: cleaned-control and treated-split checks on the state design
python python/34_summarise_minwage.py        # mw_summary.md and the main figures
python python/35_paper_tables.py             # summary, events, robustness and heterogeneity tables for paper/
python python/40_run_ses.py 99; python python/42_run_ses_rel.py 99   # family-income splits (nominal, within-year median)
python python/43_run_dropout.py 99; python python/44_run_dropout_school.py 99   # dropout outcome (Smith 2021), all months and school months
python python/45_paper_v2_tables.py          # results tables and figures in the paper's order
python python/46_regressions.py              # TWFE log-MW (all months, school months) and stacked-DiD regression tables (pyfixest; ~45 min; --reuse_stacked / --tables_only)
python python/47_twfe_diagnostics.py         # Appendix C: what drives the TWFE enrollment coefficient (months, comparison states, leads, trends)
cd paper && pdflatex minwage_teens.tex && pdflatex minwage_teens.tex
```

Stata 16, from this directory: `do stata/00_master.do` runs the build, the
Cengiz et al. stacked regression, `csdid` on the stacked cells with the wild
cluster bootstrap, and `did_multiplegt_dyn` on the log minimum wage. The
do-files have not been executed (no Stata in the build environment).

## Layout

```
python/   30_build_cps_monthly.py  31_build_mw_events.py  32_stacked_events.py  33_run_minwage.py  34_summarise_minwage.py  35_paper_tables.py
          36_substate.py  37_run_substate.py  38_unit_panel.py  39_run_units.py  aelib.py
stata/    00_master.do  30_build_cps_monthly.do  32_stacked_csdid.do  46_twfe.do
data/     raw/minwage/ (change lists, panel, events)  raw/monthly/ (extract, not committed)  clean/ (teen file, not committed)
output/   tables/ (mw_<ages>_<outcome>_<eventset>[_variant]_{event,simple,byevent}.csv; mw_summary.md)  figures/
docs/     minwage_design.md  minwage_results.md
paper/    minwage_teens.tex  minwage_teens.pdf  tables/  figures/
```
