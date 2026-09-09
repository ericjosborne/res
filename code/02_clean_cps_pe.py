"""
02_clean_cps_pe.py
------------------
Construct an Angrist-Evans-type sample of mothers from the CPS ASEC person
files redistributed by PolicyEngine (GitHub release assets of
PolicyEngine/policyengine-us-data: cps_2021.h5, cps_2022.h5, cps_2023.h5).

Why PolicyEngine?  In this build environment the Census Bureau, IPUMS, NBER
and BLS hosts are blocked, while GitHub release assets are not.  The
PolicyEngine "cps_YYYY.h5" files are the raw CPS ASEC person records with
PolicyEngine variable names (no reweighting; the "enhanced" files are NOT
used).  Income variables refer to the calendar year before the survey.
Replace with an IPUMS-CPS/ACS extract for the paper (see 90_ipums_extract.py).

Mother-child linkage.  The files carry no parent pointers, only
`own_children_in_household` (a count derived from the ASEC parent line
numbers) and family / marital-unit identifiers.  We therefore assign children
within the CPS family and KEEP ONLY families in which the assignment
reproduces the mother's own-children count exactly.  The retention rate is
reported and stored in output/tables/cps_pe_linkage.csv.

Output: data/clean/cps_pe_mothers.csv.gz in the harmonised layout of
01_clean_1980.py, plus `married`, `state_fips`, `nkids_lt6`, `age_youngest`,
`oldest_lt18`.
"""
from pathlib import Path
import numpy as np
import pandas as pd
import h5py

ROOT = Path(__file__).resolve().parents[1]
H5 = ROOT / "data" / "raw" / "policyengine" / "h5"
OUT = ROOT / "data" / "clean"
TAB = ROOT / "output" / "tables"
OUT.mkdir(parents=True, exist_ok=True)
TAB.mkdir(parents=True, exist_ok=True)

YEARS = [2021, 2022, 2023]  # cps_2024.h5 is a copy of the 2023 ASEC persons (checked)

PERSON_VARS = ["person_id", "age", "is_female", "person_family_id", "person_household_id",
               "person_marital_unit_id", "person_tax_unit_id", "is_household_head",
               "cps_race", "is_hispanic", "employment_income", "self_employment_income",
               "weekly_hours_worked", "own_children_in_household", "is_separated",
               "is_widowed", "is_full_time_college_student"]
HH_VARS = ["household_id", "household_weight", "state_fips"]


def load_year(y):
    with h5py.File(H5 / f"cps_{y}.h5", "r") as f:
        p = pd.DataFrame({v: f[v][:] for v in PERSON_VARS})
        h = pd.DataFrame({v: f[v][:] for v in HH_VARS})
    p = p.merge(h, left_on="person_household_id", right_on="household_id", how="left")
    p["year"] = y
    return p


def link_children(p):
    """Assign children to mothers inside CPS families; keep exact-count matches."""
    p = p.copy()
    p["own_children_in_household"] = p["own_children_in_household"].fillna(0).astype(int)
    # marital unit size (2 => married, spouse present in PolicyEngine's construction)
    mu = p.groupby(["year", "person_marital_unit_id"])["person_id"].transform("size")
    p["married"] = ((mu == 2) & p["person_marital_unit_id"].notna()).astype(int)

    fam_key = ["year", "person_family_id"]
    # target mothers: women 21-35 with >=2 own children in the household
    p["target"] = ((p["is_female"]) & p["age"].between(21, 35)
                   & (p["own_children_in_household"] >= 2)).astype(int)
    n_target_fam = p.groupby(fam_key)["target"].transform("sum")
    # candidate children: family members with no own children of their own, not
    # married, and at least 13 years younger than the target mother
    mom_age = p["age"].where(p["target"] == 1)
    mom_age = p.assign(_ma=mom_age).groupby(fam_key)["_ma"].transform("max")
    p["cand_child"] = ((p["target"] == 0) & (p["own_children_in_household"] == 0)
                       & (p["married"] == 0) & (p["age"] <= mom_age - 13)).astype(int)
    n_cand = p.groupby(fam_key)["cand_child"].transform("sum")

    moms = p[(p["target"] == 1)].copy()
    moms["n_target_fam"] = n_target_fam[moms.index]
    moms["n_cand"] = n_cand[moms.index]
    moms["match"] = ((moms["n_target_fam"] == 1)
                     & (moms["n_cand"] == moms["own_children_in_household"])).astype(int)

    linkage = (moms.groupby("year")
               .agg(target_mothers=("match", "size"),
                    one_mother_families=("n_target_fam", lambda s: (s == 1).sum()),
                    exact_matches=("match", "sum"))
               .assign(retention=lambda d: d["exact_matches"] / d["target_mothers"]))
    print("\nmother-child linkage by survey year:\n", linkage.round(3).to_string())
    linkage.to_csv(TAB / "cps_pe_linkage.csv")

    keep = moms[moms["match"] == 1]
    kids = p[(p["cand_child"] == 1)].merge(
        keep[fam_key + ["person_id"]].rename(columns={"person_id": "mother_id"}),
        on=fam_key, how="inner")
    kids = kids.sort_values(["mother_id", "age"], ascending=[True, False])
    kids["birth_order"] = kids.groupby("mother_id").cumcount() + 1

    g = kids.groupby("mother_id")
    first = kids[kids["birth_order"] == 1].set_index("mother_id")
    second = kids[kids["birth_order"] == 2].set_index("mother_id")
    third_age = kids[kids["birth_order"] == 3].set_index("mother_id")["age"]
    feats = pd.DataFrame({
        "kids": g.size(),
        "boy1st": (~first["is_female"].astype(bool)).astype(int),
        "boy2nd": (~second["is_female"].astype(bool)).astype(int),
        "age_first": first["age"], "age_second": second["age"],
        "age_youngest": g["age"].min(),
        "nkids_lt6": g["age"].apply(lambda s: (s < 6).sum()),
    })
    feats["multi2nd"] = (feats["age_second"] == third_age.reindex(feats.index)).fillna(False).astype(int)
    out = keep.set_index("person_id").join(feats, how="inner")
    return out.reset_index(drop=True)


