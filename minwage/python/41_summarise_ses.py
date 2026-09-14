"""41_summarise_ses.py -- tables and figures for the socioeconomic heterogeneity runs (40_run_ses.py)."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
sys.path.insert(0, str(Path(__file__).resolve().parent))
from aelib import PALETTE, INK2, GRID, style_axes, to_markdown
PF = Path(__file__).resolve().parents[1]; TAB = PF / "output" / "tables"; FIG = PF / "output" / "figures"; P = PF / "paper"
SUF = sys.argv[1] if len(sys.argv) > 1 else ""          # "" nominal split; "rel" within-year median split
LAB = {"log_wage": "Log hourly wage, hourly-paid teens", "enrolled": "Enrolled in school", "employed": "Employed", "enr_emp": "Enrolled and employed",
       "enr_only": "Enrolled only", "emp_only": "Employed only", "neither": "Neither enrolled nor employed", "hours": "Usual weekly hours"}
GRP = [("lowses" + SUF, "Low"), ("highses" + SUF, "High")]


def simple(tag):
    f = TAB / f"{tag}_simple.csv"
    if not f.exists(): return np.nan, np.nan, np.nan, np.nan
    s = pd.read_csv(f).iloc[0]; return s.post_avg, s.se, s.pre_avg, int(s.n_obs)


def st(b, se):
    if np.isnan(se) or se == 0: return ""
    z = abs(b / se); return "***" if z > 2.576 else "**" if z > 1.96 else "*" if z > 1.645 else ""


rows, tex = [], []
for y, lab in LAB.items():
    r = {"outcome": lab}; l1, l2 = [lab], [""]
    for ages in ("1617", "1819", "1619"):
        for g, gl in GRP:
            b, se, pre, n = simple(f"mw_{ages}_{y}_unit_{g}"); dg = 2 if y == "hours" else 3
            r[f"{ages[:2]}-{ages[2:]} {gl}"] = b; r[f"{ages[:2]}-{ages[2:]} {gl} se"] = se; r[f"{ages[:2]}-{ages[2:]} {gl} sig"] = st(b, se); r[f"{ages[:2]}-{ages[2:]} {gl} pre"] = pre
            l1.append(f"{b:.{dg}f}" + {"": "", "*": "$^{*}$", "**": "$^{**}$", "***": "$^{***}$"}[st(b, se)] if not np.isnan(b) else ""); l2.append(f"({se:.{dg}f})" if not np.isnan(se) else "")
        # difference low - high and its bootstrap-free approximate s.e. (independent samples)
        bl, sl, _, _ = simple(f"mw_{ages}_{y}_unit_{GRP[0][0]}"); bh, sh, _, _ = simple(f"mw_{ages}_{y}_unit_{GRP[1][0]}")
        r[f"{ages[:2]}-{ages[2:]} diff"] = bl - bh; r[f"{ages[:2]}-{ages[2:]} diff se"] = np.sqrt(sl ** 2 + sh ** 2)
    rows.append(r); tex.append(" & ".join(l1) + " \\\\"); tex.append(" & ".join(l2) + " \\\\")
T = pd.DataFrame(rows)
with open(TAB / f"mw_ses_summary{SUF}.md", "w") as f:
    f.write(f"## Heterogeneity by family income ({'within-year median split' if SUF else 'below vs at or above $50,000, nominal'}), unit design, 2010+ events: post-event averages\n\n" + to_markdown(T, ".4f", index=False))
print(open(TAB / f"mw_ses_summary{SUF}.md").read())
(P / "tables" / f"tab7_ses{SUF}.tex").write_text("\\begin{tabular}{lcccccc}\n\\toprule\n & \\multicolumn{2}{c}{Ages 16--17} & \\multicolumn{2}{c}{Ages 18--19} & \\multicolumn{2}{c}{Ages 16--19} \\\\\n\\cmidrule(lr){2-3}\\cmidrule(lr){4-5}\\cmidrule(lr){6-7}\n & Low & High & Low & High & Low & High \\\\\n\\midrule\n" + "\n".join(tex) + "\n\\bottomrule\n\\end{tabular}\n")

# figure: event studies, low vs high, pooled ages 16-19, six outcomes
OUT6 = ["log_wage", "enrolled", "employed", "enr_emp", "enr_only", "neither"]
for ages, name in [("1619", ""), ("1617", "_1617"), ("1819", "_1819")]:
    fig, axes = plt.subplots(2, 3, figsize=(15, 8.4))
    for ax, y in zip(axes.flat, OUT6):
        for (g, gl), col, off in zip(GRP, [PALETTE[0], PALETTE[1]], [-0.1, 0.1]):
            f = TAB / f"mw_{ages}_{y}_unit_{g}_event.csv"
            if not f.exists(): continue
            E = pd.read_csv(f); ax.errorbar(E.k + off, E.estimate, yerr=1.96 * E.se, fmt="o", color=col, elinewidth=1.8, markersize=5, label=f"{gl} family income")
        ax.axhline(0, color=INK2, linewidth=1); ax.axvline(-0.5, color=GRID, linewidth=1); ax.set_title(LAB[y], fontsize=10.5, loc="left"); style_axes(ax)
    for ax in axes[1]: ax.set_xlabel("Years relative to the increase (base: year -1)")
    axes[0, 0].legend(frameon=False, fontsize=9, loc="upper left")
    fig.suptitle(f"By family income ({'within-year median split' if SUF else 'below vs at or above $50,000'}), ages {ages[:2]}-{ages[2:]}, unit design, 2010+ events, 95% intervals", fontsize=11, x=0.01, ha="left")
    fig.tight_layout(); fig.savefig(FIG / f"mw_ses_grid{SUF}{name}.png", dpi=200)
    if ages == "1619": fig.savefig(P / "figures" / f"fig7_ses{SUF}.png", dpi=200)
print("wrote figures")
