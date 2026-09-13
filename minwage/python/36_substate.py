"""36_substate.py -- city and county minimum wages: county-month panel, control contamination flags, local events.

Input: data/raw/minwage/substate_mw_changes.csv (Vaghul-Zipperer substate list, through 2022) and the state panel.
Localities are mapped to CPS county codes (state FIPS x 1000 + county FIPS); a city rate is applied to its whole
county, which overstates coverage for cities that are a fraction of the county (Seattle in King, Portland ME in
Cumberland).  Oregon's nonurban counties have a rate below the state standard.
Outputs: data/raw/minwage/county_mw_monthly.csv (county, ym, mw_local, mw_state, mw_county),
         data/raw/minwage/state_local_flags.csv (state_fips, ym, local_above: any locality above the state rate),
         data/raw/minwage/local_events.csv (county-level events, same rule as state events).
"""
from pathlib import Path
import numpy as np, pandas as pd
PF = Path(__file__).resolve().parents[1]; MW = PF / "data" / "raw" / "minwage"
PRE, POST, MIN_PCT = 36, 48, 0.05
COUNTY = {  # locality -> CPS county codes
    ("Arizona", "Flagstaff"): [4005],
    ("California", "Alameda"): [6001], ("California", "Berkeley"): [6001], ("California", "Emeryville"): [6001], ("California", "Fremont"): [6001], ("California", "Hayward"): [6001], ("California", "Oakland"): [6001], ("California", "San Leandro"): [6001],
    ("California", "Belmont"): [6081], ("California", "East Palo Alto"): [6081], ("California", "Redwood City"): [6081], ("California", "San Mateo"): [6081],
    ("California", "Cupertino"): [6085], ("California", "Los Altos"): [6085], ("California", "Milpitas"): [6085], ("California", "Mountain View"): [6085], ("California", "Palo Alto"): [6085], ("California", "San Jose"): [6085], ("California", "Santa Clara"): [6085], ("California", "Sunnyvale"): [6085],
    ("California", "El Cerrito"): [6013], ("California", "Richmond"): [6013],
    ("California", "Los Angeles"): [6037], ("California", "Los Angeles County"): [6037], ("California", "Malibu"): [6037], ("California", "Pasadena"): [6037], ("California", "Santa Monica"): [6037],
    ("California", "Novato"): [6041], ("California", "Petaluma"): [6097], ("California", "Santa Rosa"): [6097], ("California", "Sonoma"): [6097], ("California", "San Diego"): [6073], ("California", "San Francisco"): [6075],
    ("Colorado", "Denver"): [8031], ("Illinois", "Chicago"): [17031], ("Illinois", "Cook County"): [17031],
    ("Iowa", "Johnson County"): [19103], ("Iowa", "Linn County"): [19113], ("Iowa", "Wapello County"): [19179],
    ("Kentucky", "Lexington"): [21067], ("Kentucky", "Louisville"): [21111], ("Maine", "Portland"): [23005],
    ("Maryland", "Montgomery County"): [24031], ("Maryland", "Prince George's County"): [24033],
    ("Minnesota", "Minneapolis"): [27053], ("Minnesota", "St. Paul"): [27123],
    ("New Mexico", "Albuquerque"): [35001], ("New Mexico", "Bernalillo County"): [35001], ("New Mexico", "Las Cruces"): [35013], ("New Mexico", "Santa Fe"): [35049], ("New Mexico", "Santa Fe County"): [35049],
    ("New York", "New York City"): [36005, 36047, 36061, 36081, 36085], ("New York", "Long Island & Westchester"): [36059, 36103, 36119],
    ("Oregon", "Portland"): [41051, 41067, 41005],
    ("Oregon", "Nonurban counties"): [41001, 41011, 41013, 41015, 41019, 41021, 41023, 41025, 41031, 41035, 41037, 41045, 41049, 41055, 41059, 41061, 41063, 41069],
    ("Washington", "SeaTac"): [53033], ("Washington", "Seattle"): [53033], ("Washington", "Tacoma"): [53053],
}
SKIP = {("District of Columbia", "Washington"), ("New York", "Remainder of New York State"), ("Oregon", "Remainder of Oregon")}   # equal to the state series

sub = pd.read_csv(MW / "substate_mw_changes.csv", parse_dates=["date"])
sub = sub[~sub.apply(lambda r: (r.state, r.locality) in SKIP, axis=1)]
unmapped = sorted({(r.state, r.locality) for r in sub.itertuples() if (r.state, r.locality) not in COUNTY}); assert not unmapped, unmapped
P = pd.read_csv(MW / "state_mw_monthly.csv"); months = sorted(P.ym.unique())
S = P.set_index(["state_fips", "ym"]).mw
rows = []
for (state, loc), g in sub.groupby(["state", "locality"]):
    g = g.sort_values("date"); sf = int(g.state_fips.iloc[0])
    for cty in COUNTY[(state, loc)]:
        for ym in months:
            dt = pd.Period(ym, "M").to_timestamp(how="start")
            local = g[g.date <= dt].mw.iloc[-1] if (g.date <= dt).any() else np.nan
            if np.isnan(local): continue
            rows.append((cty, sf, ym, loc, local))
