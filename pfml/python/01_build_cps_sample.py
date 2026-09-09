"""
01_build_cps_sample.py -- women aged 18-44 from the CPS ASEC 2021-2023 person
files (PolicyEngine release assets; raw ASEC persons, no reweighting), with the
age of the youngest own child, marital status, state, labour-supply outcomes,
and the PFML treatment cohort.  Output in CSV and Stata 16 (.dta, version 118).

Same linkage rule as ../../code/02_clean_cps_pe.py, generalised to all women:
children are assigned within the CPS family and the assignment is kept only
when it reproduces the ASEC own-children count exactly (women with no own
children need no linkage).

ASEC income and weeks refer to the calendar year before the survey, so the
panel is indexed by reference year 2020, 2021, 2022.
"""
from pathlib import Path
import numpy as np
import pandas as pd
import h5py

ROOT = Path(__file__).resolve().parents[2]          # repository root
H5 = ROOT / "data" / "raw" / "policyengine" / "h5"
PF = ROOT / "pfml"
OUT = PF / "data" / "clean"; OUT.mkdir(parents=True, exist_ok=True)
TAB = PF / "output" / "tables"; TAB.mkdir(parents=True, exist_ok=True)
YEARS = [2021, 2022, 2023]

PERSON_VARS = ["person_id", "age", "is_female", "person_family_id", "person_household_id",
               "person_marital_unit_id", "cps_race", "is_hispanic", "employment_income",
               "self_employment_income", "weekly_hours_worked", "own_children_in_household",
               "is_full_time_college_student", "is_disabled"]
HH_VARS = ["household_id", "household_weight", "state_fips"]


def load_year(y):
    with h5py.File(H5 / f"cps_{y}.h5", "r") as f:
        p = pd.DataFrame({v: f[v][:] for v in PERSON_VARS})
        h = pd.DataFrame({v: f[v][:] for v in HH_VARS})
    p = p.merge(h, left_on="person_household_id", right_on="household_id", how="left")
    p["survey_year"] = y
    p["year"] = y - 1  # ASEC reference year for income / weeks
    return p


