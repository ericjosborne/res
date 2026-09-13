"""22_summarise_nsch.py -- collect the NSCH runs (21_run_nsch.sh) into summary tables and figures."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
sys.path.insert(0, str(Path(__file__).resolve().parent))
from aelib import PALETTE, INK, INK2, GRID, style_axes, to_markdown

PF = Path(__file__).resolve().parents[1]; TAB = PF / "output" / "tables"; FIG = PF / "output" / "figures"; CLEAN = PF / "data" / "clean"
d = pd.read_csv(CLEAN / "nsch_children.csv.gz", low_memory=False)
d = d[d.year.between(2010, 2024)]

LAB = {"a1_ment": "Mental health score 1-5 (5 = poor)", "a1_ment_fairpoor": "Mental health fair/poor", "a1_ment_excellent": "Mental health excellent",
       "a1_phys": "Physical health score 1-5", "parent_stress": "Parenting stress score 1-5", "stress_any": "Any stress item usually/always",
       "coping_notwell": "Coping not well with parenting", "support": "Has emotional support", "a1_employed": "Employed", "a1_fulltime": "Employed full-time",
       "child_fairpoor": "Child health fair/poor", "prev_visit": "Child preventive visit, 12 months", "everbf": "Ever breastfed", "bf_ge26wk": "Breastfed 26+ weeks",
       "a2_ment": "Second adult (father) mental health 1-5"}


def simple(tag):
    f = TAB / f"{tag}_simple.csv"
    if not f.exists():
        return np.nan, np.nan
    s = pd.read_csv(f); return float(s.iloc[0, 0]), float(s.iloc[0, 1])


def event(tag):
    f = TAB / f"{tag}_event.csv"; return pd.read_csv(f) if f.exists() else None


def mean_pre(mask, y):
    x = d[mask & d[y].notna() & (d.gvar.between(2011, 2024)) & (d.year < d.gvar)]
    return float(np.average(x[y], weights=x.weight)) if len(x) else np.nan


def stars(b, se):
    if np.isnan(se) or se == 0: return ""
    z = abs(b / se); return "***" if z > 2.576 else "**" if z > 1.96 else "*" if z > 1.645 else ""


rows = []
m05 = (d.mother == 1) & (d.child_age <= 5)
for y in ["a1_ment", "a1_ment_fairpoor", "a1_ment_excellent", "a1_phys", "parent_stress", "stress_any", "coping_notwell", "support", "a1_employed", "a1_fulltime",
          "child_fairpoor", "prev_visit", "everbf", "bf_ge26wk"]:
    b, se = simple(f"nsch_mothers_0_5_{y}"); n = int((m05 & d[y].notna()).sum())
    rows.append({"outcome": LAB[y], "pre-period mean (treated cohorts)": mean_pre(m05, y), "simple ATT": b, "s.e.": se, "sig": stars(b, se), "n": n})
T1 = pd.DataFrame(rows)

rows = []
for tag, lab, mask, y in [("nsch_mothers_0_1_a1_ment", "Mothers, child 0-1", (d.mother == 1) & (d.child_age <= 1), "a1_ment"),
                          ("nsch_mothers_2_3_a1_ment", "Mothers, child 2-3", (d.mother == 1) & d.child_age.between(2, 3), "a1_ment"),
                          ("nsch_mothers_4_5_a1_ment", "Mothers, child 4-5", (d.mother == 1) & d.child_age.between(4, 5), "a1_ment"),
                          ("nsch_mothers_0_5_a1_ment", "Mothers, child 0-5 (main)", m05, "a1_ment"),
                          ("nsch_fathers_0_5_a1_ment", "Respondent fathers, child 0-5", (d.father == 1) & (d.child_age <= 5), "a1_ment"),
                          ("nsch_a2fathers_0_5_a2_ment", "Fathers as second adult (mother responds), 0-5", m05 & (d.a2_father == 1), "a2_ment"),
                          ("nsch_calendar_mothers_6_17_a1_ment", "Placebo: mothers of 6-17 year olds, calendar time (not exposed at birth)", (d.mother == 1) & (d.child_age >= 6), "a1_ment"),
                          ("nsch_calendar_mothers_0_5_a1_ment", "Mothers of 0-5, calendar time (survey year, not birth year)", m05, "a1_ment")]:
    b, se = simple(tag); b2, se2 = simple(tag.replace("a1_ment", "a1_ment_fairpoor")) if "a2" not in tag and "calendar" not in tag else (np.nan, np.nan)
    b3, se3 = simple(tag.replace("a1_ment", "a1_phys")) if "a2" not in tag else (np.nan, np.nan)
    rows.append({"sample": lab, "score ATT": b, "s.e.": se, "sig": stars(b, se), "fair/poor ATT": b2, "s.e. ": se2, "sig ": stars(b2, se2),
                 "physical ATT": b3, "s.e.  ": se3, "sig  ": stars(b3, se3), "n": int((mask & d[y].notna()).sum())})
T2 = pd.DataFrame(rows)

rows = []
for tag, lab in [("nsch_mothers_0_5_a1_ment", "Main (never-treated controls, base g-1, reported birth year from 2019)"),
                 ("nsch_mothers_0_5_a1_ment_notyet", "Not-yet-treated controls"),
                 ("nsch_mothers_0_5_a1_ment_ant1", "Base period g-2 (births in g-1 partly exposed)"),
                 ("nsch_mothers_0_5_a1_ment_yearminusage", "Birth year = survey year minus age, all years"),
                 ("nsch_mothers_0_5_a1_ment_nopandemic", "Drop 2020 and 2021 surveys"),
                 ("nsch_mothers_0_5_a1_ment_s2019plus", "Surveys 2019-2024 only (reported birth year)"),
                 ("nsch_mothers_0_5_a1_ment_noNY", "Drop New York (cohort 2018)")]:
    b, se = simple(tag); b2, se2 = simple(tag.replace("a1_ment", "a1_ment_fairpoor")); b3, se3 = simple(tag.replace("a1_ment", "a1_ment_excellent")); b4, se4 = simple(tag.replace("a1_ment", "a1_phys"))
    rows.append({"specification": lab, "score ATT": b, "s.e.": se, "fair/poor ATT": b2, "s.e. ": se2, "excellent ATT": b3, "s.e.  ": se3, "physical ATT": b4, "s.e.   ": se4})
T3 = pd.DataFrame(rows)

rows = []
for k, lab in [("lowinc", "Family income < 200% FPL"), ("highinc", "Family income >= 200% FPL"), ("married", "Married"), ("unmarried", "Not married"),
               ("white", "White non-Hispanic"), ("black", "Black"), ("hispanic", "Hispanic"), ("college", "BA or more"), ("noncollege", "Less than BA")]:
    b, se = simple(f"nsch_het_{k}_a1_ment"); b2, se2 = simple(f"nsch_het_{k}_a1_ment_fairpoor")
    rows.append({"subgroup": lab, "score ATT": b, "s.e.": se, "sig": stars(b, se), "fair/poor ATT": b2, "s.e. ": se2, "sig ": stars(b2, se2)})
T4 = pd.DataFrame(rows)

with open(TAB / "nsch_summary.md", "w") as f:
    f.write("## Mothers of children 0-5: simple ATT by outcome\n\n" + to_markdown(T1, ".3f", index=False))
    f.write("\n\n## Samples: age bands, fathers, placebo\n\n" + to_markdown(T2, ".3f", index=False))
    f.write("\n\n## Robustness (mothers 0-5)\n\n" + to_markdown(T3, ".3f", index=False))
    f.write("\n\n## Heterogeneity (mothers 0-5)\n\n" + to_markdown(T4, ".3f", index=False))
print(open(TAB / "nsch_summary.md").read())

# figure 1: event studies for the score and fair/poor, mothers 0-5, with the placebo
fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
for ax, y, lab in zip(axes, ["a1_ment", "a1_phys"], ["Mental health score (1 excellent - 5 poor)", "Physical health score (1 excellent - 5 poor)"]):
    for tag, col, name, off in [(f"nsch_mothers_0_5_{y}", PALETTE[0], "Mothers, child 0-5, exposure at birth (birth-year time)", -0.12),
                                (f"nsch_calendar_mothers_0_5_{y}", PALETTE[1], "Same mothers, calendar time (survey year)", 0.12)]:
        E = event(tag)
        if E is None: continue
        E = E[E.e.between(-5, 5)]
        ax.errorbar(E.e + off, E.estimate, yerr=1.96 * E.se, fmt="o", color=col, elinewidth=1.8, markersize=5, label=name)
    ax.axhline(0, color=INK2, linewidth=1); ax.axvline(-0.5, color=GRID, linewidth=1)
    ax.set_xlabel("Years relative to first treated birth year (or survey year)"); ax.set_title(lab, fontsize=10.5, loc="left"); style_axes(ax)
axes[0].legend(frameon=False, fontsize=8.5, loc="lower left")
fig.suptitle("PFML and mothers' self-rated health, NSCH 2016-2024 (Callaway-Sant'Anna, never-treated controls)", fontsize=10, x=0.01, ha="left")
fig.tight_layout(); fig.savefig(FIG / "nsch_event_mothers.png", dpi=200)

# figure 2: simple ATT by sample (bands, fathers, placebo) for the score
fig, ax = plt.subplots(figsize=(9.5, 4.2))
T = T2.dropna(subset=["score ATT"]); yy = np.arange(len(T))[::-1]
ax.errorbar(T["score ATT"], yy, xerr=1.96 * T["s.e."], fmt="o", color=PALETTE[0], elinewidth=1.8, markersize=6)
ax.axvline(0, color=INK2, linewidth=1); ax.set_yticks(yy); ax.set_yticklabels(T["sample"], fontsize=9)
ax.set_xlabel("Simple ATT on mental health score (1-5, higher = worse), 95% intervals"); ax.set_title("Who is affected: age at survey, fathers, placebos", fontsize=10.5, loc="left")
style_axes(ax); fig.subplots_adjust(left=0.5, right=0.97, top=0.9, bottom=0.15); fig.savefig(FIG / "nsch_samples.png", dpi=200)

# figure 3: raw mental-health score by birth year, treated (2018+ cohorts) vs never-treated, mothers 0-5
fig, ax = plt.subplots(figsize=(7.5, 4))
x = d[m05 & d.a1_ment.notna()].copy()
x["grp"] = np.select([x.gvar.isin([2018, 2020, 2021, 2022]), x.gvar == 0], ["Cohorts 2018-2022 (NY, WA, DC, MA, CT)", "Never treated"], "other")
for g, col in [("Cohorts 2018-2022 (NY, WA, DC, MA, CT)", PALETTE[0]), ("Never treated", PALETTE[1])]:
    s = x[x.grp == g].groupby("year").apply(lambda z: np.average(z.a1_ment, weights=z.weight))
    s = s[(s.index >= 2011) & (s.index <= 2022)]
    ax.plot(s.index, s.values, marker="o", color=col, label=g)
ax.set_xlabel("Child's birth year"); ax.set_ylabel("Mean mental health score (1 excellent - 5 poor)"); ax.set_title("Raw means: mothers of 0-5 year olds, by child's birth year (weighted)", fontsize=10.5, loc="left")
ax.legend(frameon=False, fontsize=9); style_axes(ax); fig.tight_layout(); fig.savefig(FIG / "nsch_raw_score.png", dpi=200)
print("wrote figures")