L = pd.DataFrame(rows, columns=["county", "state_fips", "ym", "locality", "mw_local"])
# one locality represents each county: the county-wide rate where one exists, otherwise the largest city
PRIMARY = {4005: "Flagstaff", 6001: "Oakland", 6081: "San Mateo", 6085: "San Jose", 6013: "Richmond", 6037: "Los Angeles County", 6041: "Novato", 6097: "Santa Rosa",
           6073: "San Diego", 6075: "San Francisco", 8031: "Denver", 17031: "Chicago", 19103: "Johnson County", 19113: "Linn County", 19179: "Wapello County",
           21067: "Lexington", 21111: "Louisville", 23005: "Portland", 24031: "Montgomery County", 24033: "Prince George's County", 27053: "Minneapolis", 27123: "St. Paul",
           35001: "Albuquerque", 35013: "Las Cruces", 35049: "Santa Fe", 53033: "Seattle", 53053: "Tacoma"}
nonurban = L.locality == "Nonurban counties"
L = L[nonurban | L.locality.isin(["New York City", "Long Island & Westchester", "Portland"]) | (L.locality == L.county.map(PRIMARY))]
C = L[~nonurban].groupby(["county", "state_fips", "ym"]).mw_local.max().reset_index()
C = pd.concat([C, L[nonurban][["county", "state_fips", "ym", "mw_local"]]], ignore_index=True)
C["mw_state"] = [S.get((s, y), np.nan) for s, y in zip(C.state_fips, C.ym)]
C["mw_county"] = np.where(C.county.isin(COUNTY[("Oregon", "Nonurban counties")]), C.mw_local, np.maximum(C.mw_local, C.mw_state))
C["local_above"] = (C.mw_county > C.mw_state + 0.01).astype(int)
C.to_csv(MW / "county_mw_monthly.csv", index=False)
F = C.groupby(["state_fips", "ym"]).local_above.max().reset_index(); F = F[F.local_above == 1]
F.to_csv(MW / "state_local_flags.csv", index=False)
print("county-months with a local rate above the state rate:", int(C.local_above.sum()), "; state-months flagged:", len(F))
print(F.groupby("state_fips").ym.agg(["min", "max", "size"]).to_string())

# local events: county effective minimum rises >= 5% after 36 quiet months, and the rise is local (county rate above state after it)
ev = []
for cty, g in C.sort_values("ym").groupby("county"):
    g = g.set_index("ym").reindex(months); st = pd.Series([S.get((int(cty) // 1000, y), np.nan) for y in months], index=months)
    g["mw_county"] = g.mw_county.fillna(st); g["mw_state"] = st; g["local_above"] = g.local_above.fillna(0)
    pct = g.mw_county / g.mw_county.shift(1) - 1; qual = (pct >= MIN_PCT).astype(int).values; spct = g.mw_state / g.mw_state.shift(1) - 1; squal = (spct >= MIN_PCT).astype(int).values
    i = 0
    while i < len(g):
        if qual[i] == 1 and squal[i] == 0 and g.local_above.iloc[i] == 1 and i >= PRE and qual[i - PRE:i].sum() == 0:
            win = g.iloc[i:i + POST]
            ev.append({"county": int(cty), "state_fips": int(cty) // 1000, "event_ym": g.index[i], "mw_before": g.mw_county.iloc[i - 1], "mw_first": g.mw_county.iloc[i], "mw_end": win.mw_county.iloc[-1],
                       "pct_first": pct.iloc[i], "pct_window": win.mw_county.iloc[-1] / g.mw_county.iloc[i - 1] - 1, "n_steps": int(qual[i:i + POST].sum())})
            i += POST
        else:
            i += 1
E = pd.DataFrame(ev)
SE = pd.read_csv(MW / "mw_events.csv"); idx = {ym: k for k, ym in enumerate(months)}
QS = P.pivot(index="ym", columns="state_fips", values="qual_state")
ctrl = []
for _, e in E.iterrows():
    k = idx[e.event_ym]; lo, hi = max(0, k - PRE), min(len(QS), k + POST)
    ok = QS.iloc[lo:hi].sum(axis=0); ctrl.append(" ".join(str(int(c)) for c in ok.index if ok[c] == 0 and c != e.state_fips))
E["controls"] = ctrl; E["n_controls"] = [len(c.split()) for c in ctrl]; E["event_id"] = range(1001, 1001 + len(E)); E["federal_induced"] = 0
E.to_csv(MW / "local_events.csv", index=False)
print("local events:", len(E)); print(E[["event_id", "county", "event_ym", "mw_before", "mw_first", "mw_end", "pct_window", "n_steps", "n_controls"]].round(2).to_string(index=False))
