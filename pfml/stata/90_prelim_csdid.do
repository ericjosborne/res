*==============================================================================
* 90_prelim_csdid.do -- preliminary Callaway-Sant'Anna estimates on the CPS
*                       ASEC 2021-23 file built by pfml/python/01_build_cps_sample.py
*                       (pfml/data/clean/cps_women_1844.dta, Stata 16 format).
*
* Mirrors pfml/python/02_csdid_prelim.py: same sample restrictions, never-
* treated controls, no covariates (method(reg) with no X equals the cell-mean
* estimator), varying base period, state-clustered wild bootstrap.
* Point estimates should equal those in pfml/output/tables/prelim_*.csv.
*==============================================================================
version 16
use "$CLEAN/cps_women_1844.dta", clear

* window 2020-2022; drop cohorts treated before the window; recode not-yet-treated to never
drop if inlist(gvar, 2004, 2009, 2014, 2018, 2020)
gen g = gvar
replace g = 0 if g > 2022
label var g "PFML cohort (2021 = MA, 2022 = CT, 0 = never/not-yet)"
tab g year [iw = weight] if mother_lt6 == 1

tempfile all
save `all'

foreach s in mother_lt6 mother childless {
    use `all', clear
    if "`s'" == "mother_lt6"  keep if mother_lt6 == 1
    if "`s'" == "mother"      keep if mother == 1
    if "`s'" == "childless"   keep if mother == 0
    foreach y in worked hours fulltime {
        * repeated cross sections: no ivar(); csdid accepts iweights (use [pw=] if your version rejects iw)
        csdid `y' [iw = weight], time(year) gvar(g) method(reg) cluster(state_fips) ///
            wboot rseed(20260909) reps(999)
        estat simple, estore(p_`s'_`y'_simple)
        estat event,  estore(p_`s'_`y'_event)
        estat group,  estore(p_`s'_`y'_group)
        estat pretrend
        if "`s'" == "mother_lt6" & "`y'" == "worked" {
            csdid_plot, title("PFML and mothers' employment: MA 2021, CT 2022") name(pre_ev, replace)
            graph export "$FIG/prelim_event_worked_stata.png", replace width(1600)
        }
    }
}

esttab p_mother_lt6_worked_simple p_mother_lt6_hours_simple p_mother_lt6_fulltime_simple ///
       p_childless_worked_simple p_childless_hours_simple ///
    using "$TAB/prelim_cs_simple_stata.tex", replace se star(* 0.10 ** 0.05 *** 0.01) booktabs ///
    mtitles("Worked" "Hours" "Full time" "Placebo: worked" "Placebo: hours") ///
    title("Preliminary simple ATT, CPS ASEC 2021-23, never-treated controls")
esttab p_mother_lt6_worked_event p_mother_lt6_hours_event p_childless_worked_event ///
    using "$TAB/prelim_cs_event_stata.tex", replace se star(* 0.10 ** 0.05 *** 0.01) booktabs ///
    mtitles("Worked" "Hours" "Placebo: worked") title("Preliminary event study")
