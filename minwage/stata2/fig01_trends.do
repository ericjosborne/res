*==============================================================================
* fig01_trends.do -- Figure 1: teen employment, enrollment and school-work status, 1995-2025.
*   The only output that uses years before 2010: it shows the decline the paper is about.
*   Input : the raw IPUMS extract (all years).  Output: output/stata2/fig01_trends.png
*==============================================================================
do "stata2/00_setup.do"
import delimited "$RAW/monthly/cps_00091.csv", clear varnames(1) case(lower)
keep if inrange(age, 16, 19) & inrange(year, 1995, 2025) & schlcoll != 0
gen enrolled = inrange(schlcoll, 1, 4)
gen employed = inlist(empstat, 10, 12)
gen enr_emp  = enrolled * employed
gen enr_only = enrolled * (1 - employed)
gen emp_only = (1 - enrolled) * employed
gen neither  = (1 - enrolled) * (1 - employed)
gen band = cond(age <= 17, 1, 2)
* annual weighted means by age band, and pooled
preserve
    collapse (mean) employed enrolled [pw = wtfinl], by(year band)
    reshape wide employed enrolled, i(year) j(band)
    twoway (line employed1 year, lcolor(navy)) (line employed2 year, lcolor(maroon)) ///
           (line enrolled1 year, lcolor(navy) lpattern(dash)) (line enrolled2 year, lcolor(maroon) lpattern(dash)), ///
        legend(order(1 "Employed, 16-17" 2 "Employed, 18-19" 3 "Enrolled, 16-17" 4 "Enrolled, 18-19") rows(2)) ///
        xline(2009.5 2025.5, lcolor(gs12)) ytitle("Share") xtitle("Year") title("Employment and enrollment, by age") name(g1, replace)
restore
collapse (mean) enr_emp enr_only emp_only neither [pw = wtfinl], by(year)
twoway (line enr_emp year) (line enr_only year) (line emp_only year) (line neither year), ///
    legend(order(1 "Enrolled and employed" 2 "Enrolled only" 3 "Employed only" 4 "Neither") rows(2)) ///
    xline(2009.5 2025.5, lcolor(gs12)) ytitle("Share") xtitle("Year") title("School-work status, ages 16-19") name(g2, replace)
graph combine g1 g2, cols(2) note("Shaded years 2010-2025 are the analysis window (marked by the vertical lines).")
graph export "$OUT/fig01_trends.png", replace width(2000)
