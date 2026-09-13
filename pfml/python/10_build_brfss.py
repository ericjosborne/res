"""
10_build_brfss.py -- build the BRFSS analysis file for the paid-leave mental
health design (see data/raw/BRFSS_SPEC.md).

Reads every BRFSS transport file in data/raw/brfss/ (CDBRFSyy.XPT for
1993-2010, LLCPyyyy.XPT for 2011-), harmonises the variables whose names
changed over time, keeps adults aged 18-44, attaches the PFML cohorts, and
writes data/clean/brfss_adults_1844.csv.gz (+ .dta, Stata 16).

Usage: python python/10_build_brfss.py [--dir data/raw/brfss] [--years 1993-2024]
Written without access to the files; the variable map below follows the CDC
codebooks and prints, for each year, which source column was used, so a wrong
mapping is visible in the log.
"""
import argparse, re, sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"; CLEAN = ROOT / "data" / "clean"; CLEAN.mkdir(parents=True, exist_ok=True)

# candidate source names in priority order, per concept
MAP = {
    "state": ["_STATE", "STATE"],
    "iyear": ["IYEAR"], "imonth": ["IMONTH"],
    "weight": ["_LLCPWT", "_FINALWT", "FINALWT"],
    "psu": ["_PSU", "PSU"], "strata": ["_STSTR", "STSTR"],
    "sex": ["SEXVAR", "_SEX", "SEX"],
    "age": ["AGE", "_AGE80", "_IMPAGE"], "ageg5": ["_AGEG5YR"],
    "children": ["CHILDREN"], "pregnant": ["PREGNANT"],
    "menthlth": ["MENTHLTH"], "physhlth": ["PHYSHLTH"], "poorhlth": ["POORHLTH"], "genhlth": ["GENHLTH"],
    "employ": ["EMPLOY1", "EMPLOY"], "income": ["INCOME3", "INCOME2", "INCOME"],
    "marital": ["MARITAL"], "educa": ["EDUCA"],
    "race": ["_RACE", "_RACEG21", "_RACEG2", "RACE"], "hispanic": ["HISPANC3", "HISPANC2", "HISPANIC"],
    "hlthplan": ["_HLTHPLN", "HLTHPLN1", "HLTHPLAN"],
    "emtsuprt": ["EMTSUPRT"], "lsatisfy": ["LSATISFY"],
}
AGEG5_MID = {1: 21, 2: 27, 3: 32, 4: 37, 5: 42, 6: 47, 7: 52, 8: 57, 9: 62, 10: 67, 11: 72, 12: 77, 13: 82}


def pick(df, names):
    for n in names:
        if n in df.columns:
            return n
    return None


def days(x):
    """BRFSS 30-day counts: 1-30 days, 88 = none, 77/99 = don't know/refused."""
    x = pd.to_numeric(x, errors="coerce")
    return x.where(x.between(1, 30), np.where(x == 88, 0, np.nan))


