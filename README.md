# Female labour force participation: research projects

Two designs live in this repository. The active one is the policy evaluation
in `pfml/`, written for Stata 16 with Callaway and Sant'Anna's `csdid`. The
first project, the Angrist-Evans same-sex instrument, is kept in `code/` and
`docs/` as a complete, reproducible appendix.

## Active project: state paid family and medical leave and mothers' labour supply (`pfml/`)

Staggered adoption of paid family and medical leave across nine states and DC
(2004-2024), estimated with Callaway and Sant'Anna (2021) group-time ATTs on
CPS repeated cross sections. Design memo: `pfml/docs/research_design.md`.
Preliminary results: `pfml/docs/preliminary_results.md`.

| Path | Contents |
|---|---|
| `pfml/stata/` | Stata 16 do-files: master, IPUMS-CPS build, `csdid` main estimates, robustness (not-yet-treated, triple difference, BJS, Sun-Abraham, dCDH, HonestDiD, placebo), tables, and a preliminary do-file that runs on the data shipped here. **Untested: no Stata in the build environment.** |
| `pfml/python/` | Executed pipeline: CPS ASEC 2021-23 sample build (`01_build_cps_sample.py`) and a Callaway-Sant'Anna demonstration (`02_csdid_prelim.py`) that cross-checks the `csdid` Python port against a cell-mean implementation. |
| `pfml/data/raw/pfml_policy_dates.csv` | Enactment, contribution and benefit start dates by state (compiled from memory; verify). |
| `pfml/data/clean/cps_women_1844.dta` | Women 18-44, reference years 2020-2022, with linked children and cohort variable, Stata 16 format. |
| `pfml/output/` | Tables and figures from the preliminary run. |

### Status of the preliminary run

Only two cohorts (Massachusetts 2021, Connecticut 2022) fall inside the CPS
window reachable from this environment, with 60-150 treated mothers per cell.
Point estimates for mothers of under-6s are positive (+3 to +8 points on
employment) but imprecise, and the childless-women placebo moves, so the window
cannot identify the policy effect. The paper needs the IPUMS-CPS basic monthly
files 2000-2024; the Stata build for them is written.

## Data provenance

The build environment blocks every statistical-agency host (Census Bureau,
IPUMS, NBER, BLS, FRED, World Bank, OECD, ILO). Reachable: PyPI, conda-forge,
GitHub raw content, GitHub release assets, git clones.

| Data | Source used | Original provenance |
|---|---|---|
| CPS ASEC 2021, 2022, 2023 person records | PolicyEngine `cps_YYYY.h5` GitHub release assets (`code/00_download.sh`) | Census Bureau CPS ASEC public-use files, renamed by PolicyEngine, no reweighting |
| 1980 Census Angrist-Evans samples | Rdatasets GitHub mirror; `wooldridge` PyPI package | Stock & Watson (2007); Wooldridge, from Angrist & Evans (1998) |
| Long-run FLFP series | `owid/owid-datasets` GitHub repo | Olivetti (2013); OECD via OWID (2017) |

## How to run

```bash
pip install -r requirements.txt
bash code/00_download.sh                 # PolicyEngine CPS release assets (not committed)
python pfml/python/01_build_cps_sample.py
python pfml/python/02_csdid_prelim.py
# Stata 16, from the repository root, after installing the packages listed in pfml/stata/00_master.do:
#   do pfml/stata/00_master.do
```

## Appendix project: children and mothers' labour supply, 1980 vs 2020s (`code/`, `docs/`)

Angrist-Evans (1998) sibling-sex instrument replicated on the 1980 Census
(254,654 married mothers) and re-estimated on the 2021-23 CPS; heterogeneity,
two-boys vs two-girls LATEs, distributional LATE, complier profile, Kitagawa
validity check. See `docs/research_design.md` and `docs/preliminary_results.md`.
