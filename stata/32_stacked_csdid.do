*==============================================================================
* 32_stacked_csdid.do -- minimum wage events and teen enrollment: stacked event design
*   (a) Cengiz-Dube-Lindner-Zipperer stacked regression: event x state and event x time effects
*   (b) csdid on the stacked file (treated cohort = event, clean controls), wild cluster bootstrap by state
*   (c) de Chaisemartin-D'Haultfoeuille did_multiplegt_dyn on the state-month panel with log minimum wage
* Events and clean controls come from data/raw/minwage/mw_events.csv (python/31_build_mw_events.py).
*==============================================================================
version 16
local outcomes "enrolled enr_hs employed enr_emp enr_only emp_only neither hours log_wage"
local PRE = 36
local POST = 48

* ---- event list ---------------------------------------------------------------
import delimited "$RAW/minwage/mw_events.csv", clear varnames(1) encoding(utf8) bindquote(strict)
keep if federal_induced == 0 & event_ym >= "2010-01"
gen ym_idx = real(substr(event_ym, 1, 4)) * 12 + real(substr(event_ym, 6, 2)) - 1
keep event_id state_fips ym_idx controls pct_window
tempfile events
save `events'
local N = _N

* ---- state x month x age-band cell means (fast: the stacked regressions run on cells) --------
use "$CLEAN/cps_monthly_1624.dta", clear
keep if inrange(age, 16, 19)
gen band = cond(age <= 17, 1, 2)
collapse (mean) `outcomes' (rawsum) n = weight [pw = weight], by(state_fips ym band)
tempfile cells
save `cells'

* ---- stack --------------------------------------------------------------------
tempfile stack
local first = 1
forvalues i = 1/`N' {
    use `events' in `i', clear
    local ev = event_id[1]
    local st = state_fips[1]
    local t0 = ym_idx[1]
    local ctrl = controls[1]
    use `cells', clear
    gen keep = state_fips == `st'
    foreach c of local ctrl {
        replace keep = 1 if state_fips == `c'
    }
    keep if keep & inrange(ym - `t0', -`PRE', `POST' - 1)
    gen event_id = `ev'
    gen treated = state_fips == `st'
    gen rel = ym - `t0'
    gen relyear = floor(rel / 12)
    gen time = relyear + 4                    // 1..8 for csdid; event at time 4
    gen gvar = cond(treated, 4, 0)
    if `first' { save `stack', replace
                 local first = 0 }
    else { append using `stack'
           save `stack', replace }
}
use `stack', clear
egen es = group(event_id state_fips)
egen et = group(event_id ym)
save "$CLEAN/mw_stacked_cells.dta", replace

* (a) stacked regression, Cengiz et al.: relative-year dummies interacted with treated, base year -1
foreach y of local outcomes {
    foreach b in 1 2 {
        reghdfe `y' ib3.time#1.treated [aw = n] if band == `b', absorb(es et) cluster(state_fips)
        estimates store st_`y'_b`b'
    }
}
esttab st_enrolled_b1 st_enrolled_b2 st_employed_b1 st_employed_b2 st_enr_emp_b1 st_enr_emp_b2 st_neither_b1 st_neither_b2 ///
    using "$TAB/t20_mw_stacked.tex", replace se star(* 0.10 ** 0.05 *** 0.01) booktabs keep(*treated*) ///
    mtitles("Enrolled 16-17" "Enrolled 18-19" "Employed 16-17" "Employed 18-19" "Enr&emp 16-17" "Enr&emp 18-19" "Neither 16-17" "Neither 18-19")

* (b) csdid on the stacked cells: every event's treated state is cohort 4, its clean controls are never-treated
*     within the event block; event x state is the unit, event x relative year the time
foreach y of local outcomes {
    foreach b in 1 2 {
        preserve
        keep if band == `b'
        collapse (mean) `y' [aw = n], by(event_id state_fips es time gvar)
        csdid `y' [iw = 1], ivar(es) time(time) gvar(gvar) method(reg) cluster(state_fips) wboot rseed(30) reps(999)
        estat event, estore(cs_`y'_b`b')
        estat simple
        restore
    }
}
esttab cs_enrolled_b1 cs_enrolled_b2 cs_employed_b1 cs_employed_b2 ///
    using "$TAB/t21_mw_csdid.tex", replace se star(* 0.10 ** 0.05 *** 0.01) booktabs ///
    mtitles("Enrolled 16-17" "Enrolled 18-19" "Employed 16-17" "Employed 18-19")

* (c) continuous treatment: state x month panel, log effective minimum wage
import delimited "$RAW/minwage/state_mw_monthly.csv", clear varnames(1)
gen ym_idx = real(substr(ym, 1, 4)) * 12 + real(substr(ym, 6, 2)) - 1
drop ym
rename ym_idx ym
gen lmw = ln(mw)
tempfile mw
save `mw'
use `cells', clear
merge m:1 state_fips ym using `mw', keep(match) nogen
foreach b in 1 2 {
    did_multiplegt_dyn enrolled state_fips ym lmw if band == `b', effects(4) placebo(3) cluster(state_fips) weight(n) continuous(1)
    graph export "$FIG/mw_dcdh_enrolled_b`b'.png", replace width(1600)
}
