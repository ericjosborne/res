*==============================================================================
* 00_master.do -- State paid family and medical leave (PFML) and mothers'
*                 labour supply: Callaway & Sant'Anna (2021) staggered DiD
*
* Stata 16.  Run from the repository root:  do pfml/stata/00_master.do
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
* Data: an IPUMS-CPS basic-monthly extract 2000m1-2024m12 (see 01_build_cps.do
* for the variable list) saved as pfml/data/raw/ipums_cps_basic.dta, plus the
* policy file pfml/data/raw/pfml_policy_dates.csv.
*==============================================================================
version 16
clear all
set more off
set maxvar 20000
set seed 20260909

global ROOT  "`c(pwd)'"
global PF    "$ROOT/pfml"
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

* Preliminary demonstration on the CPS ASEC 2021-23 file built in Python
* (pfml/data/clean/cps_women_1844.dta); does not need the IPUMS extract.
do "$PF/stata/90_prelim_csdid.do"

* Full pipeline (requires the IPUMS-CPS extract)
capture confirm file "$RAW/ipums_cps_basic.dta"
if _rc == 0 {
    do "$PF/stata/01_build_cps.do"
    do "$PF/stata/02_csdid.do"
    do "$PF/stata/03_robustness.do"
    do "$PF/stata/04_tables.do"
}
else {
    display as error "IPUMS-CPS extract not found at $RAW/ipums_cps_basic.dta; only the preliminary demo ran."
}
log close
