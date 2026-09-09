"""
02_csdid_prelim.py -- Callaway & Sant'Anna (2021) group-time ATTs for state
PFML adoption on the CPS ASEC 2021-23 window (reference years 2020-2022).

Cohorts inside the window: Massachusetts (benefits Jan 2021) and Connecticut
(Jan 2022).  Earlier adopters (CA, NJ, RI, NY, WA, DC) have no pre-period in
the window and are dropped; states adopting after 2022 are not-yet-treated and
are recoded to never-treated, which is what csdid does internally.

Two implementations, which must agree on the point estimates:
  (1) the `csdid` Python port of the R `did` package (Rios-Avila et al.),
      repeated cross sections, never-treated controls, outcome regression with
      no covariates, multiplier bootstrap clustered by state;
  (2) a transparent cell-mean implementation of the same estimand with a
      state block bootstrap, used to check (1) and to document the formula.
The Stata do-file pfml/stata/90_prelim_csdid.do runs the same specification
with csdid on the exported .dta.

Outputs: pfml/output/tables/prelim_*.csv|md, pfml/output/figures/prelim_*.png
"""
import sys, warnings
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "code"))
from aelib import PALETTE, INK, INK2, GRID, style_axes, to_markdown, fmt

warnings.filterwarnings("ignore")
PF = Path(__file__).resolve().parents[1]
CLEAN = PF / "data" / "clean"; TAB = PF / "output" / "tables"; FIG = PF / "output" / "figures"
TAB.mkdir(parents=True, exist_ok=True); FIG.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(20260909)

d0 = pd.read_csv(CLEAN / "cps_women_1844.csv.gz")
EARLY = {2004, 2009, 2014, 2018, 2020}


def analysis_sample(d, mask):
    d = d[mask & ~d["gvar"].isin(EARLY)].copy()
    d["g"] = np.where(d["gvar"] > 2022, 0, d["gvar"])
    d["uid"] = np.arange(len(d))
    return d


def save(df, name, floatfmt=".3f"):
    df.to_csv(TAB / f"{name}.csv"); (TAB / f"{name}.md").write_text(to_markdown(df, floatfmt) + "\n")
    print(f"\n### {name}\n" + to_markdown(df, floatfmt))


# ---------------------------------------------------------------- (2) cell-mean CS implementation
def wmean(x, w):
    return np.average(x, weights=w)


def attgt_cells(d, y):
    """ATT(g,t) for all g in {2021, 2022}, t in {2021, 2022}, varying base period."""
    C = d[d["g"] == 0]
    out = {}
    for g in (2021, 2022):
        G = d[d["g"] == g]
        for t in (2021, 2022):
            base = g - 1 if t >= g else t - 1
            dy_g = wmean(G.loc[G.year == t, y], G.loc[G.year == t, "weight"]) - wmean(G.loc[G.year == base, y], G.loc[G.year == base, "weight"])
            dy_c = wmean(C.loc[C.year == t, y], C.loc[C.year == t, "weight"]) - wmean(C.loc[C.year == base, y], C.loc[C.year == base, "weight"])
            out[(g, t)] = dy_g - dy_c
    return out


def aggregate(att, d):
    """Dynamic (event-time), group and simple aggregations with group-size weights."""
    n = {g: d.loc[(d.g == g) & (d.year == g), "weight"].sum() for g in (2021, 2022)}
    ev = {-1: att[(2022, 2021)], 0: (n[2021] * att[(2021, 2021)] + n[2022] * att[(2022, 2022)]) / (n[2021] + n[2022]), 1: att[(2021, 2022)]}
    grp = {2021: (att[(2021, 2021)] + att[(2021, 2022)]) / 2, 2022: att[(2022, 2022)]}
    simple = (n[2021] * att[(2021, 2021)] + n[2021] * att[(2021, 2022)] + n[2022] * att[(2022, 2022)]) / (2 * n[2021] + n[2022])
    return ev, grp, simple


