*==============================================================================
* 30_build_cps_monthly.do -- IPUMS-CPS basic monthly extract to the teen file for the minimum wage /
*                            enrollment design (mirrors python/30_build_cps_monthly.py).
*                            The extract is large (all ages, 1994-2026); import in year blocks if memory is short.
*==============================================================================
version 16
import delimited "$RAW/monthly/cps_00091.csv", clear varnames(1) case(lower)
keep if inrange(age, 16, 24)
rename (statefip wtfinl) (state_fips weight)
gen ym = year * 12 + month - 1
gen enrolled = inrange(schlcoll, 1, 4) if schlcoll != 0
gen enr_hs = inlist(schlcoll, 1, 2) if schlcoll != 0
gen enr_college = inlist(schlcoll, 3, 4) if schlcoll != 0
gen enr_ft = inlist(schlcoll, 1, 3) if schlcoll != 0
gen employed = inlist(empstat, 10, 12)
gen atwork = empstat == 10
gen inlf = labforce == 2
gen unemp = inrange(empstat, 20, 22)
gen hours = cond(employed == 0, 0, cond(uhrsworkt < 997, uhrsworkt, .))
gen enr_emp = enrolled * employed
gen enr_only = enrolled * (1 - employed)
gen emp_only = (1 - enrolled) * employed
gen neither = (1 - enrolled) * (1 - employed)
gen female = sex == 2
gen black = race == 200
gen hispanic = inrange(hispan, 1, 899)
gen org = eligorg == 1
capture confirm variable hourwage2
if _rc gen hourwage2 = 999.99
capture confirm variable earnweek2
if _rc gen earnweek2 = 999999.99
gen hw = cond(hourwage < 999, hourwage, cond(hourwage2 < 999, hourwage2, .))
gen log_wage = ln(hw) if org & paidhour == 2 & hw > 0
gen ew = cond(earnweek < 9999, earnweek, cond(earnweek2 < 999999, earnweek2, .))
gen log_earnweek = ln(ew) if org & ew > 0
drop if missing(enrolled)
compress
save "$CLEAN/cps_monthly_1624.dta", replace