def harmonise(df, year):
    df.columns = [c.upper() for c in df.columns]
    src = {k: pick(df, v) for k, v in MAP.items()}
    print(f"{year}: n={len(df):,}  " + " ".join(f"{k}={v}" for k, v in src.items() if k in ("weight", "sex", "age", "employ", "income", "race", "hlthplan")))
    out = pd.DataFrame(index=df.index)
    out["survey_year"] = year
    out["state_fips"] = pd.to_numeric(df[src["state"]], errors="coerce").astype("Int64")
    out["year"] = pd.to_numeric(df[src["iyear"]], errors="coerce").fillna(year).astype(int) if src["iyear"] else year
    out["month"] = pd.to_numeric(df[src["imonth"]], errors="coerce").astype("Int64") if src["imonth"] else pd.NA
    out["weight"] = pd.to_numeric(df[src["weight"]], errors="coerce")
    out["psu"] = df[src["psu"]] if src["psu"] else np.nan
    out["strata"] = df[src["strata"]] if src["strata"] else np.nan
    sex = pd.to_numeric(df[src["sex"]], errors="coerce")
    out["female"] = np.where(sex == 2, 1, np.where(sex == 1, 0, np.nan))
    age = pd.to_numeric(df[src["age"]], errors="coerce") if src["age"] else pd.Series(np.nan, index=df.index)
    age = age.where(age.between(18, 99))
    if src["ageg5"]:
        g5 = pd.to_numeric(df[src["ageg5"]], errors="coerce").map(AGEG5_MID)
        age = age.fillna(g5)
    out["age"] = age
    ch = pd.to_numeric(df[src["children"]], errors="coerce") if src["children"] else pd.Series(np.nan, index=df.index)
    out["nkids"] = ch.where(ch.between(1, 30), np.where(ch == 88, 0, np.nan))
    pr = pd.to_numeric(df[src["pregnant"]], errors="coerce") if src["pregnant"] else pd.Series(np.nan, index=df.index)
    out["pregnant"] = np.where(pr == 1, 1, np.where(pr == 2, 0, np.nan))
    out["mentdays"] = days(df[src["menthlth"]]) if src["menthlth"] else np.nan
    out["physdays"] = days(df[src["physhlth"]]) if src["physhlth"] else np.nan
    out["poordays"] = days(df[src["poorhlth"]]) if src["poorhlth"] else np.nan
    gh = pd.to_numeric(df[src["genhlth"]], errors="coerce") if src["genhlth"] else pd.Series(np.nan, index=df.index)
    out["genhlth"] = gh.where(gh.between(1, 5))
    em = pd.to_numeric(df[src["employ"]], errors="coerce") if src["employ"] else pd.Series(np.nan, index=df.index)
    # 1 employed for wages, 2 self-employed, 3 out of work >1y, 4 out of work <1y, 5 homemaker, 6 student, 7 retired, 8 unable to work
    out["employed"] = np.where(em.isin([1, 2]), 1, np.where(em.between(3, 8), 0, np.nan))
    out["unable_work"] = np.where(em == 8, 1, np.where(em.between(1, 7), 0, np.nan))
    out["homemaker"] = np.where(em == 5, 1, np.where(em.between(1, 8) & (em != 5), 0, np.nan))
    inc = pd.to_numeric(df[src["income"]], errors="coerce") if src["income"] else pd.Series(np.nan, index=df.index)
    out["income_cat"] = inc.where(inc.between(1, 11))
    out["inc_lt25k"] = np.where(inc.between(1, 4), 1, np.where(inc.between(5, 11), 0, np.nan))   # <$25k in INCOME2/3 coding
    ma = pd.to_numeric(df[src["marital"]], errors="coerce") if src["marital"] else pd.Series(np.nan, index=df.index)
    out["married"] = np.where(ma == 1, 1, np.where(ma.between(2, 6), 0, np.nan))
    ed = pd.to_numeric(df[src["educa"]], errors="coerce") if src["educa"] else pd.Series(np.nan, index=df.index)
    out["educ3"] = np.select([ed.between(1, 4), ed == 5, ed == 6], ["hs_or_less", "some_college", "college"], None)
    # race/ethnicity: _RACE (2001+): 1 white NH, 2 black NH, 3 AIAN, 4 Asian, 5 NHPI, 6 other, 7 multi, 8 Hispanic
    rc = pd.to_numeric(df[src["race"]], errors="coerce") if src["race"] else pd.Series(np.nan, index=df.index)
    if src["race"] == "_RACE":
        out["race4"] = np.select([rc == 8, rc == 1, rc == 2, rc.between(3, 7)], ["hispanic", "white", "black", "other"], None)
    else:  # older files: RACE (1 white 2 black ... ) plus HISPANIC (1 yes 2 no); rough map, checked in the log
        hi = pd.to_numeric(df[src["hispanic"]], errors="coerce") if src["hispanic"] else pd.Series(np.nan, index=df.index)
        out["race4"] = np.select([hi == 1, rc == 1, rc == 2, rc.between(3, 9)], ["hispanic", "white", "black", "other"], None)
    hp = pd.to_numeric(df[src["hlthplan"]], errors="coerce") if src["hlthplan"] else pd.Series(np.nan, index=df.index)
    out["insured"] = np.where(hp == 1, 1, np.where(hp == 2, 0, np.nan))
    for k in ("emtsuprt", "lsatisfy"):
        out[k] = pd.to_numeric(df[src[k]], errors="coerce") if src[k] else np.nan
    return out


