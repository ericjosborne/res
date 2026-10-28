*==============================================================================
* tab02_stacked_controls.do -- Table 2: stacked difference-in-differences with individual controls, all teens.
*   For each outcome and age group: regress the cell mean on post x treated, with event x unit and event x month
*   fixed effects AND fixed effects for age, sex, race/ethnicity and family-income category, weighted by cell size,
*   clustered by state.  Because the cells are unit x month x age x sex x race x income, this equals the
*   person-level regression with those dummies.  The coefficient is the post-event average effect.
*   Input: data/clean/stacked_fine2.dta (04_build_stacked_fine.do).  Output: output/stata2/tab02_stacked_controls.csv
*   The same file with a different KEEP line gives Tables 3, 4, 5 (see tab03_, tab04_, tab05_).
*==============================================================================
do "stata2/00_setup.do"
use "$CLEAN/stacked_fine2.dta", clear

tempfile res
postfile P str20 outcome str10 ages double b double se long cells using `res', replace
foreach y in enr_emp enr_only emp_only neither enrolled employed {
    foreach a in 1 2 3 {
        local cond = cond(`a' == 3, "1", "band == `a'")
        reghdfe `y' post [aw = n] if `cond', absorb(eg et age female race4 finc) cluster(state_fips)
        post P ("`y'") ("`a'") (_b[post]) (_se[post]) (e(N))
    }
}
postclose P
use `res', clear
replace ages = cond(ages == "1", "16-17", cond(ages == "2", "18-19", "16-19"))
gen stars = cond(abs(b/se) > 2.576, "***", cond(abs(b/se) > 1.96, "**", cond(abs(b/se) > 1.645, "*", "")))
format b se %8.4f
list outcome ages b se stars cells, sepby(outcome) noobs
export delimited using "$OUT/tab02_stacked_controls.csv", replace
