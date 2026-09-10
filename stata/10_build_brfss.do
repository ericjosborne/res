*==============================================================================
* 10_build_brfss.do -- BRFSS 1993-2024 to the analysis file for the paid-leave
*                      mental-health design (mirrors python/10_build_brfss.py).
* Input : data/raw/brfss/CDBRFSyy.XPT (1993-2010), LLCPyyyy.XPT (2011-)
* Output: data/clean/brfss_adults_1844.dta
* Stata 16 reads SAS transport files with import sasxport5.  Variable names
* change across years; each block below tests for the alternatives.
*==============================================================================
version 16
tempfile acc
local first = 1
forvalues y = 1993/2024 {
    local yy = substr("`y'", 3, 2)
    local f ""
    if `y' <= 2010 local f "$RAW/brfss/CDBRFS`yy'.XPT"
    else            local f "$RAW/brfss/LLCP`y'.XPT"
    capture confirm file "`f'"
    if _rc {
        display as text "skip `y': `f' not found"
        continue
    }
    display as result "reading `f'"
    import sasxport5 "`f'", clear
    rename *, lower
    gen survey_year = `y'
    * --- variable-name harmonisation
    capture confirm variable _llcpwt
    if !_rc gen weight = _llcpwt
    else    gen weight = _finalwt
    capture confirm variable sexvar
    if !_rc gen female = sexvar == 2 if inlist(sexvar, 1, 2)
    else {
        capture confirm variable _sex
        if !_rc gen female = _sex == 2 if inlist(_sex, 1, 2)
        else    gen female = sex == 2 if inlist(sex, 1, 2)
    }
    capture confirm variable age
    if !_rc gen agev = age if inrange(age, 18, 99)
    else {
        capture confirm variable _age80
        if !_rc gen agev = _age80 if inrange(_age80, 18, 99)
        else    gen agev = .
    }
    capture confirm variable _ageg5yr
    if !_rc replace agev = cond(_ageg5yr == 1, 21, cond(_ageg5yr == 2, 27, cond(_ageg5yr == 3, 32, cond(_ageg5yr == 4, 37, cond(_ageg5yr == 5, 42, .))))) if missing(agev)
    keep if inrange(agev, 18, 44) & weight > 0 & _state <= 56
    gen state_fips = _state
    gen year  = `y'
    capture replace year = iyear if !missing(iyear)
    capture gen month = imonth
    gen nkids = cond(children == 88, 0, cond(inrange(children, 1, 30), children, .))
    capture gen pregnant = cond(pregnant == 1, 1, cond(pregnant == 2, 0, .))
    gen mentdays = cond(menthlth == 88, 0, cond(inrange(menthlth, 1, 30), menthlth, .))
    gen physdays = cond(physhlth == 88, 0, cond(inrange(physhlth, 1, 30), physhlth, .))
    capture gen poordays = cond(poorhlth == 88, 0, cond(inrange(poorhlth, 1, 30), poorhlth, .))
    gen genhlth_v = genhlth if inrange(genhlth, 1, 5)
    capture confirm variable employ1
    if !_rc gen emp = employ1
    else    gen emp = employ
    gen employed    = inlist(emp, 1, 2) if inrange(emp, 1, 8)
    gen unable_work = emp == 8          if inrange(emp, 1, 8)
    capture confirm variable income3
    if !_rc gen inc = income3
    else {
        capture confirm variable income2
        if !_rc gen inc = income2
        else    gen inc = income
    }
    gen inc_lt25k = inrange(inc, 1, 4) if inrange(inc, 1, 11)
    gen married = marital == 1 if inrange(marital, 1, 6)
    gen educ3 = cond(inrange(educa, 1, 4), 1, cond(educa == 5, 2, cond(educa == 6, 3, .)))
    capture confirm variable _race
    if !_rc gen race4 = cond(_race == 8, 3, cond(_race == 1, 1, cond(_race == 2, 2, cond(inrange(_race, 3, 7), 4, .))))
    else {
        capture confirm variable hispanic
        if _rc gen hispanic = .
        gen race4 = cond(hispanic == 1, 3, cond(race == 1, 1, cond(race == 2, 2, cond(inrange(race, 3, 9), 4, .))))
    }
    capture confirm variable _hlthpln
    if !_rc gen insured = _hlthpln == 1 if inlist(_hlthpln, 1, 2)
    else {
        capture confirm variable hlthpln1
        if !_rc gen insured = hlthpln1 == 1 if inlist(hlthpln1, 1, 2)
        else    gen insured = hlthplan == 1 if inlist(hlthplan, 1, 2)
    }
    keep survey_year state_fips year month weight female agev nkids pregnant mentdays physdays poordays genhlth_v ///
         employed unable_work inc_lt25k married educ3 race4 insured
    rename (agev genhlth_v) (age genhlth)
    if `first' {
        save `acc', replace
        local first = 0
    }
    else {
        append using `acc'
        save `acc', replace
    }
}
use `acc', clear
gen fmd = mentdays >= 14 if !missing(mentdays)
gen fairpoor = genhlth >= 4 if !missing(genhlth)
gen parent = nkids > 0 if !missing(nkids)
gen mother = female == 1 & parent == 1
gen mother_young = mother & age <= 34
gen agegrp = floor(age / 5) * 5
label define educ3 1 "HS or less" 2 "Some college" 3 "BA or more"
label values educ3 educ3
label define race4 1 "White non-Hispanic" 2 "Black" 3 "Hispanic" 4 "Other"
label values race4 race4

* PFML cohorts: year with >= 6 months of benefits (benefit start in Jan-Jun -> that year, else next)
preserve
import delimited "$RAW/pfml_policy_dates.csv", clear varnames(1) encoding(utf8)
gen double bstart = date(benefits_start, "YMD")
gen gvar = cond(month(bstart) <= 6, year(bstart), year(bstart) + 1)
gen gvar_month = year(bstart) * 12 + month(bstart)
keep state_fips gvar gvar_month
tempfile pol
save `pol'
restore
merge m:1 state_fips using `pol', keep(master match) nogen
replace gvar = 0 if missing(gvar)
replace gvar_month = 0 if missing(gvar_month)
gen ym = year * 12 + cond(missing(month), 6, month)
compress
save "$CLEAN/brfss_adults_1844.dta", replace