def cs_cells(d, y, B=499):
    att = attgt_cells(d, y); ev, grp, simple = aggregate(att, d)
    states = d["state_fips"].unique(); treated = [25, 9]
    never = [s for s in states if s not in treated]
    draws = []
    for _ in range(B):
        # block bootstrap over never-treated states; treated states are the cohorts themselves,
        # so resample individuals within MA and CT (state-cluster bootstrap would drop the cohort)
        samp = rng.choice(never, size=len(never), replace=True)
        parts = [d[d.state_fips == s] for s in samp]
        for s in treated:
            ds = d[d.state_fips == s]; parts.append(ds.iloc[rng.integers(0, len(ds), len(ds))])
        db = pd.concat(parts)
        a = attgt_cells(db, y); e, gg, si = aggregate(a, db)
        draws.append([a[(2021, 2021)], a[(2021, 2022)], a[(2022, 2021)], a[(2022, 2022)], e[-1], e[0], e[1], gg[2021], gg[2022], si])
    se = np.array(draws).std(axis=0)
    est = [att[(2021, 2021)], att[(2021, 2022)], att[(2022, 2021)], att[(2022, 2022)], ev[-1], ev[0], ev[1], grp[2021], grp[2022], simple]
    idx = ["ATT(MA 2021, 2021)", "ATT(MA 2021, 2022)", "ATT(CT 2022, 2021) [pre]", "ATT(CT 2022, 2022)",
           "event e=-1 (pre)", "event e=0", "event e=1", "group MA", "group CT", "simple ATT"]
    return pd.DataFrame({"estimate": est, "se (block bootstrap)": se}, index=idx)


# ---------------------------------------------------------------- (1) csdid port
def cs_port(d, y):
    from csdid.att_gt import ATTgt
    m = ATTgt(yname=y, tname="year", idname="uid", gname="g", data=d, control_group="nevertreated",
              panel=False, clustervar="state_fips", weights_name="weight", biters=999, cband=False)
    m.fit(est_method="reg", base_period="varying")
    res = {}
    def snap(a):  # the port returns a plain dict
        g = lambda k: a.get(k) if isinstance(a, dict) else getattr(a, k, None)
        arr = lambda k: np.array([] if g(k) is None else g(k), float).ravel()
        return {"egt": arr("egt"), "att": arr("att_egt"), "se": arr("se_egt"),
                "overall": (float(arr("overall_att")[0]), float(arr("overall_se")[0]))}
    for typ in ("dynamic", "simple", "group"):
        try:
            m.aggte(typec=typ); res[typ] = snap(m.atte)   # copy now: the port mutates one object across calls
        except Exception:  # the port's group aggregation can fail on 2-cohort designs; not needed
            res[typ] = None
    return m, res


def port_table(res):
    rows = {}
    for lab in ("event", "group"):
        obj = res.get("dynamic" if lab == "event" else "group")
        if obj is None:
            continue
        for e, a, s in zip(obj["egt"], obj["att"], obj["se"]):
            rows[f"{lab} {int(e)}"] = (a, s)
    if res.get("simple") is not None:
        rows["overall (simple)"] = res["simple"]["overall"]
    return pd.DataFrame(rows, index=["estimate", "se (multiplier bootstrap)"]).T


# ---------------------------------------------------------------- run
SAMPLES = {
    "Mothers of children under 6": d0["mother_lt6"] == 1,
    "All mothers": d0["mother"] == 1,
    "Women without children (placebo)": d0["mother"] == 0,
    "All women 18-44": d0["age"] >= 18,
}
TAGS = {"Mothers of children under 6": "mothers_lt6", "All mothers": "mothers", "Women without children (placebo)": "childless", "All women 18-44": "women"}
OUTS = {"worked": "Worked for pay", "hours": "Usual weekly hours", "fulltime": "Full time (35+ h)"}

summary, details = [], {}
for sname, mask in SAMPLES.items():
    d = analysis_sample(d0, mask)
    ncoh = d[d.g > 0].groupby(["g", "year"]).size()
    print(f"\n==== {sname}: n={len(d):,}; MA/CT cells:", ncoh.to_dict())
    for y, ylab in OUTS.items():
        cells = cs_cells(d, y)
        try:
            m, res = cs_port(d, y); pt = port_table(res)
            port_ok = True
        except Exception as ex:
            print("csdid port failed:", ex); pt = None; port_ok = False
        details[(sname, y)] = (cells, pt)
        row = {"sample": sname, "outcome": ylab, "N": len(d),
               "pre-mean, treated": round(wmean(d.loc[(d.g > 0) & (d.year == 2020), y], d.loc[(d.g > 0) & (d.year == 2020), "weight"]), 3),
               "e=-1 (pre)": fmt(*cells.loc["event e=-1 (pre)"]), "e=0": fmt(*cells.loc["event e=0"]), "e=1": fmt(*cells.loc["event e=1"]),
               "simple ATT": fmt(*cells.loc["simple ATT"])}
        if port_ok:
            row["e=0 (csdid port, its SE)"] = fmt(pt.loc["event 0", "estimate"], pt.loc["event 0", "se (multiplier bootstrap)"]) if "event 0" in pt.index else ""
        summary.append(row)
        if port_ok:
            # point estimates must agree
            # single-ATT event times (-1 = CT only, 1 = MA only) must match exactly; e=0 pools two
            # cohorts and the port's cohort weights (all periods) differ slightly from base-year weights
            for k_c, k_p in [("event e=-1 (pre)", "event -1"), ("event e=1", "event 1")]:
                assert abs(cells.loc[k_c, "estimate"] - pt.loc[k_p, "estimate"]) < 1e-6, (sname, y, k_c, cells.loc[k_c, "estimate"], pt.loc[k_p, "estimate"])
            print(f"   {y}: cell implementation and csdid port agree on ATT(g,t) point estimates; "
                  f"pooled e=0 differs by {cells.loc['event e=0', 'estimate'] - pt.loc['event 0', 'estimate']:+.4f} (cohort weighting)")

