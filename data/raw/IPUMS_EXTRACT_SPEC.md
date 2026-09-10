# IPUMS-CPS extract specification

Site: https://cps.ipums.org/cps/ → "Get Data". One extract is required (A);
a second (B) is optional and adds monthly timing.

## Extract A (required): ASEC, 1990–2025, women 18–44

**Samples.** Tick "ASEC" only (untick basic monthly), then every year from
**1990 through 2025** (36 samples). 1990 gives 14 pre-treatment years before
California's 2004 start; earlier years are fine but not needed.

**Variables** (search box on the variable list; type the name exactly).

| Group | Variables |
|---|---|
| Technical (preselected) | `YEAR` `SERIAL` `MONTH` `CPSID` `ASECFLAG` `ASECWTH` `PERNUM` `CPSIDP` `ASECWT` |
| Geography | `STATEFIP` `METRO` |
| Demographics | `AGE` `SEX` `RACE` `MARST` `HISPAN` `NATIVITY` `CITIZEN` |
| Education | `EDUC` |
| Family interrelationships | `NCHILD` `NCHLT5` `YNGCH` `ELDCH` `MOMLOC` `SPLOC` `FAMSIZE` `RELATE` |
| Work, survey week | `EMPSTAT` `LABFORCE` `UHRSWORKT` `WKSTAT` `CLASSWKR` `OCC` `IND` |
| Work, previous calendar year | `WORKLY` `WKSWORK1` `WKSWORK2` `UHRSWORKLY` `FULLPART` `WHYNWLY` |
| Income, previous calendar year | `INCWAGE` `INCBUS` `INCTOT` `FTOTVAL` |
| Fertility / disability (optional) | `DIFFANY` `PAIDGH` `HIMCAIDLY` |

**Select cases** (button "Select cases" on the cart page): `SEX` = Female (2);
`AGE` = 18 through 44. This cuts the file to roughly one fifth of its size,
about 1.5 million person-years, and keeps it under GitHub's 100 MB file limit.

**Format.** "Data format" = CSV. "Structure" = rectangular (person). Leave
"Compressed (gzip)" ticked. Also download the DDI codebook (`.xml`).

**Where to put it.** Rename and place:

```
data/raw/ipums_cps_asec.csv.gz      # the data
data/raw/ipums_cps_asec.xml         # the DDI codebook
```

Then run `python python/01_build_ipums_asec.py` and
`python python/02_csdid.py`, or in Stata `do stata/00_master.do`.
The Stata build reads the uncompressed CSV; gunzip it first
(`gunzip -k data/raw/ipums_cps_asec.csv.gz`) — the `.csv` is git-ignored.

## Extract B (optional): basic monthly, 2000m1–2025m12, women 18–44

Adds month-level timing of the response around each state's benefit start.
Same site; tick basic monthly samples for every month 2000–2025 (312 samples),
untick ASEC.

Variables: `YEAR` `SERIAL` `MONTH` `HWTFINL` `CPSID` `PERNUM` `WTFINL` `CPSIDP`
`STATEFIP` `METRO` `AGE` `SEX` `RACE` `MARST` `HISPAN` `EDUC` `NCHILD` `NCHLT5`
`YNGCH` `ELDCH` `MOMLOC` `EMPSTAT` `LABFORCE` `UHRSWORKT` `WKSTAT` `CLASSWKR`
`EARNWEEK` `HOURWAGE` `PAIDHOUR` `ELIGORG`.

Select cases: `SEX` = Female, `AGE` 18–44. About 8 million rows, 150–250 MB
gzipped, which is over GitHub's single-file limit: either enable Git LFS for
`data/raw/*.csv.gz` or split by year (`zcat file.csv.gz | awk ...`) into
`data/raw/monthly/ipums_cps_monthly_YYYY.csv.gz`. The build script
accepts either layout.

## Why these variables

* `NCHILD`, `NCHLT5`, `YNGCH`, `MOMLOC` are the IPUMS family pointers: they
  identify mothers and the age of the youngest own child exactly, replacing
  the family-based linkage used on the PolicyEngine files.
* `WORKLY`, `WKSWORK1/2`, `UHRSWORKLY`, `INCWAGE` describe the previous
  calendar year, which is the reference period for treatment timing in the
  ASEC design; `EMPSTAT`, `LABFORCE`, `UHRSWORKT` describe the survey week
  (March) and give a second, later-dated outcome set.
* `ASECWT` is the person weight; `CPSIDP` allows linking the ASEC to the
  basic monthly file if extract B is added.
