*==============================================================================
* 11_csdid_brfss.do -- Callaway & Sant'Anna estimates of PFML effects on
*                      mental health, BRFSS 1993-2024.
* Main sample: women 18-44 with children in the household; outcomes: days of
* poor mental health (0-30), frequent mental distress (>= 14 days), general
* health fair/poor, physical health days.  Placebos: childless women; men
* without children.  Robustness: not-yet-treated controls, monthly cohorts,
* drop the 2010-2011 survey redesign, women 18-34 with children.
*==============================================================================
version 16
use "$CLEAN/brfss_adults_1844.dta", clear
replace gvar = 0 if gvar > 2024
local xvars "i.agegrp married i.race4 i.educ3"

tempfile all
save `all'

* (a) main: mothers
keep if mother == 1
foreach y in mentdays fmd fairpoor physdays employed {
    csdid `y' `xvars' [iw = weight], time(year) gvar(gvar) method(drimp) cluster(state_fips) wboot rseed(20260910) reps(999)
    estat simple,   estore(mh_`y'_simple)
    estat group,    estore(mh_`y'_group)
    estat calendar, estore(mh_`y'_cal)
    estat event, window(-8 8) estore(mh_`y'_event)
    estat pretrend
    csdid_plot, title("PFML and mothers' `y' (BRFSS, CS, never-treated controls)") name(mh_`y', replace)
    graph export "$FIG/brfss_event_`y'.png", replace width(1600)
}

* (b) placebos
foreach s in "female == 1 & parent == 0" "female == 0 & parent == 0" {
    use `all', clear
    replace gvar = 0 if gvar > 2024
    keep if `s'
    local tag = cond("`s'" == "female == 1 & parent == 0", "childless_w", "childless_m")
    csdid mentdays `xvars' [iw = weight], time(year) gvar(gvar) method(drimp) cluster(state_fips) wboot rseed(11) reps(499)
    estat event, window(-8 8) estore(mh_pl_`tag')
}

* (c) robustness
use `all', clear
replace gvar = 0 if gvar > 2024
keep if mother == 1
csdid mentdays `xvars' [iw = weight], time(year) gvar(gvar) method(drimp) cluster(state_fips) wboot rseed(12) reps(499) notyet
estat event, window(-8 8) estore(mh_rb_notyet)
csdid mentdays `xvars' [iw = weight] if !inlist(survey_year, 2010, 2011), time(year) gvar(gvar) method(drimp) cluster(state_fips) wboot rseed(13) reps(499)
estat event, window(-8 8) estore(mh_rb_no1011)
csdid mentdays `xvars' [iw = weight] if mother_young == 1, time(year) gvar(gvar) method(drimp) cluster(state_fips) wboot rseed(14) reps(499)
estat event, window(-8 8) estore(mh_rb_young)
* monthly cohorts (interview month), event window +-24 months
replace gvar_month = 0 if gvar_month > 2024 * 12 + 12
csdid mentdays `xvars' [iw = weight], time(ym) gvar(gvar_month) method(drimp) cluster(state_fips) wboot rseed(15) reps(299) notyet
estat event, window(-24 24) estore(mh_rb_monthly)

* (d) heterogeneity: income, marital status, race
foreach v in inc_lt25k married race4 educ3 {
    levelsof `v', local(L)
    foreach l of local L {
        use `all', clear
        replace gvar = 0 if gvar > 2024
        keep if mother == 1 & `v' == `l'
        csdid mentdays i.agegrp [iw = weight], time(year) gvar(gvar) method(drimp) cluster(state_fips) wboot rseed(16) reps(299)
        estat simple, estore(mh_het_`v'_`l')
    }
}

esttab mh_mentdays_simple mh_fmd_simple mh_fairpoor_simple mh_physdays_simple mh_employed_simple ///
    using "$TAB/t9_brfss_simple.tex", replace se star(* 0.10 ** 0.05 *** 0.01) booktabs ///
    mtitles("Mental health days" "Frequent distress" "Fair/poor health" "Physical days" "Employed") ///
    title("PFML and mothers' health, BRFSS 1993-2024, never-treated controls, drimp")
esttab mh_mentdays_event mh_pl_childless_w mh_pl_childless_m mh_rb_notyet mh_rb_no1011 mh_rb_young ///
    using "$TAB/t10_brfss_event.tex", replace se star(* 0.10 ** 0.05 *** 0.01) booktabs ///
    mtitles("Mothers" "Childless women" "Childless men" "Not-yet controls" "Drop 2010-11" "Mothers 18-34")
