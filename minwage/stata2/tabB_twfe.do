*==============================================================================
* tabB_twfe.do -- Appendix Tables 24-31: two-way fixed effects regressions on the log minimum wage, school months.
*   Person-level regression: y on ln(effective minimum of the teen's unit), with unit and year-month fixed effects,
*   dummies for single year of age, sex, race and Hispanic origin, survey weights (earnings weights for wages),
*   clustered by state.  The coefficient is the effect of a 100 log-point rise; multiply by 0.32 for the average event.
*   Sample: September-May (the enrollment item records summer school in June-August; see tabB_twfe_diag.do).
*   Groups: all teens, by family income, by sex, by race.
*   Inputs: data/clean/cps2.dta, data/clean/mwpanel2.dta.  Output: output/stata2/tabB_twfe.csv
*==============================================================================
do "stata2/00_setup.do"
use "$CLEAN/cps2.dta", clear
keep if inrange(age, 16, 19) & inlist(month, 1, 2, 3, 4, 5, 9, 10, 11, 12)
merge m:1 geo ym using "$CLEAN/mwpanel2.dta", keep(match) nogen keepusing(log_mw)
gen all = 1
gen male = 1 - female
gen nonwhite = 1 - white
gen band = cond(age <= 17, 1, 2)

tempfile res
postfile P str10 grp str20 outcome str10 ages double b double se long nobs using `res', replace
foreach g in all lowses highses female male white nonwhite {
    foreach y in enr_emp enr_only emp_only neither enrolled employed log_wage log_earnweek {
        local w = cond(strpos("`y'", "log_") == 1, "earnwt", "weight")
        foreach a in 1 2 3 {
            local cond = cond(`a' == 3, "`g' == 1", "`g' == 1 & band == `a'")
            reghdfe `y' log_mw i.age female black hispanic [aw = `w'] if `cond', absorb(geo ym) cluster(state_fips)
            post P ("`g'") ("`y'") ("`a'") (_b[log_mw]) (_se[log_mw]) (e(N))
        }
    }
}
postclose P
use `res', clear
replace ages = cond(ages == "1", "16-17", cond(ages == "2", "18-19", "16-19"))
gen stars = cond(abs(b/se) > 2.576, "***", cond(abs(b/se) > 1.96, "**", cond(abs(b/se) > 1.645, "*", "")))
format b se %8.4f
list grp outcome ages b se stars nobs, sepby(grp outcome) noobs
export delimited using "$OUT/tabB_twfe.csv", replace
