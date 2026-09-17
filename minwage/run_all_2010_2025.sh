#!/bin/sh
# Full pipeline on the 2010-2025 window: build, event-study batteries, regressions, tables and figures. ~5 hours.
set -e
cd "$(dirname "$0")"; L=output/logs; mkdir -p $L
python3 python/30_build_cps_monthly.py            > $L/all_30_build.out 2>&1
python3 python/33_run_minwage.py --B 99 --P 4      > $L/all_33_unit.out 2>&1
python3 python/39_run_units.py 99                  > $L/all_39_units.out 2>&1
python3 python/33_run_minwage.py --B 99 --P 4 --design post2009 > $L/all_33_state.out 2>&1
python3 python/40_run_ses.py 99                    > $L/all_40_ses.out 2>&1
python3 python/42_run_ses_rel.py 99                > $L/all_42_sesrel.out 2>&1
python3 python/43_run_dropout.py 99                > $L/all_43_dropout.out 2>&1
python3 python/44_run_dropout_school.py 99         > $L/all_44_dropout_school.out 2>&1
python3 python/48_run_het.py 99                    > $L/all_48_het.out 2>&1
python3 python/46_regressions.py                   > $L/all_46_regressions.out 2>&1
python3 python/47_twfe_diagnostics.py              > $L/all_47_diag.out 2>&1
python3 python/51_stacked_controls.py --groups=all,lowses,highses,female,male,white,nonwhite > $L/all_51_stacked.out 2>&1
python3 python/34_summarise_minwage.py             > $L/all_34.out 2>&1
python3 python/35_paper_tables.py                  > $L/all_35.out 2>&1
python3 python/41_summarise_ses.py                 > $L/all_41.out 2>&1
python3 python/41_summarise_ses.py rel             > $L/all_41rel.out 2>&1
python3 python/45_paper_v2_tables.py               > $L/all_45.out 2>&1
python3 python/51_stacked_controls.py --tables     > $L/all_51_tables.out 2>&1
echo ALLDONE > $L/all_done.flag
