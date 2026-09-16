"""46_regressions.py -- regression counterparts of the event-study results, for the tables that precede each event-study figure.

(1) Two-way fixed effects: y on log(effective minimum) of the teen's unit, with unit and year-month fixed effects and
    age, sex, race and ethnicity controls, individual-level, weighted, clustered by state (the Neumark-Shupe / Smith
    specification, on the 2010-2026 sample).  Coefficient = effect of a 100 log-point rise; x 0.32 for the average
    event (38 percent, ln 1.38 = 0.32).
(1a) The same on school months only (September-May), because the CPS enrollment item asks about attendance last
    week and in June-August measures summer school (63 percent of 16-17 year olds report enrollment in summer against
    93 percent in school months); the all-months TWFE enrollment effect is a summer-months effect.
(1b) The same with unit-specific linear trends (geo[t]), which absorb differential long-run trends between high- and
    low-minimum units.
(2) Stacked difference-in-differences: unit-month cell means stacked over the 73 events (treated unit and its clean
    controls, -36..+47 months), y on post x treated with event-by-unit and event-by-month fixed effects, cell-weighted,
    clustered by state (Cengiz et al. 2019 regression form of the design; one coefficient = post-event average).
Outputs: output/tables/mw_regressions.csv and paper/tables/tab*_reg.tex.  --reuse_stacked reads the stacked
coefficients from an existing mw_regressions.csv and recomputes only the TWFE rows (the stacked step is the slow one).
"""
import sys, warnings
from pathlib import Path
import numpy as np, pandas as pd
import pyfixest as pf
warnings.filterwarnings("ignore")
PF = Path(__file__).resolve().parents[1]; CLEAN = PF / "data" / "clean"; MW = PF / "data" / "raw" / "minwage"; TAB = PF / "output" / "tables"; PT = PF / "paper" / "tables"
PRE, POST = 36, 48
REUSE = "--reuse_stacked" in sys.argv; TABLES_ONLY = "--tables_only" in sys.argv
OLD = pd.read_csv(TAB / "mw_regressions.csv", dtype={"ages": str}) if REUSE and (TAB / "mw_regressions.csv").exists() else None
ONLY = [g for g in sys.argv if g.startswith("--only=")]; ONLY = ONLY[0][7:].split(",") if ONLY else None  # --only=female,male: estimate these groups, merge the rest from the csv

d = pd.read_csv(CLEAN / "cps_monthly_1624.csv.gz", usecols=["year", "month", "ym", "state_fips", "county", "weight", "earnwt", "age", "female", "black", "hispanic", "white", "faminc", "hs_grad",
                                                             "enrolled", "employed", "org", "hourwage", "paidhour", "earnweek"])
