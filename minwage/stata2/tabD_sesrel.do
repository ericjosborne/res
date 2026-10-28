*==============================================================================
* tabD_sesrel.do -- Appendix D (Tables 33-34, Figure 14): the income split at the within-year weighted median
*   income category instead of the nominal $50,000.  Build the two stacked files first:
*       do "stata2/03b_build_stacked_groups.do" lowsesrel
*       do "stata2/03b_build_stacked_groups.do" highsesrel
*   Then this file gives post-event averages (shares and wages) and the pooled-age event-study figure.
*   Output: output/stata2/tabD_sesrel.csv, fig14_groups_sesrel.png
*==============================================================================
do "stata2/00_setup.do"
tempfile res coefs
postfile P str12 grp str20 outcome str10 ages double post double se double pre using `res', replace
postfile C str12 grp str20 outcome int k double b double se using `coefs', replace
foreach g in lowsesrel highsesrel {
    use "$CLEAN/stacked2_`g'.dta", clear
    foreach y in enr_emp enr_only emp_only neither enrolled employed log_wage log_earnweek {
        local w = cond(strpos("`y'", "log_") == 1, "nw", "n")
        foreach a in 1 2 3 {
            local cond = cond(`a' == 3, "1", "band == `a'")
            reghdfe `y' ib3.rk#i.treated [aw = `w'] if `cond', absorb(eg et) cluster(state_fips)
            lincom (_b[4.rk#1.treated] + _b[5.rk#1.treated] + _b[6.rk#1.treated] + _b[7.rk#1.treated]) / 4
            local post = r(estimate)
            local se = r(se)
            lincom (_b[1.rk#1.treated] + _b[2.rk#1.treated]) / 2
            post P ("`g'") ("`y'") ("`a'") (`post') (`se') (r(estimate))
            if `a' == 3 & inlist("`y'", "enr_emp", "enr_only", "emp_only", "neither") {
                forvalues k = 1/7 {
                    if `k' == 3 {
                        post C ("`g'") ("`y'") (-1) (0) (0)
                    }
                    else {
                        post C ("`g'") ("`y'") (`k' - 4) (_b[`k'.rk#1.treated]) (_se[`k'.rk#1.treated])
                    }
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
export delimited using "$OUT/tabD_sesrel.csv", replace
use `coefs', clear
gen lo = b - 1.96 * se
gen hi = b + 1.96 * se
gen kk = k + cond(grp == "lowsesrel", -0.1, 0.1)
local i = 0
foreach y in enr_emp enr_only emp_only neither {
    local ++i
    twoway (rcap lo hi kk if outcome == "`y'" & grp == "lowsesrel", lcolor(navy)) (scatter b kk if outcome == "`y'" & grp == "lowsesrel", mcolor(navy)) ///
           (rcap lo hi kk if outcome == "`y'" & grp == "highsesrel", lcolor(maroon)) (scatter b kk if outcome == "`y'" & grp == "highsesrel", mcolor(maroon)), ///
        yline(0) xline(-0.5, lcolor(gs12)) xlabel(-3(1)3) title("`y'", size(medsmall)) ///
        xtitle("Years relative to the increase") ytitle("Effect (share)") legend(order(2 "Below median" 4 "At or above median") rows(1) size(small)) name(p`i', replace)
}
grc1leg p1 p2 p3 p4, cols(2) title("School-work status by family income, within-year median split, ages 16-19", size(small))
graph export "$OUT/fig14_groups_sesrel.png", replace width(2000)
