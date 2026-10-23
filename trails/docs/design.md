# Design memo: multi-use trails and local economies in New York

## Question

Do new rail-trails and off-road multi-use paths raise business activity next to them, and is the gain new activity or
activity moved from a few miles away? Every rail-trail and bike/pedestrian multi-use path opened in New York State is
in scope, not only the Empire State Trail. The Empire State Trail gives a large group of segments in 2017-2021 (gap
closures linking the Erie Canalway, Hudson Valley and Champlain routes). Other rail-trails and greenways, upstate and
downstate, add events in other years.

## Treatment

A *segment* is a piece of trail with its own opening date (a new rail-trail, an extension, a gap closure, a bridge).
The inventory in `data/raw/trails/segments_*.csv` is compiled by hand from press releases and local news, with a source on every row.
This dated segment inventory is a contribution of its own. Rules:

* Off-road segments only in the main sample (`new_offroad`, `gap_closure`, `extension`, `bridge`). Resurfacing
  (`upgrade`) and signed on-road routes (`onroad_designation`) are separate, weaker treatments.
* Dates to the month. LODES counts jobs in the second quarter (see the LODES technical documentation), so a segment
  opened by the end of March is treated that year, otherwise the next year (`02_segments.py --cutoff_month`). Segments
  dated only to the year are dropped by default.
* Where the trail runs comes from OpenStreetMap (today's network). Each segment is the stretch of its named OSM trail
  between its two endpoints, which come from hand-entered coordinates or a 2020 Gazetteer lookup. Check every
  geometry on a map (`data/clean/segments.geojson`); `geo_status` flags the unclipped ones.

## Outcome data

Main source: LEHD LODES8 workplace area characteristics. These are jobs by 2020 census block for every year from 2002,
by sector: all jobs, retail (NAICS 44-45), arts/entertainment/recreation (71), accommodation and food services (72).
They are free, cover the whole state and use the same block geography in every year. Limits: they count only jobs
covered by unemployment insurance, so the self-employed (many B&Bs and bike rentals) are missing; block cells carry
added noise; and the latest year runs about two to three years behind.

## Estimator

A stacked event study, one 2x2 comparison per segment (`04_event_study.py`):

* treated ring: blocks within 0.5 mile of the segment; spillover ring 0.5-1.5 miles; control ring 2-5 miles;
* jobs summed over the ring; ATT_s(e) = change in ln(treated) minus change in ln(control) from g-1 to g+e;
* blocks near another segment opening within the event window are dropped from that stack; `--drop_near_old`
  also drops blocks already beside an older trail;
* ATT(e) averages over segments; standard errors bootstrap whole trails (segments of one trail are correlated).

A control ring in the same corridor nets out local shocks such as county economies, the canal towns' long decline
and COVID. It is valid only if blocks half a mile and three miles from a trail would have trended the same. The trail
routes follow old rail and canal rights-of-way, which date from the 19th century. That helps, but town centres sit
on the canal, so pre-trends must be checked. The spill ring tests for displacement: a negative spill estimate means
activity moved toward the trail.

## Threats and checks

1. **COVID.** Many Empire State Trail segments have g = 2021. Run `--no_covid`, and use the pre-2020 and post-2022
   events on their own.
2. **Placement and timing.** Towns that got segments early may already have been growing. Check pre-trends, and use
   placebo events on announced-but-not-yet-built segments (dated by their funding announcement).
3. **Downstate density.** In NYC a 2-5 mile ring is a different economy. Use `--exclude_nyc`, or narrower rings
   for downstate.
4. **Power.** Treated rings in rural places hold few accommodation and food jobs. Use `--min_base_jobs` and report
   the number of events at each event time.
5. **Second outcomes.** Home sale prices from NYS ORPS (repeat sales by distance), ZIP Business Patterns
   establishment counts, and Advan foot traffic (from about 2019) to show visits actually rose (first stage).

## Status

Pipeline written and smoke-tested on synthetic data (it recovers a planted +20% effect). It has **not** been run
on real data, because the session that wrote it could not reach the Census, NY or OSM servers. Run `01_fetch_raw.py`
on a machine with internet access.
