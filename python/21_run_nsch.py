"""21_run_nsch.py -- Callaway-Sant'Anna runs on the NSCH file (docs/nsch_design.md), in parallel.

Time index = child's birth year; cohort = first birth year with >= 6 months of PFML benefits.
Outputs: output/tables/nsch_<sample>_<outcome>[_<variant>]_{event,group,calendar,simple,attgt}.csv
Usage: python 21_run_nsch.py [--B 299] [--P 4]
"""
import argparse, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

PF = Path(__file__).resolve().parents[1]; LOG = PF / "output" / "logs"; LOG.mkdir(parents=True, exist_ok=True)
ap = argparse.ArgumentParser(); ap.add_argument("--B", type=int, default=299); ap.add_argument("--P", type=int, default=4); a = ap.parse_args()

runs = []
# (a) mothers of 0-5: parent and child outcomes, never-treated controls
for y in ["a1_ment", "a1_ment_fairpoor", "a1_ment_excellent", "a1_phys", "parent_stress", "stress_any", "coping_notwell", "support",
          "a1_employed", "a1_fulltime", "child_fairpoor", "prev_visit", "everbf", "bf_ge26wk"]:
    runs.append(["--sample", "mothers_0_5", "--outcome", y])
# (b) child-age bands (survey year moves one-for-one with birth year within a band)
for s in ["mothers_0_1", "mothers_2_3", "mothers_4_5"]:
    for y in ["a1_ment", "a1_ment_fairpoor"]:
        runs.append(["--sample", s, "--outcome", y])
# (c) fathers: respondent fathers; second-adult fathers reported by the mother
for y in ["a1_ment", "a1_ment_fairpoor"]:
    runs.append(["--sample", "fathers_0_5", "--outcome", y])
runs.append(["--sample", "mothers_0_5", "--outcome", "a2_ment", "--query", "a2_father==1", "--tag", "nsch_a2fathers_0_5_a2_ment"])
# (d) placebo: mothers of children aged 6-17 (born before the policy, observed after it)
for y in ["a1_ment", "a1_ment_fairpoor"]:
    runs.append(["--sample", "mothers_6_17", "--outcome", y])
# (e) robustness on the main outcomes
for y in ["a1_ment", "a1_ment_fairpoor"]:
    runs.append(["--sample", "mothers_0_5", "--outcome", y, "--notyet"])
    runs.append(["--sample", "mothers_0_5", "--outcome", y, "--anticipation", "1", "--tag", f"nsch_mothers_0_5_{y}_ant1"])
    runs.append(["--sample", "mothers_0_5", "--outcome", y, "--time", "birth_year_ya", "--tag", f"nsch_mothers_0_5_{y}_yearminusage"])
    runs.append(["--sample", "mothers_0_5", "--outcome", y, "--query", "survey_year!=2020 & survey_year!=2021", "--tag", f"nsch_mothers_0_5_{y}_nopandemic"])
    runs.append(["--sample", "mothers_0_5", "--outcome", y, "--query", "survey_year>=2019", "--tag", f"nsch_mothers_0_5_{y}_s2019plus"])
# (f) heterogeneity on the mental-health outcomes
for q, k in [("fpl_lt200==1", "lowinc"), ("fpl_lt200==0", "highinc"), ("a1_married==1", "married"), ("a1_married==0", "unmarried"),
             ("race4=='white'", "white"), ("race4=='black'", "black"), ("race4=='hispanic'", "hispanic"),
             ("a1_educ3=='college'", "college"), ("a1_educ3!='college'", "noncollege")]:
    for y in ["a1_ment", "a1_ment_fairpoor"]:
        runs.append(["--sample", "mothers_0_5", "--outcome", y, "--query", q, "--tag", f"nsch_het_{k}_{y}"])


def go(args):
    tag = args[args.index("--tag") + 1] if "--tag" in args else "nsch_" + args[1] + "_" + args[3] + ("_notyet" if "--notyet" in args else "")
    cmd = [sys.executable, str(PF / "python" / "02_csdid.py"), "--data", "nsch", "--B", str(a.B), "--window", "-6", "6"] + args
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=PF)
    (LOG / f"{tag}.log").write_text(r.stdout + r.stderr)
    return tag, r.returncode


with ThreadPoolExecutor(a.P) as ex:
    for tag, rc in ex.map(go, runs):
        print(("ok   " if rc == 0 else "FAIL ") + tag, flush=True)
print("done")