d = d[d.age.between(16, 19) & (d.year >= 2010)].copy(); d["county"] = d.county.fillna(0).astype(int)
U = pd.read_csv(MW / "unit_mw_monthly.csv"); U["ymi"] = U.ym.str[:4].astype(int) * 12 + U.ym.str[5:7].astype(int) - 1
county_units = set(U.unit[U.kind == "county"]); d["geo"] = np.where(d.county.isin(county_units), d.county, d.state_fips)
d = d.merge(U[["unit", "ymi", "mw"]].rename(columns={"unit": "geo", "ymi": "ym"}), on=["geo", "ym"], how="left"); d["log_mw"] = np.log(d.mw); d["t"] = d.ym - d.ym.min()
d["enr_emp"] = d.enrolled * d.employed; d["enr_only"] = d.enrolled * (1 - d.employed); d["emp_only"] = (1 - d.enrolled) * d.employed; d["neither"] = (1 - d.enrolled) * (1 - d.employed)
d["log_wage"] = np.log(d.hourwage.where((d.org == 1) & (d.paidhour == 1) & (d.hourwage > 0))); d["log_earnweek"] = np.log(d.earnweek.where((d.org == 1) & (d.earnweek > 0)))
d["lowses"] = (d.faminc <= 740).astype(int); d["highses"] = ((d.faminc >= 820) & (d.faminc < 900)).astype(int)
d["male"] = 1 - d.female; d["nonwhite"] = 1 - d.white
d["nohs_school"] = ((d.hs_grad == 0) & ((d.month <= 5) | (d.month >= 9))).astype(int)  # no diploma or GED, September-May
E = pd.read_csv(MW / "unit_events.csv"); E = E[(E.event_ym >= "2010-01") & (E.pct_window >= 0.05)]; E["ymi"] = E.event_ym.str[:4].astype(int) * 12 + E.event_ym.str[5:7].astype(int) - 1
geo_state = dict(zip(d.geo, d.state_fips))
OUT = ["enr_emp", "enr_only", "emp_only", "neither", "enrolled", "employed", "log_wage", "log_earnweek"]
AGES = {"1617": (16, 17), "1819": (18, 19), "1619": (16, 19)}; GROUPS = {"all": None, "lowses": "lowses", "highses": "highses", "female": "female", "male": "male", "white": "white", "nonwhite": "nonwhite", "nohs_school": "nohs_school"}
rows = []
for gname, gcol in ({} if TABLES_ONLY else GROUPS).items():
    if ONLY and gname not in ONLY: continue
    for aname, (a0, a1) in AGES.items():
        s = d[d.age.between(a0, a1)]
        if gcol: s = s[s[gcol] == 1]
        for y in OUT:
            x = s[s[y].notna() & s.log_mw.notna()].copy(); x["w"] = x.earnwt if y.startswith("log_") else x.weight; x = x[x.w > 0]
            # (1) TWFE
            m = pf.feols(f"{y} ~ log_mw + C(age) + female + black + hispanic | geo + ym", data=x, weights="w", vcov={"CRV1": "state_fips"})
            b1, se1 = float(m.coef()["log_mw"]), float(m.se()["log_mw"])
            # (1a) TWFE on school months only
            xs = x[(x.month <= 5) | (x.month >= 9)]
            ms = pf.feols(f"{y} ~ log_mw + C(age) + female + black + hispanic | geo + ym", data=xs, weights="w", vcov={"CRV1": "state_fips"})
            bs, ses = float(ms.coef()["log_mw"]), float(ms.se()["log_mw"])
            # (1b) TWFE with unit-specific linear trends
            mt = pf.feols(f"{y} ~ log_mw + C(age) + female + black + hispanic | geo[t] + ym", data=x, weights="w", vcov={"CRV1": "state_fips"})
            bt, set_ = float(mt.coef()["log_mw"]), float(mt.se()["log_mw"])
            if OLD is not None and len(OLD[(OLD.group == gname) & (OLD.ages == aname) & (OLD.outcome == y)]):
                o = OLD[(OLD.group == gname) & (OLD.ages == aname) & (OLD.outcome == y)].iloc[0]
                rows.append({"group": gname, "ages": aname, "outcome": y, "twfe": b1, "twfe_se": se1, "twfe_school": bs, "twfe_school_se": ses, "twfe_trend": bt, "twfe_trend_se": set_, "stacked": o.stacked, "stacked_se": o.stacked_se, "n": len(x), "n_events": o.n_events})
                print(f"{gname:8s} {aname} {y:13s} TWFE {b1:+.4f} ({se1:.4f})  school {bs:+.4f} ({ses:.4f})  trend {bt:+.4f} ({set_:.4f})  stacked (reused) {o.stacked:+.4f} ({o.stacked_se:.4f})  n={len(x):,}", flush=True); continue
            # (2) stacked DiD on unit-month cells
            x["_wy"] = x.w * x[y]; c = x.groupby(["geo", "ym"]).agg(wy=("_wy", "sum"), w=("w", "sum")).reset_index(); c["ybar"] = c.wy / c.w
            parts = []
            for e in E.itertuples():
                if e.unit not in set(c.geo): continue
                ctrl = [int(u) for u in str(e.controls).split()]
                blk = c[c.geo.isin([e.unit] + ctrl) & c.ym.between(e.ymi - PRE, e.ymi + POST - 1)].copy()
                blk["event"] = e.event_id; blk["treated"] = (blk.geo == e.unit).astype(int); blk["post"] = ((blk.ym >= e.ymi) & (blk.geo == e.unit)).astype(int); parts.append(blk)
            S = pd.concat(parts, ignore_index=True); S["eg"] = S.event.astype(str) + "_" + S.geo.astype(str); S["et"] = S.event.astype(str) + "_" + S.ym.astype(str); S["state"] = S.geo.map(geo_state)
            m2 = pf.feols("ybar ~ post | eg + et", data=S, weights="w", vcov={"CRV1": "state"})
            b2, se2 = float(m2.coef()["post"]), float(m2.se()["post"])
            rows.append({"group": gname, "ages": aname, "outcome": y, "twfe": b1, "twfe_se": se1, "twfe_school": bs, "twfe_school_se": ses, "twfe_trend": bt, "twfe_trend_se": set_, "stacked": b2, "stacked_se": se2, "n": len(x), "n_events": int(S.event.nunique())})
            print(f"{gname:8s} {aname} {y:13s} TWFE {b1:+.4f} ({se1:.4f})  school {bs:+.4f} ({ses:.4f})  trend {bt:+.4f} ({set_:.4f})  stacked {b2:+.4f} ({se2:.4f})  n={len(x):,} events={S.event.nunique()}", flush=True)
