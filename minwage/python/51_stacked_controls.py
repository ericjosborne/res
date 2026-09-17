"""51_stacked_controls.py -- stacked difference-in-differences with individual controls, computed on finely collapsed cells.
Cells are unit x month x single year of age x sex x race/ethnicity (non-Hispanic white, Black, Hispanic, other) x CPS
family income category; the regression of the cell mean on post x treated with event-by-unit and event-by-month fixed
effects plus fixed effects for age, sex, race/ethnicity and income category, weighted by the cell's summed weight, is
numerically the person-level regression with those controls as dummies.  Clustered by state.
Usage: python python/51_stacked_controls.py [--groups all,lowses,...] [--outcomes ...] ; writes output/tables/mw_stacked_controls.csv
and paper/tables/tab*_reg.tex (the paper's stacked tables, now with controls) via --tables."""
import sys, time, warnings
from pathlib import Path
import numpy as np, pandas as pd, pyfixest as pf
warnings.filterwarnings("ignore")
PF = Path(__file__).resolve().parents[1]; CLEAN = PF / "data" / "clean"; MW = PF / "data" / "raw" / "minwage"; TAB = PF / "output" / "tables"; PT = PF / "paper" / "tables"
PRE, POST = 36, 48
arg = lambda k, d: next((a[len(k) + 1:] for a in sys.argv if a.startswith(k + "=")), d)
GROUPS = arg("--groups", "all").split(","); OUTS = arg("--outcomes", "enr_emp,enr_only,emp_only,neither,enrolled,employed,log_wage,log_earnweek").split(",")
AGES = {"1617": (16, 17), "1819": (18, 19), "1619": (16, 19)}
OUTF = TAB / "mw_stacked_controls.csv"

if "--tables" not in sys.argv:
    d = pd.read_csv(CLEAN / "cps_monthly_1624.csv.gz", usecols=["year", "month", "ym", "state_fips", "county", "weight", "earnwt", "age", "female", "black", "hispanic", "white", "faminc", "hs_grad",
                                                                 "enrolled", "employed", "org", "hourwage", "paidhour", "earnweek"])
    d = d[d.age.between(16, 19) & (d.year >= 2010)].copy(); d["county"] = d.county.fillna(0).astype(int)
    U = pd.read_csv(MW / "unit_mw_monthly.csv", usecols=["unit", "kind"]); county_units = set(U.unit[U.kind == "county"]); d["geo"] = np.where(d.county.isin(county_units), d.county, d.state_fips)
    d["race4"] = np.select([d.hispanic == 1, d.black == 1, d.white == 1], [3, 2, 1], 4); d["finc"] = d.faminc.where(d.faminc < 900, 999)
    d["enr_emp"] = d.enrolled * d.employed; d["enr_only"] = d.enrolled * (1 - d.employed); d["emp_only"] = (1 - d.enrolled) * d.employed; d["neither"] = (1 - d.enrolled) * (1 - d.employed)
    d["log_wage"] = np.log(d.hourwage.where((d.org == 1) & (d.paidhour == 1) & (d.hourwage > 0))); d["log_earnweek"] = np.log(d.earnweek.where((d.org == 1) & (d.earnweek > 0)))
    d["lowses"] = (d.faminc <= 740).astype(int); d["highses"] = ((d.faminc >= 820) & (d.faminc < 900)).astype(int); d["male"] = 1 - d.female; d["nonwhite"] = 1 - d.white
    d["nohs_school"] = ((d.hs_grad == 0) & ((d.month <= 5) | (d.month >= 9))).astype(int)
    E = pd.read_csv(MW / "unit_events.csv"); E = E[(E.event_ym >= "2010-01") & (E.pct_window >= 0.05)]
    E = E[(E.event_ym >= "2013-01") & (E.event_ym <= "2025-01")].copy(); E["ymi"] = E.event_ym.str[:4].astype(int) * 12 + E.event_ym.str[5:7].astype(int) - 1  # full 36-month pre-period and 12 post months inside the 2010-2025 window, as in the event studies (70 events)
    geo_state = dict(zip(d.geo, d.state_fips)); CELL = ["geo", "ym", "age", "female", "race4", "finc"]
    old = pd.read_csv(OUTF, dtype={"ages": str}) if OUTF.exists() else pd.DataFrame(columns=["group"])
    rows = []
    for g in GROUPS:
        for a, (a0, a1) in AGES.items():
            s = d[d.age.between(a0, a1)]
            if g != "all": s = s[s[g] == 1]
            for y in OUTS:
                t0 = time.time(); x = s[s[y].notna()].copy(); x["w"] = x.earnwt if y.startswith("log_") else x.weight; x = x[x.w > 0]; x["_wy"] = x.w * x[y]
                c = x.groupby(CELL).agg(wy=("_wy", "sum"), w=("w", "sum")).reset_index(); c["ybar"] = c.wy / c.w; del c["wy"]
                units = set(c.geo); parts = []
                for e in E.itertuples():
                    if e.unit not in units: continue
                    ctrl = [int(u) for u in str(e.controls).split()]
                    blk = c[c.geo.isin([e.unit] + ctrl) & c.ym.between(e.ymi - PRE, e.ymi + POST - 1)].copy()
                    blk["event"] = e.event_id; blk["post"] = ((blk.ym >= e.ymi) & (blk.geo == e.unit)).astype(np.int8); parts.append(blk)
                S = pd.concat(parts, ignore_index=True); del parts, c
                S["eg"] = (S.event * 100000 + S.geo).astype(np.int64); S["et"] = (S.event * 10000 + S.ym).astype(np.int64); S["state"] = S.geo.map(geo_state).astype(np.int16)
                S = S[["ybar", "post", "w", "eg", "et", "age", "female", "race4", "finc", "state", "event"]]; n_cells, n_ev = len(S), int(S.event.nunique()); S = S.drop(columns="event")
                m1 = pf.feols("ybar ~ post | eg + et + age + female + race4 + finc", data=S, weights="w", vcov={"CRV1": "state"}, copy_data=False, store_data=False)
                b, se = float(m1.coef()["post"]), float(m1.se()["post"]); del m1, S
                rows.append({"group": g, "ages": a, "outcome": y, "stacked_ctrl": b, "stacked_ctrl_se": se, "n_cells": n_cells, "n_persons": len(x), "n_events": n_ev})
                print(f"{g:11s} {a} {y:13s} with controls {100*b:+.2f} ({100*se:.2f})  cells={n_cells:,} persons={len(x):,} {time.time()-t0:.0f}s", flush=True)
        R = pd.concat([old[~old.group.isin(GROUPS)], pd.DataFrame(rows)], ignore_index=True); R.to_csv(OUTF, index=False)
    print("done")