def build():
    p = pd.concat([load_year(y) for y in YEARS], ignore_index=True)
    p["own_children_in_household"] = p["own_children_in_household"].fillna(0).astype(int)
    mu = p.groupby(["survey_year", "person_marital_unit_id"])["person_id"].transform("size")
    p["married"] = ((mu == 2) & p["person_marital_unit_id"].notna()).astype(int)
    fam = ["survey_year", "person_family_id"]

    women = p[(p["is_female"]) & p["age"].between(18, 44)].copy()
    # mothers needing linkage
    p["target"] = ((p["is_female"]) & p["age"].between(18, 44) & (p["own_children_in_household"] > 0)).astype(int)
    n_target = p.groupby(fam)["target"].transform("sum")
    mom_age = p.assign(_a=p["age"].where(p["target"] == 1)).groupby(fam)["_a"].transform("max")
    p["cand"] = ((p["target"] == 0) & (p["own_children_in_household"] == 0) & (p["married"] == 0)
                 & (p["age"] <= mom_age - 13)).astype(int)
    n_cand = p.groupby(fam)["cand"].transform("sum")
    moms = p[p["target"] == 1].copy()
    moms["match"] = ((n_target[moms.index] == 1) & (n_cand[moms.index] == moms["own_children_in_household"])).astype(int)
    link = moms.groupby("survey_year")["match"].agg(["size", "sum"]).rename(columns={"size": "mothers", "sum": "linked"})
    link["retention"] = link["linked"] / link["mothers"]
    print("linkage:\n", link.round(3).to_string()); link.to_csv(TAB / "linkage_rates.csv")

    kids = p[p["cand"] == 1].merge(moms.loc[moms["match"] == 1, fam + ["person_id"]]
                                   .rename(columns={"person_id": "mother_id"}), on=fam)
    kf = kids.groupby(["survey_year", "mother_id"])["age"].agg(age_youngest="min", age_oldest="max", nkids="size")
    kf["nkids_lt6"] = kids[kids["age"] < 6].groupby(["survey_year", "mother_id"]).size()
    kf["nkids_lt6"] = kf["nkids_lt6"].fillna(0).astype(int)
    kf["has_infant"] = (kf["age_youngest"] < 1).astype(int)

    w = women.merge(kf, left_on=["survey_year", "person_id"], right_index=True, how="left")
    unlinked = w["own_children_in_household"].gt(0) & w["nkids"].isna()
    print(f"women 18-44: {len(w):,}; mothers dropped for failed linkage: {int(unlinked.sum()):,}")
    w = w[~unlinked].copy()
    w["nkids"] = w["nkids"].fillna(0).astype(int)
    w["nkids_lt6"] = w["nkids_lt6"].fillna(0).astype(int)
    w["has_infant"] = w["has_infant"].fillna(0).astype(int)
    w["mother"] = (w["nkids"] > 0).astype(int)
    w["mother_lt6"] = (w["nkids_lt6"] > 0).astype(int)

    labinc = w["employment_income"].astype(float) + w["self_employment_income"].astype(float)
    d = pd.DataFrame({
        "year": w["year"], "survey_year": w["survey_year"], "state_fips": w["state_fips"].astype(int),
        "weight": w["household_weight"].astype(float),
        "worked": (labinc > 0).astype(int), "hours": w["weekly_hours_worked"].astype(float),
        "labinc": labinc / 1000.0, "fulltime": (w["weekly_hours_worked"] >= 35).astype(int),
        "age": w["age"].astype(int), "married": w["married"],
        "black": (w["cps_race"] == 2).astype(int), "hispanic": w["is_hispanic"].astype(bool).astype(int),
        "other": ((w["cps_race"] >= 3) & (w["cps_race"] != 2)).astype(int),
        "student": w["is_full_time_college_student"].astype(bool).astype(int),
        "disabled": w["is_disabled"].astype(bool).astype(int),
        "mother": w["mother"], "mother_lt6": w["mother_lt6"], "has_infant": w["has_infant"],
        "nkids": w["nkids"], "nkids_lt6": w["nkids_lt6"], "age_youngest": w["age_youngest"],
    })
    pol = pd.read_csv(PF / "data" / "raw" / "pfml_policy_dates.csv")
    g = pol.set_index("state_fips")["cohort_asec_refyear"]
    d["gvar"] = d["state_fips"].map(g).fillna(0).astype(int)      # 0 = never treated (csdid convention)
    d["gvar_full"] = d["state_fips"].map(pol.set_index("state_fips")["first_full_ref_year"]).fillna(0).astype(int)
    d["treated_now"] = ((d["gvar"] > 0) & (d["year"] >= d["gvar"])).astype(int)
    return d


if __name__ == "__main__":
    d = build()
    print("\nrows by year:", d.groupby("year").size().to_dict())
    print("cohorts (gvar) among women 18-44, unweighted rows:\n", d.groupby("gvar").size().to_string())
    ma = d[(d.state_fips == 25) & (d.mother_lt6 == 1)].groupby("year").size(); ct = d[(d.state_fips == 9) & (d.mother_lt6 == 1)].groupby("year").size()
    print("\nmothers of children <6 per year: MA", ma.to_dict(), " CT", ct.to_dict())
    d.to_csv(OUT / "cps_women_1844.csv.gz", index=False)
    labels = {"year": "ASEC reference year", "gvar": "PFML cohort: first ref. year with benefits (0 = never)",
              "worked": "Worked for pay in ref. year", "hours": "Usual weekly hours", "labinc": "Labour income, $1000s",
              "mother_lt6": "Own child under 6 in household", "has_infant": "Own child under 1", "weight": "ASEC household weight"}
    d.to_stata(OUT / "cps_women_1844.dta", write_index=False, version=118, variable_labels=labels)
    print("wrote", OUT / "cps_women_1844.csv.gz", "and .dta (Stata 16 format 118)")
