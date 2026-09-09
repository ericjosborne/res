"""
03_build_ipums_asec.py -- build the estimation file from the IPUMS-CPS ASEC
extract described in ../data/raw/IPUMS_EXTRACT_SPEC.md (women 18-44,
1990-2025), in the same layout as the PolicyEngine-based file so that
04_csdid_full.py runs on either.

Input : pfml/data/raw/ipums_cps_asec.csv.gz
Output: pfml/data/clean/cps_asec_women_1844.csv.gz and .dta (Stata 16)

Written against the documented IPUMS-CPS codes; the DDI codebook that ships
with the extract is the authority (EDUC and RACE codes in particular).
"""
from pathlib import Path
import numpy as np
import pandas as pd

PF = Path(__file__).resolve().parents[1]
RAW = PF / "data" / "raw"; OUT = PF / "data" / "clean"; OUT.mkdir(parents=True, exist_ok=True)

USECOLS = ["YEAR", "SERIAL", "PERNUM", "ASECWT", "STATEFIP", "METRO", "HFLAG", "MOMLOC", "AGE", "SEX", "RACE", "MARST",
           "HISPAN", "EDUC", "NCHILD", "NCHLT5", "YNGCH", "ELDCH", "EMPSTAT", "LABFORCE", "UHRSWORKT",
           "WORKLY", "WKSWORK1", "WKSWORK2", "UHRSWORKLY", "FULLPART", "INCWAGE", "INCBUS", "NATIVITY"]
WKS2_MID = {0: 0, 1: 7, 2: 20, 3: 33, 4: 43.5, 5: 48.5, 6: 51}


def find_extract():
    """ipums_cps_asec.csv(.gz) if present, else the newest cps_NNNNN.csv(.gz) in data/raw."""
    for cand in [RAW / "ipums_cps_asec.csv.gz", RAW / "ipums_cps_asec.csv"]:
        if cand.exists():
            return cand
    found = sorted(RAW.glob("cps_*.csv*"))
    if not found:
        raise FileNotFoundError("no IPUMS extract in pfml/data/raw (see IPUMS_EXTRACT_SPEC.md)")
    return found[-1]


def build(path=None):
    path = path or find_extract()
    print("reading", path)
    df = pd.read_csv(path, usecols=lambda c: c.upper() in USECOLS)
    df.columns = [c.upper() for c in df.columns]
    df = df[(df["SEX"] == 2) & df["AGE"].between(18, 44) & (df["ASECWT"] > 0)].copy()

    d = pd.DataFrame({
        "year": df["YEAR"] - 1,                       # reference year of income / weeks
        "survey_year": df["YEAR"],
        "state_fips": df["STATEFIP"].astype(int),
        "weight": df["ASECWT"].astype(float),
        "age": df["AGE"].astype(int),
    })
    # outcomes, previous calendar year
    d["worked"] = (df["WORKLY"] == 2).astype(int)
    wks = np.where(df["WKSWORK1"].notna() & (df["WKSWORK1"] >= 0), df["WKSWORK1"], df["WKSWORK2"].map(WKS2_MID))
    d["weeks"] = np.where(d["worked"] == 1, wks, 0).astype(float)
    hrs = df["UHRSWORKLY"].where(df["UHRSWORKLY"].between(0, 99), np.nan)
    d["hours"] = np.where(d["worked"] == 1, hrs, 0).astype(float)
    d["fulltime"] = ((df["FULLPART"] == 1) & (d["worked"] == 1)).astype(int)
    inc = df["INCWAGE"].replace({9999999: np.nan, 9999998: np.nan}).fillna(0) + df["INCBUS"].replace({9999999: np.nan, 9999998: np.nan}).fillna(0)
    d["labinc"] = inc / 1000.0
    # outcomes, survey week (March)
    d["inlf"] = (df["LABFORCE"] == 2).astype(int)
    d["employed"] = df["EMPSTAT"].isin([10, 12]).astype(int)
    d["hours_now"] = np.where(d["employed"] == 1, df["UHRSWORKT"].where(df["UHRSWORKT"] < 997, np.nan), 0)
    # family structure from IPUMS pointers
    d["nkids"] = df["NCHILD"].astype(int)
    d["mother"] = (df["NCHILD"] > 0).astype(int)
    d["age_youngest"] = df["YNGCH"].where(df["YNGCH"] < 99, np.nan)
    d["mother_lt6"] = ((df["NCHILD"] > 0) & (df["YNGCH"] < 6)).astype(int)
    d["has_infant"] = ((df["NCHILD"] > 0) & (df["YNGCH"] == 0)).astype(int)
    d["nkids_lt6"] = df["NCHLT5"].astype(int)
    # demographics
    d["married"] = df["MARST"].isin([1, 2]).astype(int)
    d["black"] = (df["RACE"] == 200).astype(int)
    d["hispanic"] = df["HISPAN"].between(1, 899).astype(int)
    d["other"] = ((df["RACE"] > 200) & (d["hispanic"] == 0)).astype(int)
    d["college"] = (df["EDUC"] >= 111).astype(int)
    d["hs_or_less"] = (df["EDUC"] <= 73).astype(int)
    d["foreign_born"] = df["NATIVITY"].eq(5).astype(int)
    d["agegrp"] = (d["age"] // 5) * 5
    # treatment cohorts
    pol = pd.read_csv(RAW / "pfml_policy_dates.csv").set_index("state_fips")
    d["gvar"] = d["state_fips"].map(pol["cohort_asec_refyear"]).fillna(0).astype(int)
    d["gvar_full"] = d["state_fips"].map(pol["first_full_ref_year"]).fillna(0).astype(int)
    d["treated_now"] = ((d["gvar"] > 0) & (d["year"] >= d["gvar"])).astype(int)
    d["metro"] = df["METRO"].astype(int) if "METRO" in df else -1
    d["hflag"] = df["HFLAG"].fillna(-1).astype(int) if "HFLAG" in df else -1   # 2014: two ASEC subsamples, both kept
    return d


if __name__ == "__main__":
    import sys
    d = build(Path(sys.argv[1]) if len(sys.argv) > 1 else None)
    print("rows:", len(d), " years:", d["year"].min(), "-", d["year"].max())
    print("mothers of under-6s per year (mean):", round(d.groupby("year")["mother_lt6"].sum().mean()))
    print(d.groupby("gvar").size())
    d.to_csv(OUT / "cps_asec_women_1844.csv.gz", index=False)
    d.to_stata(OUT / "cps_asec_women_1844.dta", write_index=False, version=118)
    print("wrote", OUT / "cps_asec_women_1844.csv.gz", "and .dta")
