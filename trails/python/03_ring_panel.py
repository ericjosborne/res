"""03_ring_panel.py -- LODES jobs around each segment, by distance ring and year (the stacked panel).

Inputs: data/clean/segments.geojson / segments.csv (02_segments.py); data/raw/lodes/ny_wac_S000_JT00_<year>.csv.gz and
ny_xwalk.csv.gz (01_fetch_raw.py).  LODES8 is on 2020 census blocks for every year, so block geography is constant.

For each segment event, every 2020 block whose centroid is within --ctrl_hi miles of the segment is put in a ring:
  treat   distance <= --treat_mi (0.5)
  spill   --treat_mi < distance <= --spill_mi (1.5)   reported, never used as a control
  ctrl    --ctrl_lo (2) < distance <= --ctrl_hi (5)
Blocks within --ctrl_hi of a *different* segment that opens within [g - PRE, g + POST] are dropped from this event's
stack (they are treated, or about to be, by another event); --drop_near_old also drops blocks within --treat_mi of a
segment that opened before g - PRE (already next to a trail).  Jobs (all, retail 44-45, arts/entertainment/recreation
71, accommodation and food services 72) are summed over the blocks in each ring and year; a block missing from a
year's WAC file has no jobs that year.  LODES counts jobs covered by unemployment insurance (no self-employment) and
adds noise to block cells; ring sums average the noise out.

Output: data/clean/ring_panel.csv (event, ring, year, jobs by sector, blocks, blocks with any job).
"""
import argparse
from pathlib import Path
import numpy as np, pandas as pd, geopandas as gpd
PF = Path(__file__).resolve().parents[1]; RAW = PF / "data" / "raw"; CL = PF / "data" / "clean"
CRS, MI = 26918, 1609.344
ap = argparse.ArgumentParser()
ap.add_argument("--treat_mi", type=float, default=0.5); ap.add_argument("--spill_mi", type=float, default=1.5)
ap.add_argument("--ctrl_lo", type=float, default=2.0); ap.add_argument("--ctrl_hi", type=float, default=5.0)
ap.add_argument("--pre", type=int, default=5); ap.add_argument("--post", type=int, default=5); ap.add_argument("--drop_near_old", action="store_true")
a = ap.parse_args()
SECT = {"C000": "jobs_all", "CNS07": "jobs_retail", "CNS17": "jobs_arts_rec", "CNS18": "jobs_accom_food"}

W = []
for f in sorted((RAW / "lodes").glob("ny_wac_S000_JT00_*.csv.gz")):
    w = pd.read_csv(f, usecols=["w_geocode"] + list(SECT), dtype={"w_geocode": str}).rename(columns=SECT)
    W.append(w.assign(year=int(f.stem.split("_")[-1].split(".")[0])))
W = pd.concat(W, ignore_index=True); years = sorted(W.year.unique()); print("LODES years", years[0], "-", years[-1])
X = pd.read_csv(RAW / "lodes" / "ny_xwalk.csv.gz", usecols=["tabblk2020", "blklatdd", "blklondd"], dtype={"tabblk2020": str})
B = gpd.GeoDataFrame(X, geometry=gpd.points_from_xy(X.blklondd, X.blklatdd), crs=4326).to_crs(CRS).reset_index(drop=True)
W = W.merge(B[["tabblk2020"]].reset_index().rename(columns={"index": "bi"}), left_on="w_geocode", right_on="tabblk2020", how="inner")
Wi = W.set_index(["bi", "year"])[list(SECT.values())]

S = gpd.read_file(CL / "segments.geojson").to_crs(CRS)
S["g"] = pd.to_numeric(S.g, errors="coerce"); S = S[S.g.notna() & S.geometry.notna() & ~S.geometry.is_empty].reset_index(drop=True)
rows = []
for i, s in S.iterrows():
    near = B.sindex.query(s.geometry, predicate="dwithin", distance=a.ctrl_hi * MI)
    dist = B.geometry.iloc[near].distance(s.geometry).to_numpy() / MI
    ring = np.select([dist <= a.treat_mi, dist <= a.spill_mi, (dist > a.ctrl_lo) & (dist <= a.ctrl_hi)], ["treat", "spill", "ctrl"], "")
    blk = pd.Series(ring, index=near); blk = blk[blk != ""]
    others = S[(S.index != i) & (S.g >= s.g - a.pre) & (S.g <= s.g + a.post)]
    drop = set()
    for _, o in others.iterrows(): drop |= set(B.sindex.query(o.geometry, predicate="dwithin", distance=a.ctrl_hi * MI))
    if a.drop_near_old:
        for _, o in S[S.g < s.g - a.pre].iterrows(): drop |= set(B.sindex.query(o.geometry, predicate="dwithin", distance=a.treat_mi * MI))
    blk = blk[~blk.index.isin(drop)]
    for rg, idx in blk.groupby(blk).groups.items():
        sub = Wi[Wi.index.get_level_values("bi").isin(idx)]
        agg = sub.groupby(level="year").sum().reindex(years, fill_value=0)
        pos = sub.groupby(level="year").size().reindex(years, fill_value=0)
        rows.append(agg.assign(segment_id=s.segment_id, ring=rg, n_blocks=len(idx), n_blocks_pos=pos.values).reset_index())
    print(f"{s.segment_id:30s} g={int(s.g)}  " + "  ".join(f"{k}={v}" for k, v in blk.value_counts().items()) + f"  dropped={len(drop)}")
P = pd.concat(rows, ignore_index=True)[["segment_id", "ring", "year", "n_blocks", "n_blocks_pos"] + list(SECT.values())]
P.to_csv(CL / "ring_panel.csv", index=False); print("rows", len(P))
