*==============================================================================
* 32_stacked_csdid.do -- minimum wage events and teen school-work status: the unit design of the paper in Stata.
*   Units: counties with their own minimum (CPS county code) and state remainders (state FIPS), as in
*   python/38_unit_panel.py; events and clean controls from data/raw/minwage/unit_events.csv; the same 70 events
*   as the paper (whole window inside January 2010 - December 2025).
*   (a) Cengiz-Dube-Lindner-Zipperer stacked regression on unit x month cells: event x unit and event x month
*       fixed effects, clustered by state, plus the wild cluster bootstrap (boottest) for the post x treated term
*   (b) Callaway-Sant'Anna csdid on the stacked cells (treated unit = cohort, clean controls = never treated)
*   (c) de Chaisemartin-D'Haultfoeuille did_multiplegt_dyn on the unit x month panel with the log minimum
*       wage as a continuous treatment (no event definition)
*   Packages: reghdfe ftools boottest csdid drdid did_multiplegt_dyn estout.  NOT EXECUTED for the current draft
*   (no Stata in the build environment); provided as a check on the Python estimates.
*==============================================================================
version 16
local outcomes "enrolled employed enr_emp enr_only emp_only neither log_wage"
local PRE = 36
local POST = 48

* ---- unit panel: which CPS counties are units -----------------------------------------------------
import delimited "$RAW/minwage/unit_mw_monthly.csv", clear varnames(1) encoding(utf8)
keep if kind == "county"
keep unit
duplicates drop
levelsof unit, local(county_units)

* ---- event list: the 70 events of the paper -------------------------------------------------------
import delimited "$RAW/minwage/unit_events.csv", clear varnames(1) encoding(utf8) bindquote(strict)
keep if pct_window >= 0.05 & event_ym >= "2013-01" & event_ym <= "2025-01"
gen ym_idx = real(substr(event_ym, 1, 4)) * 12 + real(substr(event_ym, 6, 2)) - 1
keep event_id unit state_fips ym_idx controls pct_window
tempfile events
save `events'
local N = _N

* ---- unit x month x age-band cell means ------------------------------------------------------------
use "$CLEAN/cps_monthly_1624.dta", clear
keep if inrange(age, 16, 19)
gen long geo = state_fips
foreach c of local county_units {
    replace geo = `c' if county == `c'
}
gen band = cond(age <= 17, 1, 2)
collapse (mean) `outcomes' (rawsum) n = weight (first) state_fips [pw = weight], by(geo ym band)
tempfile cells
save `cells'

* ---- stack: one block per event, treated unit + its clean control units, months -36..+47 -----------
tempfile stack
local first = 1
forvalues i = 1/`N' {
    use `events' in `i', clear
    local ev = event_id[1]
    local u = unit[1]
    local t0 = ym_idx[1]
    local ctrl = controls[1]
    use `cells', clear
    gen keep = geo == `u'
    foreach c of local ctrl {
        replace keep = 1 if geo == `c'
    }
    keep if keep & inrange(ym - `t0', -`PRE', `POST' - 1)
    gen event_id = `ev'
    gen treated = geo == `u'
    gen post = treated & ym >= `t0'
    gen rel = ym - `t0'
    gen relyear = floor(rel / 12)
    gen time = relyear + 4                    // 1..8 for csdid; event at time 4 (relative year 0)
    gen gvar = cond(treated, 4, 0)
    if `first' { save `stack', replace
                 local first = 0 }
    else { append using `stack'
           save `stack', replace }
}
use `stack', clear
egen eg = group(event_id geo)
egen et = group(event_id ym)
save "$CLEAN/mw_stacked_cells.dta", replace

* (a) stacked regression: (i) relative-year coefficients, base year -1; (ii) the single post x treated
*     coefficient of the paper's stacked tables, with analytic state clustering and the wild cluster bootstrap
foreach y of local outcomes {
    foreach b in 1 2 {
        reghdfe `y' ib3.time#1.treated [aw = n] if band == `b', absorb(eg et) cluster(state_fips)
        estimates store st_`y'_b`b'
        reghdfe `y' post [aw = n] if band == `b', absorb(eg et) cluster(state_fips)
        estimates store post_`y'_b`b'
        boottest post, cluster(state_fips) reps(999) seed(30) weighttype(rademacher) nograph
    }
}
esttab st_enrolled_b1 st_enrolled_b2 st_employed_b1 st_employed_b2 st_enr_emp_b1 st_enr_emp_b2 st_neither_b1 st_neither_b2 ///
    using "$TAB/t20_mw_stacked.tex", replace se star(* 0.10 ** 0.05 *** 0.01) booktabs keep(*treated*) ///
    mtitles("Enrolled 16-17" "Enrolled 18-19" "Employed 16-17" "Employed 18-19" "Enr&emp 16-17" "Enr&emp 18-19" "Neither 16-17" "Neither 18-19")
esttab post_enrolled_b1 post_enrolled_b2 post_employed_b1 post_employed_b2 post_enr_emp_b1 post_enr_emp_b2 post_neither_b1 post_neither_b2 post_log_wage_b1 post_log_wage_b2 ///
    using "$TAB/t20b_mw_stacked_post.tex", replace se star(* 0.10 ** 0.05 *** 0.01) booktabs keep(post)

* (b) csdid on the stacked cells: within each block the treated unit is cohort 4 and its clean controls are
*     never treated; event x unit is the panel unit, relative year the time; wild cluster bootstrap by state
foreach y of local outcomes {
    foreach b in 1 2 {
        preserve
        keep if band == `b'
        collapse (mean) `y' [aw = n], by(event_id geo state_fips eg time gvar)
        csdid `y' [iw = 1], ivar(eg) time(time) gvar(gvar) method(reg) cluster(state_fips) wboot rseed(30) reps(999)
        estat event, estore(cs_`y'_b`b')
        estat simple
        restore
    }
}
esttab cs_enrolled_b1 cs_enrolled_b2 cs_employed_b1 cs_employed_b2 ///
    using "$TAB/t21_mw_csdid.tex", replace se star(* 0.10 ** 0.05 *** 0.01) booktabs ///
    mtitles("Enrolled 16-17" "Enrolled 18-19" "Employed 16-17" "Employed 18-19")

* (c) continuous treatment: unit x month panel, log effective minimum of the unit, no events
import delimited "$RAW/minwage/unit_mw_monthly.csv", clear varnames(1) encoding(utf8)
gen ym_idx = real(substr(ym, 1, 4)) * 12 + real(substr(ym, 6, 2)) - 1
drop ym
rename ym_idx ym
rename unit geo
gen lmw = ln(mw)
keep geo ym lmw
tempfile mw
save `mw'
use `cells', clear
merge m:1 geo ym using `mw', keep(match) nogen
foreach y in enrolled employed neither log_wage {
    foreach b in 1 2 {
        did_multiplegt_dyn `y' geo ym lmw if band == `b', effects(4) placebo(3) cluster(state_fips) weight(n) continuous(1)
        graph export "$FIG/mw_dcdh_`y'_b`b'.png", replace width(1600)
    }
}
