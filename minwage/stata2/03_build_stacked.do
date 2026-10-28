*==============================================================================
* 03_build_stacked.do -- the stacked event file behind every event-study table and figure (all teens).
*   Step 1: collapse teens to unit x month x single-year-of-age cells (so any age range can be formed later).
*   Step 2: for each event keep its treated unit and its clean control units for the 84 months from 36 before
*           to 47 after the event month; stack the 70 blocks.
*   Output: data/clean/stacked2.dta   (one row per event x unit x month x age)
*           data/clean/cells2.dta     (the cells, reused by the robustness file)
*   To build the same file for a subgroup (income, sex, race, school months) run 03b_build_stacked_groups.do.
*==============================================================================
do "stata2/00_setup.do"

* ---- Step 1: cells ----
use "$CLEAN/cps2.dta", clear
keep if inrange(age, 16, 19)
local outcomes "enrolled employed inlf enr_emp enr_only emp_only neither dropout"
* person-weighted means of the school-work outcomes; n = sum of person weights
collapse (mean) `outcomes' (rawsum) n = weight (first) state_fips [pw = weight], by(geo ym age)
tempfile c1
save `c1'
* earnings-weighted means of the wage outcomes (outgoing rotation groups); nw = sum of earnings weights
use "$CLEAN/cps2.dta", clear
keep if inrange(age, 16, 19) & org == 1
collapse (mean) log_wage log_earnweek (rawsum) nw = earnwt [pw = earnwt], by(geo ym age)
merge 1:1 geo ym age using `c1', nogen
save "$CLEAN/cells2.dta", replace

* ---- Step 2: stack ----
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
    use "$CLEAN/cells2.dta", clear
    gen keep = geo == `u'                              // the treated unit
    foreach c of local ctrl {
        replace keep = 1 if geo == `c'                 // its clean control units
    }
    keep if keep & inrange(ym - `t0', -36, 47)
    drop keep
    gen event_id = `ev'
    gen treated  = geo == `u'
    gen rel      = ym - `t0'                           // months relative to the event month
    gen relyear  = floor(rel / 12)                     // -3..3; year -1 = the twelve months before the increase
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
drop if any_treated == 0                               // events whose treated unit has no CPS teens
drop any_treated
egen eg = group(event_id geo)                          // event x unit fixed effect
egen et = group(event_id ym)                           // event x month fixed effect
gen rk = relyear + 4                                   // 1..7; 3 is year -1, the base; factor variables need positive values
label define rk 1 "-3" 2 "-2" 3 "-1" 4 "0" 5 "1" 6 "2" 7 "3"
label values rk rk
gen band = cond(age <= 17, 1, 2)                       // 1 = 16-17, 2 = 18-19
compress
save "$CLEAN/stacked2.dta", replace
display "events in the stacked file:"
tab event_id if treated & rel == 0 & age == 16, nolabel
