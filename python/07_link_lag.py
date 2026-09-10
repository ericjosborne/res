"""
07_link_lag.py -- link consecutive ASECs through CPSIDP to observe whether a
woman worked in the year BEFORE the reference year (an eligibility proxy: PFML
benefits require an earnings history in the base period).

Households in rotation groups 1-4 in March of year t are re-interviewed in
March of year t+1, so about half of the year-t+1 sample has a year-t record.
IPUMS advises validating links on sex and age; we require the same sex and an
age change of 0 to 2 years.  Also brings in the survey-week class of worker
and links from the *following* March, which tell whether the woman was
employed a year later (a persistence outcome).

Adds to data/clean/cps_asec_women_1844.csv.gz:
  linked_prev   1 if a valid previous-March record exists
  worked_lag    worked in the year before the reference year (NaN if unlinked)
  labinc_lag    labour income in that year, $1000s
  classwkr_now  IPUMS CLASSWKR in the survey week (0 = NIU / not employed)
"""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"; CLEAN = ROOT / "data" / "clean"

src = sorted(RAW.glob("cps_*.csv*"))[-1]
print("reading", src)
cols = ["YEAR", "SERIAL", "PERNUM", "CPSIDP", "SEX", "AGE", "WORKLY", "INCWAGE", "INCBUS", "CLASSWKR"]
raw = pd.read_csv(src, usecols=cols)
raw = raw[raw["CPSIDP"] > 0].copy()
raw["labinc"] = (raw["INCWAGE"].replace({9999999: np.nan, 9999998: np.nan}).fillna(0)
                 + raw["INCBUS"].replace({9999999: np.nan, 9999998: np.nan}).fillna(0)) / 1000.0
raw["worked"] = (raw["WORKLY"] == 2).astype(int)

# previous March record for each (CPSIDP, YEAR): match YEAR-1
prev = raw[["CPSIDP", "YEAR", "SEX", "AGE", "worked", "labinc"]].rename(
    columns={"YEAR": "YEAR_prev", "SEX": "SEX_prev", "AGE": "AGE_prev", "worked": "worked_lag", "labinc": "labinc_lag"})
prev["YEAR"] = prev["YEAR_prev"] + 1
prev = prev.drop_duplicates(["CPSIDP", "YEAR"])
cur = raw[["YEAR", "SERIAL", "PERNUM", "CPSIDP", "SEX", "AGE", "CLASSWKR"]]
m = cur.merge(prev, on=["CPSIDP", "YEAR"], how="left")
valid = (m["SEX"] == m["SEX_prev"]) & (m["AGE"] - m["AGE_prev"]).between(0, 2)
m.loc[~valid, ["worked_lag", "labinc_lag"]] = np.nan
m["linked_prev"] = valid.astype(int)
print("link rate, all persons with CPSIDP:", round(m["linked_prev"].mean(), 3))

d = pd.read_csv(CLEAN / "cps_asec_women_1844.csv.gz")
key = ["survey_year", "serial", "pernum"] if "serial" in d else None
if key is None:
    # the clean file does not carry SERIAL/PERNUM: rebuild the join keys from the raw file order
    raise SystemExit("clean file lacks serial/pernum; rerun 01_build_ipums_asec.py after adding them")
mm = m.rename(columns={"YEAR": "survey_year", "SERIAL": "serial", "PERNUM": "pernum", "CLASSWKR": "classwkr_now"})
d = d.drop(columns=[c for c in ["linked_prev", "worked_lag", "labinc_lag", "classwkr_now"] if c in d])
d = d.merge(mm[["survey_year", "serial", "pernum", "linked_prev", "worked_lag", "labinc_lag", "classwkr_now"]],
            on=["survey_year", "serial", "pernum"], how="left")
d["linked_prev"] = d["linked_prev"].fillna(0).astype(int)
print("women 18-44 linked to previous March:", round(d["linked_prev"].mean(), 3))
w = d[(d.mother_lt6 == 1) & (d.linked_prev == 1)]
print("mothers of under-6s, linked: worked_lag rate by race:\n", w.groupby("race4").apply(lambda x: np.average(x["worked_lag"], weights=x["weight"])).round(3).to_string())
d.to_csv(CLEAN / "cps_asec_women_1844.csv.gz", index=False)
d.to_stata(CLEAN / "cps_asec_women_1844.dta", write_index=False, version=118)
print("updated", CLEAN / "cps_asec_women_1844.csv.gz")
