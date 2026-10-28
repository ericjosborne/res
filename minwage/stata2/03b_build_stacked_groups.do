*==============================================================================
* 03b_build_stacked_groups.do -- the stacked file for a subgroup of teens.  Same steps as 03, on a subset.
*   Usage:  do "stata2/03b_build_stacked_groups.do" lowses      (one word: the group name below)
*   Groups: lowses highses female male white nonwhite lowsesrel highsesrel school
*           school_lowses school_highses school_lowsesrel school_highsesrel (school months x income, for the dropout table)
*           lowses/highses  = family income below / at or above $50,000 (missing excluded)
*           lowsesrel/highsesrel = below / at or above the weighted median income category among 16-19 year olds
*                                  in the same survey year
*           school          = September-May only (used for the dropout outcome and the school-months check)
*   Output: data/clean/stacked2_<group>.dta
*==============================================================================
do "stata2/00_setup.do"
local g "`1'"
if "`g'" == "" {
    display as error "give a group name, e.g.  do stata2/03b_build_stacked_groups.do lowses"
    exit 198
}

use "$CLEAN/cps2.dta", clear
keep if inrange(age, 16, 19)

* ---- the within-year median income split needs the median first ----
if inlist("`g'", "lowsesrel", "highsesrel") {
    gen medcat = .
    forvalues y = 2010/2025 {
        quietly _pctile faminc [pw = weight] if year == `y' & faminc < 900, p(50)
        quietly replace medcat = r(r1) if year == `y'
    }
    gen lowsesrel  = faminc < medcat if faminc < 900
    gen highsesrel = faminc >= medcat if faminc < 900
}
gen male     = 1 - female
gen nonwhite = 1 - white
gen school   = inlist(month, 1, 2, 3, 4, 5, 9, 10, 11, 12)

if strpos("`g'", "school_") == 1 {
    local g2 = subinstr("`g'", "school_", "", 1)
    keep if school == 1 & `g2' == 1                    // school months x income group
}
else {
    keep if `g' == 1                                   // the subgroup
}

* ---- cells (as in 03) ----
local outcomes "enrolled employed inlf enr_emp enr_only emp_only neither dropout"
preserve
    keep if org == 1
    collapse (mean) log_wage log_earnweek (rawsum) nw = earnwt [pw = earnwt], by(geo ym age)
    tempfile cw
    save `cw'
restore
collapse (mean) `outcomes' (rawsum) n = weight (first) state_fips [pw = weight], by(geo ym age)
merge 1:1 geo ym age using `cw', nogen
tempfile cells
save `cells'

* ---- stack (as in 03) ----
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
    gen event_id = `ev'
    gen treated  = geo == `u'
    gen rel      = ym - `t0'
    gen relyear  = floor(rel / 12)
    gen post     = treated * (rel >= 0)
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
egen eg = group(event_id geo)
egen et = group(event_id ym)
gen rk = relyear + 4
label define rk 1 "-3" 2 "-2" 3 "-1" 4 "0" 5 "1" 6 "2" 7 "3"
label values rk rk
gen band = cond(age <= 17, 1, 2)
compress
save "$CLEAN/stacked2_`g'.dta", replace