def read_xpt(path):
    try:
        return pd.read_sas(path, format="xport", encoding="latin-1")
    except Exception as ex:
        print("  read_sas failed on", path.name, ":", ex, "-> retrying without encoding")
        return pd.read_sas(path, format="xport")


def main(dirpath, years):
    files = sorted(Path(dirpath).glob("*.[Xx][Pp][Tt]"))
    if not files:
        sys.exit(f"no .XPT files in {dirpath}; see data/raw/BRFSS_SPEC.md")
    parts = []
    for f in files:
        m = re.search(r"(\d{2,4})", f.stem)
        yy = int(m.group(1)); year = yy if yy > 1900 else (1900 + yy if yy >= 90 else 2000 + yy)
        if year not in years:
            continue
        df = read_xpt(f)
        h = harmonise(df, year)
        h = h[h["age"].between(18, 44) & h["weight"].gt(0) & h["state_fips"].le(56)]
        parts.append(h)
        del df
    d = pd.concat(parts, ignore_index=True)
    d["fmd"] = np.where(d["mentdays"].isna(), np.nan, (d["mentdays"] >= 14).astype(float))
    d["fairpoor"] = np.where(d["genhlth"].isna(), np.nan, (d["genhlth"] >= 4).astype(float))
    d["parent"] = np.where(d["nkids"].isna(), np.nan, (d["nkids"] > 0).astype(float))
    d["mother"] = np.where(d["female"] == 1, d["parent"], 0)
    d["mother_young"] = ((d["mother"] == 1) & (d["age"] <= 34)).astype(int)
    d["agegrp"] = (d["age"] // 5) * 5
    pol = pd.read_csv(RAW / "pfml_policy_dates.csv").set_index("state_fips")
    bs = pd.to_datetime(pol["benefits_start"])
    d["gvar"] = d["state_fips"].map(bs.dt.year.where(bs.dt.month <= 6, bs.dt.year + 1)).fillna(0).astype(int)   # year with >=6 months of benefits
    d["gvar_month"] = d["state_fips"].map(bs.dt.year * 12 + bs.dt.month).fillna(0).astype(int)                   # monthly cohort
    d["ym"] = d["year"] * 12 + d["month"].fillna(6).astype(int)
    d["treated_now"] = ((d["gvar"] > 0) & (d["year"] >= d["gvar"])).astype(int)
    print("\nrows:", len(d), " years:", d.year.min(), "-", d.year.max())
    print("women 18-44 with children per year (mean):", round(d[d.mother == 1].groupby("year").size().mean()))
    print("mentdays mean / fmd share, mothers:", round(d.loc[d.mother == 1, "mentdays"].mean(), 2), round(d.loc[d.mother == 1, "fmd"].mean(), 3))
    d.to_csv(CLEAN / "brfss_adults_1844.csv.gz", index=False)
    d.drop(columns=["psu", "strata"]).to_stata(CLEAN / "brfss_adults_1844.dta", write_index=False, version=118)
    print("wrote", CLEAN / "brfss_adults_1844.csv.gz")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=str(RAW / "brfss"))
    ap.add_argument("--years", default="1993-2024")
    a = ap.parse_args()
    y0, y1 = map(int, a.years.split("-"))
    main(a.dir, set(range(y0, y1 + 1)))
