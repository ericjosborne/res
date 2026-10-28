*==============================================================================
* tabB_twfe_diag.do -- Appendix Table 32: what drives the TWFE coefficient for enrollment and for "neither".
*   The same regression as tabB_twfe under variations: all months; school months; summer months; raising units only
*   (drop the federal-floor states); region x month effects; 2010-2019; drop 2020-21; a 24-month lead of the log
*   minimum (placebo: its own coefficient is reported); unit-specific linear trends.
*   Inputs: data/clean/cps2.dta, data/clean/mwpanel2.dta.  Output: output/stata2/tabB_twfe_diag.csv
*==============================================================================
do "stata2/00_setup.do"
use "$CLEAN/cps2.dta", clear
keep if inrange(age, 16, 19)
merge m:1 geo ym using "$CLEAN/mwpanel2.dta", keep(match) nogen keepusing(log_mw)
* the log minimum 24 months ahead (placebo)
preserve
    use "$CLEAN/mwpanel2.dta", clear
    replace ym = ym - 24
    rename log_mw log_mw_lead24
    keep geo ym log_mw_lead24
    tempfile lead
    save `lead'
restore
merge m:1 geo ym using `lead', keep(master match) nogen
gen band = cond(age <= 17, 1, 2)
gen summer = inlist(month, 6, 7, 8)
gen region = 1 if inlist(state_fips, 9, 23, 25, 33, 44, 50, 34, 36, 42)
replace region = 2 if inlist(state_fips, 17, 18, 26, 39, 55, 19, 20, 27, 29, 31, 38, 46)
replace region = 3 if inlist(state_fips, 10, 11, 12, 13, 24, 37, 45, 51, 54, 1, 21, 28, 47, 5, 22, 40, 48)
replace region = 4 if missing(region)
egen region_ym = group(region ym)
bysort geo: egen mw_range = max(log_mw)
bysort geo: egen mw_min = min(log_mw)
gen raiser = (mw_range - mw_min) > 0.01                       // the unit's minimum changed at some point
gen t = ym - 2010 * 12

capture program drop diag
program define diag
    args variant cond fe rhs coef
    foreach y in enrolled neither {
        foreach a in 1 2 3 {
            local c2 = cond(`a' == 3, "`cond'", "`cond' & band == `a'")
            reghdfe `y' `rhs' i.age female black hispanic [aw = weight] if `c2', absorb(`fe') cluster(state_fips)
            post P ("`variant'") ("`y'") ("`a'") (_b[`coef']) (_se[`coef'])
        }
    }
end
tempfile res
postfile P str45 variant str10 outcome str10 ages double b double se using `res', replace
diag "all months (baseline)"            "1"               "geo ym"        "log_mw"              "log_mw"
diag "school months, Sept-May"          "summer == 0"     "geo ym"        "log_mw"              "log_mw"
diag "summer months, June-Aug"          "summer == 1"     "geo ym"        "log_mw"              "log_mw"
diag "raising units only"               "raiser == 1"     "geo ym"        "log_mw"              "log_mw"
diag "school months, raising units"     "summer == 0 & raiser == 1" "geo ym" "log_mw"           "log_mw"
diag "region x month fixed effects"     "1"               "geo region_ym" "log_mw"              "log_mw"
diag "2010-2019"                        "year <= 2019"    "geo ym"        "log_mw"              "log_mw"
diag "drop 2020-21"                     "!inrange(year, 2020, 2021)" "geo ym" "log_mw"          "log_mw"
diag "24-month lead (coef. on the lead)" "!missing(log_mw_lead24)" "geo ym" "log_mw log_mw_lead24" "log_mw_lead24"
diag "unit-specific linear trends"      "1"               "geo ym geo#c.t" "log_mw"             "log_mw"
postclose P
use `res', clear
replace ages = cond(ages == "1", "16-17", cond(ages == "2", "18-19", "16-19"))
format b se %8.4f
list variant outcome ages b se, sepby(variant) noobs
export delimited using "$OUT/tabB_twfe_diag.csv", replace
