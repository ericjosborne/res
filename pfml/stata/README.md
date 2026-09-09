# Stata 16 code

Written for Stata 16 with these community packages: `csdid`, `drdid`, `estout`,
`coefplot`, `reghdfe`, `did_imputation`, `eventstudyinteract`,
`did_multiplegt_dyn`, `honestdid` (see the header of `00_master.do` for the
install lines).

**Status: not executed.** The build environment has no Stata licence, so
these files are untested. They were written to mirror the Python pipeline in
`../python/`, which was executed; the preliminary do-file `90_prelim_csdid.do`
should reproduce the point estimates in `../output/tables/prelim_*.csv` on the
exported `../data/clean/cps_women_1844.dta` (Stata format 118). Two things to
check on first run:

1. `csdid` weight type: the do-files use `[iw = weight]`; if your `csdid`
   version rejects it, use `[pw = weight]`.
2. `estat event` in `csdid` uses `window()`; older versions call it
   `estat event, window(-6 6)` as written, newer ones accept the same syntax.

| File | Purpose |
|---|---|
| `00_master.do` | paths, logging, runs everything |
| `01_build_cps.do` | IPUMS-CPS basic monthly 2000-2024 to the estimation file and state-cell panels |
| `02_csdid.do` | main Callaway-Sant'Anna estimates (yearly and monthly cohorts, drimp, wild cluster bootstrap) |
| `03_robustness.do` | not-yet-treated controls, triple difference, BJS, Sun-Abraham, dCDH, HonestDiD, placebo, alternative cohort timing |
| `04_tables.do` | esttab tables |
| `90_prelim_csdid.do` | preliminary estimates on the ASEC 2021-23 file (runs without the IPUMS extract) |