if "--tables" in sys.argv:
    R = pd.read_csv(OUTF, dtype={"ages": str})
    LAB = {"enr_emp": "Enrolled and employed", "enr_only": "Enrolled only", "emp_only": "Employed only", "neither": "Neither enrolled nor employed", "enrolled": "Enrolled", "employed": "Employed",
           "log_wage": "Log hourly wage, hourly paid", "log_earnweek": "Log weekly earnings"}
    def st(b, se): z = abs(b / se); return "$^{***}$" if z > 2.576 else "$^{**}$" if z > 1.96 else "$^{*}$" if z > 1.645 else ""
    def get(g, a, y): r = R[(R.group == g) & (R.ages == a) & (R.outcome == y)].iloc[0]; return r.stacked_ctrl, r.stacked_ctrl_se
    def tab(outs, fname, cols, heads=None):
        L = []
        for y in outs:
            l1, l2 = [LAB[y]], [""]
            for g, a in cols: b, se = get(g, a, y); l1.append(f"{b:.3f}{st(b, se)}"); l2.append(f"({se:.3f})")
            L += [" & ".join(l1) + " \\\\", " & ".join(l2) + " \\\\"]
        if heads: head = "\\begin{tabular}{lcccccc}\n\\toprule\n & \\multicolumn{2}{c}{Ages 16--17} & \\multicolumn{2}{c}{Ages 18--19} & \\multicolumn{2}{c}{Ages 16--19} \\\\\n\\cmidrule(lr){2-3}\\cmidrule(lr){4-5}\\cmidrule(lr){6-7}\n & %s & %s & %s & %s & %s & %s \\\\\n\\midrule\n" % (heads * 3)
        else: head = "\\begin{tabular}{lccc}\n\\toprule\n & Ages 16--17 & Ages 18--19 & Ages 16--19 \\\\\n\\midrule\n"
        (PT / fname).write_text(head + "\n".join(L) + "\n\\bottomrule\n\\end{tabular}\n"); print("wrote", fname)
    G6 = ["enr_emp", "enr_only", "emp_only", "neither", "enrolled", "employed"]; G4 = G6[:4]; W = ["log_wage", "log_earnweek"]
    have = set(R.group)
    if "all" in have: tab(G6, "tabR1b_groups_reg.tex", [("all", a) for a in AGES]); tab(W, "tabR3b_wage_reg.tex", [("all", a) for a in AGES])
    for tagn, pair, heads in (("ses", ("lowses", "highses"), ("Low", "High")), ("sex", ("female", "male"), ("Girls", "Boys")), ("race", ("white", "nonwhite"), ("White", "Non-white"))):
        if set(pair) <= have:
            cols = [(g, a) for a in AGES for g in pair]; tab(G4, f"tabR2b_groups_{tagn}_reg.tex", cols, heads); tab(W, f"tabR4b_wage_{tagn}_reg.tex", cols, heads)
    if "nohs_school" in have: tab(G6, "tabR1b_groups_reg_nohs.tex", [("nohs_school", a) for a in AGES])
