"""35_paper_tables.py -- LaTeX tables and descriptive figures for paper/minwage_teens.tex from the run outputs."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
sys.path.insert(0, str(Path(__file__).resolve().parent))
from aelib import PALETTE, INK2, GRID, style_axes
PF = Path(__file__).resolve().parents[1]; TAB = PF / "output" / "tables"; MW = PF / "data" / "raw" / "minwage"; P = PF / "paper"; (P / "tables").mkdir(parents=True, exist_ok=True); (P / "figures").mkdir(exist_ok=True)


def simple(tag):
    f = TAB / f"{tag}_simple.csv"
    if not f.exists(): return np.nan, np.nan, np.nan, np.nan
    s = pd.read_csv(f).iloc[0]; return s.post_avg, s.se, s.pre_avg, int(s.n_events)


def st(b, se):
    if np.isnan(se) or se == 0: return ""
    z = abs(b / se); return "$^{***}$" if z > 2.576 else "$^{**}$" if z > 1.96 else "$^{*}$" if z > 1.645 else ""


def cell(b, se, d=3):
    return f"{b:.{d}f}{st(b, se)}" if not np.isnan(b) else "", f"({se:.{d}f})" if not np.isnan(se) else ""


# ---- descriptive figure: teen employment, enrollment and status, 1994-2026 -------------------------------
d = pd.read_csv(PF / "data" / "clean" / "cps_monthly_1624.csv.gz", usecols=["year", "age", "weight", "enrolled", "employed", "inlf", "state_fips"])
t = d[d.age.between(16, 19)].copy(); t["enr_emp"] = t.enrolled * t.employed; t["enr_only"] = t.enrolled * (1 - t.employed); t["emp_only"] = (1 - t.enrolled) * t.employed; t["neither"] = (1 - t.enrolled) * (1 - t.employed)
wm = lambda g, y: np.average(g[y], weights=g.weight)
fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
for a, col in [((16, 17), PALETTE[0]), ((18, 19), PALETTE[1])]:
    s = t[t.age.between(*a)].groupby("year").apply(lambda g: pd.Series({"employed": wm(g, "employed"), "enrolled": wm(g, "enrolled")}))
    s = s[s.index <= 2025]
    axes[0].plot(s.index, s.employed, marker="o", ms=3, color=col, label=f"Employed, {a[0]}-{a[1]}"); axes[0].plot(s.index, s.enrolled, marker="s", ms=3, color=col, linestyle="--", label=f"Enrolled, {a[0]}-{a[1]}")
axes[0].set_title("Employment and school enrollment, ages 16-19", fontsize=10.5, loc="left"); axes[0].legend(frameon=False, fontsize=8.5, ncol=2, loc="center right"); axes[0].set_ylim(0, 1); style_axes(axes[0])
s = t.groupby("year").apply(lambda g: pd.Series({k: wm(g, k) for k in ["enr_emp", "enr_only", "emp_only", "neither"]})); s = s[s.index <= 2025]
for k, lab, col in [("enr_emp", "Enrolled and employed", PALETTE[0]), ("enr_only", "Enrolled only", PALETTE[1]), ("emp_only", "Employed only", PALETTE[2]), ("neither", "Neither", PALETTE[3])]:
    axes[1].plot(s.index, s[k], marker="o", ms=3, color=col, label=lab)
axes[1].set_title("School-work status, ages 16-19", fontsize=10.5, loc="left"); axes[1].legend(frameon=False, fontsize=8.5); style_axes(axes[1])
for ax in axes: ax.set_xlabel("Year")
fig.tight_layout(); fig.savefig(P / "figures" / "fig1_trends.png", dpi=200)

# ---- minimum wage panel figure: population-weighted mean effective minimum and share of teens above the federal floor ----
mw = pd.read_csv(MW / "state_mw_monthly.csv"); mw["year"] = mw.ym.str[:4].astype(int)
pop = t.groupby("state_fips").weight.sum(); mw["pop"] = mw.state_fips.map(pop).fillna(0)
ann = mw.groupby("year").apply(lambda g: pd.Series({"mean_mw": np.average(g.mw, weights=g["pop"]), "share_above": np.average((g.mw > g.mw_federal + 0.01).astype(float), weights=g["pop"])}))
ann = ann[(ann.index >= 1994) & (ann.index <= 2025)]
E = pd.read_csv(MW / "mw_events.csv"); E = E[E.federal_induced == 0]; E["year"] = E.event_ym.str[:4].astype(int)
fig, ax = plt.subplots(figsize=(7.5, 4)); ax2 = ax.twinx()
ax.plot(ann.index, ann.mean_mw, color=PALETTE[0], marker="o", ms=3, label="Population-weighted effective minimum ($)"); ax.set_ylabel("Dollars")
ax2.bar(E.groupby("year").size().index, E.groupby("year").size().values, color=PALETTE[1], alpha=0.5, label="Events (state increases of 5%+ after 3 quiet years)"); ax2.set_ylabel("Number of events")
ax.set_xlabel("Year"); ax.set_title("Minimum wages and the event calendar, 1994-2025", fontsize=10.5, loc="left"); style_axes(ax)
h1, l1 = ax.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels(); ax.legend(h1 + h2, l1 + l2, frameon=False, fontsize=8.5, loc="upper left")
fig.tight_layout(); fig.savefig(P / "figures" / "fig2_minwage.png", dpi=200)

# copy result figures
import shutil
for f, g in [("mw_wage_first_stage.png", "fig3_first_stage.png"), ("mw_event_main.png", "fig4_event_main.png"), ("mw_status_1819.png", "fig5_status_1819.png"), ("mw_byevent_1819.png", "fig6_byevent.png")]:
    shutil.copy(PF / "output" / "figures" / f, P / "figures" / g)

# ---- Table 1: events ------------------------------------------------------------------------------------
E2 = E[E.event_ym >= "2010-01"].sort_values("event_ym")
rows = [f"{r.state} & {r.event_ym} & {r.mw_before:.2f} & {r.mw_first:.2f} & {r.mw_end:.2f} & {100 * r.pct_window:.0f} & {r.n_steps} & {r.n_controls} \\\\" for r in E2.itertuples()]
(P / "tables" / "tab1_events.tex").write_text("\\begin{tabular}{llrrrrrr}\n\\toprule\nState & Event month & Before & First step & End of window & Rise (\\%) & Steps & Controls \\\\\n\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n")

# ---- Table 2: summary statistics, year before the event, treated states vs clean controls ---------------------
dd = pd.read_csv(PF / "data" / "clean" / "cps_monthly_1624.csv.gz", usecols=["ym", "age", "weight", "state_fips", "female", "black", "hispanic", "enrolled", "employed", "inlf", "hours", "org", "earnwt", "hourwage", "paidhour"])
dd = dd[dd.age.between(16, 19)]; dd["enr_emp"] = dd.enrolled * dd.employed; dd["enr_only"] = dd.enrolled * (1 - dd.employed); dd["emp_only"] = (1 - dd.enrolled) * dd.employed; dd["neither"] = (1 - dd.enrolled) * (1 - dd.employed)
E2["ym_idx"] = E2.event_ym.str[:4].astype(int) * 12 + E2.event_ym.str[5:7].astype(int) - 1
tr, ct = [], []
for r in E2.itertuples():
    pre = dd[dd.ym.between(r.ym_idx - 12, r.ym_idx - 1)]; tr.append(pre[pre.state_fips == r.state_fips]); ct.append(pre[pre.state_fips.isin([int(x) for x in str(r.controls).split()])])
tr = pd.concat(tr); ct = pd.concat(ct)
def stats(x, band):
    x = x[x.age.between(*band)]; w = x.weight; o = {}
    for k in ["enrolled", "employed", "inlf", "enr_emp", "enr_only", "emp_only", "neither", "hours", "female", "black", "hispanic"]:
        m = x[k].notna(); o[k] = np.average(x.loc[m, k], weights=w[m])
    h = x[(x.org == 1) & (x.paidhour == 1) & (x.hourwage > 0)]; o["hourwage"] = np.average(h.hourwage, weights=h.earnwt); o["n"] = len(x)
    return o
LABS = {"enrolled": "Enrolled in school", "employed": "Employed", "inlf": "In labour force", "enr_emp": "Enrolled and employed", "enr_only": "Enrolled only", "emp_only": "Employed only", "neither": "Neither", "hours": "Usual weekly hours (0 if not working)", "hourwage": "Hourly wage, hourly paid (\\$)", "female": "Female", "black": "Black", "hispanic": "Hispanic", "n": "Person-months"}
cols = [stats(tr, (16, 17)), stats(ct, (16, 17)), stats(tr, (18, 19)), stats(ct, (18, 19))]
rows = []
for k, lab in LABS.items():
    fmt = (lambda v: f"{v:,.0f}") if k == "n" else (lambda v: f"{v:.2f}") if k in ("hours", "hourwage") else (lambda v: f"{v:.3f}")
    rows.append(f"{lab} & " + " & ".join(fmt(c[k]) for c in cols) + " \\\\")
(P / "tables" / "tab2_summary.tex").write_text("\\begin{tabular}{lrrrr}\n\\toprule\n & \\multicolumn{2}{c}{Ages 16--17} & \\multicolumn{2}{c}{Ages 18--19} \\\\\n\\cmidrule(lr){2-3}\\cmidrule(lr){4-5}\n & Event states & Controls & Event states & Controls \\\\\n\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n")

# ---- Table 3: main results ---------------------------------------------------------------------------------
OUT = [("log_wage", "Log hourly wage, hourly paid (ORG)"), ("log_earnweek", "Log weekly earnings (ORG)"), ("enrolled", "Enrolled in school"), ("enr_hs", "Enrolled in high school"), ("enr_ft", "Enrolled full time"),
       ("employed", "Employed"), ("inlf", "In labour force"), ("hours", "Usual weekly hours"), ("enr_emp", "Enrolled and employed"), ("enr_only", "Enrolled only"), ("emp_only", "Employed only"), ("neither", "Neither enrolled nor employed")]
rows = []
for y, lab in OUT:
    line1, line2 = [lab], [""]
    for ages in ("1617", "1819", "1619"):
        b, se, pre, n = simple(f"mw_{ages}_{y}_post2009"); dgt = 2 if y == "hours" else 3
        c1, c2 = cell(b, se, dgt); line1 += [c1, f"{pre:.{dgt}f}" if not np.isnan(pre) else ""]; line2 += [c2, ""]
    rows.append(" & ".join(line1) + " \\\\"); rows.append(" & ".join(line2) + " \\\\")
(P / "tables" / "tab3_main.tex").write_text("\\begin{tabular}{lcccccc}\n\\toprule\n & \\multicolumn{2}{c}{Ages 16--17} & \\multicolumn{2}{c}{Ages 18--19} & \\multicolumn{2}{c}{Ages 16--19} \\\\\n\\cmidrule(lr){2-3}\\cmidrule(lr){4-5}\\cmidrule(lr){6-7}\n & Post & Pre & Post & Pre & Post & Pre \\\\\n\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n")

# ---- Table 4: event-time coefficients for wage, enrolled, employed ----------------------------------------
rows = []
for k in (-3, -2, -1, 0, 1, 2, 3):
    line1, line2 = [f"Year {k}"], [""]
    for y in ("log_wage", "enrolled", "employed"):
        for ages in ("1617", "1819"):
            E_ = pd.read_csv(TAB / f"mw_{ages}_{y}_post2009_event.csv").set_index("k")
            if k == -1: line1.append("0"); line2.append("")
            else:
                c1, c2 = cell(E_.loc[k, "estimate"], E_.loc[k, "se"]); line1.append(c1); line2.append(c2)
    rows.append(" & ".join(line1) + " \\\\"); rows.append(" & ".join(line2) + " \\\\")
(P / "tables" / "tab4_eventtime.tex").write_text("\\begin{tabular}{lcccccc}\n\\toprule\n & \\multicolumn{2}{c}{Log hourly wage} & \\multicolumn{2}{c}{Enrolled} & \\multicolumn{2}{c}{Employed} \\\\\n\\cmidrule(lr){2-3}\\cmidrule(lr){4-5}\\cmidrule(lr){6-7}\n & 16--17 & 18--19 & 16--17 & 18--19 & 16--17 & 18--19 \\\\\n\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n")

# ---- Table 5: robustness ------------------------------------------------------------------------------------
VAR = [("post2009", "Main: 39 events from 2010, clean controls, population weights"), ("all", "All 71 events, 1994--2025"), ("pre2010", "32 events before 2010"), ("large", "Large events only (window rise $\\geq$ 20\\%)"),
       ("post2009_strict", "Strict controls (no rise of any kind)"), ("post2009_federal", "Federal-floor controls only"), ("post2009_eq", "Equal weight per event"), ("post2009_nopandemic", "Drop 2020--21"), ("post2009_schoolmonths", "September--May only"),
       ("post2009_cleanlocal", "Controls net of counties with local minimums"), ("post2009_cleanlocal_nolocal", "Treated: identified counties without a local minimum"), ("local_cleanlocal", "County-level local events (16 counties)")]
rows = []
for v, lab in VAR:
    line1, line2 = [lab], [""]
    for y in ("enrolled", "employed", "neither"):
        for ages in ("1617", "1819"):
            b, se, pre, n = simple(f"mw_{ages}_{y}_{v}"); c1, c2 = cell(b, se); line1.append(c1); line2.append(c2)
    b, se, pre, n = simple(f"mw_1617_enrolled_{v}"); line1.append(str(n) if not np.isnan(n) else ""); line2.append("")
    rows.append(" & ".join(line1) + " \\\\"); rows.append(" & ".join(line2) + " \\\\")
(P / "tables" / "tab5_robust.tex").write_text("\\begin{tabular}{lcccccccc}\n\\toprule\n & \\multicolumn{2}{c}{Enrolled} & \\multicolumn{2}{c}{Employed} & \\multicolumn{2}{c}{Neither} & Events \\\\\n\\cmidrule(lr){2-3}\\cmidrule(lr){4-5}\\cmidrule(lr){6-7}\n & 16--17 & 18--19 & 16--17 & 18--19 & 16--17 & 18--19 & \\\\\n\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n")

# ---- Table 6: heterogeneity ----------------------------------------------------------------------------------
HET = [("female", "Girls"), ("male", "Boys"), ("black", "Black"), ("hispanic", "Hispanic"), ("whiteother", "White and other"), ("faminc_lt50k", "Family income below \\$50,000"), ("faminc_ge50k", "Family income \\$50,000 or more")]
rows = []
for k, lab in HET:
    line1, line2 = [lab], [""]
    for ages in ("1617", "1819"):
        b, se, pre, n = simple(f"mw_{ages}_enrolled_post2009_{k}"); c1, c2 = cell(b, se); line1 += [c1, f"{pre:.3f}"]; line2 += [c2, ""]
    rows.append(" & ".join(line1) + " \\\\"); rows.append(" & ".join(line2) + " \\\\")
(P / "tables" / "tab6_het.tex").write_text("\\begin{tabular}{lcccc}\n\\toprule\n & \\multicolumn{2}{c}{Ages 16--17} & \\multicolumn{2}{c}{Ages 18--19} \\\\\n\\cmidrule(lr){2-3}\\cmidrule(lr){4-5}\n & Post & Pre & Post & Pre \\\\\n\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n")
print("tables and figures written to paper/")
print({k: round(v, 3) for k, v in cols[0].items()}); print({k: round(v, 3) for k, v in cols[2].items()})
