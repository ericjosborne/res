"""33_run_minwage.py -- main run battery for the minimum wage / enrollment design (python/32_stacked_events.py).
Main specification: the unit design (--events unit: every county with its own minimum is a unit, the rest of each
state another; 38_unit_panel.py).  The state design (--events post2009) is run by the same battery for the appendix.
"""
import argparse, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
PF = Path(__file__).resolve().parents[1]; LOG = PF / "output" / "logs"; LOG.mkdir(exist_ok=True, parents=True)
ap = argparse.ArgumentParser(); ap.add_argument("--B", type=int, default=99); ap.add_argument("--P", type=int, default=4); ap.add_argument("--design", default="unit", help="unit (main) | post2009 (state design)"); a = ap.parse_args()
D = a.design
runs = []
OUT = ["enrolled", "enr_hs", "enr_ft", "employed", "atwork", "inlf", "hours", "enr_emp", "enr_only", "emp_only", "neither", "log_wage", "log_earnweek"]
for ages in (["16", "17"], ["18", "19"], ["16", "19"], ["20", "24"]):
    for y in OUT:
        if ages == ["20", "24"] and y not in ("enrolled", "employed", "neither", "log_wage"): continue
        runs.append(["--ages", *ages, "--outcome", y, "--events", D])
for y in ("enrolled", "employed", "neither"):
    for ages in (["16", "17"], ["18", "19"]):
        runs.append(["--ages", *ages, "--outcome", y, "--events", D + "_all" if D == "unit" else "all"])
        runs.append(["--ages", *ages, "--outcome", y, "--events", D + "_pre2010" if D == "unit" else "pre2010"])
        runs.append(["--ages", *ages, "--outcome", y, "--events", D + "_large" if D == "unit" else "large"])
        runs.append(["--ages", *ages, "--outcome", y, "--events", D, "--controls", "strict"])
        runs.append(["--ages", *ages, "--outcome", y, "--events", D, "--controls", "federal"])
        runs.append(["--ages", *ages, "--outcome", y, "--events", D, "--equal"])
        runs.append(["--ages", *ages, "--outcome", y, "--events", D, "--query", "year<2020 | year>2021", "--tag", f"mw_{ages[0]}{ages[1]}_{y}_{D}_nopandemic"])
        runs.append(["--ages", *ages, "--outcome", y, "--events", D, "--query", "month<=5 | month>=9", "--tag", f"mw_{ages[0]}{ages[1]}_{y}_{D}_schoolmonths"])
for q, k in [("female==1", "female"), ("female==0", "male"), ("black==1", "black"), ("hispanic==1", "hispanic"), ("black==0 & hispanic==0", "whiteother"),
             ("faminc<=730", "faminc_lt50k"), ("faminc>730 & faminc<900", "faminc_ge50k")]:
    for ages in (["16", "17"], ["18", "19"]):
        runs.append(["--ages", *ages, "--outcome", "enrolled", "--events", D, "--query", q, "--tag", f"mw_{ages[0]}{ages[1]}_enrolled_{D}_{k}"])


def go(args):
    tag = args[args.index("--tag") + 1] if "--tag" in args else None
    r = subprocess.run([sys.executable, str(PF / "python" / "32_stacked_events.py"), "--B", str(a.B)] + args, capture_output=True, text=True, cwd=PF)
    line = next((l for l in r.stdout.splitlines() if l.startswith("mw_")), ""); tag = tag or (line.split(":")[0] if line else " ".join(args))
    (LOG / f"{tag}.log").write_text(r.stdout + r.stderr); return tag, r.returncode


with ThreadPoolExecutor(a.P) as ex:
    for tag, rc in ex.map(go, runs): print(("ok   " if rc == 0 else "FAIL ") + tag, flush=True)
print("done")
