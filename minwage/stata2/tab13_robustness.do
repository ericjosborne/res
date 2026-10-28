*==============================================================================
* tab13_robustness.do -- Table 13: post-event averages for enrollment, employment and neither (ages 16-17, 18-19)
*   under alternative event sets, control sets, weights and samples.  One row per variant.
*   Rows from the main stacked file: main; state-remainder events only; county events (state+local rise); county
*   events (local rise only); large events (window rise >= 20%); federal-floor controls only; equal weight per
*   event; drop 2020-21.  Strict controls are re-stacked here with the controls_strict list.
*   September-May uses stacked2_school.dta (03b ... school).  The state design is in tab13b_state_design.do.
*   Inputs: data/clean/stacked2.dta, cells2.dta, events2.dta, stacked2_school.dta.  Output: output/stata2/tab13_robustness.csv
*==============================================================================
do "stata2/00_setup.do"

* ---- helper: post-event average for one outcome and age band on the data in memory, with weight `w' ----
capture program drop post_avg
program define post_avg
    args y b w variant
    reghdfe `y' ib3.rk#i.treated [aw = `w'] if band == `b', absorb(eg et) cluster(state_fips)
    lincom (_b[4.rk#1.treated] + _b[5.rk#1.treated] + _b[6.rk#1.treated] + _b[7.rk#1.treated]) / 4
    post P ("`variant'") ("`y'") (`b') (r(estimate)) (r(se)) (e(N_clust))
end
tempfile res
postfile P str40 variant str12 outcome int band double post double se double nclust using `res', replace

use "$CLEAN/stacked2.dta", clear
merge m:1 event_id using "$CLEAN/events2.dta", keepusing(source pct_window) nogen
* equal weight per event: scale each block's weights to sum to one
bysort event_id: egen blocktot = total(n)
gen n_eq = n / blocktot
* federal-floor states (minimum at the federal $7.25 throughout 2010-2025)
gen fedfloor = inlist(state_fips, 1, 13, 16, 18, 20, 22, 28, 40, 45, 47, 48, 49, 56, 21, 37, 38, 42, 55, 33, 19, 51)
gen keep_fed = treated | fedfloor

foreach y in enrolled employed neither {
    foreach b in 1 2 {
        post_avg `y' `b' n "main"
        preserve
            keep if source == "state"
            post_avg `y' `b' n "state-remainder events only"
        restore
        preserve
            keep if source == "both"
            post_avg `y' `b' n "county events, state and local rise"
        restore
        preserve
            keep if source == "local"
            post_avg `y' `b' n "county events, local rise only"
        restore
        preserve
            keep if pct_window >= 0.20
            post_avg `y' `b' n "large events (rise >= 20%)"
        restore
        preserve
            keep if keep_fed
            post_avg `y' `b' n "federal-floor controls only"
        restore
        post_avg `y' `b' n_eq "equal weight per event"
        preserve
            drop if inrange(ym, 2020 * 12, 2021 * 12 + 11)
            post_avg `y' `b' n "drop 2020-21"
        restore
    }
}

* ---- strict controls: units with no rise of any kind in the window (re-stack with controls_strict) ----
use "$CLEAN/events2.dta", clear
local N = _N
tempfile stack
local first = 1
forvalues i = 1/`N' {
    use "$CLEAN/events2.dta" in `i', clear
    local ev = event_id[1]
    local u = unit[1]
    local t0 = ym[1]
    local ctrl = controls_strict[1]
    use "$CLEAN/cells2.dta", clear
    gen keep = geo == `u'
    foreach c of local ctrl {
        replace keep = 1 if geo == `c'
    }
    keep if keep & inrange(ym - `t0', -36, 47)
    drop keep
    gen event_id = `ev'
    gen treated = geo == `u'
    gen relyear = floor((ym - `t0') / 12)
    if `first' {
        save `stack', replace
        local first = 0
    }
    else {
        append using `stack'
        save `stack', replace
    }
}
use `stack', clear
bysort event_id: egen any_treated = max(treated)
drop if any_treated == 0
egen eg = group(event_id geo)
egen et = group(event_id ym)
gen rk = relyear + 4
gen band = cond(age <= 17, 1, 2)
foreach y in enrolled employed neither {
    foreach b in 1 2 {
        post_avg `y' `b' n "strict controls"
    }
}

* ---- September to May only ----
use "$CLEAN/stacked2_school.dta", clear
foreach y in enrolled employed neither {
    foreach b in 1 2 {
        post_avg `y' `b' n "September-May only"
    }
}
postclose P
use `res', clear
format post se %8.4f
list variant outcome band post se nclust, sepby(variant) noobs
export delimited using "$OUT/tab13_robustness.csv", replace
