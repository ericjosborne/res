"""50_run_nohs.py -- the four school-work shares (plus enrollment and employment) among teens without a high school diploma
or GED, September-May only, by family income (below / at or above $50,000); unit design, 2010+ events.
Tags mw_<ages>_<y>_unit_nohs_school_{lowses,highses}."""
import subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
PF = Path(__file__).resolve().parents[1]; LOG = PF / "output" / "logs"; LOG.mkdir(exist_ok=True, parents=True)
B = sys.argv[1] if len(sys.argv) > 1 else "99"
Q = "hs_grad==0 & (month<=5 | month>=9)"
runs = []
for y in ("enr_emp", "enr_only", "emp_only", "neither", "enrolled", "employed"):
    for ages in (["16", "19"], ["16", "17"], ["18", "19"]):
        runs.append(["--ages", *ages, "--outcome", y, "--events", "unit", "--query", Q + " & faminc<=740", "--tag", f"mw_{ages[0]}{ages[1]}_{y}_unit_nohs_school_lowses"])
        runs.append(["--ages", *ages, "--outcome", y, "--events", "unit", "--query", Q + " & faminc>=820 & faminc<900", "--tag", f"mw_{ages[0]}{ages[1]}_{y}_unit_nohs_school_highses"])
def go(args):
    r = subprocess.run([sys.executable, str(PF / "python" / "32_stacked_events.py"), "--B", B] + args, capture_output=True, text=True, cwd=PF)
    tag = args[args.index("--tag") + 1]; (LOG / f"{tag}.log").write_text(r.stdout + r.stderr); return tag, r.returncode
with ThreadPoolExecutor(3) as ex:
    for tag, rc in ex.map(go, runs): print(("ok   " if rc == 0 else "FAIL ") + tag, flush=True)
print("done")
