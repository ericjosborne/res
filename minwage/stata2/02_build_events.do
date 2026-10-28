*==============================================================================
* 02_build_events.do -- the 70 events, their clean controls, and the unit-month minimum wage panel.
*   Inputs : data/raw/minwage/unit_events.csv, unit_mw_monthly.csv  (built by python/36-38, documented in the README)
*   Outputs: data/clean/events2.dta   (one row per event: unit, event month, control units)
*            data/clean/mwpanel2.dta  (unit x month log minimum wage, for the TWFE regressions)
*==============================================================================
do "stata2/00_setup.do"

* ---- events ----
import delimited "$MW/unit_events.csv", clear varnames(1) encoding(utf8) bindquote(strict)
gen ym = real(substr(event_ym, 1, 4)) * 12 + real(substr(event_ym, 6, 2)) - 1
* an event: a rise of at least 5 percent over its window, with 36 months before and 12 after inside 2010-2025
keep if pct_window >= 0.05 & event_ym >= "2013-01" & event_ym <= "2025-01"
keep event_id unit state_fips kind source event_ym ym pct_window n_steps controls controls_strict
sort ym unit
save "$CLEAN/events2.dta", replace
count
display "events: " r(N)                               // should be 70 once units without CPS teens drop out below

* ---- minimum wage panel ----
import delimited "$MW/unit_mw_monthly.csv", clear varnames(1)
gen ymi = real(substr(ym, 1, 4)) * 12 + real(substr(ym, 6, 2)) - 1
drop ym
rename ymi ym
rename unit geo
gen log_mw = ln(mw)
keep geo state_fips kind ym mw log_mw
save "$CLEAN/mwpanel2.dta", replace