def harmonise(m):
    d = pd.DataFrame(index=m.index)
    d["sample"] = "cps_pe"
    d["year"] = m["year"]
    d["weight"] = m["household_weight"]
    d["morekids"] = (m["kids"] > 2).astype(int)
    d["kids"] = m["kids"]
    d["boy1st"] = m["boy1st"]
    d["boy2nd"] = m["boy2nd"]
    d["samesex"] = (m["boy1st"] == m["boy2nd"]).astype(int)
    d["twoboys"] = ((m["boy1st"] == 1) & (m["boy2nd"] == 1)).astype(int)
    d["twogirls"] = ((m["boy1st"] == 0) & (m["boy2nd"] == 0)).astype(int)
    d["multi2nd"] = m["multi2nd"]
    labinc = (m["employment_income"].astype(float) + m["self_employment_income"].astype(float))
    d["worked"] = (labinc > 0).astype(int)
    d["weeks"] = np.nan
    d["hours"] = m["weekly_hours_worked"].astype(float)
    d["labinc"] = labinc / 1000.0
    d["age"] = m["age"].astype(int)
    d["agefst"] = m["age"] - m["age_first"]
    # PolicyEngine cps_race: 1 white, 2 black, 3 AIAN, 4 Asian, 5 HPI, 6+ multiracial
    d["black"] = (m["cps_race"] == 2).astype(int)
    d["hispanic"] = m["is_hispanic"].astype(bool).astype(int)
    d["other"] = ((m["cps_race"] >= 3) & (d["black"] == 0)).astype(int)
    d["educ"] = np.nan
    d["nonmomi"] = np.nan
    d["married"] = m["married"]
    d["state_fips"] = m["state_fips"]
    d["nkids_lt6"] = m["nkids_lt6"]
    d["age_youngest"] = m["age_youngest"]
    d["oldest_lt18"] = (m["age_first"] < 18).astype(int)
    d["age_second"] = m["age_second"]
    return d


if __name__ == "__main__":
    frames = [load_year(y) for y in YEARS]
    p = pd.concat(frames, ignore_index=True)
    print("persons loaded:", {y: int((p.year == y).sum()) for y in YEARS})
    m = link_children(p)
    d = harmonise(m)
    # AE98 restrictions: second child at least 1 year old; mother 21-35 (already)
    n0 = len(d)
    d = d[d["age_second"] >= 1].drop(columns="age_second")
    print(f"\nafter requiring second child >= 1 year old: {len(d):,} (from {n0:,})")
    print("plausibility: age at first birth distribution\n", d["agefst"].describe().round(2).to_string())
    print("share with implausible agefst (<13):", (d["agefst"] < 13).mean().round(4))
    d = d[d["agefst"] >= 13]
    print("\nmeans (weighted):")
    w = d["weight"]
    for c in ["morekids", "samesex", "boy1st", "boy2nd", "worked", "hours", "married", "black", "hispanic", "other", "multi2nd"]:
        print(f"   {c:10s} {np.average(d[c], weights=w):.4f}")
    print("married share:", d["married"].mean().round(3), " n married:", int(d["married"].sum()))
    d.to_csv(OUT / "cps_pe_mothers.csv.gz", index=False)
    print("\nwrote", OUT / "cps_pe_mothers.csv.gz", "rows:", len(d))
