"""32_stacked_events.py -- stacked event study of state minimum wage increases and teen school enrollment
(docs/minwage_design.md).  Cengiz-Dube-Lindner-Zipperer (2019) event design with the Callaway-Sant'Anna
comparison: each event compares the treated state with its clean controls, relative to the year before the event.

Data: data/clean/cps_monthly_1624.csv.gz (30_build_cps_monthly.py) and data/raw/minwage/mw_events.csv
(31_build_mw_events.py).  Time is the month; effects are reported by relative year k = floor(months/12),
k = -3..-1 pre and 0..3 post, base k = -1 (the 12 months before the increase).

Usage: python 32_stacked_events.py --ages 16 19 --outcome enrolled [--events post2009|all|large] [--B 199]
Outputs: output/tables/mw_<tag>_{event,byevent,simple}.csv, output/figures/mw_<tag>_event.png
"""
import argparse, sys
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
sys.path.insert(0, str(Path(__file__).resolve().parent))
from aelib import PALETTE, INK2, GRID, style_axes, to_markdown
PF = Path(__file__).resolve().parents[1]; CLEAN = PF / "data" / "clean"; MW = PF / "data" / "raw" / "minwage"; TAB = PF / "output" / "tables"; FIG = PF / "output" / "figures"
PRE, POST = 36, 48

ap = argparse.ArgumentParser()
ap.add_argument("--ages", nargs=2, type=int, default=[16, 19]); ap.add_argument("--outcome", default="enrolled")
ap.add_argument("--events", default="post2009", help="post2009 (events from 2010, no federal changes in any window) | all | large (window rise >= 20%) | pre2010")
ap.add_argument("--controls", default="clean", help="clean (no state-driven rise in window) | strict (no rise of any kind) | federal (federal-floor states only)")
ap.add_argument("--B", type=int, default=199); ap.add_argument("--equal", action="store_true", help="equal weight per event (default: treated teen population)")
ap.add_argument("--query", default=None); ap.add_argument("--tag", default=None); ap.add_argument("--min_post", type=int, default=12, help="events need this many post months in the data")
a = ap.parse_args()

d = pd.read_csv(CLEAN / "cps_monthly_1624.csv.gz", usecols=lambda c: c in {"year", "month", "ym", "state_fips", "weight", "earnwt", "age", "female", "black", "hispanic", "foreign_born", "faminc", "relate",
                                                                            "enrolled", "enr_hs", "enr_college", "enr_ft", "employed", "atwork", "inlf", "unemp", "hours", "hs_grad", "org", "hourwage", "paidhour", "earnweek", "hours_org"})
d = d[d.age.between(a.ages[0], a.ages[1])]
if a.query: d = d.query(a.query)
d["enr_emp"] = d.enrolled * d.employed; d["enr_only"] = d.enrolled * (1 - d.employed); d["emp_only"] = (1 - d.enrolled) * d.employed; d["neither"] = (1 - d.enrolled) * (1 - d.employed)
d["log_wage"] = np.log(d.hourwage.where((d.org == 1) & (d.paidhour == 1) & (d.hourwage > 0)))
d["log_earnweek"] = np.log(d.earnweek.where((d.org == 1) & (d.earnweek > 0)))
y = a.outcome
if y in ("log_wage", "log_earnweek"):
    d = d[d[y].notna()]; w = d.earnwt
else:
    d = d[d[y].notna()]; w = d.weight
d["_wy"] = w * d[y]; d["_w"] = w
cells = d.groupby(["state_fips", "ym"])[["_wy", "_w"]].sum()          # state x month sufficient statistics
WY = cells["_wy"].unstack("state_fips").fillna(0.0); W = cells["_w"].unstack("state_fips").fillna(0.0)
ym_index = {ym: i for i, ym in enumerate(WY.index)}; states = list(WY.columns)
ymin, ymax = WY.index.min(), WY.index.max()

E = pd.read_csv(MW / "mw_events.csv")
E["ym_idx"] = E.event_ym.str[:4].astype(int) * 12 + E.event_ym.str[5:7].astype(int) - 1
E = E[E.federal_induced == 0]
if a.events == "post2009": E = E[E.event_ym >= "2010-01"]
elif a.events == "pre2010": E = E[E.event_ym < "2010-01"]
elif a.events == "large": E = E[E.pct_window >= 0.20]
E = E[(E.ym_idx - PRE >= ymin) & (E.ym_idx + a.min_post - 1 <= ymax)]
E["ctrl_list"] = E["controls_strict" if a.controls == "strict" else "controls"].fillna("").apply(lambda s: [int(x) for x in s.split() if int(x) in states])
if a.controls == "federal":
    fed = {1, 13, 16, 18, 20, 22, 28, 40, 45, 47, 48, 49, 56, 21, 37, 38, 42, 55, 33, 19, 51}   # states at the federal floor from 2010 (VA until 2021)
    E["ctrl_list"] = E.ctrl_list.apply(lambda L: [s for s in L if s in fed])
