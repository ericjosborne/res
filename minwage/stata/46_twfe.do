*==============================================================================
* 46_twfe.do -- two-way fixed effects regressions on the log minimum wage (the Neumark-Shupe 2019 /
*   Smith 2021 specification), the regression counterpart reported before each event-study figure.
*   Mirrors python/46_regressions.py: teens 16-19 observed from January 2010, unit = county with its own
*   minimum (city rate applied to the county) or state remainder, unit and year-month fixed effects,
*   controls for single year of age, sex, race and Hispanic origin, survey weights, clustered by state.
*   Coefficient on ln(mw) = effect of a 100 log-point rise; x 0.32 for the average event (38 percent).
* Requires the unit panel data/raw/minwage/unit_mw_monthly.csv (python/38_unit_panel.py) and reghdfe.
*==============================================================================
version 16

* ---- unit-month panel of effective minimums --------------------------------------------------
import delimited "$RAW/minwage/unit_mw_monthly.csv", clear varnames(1) encoding(utf8)
gen ymi = real(substr(ym, 1, 4)) * 12 + real(substr(ym, 6, 2)) - 1
gen byte county_unit = kind == "county"
keep unit ymi mw county_unit
rename unit geo
drop ym
tempfile umw
save `umw'
levelsof geo if county_unit, local(county_units)

* ---- teens, 2010 on, assigned to their unit -----------------------------------------------------
use "$CLEAN/cps_monthly_1624.dta", clear
keep if inrange(age, 16, 19) & year >= 2010
gen long geo = state_fips
foreach c of local county_units {
    replace geo = `c' if county == `c'
}
rename ym ymi
merge m:1 geo ymi using `umw', keep(match) nogenerate
gen log_mw = ln(mw)

* ---- regressions: one per outcome x age bracket -------------------------------------------------
local outcomes "enr_emp enr_only emp_only neither enrolled employed log_wage log_earnweek"
eststo clear
foreach y of local outcomes {
    * wages and earnings are outgoing-rotation outcomes with earnings weights
    local w = cond(strpos("`y'", "log_") == 1, "earnwt", "weight")
    foreach a in "16 17" "18 19" "16 19" {
        local a0 : word 1 of `a'
        local a1 : word 2 of `a'
        eststo twfe_`y'_`a0'`a1': ///
            reghdfe `y' log_mw i.age female black hispanic if inrange(age, `a0', `a1') [aw = `w'], ///
                absorb(geo ymi) cluster(state_fips)
    }
}
esttab twfe_* using "$TAB/mw_twfe.csv", replace csv keep(log_mw) b(4) se(4) star(* 0.10 ** 0.05 *** 0.01) ///
    stats(N, fmt(%9.0fc)) mtitles

* ---- by family income: below vs at or above $50,000 (nominal CPS category) ----------------------
gen byte lowses  = faminc <= 740
gen byte highses = inrange(faminc, 820, 899)
eststo clear
foreach g in lowses highses {
    foreach y of local outcomes {
        local w = cond(strpos("`y'", "log_") == 1, "earnwt", "weight")
        foreach a in "16 17" "18 19" "16 19" {
            local a0 : word 1 of `a'
            local a1 : word 2 of `a'
            eststo `g'_`y'_`a0'`a1': ///
                reghdfe `y' log_mw i.age female black hispanic if inrange(age, `a0', `a1') & `g' [aw = `w'], ///
                    absorb(geo ymi) cluster(state_fips)
        }
    }
}
esttab lowses_* highses_* using "$TAB/mw_twfe_ses.csv", replace csv keep(log_mw) b(4) se(4) ///
    star(* 0.10 ** 0.05 *** 0.01) stats(N, fmt(%9.0fc)) mtitles

* ---- the unit-linear-trend variant (reported in a footnote only: trends absorb a trending treatment)
gen t = ymi - 2010 * 12
reghdfe neither log_mw i.age female black hispanic if inrange(age, 16, 17) [aw = weight], ///
    absorb(geo ymi geo#c.t) cluster(state_fips)
