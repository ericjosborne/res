"""
20_build_nsch.py -- build the NSCH analysis file for the paid-leave parental
mental-health design (data/raw/NSCH_SPEC.md).

Unit of observation: sampled child, 2016-2024 topical files. Exposure is
defined at the child's birth: the child is treated if born after PFML
benefits were available in the state of residence. Cohort (for
Callaway-Sant'Anna) is the state's first birth year with >= 6 months of
benefits; "time" is the child's birth year. The estimator then compares
mothers of children born in birth-year t in cohort-g states with mothers of
children born the same year in never-treated states, relative to the last
pre-policy birth year -- a birth-cohort event study.  Survey year fixed
effects are added as a covariate in Stata (drimp) and absorbed in Python by
running within child-age bands.

Written without the files; the variable map logs which source column was
used for each concept, per year.
"""
import argparse, re, sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"; CLEAN = ROOT / "data" / "clean"; CLEAN.mkdir(parents=True, exist_ok=True)

MAP = {
    "state": ["FIPSST"], "weight": ["FWC"], "stratum": ["STRATUM"], "hhid": ["HHID"],
    "age": ["SC_AGE_YEARS"], "sex": ["SC_SEX"],
    "a1_rel": ["A1_RELATION"], "a1_sex": ["A1_SEX"], "a1_age": ["A1_AGE"], "a1_mar": ["A1_MARITAL"],
    "a1_emp": ["A1_EMPLOYED"], "a1_grade": ["A1_GRADE"], "a1_ment": ["A1_MENTHEALTH"], "a1_phys": ["A1_PHYSHEALTH"],
    "a2_rel": ["A2_RELATION"], "a2_sex": ["A2_SEX"], "a2_ment": ["A2_MENTHEALTH"], "a2_phys": ["A2_PHYSHEALTH"],
    "k8q30": ["K8Q30"], "k8q31": ["K8Q31"], "k8q32": ["K8Q32"], "k8q34": ["K8Q34"], "k8q35": ["K8Q35"],
    "chealth": ["K2Q01"], "prevvisit": ["K6Q20"],
    "everbf": ["EVERBREASTFED"], "bf_mo": ["BREASTFEDEND_MO_S"], "bf_wk": ["BREASTFEDEND_WK_S"],
    "family": ["FAMILY_R"], "race": ["SC_RACE_R"], "hisp": ["SC_HISPANIC_R"], "currcov": ["CURRCOV"],
}


def pick(df, names):
    for n in names:
        if n in df.columns:
            return n
    return None


def num(df, col):
    return pd.to_numeric(df[col], errors="coerce") if col else pd.Series(np.nan, index=df.index)