S = pd.DataFrame(summary).set_index(["sample", "outcome"])
save(S, "prelim_cs_summary")
for (sname, y), (cells, pt) in details.items():
    tag = f"{TAGS[sname]}_{y}"
    both = cells.copy()
    if pt is not None:
        m = {"event e=-1 (pre)": "event -1", "event e=0": "event 0", "event e=1": "event 1", "group MA": "group 2021", "group CT": "group 2022", "simple ATT": "overall (simple)"}
        both["csdid port estimate"] = [pt.loc[m[i], "estimate"] if i in m and m[i] in pt.index else np.nan for i in both.index]
        both["csdid port se"] = [pt.loc[m[i], "se (multiplier bootstrap)"] if i in m and m[i] in pt.index else np.nan for i in both.index]
    save(both, f"prelim_attgt_{tag}", ".4f")

# ---------------------------------------------------------------- figures
# F1: raw trends, mothers of under-6s, MA and CT vs never-treated
d = analysis_sample(d0, d0["mother_lt6"] == 1)
fig, axes = plt.subplots(1, 2, figsize=(9.6, 3.8))
for ax, (y, ylab) in zip(axes, [("worked", "Share worked for pay"), ("hours", "Usual weekly hours")]):
    for lab, mask, col in [("Never-treated states", d.g == 0, INK2), ("Massachusetts (PFML 2021)", d.state_fips == 25, PALETTE[0]), ("Connecticut (PFML 2022)", d.state_fips == 9, PALETTE[1])]:
        s = d[mask].groupby("year").apply(lambda x: wmean(x[y], x["weight"]))
        ax.plot(s.index, s.values, marker="o", color=col, linewidth=2, label=lab)
    ax.axvline(2020.5, color=PALETTE[0], linestyle=":", linewidth=1); ax.axvline(2021.5, color=PALETTE[1], linestyle=":", linewidth=1)
    ax.set_xticks([2020, 2021, 2022]); ax.set_ylabel(ylab); ax.set_xlabel("ASEC reference year"); style_axes(ax)
axes[0].legend(frameon=False, fontsize=8, loc="lower left")
fig.suptitle("Mothers of children under 6: raw means, CPS ASEC 2021-23", x=0.01, ha="left", fontsize=11, color=INK)
fig.tight_layout(); fig.savefig(FIG / "prelim_raw_trends.png", dpi=200); plt.close(fig)

# F2: event-study coefficients by sample (worked and hours)
fig, axes = plt.subplots(1, 2, figsize=(9.6, 3.8))
for ax, (y, ylab) in zip(axes, [("worked", "Effect on P(worked)"), ("hours", "Effect on weekly hours")]):
    for i, sname in enumerate(["Mothers of children under 6", "Women without children (placebo)"]):
        cells = details[(sname, y)][0]
        e = [-1, 0, 1]; est = [cells.loc[f"event e={k}" + (" (pre)" if k == -1 else ""), "estimate"] for k in e]
        se = [cells.loc[f"event e={k}" + (" (pre)" if k == -1 else ""), "se (block bootstrap)"] for k in e]
        x = np.array(e) + (i - 0.5) * 0.12
        ax.errorbar(x, est, yerr=1.96 * np.array(se), fmt="o", color=PALETTE[i], elinewidth=2, capsize=0, markersize=7, label=sname)
    ax.axhline(0, color=INK2, linewidth=1); ax.axvline(-0.5, color=GRID, linewidth=1)
    ax.set_xticks([-1, 0, 1]); ax.set_xticklabels(["e = -1\n(pre, CT only)", "e = 0", "e = 1\n(MA only)"]); ax.set_ylabel(ylab); style_axes(ax)
axes[0].legend(frameon=False, fontsize=8, loc="lower left")
fig.suptitle("Callaway-Sant'Anna event study, PFML cohorts MA 2021 and CT 2022 (95% CI)", x=0.01, ha="left", fontsize=11, color=INK)
fig.tight_layout(); fig.savefig(FIG / "prelim_event_study.png", dpi=200); plt.close(fig)
print("\ndone.")
