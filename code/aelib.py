"""
aelib.py -- small, dependency-light estimators used by 03_analysis.py.

All estimators accept optional sampling weights and report heteroskedasticity-
robust (HC1-type) standard errors.  They are written with numpy so that every
number in the paper can be traced to a few lines of linear algebra; pyfixest is
used only as a cross-check in tests.
"""
import numpy as np
import pandas as pd

PALETTE = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]  # validated categorical order
INK = "#0b0b0b"
INK2 = "#52514e"
GRID = "#e4e3df"


def _design(df, cols, const=True):
    X = df[cols].to_numpy(dtype=float) if cols else np.empty((len(df), 0))
    if const:
        X = np.column_stack([np.ones(len(df)), X])
    return X


def wls(y, X, w=None):
    """Weighted least squares with HC1 robust variance. Returns (beta, V)."""
    n, k = X.shape
    w = np.ones(n) if w is None else np.asarray(w, dtype=float)
    Xw = X * w[:, None]
    XtWX = X.T @ Xw
    XtWX_inv = np.linalg.pinv(XtWX)
    beta = XtWX_inv @ (Xw.T @ y)
    e = y - X @ beta
    meat = (Xw * e[:, None]).T @ (Xw * e[:, None])
    V = XtWX_inv @ meat @ XtWX_inv * n / (n - k)
    return beta, V, e


def tsls(y, D, Z, X, w=None):
    """
    2SLS of y on endogenous D (n x 1) and exogenous X (n x k incl. const) with
    instruments Z (n x m).  Robust variance.  Also returns first-stage stats and
    the Sargan-Hansen overidentification statistic (robust score version is not
    needed for the paper; we report the classical Sargan n*R^2 as a diagnostic).
    """
    n = len(y)
    w = np.ones(n) if w is None else np.asarray(w, dtype=float)
    Zf = np.column_stack([Z, X])
    Xf = np.column_stack([D, X])
    # first stage
    pi, Vpi, _ = wls(D, Zf, w)
    Dhat = Zf @ pi
    m = Z.shape[1]
    # robust F on excluded instruments
    R = np.zeros((m, Zf.shape[1])); R[np.arange(m), np.arange(m)] = 1
    fs_F = float((R @ pi).T @ np.linalg.pinv(R @ Vpi @ R.T) @ (R @ pi) / m)
    # second stage using fitted D
    Xhat = np.column_stack([Dhat, X])
    beta, _, _ = wls(y, Xhat, w)
    e = y - Xf @ beta  # structural residual
    Xhw = Xhat * w[:, None]
    A_inv = np.linalg.pinv(Xhat.T @ Xhw)
    meat = (Xhw * e[:, None]).T @ (Xhw * e[:, None])
    V = A_inv @ meat @ A_inv * n / (n - Xf.shape[1])
    # Sargan: regress e on Zf
    sargan = np.nan
    if m > 1:
        g, _, ee = wls(e, Zf, w)
        ybar = np.average(e, weights=w)
        r2 = 1 - np.sum(w * ee ** 2) / np.sum(w * (e - ybar) ** 2)
        sargan = n * r2
    return dict(beta=beta[0], se=float(np.sqrt(V[0, 0])), fs_coef=pi[:m], fs_se=np.sqrt(np.diag(Vpi)[:m]),
                fs_F=fs_F, sargan=sargan, sargan_df=m - 1, n=n, beta_all=beta, V=V)


def ols_coef(df, y, x, controls, w=None):
    X = _design(df, [x] + controls)
    b, V, _ = wls(df[y].to_numpy(float), X, None if w is None else df[w].to_numpy(float))
    return dict(beta=b[1], se=float(np.sqrt(V[1, 1])), n=len(df))


def iv_coef(df, y, d, z, controls, w=None):
    z = [z] if isinstance(z, str) else list(z)
    X = _design(df, controls)
    Z = df[z].to_numpy(float)
    ww = None if w is None else df[w].to_numpy(float)
    return tsls(df[y].to_numpy(float), df[d].to_numpy(float), Z, X, ww)


def wmean(x, w=None):
    x = np.asarray(x, float)
    return float(np.average(x, weights=None if w is None else np.asarray(w, float)))


def wald_diff(b1, se1, b2, se2):
    """Two-sided p-value for b1 = b2 assuming independence (conservative when
    the two estimates share a control group)."""
    from scipy.stats import norm
    z = (b1 - b2) / np.sqrt(se1 ** 2 + se2 ** 2)
    return float(2 * (1 - norm.cdf(abs(z))))


def stars(b, se):
    from scipy.stats import norm
    p = 2 * (1 - norm.cdf(abs(b / se))) if se > 0 else 1
    return "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.10 else ""


def fmt(b, se, d=3):
    return f"{b:.{d}f}{stars(b, se)} ({se:.{d}f})"


def to_markdown(df, floatfmt=".3f", index=True):
    """Minimal GitHub-flavoured markdown table writer (no tabulate dependency)."""
    d = df.copy()
    if index:
        d = d.reset_index()
    cols = [str(c) for c in d.columns]
    rows = []
    for _, r in d.iterrows():
        cells = []
        for v in r:
            if isinstance(v, (float, np.floating)):
                cells.append("" if np.isnan(v) else format(v, floatfmt))
            else:
                cells.append(str(v))
        rows.append(cells)
    out = ["| " + " | ".join(cols) + " |", "|" + "|".join(["---"] * len(cols)) + "|"]
    out += ["| " + " | ".join(r) + " |" for r in rows]
    return "\n".join(out)


def style_axes(ax):
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(GRID)
    ax.tick_params(colors=INK2, labelsize=9)
    ax.yaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.xaxis.label.set_color(INK2); ax.yaxis.label.set_color(INK2)
    ax.title.set_color(INK)
