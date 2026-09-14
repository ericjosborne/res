"""40_run_ses.py -- heterogeneity by socioeconomic standing (CPS family income category, nominal): low = below $50,000
(FAMINC <= 740), high = $50,000 or more (820-843); missing/refused (995+) excluded.  Unit design, 2010+ events."""
import subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
PF = Path(__file__).resolve().parents[1]; LOG = PF / "output" / "logs"; LOG.mkdir(exist_ok=True, parents=True)
B = sys.argv[1] if len(sys.argv) > 1 else "99"
runs = []
for y in ("log_wage", "enrolled", "employed", "enr_emp", "enr_only", "emp_only", "neither", "hours"):
    for ages in (["16", "17"], ["18", "19"], ["16", "19"]):
        runs.append(["--ages", *ages, "--outcome", y, "--events", "unit", "--query", "faminc<=740", "--tag", f"mw_{ages[0]}{ages[1]}_{y}_unit_lowses"])
        runs.append(["--ages", *ages, "--outcome", y, "--events", "unit", "--query", "faminc>=820 & faminc<900", "--tag", f"mw_{ages[0]}{ages[1]}_{y}_unit_highses"])
def go(args):
    r = subprocess.run([sys.executable, str(PF / "python" / "32_stacked_events.py"), "--B", B] + args, capture_output=True, text=True, cwd=PF)
    tag = args[args.index("--tag") + 1]; (LOG / f"{tag}.log").write_text(r.stdout + r.stderr); return tag, r.returncode
with ThreadPoolExecutor(4) as ex:
    for tag, rc in ex.map(go, runs): print(("ok   " if rc == 0 else "FAIL ") + tag, flush=True)
print("done")
