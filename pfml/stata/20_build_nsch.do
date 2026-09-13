*==============================================================================
* 20_build_nsch.do -- NSCH 2016-2024 topical files to the analysis file
*                     (mirrors python/20_build_nsch.py; see data/raw/NSCH_SPEC.md).
*==============================================================================
version 16
tempfile acc
local first = 1
forvalues y = 2016/2024 {
    * Census names the Stata files nsch_YYYYe_topical.dta (the label do-file is nsch_YYYY_topical.do)
    local f "$RAW/nsch/nsch_`y'e_topical.dta"
    capture confirm file "`f'"
    if _rc local f "$RAW/nsch/nsch_`y'_topical.dta"
    capture confirm file "`f'"
    if _rc {
        display as text "skip `y'"
        continue
    }
    use "`f'", clear
    rename *, lower
    gen survey_year = `y'
    * variables that exist only in some years: BIRTH_YR/BIRTH_MO 2019+, A1_EMPLOYED 2020-22, A1_EMPLOYED_R 2023+, K6Q20 to 2022
    foreach v in birth_yr birth_mo a1_employed a1_employed_r k6q20 k6q41r_still {
        capture confirm variable `v'
        if _rc gen `v' = .
    }
    replace a1_employed = a1_employed_r if missing(a1_employed)
    keep survey_year fipsst fwc stratum hhid sc_age_years sc_sex birth_yr birth_mo a1_relation a1_sex a1_age a1_marital a1_employed a1_grade ///
         a1_menthealth a1_physhealth a2_relation a2_sex a2_menthealth a2_physhealth k8q30 k8q31 k8q32 k8q34 k8q35 ///
         k2q01 k4q20r k6q20 k6q40 k6q41r_still breastfedend_mo_s breastfedend_wk_s breastfedend_day_s fpl_i1-fpl_i6 sc_race_r sc_hispanic_r currcov
    if `first' { save `acc', replace
                 local first = 0 }
    else { append using `acc'
           save `acc', replace }
}
use `acc', clear
rename (fipsst fwc sc_age_years) (state_fips weight child_age)
gen birth_year_ya = survey_year - child_age              // survey year minus age: overstates birth year for ~38% of children
gen birth_year = cond(missing(birth_yr), birth_year_ya, birth_yr)   // reported birth year from 2019
gen birth_month = birth_mo
gen year = birth_year
gen mother = a1_relation == 1 & a1_sex == 2
gen father = a1_relation == 1 & a1_sex == 1
gen a2_father = a2_relation == 1 & a2_sex == 1
gen a1_married = a1_marital == 1 if !missing(a1_marital)
gen a1_fulltime = a1_employed == 1 if !missing(a1_employed)                 // 1 FT, 2 PT, 3 without pay, 4 looking, 5 not looking, 6 retired
replace a1_employed = inlist(a1_employed, 1, 2) if !missing(a1_employed)
gen a1_educ3 = cond(a1_grade <= 3, 1, cond(inrange(a1_grade, 4, 6), 2, cond(a1_grade >= 7, 3, .)))   // 1-3 <= HS/GED, 4-6 vocational/some college/AA, 7-9 BA+
foreach v in a1_menthealth a1_physhealth a2_menthealth a2_physhealth {
    replace `v' = . if !inrange(`v', 1, 5)
}
rename (a1_menthealth a1_physhealth a2_menthealth a2_physhealth) (a1_ment a1_phys a2_ment a2_phys)
gen a1_ment_fairpoor = a1_ment >= 4 if !missing(a1_ment)
gen a1_ment_excellent = a1_ment == 1 if !missing(a1_ment)
egen parent_stress = rowmean(k8q31 k8q32 k8q34)                          // 1 never .. 5 always
egen stress_max = rowmax(k8q31 k8q32 k8q34)
gen stress_any = stress_max >= 4 if !missing(parent_stress)
gen coping_notwell = k8q30 >= 3 if inrange(k8q30, 1, 4)
gen support = k8q35 == 1 if inlist(k8q35, 1, 2)
gen child_fairpoor = k2q01 >= 4 if inrange(k2q01, 1, 5)
gen prev_visit = k4q20r >= 2 if inrange(k4q20r, 1, 3)                    // any preventive visit in the past 12 months
gen other_care10h = k6q20 == 1 if inlist(k6q20, 1, 2)
gen everbf = k6q40 == 1 if inlist(k6q40, 1, 2)
gen bf_weeks = cond(missing(breastfedend_mo_s), 0, breastfedend_mo_s) * 4.33 + cond(missing(breastfedend_wk_s), 0, breastfedend_wk_s) ///
             + cond(missing(breastfedend_day_s), 0, breastfedend_day_s) / 7
replace bf_weeks = . if missing(breastfedend_mo_s) & missing(breastfedend_wk_s) & missing(breastfedend_day_s)
gen bf_still = k6q41r_still == 1 if inlist(k6q41r_still, 1, 2)
gen bf_ge26wk = (bf_weeks >= 26 & !missing(bf_weeks)) | bf_still == 1 if !missing(everbf)
replace bf_ge26wk = 0 if everbf == 0
egen fpl = rowmean(fpl_i1-fpl_i6)
gen fpl_lt200 = fpl < 200 if !missing(fpl)
gen race4 = cond(sc_hispanic_r == 1, 3, cond(sc_race_r == 1, 1, cond(sc_race_r == 2, 2, cond(sc_race_r >= 3, 4, .))))
label define race4 1 "White non-Hispanic" 2 "Black" 3 "Hispanic" 4 "Other"
label values race4 race4
preserve
import delimited "$RAW/pfml_policy_dates.csv", clear varnames(1) encoding(utf8)
gen double bstart = date(benefits_start, "YMD")
gen gvar = cond(month(bstart) <= 6, year(bstart), year(bstart) + 1)
keep state_fips gvar
tempfile pol
save `pol'
restore
merge m:1 state_fips using `pol', keep(master match) nogen
replace gvar = 0 if missing(gvar)
gen exposed_at_birth = gvar > 0 & birth_year >= gvar
compress
save "$CLEAN/nsch_children.dta", replace
