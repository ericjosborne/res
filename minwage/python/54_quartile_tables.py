"""54_quartile_tables.py -- tables and figures for the family-income quartile split (53_run_quartiles.py; 51_stacked_controls.py --groups=q1,q2,q3,q4).
Writes paper/tables/tabQ_post_{ages}.tex (event-study post averages, pre averages in the note), paper/figures/figQ_groups.png and figQ_wage.png,
and output/tables/quartiles_summary.md (both estimators side by side)."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
sys.path.insert(0, str(Path(__file__).resolve().parent))
from aelib import PALETTE, INK2, GRID, style_axes
PF = Path(__file__).resolve().parents[1]; TAB = PF / "output" / "tables"; PT = PF / "paper" / "tables"; PFG = PF / "paper" / "figures"
D = "unit"; AGES = [("1617", "16--17"), ("1819", "18--19"), ("1619", "16--19")]
Q = [("q1", "Bottom quarter"), ("q2", "Second quarter"), ("q3", "Third quarter"), ("q4", "Top quarter")]
OUTS = [("enr_emp", "Enrolled and employed"), ("enr_only", "Enrolled only"), ("emp_only", "Employed only"), ("neither", "Neither enrolled nor employed"),
        ("enrolled", "Enrolled"), ("employed", "Employed"), ("log_wage", "Log hourly wage, hourly paid")]
def simple(tag):
    f = TAB / f"{tag}_simple.csv"
    if not f.exists(): return np.nan, np.nan, np.nan, np.nan, np.nan
    s = pd.read_csv(f).iloc[0]; return s.post_avg, s.se, s.pre_avg, int(s.n_events), int(s.n_obs)
def st(b, se):
    if np.isnan(se) or se == 0: return ""
    z = abs(b / se); return "$^{***}$" if z > 2.576 else "$^{**}$" if z > 1.96 else "$^{*}$" if z > 1.645 else ""
md = ["# Family income quartiles (within-year weighted quartiles of the CPS family income category among 16-19 year olds)\n"]
R = pd.read_csv(TAB / "mw_stacked_controls.csv", dtype={"ages": str}) if (TAB / "mw_stacked_controls.csv").exists() else pd.DataFrame(columns=["group"])
for a, al in AGES:
    L = []; md.append(f"\n## Ages {al.replace('--', '-')}\n\n| Outcome | Q1 post (s.e.) | Q1 pre | Q2 post (s.e.) | Q2 pre | Q3 post (s.e.) | Q3 pre | Q4 post (s.e.) | Q4 pre | Q1 stacked+controls | Q2 | Q3 | Q4 |\n|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for y, lab in OUTS:
        l1, l2, m = [lab], [""], [lab]; m2 = []
        for q, _ in Q:
            b, se, pre, n, nobs = simple(f"mw_{a}_{y}_{D}_{q}"); l1.append(f"{b:.3f}{st(b, se)}" if not np.isnan(b) else ""); l2.append(f"({se:.3f})" if not np.isnan(se) else "")
            m.append(f"{b:+.4f} ({se:.4f})" if not np.isnan(b) else ""); m.append(f"{pre:+.4f}" if not np.isnan(pre) else "")
            r = R[(R.group == q) & (R.ages == a) & (R.outcome == y)]
            m2.append(f"{r.iloc[0].stacked_ctrl:+.4f} ({r.iloc[0].stacked_ctrl_se:.4f})" if len(r) else "")
        L += [" & ".join(l1) + " \\\\", " & ".join(l2) + " \\\\"]; md.append("| " + " | ".join(m + m2) + " |")
    (PT / f"tabQ_post_{a}.tex").write_text("\\begin{tabular}{lcccc}\n\\toprule\n & Bottom quarter & Second quarter & Third quarter & Top quarter \\\\\n\\midrule\n" + "\n".join(L) + "\n\\bottomrule\n\\end{tabular}\n")
    ns = [simple(f"mw_{a}_enrolled_{D}_{q}")[4] for q, _ in Q]; md.append(f"\nTeen-months on the treated side (enrolled runs): " + ", ".join(f"Q{i+1} {n:,}" for i, n in enumerate(ns) if not np.isnan(n)))
(TAB / "quartiles_summary.md").write_text("\n".join(md) + "\n"); print("wrote quartiles_summary.md")
OFF = [-0.24, -0.08, 0.08, 0.24]
def fig_grid(outs, a, fname, ncols, title, ylabel):
    n = len(outs); nrows = int(np.ceil(n / ncols)); fig, axes = plt.subplots(nrows, ncols, figsize=(5.2 * ncols, 4.0 * nrows), squeeze=False)
    for k, (y, lab) in enumerate(outs):
        ax = axes.flat[k]
        for (q, ql), col, off in zip(Q, PALETTE[:4], OFF):
            f = TAB / f"mw_{a}_{y}_{D}_{q}_event.csv"
            if not f.exists(): continue
            E = pd.read_csv(f); ax.errorbar(E.k + off, E.estimate, yerr=1.96 * E.se, fmt="o", color=col, elinewidth=1.6, markersize=4.5, label=ql)
        ax.axhline(0, color=INK2, linewidth=1); ax.axvline(-0.5, color=GRID, linewidth=1); ax.set_title(lab, fontsize=10.5, loc="left"); style_axes(ax)
        if k // ncols == nrows - 1: ax.set_xlabel("Years relative to the increase (base: year -1)")
        if k % ncols == 0: ax.set_ylabel(ylabel)
    for k in range(n, nrows * ncols): axes.flat[k].axis("off")
    axes.flat[0].legend(frameon=False, fontsize=9, loc="upper left", ncol=2)
    fig.suptitle(title, fontsize=10.5, x=0.01, ha="left"); fig.tight_layout(); fig.savefig(PFG / fname, dpi=200); plt.close(fig)
fig_grid(OUTS[:4], "1619", "figQ_groups.png", 2, "School-work status by family income quartile (within-year), ages 16-19, 95% intervals", "Effect (share)")
fig_grid(OUTS[:4], "1617", "figQ_groups_1617.png", 2, "School-work status by family income quartile (within-year), ages 16-17, 95% intervals", "Effect (share)")
fig, axes = plt.subplots(1, 3, figsize=(15, 4.2), sharey=True)
for ax, (a, lab) in zip(axes, AGES):
    for (q, ql), col, off in zip(Q, PALETTE[:4], OFF):
        f = TAB / f"mw_{a}_log_wage_{D}_{q}_event.csv"
        if not f.exists(): continue
        E = pd.read_csv(f); ax.errorbar(E.k + off, E.estimate, yerr=1.96 * E.se, fmt="o", color=col, elinewidth=1.6, markersize=4.5, label=ql)
    ax.axhline(0, color=INK2, linewidth=1); ax.axvline(-0.5, color=GRID, linewidth=1); ax.set_title(f"Ages {lab.replace('--', '-')}" + (" (pooled)" if a == "1619" else ""), fontsize=10.5, loc="left"); ax.set_xlabel("Years relative to the increase (base: year -1)"); style_axes(ax)
axes[0].set_ylabel("Effect on log hourly wage"); axes[0].legend(frameon=False, fontsize=9, loc="upper left", ncol=2)
fig.suptitle("Teen wages by family income quartile (within-year), 95% intervals", fontsize=10.5, x=0.01, ha="left"); fig.tight_layout(); fig.savefig(PFG / "figQ_wage.png", dpi=200); plt.close(fig)
print("wrote figures")
