*==============================================================================
* fig07_wage_by_age.do -- Figure 7: event-time effects on the log hourly wage of hourly-paid teens, by age.
*   Same estimator as fig03; the wage cells are earnings-weighted (nw) and come from the outgoing rotation groups.
*   Input: data/clean/stacked2.dta.  Output: output/stata2/fig07_wage_by_age.png
*==============================================================================
do "stata2/00_setup.do"
use "$CLEAN/stacked2.dta", clear
tempfile coefs
postfile P str20 ages int k double b double se using `coefs', replace
foreach a in 1 2 3 {
    local cond = cond(`a' == 3, "1", "band == `a'")
    reghdfe log_wage ib3.rk#i.treated [aw = nw] if `cond', absorb(eg et) cluster(state_fips)
    forvalues k = 1/7 {
        if `k' == 3 {
            post P ("`a'") (-1) (0) (0)
        }
        else {
            post P ("`a'") (`k' - 4) (_b[`k'.rk#1.treated]) (_se[`k'.rk#1.treated])
        }
    }
}
postclose P
use `coefs', clear
destring ages, replace
gen lo = b - 1.96 * se
gen hi = b + 1.96 * se
gen kk = k + 0.15 * (ages - 2)
twoway (rcap lo hi kk if ages == 1, lcolor(navy))   (scatter b kk if ages == 1, mcolor(navy)) ///
       (rcap lo hi kk if ages == 2, lcolor(maroon)) (scatter b kk if ages == 2, mcolor(maroon)) ///
       (rcap lo hi kk if ages == 3, lcolor(green))  (scatter b kk if ages == 3, mcolor(green)), ///
    yline(0) xline(-0.5, lcolor(gs12)) xlabel(-3(1)3) xtitle("Years relative to the increase (base: year -1)") ///
    ytitle("Effect on log hourly wage") legend(order(2 "Ages 16-17" 4 "Ages 18-19" 6 "Ages 16-19 (pooled)") rows(1)) ///
    title("Teen wages, 70 events: event-time effects, 95% intervals", size(small))
graph export "$OUT/fig07_wage_by_age.png", replace width(2000)
