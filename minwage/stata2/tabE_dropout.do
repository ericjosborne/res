*==============================================================================
* tabE_dropout.do -- Appendix Table 35: high school dropout (not enrolled, no diploma or GED), September-May,
*   ages 16-17, 18-19, 16-18 and 16-19, for all teens and by family income (nominal and within-year median).
*   Build the stacked files first:
*       do "stata2/03b_build_stacked_groups.do" school
*       do "stata2/03b_build_stacked_groups.do" school_lowses        (and school_highses, school_lowsesrel, school_highsesrel)
*   The last column of the paper's table (all months) comes from stacked2.dta.
*   Output: output/stata2/tabE_dropout.csv
*==============================================================================
do "stata2/00_setup.do"
tempfile res
postfile P str20 sample str10 ages double post double se double pre using `res', replace
foreach s in school school_lowses school_highses school_lowsesrel school_highsesrel allmonths {
    local f = cond("`s'" == "allmonths", "stacked2.dta", "stacked2_`s'.dta")
    use "$CLEAN/`f'", clear
    foreach a in "16 17" "18 19" "16 18" "16 19" {
        local a0 : word 1 of `a'
        local a1 : word 2 of `a'
        reghdfe dropout ib3.rk#i.treated [aw = n] if inrange(age, `a0', `a1'), absorb(eg et) cluster(state_fips)
        lincom (_b[4.rk#1.treated] + _b[5.rk#1.treated] + _b[6.rk#1.treated] + _b[7.rk#1.treated]) / 4
        local post = r(estimate)
        local se = r(se)
        lincom (_b[1.rk#1.treated] + _b[2.rk#1.treated]) / 2
        post P ("`s'") ("`a0'-`a1'") (`post') (`se') (r(estimate))
    }
}
postclose P
use `res', clear
format post se pre %8.4f
list sample ages post se pre, sepby(sample) noobs
export delimited using "$OUT/tabE_dropout.csv", replace
