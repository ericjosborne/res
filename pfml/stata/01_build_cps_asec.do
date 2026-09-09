*==============================================================================
* 01_build_cps_asec.do -- build the estimation file from the IPUMS-CPS ASEC
*                         extract described in data/raw/IPUMS_EXTRACT_SPEC.md
*                         (women 18-44, ASEC 1990-2025, CSV).
*
* Input : $RAW/ipums_cps_asec.csv   (gunzip the .csv.gz first)
* Output: $CLEAN/cps_women_1844_asec.dta  (person-year, reference-year time)
*         $CLEAN/cps_cells_yearly.dta     (state x year x group cells)
* Variable names match 02_csdid.do: inlf employed hours fulltime worked weeks
* labinc, weight wt, cohorts gvar_year gvar_full, groups mother_lt6 mother
* has_infant, covariates agegrp married black hispanic other college.
*==============================================================================
version 16

*---------------------------------------------------------------- policy file
import delimited "$RAW/pfml_policy_dates.csv", clear varnames(1) encoding(utf8)
keep state_fips cohort_asec_refyear first_full_ref_year
rename (state_fips cohort_asec_refyear first_full_ref_year) (statefip g_year_half g_year_full)
tempfile policy
save `policy'

*---------------------------------------------------------------- extract
import delimited "$RAW/ipums_cps_asec.csv", clear varnames(1) case(lower)
keep if sex == 2 & inrange(age, 18, 44) & asecwt > 0
rename asecwt wt
gen year_survey = year
replace year = year - 1                       // reference year for WORKLY / INCWAGE
label var year "ASEC reference year (survey year - 1)"

* previous-calendar-year outcomes
gen worked   = workly == 2
gen weeks    = cond(!missing(wkswork1) & wkswork1 >= 0, wkswork1, .)
replace weeks = cond(wkswork2 == 1, 7, cond(wkswork2 == 2, 20, cond(wkswork2 == 3, 33, ///
                 cond(wkswork2 == 4, 43.5, cond(wkswork2 == 5, 48.5, cond(wkswork2 == 6, 51, .)))))) if missing(weeks)
replace weeks = 0 if worked == 0
gen hours    = uhrsworkly if inrange(uhrsworkly, 0, 99)
replace hours = 0 if worked == 0
gen fulltime = fullpart == 1 & worked == 1
gen labinc   = (cond(inlist(incwage, 9999999, 9999998), 0, incwage) + ///
                cond(inlist(incbus, 9999999, 9999998), 0, incbus)) / 1000

* survey-week outcomes (March of the survey year)
gen inlf     = labforce == 2
gen employed = inlist(empstat, 10, 12)
gen hours_now = uhrsworkt if uhrsworkt < 997
replace hours_now = 0 if employed == 0

* family structure (IPUMS pointers)
gen mother     = nchild > 0
gen mother_lt6 = nchild > 0 & yngch < 6
gen has_infant = nchild > 0 & yngch == 0
gen nkids_lt6  = nchlt5

* demographics
gen married    = inlist(marst, 1, 2)
gen black      = race == 200
gen hispanic   = inrange(hispan, 1, 899)
gen other      = race > 200 & !hispanic
gen college    = educ >= 111
gen hs_or_less = educ <= 73
gen agegrp     = floor(age / 5) * 5

* treatment
merge m:1 statefip using `policy', keep(master match) nogen
replace g_year_half = 0 if missing(g_year_half)
replace g_year_full = 0 if missing(g_year_full)
rename (g_year_half g_year_full) (gvar_year gvar_full)
gen treated = gvar_year > 0 & year >= gvar_year

label var gvar_year "PFML cohort: first ref. year with >= 6 months of benefits (0 = never)"
label var worked "Worked for pay in reference year (WORKLY)"
label var hours "Usual weekly hours last year (0 if did not work)"
compress
save "$CLEAN/cps_women_1844_asec.dta", replace

preserve
collapse (mean) inlf employed worked hours fulltime labinc (rawsum) n = wt [pw = wt], ///
    by(statefip year gvar_year gvar_full mother_lt6 mother has_infant)
save "$CLEAN/cps_cells_yearly.dta", replace
restore
