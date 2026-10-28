*==============================================================================
* fig02_minwage.do -- Figure 2: the population-weighted effective minimum wage and the event calendar, 2010-2025.
*   Inputs: data/raw/minwage/state_mw_monthly.csv, data/clean/events2.dta, data/clean/cps2.dta (for teen weights)
*==============================================================================
do "stata2/00_setup.do"
* teen population weights by state
use "$CLEAN/cps2.dta", clear
keep if inrange(age, 16, 19)
collapse (sum) pop = weight, by(state_fips)
tempfile pop
save `pop'
* annual mean of the state effective minimum, weighted by teen population
import delimited "$MW/state_mw_monthly.csv", clear varnames(1)
gen year = real(substr(ym, 1, 4))
keep if inrange(year, 2010, 2025)
merge m:1 state_fips using `pop', keep(match) nogen
collapse (mean) mw [pw = pop], by(year)
tempfile mwyear
save `mwyear'
* events per year
use "$CLEAN/events2.dta", clear
gen year = real(substr(event_ym, 1, 4))
collapse (count) events = event_id, by(year)
merge 1:1 year using `mwyear', nogen
replace events = 0 if missing(events)
twoway (bar events year, yaxis(2) color(gs12)) (line mw year, lwidth(medthick)), ///
    ytitle("Dollars") ytitle("Events", axis(2)) xtitle("Year") ///
    legend(order(2 "Population-weighted effective minimum ($)" 1 "Unit events in the year")) ///
    title("Minimum wages and the event calendar, 2010-2025")
graph export "$OUT/fig02_minwage.png", replace width(2000)
