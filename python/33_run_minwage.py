"""33_run_minwage.py -- run battery for the minimum wage / enrollment design (python/32_stacked_events.py)."""
import argparse, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
PF = Path(__file__).resolve().parents[1]; LOG = PF / "output" / "logs"; LOG.mkdir(exist_ok=True, parents=True)
ap = argparse.ArgumentParser(); ap.add_argument("--B", type=int, default=199); ap.add_argument("--P", type=int, default=4); a = ap.parse_args()
runs = []
OUT = ["enrolled", "enr_hs", "enr_ft", "employed", "atwork", "inlf", "hours", "enr_emp", "enr_only", "emp_only", "neither", "log_wage", "log_earnweek"]
for ages in (["16", "17"], ["18", "19"], ["16", "19"], ["20", "24"]):
    for y in OUT:
        if ages == ["20", "24"] and y not in ("enrolled", "employed", "neither", "log_wage"): continue
        runs.append(["--ages", *ages, "--outcome", y])
for y in ("enrolled", "employed", "neither"):
    for ages in (["16", "17"], ["18", "19"]):
        runs.append(["--ages", *ages, "--outcome", y, "--events", "all"])
        runs.append(["--ages", *ages, "--outcome", y, "--events", "pre2010"])
        runs.append(["--ages", *ages, "--outcome", y, "--events", "large"])
        runs.append(["--ages", *ages, "--outcome", y, "--controls", "strict"])
        runs.append(["--ages", *ages, "--outcome", y, "--controls", "federal"])
        runs.append(["--ages", *ages, "--outcome", y, "--equal"])
        runs.append(["--ages", *ages, "--outcome", y, "--query", "year<2020 | year>2021", "--tag", f"mw_{ages[0]}{ages[1]}_{y}_post2009_nopandemic"])
        runs.append(["--ages", *ages, "--outcome", y, "--query", "month<=5 | month>=9", "--tag", f"mw_{ages[0]}{ages[1]}_{y}_post2009_schoolmonths"])
for q, k in [("female==1", "female"), ("female==0", "male"), ("black==1", "black"), ("hispanic==1", "hispanic"), ("black==0 & hispanic==0", "whiteother"),
             ("faminc<=730", "faminc_lt50k"), ("faminc>730 & faminc<900", "faminc_ge50k")]:
    for ages in (["16", "17"], ["18", "19"]):
        runs.append(["--ages", *ages, "--outcome", "enrolled", "--query", q, "--tag", f"mw_{ages[0]}{ages[1]}_enrolled_post2009_{k}"])


def go(args):
    tag = args[args.index("--tag") + 1] if "--tag" in args else None
    cmd = [sys.executable, str(PF / "python" / "32_stacked_events.py"), "--B", str(a.B)] + args
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=PF)
    line = next((l for l in r.stdout.splitlines() if l.startswith("mw_")), "")
    tag = tag or (line.split(":")[0] if line else " ".join(args))
    (LOG / f"{tag}.log").write_text(r.stdout + r.stderr)
    return tag, r.returncode


with ThreadPoolExecutor(a.P) as ex:
    for tag, rc in ex.map(go, runs):
        print(("ok   " if rc == 0 else "FAIL ") + tag, flush=True)
print("done")
