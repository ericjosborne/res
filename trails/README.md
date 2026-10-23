# Multi-use trails and local economies in New York

A stacked event study of rail-trail and multi-use path openings in New York State: LODES jobs within half a mile of
each newly opened segment, compared with jobs 2-5 miles away, before and after the opening. The scope is every
rail-trail and off-road bike/pedestrian path, the Empire State Trail and everything else. Design: `docs/design.md`.
Data sources and access, including Advan/SafeGraph: `docs/data_access.md`.

**Status: pipeline only, no results yet.** The scripts have been smoke-tested on synthetic data but never run on real
data. The segment inventory has 135 segments; 76 meet the default sample rules. It was compiled from web-search
summaries and must be checked against its sources; status and gaps are in `docs/inventory.md`.

## Files

| File | What |
|---|---|
| `data/raw/trails/segments_*.csv` | hand-compiled segment opening inventory, one row per segment, with source URL, evidence and confidence; **verify before use** |
| `data/raw/trails/segment_endpoints_manual.csv` (optional) | endpoint coordinates and OSM name overrides by `segment_id` |
| `data/raw/lodes/`, `osm/`, `gazetteer/` (not committed) | downloads from `python/01_fetch_raw.py` |
| `data/clean/segments.csv`, `segments.geojson` | event list with g (first treated LODES year) and geometry |
| `data/clean/ring_panel.csv` | jobs by segment, ring (treat / spill / ctrl) and year |
| `output/tables/es_<tag>*.csv`, `output/figures/es_<tag>.png` | event-study estimates |

## How to run

From this directory (`trails/`), on a machine that can reach lehd.ces.census.gov, www2.census.gov and overpass-api.de:

```bash
pip install -r requirements.txt
python python/01_fetch_raw.py              # LODES8 NY WAC 2002-, block crosswalk, Gazetteer, OSM trail lines (~1 GB)
python python/02_segments.py               # event years and segment geometries; read output/tables/segments_status.md and fix
                                           # unmatched endpoints in data/raw/trails/segment_endpoints_manual.csv
python python/03_ring_panel.py             # ring x year job sums per segment (--drop_near_old for the stricter control)
python python/04_event_study.py            # main estimates; also --no_covid --tag nocovid, --exclude_nyc --tag upstate
```
