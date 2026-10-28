*==============================================================================
* tab12_stacked_controls_wage_race.do -- Table 12: stacked DiD with controls, wages and earnings, by race.
*   As tab02, restricted to each subgroup in turn (the subgroup flags are in the fine-cell file: lowses/highses from
*   the income category, female/male, white = non-Hispanic white).  Wage outcomes use the earnings weight nw.
*   Input: data/clean/stacked_fine2.dta.  Output: output/stata2/tab12_stacked_controls_wage_race.csv
*==============================================================================
do "stata2/00_setup.do"
use "$CLEAN/stacked_fine2.dta", clear
gen male = 1 - female
gen nonwhite = 1 - white

tempfile res
postfile P str20 outcome str10 grp str10 ages double b double se long cells using `res', replace
foreach g in white nonwhite {
    foreach y in log_wage log_earnweek {
        foreach a in 1 2 3 {
            local cond = cond(`a' == 3, "`g' == 1", "`g' == 1 & band == `a'")
            reghdfe `y' post [aw = nw] if `cond', absorb(eg et age female race4 finc) cluster(state_fips)
            post P ("`y'") ("`g'") ("`a'") (_b[post]) (_se[post]) (e(N))
        }
    }
}
postclose P
use `res', clear
replace ages = cond(ages == "1", "16-17", cond(ages == "2", "18-19", "16-19"))
gen stars = cond(abs(b/se) > 2.576, "***", cond(abs(b/se) > 1.96, "**", cond(abs(b/se) > 1.645, "*", "")))
format b se %8.4f
list outcome grp ages b se stars cells, sepby(outcome) noobs
export delimited using "$OUT/tab12_stacked_controls_wage_race.csv", replace
