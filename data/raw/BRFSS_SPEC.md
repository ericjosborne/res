# BRFSS files for the mental-health design

Source: CDC, Behavioral Risk Factor Surveillance System, annual public-use
data, https://www.cdc.gov/brfss/annual_data/annual_data.htm. One SAS
transport file per year. Download **1993 through 2024** (32 files).

| Years | File name on the CDC page | Approx. size |
|---|---|---|
| 1993-2010 | `CDBRFS93.XPT` … `CDBRFS10.XPT` (inside `CDBRFS93XPT.zip` etc.) | 30-150 MB each |
| 2011-2024 | `LLCP2011.XPT` … `LLCP2024.XPT` (inside `LLCP2011XPT.zip` etc.) | 300-900 MB each |

Unzip each and place the `.XPT` files in `data/raw/brfss/` (any
capitalisation of the extension is fine). Do not commit them; either

* upload the `.XPT` files as release assets (each is under GitHub's 2 GB
  asset limit; a `data-brfss` release with 32 assets is fine), or
* run `python python/10_build_brfss.py` locally (needs pandas) or
  `do stata/10_build_brfss.do` and upload only the output,
  `data/clean/brfss_adults_1844.csv.gz` (roughly 100-150 MB).

## What the build keeps

Adults aged 18-44 (women and men; men and childless women serve as placebo
groups), with:

| Concept | BRFSS variable(s) by year | Built variable |
|---|---|---|
| State | `_STATE` | `state_fips` |
| Interview year, month | `IYEAR`, `IMONTH` | `year`, `month` |
| Weight | `_FINALWT` (1993-2010), `_LLCPWT` (2011-) | `weight` |
| Design | `_PSU`, `_STSTR` | `psu`, `strata` |
| Sex | `SEX` (to 2017), `SEXVAR` / `_SEX` (2018-) | `female` |
| Age | `AGE` (to 2012), `_AGE80` (2013-), `_AGEG5YR` fallback | `age` |
| Children in household | `CHILDREN` (count, 88 = none) | `nkids`, `mother`/`parent` |
| Pregnant | `PREGNANT` (women 18-44, most years from 1997) | `pregnant` |
| Mental health days, past 30 | `MENTHLTH` (88 = 0, 77/99 = missing) | `mentdays`, `fmd` (>= 14 days) |
| Physical health days | `PHYSHLTH` | `physdays` |
| Days activity limited | `POORHLTH` | `poordays` |
| General health | `GENHLTH` (1 excellent … 5 poor) | `genhlth`, `fairpoor` |
| Employment | `EMPLOY` (to 2012), `EMPLOY1` (2013-) | `employed`, `unable_work` |
| Income | `INCOME2` (to 2020), `INCOME3` (2021-) | `income_cat`, `inc_lt25k` |
| Marital status | `MARITAL` | `married` |
| Education | `EDUCA` | `educ3` |
| Race/ethnicity | `_RACE` (2001-), `_RACEG2`/`RACE`+`HISPANIC` earlier | `race4` |
| Insurance | `HLTHPLAN` (to 2010), `HLTHPLN1` (2011-2020), `_HLTHPLN` (2021-) | `insured` |
| Emotional support / life satisfaction (2005-2010 module) | `EMTSUPRT`, `LSATISFY` | kept when present |

The 2011 redesign (cell-phone sample, raking weights) changes levels for all
states at once; the year effects absorb that, and `11_csdid_brfss.do` /
`02_csdid.py --data brfss` include a robustness run that drops 2010-2011.
