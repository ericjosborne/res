"""52_teen_trends_annual.py -- annual weighted means of teen employment, enrollment and school-work status by age band,
1994-2025, streamed from the raw IPUMS extract.  Used only for the descriptive trends figure (Figure 1), which shows the
decline in teen employment before the 2010-2025 analysis window; no estimate uses these years.
Writes data/clean/teen_trends_annual.csv."""
from pathlib import Path
import numpy as np, pandas as pd
PF = Path(__file__).resolve().parents[1]; src = PF / "data" / "raw" / "monthly" / "cps_00091.csv.gz"; out = PF / "data" / "clean" / "teen_trends_annual.csv"
parts = []
for ch in pd.read_csv(src, usecols=["YEAR", "AGE", "WTFINL", "SCHLCOLL", "EMPSTAT", "LABFORCE"], chunksize=2_000_000):
    ch = ch[ch.AGE.between(16, 19) & (ch.SCHLCOLL != 0) & (ch.WTFINL > 0)]
    if len(ch) == 0: continue
    d = pd.DataFrame({"year": ch.YEAR, "band": np.where(ch.AGE <= 17, "1617", "1819"), "w": ch.WTFINL})
    d["enrolled"] = ch.SCHLCOLL.between(1, 4).astype(int); d["employed"] = ch.EMPSTAT.isin([10, 12]).astype(int); d["inlf"] = (ch.LABFORCE == 2).astype(int)
    d["enr_emp"] = d.enrolled * d.employed; d["enr_only"] = d.enrolled * (1 - d.employed); d["emp_only"] = (1 - d.enrolled) * d.employed; d["neither"] = (1 - d.enrolled) * (1 - d.employed)
    for k in ["enrolled", "employed", "inlf", "enr_emp", "enr_only", "emp_only", "neither"]: d[k] = d[k] * d.w
    parts.append(d.groupby(["year", "band"]).sum().reset_index())
A = pd.concat(parts).groupby(["year", "band"]).sum().reset_index()
P = A.groupby("year").sum().reset_index(); P["band"] = "1619"; A = pd.concat([A, P], ignore_index=True)
for k in ["enrolled", "employed", "inlf", "enr_emp", "enr_only", "emp_only", "neither"]: A[k] = A[k] / A.w
A.sort_values(["band", "year"]).to_csv(out, index=False); print("wrote", out, len(A), "rows;", A.year.min(), "-", A.year.max())
