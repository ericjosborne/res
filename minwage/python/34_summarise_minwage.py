"""34_summarise_minwage.py -- collect the minimum wage runs (33_run_minwage.py) into summary tables and figures.
Main specification: the unit design (tags mw_<ages>_<outcome>_unit...); the state design (post2009) is reported as a robustness row."""
D = "unit"
import sys
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
sys.path.insert(0, str(Path(__file__).resolve().parent))
from aelib import PALETTE, INK2, GRID, style_axes, to_markdown
PF = Path(__file__).resolve().parents[1]; TAB = PF / "output" / "tables"; FIG = PF / "output" / "figures"
LAB = {"enrolled": "Enrolled in school", "enr_hs": "Enrolled in high school", "enr_ft": "Enrolled full time", "employed": "Employed", "atwork": "At work last week",
       "inlf": "In labor force", "hours": "Usual hours (0 if not working)", "enr_emp": "Enrolled and employed", "enr_only": "Enrolled only", "emp_only": "Employed only",
       "neither": "Neither enrolled nor employed", "log_wage": "Log hourly wage (hourly paid, ORG)", "log_earnweek": "Log weekly earnings (ORG)"}


def simple(tag):
    f = TAB / f"{tag}_simple.csv"
    if not f.exists(): return dict(post=np.nan, se=np.nan, pre=np.nan, se_pre=np.nan, n_events=np.nan)
    s = pd.read_csv(f).iloc[0]; return dict(post=s.post_avg, se=s.se, pre=s.pre_avg, se_pre=s.se_pre, n_events=int(s.n_events))


def stars(b, se):
    if np.isnan(se) or se == 0: return ""
    z = abs(b / se); return "***" if z > 2.576 else "**" if z > 1.96 else "*" if z > 1.645 else ""


rows = []
for y in LAB:
    r = {"outcome": LAB[y]}
    for ages in ("1617", "1819", "1619"):
        s = simple(f"mw_{ages}_{y}_{D}"); r[f"{ages[:2]}-{ages[2:]} post"] = s["post"]; r[f"{ages[:2]}-{ages[2:]} s.e."] = s["se"]; r[f"{ages[:2]}-{ages[2:]} sig"] = stars(s["post"], s["se"]); r[f"{ages[:2]}-{ages[2:]} pre"] = s["pre"]
    rows.append(r)
T1 = pd.DataFrame(rows)
rows = []
for y in ("enrolled", "employed", "neither"):
    for ages in ("1617", "1819"):
        for var, lab in [(D, "Main: unit design, 73 events from 2010, clean controls, population weights"), ("post2009", "State design (states as units), 39 events"),
                         (D + "_state", "Unit design: state-remainder events only"), (D + "_both", "Unit design: county events, state and local rise"), (D + "_local", "Unit design: county events, local rise only"),
                         (D + "_all", "All events 1994+"), (D + "_pre2010", "Events before 2010"), (D + "_large", "Large events only (window rise >= 20%)"),
                         (D + "_strict", "Strict controls"), (D + "_federal", "Federal-floor controls only"), (D + "_eq", "Equal weight per event"), (D + "_nopandemic", "Drop 2020-21"), (D + "_schoolmonths", "September-May only")]:
            s = simple(f"mw_{ages}_{y}_{var}"); rows.append({"outcome": LAB[y], "ages": f"{ages[:2]}-{ages[2:]}", "specification": lab, "post avg": s["post"], "s.e.": s["se"], "sig": stars(s["post"], s["se"]), "pre avg": s["pre"], "events": s["n_events"]})
T2 = pd.DataFrame(rows)
rows = []
for k, lab in [("female", "Girls"), ("male", "Boys"), ("black", "Black"), ("hispanic", "Hispanic"), ("whiteother", "White and other"), ("faminc_lt50k", "Family income < $50k"), ("faminc_ge50k", "Family income >= $50k")]:
    for ages in ("1617", "1819"):
        s = simple(f"mw_{ages}_enrolled_{D}_{k}"); rows.append({"subgroup": lab, "ages": f"{ages[:2]}-{ages[2:]}", "post avg": s["post"], "s.e.": s["se"], "sig": stars(s["post"], s["se"]), "pre avg": s["pre"]})
T3 = pd.DataFrame(rows)
with open(TAB / "mw_summary.md", "w") as f:
    f.write("## Post-event average effect (years 0-3) by outcome and age, unit design, 2010+ events\n\n" + to_markdown(T1, ".4f", index=False))
    f.write("\n\n## Robustness\n\n" + to_markdown(T2, ".4f", index=False)); f.write("\n\n## Heterogeneity, enrolled\n\n" + to_markdown(T3, ".4f", index=False))
print(open(TAB / "mw_summary.md").read())

