# Children and Mothers' Labour Supply, 1980 to the 2020s

Preliminary research project on female labour force participation. The design is
the Angrist and Evans (1998) sibling-sex-composition instrument for a third child,
replicated on the 1980 Census and re-estimated on an identically constructed sample
of mothers from the 2021-2023 CPS ASEC, with a ready-to-run pipeline for the full
IPUMS 1980-2023 extension that the paper needs.

* `docs/research_design.md` – question, contribution, identification, threats, plan.
* `docs/preliminary_results.md` – the results with tables and figures.
* `output/tables/*.md|csv`, `output/figures/*.png` – everything the write-up cites.

## Research question

Has the causal effect of an additional child on mothers' labour supply changed
between 1980 and the 2020s, and does the same-sex instrument still shift fertility
in an era of falling completed fertility? The same-sex instrument identifies a
local average treatment effect (LATE) for mothers who have a third child because
their first two children share a sex. The 1980 numbers replicate Angrist and
Evans exactly; the modern numbers are proof-of-concept on a small sample and a
power calculation for the ACS-based paper.

## Data and provenance

The build environment blocks every statistical-agency host (Census Bureau API and
FTP, IPUMS, NBER, BLS, FRED, World Bank, OECD, ILO, Eurostat, Our World in Data's
site, Dataverse, ICPSR, Zenodo, HuggingFace, OpenML, CRAN). Reachable: PyPI,
conda-forge, GitHub raw content, GitHub release assets and git clones. Everything
below came through those channels; each file's origin is recorded here.

| Data | Source actually used | Original provenance | Rows |
|---|---|---|---|
| 1980 Census, married mothers 21-35 with 2+ children | `AER::Fertility` via the Rdatasets GitHub mirror (`data/raw/rdatasets/AER_Fertility.csv`) | Stock & Watson (2007) companion data, taken from Angrist & Evans (1998) | 254,654 |
| Same sample, Black or Hispanic mothers, richer covariates (education, age at first birth, hours, incomes, twins) | `wooldridge` PyPI package, dataset `labsup` (`data/raw/rdatasets/wooldridge_labsup.csv`) | Wooldridge (Introductory Econometrics) from Angrist & Evans (1998) | 31,857 |
| CPS ASEC 2021, 2022, 2023 person records | PolicyEngine `cps_YYYY.h5` GitHub release assets (`code/00_download.sh`) | Census Bureau CPS ASEC public-use files, renamed by PolicyEngine, no reweighting | 443,130 persons; 9,171 mothers after linkage |
| Long-run FLFP series | `owid/owid-datasets` GitHub repo (`data/raw/owid/`) | Olivetti (2013); OECD via OWID (2017) | country-year |
| Supplementary married-women labour-supply files (not used in the results yet) | Rdatasets mirror: `Ecdat::HI` (1993 CPS wives), `wooldridge::cps91`, `Mroz87`, `Workinghours`, `Participation` | JAE data archive, Wooldridge, Mroz (1987) | 753-22,272 |

The PolicyEngine `cps_2024.h5` release is a byte-for-byte copy of the 2023 person
records and is not used. The h5 files (86 MB each) are not committed; run
`code/00_download.sh` to fetch them.

**For the paper**, replace the CPS proof-of-concept with the IPUMS USA extract
requested by `code/90_ipums_extract.py` (1980, 1990, 2000 5% samples plus ACS
2005-2023), cleaned by `code/91_clean_ipums.py` into the same layout. Both are
written but could not be executed here.

## How to run

```bash
pip install -r requirements.txt
bash code/00_download.sh              # PolicyEngine CPS release assets (GitHub)
python code/01_clean_1980.py          # -> data/clean/ae1980_full.csv.gz, ae1980_bh.csv.gz
python code/02_clean_cps_pe.py        # -> data/clean/cps_pe_mothers.csv.gz, output/tables/cps_pe_linkage.csv
python code/04_context_figure.py      # -> output/figures/F1_flfp_long_run.png
python code/03_analysis.py            # -> output/tables/T1..T8, output/figures/F2..F4
```

`code/aelib.py` holds the estimators (weighted OLS and 2SLS with HC1 standard
errors, Sargan statistic, complier profiles, markdown tables). The 2SLS output is
cross-checked against `pyfixest` at the end of `03_analysis.py`.

## Repository layout

```
code/      00_download.sh 01_clean_1980.py 02_clean_cps_pe.py 03_analysis.py
           04_context_figure.py 90_ipums_extract.py 91_clean_ipums.py aelib.py
data/raw/  rdatasets/ (CSV + codebooks)  owid/  policyengine/ (h5 not committed)
data/clean/ harmonised analysis files
output/    tables/ figures/
docs/      research_design.md preliminary_results.md
```
