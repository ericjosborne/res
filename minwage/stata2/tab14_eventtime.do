*==============================================================================
* tab14_eventtime.do -- Table 14: event-time coefficients (years -3..3, base -1) for the log wage, enrollment and
*   employment, ages 16-17 and 18-19.  Same regression as fig03/fig07, printed as a table.
*   Input: data/clean/stacked2.dta.  Output: output/stata2/tab14_eventtime.csv
*==============================================================================
do "stata2/00_setup.do"
use "$CLEAN/stacked2.dta", clear
tempfile coefs
postfile C str12 outcome int band int k double b double se using `coefs', replace
foreach y in log_wage enrolled employed {
    local w = cond("`y'" == "log_wage", "nw", "n")
    foreach b in 1 2 {
        reghdfe `y' ib3.rk#i.treated [aw = `w'] if band == `b', absorb(eg et) cluster(state_fips)
        forvalues k = 1/7 {
            if `k' == 3 {
                post C ("`y'") (`b') (-1) (0) (0)
            }
            else {
                post C ("`y'") (`b') (`k' - 4) (_b[`k'.rk#1.treated]) (_se[`k'.rk#1.treated])
            }
        }
    }
}
postclose C
use `coefs', clear
format b se %8.4f
list, sepby(outcome band) noobs
export delimited using "$OUT/tab14_eventtime.csv", replace
