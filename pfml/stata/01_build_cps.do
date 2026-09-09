*==============================================================================
* 01_build_cps.do -- build the estimation file from an IPUMS-CPS basic monthly
*                    extract, 2000m1-2024m12.
*
* Request the extract at cps.ipums.org (basic monthly samples, all months) with
* at least these variables:
*   YEAR MONTH SERIAL PERNUM CPSIDP WTFINL STATEFIP METRO
*   AGE SEX MARST RACE HISPAN EDUC NATIVITY
*   NCHILD NCHLT5 YNGCH ELDCH
*   LABFORCE EMPSTAT UHRSWORKT WKSTAT ABSENT WHYABSNT CLASSWKR
*   (optional, outgoing rotation groups) EARNWEEK HOURWAGE PAIDHOUR UNION
* Save the .dta as pfml/data/raw/ipums_cps_basic.dta.
*
* Treatment: PFML benefits available in the state (monthly precision).  The
* cohort variable gvar is the first month benefits were payable, coded as a
* Stata monthly date; gvar = 0 for never-treated states.  Two treatment
* definitions are kept: benefits start (main) and first full benefit year.
*==============================================================================
version 16

*---------------------------------------------------------------- policy file
import delimited "$RAW/pfml_policy_dates.csv", clear varnames(1) encoding(utf8)
gen double bstart = date(benefits_start, "YMD")
gen g_month = mofd(bstart)                         // Stata monthly date
format g_month %tm
gen g_year_half = cohort_asec_refyear               // first calendar year with >=6 months of benefits
gen g_year_full = first_full_ref_year
keep state_fips g_month g_year_half g_year_full
rename state_fips statefip
tempfile policy
save `policy'

*---------------------------------------------------------------- CPS extract
use "$RAW/ipums_cps_basic.dta", clear
rename *, lower

* women 18-44, civilian, not in group quarters (IPUMS basic monthly excludes GQ)
keep if sex == 2 & inrange(age, 18, 44)
drop if wtfinl <= 0 | missing(wtfinl)

* time
gen ym = ym(year, month)
format ym %tm

* outcomes (IPUMS codes: labforce 2 = in labour force; empstat 10/12 employed)
gen inlf     = labforce == 2                     if inlist(labforce, 1, 2)
gen employed = inlist(empstat, 10, 12)           if labforce == 2 | labforce == 1
replace employed = 0 if labforce == 1
gen hours    = uhrsworkt if inrange(uhrsworkt, 0, 168)
replace hours = 0 if inlf == 0 | employed == 0
gen fulltime = hours >= 35 if !missing(hours)
gen atwork   = inlist(empstat, 10)               if !missing(empstat)

* family structure
gen mother       = nchild > 0
gen mother_lt6   = nchlt5 > 0 | (yngch >= 0 & yngch < 6)
gen has_infant   = yngch == 0
gen mother_lt1   = has_infant
gen married      = inlist(marst, 1, 2)
gen black        = race == 200
gen hispanic     = hispan > 0 & hispan < 900
gen other        = race > 200 & !hispanic
gen college      = educ >= 111                    // bachelor's or more
gen hs_or_less   = educ <= 73
gen agegrp       = floor(age / 5) * 5

* treatment
merge m:1 statefip using `policy', keep(master match) nogen
replace g_month = 0 if missing(g_month)
replace g_year_half = 0 if missing(g_year_half)
replace g_year_full = 0 if missing(g_year_full)
gen treated = g_month > 0 & ym >= g_month
gen everpfml = g_month > 0

* annual cohort for the yearly specification (benefits available >= 6 months)
gen gvar_year = g_year_half
gen gvar_full = g_year_full

label var inlf "In labour force"
label var employed "Employed"
label var hours "Usual weekly hours (0 if not working)"
label var g_month "PFML cohort: first month benefits payable (0 = never)"
label var gvar_year "PFML cohort: first year with >= 6 months of benefits (0 = never)"
compress
save "$CLEAN/cps_women_1844_monthly.dta", replace

*---------------------------------------------------------------- state-cell file
* Collapsed cells speed up csdid on 25 years of monthly data and are what the
* repeated-cross-section estimator uses anyway; keep the microdata for the
* covariate-adjusted (drimp) runs.
preserve
collapse (mean) inlf employed hours fulltime (rawsum) n = wtfinl [pw = wtfinl], ///
    by(statefip year month ym g_month gvar_year gvar_full mother_lt6 mother has_infant)
save "$CLEAN/cps_cells_monthly.dta", replace
restore

preserve
collapse (mean) inlf employed hours fulltime (rawsum) n = wtfinl [pw = wtfinl], ///
    by(statefip year gvar_year gvar_full mother_lt6 mother has_infant)
save "$CLEAN/cps_cells_yearly.dta", replace
restore
