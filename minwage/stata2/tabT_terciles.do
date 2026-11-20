*==============================================================================
* tabT_terciles.do -- family income terciles: the income split in three within-year weighted terciles (low / middle / upper third) of the
*   CPS family income category among 16-19 year olds (missing income excluded).  Build the four stacked files first:
*       do "stata2/03b_build_stacked_groups.do" t1        (and t2, t3)
*   Then this file gives, for every tercile, the post-event average (years 0-3) and pre average (years -3,-2)
*   for the school-work shares and wages, and the pooled-age event-study figures.
*   Output: output/stata2/tabT_terciles.csv, figT_groups.png, figT_wage.png
*==============================================================================
do "stata2/00_setup.do"
tempfile res coefs
postfile P str12 grp str20 outcome str10 ages double post double se double pre using `res', replace
postfile C str12 grp str20 outcome str10 ages int k double b double se using `coefs', replace
foreach g in t1 t2 t3 {
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
export delimited using "$OUT/tabT_terciles.csv", replace

* ---- figures: three terciles side by side, pooled ages 16-19 ----
use `coefs', clear
keep if ages == "3"
gen lo = b - 1.96 * se
gen hi = b + 1.96 * se
gen off = cond(grp == "t1", -0.18, cond(grp == "t2", 0, 0.18))
gen kk = k + off
local i = 0
foreach y in enr_emp enr_only emp_only neither {
    local ++i
    twoway (rcap lo hi kk if outcome == "`y'" & grp == "t1", lcolor(navy))    (scatter b kk if outcome == "`y'" & grp == "t1", mcolor(navy)) ///
           (rcap lo hi kk if outcome == "`y'" & grp == "t2", lcolor(maroon))  (scatter b kk if outcome == "`y'" & grp == "t2", mcolor(maroon)) ///
           (rcap lo hi kk if outcome == "`y'" & grp == "t3", lcolor(forest_green)) (scatter b kk if outcome == "`y'" & grp == "t3", mcolor(forest_green)), ///
        yline(0) xline(-0.5, lcolor(gs12)) xlabel(-3(1)3) title("`y'", size(medsmall)) ///
        xtitle("Years relative to the increase") ytitle("Effect (share)") ///
        legend(order(2 "Low income" 4 "Middle income" 6 "Upper income") rows(1) size(small)) name(p`i', replace)
}
grc1leg p1 p2 p3 p4, cols(2) title("School-work status by family income tercile (within-year), ages 16-19", size(small))
graph export "$OUT/figT_groups.png", replace width(2000)
twoway (rcap lo hi kk if outcome == "log_wage" & grp == "t1", lcolor(navy))    (scatter b kk if outcome == "log_wage" & grp == "t1", mcolor(navy)) ///
       (rcap lo hi kk if outcome == "log_wage" & grp == "t2", lcolor(maroon))  (scatter b kk if outcome == "log_wage" & grp == "t2", mcolor(maroon)) ///
       (rcap lo hi kk if outcome == "log_wage" & grp == "t3", lcolor(forest_green)) (scatter b kk if outcome == "log_wage" & grp == "t3", mcolor(forest_green)), ///
    yline(0) xline(-0.5, lcolor(gs12)) xlabel(-3(1)3) title("Log hourly wage by family income tercile, ages 16-19", size(medsmall)) ///
    xtitle("Years relative to the increase") ytitle("Effect (log points)") ///
    legend(order(2 "Low income" 4 "Middle income" 6 "Upper income") rows(1) size(small))
graph export "$OUT/figT_wage.png", replace width(2000)