# figure: event studies, enrolled and employed, by age band
fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
for ax, y in zip(axes, ["enrolled", "employed"]):
    for ages, col, off in [("1617", PALETTE[0], -0.1), ("1819", PALETTE[1], 0.1)]:
        f = TAB / f"mw_{ages}_{y}_{D}_event.csv"
        if not f.exists(): continue
        E = pd.read_csv(f); ax.errorbar(E.k + off, E.estimate, yerr=1.96 * E.se, fmt="o", color=col, elinewidth=1.8, markersize=5, label=f"Ages {ages[:2]}-{ages[2:]}")
    ax.axhline(0, color=INK2, linewidth=1); ax.axvline(-0.5, color=GRID, linewidth=1); ax.set_xlabel("Years relative to the increase (base: year -1)"); ax.set_title(LAB[y], fontsize=10.5, loc="left"); style_axes(ax)
axes[0].legend(frameon=False, fontsize=9)
fig.suptitle("Minimum wage increases and teens: unit design (counties with their own minimum as units), 2010-2025 events", fontsize=10, x=0.01, ha="left")
fig.tight_layout(); fig.savefig(FIG / "mw_event_main.png", dpi=200)
# figure: six-outcome event-study grid, three age brackets per panel (the paper's main event figure)
OUT6 = [("log_wage", "Log hourly wage, hourly-paid teens"), ("enrolled", "Enrolled in school"), ("employed", "Employed"), ("enr_emp", "Enrolled and employed"), ("enr_only", "Enrolled only"), ("neither", "Neither enrolled nor employed")]
fig, axes = plt.subplots(2, 3, figsize=(15, 8.4))
for ax, (y, lab) in zip(axes.flat, OUT6):
    for ages, col, off in [("1617", PALETTE[0], -0.15), ("1819", PALETTE[1], 0.0), ("1619", PALETTE[2], 0.15)]:
        f = TAB / f"mw_{ages}_{y}_{D}_event.csv"
        if not f.exists(): continue
        E = pd.read_csv(f); ax.errorbar(E.k + off, E.estimate, yerr=1.96 * E.se, fmt="o", color=col, elinewidth=1.8, markersize=5, label=f"Ages {ages[:2]}-{ages[2:]}" + (" (pooled)" if ages == "1619" else ""))
    ax.axhline(0, color=INK2, linewidth=1); ax.axvline(-0.5, color=GRID, linewidth=1); ax.set_title(lab, fontsize=10.5, loc="left"); style_axes(ax)
for ax in axes[1]: ax.set_xlabel("Years relative to the increase (base: year -1)")
axes[0, 0].legend(frameon=False, fontsize=9, loc="upper left")
fig.suptitle("Unit design, 2010+ events: event-time effects by age, 95% intervals", fontsize=11, x=0.01, ha="left"); fig.tight_layout(); fig.savefig(FIG / "mw_event_grid.png", dpi=200)
# figure: four-way status, 18-19
fig, ax = plt.subplots(figsize=(7.5, 4))
for y, col in zip(["enr_emp", "enr_only", "emp_only", "neither"], PALETTE):
    f = TAB / f"mw_1819_{y}_{D}_event.csv"
    if not f.exists(): continue
    E = pd.read_csv(f); ax.plot(E.k, E.estimate, marker="o", color=col, label=LAB[y]); ax.fill_between(E.k, E.estimate - 1.96 * E.se, E.estimate + 1.96 * E.se, color=col, alpha=0.12, linewidth=0)
ax.axhline(0, color=INK2, linewidth=1); ax.axvline(-0.5, color=GRID, linewidth=1); ax.set_xlabel("Years relative to the increase"); ax.set_title("School-work status, ages 18-19", fontsize=10.5, loc="left")
ax.legend(frameon=False, fontsize=8.5, ncol=2); style_axes(ax); fig.tight_layout(); fig.savefig(FIG / "mw_status_1819.png", dpi=200)
# figure: by-event post averages, enrolled 18-19
f = TAB / f"mw_1819_enrolled_{D}_byevent.csv"
if f.exists():
    B = pd.read_csv(f).dropna(subset=["post_avg"]).sort_values("post_avg"); fig, ax = plt.subplots(figsize=(7.5, 0.22 * len(B) + 1.2))
    yy = np.arange(len(B)); ax.barh(yy, B.post_avg, color=[PALETTE[0] if v < 0 else PALETTE[1] for v in B.post_avg]); ax.set_yticks(yy); ax.set_yticklabels([f"{u} {t}" for u, t in zip(B.unit, B.event_ym)], fontsize=7.5)
    ax.axvline(0, color=INK2, linewidth=1); ax.set_xlabel("Post-event average effect on enrollment, ages 18-19"); ax.set_title("Event-by-event estimates", fontsize=10.5, loc="left"); style_axes(ax); fig.tight_layout(); fig.savefig(FIG / "mw_byevent_1819.png", dpi=200)
print("wrote figures")
