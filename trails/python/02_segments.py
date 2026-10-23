"""02_segments.py -- the segment event list with a line geometry for each segment.

Inputs: data/raw/trails/segments_*.csv (the hand-compiled opening inventory, one file per trail system; every row
carries its source), data/raw/trails/segment_endpoints_manual.csv (optional: segment_id, from_lat, from_lon, to_lat,
to_lon, osm_name -- overrides for endpoints and for the OSM name pattern), the Gazetteer files and the OSM lines from
01_fetch_raw.py.

Event year.  LODES counts jobs held in (roughly) the second quarter, so a segment that opened on or before the end
of --cutoff_month (default 3, March) is first treated in its opening year, otherwise in the next year: g = first
LODES year after the opening, base year = g - 1.  Year-only dates give g = year + 1 and are flagged ambiguous (the
opening year itself may be partly treated); 04 drops them unless --keep_ambiguous.

Geometry.  The OSM ways whose name or route relation matches the segment's osm_name (default: its trail name) are
merged; the segment is the piece of that line between the points on it nearest the two endpoints (manual
coordinates, else the Gazetteer place / county subdivision named in from_place / to_place, else the whole trail,
flagged).  Every segment's geo_status says which was used; check them on a map before using the results.

Outputs: data/clean/segments.csv (events), data/clean/segments.geojson (EPSG:4326 lines), output/tables/segments_status.md.
"""
import argparse, re
from pathlib import Path
import numpy as np, pandas as pd, geopandas as gpd
from shapely.geometry import Point, LineString, MultiLineString
from shapely.ops import linemerge, unary_union, substring
PF = Path(__file__).resolve().parents[1]; RAW = PF / "data" / "raw"; CL = PF / "data" / "clean"; TAB = PF / "output" / "tables"
CRS = 26918   # NAD83 / UTM 18N, metres
ap = argparse.ArgumentParser(); ap.add_argument("--cutoff_month", type=int, default=3); ap.add_argument("--snap_km", type=float, default=3.0); a = ap.parse_args()

S = pd.concat([pd.read_csv(f, dtype=str) for f in sorted((RAW / "trails").glob("segments_*.csv"))], ignore_index=True)
S = S[S.segment_id.notna()].drop_duplicates("segment_id")
man = RAW / "trails" / "segment_endpoints_manual.csv"
if man.exists():
    M = pd.read_csv(man, dtype={"segment_id": str, "osm_name": str}); S = S.merge(M, on="segment_id", how="left")
for c in ["from_lat", "from_lon", "to_lat", "to_lon", "osm_name"]:
    if c not in S: S[c] = np.nan

d = S.open_date.fillna("").str.strip()
S["open_year"] = pd.to_numeric(d.str[:4], errors="coerce")
S["open_month"] = pd.to_numeric(d.str[5:7].where(d.str.len() >= 7), errors="coerce")
S["ambiguous"] = S.open_month.isna() & S.open_year.notna()
S["g"] = np.where(S.open_month <= a.cutoff_month, S.open_year, S.open_year + 1)
S["base"] = S.g - 1

# --- endpoints from the Gazetteer (2020 places, then county subdivisions); NAME suffixes like "village" dropped ---
def gaz(f):
    g = pd.read_csv(RAW / "gazetteer" / f, sep="\t", dtype=str); g.columns = [c.strip() for c in g.columns]
    g["key"] = g.NAME.str.replace(r"\s+(city|town|village|CDP)$", "", regex=True).str.lower().str.strip()
    g["county"] = g.GEOID.str[2:5] if "cousub" in f else None
    return g[["key", "county", "INTPTLAT", "INTPTLONG"]].astype({"INTPTLAT": float, "INTPTLONG": float})
G = pd.concat([gaz("2020_gaz_place_36.txt"), gaz("2020_gaz_cousubs_36.txt")], ignore_index=True)
# a name is ambiguous when its places / subdivisions are more than 30 km apart (a village inside the town of the
# same name is not); ambiguous names need manual coordinates
spread = G.groupby("key").agg(dlat=("INTPTLAT", lambda x: x.max() - x.min()), dlon=("INTPTLONG", lambda x: x.max() - x.min()))
dup = set(spread[(spread.dlat * 111 > 30) | (spread.dlon * 82 > 30)].index)
G = G.drop_duplicates("key")   # first = the place

