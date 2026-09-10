#!/usr/bin/env bash
# Checks on the white-mother effect (docs/results.md 7.1): childless placebo by
# race and eligibility splits on the ASEC-to-ASEC linked sample (run 07_link_lag.py first).
set -uo pipefail; cd "$(dirname "$0")/.."; B=${1:-199}; mkdir -p output/logs
r(){ python3 python/02_csdid.py --sample "$1" --outcome "$2" --query "$3" --tag "$4" --B "$B" --window -10 10 > "output/logs/$4.log" 2>&1; }
for g in white black hispanic other; do for y in worked hours; do r childless $y "race4=='$g'" "het_${g}_childless_${y}" & done; done; wait
r mothers_lt6 worked "linked_prev==1" elig_linked_all &
r mothers_lt6 worked "linked_prev==1 and race4=='white'" elig_linked_white &
r mothers_lt6 worked "worked_lag==1" elig_yes_all &
r mothers_lt6 worked "worked_lag==0" elig_no_all &
r mothers_lt6 hours  "worked_lag==1" elig_yes_all_hours &
r mothers_lt6 worked "worked_lag==1 and race4=='white'" elig_yes_white &
r mothers_lt6 worked "worked_lag==0 and race4=='white'" elig_no_white &
r mothers_lt6 worked "worked_lag==1 and race4=='black'" elig_yes_black &
r mothers_lt6 worked "worked_lag==1 and race4=='hispanic'" elig_yes_hispanic &
r mothers_lt6 worked "worked_lag==0 and race4=='hispanic'" elig_no_hispanic &
wait; grep -L "^wrote" output/logs/elig_*.log output/logs/het_*_childless_*.log || echo "checks finished"
