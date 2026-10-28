*==============================================================================
* tab13b_state_design.do -- the state design (states as units, local minimums ignored): the "state design" row of
*   Table 13 and the appendix Figures 11-12 (first stage; enrollment and employment).
*   Events and controls come from the state event list (data/raw/minwage/mw_events.csv) with the same window rule.
*   Input: data/clean/cps2.dta.  Outputs: output/stata2/tab13b_state_design.csv, fig11_state_firststage.png, fig12_state_enr_emp.png
*==============================================================================
do "stata2/00_setup.do"

* ---- state events ----
import delimited "$MW/mw_events.csv", clear varnames(1) encoding(utf8) bindquote(strict)
gen ym = real(substr(event_ym, 1, 4)) * 12 + real(substr(event_ym, 6, 2)) - 1
keep if federal_induced == 0 & pct_window >= 0.05 & event_ym >= "2013-01" & event_ym <= "2025-01"
gen event_id = _n
keep event_id state_fips ym controls
tempfile events
save `events'
local N = _N

* ---- state x month x age cells (every teen at the state rate) ----
use "$CLEAN/cps2.dta", clear
keep if inrange(age, 16, 19)
gen geo = state_fips
preserve
    keep if org == 1
    collapse (mean) log_wage (rawsum) nw = earnwt [pw = earnwt], by(geo ym age)
    tempfile cw
    save `cw'
restore
collapse (mean) enrolled employed neither (rawsum) n = weight (first) state_fips [pw = weight], by(geo ym age)
merge 1:1 geo ym age using `cw', nogen
tempfile cells
save `cells'

* ---- stack ----
tempfile stack
local first = 1
forvalues i = 1/`N' {
    use `events' in `i', clear
    local ev = event_id[1]
    local u = state_fips[1]
    local t0 = ym[1]
    local ctrl = controls[1]
    use `cells', clear
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
egen eg = group(event_id geo)
egen et = group(event_id ym)
gen rk = relyear + 4
gen band = cond(age <= 17, 1, 2)
tab event_id if treated & relyear == 0 & age == 16, nolabel      // the state events used

* ---- post-event averages (the Table 13 row) and event-time coefficients (Figures 11-12) ----
tempfile res coefs
postfile P str12 outcome int band double post double se using `res', replace
postfile C str12 outcome int band int k double b double se using `coefs', replace
foreach y in log_wage enrolled employed neither {
    local w = cond("`y'" == "log_wage", "nw", "n")
    foreach b in 1 2 {
        reghdfe `y' ib3.rk#i.treated [aw = `w'] if band == `b', absorb(eg et) cluster(state_fips)
        lincom (_b[4.rk#1.treated] + _b[5.rk#1.treated] + _b[6.rk#1.treated] + _b[7.rk#1.treated]) / 4
        post P ("`y'") (`b') (r(estimate)) (r(se))
        forvalues k = 1/7 {
            if `k' == 3 {
                post C ("`y'") (`b') (-1) (0) (0)
            }
            else {
                post C ("`y'") (`b') (`k' - 4) (_b[`k'.rk#1.treated]) (_se[`k'.rk#1.treated])
            }
        }
    }
}
postclose P
postclose C
use `res', clear
format post se %8.4f
list, noobs
export delimited using "$OUT/tab13b_state_design.csv", replace
use `coefs', clear
gen lo = b - 1.96 * se
gen hi = b + 1.96 * se
gen kk = k + 0.15 * (band - 1.5)
twoway (rcap lo hi kk if outcome == "log_wage" & band == 1, lcolor(navy)) (scatter b kk if outcome == "log_wage" & band == 1, mcolor(navy)) ///
       (rcap lo hi kk if outcome == "log_wage" & band == 2, lcolor(maroon)) (scatter b kk if outcome == "log_wage" & band == 2, mcolor(maroon)), ///
    yline(0) xline(-0.5, lcolor(gs12)) xlabel(-3(1)3) legend(order(2 "Ages 16-17" 4 "Ages 18-19")) ///
    xtitle("Years relative to the increase") ytitle("Effect on log hourly wage") title("State design: first stage", size(small))
graph export "$OUT/fig11_state_firststage.png", replace width(2000)
local i = 0
foreach y in enrolled employed {
    local ++i
    twoway (rcap lo hi kk if outcome == "`y'" & band == 1, lcolor(navy)) (scatter b kk if outcome == "`y'" & band == 1, mcolor(navy)) ///
           (rcap lo hi kk if outcome == "`y'" & band == 2, lcolor(maroon)) (scatter b kk if outcome == "`y'" & band == 2, mcolor(maroon)), ///
        yline(0) xline(-0.5, lcolor(gs12)) xlabel(-3(1)3) legend(order(2 "Ages 16-17" 4 "Ages 18-19")) ///
        xtitle("Years relative to the increase") ytitle("Effect (share)") title("`y'", size(small)) name(q`i', replace)
}
grc1leg q1 q2, cols(2) title("State design: enrollment and employment", size(small))
graph export "$OUT/fig12_state_enr_emp.png", replace width(2000)
