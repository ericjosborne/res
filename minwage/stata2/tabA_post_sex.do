*==============================================================================
* tabA_post_sex.do -- Appendix Tables 19-20 and Table 9: post-event averages by sex (girls / boys).
*   Post = mean of the relative-year coefficients for years 0..3 (relative to year -1); Pre = mean for years -3, -2.
*   Both come from the stacked event-study regression (as in fig03), via lincom.  School-work outcomes use the
*   person weight n; wage outcomes the earnings weight nw.
*   Inputs: data/clean/stacked2_female.dta stacked2_male.dta.  Output: output/stata2/tabA_post_sex.csv
*==============================================================================
do "stata2/00_setup.do"
tempfile res
postfile P str20 grp str20 outcome str10 ages double post double se double pre using `res', replace
foreach g in female male {
    local f = cond("`g'" == "all", "stacked2.dta", "stacked2_`g'.dta")
    use "$CLEAN/`f'", clear
    foreach y in enr_emp enr_only emp_only neither enrolled employed log_wage log_earnweek {
        local w = cond(strpos("`y'", "log_") == 1, "nw", "n")
        foreach a in 1 2 3 {
            local cond = cond(`a' == 3, "1", "band == `a'")
            reghdfe `y' ib3.rk#i.treated [aw = `w'] if `cond', absorb(eg et) cluster(state_fips)
            lincom (_b[4.rk#1.treated] + _b[5.rk#1.treated] + _b[6.rk#1.treated] + _b[7.rk#1.treated]) / 4
            local post = r(estimate)
            local se   = r(se)
            lincom (_b[1.rk#1.treated] + _b[2.rk#1.treated]) / 2
            post P ("`g'") ("`y'") ("`a'") (`post') (`se') (r(estimate))
        }
    }
}
postclose P
use `res', clear
replace ages = cond(ages == "1", "16-17", cond(ages == "2", "18-19", "16-19"))
gen stars = cond(abs(post/se) > 2.576, "***", cond(abs(post/se) > 1.96, "**", cond(abs(post/se) > 1.645, "*", "")))
format post se pre %8.4f
list grp outcome ages post se stars pre, sepby(outcome) noobs
export delimited using "$OUT/tabA_post_sex.csv", replace
