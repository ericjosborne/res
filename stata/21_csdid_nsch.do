*==============================================================================
* 21_csdid_nsch.do -- PFML exposure at birth and parents' mental health, NSCH
*                     2016-2024 (docs/nsch_design.md).  Time = child's birth
*                     year; cohort = first birth year with >= 6 months of benefits.
*==============================================================================
version 16
use "$CLEAN/nsch_children.dta", clear
replace gvar = 0 if gvar > 2024
local xvars "i.survey_year i.child_age a1_age a1_married i.race4 fpl_lt200"

tempfile all
save `all'

* (a) mothers of children aged 0-5, pooled ages with survey-year and age adjustment
keep if mother == 1 & child_age <= 5
foreach y in a1_ment a1_ment_fairpoor a1_ment_excellent a1_phys parent_stress stress_any coping_notwell support a1_employed a1_fulltime {
    csdid `y' `xvars' [iw = weight], time(year) gvar(gvar) method(drimp) cluster(state_fips) wboot rseed(20260912) reps(999)
    estat simple, estore(ns_`y'_simple)
    estat group,  estore(ns_`y'_group)
    estat event, window(-5 5) estore(ns_`y'_event)
    estat pretrend
    csdid_plot, title("PFML at birth and mothers' `y' (NSCH, CS)") name(ns_`y', replace)
    graph export "$FIG/nsch_event_`y'.png", replace width(1600)
}

* (b) by child-age band (survey year fixed within band): 0-1, 2-3, 4-5
foreach band in "0 1" "2 3" "4 5" {
    tokenize `band'
    use `all', clear
    replace gvar = 0 if gvar > 2024
    keep if mother == 1 & inrange(child_age, `1', `2')
    csdid a1_ment i.survey_year a1_age a1_married i.race4 fpl_lt200 [iw = weight], time(year) gvar(gvar) method(drimp) cluster(state_fips) wboot rseed(21) reps(499)
    estat simple, estore(ns_band`1'`2')
}

* (c) fathers (respondent father, and second adult father)
use `all', clear
replace gvar = 0 if gvar > 2024
keep if father == 1 & child_age <= 5
csdid a1_ment `xvars' [iw = weight], time(year) gvar(gvar) method(drimp) cluster(state_fips) wboot rseed(22) reps(499)
estat simple, estore(ns_father_resp)
use `all', clear
replace gvar = 0 if gvar > 2024
keep if mother == 1 & a2_father == 1 & child_age <= 5
csdid a2_ment `xvars' [iw = weight], time(year) gvar(gvar) method(drimp) cluster(state_fips) wboot rseed(23) reps(499)
estat simple, estore(ns_father_a2)

* (d) placebo: parents of children born before the policy but surveyed after (ages 6-17)
use `all', clear
replace gvar = 0 if gvar > 2024
keep if mother == 1 & child_age >= 6
csdid a1_ment `xvars' [iw = weight], time(year) gvar(gvar) method(drimp) cluster(state_fips) wboot rseed(24) reps(499)
estat event, window(-5 5) estore(ns_placebo_older)

* (e) child outcomes and breastfeeding (0-5)
use `all', clear
replace gvar = 0 if gvar > 2024
keep if mother == 1 & child_age <= 5
foreach y in child_fairpoor prev_visit everbf bf_ge26wk {
    csdid `y' `xvars' [iw = weight], time(year) gvar(gvar) method(drimp) cluster(state_fips) wboot rseed(25) reps(499)
    estat simple, estore(ns_`y'_simple)
}

* (f) heterogeneity
foreach v in fpl_lt200 a1_married race4 a1_educ3 {
    levelsof `v', local(L)
    foreach l of local L {
        use `all', clear
        replace gvar = 0 if gvar > 2024
        keep if mother == 1 & child_age <= 5 & `v' == `l'
        csdid a1_ment i.survey_year i.child_age a1_age [iw = weight], time(year) gvar(gvar) method(drimp) cluster(state_fips) wboot rseed(26) reps(299)
        estat simple, estore(ns_het_`v'_`l')
    }
}

esttab ns_a1_ment_simple ns_a1_ment_fairpoor_simple ns_a1_ment_excellent_simple ns_a1_phys_simple ns_parent_stress_simple ns_a1_employed_simple ///
    using "$TAB/t11_nsch_simple.tex", replace se star(* 0.10 ** 0.05 *** 0.01) booktabs ///
    mtitles("Mental health 1-5" "Fair/poor" "Excellent" "Physical 1-5" "Parenting stress" "Employed") ///
    title("PFML exposure at birth and mothers' health, NSCH 2016-2024, children 0-5")
esttab ns_band01 ns_band23 ns_band45 ns_father_resp ns_father_a2 ns_placebo_older ///
    using "$TAB/t12_nsch_bands_fathers.tex", replace se star(* 0.10 ** 0.05 *** 0.01) booktabs ///
    mtitles("Age 0-1" "Age 2-3" "Age 4-5" "Fathers (resp.)" "Fathers (A2)" "Placebo 6-17")

* (g) robustness: base period g-2 (births in g-1 can still take bonding leave in g), not-yet-treated controls,
*     birth year = survey year minus age everywhere, pandemic surveys dropped
use `all', clear
replace gvar = 0 if gvar > 2024
keep if mother == 1 & child_age <= 5
csdid a1_ment `xvars' [iw = weight], time(year) gvar(gvar) method(drimp) cluster(state_fips) wboot rseed(27) reps(499) anticipation(1)
estat simple, estore(ns_rob_ant1)
csdid a1_ment `xvars' [iw = weight], time(year) gvar(gvar) method(drimp) cluster(state_fips) wboot rseed(28) reps(499) notyet
estat simple, estore(ns_rob_notyet)
csdid a1_ment `xvars' [iw = weight], time(birth_year_ya) gvar(gvar) method(drimp) cluster(state_fips) wboot rseed(29) reps(499)
estat simple, estore(ns_rob_ya)
csdid a1_ment `xvars' [iw = weight] if !inlist(survey_year, 2020, 2021), time(year) gvar(gvar) method(drimp) cluster(state_fips) wboot rseed(30) reps(499)
estat simple, estore(ns_rob_nopandemic)
esttab ns_a1_ment_simple ns_rob_ant1 ns_rob_notyet ns_rob_ya ns_rob_nopandemic ///
    using "$TAB/t13_nsch_robustness.tex", replace se star(* 0.10 ** 0.05 *** 0.01) booktabs ///
    mtitles("Main" "Base g-2" "Not-yet controls" "Year minus age" "No 2020-21 surveys")