def endpoint(row, side):
    lat, lon = row[f"{side}_lat"], row[f"{side}_lon"]
    if pd.notna(lat) and pd.notna(lon): return Point(float(lon), float(lat)), "manual"
    name = str(row[f"{side}_place"] or "").lower()
    name = re.split(r"[,(/]| at | near ", name)[0].strip()
    name = re.sub(r"^(town|village|city) of ", "", name)
    hit = G[G.key == name]
    if len(hit) and name not in dup: return Point(hit.INTPTLONG.iloc[0], hit.INTPTLAT.iloc[0]), "gazetteer"
    return None, "unmatched" if name not in dup else "ambiguous_name"


L = gpd.read_file(RAW / "osm" / "ny_trails.geojson").to_crs(CRS)
L["hay"] = (L["name"].fillna("") + " | " + L["routes"].fillna("")).str.lower()
out, geoms = [], []
for _, r in S.iterrows():
    pat = str(r.osm_name if pd.notna(r.osm_name) else r.trail).lower()
    pat = re.sub(r"\b(trail|rail trail|trailway|greenway|bikeway|path)\b", "", pat).strip() or pat
    ways = L[L.hay.str.contains(re.escape(pat), regex=True)]
    status = {"n_ways": len(ways)}
    if not len(ways): out.append({**r, "geo_status": "no_osm_match", **status}); geoms.append(None); continue
    line = linemerge(unary_union(list(ways.geometry)))
    parts = list(line.geoms) if isinstance(line, MultiLineString) else [line]
    pts = [endpoint(r, s) for s in ("from", "to")]
    status["from_src"], status["to_src"] = pts[0][1], pts[1][1]
    if pts[0][0] is None or pts[1][0] is None:
        out.append({**r, "geo_status": "whole_trail", **status}); geoms.append(line); continue
    p0, p1 = gpd.GeoSeries([pts[0][0], pts[1][0]], crs=4326).to_crs(CRS)
    # the merged component that both endpoints are near; else every component between them, by distance along each
    best = min(parts, key=lambda ln: ln.distance(p0) + ln.distance(p1))
    if best.distance(p0) <= a.snap_km * 1e3 and best.distance(p1) <= a.snap_km * 1e3:
        t0, t1 = sorted([best.project(p0), best.project(p1)])
        seg = substring(best, t0, t1); st = "clipped"
    else:
        box = LineString([p0, p1]).buffer(a.snap_km * 1e3)
        seg = unary_union([ln.intersection(box) for ln in parts]); st = "corridor_box"
    out.append({**r, "geo_status": st, **status, "seg_km": round(seg.length / 1e3, 2)}); geoms.append(seg)

E = gpd.GeoDataFrame(pd.DataFrame(out), geometry=geoms, crs=CRS)
keep = ["segment_id", "trail_system", "trail", "segment_name", "from_place", "to_place", "counties", "miles", "open_date",
        "date_precision", "open_type", "confidence", "open_year", "g", "base", "ambiguous", "geo_status", "n_ways", "from_src", "to_src", "seg_km"]
E = E.reindex(columns=keep + ["geometry"])
CL.mkdir(parents=True, exist_ok=True); TAB.mkdir(parents=True, exist_ok=True)
E.drop(columns="geometry").to_csv(CL / "segments.csv", index=False)
E[E.geometry.notna()].to_crs(4326).to_file(CL / "segments.geojson", driver="GeoJSON")
cnt = E.groupby(["trail_system", "geo_status"]).size().unstack(fill_value=0)
(TAB / "segments_status.md").write_text("# Segment geometry status\n\n" + cnt.to_markdown() + "\n\nEvents by first treated LODES year g:\n\n"
                                         + E.groupby("g").size().to_frame("segments").to_markdown() + "\n")
print(cnt); print(E[E.geo_status.isin(["no_osm_match", "whole_trail", "corridor_box"])][["segment_id", "trail", "geo_status", "from_src", "to_src"]].to_string())
