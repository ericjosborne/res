*==============================================================================
* tabQ_quartiles.do -- family income quartiles: the income split in four within-year weighted quartiles of the
*   CPS family income category among 16-19 year olds (missing income excluded).  Build the four stacked files first:
*       do "stata2/03b_build_stacked_groups.do" q1        (and q2, q3, q4)
*   Then this file gives, for every quartile, the post-event average (years 0-3) and pre average (years -3,-2)
*   for the school-work shares and wages, and the pooled-age event-study figures.
*   Output: output/stata2/tabQ_quartiles.csv, figQ_groups.png, figQ_wage.png
*==============================================================================
do "stata2/00_setup.do"
tempfile res coefs
postfile P str12 grp str20 outcome str10 ages double post double se double pre using `res', replace
postfile C str12 grp str20 outcome str10 ages int k double b double se using `coefs', replace
foreach g in q1 q2 q3 q4 {
    use "$CLEAN/stacked2_`g'.dta", clear
    foreach y in enr_emp enr_only emp_only neither enrolled employed log_wage {
        local w = cond(strpos("`y'", "log_") == 1, "nw", "n")
        foreach a in 1 2 3 {
            local cond = cond(`a' == 3, "1", "band == `a'")
            * relative-year dummies interacted with treated; rk = relative year + 4, so rk = 3 is year -1 (the base)
            reghdfe `y' ib3.rk#i.treated [aw = `w'] if `cond', absorb(eg et) cluster(state_fips)
            lincom (_b[4.rk#1.treated] + _b[5.rk#1.treated] + _b[6.rk#1.treated] + _b[7.rk#1.treated]) / 4
            local post = r(estimate)
            local se = r(se)
            lincom (_b[1.rk#1.treated] + _b[2.rk#1.treated]) / 2
            post P ("`g'") ("`y'") ("`a'") (`post') (`se') (r(estimate))
            forvalues k = 1/7 {
                if `k' == 3 {
                    post C ("`g'") ("`y'") ("`a'") (-1) (0) (0)
                }
                else {
                    post C ("`g'") ("`y'") ("`a'") (`k' - 4) (_b[`k'.rk#1.treated]) (_se[`k'.rk#1.treated])
                }
            }
        }
    }
}
postclose P
postclose C
use `res', clear
replace ages = cond(ages == "1", "16-17", cond(ages == "2", "18-19", "16-19"))
format post se pre %8.4f
list grp outcome ages post se pre, sepby(outcome) noobs
export delimited using "$OUT/tabQ_quartiles.csv", replace

* ---- figures: four quartiles side by side, pooled ages 16-19 ----
use `coefs', clear
keep if ages == "3"
gen lo = b - 1.96 * se
gen hi = b + 1.96 * se
gen off = cond(grp == "q1", -0.24, cond(grp == "q2", -0.08, cond(grp == "q3", 0.08, 0.24)))
gen kk = k + off
local i = 0
foreach y in enr_emp enr_only emp_only neither {
    local ++i
    twoway (rcap lo hi kk if outcome == "`y'" & grp == "q1", lcolor(navy))    (scatter b kk if outcome == "`y'" & grp == "q1", mcolor(navy)) ///
           (rcap lo hi kk if outcome == "`y'" & grp == "q2", lcolor(maroon))  (scatter b kk if outcome == "`y'" & grp == "q2", mcolor(maroon)) ///
           (rcap lo hi kk if outcome == "`y'" & grp == "q3", lcolor(forest_green)) (scatter b kk if outcome == "`y'" & grp == "q3", mcolor(forest_green)) ///
           (rcap lo hi kk if outcome == "`y'" & grp == "q4", lcolor(orange))  (scatter b kk if outcome == "`y'" & grp == "q4", mcolor(orange)), ///
        yline(0) xline(-0.5, lcolor(gs12)) xlabel(-3(1)3) title("`y'", size(medsmall)) ///
        xtitle("Years relative to the increase") ytitle("Effect (share)") ///
        legend(order(2 "Bottom quarter" 4 "Second quarter" 6 "Third quarter" 8 "Top quarter") rows(1) size(small)) name(p`i', replace)
}
grc1leg p1 p2 p3 p4, cols(2) title("School-work status by family income quartile (within-year), ages 16-19", size(small))
graph export "$OUT/figQ_groups.png", replace width(2000)
twoway (rcap lo hi kk if outcome == "log_wage" & grp == "q1", lcolor(navy))    (scatter b kk if outcome == "log_wage" & grp == "q1", mcolor(navy)) ///
       (rcap lo hi kk if outcome == "log_wage" & grp == "q2", lcolor(maroon))  (scatter b kk if outcome == "log_wage" & grp == "q2", mcolor(maroon)) ///
       (rcap lo hi kk if outcome == "log_wage" & grp == "q3", lcolor(forest_green)) (scatter b kk if outcome == "log_wage" & grp == "q3", mcolor(forest_green)) ///
       (rcap lo hi kk if outcome == "log_wage" & grp == "q4", lcolor(orange))  (scatter b kk if outcome == "log_wage" & grp == "q4", mcolor(orange)), ///
    yline(0) xline(-0.5, lcolor(gs12)) xlabel(-3(1)3) title("Log hourly wage by family income quartile, ages 16-19", size(medsmall)) ///
    xtitle("Years relative to the increase") ytitle("Effect (log points)") ///
    legend(order(2 "Bottom quarter" 4 "Second quarter" 6 "Third quarter" 8 "Top quarter") rows(1) size(small))
graph export "$OUT/figQ_wage.png", replace width(2000)
