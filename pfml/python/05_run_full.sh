#!/usr/bin/env bash
# Run the full-window Callaway-Sant'Anna estimations on the IPUMS ASEC file.
# Usage: bash pfml/python/05_run_full.sh [B]   (bootstrap draws, default 499)
set -euo pipefail
cd "$(dirname "$0")/../.."
B=${1:-499}
mkdir -p pfml/output/logs
jobs=()
for s in mothers_lt6 childless mothers; do
  for y in worked hours fulltime inlf; do
    python3 pfml/python/04_csdid_full.py --sample $s --outcome $y --B $B > pfml/output/logs/full_${s}_${y}.log 2>&1 &
    jobs+=($!)
  done
done
# not-yet-treated controls for the headline
python3 pfml/python/04_csdid_full.py --sample mothers_lt6 --outcome worked --notyet --B $B > pfml/output/logs/full_mothers_lt6_worked_notyet.log 2>&1 &
jobs+=($!)
fail=0
for j in "${jobs[@]}"; do wait "$j" || fail=1; done
echo "all runs finished (fail=$fail)"
exit $fail
