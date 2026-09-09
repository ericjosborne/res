"""
91_clean_ipums.py -- build the Angrist-Evans mother sample from an IPUMS USA
extract (see 90_ipums_extract.py) for every census / ACS year, in the same
harmonised layout as 01_clean_1980.py.

NOT RUN in the build environment (no IPUMS access).  Written against the
documented IPUMS USA codes; check the codebook shipped with your extract
(EDUC, MARST, WKSWORK2 intervals) before trusting the output.

Usage:  python code/91_clean_ipums.py data/raw/ipums/usa_00001.csv.gz
Output: data/clean/ipums_mothers.csv.gz  (one row per mother-year)
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "clean"
OUT.mkdir(parents=True, exist_ok=True)

USECOLS = ["YEAR", "SERIAL", "PERNUM", "PERWT", "STATEFIP", "MOMLOC", "SPLOC", "NCHILD", "NCHLT5",
           "ELDCH", "YNGCH", "SEX", "AGE", "MARST", "RACE", "HISPAN", "EDUC", "EMPSTAT", "LABFORCE",
           "WKSWORK1", "WKSWORK2", "UHRSWORK", "INCWAGE", "INCEARN"]
WKSWORK2_MID = {0: 0, 1: 7, 2: 20, 3: 33, 4: 43.5, 5: 48.5, 6: 51}  # IPUMS interval midpoints


def build(path):
    df = pd.read_csv(path, usecols=lambda c: c in USECOLS)
    out = []
    for year, d in df.groupby("YEAR"):
        d = d.copy()
        # children: anyone whose MOMLOC points to a person in the same household
        kids = d[d["MOMLOC"] > 0][["SERIAL", "MOMLOC", "PERNUM", "SEX", "AGE"]]
        kids = kids.sort_values(["SERIAL", "MOMLOC", "AGE"], ascending=[True, True, False])
        kids["order"] = kids.groupby(["SERIAL", "MOMLOC"]).cumcount() + 1
        k = kids.pivot_table(index=["SERIAL", "MOMLOC"], columns="order", values=["SEX", "AGE"], aggfunc="first")
        k.columns = [f"{a}_{b}" for a, b in k.columns]
        k = k.reset_index().rename(columns={"MOMLOC": "PERNUM"})
        m = d[(d["SEX"] == 2) & d["AGE"].between(21, 35) & (d["NCHILD"] >= 2)].merge(k, on=["SERIAL", "PERNUM"])
        m = m[m["AGE_2"] >= 1]  # second child at least one year old (AE98)
        o = pd.DataFrame({
            "sample": "ipums", "year": year, "weight": m["PERWT"].astype(float),
            "morekids": (m["NCHILD"] > 2).astype(int), "kids": m["NCHILD"],
            "boy1st": (m["SEX_1"] == 1).astype(int), "boy2nd": (m["SEX_2"] == 1).astype(int),
            "multi2nd": (m.get("AGE_3", pd.Series(np.nan, index=m.index)) == m["AGE_2"]).fillna(False).astype(int),
            "worked": np.where(m["WKSWORK2"].notna() & (year >= 2008), (m["WKSWORK2"] > 0).astype(int),
                               (m["WKSWORK1"] > 0).astype(int)),
            "weeks": np.where(year >= 2008, m["WKSWORK2"].map(WKSWORK2_MID), m["WKSWORK1"]),
            "hours": m["UHRSWORK"].astype(float),
            "labinc": m["INCWAGE"].replace({999999: np.nan, 999998: np.nan}).astype(float) / 1000.0,
            "age": m["AGE"].astype(int), "agefst": m["AGE"] - m["AGE_1"],
            "black": (m["RACE"] == 2).astype(int), "hispanic": (m["HISPAN"].between(1, 4)).astype(int),
            "other": ((m["RACE"] >= 3) & ~m["HISPAN"].between(1, 4)).astype(int),
            "educ": m["EDUC"].astype(float),  # IPUMS general code; map to years if needed
            "nonmomi": np.nan,
            "married": (m["MARST"] == 1).astype(int), "state_fips": m["STATEFIP"],
            "nkids_lt6": m["NCHLT5"], "age_youngest": m["YNGCH"], "oldest_lt18": (m["ELDCH"] < 18).astype(int),
        })
        o["samesex"] = (o["boy1st"] == o["boy2nd"]).astype(int)
        o["twoboys"] = ((o["boy1st"] == 1) & (o["boy2nd"] == 1)).astype(int)
        o["twogirls"] = ((o["boy1st"] == 0) & (o["boy2nd"] == 0)).astype(int)
        out.append(o)
        print(year, len(o), "mothers; P(samesex)=%.3f" % o["samesex"].mean())
    res = pd.concat(out, ignore_index=True)
    res.to_csv(OUT / "ipums_mothers.csv.gz", index=False)
    print("wrote", OUT / "ipums_mothers.csv.gz", len(res))


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else ROOT / "data" / "raw" / "ipums" / "usa_00001.csv.gz")