E = E[E.ctrl_list.apply(len) >= 3].reset_index(drop=True)
K = list(range(-3, 4))


def event_effects(mult):
    """DiD by relative year for every event, given state multiplicities (bootstrap draw); returns (K x nE) array and event weights."""
    m = np.array([mult.get(s, 0) for s in states], dtype=float)
    out = np.full((len(K), len(E)), np.nan); ew = np.zeros(len(E))
    for j, e in E.iterrows():
        if mult.get(e.state_fips, 0) == 0: continue
        ci = [states.index(s) for s in e.ctrl_list if mult.get(s, 0) > 0]
        if len(ci) < 2: continue
        ti = states.index(e.state_fips); base = e.ym_idx
        def mean(rows, cols, mm):
            lo, hi = ym_index.get(rows[0]), ym_index.get(rows[-1])
            if lo is None or hi is None: return np.nan
            wy = (WY.iloc[lo:hi + 1, cols].values * mm).sum(); ww = (W.iloc[lo:hi + 1, cols].values * mm).sum()
            return wy / ww if ww > 0 else np.nan
        Tk, Ck = {}, {}
        for k in K:
            rows = [base + 12 * k, base + 12 * k + 11]
            if rows[0] < ymin or rows[0] > ymax: Tk[k] = Ck[k] = np.nan; continue
            rows[1] = min(rows[1], ymax)
            Tk[k] = mean(rows, [ti], 1.0); Ck[k] = mean(rows, ci, m[ci])
        for i, k in enumerate(K):
            out[i, j] = (Tk[k] - Tk[-1]) - (Ck[k] - Ck[-1])
        lo, hi = ym_index[base - 12], ym_index[base - 1]
        ew[j] = 1.0 if a.equal else W.iloc[lo:hi + 1, ti].sum()
        ew[j] *= mult.get(e.state_fips, 0)
    return out, ew


def aggregate(out, ew):
    res = []
    for i, k in enumerate(K):
        ok = ~np.isnan(out[i]); res.append(np.average(out[i][ok], weights=ew[ok]) if ew[ok].sum() > 0 else np.nan)
    res = np.array(res); post = np.nanmean(res[[K.index(k) for k in (0, 1, 2, 3)]]); pre = np.nanmean(res[[K.index(k) for k in (-3, -2)]])
    return res, post, pre


full = {s: 1 for s in states}
out, ew = event_effects(full); est, post, pre = aggregate(out, ew)
rng = np.random.default_rng(20260913); draws = []
for b in range(a.B):
    samp = rng.choice(states, size=len(states), replace=True); mult = {s: int((samp == s).sum()) for s in states}
    o, w_ = event_effects(mult); draws.append(aggregate(o, w_))
se = np.nanstd(np.array([x[0] for x in draws]), axis=0); se_post = np.nanstd([x[1] for x in draws]); se_pre = np.nanstd([x[2] for x in draws])

tag = a.tag or f"mw_{a.ages[0]}{a.ages[1]}_{y}_{a.events}" + ("" if a.controls == "clean" else f"_{a.controls}") + ("_eq" if a.equal else "")
Ev = pd.DataFrame({"k": K, "estimate": est, "se": se}); Ev.to_csv(TAB / f"{tag}_event.csv", index=False)
S = pd.DataFrame({"post_avg": [post], "se": [se_post], "pre_avg": [pre], "se_pre": [se_pre], "n_events": [int((~np.isnan(out[K.index(0)])).sum())], "n_obs": [len(d)]}); S.to_csv(TAB / f"{tag}_simple.csv", index=False)
BE = E[["event_id", "state", "event_ym", "mw_before", "mw_end", "pct_window", "n_steps"]].copy()
BE["post_avg"] = np.nanmean(out[[K.index(k) for k in (0, 1, 2, 3)]], axis=0); BE["pre_avg"] = np.nanmean(out[[K.index(k) for k in (-3, -2)]], axis=0); BE["weight"] = ew / ew.sum()
BE.to_csv(TAB / f"{tag}_byevent.csv", index=False)
print(f"{tag}: n={len(d):,} events={S.n_events[0]} controls/event median={int(E.ctrl_list.apply(len).median())}")
print(to_markdown(Ev, ".4f", index=False)); print(to_markdown(S, ".4f", index=False))
fig, ax = plt.subplots(figsize=(6.8, 3.9))
ax.errorbar(Ev.k, Ev.estimate, yerr=1.96 * Ev.se, fmt="o", color=PALETTE[0], elinewidth=2, markersize=6)
ax.axhline(0, color=INK2, linewidth=1); ax.axvline(-0.5, color=GRID, linewidth=1)
ax.set_xlabel("Years relative to the minimum wage increase (base: year -1)"); ax.set_ylabel(f"Effect on {y}")
ax.set_title(f"Stacked event study, ages {a.ages[0]}-{a.ages[1]}, {S.n_events[0]} events ({a.events})", fontsize=10.5, loc="left")
style_axes(ax); fig.tight_layout(); fig.savefig(FIG / f"{tag}_event.png", dpi=200)
