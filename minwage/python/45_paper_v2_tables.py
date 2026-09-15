"""45_paper_v2_tables.py -- tables and figures for the restructured paper (results ordered: four school-work groupings,
then by SES; log wages, then by SES; robustness and sex/race heterogeneity in the appendix).  Unit design throughout."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
sys.path.insert(0, str(Path(__file__).resolve().parent))
from aelib import PALETTE, INK2, GRID, style_axes
PF = Path(__file__).resolve().parents[1]; TAB = PF / "output" / "tables"; MW = PF / "data" / "raw" / "minwage"; P = PF / "paper"; PT = P / "tables"; PFG = P / "figures"
D = "unit"; AGES = [("1617", "16--17"), ("1819", "18--19"), ("1619", "16--19")]
GROUPS = [("enr_emp", "Enrolled and employed"), ("enr_only", "Enrolled only"), ("emp_only", "Employed only"), ("neither", "Neither enrolled nor employed")]
MEMO = [("enrolled", "Enrolled (first two rows)"), ("employed", "Employed (first and third rows)")]
WAGE = [("log_wage", "Log hourly wage, hourly-paid teens"), ("log_earnweek", "Log weekly earnings, all teen workers")]
SES = [("lowses", "Low"), ("highses", "High")]; SESREL = [("lowsesrel", "Low"), ("highsesrel", "High")]


def simple(tag):
    f = TAB / f"{tag}_simple.csv"
    if not f.exists(): return np.nan, np.nan, np.nan, np.nan
    s = pd.read_csv(f).iloc[0]; return s.post_avg, s.se, s.pre_avg, int(s.n_events)


def st(b, se):
    if np.isnan(se) or se == 0: return ""
    z = abs(b / se); return "$^{***}$" if z > 2.576 else "$^{**}$" if z > 1.96 else "$^{*}$" if z > 1.645 else ""


def c1(b, se, d=3): return (f"{b:.{d}f}{st(b, se)}" if not np.isnan(b) else "", f"({se:.{d}f})" if not np.isnan(se) else "")


def table_main(outs, fname, digits=3, group=""):
    rows = []
    for y, lab in outs:
        l1, l2 = [lab], [""]
        for a, _ in AGES:
            b, se, pre, n = simple(f"mw_{a}_{y}_{D}{group}"); x, y_ = c1(b, se, digits); l1 += [x, f"{pre:.{digits}f}" if not np.isnan(pre) else ""]; l2 += [y_, ""]
        rows += [" & ".join(l1) + " \\\\", " & ".join(l2) + " \\\\"]
    (PT / fname).write_text("\\begin{tabular}{lcccccc}\n\\toprule\n & \\multicolumn{2}{c}{Ages 16--17} & \\multicolumn{2}{c}{Ages 18--19} & \\multicolumn{2}{c}{Ages 16--19} \\\\\n\\cmidrule(lr){2-3}\\cmidrule(lr){4-5}\\cmidrule(lr){6-7}\n & Post & Pre & Post & Pre & Post & Pre \\\\\n\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n")


def table_ses(outs, groups, fname, digits=3):
    rows = []
    for y, lab in outs:
        l1, l2 = [lab], [""]
        for a, _ in AGES:
            for g, _ in groups:
                b, se, pre, n = simple(f"mw_{a}_{y}_{D}_{g}"); x, y_ = c1(b, se, digits); l1.append(x); l2.append(y_)
        rows += [" & ".join(l1) + " \\\\", " & ".join(l2) + " \\\\"]
    (PT / fname).write_text("\\begin{tabular}{lcccccc}\n\\toprule\n & \\multicolumn{2}{c}{Ages 16--17} & \\multicolumn{2}{c}{Ages 18--19} & \\multicolumn{2}{c}{Ages 16--19} \\\\\n\\cmidrule(lr){2-3}\\cmidrule(lr){4-5}\\cmidrule(lr){6-7}\n & Low & High & Low & High & Low & High \\\\\n\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n")


def fig_grid(outs, series, fname, ncols, title, ylabel):
    n = len(outs); nrows = int(np.ceil(n / ncols)); fig, axes = plt.subplots(nrows, ncols, figsize=(5.2 * ncols, 4.0 * nrows), squeeze=False)
    for k, (y, lab) in enumerate(outs):
        ax = axes.flat[k]
        for tag_fn, slab, col, off in series:
            f = TAB / f"{tag_fn(y)}_event.csv"
            if not f.exists(): continue
            E = pd.read_csv(f); ax.errorbar(E.k + off, E.estimate, yerr=1.96 * E.se, fmt="o", color=col, elinewidth=1.8, markersize=5, label=slab)
        ax.axhline(0, color=INK2, linewidth=1); ax.axvline(-0.5, color=GRID, linewidth=1); ax.set_title(lab, fontsize=10.5, loc="left"); style_axes(ax)
        if k // ncols == nrows - 1: ax.set_xlabel("Years relative to the increase (base: year -1)")
        if k % ncols == 0: ax.set_ylabel(ylabel)
    for k in range(n, nrows * ncols): axes.flat[k].axis("off")
    axes.flat[0].legend(frameon=False, fontsize=9, loc="upper left")
    fig.suptitle(title, fontsize=10.5, x=0.01, ha="left"); fig.tight_layout(); fig.savefig(PFG / fname, dpi=200); plt.close(fig)


AGE_SERIES = [(lambda y, a=a: f"mw_{a}_{y}_{D}", f"Ages {lab.replace('--', '-')}" + (" (pooled)" if a == "1619" else ""), col, off) for (a, lab), col, off in zip(AGES, PALETTE[:3], [-0.15, 0, 0.15])]
def ses_series(a, groups): return [(lambda y, a=a, g=g: f"mw_{a}_{y}_{D}_{g}", f"{gl} family income", col, off) for (g, gl), col, off in zip(groups, PALETTE[:2], [-0.1, 0.1])]

# results, part 1: the four school-work groupings
table_main(GROUPS + MEMO, "tabR1_groups.tex")
fig_grid(GROUPS, AGE_SERIES, "figR1_groups.png", 2, "School-work status, 73 events from 2010: event-time effects by age, 95% intervals", "Effect (share)")
table_ses(GROUPS + MEMO, SES, "tabR2_groups_ses.tex"); table_ses(GROUPS + MEMO, SESREL, "tabA_groups_sesrel.tex")
table_main(GROUPS + MEMO, "tabR2_groups_low.tex", group="_lowses"); table_main(GROUPS + MEMO, "tabR2_groups_high.tex", group="_highses")  # separate low / high tables, layout of tabR1
fig_grid(GROUPS, ses_series("1619", SES), "figR2_groups_ses.png", 2, "School-work status by family income (below vs at or above $50,000), ages 16-19, 95% intervals", "Effect (share)")
fig_grid(GROUPS, ses_series("1619", SESREL), "figA_groups_sesrel.png", 2, "School-work status by family income (within-year median split), ages 16-19, 95% intervals", "Effect (share)")
# results, part 2: log wages
table_main(WAGE, "tabR3_wage.tex")
fig_grid([("log_wage", "Log hourly wage, hourly-paid teens (ORG)")], AGE_SERIES, "figR3_wage.png", 1, "First stage: teen wages, 73 events from 2010, 95% intervals", "Effect (log points)")
table_ses(WAGE, SES, "tabR4_wage_ses.tex"); table_ses(WAGE, SESREL, "tabA_wage_sesrel.tex")
fig_grid([(f"log_wage", f"Ages {lab.replace('--', '-')}") for a, lab in AGES], [], "tmp.png", 3, "", "")  # placeholder removed below
fig, axes = plt.subplots(1, 3, figsize=(15, 4.2), sharey=True)
for ax, (a, lab) in zip(axes, AGES):
    for (g, gl), col, off in zip(SES, PALETTE[:2], [-0.1, 0.1]):
        f = TAB / f"mw_{a}_log_wage_{D}_{g}_event.csv"
        if not f.exists(): continue
        E = pd.read_csv(f); ax.errorbar(E.k + off, E.estimate, yerr=1.96 * E.se, fmt="o", color=col, elinewidth=1.8, markersize=5, label=f"{gl} family income")
    ax.axhline(0, color=INK2, linewidth=1); ax.axvline(-0.5, color=GRID, linewidth=1); ax.set_title(f"Ages {lab.replace('--', '-')}" + (" (pooled)" if a == "1619" else ""), fontsize=10.5, loc="left"); ax.set_xlabel("Years relative to the increase (base: year -1)"); style_axes(ax)
axes[0].set_ylabel("Effect on log hourly wage"); axes[0].legend(frameon=False, fontsize=9, loc="upper left")
fig.suptitle("Teen wages by family income (below vs at or above $50,000), 95% intervals", fontsize=10.5, x=0.01, ha="left"); fig.tight_layout(); fig.savefig(PFG / "figR4_wage_ses.png", dpi=200); plt.close(fig)
(PFG / "tmp.png").unlink(missing_ok=True)

# appendix: dropout (Smith's outcome), school months, by SES
rows = []
for a, lab in [("1617", "16--17"), ("1819", "18--19"), ("1618", "16--18"), ("1619", "16--19")]:
    l1, l2 = [f"Ages {lab}"], [""]
    for tag in (f"mw_{a}_dropout_unit_school", f"mw_{a}_dropout_unit_school_lowses", f"mw_{a}_dropout_unit_school_highses", f"mw_{a}_dropout_unit_school_lowsesrel", f"mw_{a}_dropout_unit_school_highsesrel", f"mw_{a}_dropout_unit"):
        b, se, pre, n = simple(tag); x, y_ = c1(b, se); l1.append(x); l2.append(y_)
    rows += [" & ".join(l1) + " \\\\", " & ".join(l2) + " \\\\"]
(PT / "tabA_dropout.tex").write_text("\\begin{tabular}{lcccccc}\n\\toprule\n & All & \\multicolumn{2}{c}{Below / at or above \\$50,000} & \\multicolumn{2}{c}{Below / at or above median} & All months \\\\\n\\cmidrule(lr){3-4}\\cmidrule(lr){5-6}\n & Sept--May & Low & High & Low & High & \\\\\n\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n")
print("v2 tables and figures written")