if TABLES_ONLY: R = pd.read_csv(TAB / "mw_regressions.csv", dtype={"ages": str})
else:
    R = pd.DataFrame(rows)
    if ONLY: R = pd.concat([pd.read_csv(TAB / "mw_regressions.csv", dtype={"ages": str}).query("group not in @ONLY"), R], ignore_index=True)
    R.to_csv(TAB / "mw_regressions.csv", index=False)

# ---- LaTeX tables
LAB = {"enr_emp": "Enrolled and employed", "enr_only": "Enrolled only", "emp_only": "Employed only", "neither": "Neither enrolled nor employed", "enrolled": "Enrolled", "employed": "Employed",
       "log_wage": "Log hourly wage, hourly paid", "log_earnweek": "Log weekly earnings"}
def st(b, se): z = abs(b / se); return "$^{***}$" if z > 2.576 else "$^{**}$" if z > 1.96 else "$^{*}$" if z > 1.645 else ""
def get(g, a, y, k): r = R[(R.group == g) & (R.ages == a) & (R.outcome == y)].iloc[0]; return r[k], r[k + "_se"]
# main-text tables carry the stacked DiD coefficient only; the TWFE (school months) tables go to the appendix.
# All-months TWFE stays in the csv (twfe) but is not tabulated: the enrollment item records summer school in June-August.
def tab_rows(outs, fname, key, ses=False, pair=("lowses", "highses"), heads=("Low", "High"), group="all"):
    cols = [(g, a) for a in AGES for g in (pair if ses else (group,))]
    L = []
    for y in outs:
        l1, l2 = [LAB[y]], [""]
        for g, a in cols:
            b, se = get(g, a, y, key); l1.append(f"{b:.3f}{st(b, se)}"); l2.append(f"({se:.3f})")
        L += [" & ".join(l1) + " \\\\", " & ".join(l2) + " \\\\"]
    if ses: head = "\\begin{tabular}{lcccccc}\n\\toprule\n & \\multicolumn{2}{c}{Ages 16--17} & \\multicolumn{2}{c}{Ages 18--19} & \\multicolumn{2}{c}{Ages 16--19} \\\\\n\\cmidrule(lr){2-3}\\cmidrule(lr){4-5}\\cmidrule(lr){6-7}\n & %s & %s & %s & %s & %s & %s \\\\\n\\midrule\n" % (heads * 3)
    else: head = "\\begin{tabular}{lccc}\n\\toprule\n & Ages 16--17 & Ages 18--19 & Ages 16--19 \\\\\n\\midrule\n"
    (PT / fname).write_text(head + "\n".join(L) + "\n\\bottomrule\n\\end{tabular}\n")
G6 = ["enr_emp", "enr_only", "emp_only", "neither", "enrolled", "employed"]; G4 = G6[:4]; W = ["log_wage", "log_earnweek"]
tab_rows(G6, "tabR1b_groups_reg.tex", "stacked"); tab_rows(G4, "tabR2b_groups_ses_reg.tex", "stacked", ses=True)
tab_rows(W, "tabR3b_wage_reg.tex", "stacked"); tab_rows(W, "tabR4b_wage_ses_reg.tex", "stacked", ses=True)
tab_rows(G6, "tabT1_groups_twfe.tex", "twfe_school"); tab_rows(G4, "tabT2_groups_ses_twfe.tex", "twfe_school", ses=True)
tab_rows(W, "tabT3_wage_twfe.tex", "twfe_school"); tab_rows(W, "tabT4_wage_ses_twfe.tex", "twfe_school", ses=True)
if (R.group == "nohs_school").any(): tab_rows(G6, "tabR1b_groups_reg_nohs.tex", "stacked", group="nohs_school"); tab_rows(G6, "tabT1_groups_twfe_nohs.tex", "twfe_school", group="nohs_school")
for tagn, pair, heads in (("sex", ("female", "male"), ("Girls", "Boys")), ("race", ("white", "nonwhite"), ("White", "Non-white"))):
    if not all(((R.group == g).any()) for g in pair): continue
    tab_rows(G4, f"tabR2b_groups_{tagn}_reg.tex", "stacked", ses=True, pair=pair, heads=heads); tab_rows(W, f"tabR4b_wage_{tagn}_reg.tex", "stacked", ses=True, pair=pair, heads=heads)
    tab_rows(G4, f"tabT2_groups_{tagn}_twfe.tex", "twfe_school", ses=True, pair=pair, heads=heads); tab_rows(W, f"tabT4_wage_{tagn}_twfe.tex", "twfe_school", ses=True, pair=pair, heads=heads)
print("done")
