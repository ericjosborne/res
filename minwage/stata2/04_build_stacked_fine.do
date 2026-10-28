*==============================================================================
* 04_build_stacked_fine.do -- the stacked file for the regressions WITH individual controls (Tables 2-12).
*   Cells are unit x month x age x sex x race/ethnicity x family-income category.  A regression on these cells,
*   weighted by cell size, with the cell categories as fixed effects, is numerically the person-level regression
*   with those dummies (the regressors are constant within a cell).  Takes longer than 03: the file has ~13 million rows.
*   Output: data/clean/stacked_fine2.dta
*==============================================================================
do "stata2/00_setup.do"

use "$CLEAN/cps2.dta", clear
keep if inrange(age, 16, 19)
local outcomes "enrolled employed enr_emp enr_only emp_only neither"
preserve
    keep if org == 1
    collapse (mean) log_wage log_earnweek (rawsum) nw = earnwt [pw = earnwt], by(geo ym age female race4 finc)
    tempfile cw
    save `cw'
restore
collapse (mean) `outcomes' (rawsum) n = weight (first) state_fips [pw = weight], by(geo ym age female race4 finc)
merge 1:1 geo ym age female race4 finc using `cw', nogen
tempfile cells
save `cells'

use "$CLEAN/events2.dta", clear
local N = _N
tempfile stack
local first = 1
forvalues i = 1/`N' {
    use "$CLEAN/events2.dta" in `i', clear
    local ev   = event_id[1]
    local u    = unit[1]
    local t0   = ym[1]
    local ctrl = controls[1]
    use `cells', clear
    gen keep = geo == `u'
    foreach c of local ctrl {
        replace keep = 1 if geo == `c'
    }
    keep if keep & inrange(ym - `t0', -36, 47)
    drop keep
    gen int event_id = `ev'
    gen byte treated = geo == `u'
    gen byte post    = treated * (ym >= `t0')
    if `first' {
        save `stack', replace
        local first = 0
    }
    else {
        append using `stack'
        save `stack', replace
    }
}
use `stack', clear
bysort event_id: egen any_treated = max(treated)
drop if any_treated == 0
drop any_treated
egen long eg = group(event_id geo)
egen long et = group(event_id ym)
gen byte band    = cond(age <= 17, 1, 2)
gen byte lowses  = finc <= 740
gen byte highses = inrange(finc, 820, 899)
gen byte white   = race4 == 1
compress
save "$CLEAN/stacked_fine2.dta", replace
