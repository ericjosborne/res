"""38_unit_panel.py -- geographic units with their own minimum wage: each identified county with a local minimum
is a unit with its own effective minimum (city rate applied to the whole county); the rest of each state is a
unit at the state rate.  Events and clean controls are defined at the unit level, so a Seattle teen is treated
by Seattle's minimum and King County has its own event when Seattle raises it.

Inputs: state_mw_monthly.csv (31), county_mw_monthly.csv (36).  Outputs: unit_mw_monthly.csv, unit_events.csv.
Event rule as in 31: a rise of >= 5% in the unit's effective minimum, not caused by the federal floor, after 36
months without one; later rises within 48 months belong to the event.  source = local (county rise without a
state rise that month), state, or both.
"""
import argparse
from pathlib import Path
import numpy as np, pandas as pd
PF = Path(__file__).resolve().parents[1]; MW = PF / "data" / "raw" / "minwage"
ap = argparse.ArgumentParser(); ap.add_argument("--min_pct", type=float, default=0.05); ap.add_argument("--pre", type=int, default=36); ap.add_argument("--post", type=int, default=48); a = ap.parse_args()

P = pd.read_csv(MW / "state_mw_monthly.csv"); months = sorted(P.ym.unique()); idx = {ym: k for k, ym in enumerate(months)}
C = pd.read_csv(MW / "county_mw_monthly.csv")
units = []
# state remainders
S = P[["state_fips", "ym", "mw", "mw_state", "mw_federal"]].copy(); S["unit"] = S.state_fips; S["rate"] = S.mw_state; S["kind"] = "state"
units.append(S[["unit", "state_fips", "kind", "ym", "mw", "rate", "mw_federal"]])
# county units: full monthly series; county rate = local rate where one exists, otherwise the state rate
fed = P.drop_duplicates("ym").set_index("ym").mw_federal
for cty, g in C.groupby("county"):
    st = int(cty) // 1000; sp = P[P.state_fips == st].set_index("ym")
    loc = g.set_index("ym").reindex(months)
    rate = loc.mw_local.where(loc.mw_local.notna(), sp.mw_state.reindex(months))
    nonurban = bool((loc.mw_county < loc.mw_state - 0.01).any())
    mw = rate if nonurban else np.maximum(rate, fed.reindex(months))
    units.append(pd.DataFrame({"unit": int(cty), "state_fips": st, "kind": "county", "ym": months, "mw": mw.values, "rate": rate.values, "mw_federal": fed.reindex(months).values}))
U = pd.concat(units, ignore_index=True).sort_values(["unit", "ym"]).reset_index(drop=True)
U["mw_prev"] = U.groupby("unit").mw.shift(1); U["fed_prev"] = U.groupby("unit").mw_federal.shift(1); U["pct"] = U.mw / U.mw_prev - 1
U["qual"] = (U.pct >= a.min_pct).astype(int)
U["qual_policy"] = ((U.qual == 1) & (U.rate > U.fed_prev) & (U.rate >= U.mw_federal)).astype(int)     # not a federal-floor rise
sq = P.set_index(["state_fips", "ym"]).qual_state
U["state_qual"] = [sq.get((s, y), 0) for s, y in zip(U.state_fips, U.ym)]
U.to_csv(MW / "unit_mw_monthly.csv", index=False)

ev = []
for u, g in U.groupby("unit"):
    g = g.reset_index(drop=True); q = g.qual.values; qp = g.qual_policy.values
    i = 0
    while i < len(g):
        if qp[i] == 1 and i >= a.pre and q[i - a.pre:i].sum() == 0:
            win = g.iloc[i:i + a.post]
            src = "state" if g.kind[0] == "state" else ("both" if g.state_qual[i] == 1 else "local")
            ev.append({"unit": int(u), "state_fips": int(g.state_fips[0]), "kind": g.kind[0], "source": src, "event_ym": g.ym[i], "mw_before": g.mw_prev[i], "mw_first": g.mw[i],
                       "mw_end": win.mw.iloc[-1], "pct_first": g.pct[i], "pct_window": win.mw.iloc[-1] / g.mw_prev[i] - 1, "n_steps": int(win.qual.sum())})
            i += a.post
        else:
            i += 1
E = pd.DataFrame(ev)
QP = U.pivot(index="ym", columns="unit", values="qual_policy"); Q = U.pivot(index="ym", columns="unit", values="qual")
unit_state = dict(zip(U.unit, U.state_fips))
ctrl, ctrl_s = [], []
for _, e in E.iterrows():
    k = idx[e.event_ym]; lo, hi = max(0, k - a.pre), min(len(QP), k + a.post)
    ok = QP.iloc[lo:hi].sum(axis=0); ctrl.append(" ".join(str(int(c)) for c in ok.index if ok[c] == 0 and unit_state[c] != e.state_fips))
    ok = Q.iloc[lo:hi].sum(axis=0); ctrl_s.append(" ".join(str(int(c)) for c in ok.index if ok[c] == 0 and unit_state[c] != e.state_fips))
E["controls"] = ctrl; E["n_controls"] = [len(c.split()) for c in ctrl]; E["controls_strict"] = ctrl_s; E["n_controls_strict"] = [len(c.split()) for c in ctrl_s]
E["event_id"] = range(1, len(E) + 1); E["federal_induced"] = 0
E.to_csv(MW / "unit_events.csv", index=False)
p = E[E.event_ym >= "2010-01"]
print(f"units: {U.unit.nunique()} ({(U.drop_duplicates('unit').kind == 'county').sum()} counties); events: {len(E)} total, {len(p)} from 2010: {p.source.value_counts().to_dict()}")
print(p[p.kind == "county"][["event_id", "unit", "source", "event_ym", "mw_before", "mw_first", "mw_end", "pct_window", "n_steps", "n_controls"]].round(2).to_string(index=False))
