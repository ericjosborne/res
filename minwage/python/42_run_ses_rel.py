"""42_run_ses_rel.py -- SES heterogeneity with a within-year median split of the family income category (--ses rel_low / rel_high)."""
import subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
PF = Path(__file__).resolve().parents[1]; LOG = PF / "output" / "logs"
B = sys.argv[1] if len(sys.argv) > 1 else "99"
runs = []
for y in ("log_wage", "enrolled", "employed", "enr_emp", "enr_only", "emp_only", "neither", "hours"):
    for ages in (["16", "17"], ["18", "19"], ["16", "19"]):
        for ses, k in (("rel_low", "lowsesrel"), ("rel_high", "highsesrel")):
            runs.append(["--ages", *ages, "--outcome", y, "--events", "unit", "--ses", ses, "--tag", f"mw_{ages[0]}{ages[1]}_{y}_unit_{k}"])
def go(args):
    r = subprocess.run([sys.executable, str(PF / "python" / "32_stacked_events.py"), "--B", B] + args, capture_output=True, text=True, cwd=PF)
    tag = args[args.index("--tag") + 1]; (LOG / f"{tag}.log").write_text(r.stdout + r.stderr); return tag, r.returncode
with ThreadPoolExecutor(4) as ex:
    for tag, rc in ex.map(go, runs): print(("ok   " if rc == 0 else "FAIL ") + tag, flush=True)
print("done")
