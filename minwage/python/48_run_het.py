"""48_run_het.py -- heterogeneity by sex (girls / boys) and by race (non-Hispanic white / all other), unit design, 2010+
events: the eight outcomes of Sections 5.2 and 5.4 (four school-work shares, enrollment, employment, log hourly wage, log
weekly earnings) by age bracket.  Tags mw_<ages>_<y>_unit_{female,male,white,nonwhite}."""
import subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
PF = Path(__file__).resolve().parents[1]; LOG = PF / "output" / "logs"; LOG.mkdir(exist_ok=True, parents=True)
B = sys.argv[1] if len(sys.argv) > 1 else "99"
SPLITS = [("female==1", "female"), ("female==0", "male"), ("white==1", "white"), ("white==0", "nonwhite")]
runs = []
for y in ("enr_emp", "enr_only", "emp_only", "neither", "enrolled", "employed", "log_wage", "log_earnweek"):
    for ages in (["16", "17"], ["18", "19"], ["16", "19"]):
        for q, g in SPLITS:
            runs.append(["--ages", *ages, "--outcome", y, "--events", "unit", "--query", q, "--tag", f"mw_{ages[0]}{ages[1]}_{y}_unit_{g}"])
def go(args):
    r = subprocess.run([sys.executable, str(PF / "python" / "32_stacked_events.py"), "--B", B] + args, capture_output=True, text=True, cwd=PF)
    tag = args[args.index("--tag") + 1]; (LOG / f"{tag}.log").write_text(r.stdout + r.stderr); return tag, r.returncode
with ThreadPoolExecutor(4) as ex:
    for tag, rc in ex.map(go, runs): print(("ok   " if rc == 0 else "FAIL ") + tag, flush=True)
print("done")
