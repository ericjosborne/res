*==============================================================================
* tab01_means.do -- Table 1: means in the twelve months before the event, event units vs their clean controls,
*   pooled over the 70 events, for ages 16-17, 18-19 and 16-19.
*   Input: data/clean/cps2.dta, data/clean/events2.dta.  Output: output/stata2/tab01_means.tex
*==============================================================================
do "stata2/00_setup.do"
use "$CLEAN/cps2.dta", clear
keep if inrange(age, 16, 19)
gen band = cond(age <= 17, 1, 2)
tempfile teens
save `teens'

* build the pre-event sample: for each event, its treated unit (group 1) and its controls (group 0), months -12..-1
use "$CLEAN/events2.dta", clear
local N = _N
tempfile pre
local first = 1
forvalues i = 1/`N' {
    use "$CLEAN/events2.dta" in `i', clear
    local u = unit[1]
    local t0 = ym[1]
    local ctrl = controls[1]
    use `teens', clear
    keep if inrange(ym - `t0', -12, -1)
    gen grp = .
    replace grp = 1 if geo == `u'
    foreach c of local ctrl {
        replace grp = 0 if geo == `c'
    }
    keep if !missing(grp)
    if `first' {
        save `pre', replace
        local first = 0
    }
    else {
        append using `pre'
        save `pre', replace
    }
}
use `pre', clear
gen hourwage = exp(log_wage)                            // hourly-paid ORG workers only (missing otherwise)
gen allages = 1
* one column per (age group, grp): weighted means
local vars "enrolled employed inlf enr_emp enr_only emp_only neither hourwage female black hispanic"
eststo clear
foreach b in 1 2 {
    eststo t`b': estpost summarize `vars' [aw = weight] if band == `b' & grp == 1
    eststo c`b': estpost summarize `vars' [aw = weight] if band == `b' & grp == 0
}
eststo t3: estpost summarize `vars' [aw = weight] if grp == 1
eststo c3: estpost summarize `vars' [aw = weight] if grp == 0
esttab t1 c1 t2 c2 t3 c3 using "$OUT/tab01_means.tex", replace cells("mean(fmt(3))") booktabs nonumber ///
    mtitles("Event 16-17" "Control 16-17" "Event 18-19" "Control 18-19" "Event 16-19" "Control 16-19") ///
    title("Means in the year before the event, 70 unit events: event units and clean controls") noobs
* note: the hourly wage mean uses person weights here; the paper uses earnings weights for that row.
