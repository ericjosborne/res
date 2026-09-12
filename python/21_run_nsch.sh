#!/usr/bin/env bash
# 21_run_nsch.sh -- Callaway-Sant'Anna runs on the NSCH file (docs/nsch_design.md).
# Time index = child's birth year; cohort = first birth year with >= 6 months of PFML benefits.
# Outputs: output/tables/nsch_<sample>_<outcome>[_<variant>]_{event,group,calendar,simple,attgt}.csv
set -u
cd "$(dirname "$0")/.."
B=${B:-299}
run() { python3 python/02_csdid.py --data nsch --B "$B" --window -6 6 "$@" 2>&1 | grep -v Warning > "output/logs/nsch_$(echo "$*" | tr -c 'A-Za-z0-9_' '_' | cut -c1-120).log"; }
export -f run; export B
mkdir -p output/logs
{
# (a) mothers of 0-5: parent and child outcomes, never-treated controls
for y in a1_ment a1_ment_fairpoor a1_ment_excellent a1_phys parent_stress stress_any coping_notwell support a1_employed a1_fulltime \
         child_fairpoor prev_visit everbf bf_ge26wk; do
    echo "--sample mothers_0_5 --outcome $y"
done
# (b) child-age bands (survey year moves one-for-one with birth year within a band)
for s in mothers_0_1 mothers_2_3 mothers_4_5; do for y in a1_ment a1_ment_fairpoor; do echo "--sample $s --outcome $y"; done; done
# (c) fathers: respondent fathers; second-adult fathers reported by the mother
for y in a1_ment a1_ment_fairpoor; do echo "--sample fathers_0_5 --outcome $y"; done
for y in a2_ment; do echo "--sample mothers_0_5 --outcome $y --query a2_father==1 --tag nsch_a2fathers_0_5_$y"; done
# (d) placebo: mothers of children aged 6-17 (born before the policy, observed after it)
for y in a1_ment a1_ment_fairpoor; do echo "--sample mothers_6_17 --outcome $y"; done
# (e) robustness on the main outcomes
for y in a1_ment a1_ment_fairpoor; do
    echo "--sample mothers_0_5 --outcome $y --notyet"
    echo "--sample mothers_0_5 --outcome $y --anticipation 1 --tag nsch_mothers_0_5_${y}_ant1"
    echo "--sample mothers_0_5 --outcome $y --time birth_year_ya --tag nsch_mothers_0_5_${y}_yearminusage"
    echo "--sample mothers_0_5 --outcome $y --query survey_year!=2020&survey_year!=2021 --tag nsch_mothers_0_5_${y}_nopandemic"
    echo "--sample mothers_0_5 --outcome $y --query survey_year>=2019 --tag nsch_mothers_0_5_${y}_s2019plus"
done
# (f) heterogeneity on the mental-health score
for q in "fpl_lt200==1:lowinc" "fpl_lt200==0:highinc" "a1_married==1:married" "a1_married==0:unmarried" \
         "race4=='white':white" "race4=='black':black" "race4=='hispanic':hispanic" "a1_educ3=='college':college" "a1_educ3!='college':noncollege"; do
    echo "--sample mothers_0_5 --outcome a1_ment --query ${q%%:*} --tag nsch_het_${q##*:}_a1_ment"
    echo "--sample mothers_0_5 --outcome a1_ment_fairpoor --query ${q%%:*} --tag nsch_het_${q##*:}_a1_ment_fairpoor"
done
} | xargs -P "${P:-4}" -I{} bash -c 'run {}'
echo done
