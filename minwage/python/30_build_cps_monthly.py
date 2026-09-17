"""30_build_cps_monthly.py -- IPUMS-CPS basic monthly extract (all ages, 1994-2025) to the teen file for the
minimum wage / school enrollment design (docs/minwage_design.md).  Streams the gzipped CSV in chunks and keeps
ages 16-24.  Output: data/clean/cps_monthly_1624.csv.gz (one row per person-month).

SCHLCOLL (16-24 only): 0 NIU, 1 HS full-time, 2 HS part-time, 3 college full-time, 4 college part-time, 5 not attending.
EMPSTAT: 10 at work, 12 has job not at work, 20-22 unemployed, 30+ NILF.  ELIGORG 1 = outgoing rotation group
(earnings asked); PAIDHOUR 2 = paid hourly; HOURWAGE/HOURWAGE2 999.99 = NIU; EARNWEEK/EARNWEEK2 9999.99/999999.99 = NIU.
"""
import sys
from pathlib import Path
import numpy as np, pandas as pd
PF = Path(__file__).resolve().parents[1]; RAW = PF / "data" / "raw" / "monthly"; CLEAN = PF / "data" / "clean"
src = sorted(RAW.glob("cps_*.csv.gz"))[-1]
cols = ["YEAR", "MONTH", "STATEFIP", "COUNTY", "METRO", "FAMINC", "WTFINL", "CPSIDP", "MISH", "AGE", "SEX", "RACE", "HISPAN", "NATIVITY",
        "MARST", "RELATE", "EMPSTAT", "LABFORCE", "UHRSWORKT", "UHRSWORK1", "WKSTAT", "CLASSWKR", "EDUC", "SCHLCOLL",
        "ELIGORG", "EARNWT", "PAIDHOUR", "HOURWAGE", "HOURWAGE2", "EARNWEEK", "EARNWEEK2", "UHRSWORKORG"]
out = CLEAN / "cps_monthly_1624.csv.gz"; parts = []; n_in = 0
for ch in pd.read_csv(src, usecols=cols, chunksize=2_000_000):
    n_in += len(ch); ch = ch[ch.AGE.between(16, 24) & ch.YEAR.between(2010, 2025)]   # analysis window: January 2010 to December 2025, for every estimate, table and figure
    d = pd.DataFrame({"year": ch.YEAR, "month": ch.MONTH, "state_fips": ch.STATEFIP, "county": ch.COUNTY, "metro": ch.METRO, "faminc": ch.FAMINC,
                      "weight": ch.WTFINL, "cpsidp": ch.CPSIDP, "mish": ch.MISH, "age": ch.AGE, "female": (ch.SEX == 2).astype(np.int8),
                      "black": (ch.RACE == 200).astype(np.int8), "hispanic": ch.HISPAN.between(1, 899).astype(np.int8), "white": ((ch.RACE == 100) & ~ch.HISPAN.between(1, 899)).astype(np.int8), "foreign_born": (ch.NATIVITY == 5).astype(np.int8),
                      "relate": ch.RELATE, "educ": ch.EDUC, "schlcoll": ch.SCHLCOLL})
    d["enrolled"] = ch.SCHLCOLL.between(1, 4).astype(np.int8); d.loc[ch.SCHLCOLL == 0, "enrolled"] = -1
    d["enr_hs"] = ch.SCHLCOLL.isin([1, 2]).astype(np.int8); d["enr_college"] = ch.SCHLCOLL.isin([3, 4]).astype(np.int8); d["enr_ft"] = ch.SCHLCOLL.isin([1, 3]).astype(np.int8)
    d["employed"] = ch.EMPSTAT.isin([10, 12]).astype(np.int8); d["atwork"] = (ch.EMPSTAT == 10).astype(np.int8)
    d["inlf"] = (ch.LABFORCE == 2).astype(np.int8); d["unemp"] = ch.EMPSTAT.between(20, 22).astype(np.int8)
    d["hours"] = ch.UHRSWORKT.where(ch.UHRSWORKT < 997, np.nan).where(d.employed == 1, 0.0)
    d["hs_grad"] = (ch.EDUC >= 73).astype(np.int8)
    d["org"] = (ch.ELIGORG == 1).astype(np.int8); d["earnwt"] = ch.EARNWT
    hw = ch.HOURWAGE.where(ch.HOURWAGE < 999); hw2 = ch.HOURWAGE2.where(ch.HOURWAGE2 < 999) if "HOURWAGE2" in ch else np.nan
    d["hourwage"] = hw.fillna(hw2); d["paidhour"] = (ch.PAIDHOUR == 2).astype(np.int8)
    ew = ch.EARNWEEK.where(ch.EARNWEEK < 9999); ew2 = ch.EARNWEEK2.where(ch.EARNWEEK2 < 999999) if "EARNWEEK2" in ch else np.nan
    d["earnweek"] = ew.fillna(ew2); d["hours_org"] = ch.UHRSWORKORG.where(ch.UHRSWORKORG < 997)
    parts.append(d); print(f"read {n_in:,} rows; kept {sum(len(p) for p in parts):,}", flush=True)
d = pd.concat(parts, ignore_index=True)
d = d[d.enrolled >= 0]                                  # SCHLCOLL universe (drops a handful of NIU)
d["ym"] = d.year * 12 + d.month - 1                    # month index
enr = d[d.age.between(16, 19)]
print("rows", len(d), "years", d.year.min(), "-", d.year.max()); print("enrolled 16-17:", round(np.average(enr[enr.age <= 17].enrolled, weights=enr[enr.age <= 17].weight), 3),
      " 18-19:", round(np.average(enr[enr.age >= 18].enrolled, weights=enr[enr.age >= 18].weight), 3))
print("teens per month:", round(len(enr) / enr.ym.nunique()))
d.to_csv(out, index=False); print("wrote", out)
