# Staggered state policies with Callaway-Sant'Anna estimators

Three separate projects, each self-contained (own data, code, outputs, docs):

| Directory | Paper | Data | Status |
|---|---|---|---|
| [`pfml/`](pfml/) | Paid family and medical leave: mothers' labour supply and fertility (IPUMS-CPS ASEC 1990-2025) and parents' mental health one to five years after a birth (NSCH 2016-2024) | release assets `data-v1`, `data-nsch` | precise labour-supply and fertility nulls; suggestive mental-health result (`pfml/docs/results.md`, `pfml/docs/nsch_results.md`) |
| [`minwage/`](minwage/) | The fall in teen employment and the minimum wage: stacked event studies of school enrollment and work (IPUMS-CPS basic monthly 1994-2026) | release asset `data-cps-monthly` | draft paper `minwage/paper/minwage_teens.pdf`; wages up 3-7%, enrollment and employment unchanged (`minwage/docs/minwage_results.md`) |
| [`trails/`](trails/) | Rail-trails and multi-use paths in New York and nearby jobs: stacked event study of segment openings with LODES block jobs (2002-) | public downloads (`trails/python/01_fetch_raw.py`) and a hand-compiled opening inventory | pipeline written and tested on synthetic data; inventory in progress; not yet run on real data |

`results.html` is a single page summarising both (Parts I-III). Each project
is run from its own directory; see its README. Both use the same estimator
code pattern (`02_csdid.py` in `pfml/`, `32_stacked_events.py` in `minwage/`)
and the same plotting helpers (`aelib.py`, duplicated in each).
