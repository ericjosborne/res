"""32_stacked_events.py -- stacked event study of state minimum wage increases and teen school enrollment
(docs/minwage_design.md).  Cengiz-Dube-Lindner-Zipperer (2019) event design with the Callaway-Sant'Anna
comparison: each event compares the treated unit with its clean controls, relative to the year before the event.

Data: data/clean/cps_monthly_1624.csv.gz (30_build_cps_monthly.py), data/raw/minwage/mw_events.csv
(31_build_mw_events.py) and, for the substate options, county_mw_monthly.csv, state_local_flags.csv and
local_events.csv (36_substate.py).  Time is the month; effects are reported by relative year k = floor(months/12),
k = -3..-1 pre and 0..3 post, base k = -1.

Usage: python 32_stacked_events.py --ages 16 19 --outcome enrolled [--events post2009|all|large|pre2010|local]
         [--controls clean|strict|federal|cleanlocal] [--treated all|nolocal|localonly] [--B 199]
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
ap.add_argument("--events", default="post2009", help="post2009 (events from 2010, no federal changes in any window) | all | large (window rise >= 20%) | pre2010 | local (county events, 36_substate.py) | unit, unit_local, unit_state, unit_both, unit_all (unit-level design, 38_unit_panel.py: counties with their own minimum are separate units from 2010, by event source)")
ap.add_argument("--controls", default="clean", help="clean (no state-driven rise in window) | strict (no rise of any kind) | federal (federal-floor states only) | cleanlocal (clean, and control teens in counties with a local minimum above the state rate, or of unknown county in a state-month with one, dropped)")
ap.add_argument("--treated", default="all", help="all | nolocal (identified counties without a local minimum) | localonly (identified counties with a local minimum above the state rate)")
ap.add_argument("--B", type=int, default=199); ap.add_argument("--equal", action="store_true", help="equal weight per event (default: treated teen population)")
ap.add_argument("--ses", default=None, help="rel_low | rel_high: family income below / at or above the within-year weighted median category among 16-19 year olds (missing excluded)")
ap.add_argument("--query", default=None); ap.add_argument("--tag", default=None); ap.add_argument("--min_post", type=int, default=12, help="events need this many post months in the data")
a = ap.parse_args()

d = pd.read_csv(CLEAN / "cps_monthly_1624.csv.gz", usecols=lambda c: c in {"year", "month", "ym", "state_fips", "county", "weight", "earnwt", "age", "female", "black", "hispanic", "white", "foreign_born", "faminc", "relate",
                                                                            "enrolled", "enr_hs", "enr_college", "enr_ft", "employed", "atwork", "inlf", "unemp", "hours", "hs_grad", "org", "hourwage", "paidhour", "earnweek", "hours_org"})
if a.ses:
    t = d[d.age.between(16, 19) & (d.faminc < 900)]
    cut = {}
    for yr, g in t.groupby("year"):                       # weighted median family income category among teens, by survey year
        g = g.sort_values("faminc"); cw = g.weight.cumsum() / g.weight.sum(); cut[yr] = int(g.faminc.values[np.searchsorted(cw.values, 0.5)])
    med = d.year.map(cut); d = d[(d.faminc < 900) & ((d.faminc < med) if a.ses == "rel_low" else (d.faminc >= med))]
d = d[d.age.between(a.ages[0], a.ages[1])]
if a.query: d = d.query(a.query)
d["county"] = d.county.fillna(0).astype(int)
d["enr_emp"] = d.enrolled * d.employed; d["enr_only"] = d.enrolled * (1 - d.employed); d["emp_only"] = (1 - d.enrolled) * d.employed; d["neither"] = (1 - d.enrolled) * (1 - d.employed)
d["dropout"] = (1 - d.enrolled) * (1 - d.hs_grad)        # Smith (2021): not enrolled and no high school diploma or GED
d["emp_ft"] = d.employed * (d.hours >= 35).astype(int); d["emp_pt"] = d.employed - d.emp_ft   # full-time: usual hours >= 35; part-time: the rest of employment (incl. hours vary)
d["log_wage"] = np.log(d.hourwage.where((d.org == 1) & (d.paidhour == 1) & (d.hourwage > 0)))
d["log_earnweek"] = np.log(d.earnweek.where((d.org == 1) & (d.earnweek > 0)))
y = a.outcome
d = d[d[y].notna()]; w = d.earnwt if y in ("log_wage", "log_earnweek") else d.weight
d["_wy"] = w * d[y]; d["_w"] = w

# substate flags: teen in an identified county with a local minimum above the state rate; teen of unknown county in a state-month that has one
Cp = pd.read_csv(MW / "county_mw_monthly.csv"); Cp["ym"] = Cp.ym.str[:4].astype(int) * 12 + Cp.ym.str[5:7].astype(int) - 1
above = set(zip(Cp.county[Cp.local_above == 1], Cp.ym[Cp.local_above == 1]))
Fl = pd.read_csv(MW / "state_local_flags.csv"); Fl["ym"] = Fl.ym.str[:4].astype(int) * 12 + Fl.ym.str[5:7].astype(int) - 1
flagged = set(zip(Fl.state_fips, Fl.ym))
key_c = list(zip(d.county, d.ym)); key_s = list(zip(d.state_fips, d.ym))
d["local_cty"] = [k in above for k in key_c]; d["unknown_flagged"] = (d.county == 0) & np.array([k in flagged for k in key_s])

# events
if a.events.startswith("unit"):
    E = pd.read_csv(MW / "unit_events.csv")
    if a.events == "unit_pre2010": E = E[E.event_ym < "2010-01"]
    elif a.events != "unit_all": E = E[E.event_ym >= "2010-01"]
    if a.events in ("unit_local", "unit_state", "unit_both"): E = E[E.source == a.events.split("_")[1]]
    if a.events == "unit_large": E = E[E.pct_window >= 0.20]
    E = E[E.pct_window >= 0.05]
elif a.events == "local":
    E = pd.read_csv(MW / "local_events.csv"); E = E[E.pct_window >= 0.05]; E["unit"] = E.county
else:
    E = pd.read_csv(MW / "mw_events.csv"); E = E[E.federal_induced == 0]; E["unit"] = E.state_fips
    if a.events == "post2009": E = E[E.event_ym >= "2010-01"]
    elif a.events == "pre2010": E = E[E.event_ym < "2010-01"]
    elif a.events == "large": E = E[E.pct_window >= 0.20]
E["ym_idx"] = E.event_ym.str[:4].astype(int) * 12 + E.event_ym.str[5:7].astype(int) - 1
# geography key: treated counties (local events) keep their county code, everything else its state; in the unit
# design every county with its own minimum is a unit throughout, and the rest of the state is the state unit
if a.events.startswith("unit"):
    local_units = set(pd.read_csv(MW / "unit_mw_monthly.csv", usecols=["unit", "kind"]).query("kind == 'county'").unit.unique())
else:
    local_units = set(E.unit) if a.events == "local" else set()
d["geo"] = np.where(d.county.isin(local_units), d.county, d.state_fips)
d["_state"] = d.state_fips

# cells: treated side and control side may use different samples
dT = d.copy()
if a.treated == "nolocal": dT = dT[(dT.county > 0) & ~dT.local_cty]
elif a.treated == "localonly": dT = dT[(dT.county > 0) & dT.local_cty]
dC = d[~(d.local_cty | d.unknown_flagged)] if a.controls == "cleanlocal" else d
def cells(x):
    c = x.groupby(["geo", "ym"])[["_wy", "_w"]].sum(); return c["_wy"].unstack("geo").fillna(0.0), c["_w"].unstack("geo").fillna(0.0)
WY_T, W_T = cells(dT); WY_C, W_C = cells(dC)
ymin, ymax = d.ym.min(), d.ym.max()
geo_state = dict(zip(d.geo, d._state)); states = sorted(d.state_fips.unique())

E = E[(E.ym_idx - PRE >= ymin) & (E.ym_idx + a.min_post - 1 <= ymax)]
E["ctrl_list"] = E["controls_strict" if a.controls == "strict" else "controls"].fillna("").apply(lambda s: [int(x) for x in str(s).split() if int(x) in W_C.columns])
if a.controls == "federal":
    fed = {1, 13, 16, 18, 20, 22, 28, 40, 45, 47, 48, 49, 56, 21, 37, 38, 42, 55, 33, 19, 51}
    E["ctrl_list"] = E.ctrl_list.apply(lambda L: [s for s in L if s in fed])
E = E[E.ctrl_list.apply(len) >= 3]
E = E[E.unit.isin(W_T.columns)].reset_index(drop=True)
K = list(range(-3, 4))


def wmean(WY, W, r0, r1, cols, mm):
    blk = WY.loc[r0:r1]; blkw = W.loc[r0:r1]
    if len(blk) == 0: return np.nan
    wy = (blk[cols].values * mm).sum(); ww = (blkw[cols].values * mm).sum()
    return wy / ww if ww > 0 else np.nan


def event_effects(mult):
    """DiD by relative year for every event, given state multiplicities (bootstrap draw)."""
    out = np.full((len(K), len(E)), np.nan); ew = np.zeros(len(E))
    for j, e in E.iterrows():
        mt = mult.get(geo_state.get(e.unit, e.unit), 0)
        if mt == 0: continue
        ci = [s for s in e.ctrl_list if mult.get(s, 0) > 0]
        if len(ci) < 2: continue
        m = np.array([mult[s] for s in ci], dtype=float); base = e.ym_idx
        Tk, Ck = {}, {}
        for k in K:
            r0 = base + 12 * k; r1 = min(r0 + 11, ymax)
            if r0 < ymin or r0 > ymax: Tk[k] = Ck[k] = np.nan; continue
            Tk[k] = wmean(WY_T, W_T, r0, r1, [e.unit], 1.0); Ck[k] = wmean(WY_C, W_C, r0, r1, ci, m)
        for i, k in enumerate(K):
            out[i, j] = (Tk[k] - Tk[-1]) - (Ck[k] - Ck[-1])
        ew[j] = (1.0 if a.equal else W_T.loc[base - 12:base - 1, e.unit].sum()) * mt
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

tag = a.tag or f"mw_{a.ages[0]}{a.ages[1]}_{y}_{a.events}" + ("" if a.controls == "clean" else f"_{a.controls}") + ("" if a.treated == "all" else f"_{a.treated}") + ("_eq" if a.equal else "")
Ev = pd.DataFrame({"k": K, "estimate": est, "se": se}); Ev.to_csv(TAB / f"{tag}_event.csv", index=False)
n_ev = int((~np.isnan(out[K.index(0)])).sum())
S = pd.DataFrame({"post_avg": [post], "se": [se_post], "pre_avg": [pre], "se_pre": [se_pre], "n_events": [n_ev], "n_obs": [len(dT)]}); S.to_csv(TAB / f"{tag}_simple.csv", index=False)
BE = E[["event_id", "unit", "event_ym", "mw_before", "mw_end", "pct_window", "n_steps"]].copy()
if "state" in E.columns: BE["state"] = E.state
if "source" in E.columns: BE["source"] = E.source
BE["post_avg"] = np.nanmean(out[[K.index(k) for k in (0, 1, 2, 3)]], axis=0); BE["pre_avg"] = np.nanmean(out[[K.index(k) for k in (-3, -2)]], axis=0); BE["weight"] = ew / ew.sum() if ew.sum() > 0 else np.nan
BE.to_csv(TAB / f"{tag}_byevent.csv", index=False)
print(f"{tag}: n_treated_side={len(dT):,} n_control_side={len(dC):,} events={n_ev} controls/event median={int(E.ctrl_list.apply(len).median()) if len(E) else 0}")
print(to_markdown(Ev, ".4f", index=False)); print(to_markdown(S, ".4f", index=False))
fig, ax = plt.subplots(figsize=(6.8, 3.9))
ax.errorbar(Ev.k, Ev.estimate, yerr=1.96 * Ev.se, fmt="o", color=PALETTE[0], elinewidth=2, markersize=6)
ax.axhline(0, color=INK2, linewidth=1); ax.axvline(-0.5, color=GRID, linewidth=1)
ax.set_xlabel("Years relative to the minimum wage increase (base: year -1)"); ax.set_ylabel(f"Effect on {y}")
ax.set_title(f"Stacked event study, ages {a.ages[0]}-{a.ages[1]}, {n_ev} events ({a.events}, {a.controls}, {a.treated})", fontsize=10, loc="left")
style_axes(ax); fig.tight_layout(); fig.savefig(FIG / f"{tag}_event.png", dpi=200)
