*==============================================================================
* 01_build_cps.do -- the analysis file: CPS basic monthly, ages 16-24, January 2010 - December 2025.
*   Input : data/raw/monthly/cps_00091.csv (the IPUMS extract, unzipped)
*   Output: data/clean/cps2.dta  (one row per person-month)
*   This is the only place the analysis window is set.  Run once; takes a few minutes.
*==============================================================================
do "stata2/00_setup.do"

import delimited "$RAW/monthly/cps_00091.csv", clear varnames(1) case(lower)
keep if inrange(age, 16, 24) & inrange(year, 2010, 2025)

* ---- time ----
gen ym = year * 12 + month - 1                        // month index: Jan 2010 = 24120

* ---- enrollment (basic monthly item SCHLCOLL: attended school/college last week) ----
gen enrolled = inrange(schlcoll, 1, 4) if schlcoll != 0   // 0 = not asked (not 16-24): missing
drop if missing(enrolled)

* ---- work ----
gen employed = inlist(empstat, 10, 12)
gen inlf     = labforce == 2

* ---- the four school-work states ----
gen enr_emp  = enrolled * employed
gen enr_only = enrolled * (1 - employed)
gen emp_only = (1 - enrolled) * employed
gen neither  = (1 - enrolled) * (1 - employed)

* ---- demographics ----
gen female   = sex == 2
gen black    = race == 200
gen hispanic = inrange(hispan, 1, 899)
gen white    = race == 100 & hispanic == 0             // non-Hispanic white
gen race4    = cond(hispanic, 3, cond(black, 2, cond(white, 1, 4)))   // 1 white, 2 Black, 3 Hispanic, 4 other
gen hs_grad  = educ >= 73                              // high school diploma or GED
gen dropout  = (1 - enrolled) * (1 - hs_grad)          // Smith (2021): not enrolled and no diploma

* ---- family income (CPS category codes; 995+ = missing/refused) ----
gen lowses   = faminc <= 740                           // below $50,000
gen highses  = inrange(faminc, 820, 899)               // $50,000 or more
gen finc     = cond(faminc < 900, faminc, 999)         // category, with one code for missing

* ---- wages: outgoing rotation groups only ----
gen org = eligorg == 1
capture confirm variable hourwage2
if _rc gen hourwage2 = 999.99
capture confirm variable earnweek2
if _rc gen earnweek2 = 999999.99
gen hw = cond(hourwage < 999, hourwage, cond(hourwage2 < 999, hourwage2, .))
gen log_wage = ln(hw) if org & paidhour == 2 & hw > 0            // hourly-paid workers
gen ew = cond(earnweek < 9999, earnweek, cond(earnweek2 < 999999, earnweek2, .))
gen log_earnweek = ln(ew) if org & ew > 0                        // all workers

* ---- geography: county units get their county code, everyone else their state ----
preserve
    import delimited "$MW/unit_mw_monthly.csv", clear varnames(1)
    keep if kind == "county"
    keep unit
    duplicates drop
    levelsof unit, local(county_units)
restore
gen long geo = statefip
foreach c of local county_units {
    replace geo = `c' if county == `c'
}
rename statefip state_fips
rename wtfinl   weight

keep year month ym state_fips county geo age weight earnwt female black hispanic white race4 faminc finc lowses highses ///
     hs_grad enrolled employed inlf enr_emp enr_only emp_only neither dropout org log_wage log_earnweek
compress
save "$CLEAN/cps2.dta", replace
