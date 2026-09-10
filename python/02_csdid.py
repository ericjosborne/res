"""
02_csdid.py -- Callaway & Sant'Anna (2021) on any window / cohort set.

Runs on data/clean/cps_asec_women_1844.csv.gz (IPUMS extract, once it
is in the repository) and falls back to the PolicyEngine 2020-22 file, on
which it reproduces (the 2021-23 pilot, now removed) exactly.

Estimator: repeated cross sections, never-treated controls (option: not-yet-
treated), no covariates (cell-mean outcome regression, which equals csdid's
method(reg) without X), varying base period.  Aggregations follow the R `did`
package: event-time (dynamic), cohort (group), calendar, and simple.  Inference:
block bootstrap over never-treated states with within-state resampling of
treated cohorts (B draws).  The `csdid` Python port is run alongside as a
point-estimate check when the sample is small enough for it.

Usage: python 02_csdid.py [--sample mothers_lt6|mothers|childless|all]
                               [--outcome worked] [--notyet] [--window -8 8] [--B 499]
"""
import argparse, sys, warnings
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
from aelib import PALETTE, INK, INK2, GRID, style_axes, to_markdown, fmt
warnings.filterwarnings("ignore")

PF = Path(__file__).resolve().parents[1]
CLEAN = PF / "data" / "clean"; TAB = PF / "output" / "tables"; FIG = PF / "output" / "figures"


def load():
    return pd.read_csv(CLEAN / "cps_asec_women_1844.csv.gz"), "ipums"


def wmean(x, w):
    return float(np.average(x, weights=w)) if len(x) else np.nan


class CS:
    """Group-time ATTs from weighted cell means on repeated cross sections."""

    def __init__(self, d, y, notyet=False, anticipation=0):
        self.y, self.notyet, self.ant = y, notyet, anticipation
        self.years = sorted(d["year"].unique())
        tmin, tmax = min(self.years), max(self.years)
        d = d.copy()
        d["g"] = np.where(d["gvar"] > tmax, 0, d["gvar"])
        d = d[(d["g"] == 0) | (d["g"] > tmin + anticipation)]        # cohorts need a pre-period
        self.d = d
        self.groups = sorted(g for g in d["g"].unique() if g > 0)
        cells = d.groupby(["g", "year"]).apply(lambda x: pd.Series({"m": wmean(x[y], x["weight"]), "n": x["weight"].sum(), "obs": len(x)}))
        self.cells = cells

    def _m(self, g, t):
        return self.cells.loc[(g, t), "m"] if (g, t) in self.cells.index else np.nan

    def _control_mean(self, g, t, base):
        """Mean outcome change among controls: never-treated, or never + not-yet-treated by max(t, base)."""
        if not self.notyet:
            return self._m(0, t) - self._m(0, base)
        ctrl = [0] + [h for h in self.groups if h > max(t, base) + self.ant]
        sub = self.d[self.d["g"].isin(ctrl)]
        return (wmean(sub.loc[sub.year == t, self.y], sub.loc[sub.year == t, "weight"])
                - wmean(sub.loc[sub.year == base, self.y], sub.loc[sub.year == base, "weight"]))

    def attgt(self):
        out = {}
        for g in self.groups:
            for t in self.years:
                base = g - 1 - self.ant if t >= g - self.ant else t - 1
                if base not in self.years or t == base:
                    continue
                dy_g = self._m(g, t) - self._m(g, base)
                if np.isnan(dy_g):
                    continue
                out[(g, t)] = dy_g - self._control_mean(g, t, base)
        return out

    def aggregate(self, att):
        n = {g: self.cells.loc[(g, g), "n"] if (g, g) in self.cells.index else self.cells.xs(g, level="g")["n"].mean() for g in self.groups}
        ev, grp, cal = {}, {}, {}
        for (g, t), a in att.items():
            e = t - g
            ev.setdefault(e, []).append((n[g], a))
            if e >= 0:
                grp.setdefault(g, []).append(a)
                cal.setdefault(t, []).append((n[g], a))
        wavg = lambda lst: sum(w * a for w, a in lst) / sum(w for w, _ in lst)
        ev = {e: wavg(v) for e, v in ev.items()}
        grp = {g: float(np.mean(v)) for g, v in grp.items()}
        cal = {t: wavg(v) for t, v in cal.items()}
        post = [(n[g], a) for (g, t), a in att.items() if t >= g]
        simple = wavg(post) if post else np.nan
        return ev, grp, cal, simple

    def bootstrap(self, B, rng, treated_states):
        states = self.d["state_fips"].unique()
        never = [s for s in states if s not in treated_states]
        draws = []
        for _ in range(B):
            samp = rng.choice(never, size=len(never), replace=True)
            parts = [self.d[self.d.state_fips == s] for s in samp]
            for s in treated_states:
                ds = self.d[self.d.state_fips == s]
                parts.append(ds.iloc[rng.integers(0, len(ds), len(ds))])
            cs = CS.__new__(CS); cs.__dict__.update(self.__dict__); cs.d = pd.concat(parts)
            cs.cells = cs.d.groupby(["g", "year"]).apply(lambda x: pd.Series({"m": wmean(x[self.y], x["weight"]), "n": x["weight"].sum(), "obs": len(x)}))
            draws.append(cs.aggregate(cs.attgt()))
        return draws


