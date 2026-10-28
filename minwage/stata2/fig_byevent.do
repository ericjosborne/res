*==============================================================================
* fig_byevent.do -- the event-by-event post-event averages for enrollment of 18-19 year olds (appendix figure).
*   For each event separately: (treated post mean - treated year -1 mean) - (control post mean - control year -1 mean),
*   using the 48 post months and the 12 months of year -1.  No regression: plain weighted means.
*   Input: data/clean/stacked2.dta.  Output: output/stata2/fig_byevent.png, fig_byevent.csv
*==============================================================================
do "stata2/00_setup.do"
use "$CLEAN/stacked2.dta", clear
keep if band == 2
gen period = cond(relyear == -1, 1, cond(relyear >= 0, 2, .))   // 1 = year -1, 2 = post (years 0..3)
drop if missing(period)
collapse (mean) enrolled (rawsum) n [pw = n], by(event_id treated period)
reshape wide enrolled n, i(event_id treated) j(period)
gen change = enrolled2 - enrolled1                            // post minus base, within group
reshape wide change enrolled1 enrolled2 n1 n2, i(event_id) j(treated)
gen did = change1 - change0                                   // the event's effect
gen weight = n11                                               // treated teen weight in year -1 (the paper's event weight)
merge 1:1 event_id using "$CLEAN/events2.dta", keepusing(unit event_ym source) nogen keep(match)
sort did
gen rank = _n
list event_ym unit source did, noobs
export delimited event_id unit event_ym source did weight using "$OUT/fig_byevent.csv", replace
twoway (scatter did rank, msymbol(circle)) , yline(0) xtitle("Events, sorted") ytitle("Post-event average, enrollment 18-19") ///
    title("Event-by-event estimates, enrollment of 18-19 year olds", size(small))
graph export "$OUT/fig_byevent.png", replace width(2000)
count if did < 0
display "negative: " r(N) " of " _N
