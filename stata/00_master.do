*==============================================================================
* 00_master.do -- State paid family and medical leave (PFML) and mothers'
*                 labour supply: Callaway & Sant'Anna (2021) staggered DiD
*
* Stata 16.  Run from the repository root:  do stata/00_master.do
*
* Community packages (install once):
*   ssc install csdid, replace      // Rios-Avila, Sant'Anna & Callaway
*   ssc install drdid, replace      // doubly-robust DiD building block
*   ssc install estout, replace     // esttab tables
*   ssc install did_imputation      // Borusyak, Jaravel & Spiess (robustness)
*   ssc install eventstudyinteract  // Sun & Abraham (robustness)
*   ssc install did_multiplegt_dyn  // de Chaisemartin & D'Haultfoeuille (robustness)
*   net install honestdid, from("https://raw.githubusercontent.com/mcaceresb/stata-honestdid/main") replace
*   ssc install coefplot, replace
*
* Data: the IPUMS-CPS ASEC extract (women 18-44, 1990-2025) described in
* data/raw/IPUMS_EXTRACT_SPEC.md, saved as data/raw/ipums_cps_asec.csv,
* plus the policy file data/raw/pfml_policy_dates.csv.  A basic-monthly
* extract (optional) adds month-level timing.
*==============================================================================
version 16
clear all
set more off
set maxvar 20000
set seed 20260909

global ROOT  "`c(pwd)'"
global PF    "$ROOT"
global RAW   "$PF/data/raw"
global CLEAN "$PF/data/clean"
global TAB   "$PF/output/tables"
global FIG   "$PF/output/figures"
global LOG   "$PF/output/logs"
foreach d in "$CLEAN" "$TAB" "$FIG" "$LOG" {
    capture mkdir "`d'"
}
capture log close
log using "$LOG/master_`c(current_date)'.log", replace text

* Full pipeline: ASEC extract (required, see data/raw/IPUMS_EXTRACT_SPEC.md)
global ASEC "$RAW/cps_00090.csv"        // IPUMS extract (women 18-44 or all persons; the build filters)
capture confirm file "$ASEC"
if _rc != 0  global ASEC "$RAW/ipums_cps_asec.csv"
capture confirm file "$ASEC"
if _rc == 0 {
    do "$PF/stata/01_build_cps_asec.do"
    global DATA "$CLEAN/cps_women_1844_asec.dta"
    global TVAR "year"
    do "$PF/stata/02_csdid.do"
    do "$PF/stata/03_robustness.do"
    do "$PF/stata/04_tables.do"
}
else {
    display as error "ASEC extract not found ($ASEC); nothing was run."
}
* Optional: basic monthly extract for month-level timing (extract B in the spec)
capture confirm file "$RAW/ipums_cps_basic.dta"
if _rc == 0 {
    do "$PF/stata/01_build_cps_monthly.do"
    do "$PF/stata/02b_csdid_monthly.do"
}
log close
