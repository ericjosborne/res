"""01_fetch_raw.py -- download the public inputs: LODES8 workplace area characteristics for New York, the LODES block
crosswalk (2020 block centroids), the 2020 Census Gazetteer files for NY places and county subdivisions (to place the
segment endpoints), and the trail lines from OpenStreetMap (Overpass API).

Outputs: data/raw/lodes/ny_wac_S000_JT00_<year>.csv.gz, data/raw/lodes/ny_xwalk.csv.gz,
data/raw/gazetteer/2020_gaz_{place,cousubs}_36.txt, data/raw/osm/ny_trails.geojson.
Years that are not yet published (or missing for NY) are skipped with a message.  Re-running skips files already on
disk unless --force.  Needs outbound access to lehd.ces.census.gov, www2.census.gov and overpass-api.de.
"""
import argparse, json, time, urllib.request, urllib.error, urllib.parse
from pathlib import Path
PF = Path(__file__).resolve().parents[1]; RAW = PF / "data" / "raw"
ap = argparse.ArgumentParser(); ap.add_argument("--start", type=int, default=2002); ap.add_argument("--end", type=int, default=2024)
ap.add_argument("--skip_osm", action="store_true"); ap.add_argument("--force", action="store_true"); a = ap.parse_args()
LODES = "https://lehd.ces.census.gov/data/lodes/LODES8/ny"
GAZ = "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2020_Gazetteer"
OVERPASS = "https://overpass-api.de/api/interpreter"


def get(url, dest):
    if dest.exists() and not a.force: print("have", dest.name); return True
    dest.parent.mkdir(parents=True, exist_ok=True)
    for k in range(4):
        try:
            with urllib.request.urlopen(url, timeout=300) as r: dest.write_bytes(r.read())
            print("got ", dest.name); return True
        except urllib.error.HTTPError as e:
            if e.code == 404: print("none", url); return False
            err = e
        except urllib.error.URLError as e: err = e
        time.sleep(2 ** (k + 1))
    raise SystemExit(f"failed {url}: {err}")


for y in range(a.start, a.end + 1): get(f"{LODES}/wac/ny_wac_S000_JT00_{y}.csv.gz", RAW / "lodes" / f"ny_wac_S000_JT00_{y}.csv.gz")
get(f"{LODES}/ny_xwalk.csv.gz", RAW / "lodes" / "ny_xwalk.csv.gz")
for f in ["2020_gaz_place_36.txt", "2020_gaz_cousubs_36.txt"]: get(f"{GAZ}/{f}", RAW / "gazetteer" / f)

if not a.skip_osm:
    # Every way that is a bike/foot path or is a member of a named cycle route, in New York State.  Paths shorter than
    # trails (sidewalks, park paths) come along too; 02_segments.py keeps only the ways whose name or route matches a
    # trail in the inventory.  OSM is today's network, so it gives where a trail runs, never when it opened.
    q = """[out:json][timeout:900];
area["ISO3166-2"="US-NY"][admin_level=4]->.ny;
(relation["route"~"bicycle|hiking|foot"](area.ny);)->.r;
(way(r.r); way["highway"~"cycleway|path|track|footway"]["name"](area.ny);)->.w;
.r out body; .w out tags geom;"""
    dest = RAW / "osm" / "ny_trails_overpass.json"
    if not dest.exists() or a.force:
        req = urllib.request.Request(OVERPASS, data=urllib.parse.urlencode({"data": q}).encode())
        with urllib.request.urlopen(req, timeout=1200) as r: dest.write_bytes(r.read())
    els = json.loads(dest.read_text())["elements"]
    member_of = {}
    for e in els:
        if e["type"] == "relation":
            for m in e.get("members", []):
                if m["type"] == "way": member_of.setdefault(m["ref"], []).append(e.get("tags", {}).get("name", ""))
    feats = []
    for e in els:
        if e["type"] != "way" or "geometry" not in e: continue
        t = e.get("tags", {})
        feats.append({"type": "Feature", "geometry": {"type": "LineString", "coordinates": [[p["lon"], p["lat"]] for p in e["geometry"]]},
                      "properties": {"osm_id": e["id"], "name": t.get("name", ""), "highway": t.get("highway", ""), "surface": t.get("surface", ""),
                                     "routes": "|".join(sorted(set(member_of.get(e["id"], []))))}})
    (RAW / "osm" / "ny_trails.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": feats}))
    print("osm ways", len(feats))
