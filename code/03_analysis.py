"""
03_analysis.py -- preliminary results.

Design: Angrist & Evans (1998) sibling-sex-composition instrument for having a
third child, applied to (i) the 1980 Census married-mother sample (n=254,654),
(ii) its Black/Hispanic subsample with richer covariates (n=31,857), and
(iii) an identically constructed sample of mothers from the 2021-2023 CPS ASEC.

Outputs (output/tables/*.csv + *.md, output/figures/*.png):
  T1  descriptive statistics by sample
  T2  first stage: morekids on samesex / twoboys+twogirls
  T3  OLS vs 2SLS for labour-supply outcomes
  T4  heterogeneity of the LATE (race, age, education, other income)
  T5  two-boys vs two-girls LATEs and overidentification test
  T6  complier characterisation (Abadie 2003)
  T7  Kitagawa (2015) / Huber-Mellace (2015) instrument-validity inequalities
  T8  1980 vs 2021-23 comparison with pooled interaction test
  F2  distributional LATE on weeks worked (1980)
  F3  heterogeneity coefficient plot
  F4  1980 vs 2020s first stage / reduced form / LATE
"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import chi2, norm

from aelib import (PALETTE, INK, INK2, GRID, wls, tsls, ols_coef, iv_coef, wmean, wald_diff,
                   fmt, to_markdown, style_axes, _design)

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "data" / "clean"
TAB = ROOT / "output" / "tables"
FIG = ROOT / "output" / "figures"
TAB.mkdir(parents=True, exist_ok=True); FIG.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(1980)

full = pd.read_csv(CLEAN / "ae1980_full.csv.gz")
bh = pd.read_csv(CLEAN / "ae1980_bh.csv.gz")
cps = pd.read_csv(CLEAN / "cps_pe_mothers.csv.gz")
cps_m = cps[cps["married"] == 1].copy()

for d in (full, bh, cps, cps_m):
    d["agesq"] = d["age"] ** 2
    d["white"] = ((d["black"] == 0) & (d["hispanic"] == 0) & (d["other"] == 0)).astype(int)

# AE98 covariate set: age, age at first birth (where available), boy1st, race
CTRL_FULL = ["age", "agesq", "boy1st", "black", "hispanic", "other"]
CTRL_BH = ["age", "agesq", "agefst", "boy1st", "black"]           # hispanic = 1-black in bh
CTRL_CPS = ["age", "agesq", "agefst", "boy1st", "black", "hispanic", "other"]

SAMPLES = {
    "1980 Census, married mothers": (full, CTRL_FULL, None),
    "1980 Census, Black/Hispanic mothers": (bh, CTRL_BH, None),
    "CPS ASEC 2021-23, all mothers": (cps, CTRL_CPS, "weight"),
    "CPS ASEC 2021-23, married mothers": (cps_m, CTRL_CPS, "weight"),
}

def save(df, name, floatfmt=".3f", index=True):
    df.to_csv(TAB / f"{name}.csv")
    (TAB / f"{name}.md").write_text(to_markdown(df, floatfmt, index) + "\n")
    print(f"\n### {name}\n" + to_markdown(df, floatfmt, index))

# ---------------------------------------------------------------- T1 descriptives
rows = {}
for name, (d, ctrl, w) in SAMPLES.items():
    ww = None if w is None else d[w]
    r = {"N": len(d)}
    for v in ["morekids", "kids", "samesex", "twoboys", "twogirls", "boy1st", "worked", "weeks", "hours",
              "labinc", "age", "agefst", "educ", "black", "hispanic", "other", "married"]:
        if v in d and d[v].notna().any():
            r[v] = wmean(d[v][d[v].notna()], None if ww is None else ww[d[v].notna()])
    rows[name] = r
T1 = pd.DataFrame(rows)
save(T1, "T1_descriptives")

# ---------------------------------------------------------------- T2 first stage
rows = []
for name, (d, ctrl, w) in SAMPLES.items():
    ww = None if w is None else d[w].to_numpy(float)
    y = d["morekids"].to_numpy(float)
    # (a) samesex, no controls
    b, V, _ = wls(y, _design(d, ["samesex"]), ww)
    r = {"sample": name, "N": len(d), "samesex (no controls)": fmt(b[1], np.sqrt(V[1, 1]))}
    # (b) samesex with controls
    b, V, _ = wls(y, _design(d, ["samesex"] + ctrl), ww)
    r["samesex (controls)"] = fmt(b[1], np.sqrt(V[1, 1]))
    r["F (robust)"] = round(float(b[1] ** 2 / V[1, 1]), 1)
    # (c) twoboys, twogirls with controls incl boy1st
    b, V, _ = wls(y, _design(d, ["twoboys", "twogirls"] + ctrl), ww)
    r["two boys"] = fmt(b[1], np.sqrt(V[1, 1])); r["two girls"] = fmt(b[2], np.sqrt(V[2, 2]))
    r["p: boys=girls"] = round(wald_diff(b[1], np.sqrt(V[1, 1]), b[2], np.sqrt(V[2, 2])), 3)
    rows.append(r)
T2 = pd.DataFrame(rows).set_index("sample")
save(T2, "T2_first_stage")

# ---------------------------------------------------------------- T3 OLS vs 2SLS
OUTCOMES = {"worked": "Worked for pay", "weeks": "Weeks worked", "hours": "Hours per week",
            "labinc": "Labour income ($1000s)", "kids": "Number of children"}
rows = []
for name, (d, ctrl, w) in SAMPLES.items():
    for v, lab in OUTCOMES.items():
        if v not in d or d[v].isna().all():
            continue
        dd = d[d[v].notna()]
        o = ols_coef(dd, v, "morekids", ctrl, w)
        iv = iv_coef(dd, v, "morekids", "samesex", ctrl, w)
        iv2 = iv_coef(dd, v, "morekids", ["twoboys", "twogirls"], ctrl, w)
        rows.append({"sample": name, "outcome": lab, "mean": round(wmean(dd[v], None if w is None else dd[w]), 3),
                     "OLS": fmt(o["beta"], o["se"]), "2SLS samesex": fmt(iv["beta"], iv["se"]),
                     "2SLS twoboys+twogirls": fmt(iv2["beta"], iv2["se"]),
                     "Sargan p": round(1 - chi2.cdf(iv2["sargan"], 1), 3), "N": len(dd)})
T3 = pd.DataFrame(rows).set_index(["sample", "outcome"])
save(T3, "T3_ols_vs_2sls")

# ---------------------------------------------------------------- T4 heterogeneity (1980)
def het(d, ctrl, groups, y, w=None, drop_ctrl=()):
    out = []
    for gname, mask in groups.items():
        dd = d[mask]
        c = [x for x in ctrl if x not in drop_ctrl and dd[x].nunique() > 1]
        iv = iv_coef(dd, y, "morekids", "samesex", c, w)
        fs = iv["fs_coef"][0]
        rf = fs * iv["beta"]
        out.append({"group": gname, "N": len(dd), "mean(y)": round(wmean(dd[y], None if w is None else dd[w]), 3),
                    "first stage": f"{fs:.3f} ({iv['fs_se'][0]:.3f})",
                    "reduced form": round(rf, 4), "LATE": iv["beta"], "se": iv["se"], "LATE (se)": fmt(iv["beta"], iv["se"])})
    return pd.DataFrame(out).set_index("group")

groups_full = {
    "All": full.index == full.index,
    "White (non-Hispanic)": full["white"] == 1, "Black": full["black"] == 1,
    "Hispanic": full["hispanic"] == 1, "Other race": full["other"] == 1,
    "Age 21-27": full["age"] <= 27, "Age 28-31": full["age"].between(28, 31), "Age 32-35": full["age"] >= 32,
}
H_full_worked = het(full, CTRL_FULL, groups_full, "worked")
H_full_weeks = het(full, CTRL_FULL, groups_full, "weeks")
groups_bh = {
    "All Black/Hispanic": bh.index == bh.index,
    "Education < 12": bh["educ"] < 12, "Education = 12": bh["educ"] == 12, "Education > 12": bh["educ"] > 12,
    "First birth at <= 19": bh["agefst"] <= 19, "First birth at 20-22": bh["agefst"].between(20, 22),
    "First birth at >= 23": bh["agefst"] >= 23,
    "Other income: bottom tercile": bh["nonmomi"] <= bh["nonmomi"].quantile(1/3),
    "Other income: middle tercile": bh["nonmomi"].between(bh["nonmomi"].quantile(1/3), bh["nonmomi"].quantile(2/3)),
    "Other income: top tercile": bh["nonmomi"] > bh["nonmomi"].quantile(2/3),
}
H_bh_worked = het(bh, CTRL_BH, groups_bh, "worked")
H_bh_hours = het(bh, CTRL_BH, groups_bh, "hours")
T4 = pd.concat({"1980 married: worked": H_full_worked, "1980 married: weeks": H_full_weeks,
                "1980 B/H: worked": H_bh_worked, "1980 B/H: hours": H_bh_hours}, names=["panel", "group"])
save(T4.drop(columns=["LATE", "se"]), "T4_heterogeneity")

# F3 heterogeneity coefficient plot (worked, 1980 married)
fig, ax = plt.subplots(figsize=(7.2, 4.2))
h = H_full_worked.iloc[::-1]
ax.errorbar(h["LATE"], np.arange(len(h)), xerr=1.96 * h["se"], fmt="o", color=PALETTE[0],
            ecolor=PALETTE[0], elinewidth=2, capsize=0, markersize=7)
ax.axvline(0, color=INK2, linewidth=1)
ax.set_yticks(np.arange(len(h))); ax.set_yticklabels(h.index)
ax.set_xlabel("2SLS effect of a third child on P(worked for pay), 95% CI")
ax.set_title("Effect of a third child on mothers' employment by subgroup, 1980", fontsize=11, loc="left")
style_axes(ax); ax.xaxis.grid(True, color=GRID); ax.yaxis.grid(False)
fig.tight_layout(); fig.savefig(FIG / "F3_heterogeneity_1980.png", dpi=200); plt.close(fig)

# ---------------------------------------------------------------- T5 two boys vs two girls (1980 married)
rows = []
for name, (d, ctrl, w) in SAMPLES.items():
    for y in ["worked", "weeks", "hours"]:
        if y not in d or d[y].isna().all():
            continue
        dd = d[d[y].notna()]
        # LATEs using each instrument separately, mixed-sex families as the base
        base_b = dd[(dd["twogirls"] == 0)]  # two boys vs mixed
        base_g = dd[(dd["twoboys"] == 0)]   # two girls vs mixed
        ivb = iv_coef(base_b, y, "morekids", "twoboys", ctrl, w)
        ivg = iv_coef(base_g, y, "morekids", "twogirls", ctrl, w)
        ivo = iv_coef(dd, y, "morekids", ["twoboys", "twogirls"], ctrl, w)
        rows.append({"sample": name, "outcome": y,
                     "FS two boys": f"{ivb['fs_coef'][0]:.3f}", "FS two girls": f"{ivg['fs_coef'][0]:.3f}",
                     "LATE two boys": fmt(ivb["beta"], ivb["se"]), "LATE two girls": fmt(ivg["beta"], ivg["se"]),
                     "LATE overid": fmt(ivo["beta"], ivo["se"]),
                     "Sargan stat": round(ivo["sargan"], 2), "Sargan p": round(1 - chi2.cdf(ivo["sargan"], 1), 3)})
T5 = pd.DataFrame(rows).set_index(["sample", "outcome"])
save(T5, "T5_twoboys_twogirls")

# ---------------------------------------------------------------- T6 complier characterisation (1980 married)
def complier_profile(d, covs, w=None):
    ww = None if w is None else d[w].to_numpy(float)
    fs_all = wmean(d.loc[d.samesex == 1, "morekids"], None if w is None else d.loc[d.samesex == 1, w]) - \
             wmean(d.loc[d.samesex == 0, "morekids"], None if w is None else d.loc[d.samesex == 0, w])
    out = []
    for c, lab in covs.items():
        m = d[c] == 1
        fs_c = wmean(d.loc[m & (d.samesex == 1), "morekids"], None if w is None else d.loc[m & (d.samesex == 1), w]) - \
               wmean(d.loc[m & (d.samesex == 0), "morekids"], None if w is None else d.loc[m & (d.samesex == 0), w])
        p = wmean(m, ww)
        out.append({"characteristic": lab, "P(X=1)": p, "P(X=1 | complier)": p * fs_c / fs_all,
                    "relative likelihood": fs_c / fs_all})
    return pd.DataFrame(out).set_index("characteristic")

covs_full = {"white": "White (non-Hispanic)", "black": "Black", "hispanic": "Hispanic", "other": "Other race",
             "boy1st": "First child a boy"}
full["young"] = (full["age"] <= 27).astype(int); full["old"] = (full["age"] >= 32).astype(int)
covs_full.update({"young": "Age 21-27", "old": "Age 32-35"})
T6a = complier_profile(full, covs_full)
bh["lowed"] = (bh["educ"] < 12).astype(int); bh["hied"] = (bh["educ"] > 12).astype(int)
bh["teenmom"] = (bh["agefst"] <= 19).astype(int)
bh["lowinc"] = (bh["nonmomi"] <= bh["nonmomi"].quantile(1/3)).astype(int)
T6b = complier_profile(bh, {"black": "Black", "lowed": "Education < 12", "hied": "Education > 12",
                            "teenmom": "First birth at <= 19", "lowinc": "Other income: bottom tercile"})
T6 = pd.concat({"1980 married": T6a, "1980 Black/Hispanic": T6b}, names=["panel", "characteristic"])
save(T6, "T6_compliers")

# ---------------------------------------------------------------- T7 IV validity inequalities (Kitagawa 2015)
def kitagawa(d, y, bins, w=None, B=300):
    """Kitagawa (2015) testable implication of LATE assumptions for binary Z, D:
    P(Y in B, D=1 | Z=1) >= P(Y in B, D=1 | Z=0) and P(Y in B, D=0 | Z=0) >= P(Y in B, D=0 | Z=1)
    for every set B.  We report the minimum over the bins of each difference and
    a bootstrap p-value for min < 0 (one-sided, with the least-favourable null
    of zero difference imposed by recentring)."""
    ww = np.ones(len(d)) if w is None else d[w].to_numpy(float)
    Y = d[y].to_numpy(float); D = d["morekids"].to_numpy(int); Z = d["samesex"].to_numpy(int)
    edges = np.array(bins, float)
    cat = np.digitize(Y, edges[1:-1], right=True)

    def diffs(idx):
        y_, d_, z_, w_ = cat[idx], D[idx], Z[idx], ww[idx]
        res = []
        for dv, sign in ((1, 1), (0, -1)):
            for b in range(len(edges) - 1):
                p1 = np.sum(w_ * ((y_ == b) & (d_ == dv) & (z_ == 1))) / np.sum(w_ * (z_ == 1))
                p0 = np.sum(w_ * ((y_ == b) & (d_ == dv) & (z_ == 0))) / np.sum(w_ * (z_ == 0))
                res.append(sign * (p1 - p0))
        return np.array(res)

    idx = np.arange(len(d))
    est = diffs(idx)
    boots = np.array([diffs(rng.integers(0, len(d), len(d))) for _ in range(B)])
    se = boots.std(axis=0)
    tstat = est / se
    # p-value for H0: all differences >= 0 via min t, bootstrap recentred at zero
    tb = ((boots - est) / se).min(axis=1)
    p = float(np.mean(tb <= tstat.min()))
    labels = [f"D={dv}, {lo:g}-{hi:g}" for dv in (1, 0) for lo, hi in zip(edges[:-1], edges[1:])]
    tab = pd.DataFrame({"difference": est, "boot se": se, "t": tstat}, index=labels)
    return tab, p

T7_tab, T7_p = kitagawa(full, "weeks", [0, 0.5, 13, 26, 39, 47, 52.5])
T7_tab.attrs["p_min"] = T7_p
save(T7_tab, "T7_kitagawa_1980_weeks", ".4f")
(TAB / "T7_kitagawa_1980_weeks.md").open("a").write(f"\nBootstrap p-value (H0: all inequalities hold, min-t statistic): {T7_p:.3f}\n")
print(f"Kitagawa min-t bootstrap p-value: {T7_p:.3f}")

# ---------------------------------------------------------------- F2 distributional LATE on weeks (1980)
ks = np.arange(1, 53)
late_k, se_k = [], []
for k in ks:
    full["_yk"] = (full["weeks"] >= k).astype(float)
    r = iv_coef(full, "_yk", "morekids", "samesex", CTRL_FULL)
    late_k.append(r["beta"]); se_k.append(r["se"])
late_k, se_k = np.array(late_k), np.array(se_k)
pd.DataFrame({"k": ks, "LATE_P(weeks>=k)": late_k, "se": se_k}).to_csv(TAB / "F2_distributional_late.csv", index=False)
fig, ax = plt.subplots(figsize=(7.2, 4.0))
ax.fill_between(ks, late_k - 1.96 * se_k, late_k + 1.96 * se_k, color=PALETTE[0], alpha=0.18, linewidth=0)
ax.plot(ks, late_k, color=PALETTE[0], linewidth=2)
ax.axhline(0, color=INK2, linewidth=1)
ax.set_xlabel("k (weeks worked in 1979)"); ax.set_ylabel("2SLS effect of a third child on P(weeks ≥ k)")
ax.set_title("Where in the weeks distribution does a third child bite? 1980 Census", fontsize=11, loc="left")
ax.set_xlim(1, 52); style_axes(ax)
fig.tight_layout(); fig.savefig(FIG / "F2_distributional_late_1980.png", dpi=200); plt.close(fig)

# ---------------------------------------------------------------- T8 / F4 1980 vs 2020s
def pooled_interaction(d80, dcps, y, ctrl80, ctrlcps):
    """Stack the two samples; instrument morekids and morekids x post with
    samesex and samesex x post; report LATE_1980, LATE_2020s and the difference."""
    a = d80[[y, "morekids", "samesex", "boy1st", "age", "agesq", "black", "hispanic", "other"]].copy(); a["post"] = 0; a["w"] = 1.0
    b = dcps[[y, "morekids", "samesex", "boy1st", "age", "agesq", "black", "hispanic", "other", "weight"]].copy(); b["post"] = 1
    b["w"] = b["weight"] * len(b) / b["weight"].sum()  # normalise CPS weights to mean 1
    s = pd.concat([a.drop(columns=[]), b.drop(columns=["weight"])], ignore_index=True)
    ctrl = ["boy1st", "age", "agesq", "black", "hispanic", "other"]
    for c in ctrl:
        s[c + "_post"] = s[c] * s["post"]
    s["mk_post"] = s["morekids"] * s["post"]; s["ss_post"] = s["samesex"] * s["post"]
    X = _design(s, ctrl + [c + "_post" for c in ctrl] + ["post"])
    Z = s[["samesex", "ss_post"]].to_numpy(float)
    D = s[["morekids", "mk_post"]].to_numpy(float)
    yv = s[y].to_numpy(float); w = s["w"].to_numpy(float)
    # 2SLS with two endogenous regressors
    Zf = np.column_stack([Z, X]); Xf = np.column_stack([D, X])
    Dhat = np.column_stack([wls(D[:, j], Zf, w)[0] @ Zf.T for j in range(2)])
    Xhat = np.column_stack([Dhat, X])
    beta, _, _ = wls(yv, Xhat, w)
    e = yv - Xf @ beta
    Xhw = Xhat * w[:, None]; A_inv = np.linalg.pinv(Xhat.T @ Xhw)
    V = A_inv @ ((Xhw * e[:, None]).T @ (Xhw * e[:, None])) @ A_inv
    return dict(late80=beta[0], se80=np.sqrt(V[0, 0]), diff=beta[1], sediff=np.sqrt(V[1, 1]),
                late20=beta[0] + beta[1], se20=np.sqrt(V[0, 0] + V[1, 1] + 2 * V[0, 1]))

rows = []
comp = {"worked": ("1980 Census, married mothers", full, "CPS ASEC 2021-23, married mothers", cps_m),
        "worked (all mothers, CPS)": ("1980 Census, married mothers", full, "CPS ASEC 2021-23, all mothers", cps)}
for lab, (n80, d80, n20, d20) in comp.items():
    r = pooled_interaction(d80, d20, "worked", CTRL_FULL, CTRL_CPS)
    fs80 = iv_coef(d80, "worked", "morekids", "samesex", CTRL_FULL)
    fs20 = iv_coef(d20, "worked", "morekids", "samesex", CTRL_CPS, "weight")
    rows.append({"comparison": f"{n80} vs {n20}", "outcome": "worked",
                 "FS 1980": fmt(fs80["fs_coef"][0], fs80["fs_se"][0]), "FS 2020s": fmt(fs20["fs_coef"][0], fs20["fs_se"][0]),
                 "RF 1980": round(fs80["fs_coef"][0] * fs80["beta"], 4), "RF 2020s": round(fs20["fs_coef"][0] * fs20["beta"], 4),
                 "LATE 1980": fmt(r["late80"], r["se80"]), "LATE 2020s": fmt(r["late20"], r["se20"]),
                 "difference": fmt(r["diff"], r["sediff"]), "N 2020s": len(d20)})
# hours: Black/Hispanic 1980 vs CPS Black/Hispanic
bh_cps = cps[(cps["black"] == 1) | (cps["hispanic"] == 1)].copy()
ivh80 = iv_coef(bh, "hours", "morekids", "samesex", CTRL_BH)
ivh20 = iv_coef(bh_cps, "hours", "morekids", "samesex", CTRL_CPS, "weight")
rows.append({"comparison": "1980 Black/Hispanic mothers vs CPS 2021-23 Black/Hispanic mothers", "outcome": "hours",
             "FS 1980": fmt(ivh80["fs_coef"][0], ivh80["fs_se"][0]), "FS 2020s": fmt(ivh20["fs_coef"][0], ivh20["fs_se"][0]),
             "RF 1980": round(ivh80["fs_coef"][0] * ivh80["beta"], 3), "RF 2020s": round(ivh20["fs_coef"][0] * ivh20["beta"], 3),
             "LATE 1980": fmt(ivh80["beta"], ivh80["se"]), "LATE 2020s": fmt(ivh20["beta"], ivh20["se"]),
             "difference": fmt(ivh20["beta"] - ivh80["beta"], np.sqrt(ivh20["se"] ** 2 + ivh80["se"] ** 2)), "N 2020s": len(bh_cps)})
T8 = pd.DataFrame(rows).set_index(["comparison", "outcome"])
save(T8, "T8_1980_vs_2020s")

# minimum detectable effect for the CPS sample (80% power, 5% size)
mde = 2.8 * fs20["se"]
(TAB / "T8_1980_vs_2020s.md").open("a").write(
    f"\nMinimum detectable LATE on P(worked) in the CPS 2021-23 all-mothers sample (80% power, two-sided 5%): {mde:.3f}\n")
print(f"MDE (worked, CPS all mothers): {mde:.3f}")

# F4: first stage / reduced form / LATE by period
fig, axes = plt.subplots(1, 3, figsize=(9.6, 3.6))
items = [("First stage: P(more than 2 kids)", fs80["fs_coef"][0], fs80["fs_se"][0], fs20["fs_coef"][0], fs20["fs_se"][0]),
         ("Reduced form: P(worked)", fs80["fs_coef"][0] * fs80["beta"], None, fs20["fs_coef"][0] * fs20["beta"], None),
         ("2SLS: effect of 3rd child on P(worked)", fs80["beta"], fs80["se"], fs20["beta"], fs20["se"])]
# reduced-form SEs from direct regression
rf80 = ols_coef(full, "worked", "samesex", CTRL_FULL); rf20 = ols_coef(cps, "worked", "samesex", CTRL_CPS, "weight")
items[1] = (items[1][0], rf80["beta"], rf80["se"], rf20["beta"], rf20["se"])
for ax, (title, b80, s80, b20, s20) in zip(axes, items):
    ax.bar([0, 1], [b80, b20], color=[PALETTE[0], PALETTE[1]], width=0.55, yerr=[1.96 * s80, 1.96 * s20],
           error_kw=dict(ecolor=INK2, elinewidth=1.5, capsize=0))
    ax.axhline(0, color=INK2, linewidth=1)
    ax.set_xticks([0, 1]); ax.set_xticklabels(["1980 Census\n(married)", "CPS 2021-23\n(all mothers)"])
    ax.set_title(title, fontsize=9.5, loc="left"); style_axes(ax)
    for x, b, se_ in [(0, b80, s80), (1, b20, s20)]:
        ax.annotate(f"{b:.3f}\n({se_:.3f})", (x + 0.3, b), ha="left", va="center", fontsize=8, color=INK2)
fig.suptitle("Same-sex instrument, 1980 vs 2021-23 (95% CIs)", x=0.01, ha="left", fontsize=11, color=INK)
fig.tight_layout(); fig.savefig(FIG / "F4_1980_vs_2020s.png", dpi=200); plt.close(fig)

# ---------------------------------------------------------------- cross-check vs pyfixest
try:
    import pyfixest as pf
    m = pf.feols("worked ~ age + agesq + boy1st + black + hispanic + other | morekids ~ samesex", data=full, vcov="hetero")
    mine = iv_coef(full, "worked", "morekids", "samesex", CTRL_FULL)
    print(f"\ncross-check pyfixest 2SLS worked: {m.coef()['morekids']:.5f} (se {m.se()['morekids']:.5f}) "
          f"vs aelib {mine['beta']:.5f} (se {mine['se']:.5f})")
except Exception as ex:  # pragma: no cover
    print("pyfixest cross-check skipped:", ex)
print("\ndone.")
