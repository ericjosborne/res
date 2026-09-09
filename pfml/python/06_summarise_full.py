"""
06_summarise_full.py -- assemble the full-window results written by
04_csdid_full.py (via 05_run_full.sh) into paper-style tables and figures.

Outputs (pfml/output/):
  tables/full_summary_simple.md|csv     simple ATT by sample x outcome
  tables/full_summary_event.md|csv      event-time coefficients, headline samples
  tables/full_summary_group.md|csv      cohort ATTs, mothers of under-6s
  figures/full_event_mothers_vs_childless.png
  figures/full_group_worked.png
  figures/full_raw_trends_worked.png
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "code"))
from aelib import PALETTE, INK, INK2, GRID, style_axes, to_markdown, fmt

PF = Path(__file__).resolve().parents[1]
TAB = PF / "output" / "tables"; FIG = PF / "output" / "figures"
SAMPLES = {"mothers_lt6": "Mothers of children under 6", "mothers": "All mothers", "childless": "Women without children (placebo)"}
OUTS = {"worked": "Worked last year", "hours": "Usual weekly hours", "fulltime": "Full time", "inlf": "In labour force (March)"}
STATES = {6: "CA", 34: "NJ", 44: "RI", 36: "NY", 53: "WA", 11: "DC", 25: "MA", 9: "CT", 41: "OR", 8: "CO"}


def load(kind, s, y, notyet=False):
    p = TAB / f"full_ipums_{s}_{y}{'_notyet' if notyet else ''}_{kind}.csv"
    return pd.read_csv(p) if p.exists() else None


# ---- simple ATT table
rows = []
for s, sl in SAMPLES.items():
    for y, yl in OUTS.items():
        S = load("simple", s, y)
        if S is None:
            continue
        r = {"sample": sl, "outcome": yl, "simple ATT (never-treated)": fmt(S.iloc[0, 0], S.iloc[0, 1])}
        Sn = load("simple", s, y, notyet=True)
        if Sn is not None:
            r["simple ATT (not-yet-treated)"] = fmt(Sn.iloc[0, 0], Sn.iloc[0, 1])
        E = load("event", s, y)
        if E is not None:
            pre = E[(E.e < 0) & (E.e >= -5)]; post = E[(E.e >= 0) & (E.e <= 5)]
            r["mean pre (e=-5..-1)"] = round(pre.estimate.mean(), 4)
            r["mean post (e=0..5)"] = round(post.estimate.mean(), 4)
        rows.append(r)
T = pd.DataFrame(rows).set_index(["sample", "outcome"])
T.to_csv(TAB / "full_summary_simple.csv"); (TAB / "full_summary_simple.md").write_text(to_markdown(T) + "\n")
print(to_markdown(T))

# ---- event-time table for worked / hours, mothers_lt6 and childless
cols = {}
for s in ["mothers_lt6", "childless"]:
    for y in ["worked", "hours"]:
        E = load("event", s, y)
        if E is not None:
            cols[f"{SAMPLES[s]}: {OUTS[y]}"] = pd.Series([fmt(a, b) for a, b in zip(E.estimate, E.se)], index=E.e.astype(int))
EV = pd.DataFrame(cols); EV.index.name = "event time"
EV.to_csv(TAB / "full_summary_event.csv"); (TAB / "full_summary_event.md").write_text(to_markdown(EV) + "\n")
print("\n" + to_markdown(EV))

# ---- cohort table
G = load("group", "mothers_lt6", "worked")
if G is not None:
    G["states"] = G["states"].astype(str).apply(lambda s: ", ".join(STATES.get(int(x), x) for x in s.split(", ")))
    Gh = load("group", "mothers_lt6", "hours")
    G["worked ATT"] = [fmt(a, b) for a, b in zip(G.estimate, G.se)]
    if Gh is not None:
        G["hours ATT"] = [fmt(a, b) for a, b in zip(Gh.estimate, Gh.se)]
    Gt = G[["cohort", "states", "worked ATT"] + (["hours ATT"] if Gh is not None else [])].set_index("cohort")
    Gt.to_csv(TAB / "full_summary_group.csv"); (TAB / "full_summary_group.md").write_text(to_markdown(Gt) + "\n")
    print("\n" + to_markdown(Gt))

# ---- figure: event study, mothers of under-6s vs childless, worked and hours
fig, axes = plt.subplots(1, 2, figsize=(10, 4))
for ax, (y, yl) in zip(axes, [("worked", "Effect on P(worked last year)"), ("hours", "Effect on usual weekly hours")]):
    for i, s in enumerate(["mothers_lt6", "childless"]):
        E = load("event", s, y)
        if E is None:
            continue
        x = E.e + (i - 0.5) * 0.25
        ax.errorbar(x, E.estimate, yerr=1.96 * E.se, fmt="o", color=PALETTE[i], elinewidth=1.8, capsize=0, markersize=5, label=SAMPLES[s])
    ax.axhline(0, color=INK2, linewidth=1); ax.axvline(-0.5, color=GRID, linewidth=1.2)
    ax.set_xlabel("Years since PFML benefits available"); ax.set_ylabel(yl); style_axes(ax)
axes[0].legend(frameon=False, fontsize=8.5, loc="upper left")
fig.suptitle("PFML event study, Callaway-Sant'Anna, never-treated controls, CPS ASEC 1990-2024 (95% CI)", x=0.01, ha="left", fontsize=11, color=INK)
fig.tight_layout(); fig.savefig(FIG / "full_event_mothers_vs_childless.png", dpi=200); plt.close(fig)

# ---- figure: cohort ATTs on worked
if G is not None:
    fig, ax = plt.subplots(figsize=(7.2, 4))
    ax.errorbar(G.estimate, np.arange(len(G)), xerr=1.96 * G.se, fmt="o", color=PALETTE[0], elinewidth=2, capsize=0, markersize=6)
    ax.axvline(0, color=INK2, linewidth=1)
    ax.set_yticks(np.arange(len(G))); ax.set_yticklabels([f"{int(c)} ({s})" for c, s in zip(G.cohort, G.states)])
    ax.set_xlabel("Cohort ATT on P(worked last year), mothers of under-6s, 95% CI")
    ax.set_title("Effect of PFML by adoption cohort", fontsize=11, loc="left")
    style_axes(ax); ax.xaxis.grid(True, color=GRID); ax.yaxis.grid(False)
    fig.tight_layout(); fig.savefig(FIG / "full_group_worked.png", dpi=200); plt.close(fig)

# ---- figure: raw trends, mothers of under-6s, treated cohorts vs never-treated
d = pd.read_csv(PF / "data" / "clean" / "cps_asec_women_1844.csv.gz")
m = d[d.mother_lt6 == 1]
fig, ax = plt.subplots(figsize=(8.4, 4))
never = m[m.gvar == 0].groupby("year").apply(lambda x: np.average(x.worked, weights=x.weight))
ax.plot(never.index, never.values, color=INK2, linewidth=2.2, label="Never-treated states")
for i, (g, lab) in enumerate([(2004, "California (2004)"), (2009, "New Jersey (2009)"), (2018, "New York (2018)")]):
    s = m[m.gvar == g].groupby("year").apply(lambda x: np.average(x.worked, weights=x.weight))
    ax.plot(s.index, s.values, color=PALETTE[i], linewidth=1.8, label=lab)
    ax.axvline(g - 0.5, color=PALETTE[i], linestyle=":", linewidth=1)
ax.set_ylabel("Share worked last year"); ax.set_xlabel("Reference year"); ax.legend(frameon=False, fontsize=8.5, loc="lower right")
ax.set_title("Employment of mothers of under-6s: three largest cohorts vs never-treated states", fontsize=10.5, loc="left")
style_axes(ax); fig.tight_layout(); fig.savefig(FIG / "full_raw_trends_worked.png", dpi=200); plt.close(fig)
print("\nfigures written")