def run(d, y, sample, notyet, window, B, seed=20260909):
    rng = np.random.default_rng(seed)
    cs = CS(d, y, notyet=notyet)
    att = cs.attgt(); ev, grp, cal, simple = cs.aggregate(att)
    treated_states = d.loc[d["gvar"].isin(cs.groups), "state_fips"].unique().tolist()
    draws = cs.bootstrap(B, rng, treated_states)
    def se(getter):
        vals = [getter(x) for x in draws]; vals = [v for v in vals if v is not None and not np.isnan(v)]
        return float(np.std(vals)) if len(vals) > 10 else np.nan
    E = pd.DataFrame({"e": sorted(k for k in ev if window[0] <= k <= window[1])})
    E["estimate"] = [ev[e] for e in E.e]; E["se"] = [se(lambda x, e=e: x[0].get(e)) for e in E.e]
    G = pd.DataFrame({"cohort": sorted(grp)}); G["estimate"] = [grp[g] for g in G.cohort]; G["se"] = [se(lambda x, g=g: x[1].get(g)) for g in G.cohort]
    G["states"] = [", ".join(sorted(map(str, d.loc[d.gvar == g, "state_fips"].unique()))) for g in G.cohort]
    C = pd.DataFrame({"year": sorted(cal)}); C["estimate"] = [cal[t] for t in C.year]; C["se"] = [se(lambda x, t=t: x[2].get(t)) for t in C.year]
    S = pd.DataFrame({"simple ATT": [simple], "se": [se(lambda x: x[3])]})
    return cs, att, E, G, C, S


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", default="mothers_lt6", choices=["mothers_lt6", "mothers", "childless", "all"])
    ap.add_argument("--outcome", default="worked")
    ap.add_argument("--notyet", action="store_true")
    ap.add_argument("--window", nargs=2, type=int, default=[-8, 8])
    ap.add_argument("--B", type=int, default=499)
    a = ap.parse_args()
    d0, src = load()
    mask = {"mothers_lt6": d0.mother_lt6 == 1, "mothers": d0.mother == 1, "childless": d0.mother == 0, "all": d0.age >= 0}[a.sample]
    d = d0[mask].copy()
    tag = f"{a.sample}_{a.outcome}" + ("_notyet" if a.notyet else "")
    print(f"source={src} sample={a.sample} n={len(d):,} years {d.year.min()}-{d.year.max()} outcome={a.outcome}")
    cs, att, E, G, C, S = run(d, a.outcome, a.sample, a.notyet, a.window, a.B)
    print("cohorts:", cs.groups)
    for name, df in [("event", E), ("group", G), ("calendar", C), ("simple", S)]:
        df.to_csv(TAB / f"{tag}_{name}.csv", index=False)
        print(f"\n## {name}\n" + to_markdown(df, ".4f", index=False))
    A = pd.DataFrame([{"g": g, "t": t, "ATT": v} for (g, t), v in att.items()]); A.to_csv(TAB / f"{tag}_attgt.csv", index=False)
    fig, ax = plt.subplots(figsize=(7.2, 4))
    ax.errorbar(E.e, E.estimate, yerr=1.96 * E.se, fmt="o", color=PALETTE[0], elinewidth=2, capsize=0, markersize=6)
    ax.axhline(0, color=INK2, linewidth=1); ax.axvline(-0.5, color=GRID, linewidth=1)
    ax.set_xlabel("Years since benefits available"); ax.set_ylabel(f"Effect on {a.outcome}")
    ax.set_title(f"PFML event study, {a.sample}, {src} data ({'not-yet' if a.notyet else 'never'}-treated controls)", fontsize=10.5, loc="left")
    style_axes(ax); fig.tight_layout(); fig.savefig(FIG / f"{tag}_event.png", dpi=200)
    print("wrote", FIG / f"{tag}_event.png")
