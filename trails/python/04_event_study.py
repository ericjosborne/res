"""04_event_study.py -- stacked event study of trail segment openings on nearby jobs (LODES ring panel).

Inputs: data/clean/ring_panel.csv (03_ring_panel.py), data/clean/segments.csv (02_segments.py).

Each segment event compares the jobs in its treated ring (<= 0.5 mile) with its own control ring (2-5 miles) relative
to the base year g - 1, the Callaway-Sant'Anna 2x2 for one cohort:
  ATT_s(e) = [ln Y_treat(g+e) - ln Y_treat(g-1)] - [ln Y_ctrl(g+e) - ln Y_ctrl(g-1)]
(the spill ring 0.5-1.5 mile is estimated the same way against the same control).  ATT(e) averages ATT_s(e) over
events, equally or by baseline treated-ring jobs (--weight jobs); "post" averages e = 0..POST.  Standard errors:
bootstrap over events, resampling whole trails (--cluster trail, default) or single segments.

Default sample: segments that add off-road trail (new_offroad, gap_closure, extension, bridge), dates to the month,
confidence high or medium, a clipped geometry, and base year and e = 0 inside the LODES years; --no_covid drops
events with g in 2020-2022; --exclude_nyc drops segments in the five boroughs (dense rings, different margins);
--min_base_jobs drops events whose treated ring had fewer jobs in the base year in the sector.

Outputs: output/tables/es_<tag>.csv (event time x outcome x ring), es_<tag>_post.csv, es_<tag>_events.csv,
output/figures/es_<tag>.png.
"""
import argparse
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
PF = Path(__file__).resolve().parents[1]; CL = PF / "data" / "clean"; TAB = PF / "output" / "tables"; FIG = PF / "output" / "figures"
ap = argparse.ArgumentParser()
ap.add_argument("--pre", type=int, default=5); ap.add_argument("--post", type=int, default=5); ap.add_argument("--B", type=int, default=999)
ap.add_argument("--weight", choices=["equal", "jobs"], default="equal"); ap.add_argument("--cluster", choices=["trail", "segment"], default="trail")
ap.add_argument("--types", default="new_offroad,gap_closure,extension,bridge"); ap.add_argument("--keep_ambiguous", action="store_true")
ap.add_argument("--keep_unclipped", action="store_true"); ap.add_argument("--no_covid", action="store_true"); ap.add_argument("--exclude_nyc", action="store_true")
ap.add_argument("--min_base_jobs", type=float, default=0); ap.add_argument("--tag", default="main"); ap.add_argument("--seed", type=int, default=20261023)
a = ap.parse_args()
OUT = ["jobs_all", "jobs_retail", "jobs_arts_rec", "jobs_accom_food"]
NYC = {"New York", "Kings", "Queens", "Bronx", "Richmond"}

P = pd.read_csv(CL / "ring_panel.csv", dtype={"segment_id": str})
S = pd.read_csv(CL / "segments.csv", dtype={"segment_id": str})
years = sorted(P.year.unique())
S = S[S.open_type.isin(a.types.split(",")) & S.confidence.isin(["high", "medium"]) & S.g.notna()]
if not a.keep_ambiguous: S = S[S.ambiguous.astype(str).str.lower() != "true"]
if not a.keep_unclipped: S = S[S.geo_status == "clipped"]
if a.no_covid: S = S[~S.g.between(2020, 2022)]
if a.exclude_nyc: S = S[~S.counties.fillna("").apply(lambda c: bool(set(x.strip() for x in c.split(";")) & NYC))]
S = S[(S.g - 1 >= years[0]) & (S.g <= years[-1])]

