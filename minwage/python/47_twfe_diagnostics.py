"""47_twfe_diagnostics.py -- what drives the two-way fixed effects coefficient on the log minimum wage for enrollment and
for 'neither enrolled nor employed' (Appendix table).  Variants of the TWFE regression of python/46_regressions.py:
all months; school months (Sept-May); summer months (June-Aug); raising units only (units whose minimum changed
2010-2026, i.e. dropping the federal-floor states); census-region x month fixed effects; 2010-2019; drop 2020-2021;
a 24-month lead of the log minimum as a placebo (its own coefficient reported); unit-specific linear trends.
Writes output/tables/mw_twfe_diagnostics.csv and paper/tables/tabA_twfe_diag.tex."""
import warnings; warnings.filterwarnings("ignore")
from pathlib import Path
import numpy as np, pandas as pd, pyfixest as pf
PF = Path(__file__).resolve().parents[1]; CLEAN = PF / "data" / "clean"; MW = PF / "data" / "raw" / "minwage"; TAB = PF / "output" / "tables"; PT = PF / "paper" / "tables"
d = pd.read_csv(CLEAN / "cps_monthly_1624.csv.gz", usecols=["year", "month", "ym", "state_fips", "county", "weight", "age", "female", "black", "hispanic", "enrolled", "employed"])
d = d[d.age.between(16, 19) & (d.year >= 2010)].copy(); d["county"] = d.county.fillna(0).astype(int)
U = pd.read_csv(MW / "unit_mw_monthly.csv"); U["ymi"] = U.ym.str[:4].astype(int) * 12 + U.ym.str[5:7].astype(int) - 1
cu = set(U.unit[U.kind == "county"]); d["geo"] = np.where(d.county.isin(cu), d.county, d.state_fips)
Um = U[["unit", "ymi", "mw"]].rename(columns={"unit": "geo", "ymi": "ym"})
d = d.merge(Um, on=["geo", "ym"], how="left"); d["log_mw"] = np.log(d.mw)
lead = Um.copy(); lead["ym"] = lead.ym - 24; lead = lead.rename(columns={"mw": "mw_f24"}); d = d.merge(lead, on=["geo", "ym"], how="left"); d["log_mw_f24"] = np.log(d.mw_f24)
d["neither"] = (1 - d.enrolled) * (1 - d.employed); d["t"] = d.ym - d.ym.min()
REG = {1: [9, 23, 25, 33, 44, 50], 2: [17, 18, 26, 27, 29, 31, 38, 39, 46, 55], 3: [1, 5, 10, 11, 12, 13, 21, 22, 24, 28, 37, 40, 45, 47, 48, 51, 54], 4: [2, 4, 6, 8, 15, 16, 30, 32, 35, 41, 49, 53, 56]}
d["reg_ym"] = d.state_fips.map({s: k for k, v in REG.items() for s in v}).astype(str) + "_" + d.ym.astype(str)
rng = d.groupby("geo").log_mw.agg(lambda s: s.max() - s.min()); d["raiser"] = d.geo.map(rng > 0.01)
summer = d.month.between(6, 8)
VARIANTS = [("All months (baseline)", None, "geo + ym", "log_mw", "log_mw"),
            ("School months, September--May", ~summer, "geo + ym", "log_mw", "log_mw"),
            ("Summer months, June--August", summer, "geo + ym", "log_mw", "log_mw"),
            ("Raising units only (drop federal-floor states)", d.raiser, "geo + ym", "log_mw", "log_mw"),
            ("School months, raising units only", (~summer) & d.raiser, "geo + ym", "log_mw", "log_mw"),
            ("Census region $\\times$ month fixed effects", None, "geo + reg_ym", "log_mw", "log_mw"),
            ("2010--2019", d.year <= 2019, "geo + ym", "log_mw", "log_mw"),
            ("Drop 2020--2021", ~d.year.between(2020, 2021), "geo + ym", "log_mw", "log_mw"),
            ("24-month lead of log minimum (coefficient on the lead)", None, "geo + ym", "log_mw + log_mw_f24", "log_mw_f24"),
            ("Unit-specific linear trends", None, "geo[t] + ym", "log_mw", "log_mw")]
AGES = {"1617": (16, 17), "1819": (18, 19), "1619": (16, 19)}
rows = []
for name, mask, fe, rhs, coef in VARIANTS:
    for y in ("enrolled", "neither"):
        for a, (a0, a1) in AGES.items():
            x = d[d.age.between(a0, a1) & d.log_mw.notna() & (d.weight > 0)]
            if "f24" in rhs: x = x[x.log_mw_f24.notna()]
            if mask is not None: x = x[mask.loc[x.index]]
            m = pf.feols(f"{y} ~ {rhs} + C(age) + female + black + hispanic | {fe}", data=x, weights="weight", vcov={"CRV1": "state_fips"})
            rows.append({"variant": name, "outcome": y, "ages": a, "b": float(m.coef()[coef]), "se": float(m.se()[coef]), "n": len(x)})
            print(f"{name[:45]:45s} {y:9s} {a} {rows[-1]['b']:+.4f} ({rows[-1]['se']:.4f}) n={len(x):,}", flush=True)
R = pd.DataFrame(rows); R.to_csv(TAB / "mw_twfe_diagnostics.csv", index=False)
def st(b, se): z = abs(b / se); return "$^{***}$" if z > 2.576 else "$^{**}$" if z > 1.96 else "$^{*}$" if z > 1.645 else ""
L = []
for name, *_ in VARIANTS:
    l1, l2 = [name], [""]
    for y in ("enrolled", "neither"):
        for a in AGES:
            r = R[(R.variant == name) & (R.outcome == y) & (R.ages == a)].iloc[0]; l1.append(f"{r.b:.3f}{st(r.b, r.se)}"); l2.append(f"({r.se:.3f})")
    L += [" & ".join(l1) + " \\\\", " & ".join(l2) + " \\\\"]
(PT / "tabA_twfe_diag.tex").write_text("\\begin{tabular}{lcccccc}\n\\toprule\n & \\multicolumn{3}{c}{Enrolled} & \\multicolumn{3}{c}{Neither enrolled nor employed} \\\\\n\\cmidrule(lr){2-4}\\cmidrule(lr){5-7}\n & 16--17 & 18--19 & 16--19 & 16--17 & 18--19 & 16--19 \\\\\n\\midrule\n" + "\n".join(L) + "\n\\bottomrule\n\\end{tabular}\n")
print("done")
