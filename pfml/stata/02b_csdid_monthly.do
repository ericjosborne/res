*==============================================================================
* 02b_csdid_monthly.do -- month-level event study on the optional basic
*                         monthly extract (built by 01_build_cps_monthly.do).
*==============================================================================
version 16
local xvars "i.agegrp married black hispanic other college"
* Monthly-cohort version (benefits-start month), aggregated to event-time in
* months, for the timing of the response.
use "$CLEAN/cps_women_1844_monthly.dta", clear
keep if mother_lt6 == 1
gen gvar = g_month
replace gvar = 0 if gvar > ym(2024, 12)
csdid inlf `xvars' [iw = wt], time(ym) gvar(gvar) method(drimp) ///
    cluster(statefip) wboot rseed(20260909) reps(499) notyet
estat event, window(-24 24) estore(cs_inlf_event_monthly)
csdid_plot, title("Monthly event study, LFP of mothers of under-6s") name(ev_m, replace)
graph export "$FIG/event_inlf_monthly.png", replace width(1600)

