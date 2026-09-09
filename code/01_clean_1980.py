"""
01_clean_1980.py
----------------
Build analysis-ready files from the two 1980 Census extracts of the
Angrist & Evans (1998, AER) "married women aged 21-35 with two or more
children" sample that are redistributed in R/Python teaching packages:

  * AER::Fertility (Stock & Watson companion; 254,654 obs, 8 variables)
      -> data/raw/rdatasets/AER_Fertility.csv
  * wooldridge::labsup (31,857 obs; AE98's Black-or-Hispanic subsample with
    richer covariates: education, age at first birth, hours, incomes, twins)
      -> data/raw/rdatasets/wooldridge_labsup.csv

Output: data/clean/ae1980_full.csv.gz and data/clean/ae1980_bh.csv.gz with a
harmonised variable layout shared with the modern CPS sample (02_clean_cps_pe.py).

Harmonised layout
-----------------
sample        'ae1980_full' | 'ae1980_bh' | 'cps_pe'
year          census / survey year
weight        sampling weight (1 for the 1980 census extracts, which are
              self-weighting 1980 PUMS draws)
morekids      1 if >2 children
kids          number of children (labsup / CPS only)
boy1st boy2nd 1 if first / second child is a boy
samesex       boy1st == boy2nd
twoboys twogirls
multi2nd      1 if second birth was a multiple birth (labsup / CPS only)
worked        1 if mother worked for pay in the reference year
weeks         weeks worked in reference year (1980 full sample only)
hours         usual weekly hours (labsup / CPS only)
labinc        mother's labour income, $1000s (labsup / CPS only, nominal)
age           mother's age
agefst        mother's age at first birth (labsup / CPS only)
black hispanic other  race/ethnicity indicators (white = none of them)
educ          years of schooling (labsup only)
nonmomi       family income minus mother's labour income, $1000s (labsup only)
"""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "rdatasets"
OUT = ROOT / "data" / "clean"
OUT.mkdir(parents=True, exist_ok=True)

COLS = ["sample", "year", "weight", "morekids", "kids", "boy1st", "boy2nd", "samesex",
        "twoboys", "twogirls", "multi2nd", "worked", "weeks", "hours", "labinc",
        "age", "agefst", "black", "hispanic", "other", "educ", "nonmomi"]


def yes(s):
    return (s.astype(str).str.lower().isin(["yes", "male", "true", "1"])).astype(int)


def clean_full():
    df = pd.read_csv(RAW / "AER_Fertility.csv")
    out = pd.DataFrame({
        "sample": "ae1980_full", "year": 1980, "weight": 1.0,
        "morekids": yes(df["morekids"]),
        "kids": np.nan,
        "boy1st": yes(df["gender1"]),
        "boy2nd": yes(df["gender2"]),
        "multi2nd": np.nan,
        "weeks": df["work"].astype(float),
        "hours": np.nan, "labinc": np.nan,
        "age": df["age"].astype(int), "agefst": np.nan,
        "black": yes(df["afam"]), "hispanic": yes(df["hispanic"]), "other": yes(df["other"]),
        "educ": np.nan, "nonmomi": np.nan,
    })
    out["worked"] = (out["weeks"] > 0).astype(int)
    return out


def clean_bh():
    df = pd.read_csv(RAW / "wooldridge_labsup.csv")
    out = pd.DataFrame({
        "sample": "ae1980_bh", "year": 1980, "weight": 1.0,
        "morekids": df["morekids"].astype(int),
        "kids": df["kids"].astype(int),
        "boy1st": df["boy1st"].astype(int),
        "boy2nd": df["boy2nd"].astype(int),
        "multi2nd": df["multi2nd"].astype(int),
        "worked": df["worked"].astype(int),
        "weeks": df["weeks"].astype(float),
        "hours": df["hours"].astype(float),
        "labinc": df["labinc"].astype(float),
        "age": df["age"].astype(int),
        "agefst": df["agefstm"].astype(int),
        "black": df["black"].astype(int),
        "hispanic": df["hispan"].astype(int),
        "other": 0,
        "educ": df["educ"].astype(float),
        "nonmomi": df["nonmomi"].astype(float),
    })
    return out


def add_instruments(d):
    d["samesex"] = (d["boy1st"] == d["boy2nd"]).astype(int)
    d["twoboys"] = ((d["boy1st"] == 1) & (d["boy2nd"] == 1)).astype(int)
    d["twogirls"] = ((d["boy1st"] == 0) & (d["boy2nd"] == 0)).astype(int)
    return d[COLS]


def checks(d, name):
    """Consistency checks that must hold in an AE-type sample."""
    print(f"\n== {name}: n={len(d):,}")
    assert d["age"].between(21, 35).all(), "age outside 21-35"
    assert d[["morekids", "boy1st", "boy2nd", "worked"]].isin([0, 1]).all().all()
    # Sex ratio at birth ~0.51 boys and independence of sexes across births
    p1, p2 = d["boy1st"].mean(), d["boy2nd"].mean()
    ct = pd.crosstab(d["boy1st"], d["boy2nd"], normalize=True)
    print(f"   P(boy1st)={p1:.4f}  P(boy2nd)={p2:.4f}  P(samesex)={d['samesex'].mean():.4f}")
    print("   joint distribution of (boy1st, boy2nd):\n", ct.round(4).to_string())
    # weeks is a whole number in 0..52
    if d["weeks"].notna().any():
        assert d["weeks"].between(0, 52).all()
        assert ((d["weeks"] > 0) == (d["worked"] == 1)).all(), "worked != (weeks>0)"
    if d["kids"].notna().any():
        assert ((d["kids"] > 2) == (d["morekids"] == 1)).all()
    if d["hours"].notna().any():
        print(f"   hours: mean={d['hours'].mean():.2f}, share 0 = {(d['hours']==0).mean():.3f}, "
              f"worked but hours==0: {((d['worked']==1)&(d['hours']==0)).sum()}")
    print("   means:", d[["morekids", "samesex", "worked", "weeks", "age", "black", "hispanic", "other"]]
          .mean().round(4).to_dict())


if __name__ == "__main__":
    full = add_instruments(clean_full())
    bh = add_instruments(clean_bh())
    checks(full, "AER::Fertility (AE98 married sample)")
    checks(bh, "wooldridge::labsup (AE98 Black/Hispanic subsample)")
    # Race coding conflicts noted in the AER codebook: report them, keep indicators.
    print("\n   race indicator overlap in full sample:\n",
          pd.crosstab([full["black"], full["hispanic"]], full["other"]).to_string())
    full.to_csv(OUT / "ae1980_full.csv.gz", index=False)
    bh.to_csv(OUT / "ae1980_bh.csv.gz", index=False)
    print("\nwrote", OUT / "ae1980_full.csv.gz", "and", OUT / "ae1980_bh.csv.gz")
