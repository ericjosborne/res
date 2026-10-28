*==============================================================================
* fig03_groups_by_age.do -- Figure 3: event-time effects on the four school-work shares, by age (16-17, 18-19, pooled).
*   Estimator: stacked regression of the cell mean on relative-year dummies x treated, with event x unit and
*   event x month fixed effects, weighted by cell population, clustered by state; year -1 is the base.
*   (The paper's figures use the equivalent difference-in-means form with a state block bootstrap; the two agree closely.)
*   Input: data/clean/stacked2.dta.  Output: output/stata2/fig03_groups_by_age.png
*==============================================================================
do "stata2/00_setup.do"
use "$CLEAN/stacked2.dta", clear

* ---- collect the seven relative-year coefficients for each outcome and age group ----
tempfile coefs
postfile P str30 outcome str20 ages int k double b double se using `coefs', replace
foreach y in enr_emp enr_only emp_only neither {
    foreach a in 1 2 3 {                                                   // 1 = 16-17, 2 = 18-19, 3 = pooled
        local cond = cond(`a' == 3, "1", "band == `a'")
        reghdfe `y' ib3.rk#i.treated [aw = n] if `cond', absorb(eg et) cluster(state_fips)
        forvalues k = 1/7 {
            if `k' == 3 {
                post P ("`y'") ("`a'") (-1) (0) (0)                        // base year
            }
            else {
                post P ("`y'") ("`a'") (`k' - 4) (_b[`k'.rk#1.treated]) (_se[`k'.rk#1.treated])
            }
        }
    }
}
postclose P

* ---- plot: one panel per outcome, three series offset slightly so the intervals do not overlap ----
use `coefs', clear
destring ages, replace
gen lo = b - 1.96 * se
gen hi = b + 1.96 * se
gen kk = k + 0.15 * (ages - 2)
local i = 0
foreach y in enr_emp enr_only emp_only neither {
    local ++i
    local ttl : word `i' of "Enrolled_and_employed" "Enrolled_only" "Employed_only" "Neither"
    local ttl = subinstr("`ttl'", "_", " ", .)
    twoway (rcap lo hi kk if outcome == "`y'" & ages == 1, lcolor(navy))   (scatter b kk if outcome == "`y'" & ages == 1, mcolor(navy)) ///
           (rcap lo hi kk if outcome == "`y'" & ages == 2, lcolor(maroon)) (scatter b kk if outcome == "`y'" & ages == 2, mcolor(maroon)) ///
           (rcap lo hi kk if outcome == "`y'" & ages == 3, lcolor(green))  (scatter b kk if outcome == "`y'" & ages == 3, mcolor(green)), ///
        yline(0) xline(-0.5, lcolor(gs12)) xlabel(-3(1)3) title("`ttl'", size(medsmall)) ///
        xtitle("Years relative to the increase (base: year -1)") ytitle("Effect (share)") ///
        legend(order(2 "Ages 16-17" 4 "Ages 18-19" 6 "Ages 16-19 (pooled)") rows(1) size(small)) name(p`i', replace)
}
grc1leg p1 p2 p3 p4, cols(2) title("School-work status, 70 events: event-time effects by age, 95% intervals", size(small))
graph export "$OUT/fig03_groups_by_age.png", replace width(2000)
* (grc1leg is a user-written command for a shared legend: ssc install grc1leg.  If unavailable, use: graph combine p1 p2 p3 p4, cols(2))
