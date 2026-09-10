*==============================================================================
* 05_heterogeneity.do -- effects of PFML by education, other family income,
*                        marital status and race/ethnicity (csdid by subgroup).
* Mirrors python/05_heterogeneity.sh.  Requires $DATA from 00_master.do.
*==============================================================================
version 16
use "$DATA", clear
gen gvar = gvar_year
replace gvar = 0 if gvar > 2024
local xvars "i.agegrp married black hispanic other college"

* groups (educ3, race4, ofi_tercile are built in 01_build_cps_asec.do)
capture confirm variable educ3
if _rc {
    gen educ3 = cond(educ <= 73, 1, cond(educ >= 111, 3, 2))
    label define educ3 1 "HS or less" 2 "Some college" 3 "BA or more"
    label values educ3 educ3
    gen race4 = cond(hispanic, 3, cond(black, 2, cond(other, 4, 1)))
    label define race4 1 "White non-Hispanic" 2 "Black" 3 "Hispanic" 4 "Other"
    label values race4 race4
    gen other_faminc = (ftotval - labinc * 1000) / 1000
    bysort year_survey: egen ofi_p33 = pctile(other_faminc), p(33.33)
    bysort year_survey: egen ofi_p67 = pctile(other_faminc), p(66.67)
    gen ofi_tercile = cond(other_faminc <= ofi_p33, 1, cond(other_faminc <= ofi_p67, 2, 3))
}

tempfile all
save `all'

* (a) mothers of under-6s: worked and hours by subgroup
foreach y in worked hours {
    foreach v in educ3 ofi_tercile married race4 {
        levelsof `v', local(L)
        foreach l of local L {
            use `all', clear
            keep if mother_lt6 == 1 & `v' == `l'
            * drop the split variable from the covariates when it is constant
            local xv : subinstr local xvars "married" "", all
            local xv : subinstr local xv "black hispanic other" "", all
            local xv : subinstr local xv "college" "", all
            csdid `y' `xv' [iw = wt], time(year) gvar(gvar) method(drimp) cluster(statefip) wboot rseed(7) reps(499)
            estat simple, estore(het_`y'_`v'_`l')
            estat event, window(-8 8) estore(hetev_`y'_`v'_`l')
        }
    }
}

* (b) all women: birth last year by education and other family income
foreach v in educ3 ofi_tercile {
    levelsof `v', local(L)
    foreach l of local L {
        use `all', clear
        keep if `v' == `l'
        csdid has_infant i.agegrp married black hispanic other [iw = wt], time(year) gvar(gvar) method(drimp) ///
            cluster(statefip) wboot rseed(8) reps(499)
        estat simple, estore(het_infant_`v'_`l')
    }
}

* tables
esttab het_worked_educ3_1 het_worked_educ3_2 het_worked_educ3_3 het_worked_ofi_tercile_1 het_worked_ofi_tercile_2 het_worked_ofi_tercile_3 ///
    using "$TAB/t6_het_worked_income.tex", replace se star(* 0.10 ** 0.05 *** 0.01) booktabs ///
    mtitles("HS or less" "Some college" "BA+" "OFI low" "OFI mid" "OFI high") title("Worked last year, mothers of under-6s")
esttab het_worked_married_0 het_worked_married_1 het_worked_race4_1 het_worked_race4_2 het_worked_race4_3 het_worked_race4_4 ///
    using "$TAB/t7_het_worked_marital_race.tex", replace se star(* 0.10 ** 0.05 *** 0.01) booktabs ///
    mtitles("Not married" "Married" "White" "Black" "Hispanic" "Other") title("Worked last year, mothers of under-6s")
esttab het_infant_educ3_1 het_infant_educ3_2 het_infant_educ3_3 het_infant_ofi_tercile_1 het_infant_ofi_tercile_2 het_infant_ofi_tercile_3 ///
    using "$TAB/t8_het_births.tex", replace se star(* 0.10 ** 0.05 *** 0.01) booktabs ///
    mtitles("HS or less" "Some college" "BA+" "OFI low" "OFI mid" "OFI high") title("Birth last year, all women 18-44")