P = P[P.segment_id.isin(S.segment_id)].merge(S[["segment_id", "trail", "g"]], on="segment_id")
P["e"] = P.year - P.g
P = P[P.e.between(-a.pre, a.post)]
W = P.pivot_table(index=["segment_id", "trail", "g", "e"], columns="ring", values=OUT)
rows = []
for y in OUT:
    if "ctrl" not in W[y]: continue
    for rg in ["treat", "spill"]:
        if rg not in W[y]: continue
        d = (np.log(W[y][rg]) - np.log(W[y]["ctrl"])).replace([np.inf, -np.inf], np.nan).rename("d").reset_index()
        base = d[d.e == -1].set_index("segment_id").d.rename("d0")
        bj = W[y][rg].xs(-1, level="e").reset_index(level=["trail", "g"], drop=True).rename("bj")
        d = d.join(base, on="segment_id").join(bj, on="segment_id")
        d = d[d.bj >= a.min_base_jobs].dropna(subset=["d", "d0"])
        d["att"] = d.d - d.d0; d["w"] = 1.0 if a.weight == "equal" else d.bj
        rows.append(d.assign(outcome=y, ring=rg))
D = pd.concat(rows, ignore_index=True)


def est(D):
    t = D.groupby(["outcome", "ring", "e"]).apply(lambda x: np.average(x.att, weights=x.w), include_groups=False).rename("att")
    post = D[D.e >= 0].groupby(["outcome", "ring", "segment_id"]).apply(lambda x: pd.Series({"att": x.att.mean(), "w": x.w.iloc[0]}), include_groups=False)
    p = post.groupby(["outcome", "ring"]).apply(lambda x: np.average(x.att, weights=x.w), include_groups=False).rename("att")
    return t, p


t, p = est(D)
rng = np.random.default_rng(a.seed); cl = D[a.cluster if a.cluster == "trail" else "segment_id"].unique()
key = "trail" if a.cluster == "trail" else "segment_id"
G = {c: D[D[key] == c] for c in cl}; bt, bp = [], []
for b in range(a.B):
    draw = rng.choice(cl, size=len(cl), replace=True)
    Db = pd.concat([G[c].assign(segment_id=G[c].segment_id + f"#{k}") for k, c in enumerate(draw)], ignore_index=True)
    tb, pb = est(Db); bt.append(tb); bp.append(pb)
bt, bp = pd.concat(bt, axis=1), pd.concat(bp, axis=1)
T = pd.DataFrame({"att": t, "se": bt.std(axis=1), "lo": bt.quantile(0.025, axis=1), "hi": bt.quantile(0.975, axis=1),
                  "n_events": D.groupby(["outcome", "ring", "e"]).segment_id.nunique()}).reset_index()
Pt = pd.DataFrame({"att": p, "se": bp.std(axis=1), "lo": bp.quantile(0.025, axis=1), "hi": bp.quantile(0.975, axis=1),
                   "n_events": D[D.e >= 0].groupby(["outcome", "ring"]).segment_id.nunique()}).reset_index()
TAB.mkdir(parents=True, exist_ok=True); FIG.mkdir(parents=True, exist_ok=True)
T.to_csv(TAB / f"es_{a.tag}.csv", index=False); Pt.to_csv(TAB / f"es_{a.tag}_post.csv", index=False)
S[S.segment_id.isin(D.segment_id)].to_csv(TAB / f"es_{a.tag}_events.csv", index=False)
print(f"{D.segment_id.nunique()} events on {D.trail.nunique()} trails, cluster={a.cluster}, B={a.B}\n"); print(Pt.round(3).to_string(index=False))

fig, axs = plt.subplots(1, len(OUT), figsize=(3.2 * len(OUT), 3.0), sharey=True)
for ax, y in zip(axs, OUT):
    for k, (rg, col) in enumerate([("treat", "#2a78d6"), ("spill", "#eb6834")]):
        z = T[(T.outcome == y) & (T.ring == rg)]
        ax.errorbar(z.e + (k - 0.5) * 0.15, z.att, yerr=1.96 * z.se, fmt="o", ms=3.5, color=col, lw=1, capsize=0, label={"treat": "≤ 0.5 mi", "spill": "0.5–1.5 mi"}[rg])
    ax.axhline(0, color="#52514e", lw=0.8); ax.axvline(-0.5, color="#e4e3df", lw=0.8)
    ax.set_title(y.replace("jobs_", "").replace("_", " "), fontsize=10); ax.set_xlabel("years since opening")
axs[0].set_ylabel("log jobs vs. 2–5 mi ring"); axs[0].legend(frameon=False, fontsize=8)
fig.tight_layout(); fig.savefig(FIG / f"es_{a.tag}.png", dpi=200)
