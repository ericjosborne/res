*==============================================================================
* fig10_wage_race.do -- Figure 10: log hourly wage by race and age.
*   Same estimator as fig07, on the two subgroup stacked files; one panel per age group.
*   Inputs: data/clean/stacked2_white.dta, data/clean/stacked2_nonwhite.dta.  Output: output/stata2/fig10_wage_race.png
*==============================================================================
do "stata2/00_setup.do"
tempfile coefs
postfile P str20 grp str20 ages int k double b double se using `coefs', replace
foreach g in white nonwhite {
    use "$CLEAN/stacked2_`g'.dta", clear
    foreach a in 1 2 3 {
        local cond = cond(`a' == 3, "1", "band == `a'")
        reghdfe log_wage ib3.rk#i.treated [aw = nw] if `cond', absorb(eg et) cluster(state_fips)
        forvalues k = 1/7 {
            if `k' == 3 {
                post P ("`g'") ("`a'") (-1) (0) (0)
            }
            else {
                post P ("`g'") ("`a'") (`k' - 4) (_b[`k'.rk#1.treated]) (_se[`k'.rk#1.treated])
            }
        }
    }
}
postclose P
use `coefs', clear
destring ages, replace
gen lo = b - 1.96 * se
gen hi = b + 1.96 * se
gen kk = k + cond(grp == "white", -0.1, 0.1)
foreach a in 1 2 3 {
    local ttl : word `a' of "Ages_16-17" "Ages_18-19" "Ages_16-19_(pooled)"
    local ttl = subinstr("`ttl'", "_", " ", .)
    twoway (rcap lo hi kk if ages == `a' & grp == "white", lcolor(navy))   (scatter b kk if ages == `a' & grp == "white", mcolor(navy)) ///
           (rcap lo hi kk if ages == `a' & grp == "nonwhite", lcolor(maroon)) (scatter b kk if ages == `a' & grp == "nonwhite", mcolor(maroon)), ///
        yline(0) xline(-0.5, lcolor(gs12)) xlabel(-3(1)3) title("`ttl'", size(medsmall)) ///
        xtitle("Years relative to the increase (base: year -1)") ytitle("Effect on log hourly wage") ///
        legend(order(2 "White" 4 "Non-white") rows(1) size(small)) name(p`a', replace)
}
grc1leg p1 p2 p3, cols(3) title("Figure 10: log hourly wage by race and age, 95% intervals", size(small))
graph export "$OUT/fig10_wage_race.png", replace width(2200)
