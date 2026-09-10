"""
06_summarise_het.py -- collect the heterogeneity runs (05_heterogeneity.sh)
into one table per outcome and a coefficient plot.
Output: output/tables/het_summary.csv|md, output/figures/het_worked.png, het_has_infant.png
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, str(Path(__file__).resolve().parent))
from aelib import PALETTE, INK, INK2, GRID, style_axes, to_markdown, fmt

ROOT = Path(__file__).resolve().parents[1]
TAB = ROOT / "output" / "tables"; FIG = ROOT / "output" / "figures"
CLEAN = ROOT / "data" / "clean" / "cps_asec_women_1844.csv.gz"

GROUPS = [("educ_hs", "Education: HS or less", "Education"), ("educ_some", "Education: some college", "Education"),
          ("educ_college", "Education: BA or more", "Education"),
          ("ofi_low", "Other family income: bottom tercile", "Other family income"), ("ofi_mid", "Other family income: middle", "Other family income"),
          ("ofi_high", "Other family income: top tercile", "Other family income"),
          ("married", "Married", "Marital status"), ("unmarried", "Not married", "Marital status"),
          ("white", "White, non-Hispanic", "Race/ethnicity"), ("black", "Black", "Race/ethnicity"),
          ("hispanic", "Hispanic", "Race/ethnicity"), ("other", "Other race", "Race/ethnicity")]
SPECS = [("mothers_lt6", "worked", "Mothers of under-6s: worked last year"), ("mothers_lt6", "hours", "Mothers of under-6s: usual weekly hours"),
         ("all", "has_infant", "All women 18-44: birth last year")]
BASE = {("mothers_lt6", "worked"): "mothers_lt6_worked", ("mothers_lt6", "hours"): "mothers_lt6_hours", ("all", "has_infant"): "all_has_infant"}

d = pd.read_csv(CLEAN, usecols=["mother_lt6", "weight", "educ3", "ofi_tercile", "married", "race4", "worked", "hours", "has_infant", "gvar", "year"])
rows = []
for s, y, lab in SPECS:
    base = pd.read_csv(TAB / f"{BASE[(s, y)]}_simple.csv").iloc[0]
    rows.append({"spec": lab, "group": "All", "family": "All", "share": 1.0, "pre-mean (treated)": np.nan,
                 "simple ATT": base["simple ATT"], "se": base["se"], "pre e=-5..-1": np.nan})
    sub = d[d.mother_lt6 == 1] if s == "mothers_lt6" else d
    for g, glab, fam in GROUPS:
        p = TAB / f"het_{g}_{s}_{y}_simple.csv"
        if not p.exists():
            continue
        r = pd.read_csv(p).iloc[0]; ev = pd.read_csv(TAB / f"het_{g}_{s}_{y}_event.csv")
        q = {"educ_hs": "educ3=='hs_or_less'", "educ_some": "educ3=='some_college'", "educ_college": "educ3=='college'",
             "ofi_low": "ofi_tercile=='low'", "ofi_mid": "ofi_tercile=='mid'", "ofi_high": "ofi_tercile=='high'",
             "married": "married==1", "unmarried": "married==0", "white": "race4=='white'", "black": "race4=='black'",
             "hispanic": "race4=='hispanic'", "other": "race4=='other'"}[g]
        gg = sub.query(q); tr = gg[(gg.gvar > 0) & (gg.year == gg.gvar - 1)]
        rows.append({"spec": lab, "group": glab, "family": fam, "share": gg["weight"].sum() / sub["weight"].sum(),
                     "pre-mean (treated)": np.average(tr[y], weights=tr["weight"]) if len(tr) else np.nan,
                     "simple ATT": r["simple ATT"], "se": r["se"],
                     "pre e=-5..-1": ev[ev.e.between(-5, -1)]["estimate"].mean()})
H = pd.DataFrame(rows)
H["ATT (se)"] = [fmt(b, s) for b, s in zip(H["simple ATT"], H["se"])]
out = H[["spec", "group", "share", "pre-mean (treated)", "ATT (se)", "pre e=-5..-1"]]
out.to_csv(TAB / "het_summary.csv", index=False); (TAB / "het_summary.md").write_text(to_markdown(out, ".3f", index=False) + "\n")
print(to_markdown(out, ".3f", index=False))

for s, y, lab in SPECS:
    h = H[(H.spec == lab) & (H.group != "All")].copy()
    fams = list(dict.fromkeys(h["family"]))
    fig, ax = plt.subplots(figsize=(7.6, 5.6))
    yy = np.arange(len(h))[::-1]
    for i, fam in enumerate(fams):
        m = (h["family"] == fam).to_numpy()
        ax.errorbar(h.loc[m, "simple ATT"], yy[m], xerr=1.96 * h.loc[m, "se"], fmt="o", color=PALETTE[i % 4], elinewidth=2, capsize=0, markersize=6, label=fam)
    base = H[(H.spec == lab) & (H.group == "All")].iloc[0]
    ax.axvline(base["simple ATT"], color=INK2, linewidth=1, linestyle="--"); ax.axvline(0, color=INK2, linewidth=1)
    ax.set_yticks(yy); ax.set_yticklabels(h["group"]); ax.set_xlabel("Simple ATT, 95% CI (dashed: full-sample estimate)")
    ax.set_title(lab, fontsize=11, loc="left"); ax.legend(frameon=False, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=4)
    style_axes(ax); ax.xaxis.grid(True, color=GRID); ax.yaxis.grid(False)
    fig.tight_layout(); fig.savefig(FIG / f"het_{y}.png", dpi=200); plt.close(fig)
print("figures written")
