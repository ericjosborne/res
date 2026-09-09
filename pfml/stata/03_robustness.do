*==============================================================================
* 03_robustness.do -- alternative estimators, comparison groups and
*                     sensitivity to parallel-trends violations.
*==============================================================================
version 16
use "$CLEAN/cps_women_1844_monthly.dta", clear
gen gvar = gvar_year
replace gvar = 0 if gvar > 2024
local xvars "i.agegrp married black hispanic other college"

*---------------------------------------------------------------- (a) not-yet-treated controls
preserve
keep if mother_lt6 == 1
csdid inlf `xvars' [iw = wtfinl], time(year) gvar(gvar) method(drimp) cluster(statefip) wboot rseed(2) notyet
estat event, window(-6 6) estore(rb_notyet)
restore

*---------------------------------------------------------------- (b) triple difference
* Mothers of under-6s vs women 18-44 without children in the same state-year.
* Implemented as CS on the within-state-year difference of cell means.
use "$CLEAN/cps_cells_yearly.dta", clear
keep if inlist(mother_lt6, 0, 1) & mother_lt6 == 1 | (mother == 0)
gen grp = cond(mother_lt6 == 1, 1, 0)
collapse (mean) inlf employed hours [pw = n], by(statefip year gvar_year grp)
reshape wide inlf employed hours, i(statefip year gvar_year) j(grp)
gen d_inlf = inlf1 - inlf0
gen d_employed = employed1 - employed0
gen d_hours = hours1 - hours0
gen gvar = gvar_year
replace gvar = 0 if gvar > 2024
csdid d_inlf, ivar(statefip) time(year) gvar(gvar) method(reg) cluster(statefip) wboot rseed(3)
estat event, window(-6 6) estore(rb_ddd_inlf)
csdid_plot, title("Triple difference: mothers of under-6s minus childless women") name(ddd, replace)
graph export "$FIG/event_ddd_inlf.png", replace width(1600)

*---------------------------------------------------------------- (c) other estimators on the state-year cell panel
use "$CLEAN/cps_cells_yearly.dta", clear
keep if mother_lt6 == 1
gen gvar = gvar_year
replace gvar = 0 if gvar > 2024
gen ever = gvar > 0
gen rel = year - gvar if ever
gen treat = ever & year >= gvar

* Borusyak-Jaravel-Spiess imputation
did_imputation inlf statefip year gvar [aw = n], allhorizons pretrends(6) cluster(statefip)
estimates store rb_bjs

* Sun & Abraham
gen never = gvar == 0
forvalues k = 6(-1)2 { gen lead`k' = rel == -`k' if ever ; replace lead`k' = 0 if !ever }
forvalues k = 0/6     { gen lag`k'  = rel == `k'  if ever ; replace lag`k'  = 0 if !ever }
eventstudyinteract inlf lead6-lead2 lag0-lag6 [aw = n], cohort(gvar) control_cohort(never) ///
    absorb(i.statefip i.year) vce(cluster statefip)
estimates store rb_sa

* de Chaisemartin & D'Haultfoeuille
did_multiplegt_dyn inlf statefip year treat, effects(6) placebo(6) cluster(statefip) weight(n)

* Two-way fixed effects for reference (biased under heterogeneous effects)
reghdfe inlf treat [aw = n], absorb(statefip year) vce(cluster statefip)
estimates store rb_twfe

*---------------------------------------------------------------- (d) Honest DiD (Rambachan & Roth 2023)
* Uses the CS event-study coefficients stored in 02_csdid.do (cs_inlf_event).
estimates restore cs_inlf_event
honestdid, pre(1/5) post(7/12) mvec(0(0.01)0.05) coefplot
graph export "$FIG/honestdid_inlf.png", replace width(1600)

*---------------------------------------------------------------- (e) alternative cohort timing
use "$CLEAN/cps_women_1844_monthly.dta", clear
keep if mother_lt6 == 1
gen gvar = gvar_full
replace gvar = 0 if gvar > 2024
csdid inlf `xvars' [iw = wtfinl], time(year) gvar(gvar) method(drimp) cluster(statefip) wboot rseed(4)
estat event, window(-6 6) estore(rb_fullyear)

*---------------------------------------------------------------- (f) placebo group: women 18-44 without children
use "$CLEAN/cps_women_1844_monthly.dta", clear
keep if mother == 0
gen gvar = gvar_year
replace gvar = 0 if gvar > 2024
csdid inlf `xvars' [iw = wtfinl], time(year) gvar(gvar) method(drimp) cluster(statefip) wboot rseed(5)
estat event, window(-6 6) estore(rb_placebo_childless)
