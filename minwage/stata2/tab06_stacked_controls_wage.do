*==============================================================================
* tab06_stacked_controls_wage.do -- Table 6: stacked DiD with controls, log hourly wage and log weekly earnings, all teens.
*   As tab02 with the wage outcomes, weighted by the earnings weight nw (outgoing rotation groups).
*   Input: data/clean/stacked_fine2.dta.  Output: output/stata2/tab06_stacked_controls_wage.csv
*==============================================================================
do "stata2/00_setup.do"
use "$CLEAN/stacked_fine2.dta", clear
tempfile res
postfile P str20 outcome str10 ages double b double se long cells using `res', replace
foreach y in log_wage log_earnweek {
    foreach a in 1 2 3 {
        local cond = cond(`a' == 3, "1", "band == `a'")
        reghdfe `y' post [aw = nw] if `cond', absorb(eg et age female race4 finc) cluster(state_fips)
        post P ("`y'") ("`a'") (_b[post]) (_se[post]) (e(N))
    }
}
postclose P
use `res', clear
replace ages = cond(ages == "1", "16-17", cond(ages == "2", "18-19", "16-19"))
gen stars = cond(abs(b/se) > 2.576, "***", cond(abs(b/se) > 1.96, "**", cond(abs(b/se) > 1.645, "*", "")))
format b se %8.4f
list outcome ages b se stars cells, sepby(outcome) noobs
export delimited using "$OUT/tab06_stacked_controls_wage.csv", replace
