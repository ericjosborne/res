# Data access

| Source | Geography, frequency | Use | Access |
|---|---|---|---|
| LEHD LODES8 WAC | 2020 block, annual 2002- | main outcome: jobs by sector | free, `01_fetch_raw.py` (lehd.ces.census.gov) |
| OpenStreetMap (Overpass) | trail lines | segment geometry (not dates) | free, `01_fetch_raw.py` |
| Census 2020 Gazetteer | place / county subdivision points | segment endpoints | free, `01_fetch_raw.py` |
| Segment opening dates | segment | treatment timing | hand-compiled, `data/raw/trails/segments_*.csv`; check every row |
| ZIP Business Patterns | ZIP, annual | establishment counts by detailed NAICS (722, 721, sporting goods) | free, census.gov CBP |
| NYS ORPS property sales | parcel | repeat-sales prices by distance to trail | free, data.ny.gov |
| NYS taxable sales and purchases | county / some cities, quarterly | sales-tax base by industry | free, data.ny.gov |
| Census Business Formation Statistics | county, monthly | new business applications | free |
| Advan Monthly Patterns (formerly SafeGraph) | point of interest, monthly, about 2019- | foot traffic at businesses near trails; visitor origins | Dewey Data: check for a university licence; individual Researcher plan $3,600/yr (Dewey pricing page, October 2026) |
| Data Axle / Infogroup historical business files | establishment | business openings and closures | many university libraries |
| QCEW establishment microdata | establishment | exact locations and payroll | restricted (FSRDC or NYS DOL agreement) |
| Trail counters, Strava Metro | segment | first stage: use | NYS DOT / Parks, Parks & Trails NY; Strava Metro free for research partners |

Advan bought SafeGraph's Patterns business in 2022, and academic access now runs through Dewey Data. Visit counts move
with changes in the size of the phone panel, so use normalized visits and compare within county and month.
