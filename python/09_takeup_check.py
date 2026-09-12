"""09_takeup_check.py -- does PFML raise 'employed but absent from work' in the March survey week
among parents of infants?  First-stage check on the CPS ASEC extract (docs/results.md 7.2).

Time = survey year (March survey week); cohort = first survey year in which benefits were
available at the survey week (benefits_start on or before March of that year).
"""
import importlib.util, sys
from pathlib import Path
import numpy as np, pandas as pd
PF = Path(__file__).resolve().parents[1]; RAW = PF / "data" / "raw"; CLEAN = PF / "data" / "clean"; TAB = PF / "output" / "tables"
spec = importlib.util.spec_from_file_location("csdid", PF / "python" / "02_csdid.py"); cs = importlib.util.module_from_spec(spec); spec.loader.exec_module(cs)

out = CLEAN / "cps_asec_infant_parents.csv.gz"
if not out.exists():
    cols = ["YEAR", "STATEFIP", "ASECWT", "AGE", "SEX", "NCHILD", "YNGCH", "EMPSTAT", "LABFORCE", "UHRSWORKT", "MARST", "RACE", "HISPAN", "EDUC", "HFLAG"]
    df = pd.read_csv(next(RAW.glob("cps_*.csv")), usecols=cols)
    df = df[(df.AGE.between(18, 54)) & (df.YNGCH.isin([0, 1, 2]) & (df.NCHILD > 0) | ((df.NCHILD == 0) & df.AGE.between(18, 44)))]
    d = pd.DataFrame({"survey_year": df.YEAR, "state_fips": df.STATEFIP, "weight": df.ASECWT, "age": df.AGE, "female": (df.SEX == 2).astype(int),
                      "age_youngest": df.YNGCH.where(df.NCHILD > 0, np.nan), "nchild": df.NCHILD,
                      "employed": df.EMPSTAT.isin([10, 12]).astype(int), "atwork": (df.EMPSTAT == 10).astype(int), "absent": (df.EMPSTAT == 12).astype(int),
                      "inlf": (df.LABFORCE == 2).astype(int), "hours_now": df.UHRSWORKT.where(df.UHRSWORKT < 997, np.nan),
                      "married": df.MARST.isin([1, 2]).astype(int), "college": (df.EDUC >= 111).astype(int)})
    d["absent_if_emp"] = d.absent.where(d.employed == 1)
    pol = pd.read_csv(RAW / "pfml_policy_dates.csv").set_index("state_fips"); bs = pd.to_datetime(pol["benefits_start"])
    gmar = bs.dt.year.where(bs.dt.month <= 3, bs.dt.year + 1)          # first March survey week with benefits available
    d["gvar"] = d.state_fips.map(gmar).fillna(0).astype(int); d["year"] = d.survey_year
    d.to_csv(out, index=False); print("wrote", out, len(d))
d = pd.read_csv(out)
d.loc[d.gvar > 2025, "gvar"] = 0

samples = {
    "mothers_infant": (d.female == 1) & (d.age_youngest == 0) & d.age.between(18, 44),
    "fathers_infant": (d.female == 0) & (d.age_youngest == 0) & d.age.between(18, 54),
    "mothers_age1": (d.female == 1) & (d.age_youngest == 1) & d.age.between(18, 44),
    "mothers_age2": (d.female == 1) & (d.age_youngest == 2) & d.age.between(18, 44),
    "childless_w": (d.female == 1) & (d.nchild == 0),
}
rows = []
for s, mask in samples.items():
    for y in (["absent", "atwork", "employed", "inlf", "absent_if_emp"] if s != "childless_w" else ["absent", "employed"]):
        x = d[mask & d[y].notna()].copy()
        csm, att, E, G, C, S = cs.run(x, y, s, False, [-6, 6], 299)
        tag = f"takeup_{s}_{y}"
        for name, df_ in [("event", E), ("group", G), ("simple", S)]:
            df_.to_csv(TAB / f"{tag}_{name}.csv", index=False)
        pre = x[(x.gvar > 0) & (x.year < x.gvar)]; premean = np.average(pre[y], weights=pre.weight)
        rows.append({"sample": s, "outcome": y, "pre mean": premean, "ATT": S.iloc[0, 0], "se": S.iloc[0, 1], "n": len(x),
                     "pre e=-3..-1": E[E.e.between(-3, -1)].estimate.mean(), "post e=0..3": E[E.e.between(0, 3)].estimate.mean()})
        print(f"{s:16s} {y:14s} pre={premean:.3f} ATT={S.iloc[0,0]:+.4f} ({S.iloc[0,1]:.4f}) n={len(x):,}", flush=True)
R = pd.DataFrame(rows); R.to_csv(TAB / "takeup_summary.csv", index=False)
print(cs.to_markdown(R, ".4f", index=False))