def harmonise(df, year):
    df.columns = [c.upper() for c in df.columns]
    src = {k: pick(df, v) for k, v in MAP.items()}
    missing = [k for k, v in src.items() if v is None]
    print(f"{year}: n={len(df):,}; missing concepts: {missing if missing else 'none'}")
    o = pd.DataFrame(index=df.index)
    o["survey_year"] = year
    o["state_fips"] = num(df, src["state"]).astype("Int64")
    o["weight"] = num(df, src["weight"]); o["stratum"] = df[src["stratum"]] if src["stratum"] else np.nan
    o["child_age"] = num(df, src["age"]); o["child_female"] = (num(df, src["sex"]) == 2).astype(float)
    # field period runs roughly June (year) to January (year+1); a child aged a was born, on average,
    # in year - a - 0.3; use year - age for age-in-years and flag the half-year uncertainty
    o["birth_year"] = (year - o["child_age"]).astype("Int64")
    a1rel = num(df, src["a1_rel"]); a1sex = num(df, src["a1_sex"])
    o["a1_parent"] = a1rel.isin([1]).astype(float)               # 1 = biological or adoptive parent
    o["a1_mother"] = ((a1rel == 1) & (a1sex == 2)).astype(float)
    o["a1_father"] = ((a1rel == 1) & (a1sex == 1)).astype(float)
    o["a1_age"] = num(df, src["a1_age"])
    o["a1_married"] = (num(df, src["a1_mar"]) == 1).astype(float).where(num(df, src["a1_mar"]).notna())
    o["a1_employed"] = (num(df, src["a1_emp"]) == 1).astype(float).where(num(df, src["a1_emp"]).notna())
    g = num(df, src["a1_grade"])
    o["a1_educ3"] = np.select([g <= 3, g.between(4, 6), g >= 7], ["hs_or_less", "some_college", "college"], None)  # verify codes in codebook
    for k in ("a1_ment", "a1_phys", "a2_ment", "a2_phys"):
        v = num(df, src[k]); o[k] = v.where(v.between(1, 5))
    o["a1_ment_fairpoor"] = np.where(o["a1_ment"].isna(), np.nan, (o["a1_ment"] >= 4).astype(float))
    o["a1_ment_excellent"] = np.where(o["a1_ment"].isna(), np.nan, (o["a1_ment"] == 1).astype(float))
    a2rel = num(df, src["a2_rel"]); a2sex = num(df, src["a2_sex"])
    o["a2_father"] = ((a2rel == 1) & (a2sex == 1)).astype(float)
    for k in ("k8q30", "k8q31", "k8q32", "k8q34", "k8q35"):
        v = num(df, src[k]); o[k] = v.where(v.between(1, 5))
    o["parent_stress"] = o[["k8q31", "k8q32", "k8q34"]].mean(axis=1)   # higher = more stress (verify direction)
    v = num(df, src["chealth"]); o["child_health"] = v.where(v.between(1, 5)); o["child_fairpoor"] = (o["child_health"] >= 4).astype(float).where(o["child_health"].notna())
    o["prev_visit"] = (num(df, src["prevvisit"]) == 1).astype(float).where(num(df, src["prevvisit"]).notna())
    o["everbf"] = (num(df, src["everbf"]) == 1).astype(float).where(num(df, src["everbf"]).notna())
    o["bf_weeks"] = num(df, src["bf_mo"]) * 4.33 + num(df, src["bf_wk"]).fillna(0)
    fpl = [c for c in df.columns if re.fullmatch(r"FPL_I\d", c)]
    o["fpl"] = df[fpl].apply(pd.to_numeric, errors="coerce").mean(axis=1) if fpl else np.nan
    o["fpl_lt200"] = (o["fpl"] < 200).astype(float).where(o["fpl"].notna())
    r = num(df, src["race"]); h = num(df, src["hisp"])
    o["race4"] = np.select([h == 1, r == 1, r == 2, r >= 3], ["hispanic", "white", "black", "other"], None)
    o["insured"] = (num(df, src["currcov"]) == 1).astype(float).where(num(df, src["currcov"]).notna())
    return o


def main(dirpath):
    files = sorted(Path(dirpath).glob("*"))
    parts = []
    for f in files:
        m = re.search(r"(20\d\d)", f.name)
        if not m or f.suffix.lower() not in (".dta", ".csv", ".sas7bdat"):
            continue
        year = int(m.group(1))
        df = pd.read_stata(f, convert_categoricals=False) if f.suffix.lower() == ".dta" else \
             pd.read_csv(f, low_memory=False) if f.suffix.lower() == ".csv" else pd.read_sas(f)
        parts.append(harmonise(df, year))
    if not parts:
        sys.exit(f"no NSCH files in {dirpath}; see data/raw/NSCH_SPEC.md")
    d = pd.concat(parts, ignore_index=True)
    pol = pd.read_csv(RAW / "pfml_policy_dates.csv").set_index("state_fips")
    bs = pd.to_datetime(pol["benefits_start"])
    gcal = bs.dt.year.where(bs.dt.month <= 6, bs.dt.year + 1)           # first calendar year with >= 6 months of benefits
    d["gvar"] = d["state_fips"].map(gcal).fillna(0).astype(int)          # cohort in birth-year time
    d["year"] = d["birth_year"].astype(int)                              # time index for csdid = birth year
    d["exposed_at_birth"] = ((d["gvar"] > 0) & (d["year"] >= d["gvar"])).astype(int)
    d["mother"] = d["a1_mother"]; d["father"] = d["a1_father"]
    print("\nrows:", len(d), " birth years:", d.year.min(), "-", d.year.max())
    print("respondent is mother:", round(d.a1_mother.mean(), 3), " father:", round(d.a1_father.mean(), 3))
    print("A1 mental health fair/poor, mothers of 0-5:", round(d.loc[(d.a1_mother == 1) & (d.child_age <= 5), "a1_ment_fairpoor"].mean(), 3))
    print("exposed children by cohort:\n", d[d.gvar > 0].groupby("gvar")["exposed_at_birth"].agg(["size", "sum"]).to_string())
    d.to_csv(CLEAN / "nsch_children.csv.gz", index=False)
    d.drop(columns=["stratum"]).to_stata(CLEAN / "nsch_children.dta", write_index=False, version=118)
    print("wrote", CLEAN / "nsch_children.csv.gz")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--dir", default=str(RAW / "nsch"))
    main(ap.parse_args().dir)
