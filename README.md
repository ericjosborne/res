# Paid family and medical leave and mothers' labour supply

Staggered adoption of state paid family and medical leave (PFML) across nine
states and DC, 2004-2024, estimated with Callaway and Sant'Anna (2021)
group-time average treatment effects on IPUMS-CPS ASEC repeated cross sections,
1990-2025. Written for Stata 16 (`stata/`), with an executed Python pipeline
(`python/`) that produced the current results.

* `docs/research_design.md` – question, identification, data, specification, threats.
* `docs/results.md` – results with tables and figures (`docs/results.html` is the same as a page).
* `output/tables/`, `output/figures/` – every number and plot the write-up cites.

## Headline

PFML has no detectable effect on the employment, hours or full-time work of
mothers of children under 6 in the first five years after benefits become
available. Simple ATT on employment: +0.021 (s.e. 0.014), a 95 percent
interval of -0.7 to +4.9 points; pre-trends flat; childless-women placebo
zero. A rise to +4 points in years 7-10 is identified by California and New
Jersey alone. By subgroup (section 7 of `docs/results.md`): no heterogeneity
by education, other family income or marital status; the effect is confined to
white non-Hispanic mothers (+5.4 points, +2.2 hours) with zero for Black,
Hispanic and other mothers. Births do not respond for any group. The
white-mother effect passes a childless-women placebo by race but is absent in
the ASEC-to-ASEC linked (address-stayer) sample and does not line up with
prior-year work, so migration composition is the open question (section 7.1).

## Next: paid leave and parents' mental health beyond the leave (NSCH)

The labour-supply and fertility results are precise nulls. Wells et al. (2026,
AJE) already estimate postpartum depression effects with PRAMS and the same
estimator, so the paper is being re-centred on the NSCH (2016-2024): exposure
to paid leave at the child's birth and the parent's mental health one to five
years later, fathers included, with the newest cohorts. Design memo:
`docs/nsch_design.md`. Data instructions: `data/raw/NSCH_SPEC.md`. Build:
`python/20_build_nsch.py`, `stata/20_build_nsch.do`. Estimation:
`python/02_csdid.py --data nsch ...`, `stata/21_csdid_nsch.do`. Waiting on the
NSCH files. (The BRFSS scripts, `10_*`/`11_*`, are parked: BRFSS cannot
identify new mothers, so it would be a diluted replication of Wells et al.;
a pregnant-women prenatal analysis remains a possible section.)

## Data

| File | What | Where it comes from |
|---|---|---|
| `data/raw/cps_00090.csv` (1 GB, not committed) | IPUMS-CPS ASEC 1990-2025, all persons; the spec is `data/raw/IPUMS_EXTRACT_SPEC.md` | GitHub release `data-v1` of this repository: `https://github.com/ericjosborne/res/releases/download/data-v1/cps_00090.csv` |
| `data/raw/pfml_policy_dates.csv` | Enactment, contribution and benefit start dates by state; cohort definitions | Compiled from memory, **verify before use** (`data/raw/README.md`) |
| `data/clean/cps_asec_women_1844.csv.gz` | Women 18-44, 1,216,812 person-years, outcomes, family structure, cohorts | `python/01_build_ipums_asec.py` (the `.dta` twin is rebuilt locally, not committed) |

## How to run

```bash
pip install -r requirements.txt
python python/01_build_ipums_asec.py        # extract -> data/clean/cps_asec_women_1844.{csv.gz,dta}
bash   python/03_run_all.sh                 # 13 Callaway-Sant'Anna runs (samples x outcomes), ~30 min
python python/04_summarise.py               # summary tables and the three main figures
bash   python/05_heterogeneity.sh           # 36 subgroup runs; then python python/06_summarise_het.py
python python/07_link_lag.py                # ASEC-to-ASEC link (prior-year work); then the elig_* runs in docs/results.md 7.1
```

Stata 16, from the repository root, after installing the packages listed at the
top of `stata/00_master.do` (`csdid`, `drdid`, `estout`, `coefplot`, `reghdfe`,
`did_imputation`, `eventstudyinteract`, `did_multiplegt_dyn`, `honestdid`):

```stata
do stata/00_master.do
```

`00_master.do` builds the file from the extract, runs the main `csdid`
estimates (doubly robust, covariates, state-clustered wild bootstrap), the
robustness set (not-yet-treated controls, triple difference, Sun-Abraham, BJS
imputation, de Chaisemartin-D'Haultfoeuille, HonestDiD, childless placebo) and
the esttab tables. **The do-files have not been executed** (no Stata in the
build environment); `stata/README.md` lists the two things to check first.

## Layout

```
python/   01_build_ipums_asec.py  02_csdid.py  03_run_all.sh  04_summarise.py  05_heterogeneity.sh  06_summarise_het.py  07_link_lag.py
          08_checks_race.sh  10_build_brfss.py (parked)  20_build_nsch.py  aelib.py
stata/    00_master.do  01_build_cps_asec.do  02_csdid.do  03_robustness.do  04_tables.do  05_heterogeneity.do
          10_build_brfss.do  11_csdid_brfss.do   (BRFSS, parked)
          20_build_nsch.do  21_csdid_nsch.do    (NSCH mental-health design)
          01_build_cps_monthly.do  02b_csdid_monthly.do   (optional monthly extract)
data/     raw/ (policy dates, extract specs; brfss/ and nsch/ raw files not committed)   clean/ (analysis files)
output/   tables/ (per-run event/group/calendar/simple/attgt CSVs; summary_*.md)   figures/
docs/     research_design.md  results.md  results.html
```

Output file names are `<sample>_<outcome>[_notyet]_<aggregation>.csv` with
samples `mothers_lt6`, `mothers`, `childless` and outcomes `worked`, `hours`,
`fulltime`, `inlf`.

The earlier project on this branch (Angrist-Evans same-sex instrument) and the
2021-23 pilot on PolicyEngine files were removed in the restructuring commit;
they remain in the git history before it.
