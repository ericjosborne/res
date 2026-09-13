"""37_run_substate.py -- substate robustness runs: contamination-cleaned controls, treated-side local-dose splits, county-level local events."""
import subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
PF = Path(__file__).resolve().parents[1]; LOG = PF / "output" / "logs"; LOG.mkdir(exist_ok=True, parents=True)
B = sys.argv[1] if len(sys.argv) > 1 else "99"
runs = []
for y in ("enrolled", "employed", "log_wage", "neither"):
    for ages in (["16", "17"], ["18", "19"]):
        runs.append(["--ages", *ages, "--outcome", y, "--controls", "cleanlocal"])
        runs.append(["--ages", *ages, "--outcome", y, "--controls", "cleanlocal", "--treated", "nolocal"])
        runs.append(["--ages", *ages, "--outcome", y, "--controls", "cleanlocal", "--treated", "localonly"])
        runs.append(["--ages", *ages, "--outcome", y, "--controls", "cleanlocal", "--events", "local"])
def go(args):
    r = subprocess.run([sys.executable, str(PF / "python" / "32_stacked_events.py"), "--B", B] + args, capture_output=True, text=True, cwd=PF)
    line = next((l for l in r.stdout.splitlines() if l.startswith("mw_")), " ".join(args)); tag = line.split(":")[0]
    (LOG / f"{tag}.log").write_text(r.stdout + r.stderr); return tag, r.returncode
with ThreadPoolExecutor(4) as ex:
    for tag, rc in ex.map(go, runs): print(("ok   " if rc == 0 else "FAIL ") + tag, flush=True)
print("done")
