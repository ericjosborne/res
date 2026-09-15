*==============================================================================
* 00_master.do -- minimum wage increases and teen school enrollment.
*   Run from the minwage/ directory: the working directory is the project root.
*   Packages: ssc install csdid drdid reghdfe ftools estout did_multiplegt_dyn
*==============================================================================
version 16
clear all
set more off
global ROOT  "`c(pwd)'"
global RAW   "$ROOT/data/raw"
global CLEAN "$ROOT/data/clean"
global TAB   "$ROOT/output/tables"
global FIG   "$ROOT/output/figures"
global LOG   "$ROOT/output/logs"
capture mkdir "$LOG"
capture log close
log using "$LOG/master.log", replace text

* the monthly extract is data/raw/monthly/cps_00091.csv.gz: unzip it first (gunzip -k)
do "$ROOT/stata/30_build_cps_monthly.do"
* the event list is built by python/31_build_mw_events.py (data/raw/minwage/mw_events.csv)
do "$ROOT/stata/32_stacked_csdid.do"
* the unit panel is built by python/38_unit_panel.py (data/raw/minwage/unit_mw_monthly.csv)
do "$ROOT/stata/46_twfe.do"

log close
