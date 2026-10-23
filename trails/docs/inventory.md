# Segment inventory: status and gaps

`data/raw/trails/segments_*.csv` holds 138 rows: 43 Hudson Valley / Champlain, 29 Erie Canalway, 40 other upstate and
26 downstate (NYC, Long Island, Westchester). Three rows are the same opening found from two lists and are marked
`duplicate_of`, leaving 135 segments.

**How it was compiled.** By web search only: the session could not open source pages, so every date rests on a
search result's summary of its source. Each row carries `source_url`, a short `evidence` paraphrase and a
`confidence` rating (high 43, medium 73, low 22). Before any result is used, open every source and confirm the date.
Start with the rows marked low, the ones whose notes say the date was inferred ("yesterday", "20-year-old section"),
and the ones dated 2020-12-31, which is the statewide Empire State Trail completion, not a date specific to the
segment.

**Default sample** (off-road types; high or medium confidence; dated to the month): 76 segments. Of these, 66 have
g ≤ 2023 (likely LODES coverage): 31 before 2020, 33 in 2020-2022 and 16 in NYC.

## Not yet searched or not dated (the search budget ran out)

* **Erie Canalway:** Mohawk-Hudson Bike-Hike Trail sections after 1977; Old Erie Canal State Park opening;
  1990s western build-out (Lockport-Palmyra); Buffalo / Tonawanda / Niagara segments; Port Byron-Weedsport-Jordan;
  Lyons-Clyde; Montgomery County paving and Canajoharie / St. Johnsville; Oswego Canal. A good single source: the
  August 2021 Empire State Trail final report's project table.
* **Hudson / Champlain:** Putnam Trailway Baldwin Place-Carmel; Schuylerville Ferry St-Garnsey Lane; Glens Falls
  Feeder Canal Trail; Ticonderoga-Keeseville and Mechanicville-Schuylerville (on-road); intermediate North and
  South County Trailway segments.
* **Other upstate:** original Wallkill Valley Rail Trail (1993); O&W beyond Kingston; Catskill Scenic extension;
  Auburn Trail; later Genesee Valley Greenway pieces; Catharine Valley; Zim Smith original; Saranac River Trail;
  D&H Rail Trail; Uncle Sam Bikeway; Vestal / Two Rivers Greenway; Keuka Outlet; Clarence Pathways; Allegheny River
  Valley; Black River Trail; El Camino and Genesee Riverway; South Hill / East Ithaca recreation ways; Kingston
  Greenline.
* **Downstate:** Rockaway / Queens greenways; Staten Island; Long Beach boardwalk; Old Croton Aqueduct; Bronx River
  Pathway (Westchester); Old Put / Joseph B. Clarke; Bethpage-Syosset and Massapequa extensions; Bronx River
  Shoelace and Soundview segments; Harlem River Greenway pieces.
* **Statewide sweep** (NYSDOT Transportation Alternatives awards, NYS Parks Recreational Trails Program grants,
  TrailLink's NY list): not started.
