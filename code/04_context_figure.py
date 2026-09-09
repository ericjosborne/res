"""
04_context_figure.py -- motivation figure from Our World in Data (GitHub mirror
owid/owid-datasets): long-run US female labour force participation (Olivetti
2013) and OECD-based series for a fixed set of comparison countries.
Output: output/figures/F1_flfp_long_run.png
"""
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from aelib import PALETTE, INK, INK2, GRID, style_axes

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "owid"
FIG = ROOT / "output" / "figures"; FIG.mkdir(parents=True, exist_ok=True)

us = pd.read_csv(RAW / "us_flfp_olivetti_2013.csv"); us.columns = ["entity", "year", "flfp"]
oecd = pd.read_csv(RAW / "flfp_owid_2017.csv"); oecd.columns = ["entity", "year", "flfp"]
countries = ["United States", "Canada", "Germany", "Japan"]  # fixed order -> fixed palette slots

fig, axes = plt.subplots(1, 2, figsize=(10, 4), gridspec_kw={"width_ratios": [1, 1.25]})
ax = axes[0]
ax.plot(us["year"], us["flfp"], color=PALETTE[0], linewidth=2, marker="o", markersize=4)
ax.set_title("United States, 1890-2005 (Olivetti 2013)", fontsize=10, loc="left")
ax.set_ylabel("Female labour force participation (%)"); ax.set_xlim(1885, 2010); ax.set_ylim(0, 70)
ax.annotate("1980 Census\n(our micro sample)", xy=(1980, us.loc[us.year == 1980, "flfp"].iloc[0]),
            xytext=(1935, 55), fontsize=8.5, color=INK2, arrowprops=dict(arrowstyle="-", color=INK2, lw=0.8))
style_axes(ax)
ax = axes[1]
for i, c in enumerate(countries):
    s = oecd[(oecd.entity == c) & (oecd.year >= 1960)].sort_values("year")
    ax.plot(s["year"], s["flfp"], color=PALETTE[i], linewidth=2, label=c)
ax.set_title("Four countries, women 15+, 1960-2016 (OECD via OWID)", fontsize=10, loc="left")
ax.set_xlim(1960, 2018); ax.set_ylim(0, 70); ax.legend(frameon=False, fontsize=8.5, loc="lower right")
style_axes(ax)
fig.suptitle("Female labour force participation rose for a century, then flattened after 2000",
             x=0.01, ha="left", fontsize=11.5, color=INK)
fig.tight_layout(); fig.savefig(FIG / "F1_flfp_long_run.png", dpi=200)
print("wrote", FIG / "F1_flfp_long_run.png")
