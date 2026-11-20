"""53_run_quartiles.py -- event studies by within-year family income quartile (--ses rel_q1 .. rel_q4 in 32_stacked_events.py)
or tercile (rel_t1 .. rel_t3).  Tags: mw_{ages}_{outcome}_unit_q{1..4} / _t{1..3}.
Usage: python python/53_run_quartiles.py [B] [workers] [q|t]"""
import subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
PF = Path(__file__).resolve().parents[1]; LOG = PF / "output" / "logs"; LOG.mkdir(exist_ok=True, parents=True)
B = sys.argv[1] if len(sys.argv) > 1 else "99"; P = int(sys.argv[2]) if len(sys.argv) > 2 else 4; S = sys.argv[3] if len(sys.argv) > 3 else "q"; NG = 4 if S == "q" else 3
runs = []
for y in ("log_wage", "enr_emp", "enr_only", "emp_only", "neither", "enrolled", "employed"):
    for ages in (["16", "17"], ["18", "19"], ["16", "19"]):
        for q in range(1, NG + 1):
            runs.append(["--ages", *ages, "--outcome", y, "--events", "unit", "--ses", f"rel_{S}{q}", "--tag", f"mw_{ages[0]}{ages[1]}_{y}_unit_{S}{q}"])
def go(args):
    r = subprocess.run([sys.executable, str(PF / "python" / "32_stacked_events.py"), "--B", B] + args, capture_output=True, text=True, cwd=PF)
    tag = args[args.index("--tag") + 1]; (LOG / f"{tag}.log").write_text(r.stdout + r.stderr); return tag, r.returncode
with ThreadPoolExecutor(P) as ex:
    for tag, rc in ex.map(go, runs): print(("ok   " if rc == 0 else "FAIL ") + tag, flush=True)
print("done")
