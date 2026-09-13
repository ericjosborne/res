"""31_build_mw_events.py -- monthly state minimum wage panel and the event list for the stacked design.

Inputs: data/raw/minwage/state_mw_changes_1974_2022.csv (Vaghul-Zipperer), federal_mw_changes.csv, and
state_mw_changes_2023plus_manual.csv (compiled from memory; verify).  Effective minimum = max(state, federal).
Event (Cengiz et al. 2019 style): a month in which the effective minimum rises by at least MIN_PCT (default 5%)
and there was no such rise in the state in the previous PRE months (36).  Later rises within the POST window (48
months) belong to the same event.  Controls for an event: states with no qualifying rise in [-PRE, +POST-1].
Outputs: data/raw/minwage/state_mw_monthly.csv, data/raw/minwage/mw_events.csv.
"""
import argparse
from pathlib import Path
import numpy as np, pandas as pd
PF = Path(__file__).resolve().parents[1]; MW = PF / "data" / "raw" / "minwage"
ap = argparse.ArgumentParser(); ap.add_argument("--min_pct", type=float, default=0.05); ap.add_argument("--pre", type=int, default=36); ap.add_argument("--post", type=int, default=48)
ap.add_argument("--start", default="1990-01"); ap.add_argument("--end", default="2025-12"); a = ap.parse_args()

s = pd.read_csv(MW / "state_mw_changes_1974_2022.csv", parse_dates=["date"])
m = pd.read_csv(MW / "state_mw_changes_2023plus_manual.csv", parse_dates=["date"])
# the 2022 file already carries steps enacted by end-2022 (through 2028); the manual list adds later enactments and
# index adjustments.  Where both give a value for the same state and month, the manual entry wins.
s = pd.concat([s[["state_fips", "state", "date", "minwage"]], m[["state_fips", "state", "date", "minwage"]].assign(manual=1)], ignore_index=True)
s["ym_"] = s.date.dt.to_period("M"); s = s.sort_values(["state_fips", "date", "manual"]).drop_duplicates(["state_fips", "ym_"], keep="last")
f = pd.read_csv(MW / "federal_mw_changes.csv", parse_dates=["date"])
fips = pd.read_csv(PF / "data" / "raw" / "pfml_policy_dates.csv")[["state_fips", "state"]] if False else None
all_fips = sorted(set(s.state_fips) | {1, 13, 16, 18, 20, 22, 28, 40, 45, 47, 48, 49, 56})   # add the federal-floor states with no state changes
months = pd.period_range(a.start, a.end, freq="M")
rows = []
for st in all_fips:
    ss = s[s.state_fips == st].sort_values("date"); name = ss.state.iloc[0] if len(ss) else {1: "Alabama", 13: "Georgia", 16: "Idaho", 18: "Indiana", 20: "Kansas", 22: "Louisiana", 28: "Mississippi", 40: "Oklahoma", 45: "South Carolina", 47: "Tennessee", 48: "Texas", 49: "Utah", 56: "Wyoming"}[st]
    for p in months:
        d = p.to_timestamp(how="start")
        stw = ss[ss.date <= d].minwage.iloc[-1] if (ss.date <= d).any() else 0.0
        fed = f[f.date <= d].minwage.iloc[-1]
        rows.append((st, name, str(p), max(stw, fed), stw, fed))
P = pd.DataFrame(rows, columns=["state_fips", "state", "ym", "mw", "mw_state", "mw_federal"])
P["mw_prev"] = P.groupby("state_fips").mw.shift(1); P["pct"] = P.mw / P.mw_prev - 1
P["qual"] = (P.pct >= a.min_pct).astype(int)
P["fed_prev"] = P.groupby("state_fips").mw_federal.shift(1)
P["qual_state"] = ((P.qual == 1) & (P.mw_state > P.fed_prev) & (P.mw_state >= P.mw_federal)).astype(int)   # rise driven by state law, not the federal floor
P.to_csv(MW / "state_mw_monthly.csv", index=False)

# events
ev = []
for st, g in P.groupby("state_fips"):
    g = g.reset_index(drop=True); q = g.qual.values; qs = g.qual_state.values
    i = 0
    while i < len(g):
        if qs[i] == 1 and i >= a.pre and q[i - a.pre:i].sum() == 0:
            win = g.iloc[i:i + a.post]
            ev.append({"state_fips": st, "state": g.state[0], "event_ym": g.ym[i], "mw_before": g.mw_prev[i], "mw_first": g.mw[i], "mw_end": win.mw.iloc[-1],
                       "pct_first": g.pct[i], "pct_window": win.mw.iloc[-1] / g.mw_prev[i] - 1, "n_steps": int(win.qual.sum()), "federal_induced": int(g.mw_state[i] < g.mw_federal[i] or g.mw_state[i] == g.mw_federal[i] == g.mw[i] and g.mw_prev[i] < g.mw_federal[i])})
            i += a.post
        else:
            i += 1
E = pd.DataFrame(ev)
# clean controls: no state-driven qualifying rise in [-pre, +post-1] months around the event ("controls"), and the
# stricter set with no rise of any kind, federal included ("controls_strict")
idx = {ym: k for k, ym in enumerate(sorted(P.ym.unique()))}
Q = P.pivot(index="ym", columns="state_fips", values="qual"); QS = P.pivot(index="ym", columns="state_fips", values="qual_state")
ctrl, ctrl_s = [], []
for _, e in E.iterrows():
    k = idx[e.event_ym]; lo, hi = max(0, k - a.pre), min(len(Q), k + a.post)
    ok = QS.iloc[lo:hi].sum(axis=0); ctrl.append(" ".join(str(int(c)) for c in ok.index if ok[c] == 0 and c != e.state_fips))
    ok = Q.iloc[lo:hi].sum(axis=0); ctrl_s.append(" ".join(str(int(c)) for c in ok.index if ok[c] == 0 and c != e.state_fips))
E["n_controls"] = [len(c.split()) for c in ctrl]; E["controls"] = ctrl; E["n_controls_strict"] = [len(c.split()) for c in ctrl_s]; E["controls_strict"] = ctrl_s
E["event_id"] = range(1, len(E) + 1)
E.to_csv(MW / "mw_events.csv", index=False)
print(f"events: {len(E)}  (federal-induced {E.federal_induced.sum()}, state {len(E) - E.federal_induced.sum()})")
print(E.assign(yr=E.event_ym.str[:4].astype(int)).groupby(pd.cut(E.event_ym.str[:4].astype(int), [1989, 1999, 2009, 2015, 2019, 2025])).size().to_string())
print(E[["event_id", "state", "event_ym", "mw_before", "mw_first", "mw_end", "pct_first", "pct_window", "n_steps", "n_controls", "n_controls_strict"]].round(3).to_string(index=False))
