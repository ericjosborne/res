*==============================================================================
* 04_tables.do -- export tables (esttab) for the paper.
*==============================================================================
version 16

* Table 1: descriptive statistics by treatment status, mothers of under-6s
use "$DATA", clear
keep if mother_lt6 == 1
gen ever = gvar_year > 0
estpost tabstat worked weeks hours fulltime inlf age married black hispanic college [aw = wt], ///
    by(ever) statistics(mean sd) columns(statistics)
esttab using "$TAB/t1_descriptives.tex", replace cells("mean(fmt(3)) sd(fmt(3))") ///
    label nonumber booktabs title("Mothers of children under 6, CPS ASEC 1990-2025")

* Table 2: CS aggregate effects, four outcomes
esttab cs_worked_simple cs_hours_simple cs_fulltime_simple cs_inlf_simple ///
    using "$TAB/t2_cs_simple.tex", replace se star(* 0.10 ** 0.05 *** 0.01) booktabs ///
    mtitles("Worked last year" "Hours" "Full time" "In LF (March)") title("Simple ATT, never-treated controls, drimp")

* Table 3: by cohort
esttab cs_worked_group cs_hours_group using "$TAB/t3_cs_group.tex", replace se ///
    star(* 0.10 ** 0.05 *** 0.01) booktabs mtitles("Worked" "Hours") title("ATT by adoption cohort")

* Table 4: event-study coefficients, main vs robustness
esttab cs_worked_event rb_notyet rb_fullyear rb_ddd_worked rb_placebo_childless ///
    using "$TAB/t4_event_robustness.tex", replace se star(* 0.10 ** 0.05 *** 0.01) booktabs ///
    mtitles("Main" "Not-yet controls" "Full-year cohort" "Triple diff" "Childless placebo")

* Table 5: alternative estimators
esttab rb_bjs rb_sa rb_twfe using "$TAB/t5_estimators.tex", replace se star(* 0.10 ** 0.05 *** 0.01) ///
    booktabs mtitles("BJS imputation" "Sun-Abraham" "TWFE")
