*==============================================================================
* 02_csdid.do -- Callaway & Sant'Anna (2021) group-time ATTs for PFML and
*                mothers' labour supply.  Main specification: yearly cohorts,
*                never-treated controls, doubly-robust (drimp) with covariates,
*                state-clustered wild bootstrap.
*
* Sample:  women 18-44 with an own child under 6 (mother_lt6 == 1).
* Data:    $DATA (set by 00_master.do; ASEC file, reference-year time).
* Window:  1990-2024 reference years.  CA (2004), NJ (2009), RI (2014), NY (2018), WA/DC (2020),
*          MA (2021), CT (2022), OR (2023), CO (2024) are treated cohorts;
*          DE/MN (2026) and MD (2028) are not-yet-treated within the window and
*          are recoded to never-treated (csdid convention).
*==============================================================================
version 16
use "$DATA", clear

keep if mother_lt6 == 1
gen gvar = gvar_year
replace gvar = 0 if gvar > 2024

* csdid on repeated cross sections: omit ivar().  Cluster by state.
* method(drimp) = doubly-robust improved (Sant'Anna & Zhao 2020); reg = outcome regression.
local xvars "i.agegrp married black hispanic other college"

foreach y in worked hours fulltime weeks inlf employed {
    csdid `y' `xvars' [iw = wt], time(year) gvar(gvar) method(drimp) ///
        cluster(statefip) wboot rseed(20260909) reps(999)
    estat simple,   estore(cs_`y'_simple)
    estat group,    estore(cs_`y'_group)
    estat calendar, estore(cs_`y'_cal)
    estat event, window(-8 8) estore(cs_`y'_event)
    estat pretrend
    csdid_plot, title("PFML and mothers' `y': event study (CS, never-treated controls)") ///
        name(ev_`y', replace)
    graph export "$FIG/event_`y'.png", replace width(1600)
}

* Heterogeneity by cohort generation (early adopters CA/NJ/RI vs 2018+)
use "$DATA", clear
keep if mother_lt6 == 1
gen gvar = gvar_year
replace gvar = 0 if gvar > 2024
csdid inlf `xvars' [iw = wt], time(year) gvar(gvar) method(drimp) cluster(statefip) wboot rseed(1)
estat group, estore(cs_inlf_bygroup)
