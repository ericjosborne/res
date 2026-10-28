*==============================================================================
* fig05_groups_sex.do -- Figure 5: four school-work shares by sex, ages 16-19.
*   Same estimator as fig03, run separately on the two subgroup stacked files (03b_build_stacked_groups.do female / male).
*   Inputs: data/clean/stacked2_female.dta, data/clean/stacked2_male.dta.  Output: output/stata2/fig05_groups_sex.png
*==============================================================================
do "stata2/00_setup.do"
tempfile coefs
postfile P str30 outcome str20 grp int k double b double se using `coefs', replace
foreach g in female male {
    use "$CLEAN/stacked2_`g'.dta", clear
    foreach y in enr_emp enr_only emp_only neither {
        reghdfe `y' ib3.rk#i.treated [aw = n], absorb(eg et) cluster(state_fips)       // pooled ages 16-19
        forvalues k = 1/7 {
            if `k' == 3 {
                post P ("`y'") ("`g'") (-1) (0) (0)
            }
            else {
                post P ("`y'") ("`g'") (`k' - 4) (_b[`k'.rk#1.treated]) (_se[`k'.rk#1.treated])
            }
        }
    }
}
postclose P
use `coefs', clear
gen lo = b - 1.96 * se
gen hi = b + 1.96 * se
gen kk = k + cond(grp == "female", -0.1, 0.1)
local i = 0
foreach y in enr_emp enr_only emp_only neither {
    local ++i
    local ttl : word `i' of "Enrolled_and_employed" "Enrolled_only" "Employed_only" "Neither"
    local ttl = subinstr("`ttl'", "_", " ", .)
    twoway (rcap lo hi kk if outcome == "`y'" & grp == "female", lcolor(navy))   (scatter b kk if outcome == "`y'" & grp == "female", mcolor(navy)) ///
           (rcap lo hi kk if outcome == "`y'" & grp == "male", lcolor(maroon)) (scatter b kk if outcome == "`y'" & grp == "male", mcolor(maroon)), ///
        yline(0) xline(-0.5, lcolor(gs12)) xlabel(-3(1)3) title("`ttl'", size(medsmall)) ///
        xtitle("Years relative to the increase (base: year -1)") ytitle("Effect (share)") ///
        legend(order(2 "Girls" 4 "Boys") rows(1) size(small)) name(p`i', replace)
}
grc1leg p1 p2 p3 p4, cols(2) title("Figure 5: four school-work shares by sex, ages 16-19, 95% intervals", size(small))
graph export "$OUT/fig05_groups_sex.png", replace width(2000)
