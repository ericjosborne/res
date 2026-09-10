#!/usr/bin/env bash
# Heterogeneous effects of PFML: mothers of under-6s (worked, hours) and all
# women (birth last year) by education, other family income tercile, marital
# status and race/ethnicity.  Output: output/tables/het_<group>_<outcome>_*.csv
# Usage: bash python/05_heterogeneity.sh [B]
set -uo pipefail
cd "$(dirname "$0")/.."
B=${1:-199}
mkdir -p output/logs
declare -A Q=(
  [educ_hs]="educ3=='hs_or_less'"  [educ_some]="educ3=='some_college'"  [educ_college]="educ3=='college'"
  [ofi_low]="ofi_tercile=='low'"   [ofi_mid]="ofi_tercile=='mid'"        [ofi_high]="ofi_tercile=='high'"
  [married]="married==1"           [unmarried]="married==0"
  [white]="race4=='white'"         [black]="race4=='black'"              [hispanic]="race4=='hispanic'"  [other]="race4=='other'"
)
run() {  # sample outcome group
  python3 python/02_csdid.py --sample "$1" --outcome "$2" --query "${Q[$3]}" --tag "het_${3}_${1}_${2}" --B "$B" --window -10 10 \
    > "output/logs/het_${3}_${1}_${2}.log" 2>&1
}

n=0
for g in "${!Q[@]}"; do
  for spec in "mothers_lt6 worked" "mothers_lt6 hours" "all has_infant"; do
    set -- $spec
    run "$1" "$2" "$g" &
    n=$((n+1)); if (( n % 8 == 0 )); then wait; fi
  done
done
wait
grep -L "^wrote" output/logs/het_*.log || echo "all heterogeneity runs finished"
