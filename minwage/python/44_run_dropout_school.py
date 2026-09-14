"""44_run_dropout_school.py -- dropout outcome in school months only (September-May), since summer non-attendance inflates
'not enrolled' in the basic monthly enrollment item; unit design, main and by family income."""
import subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
PF = Path(__file__).resolve().parents[1]; LOG = PF / "output" / "logs"
B = sys.argv[1] if len(sys.argv) > 1 else "99"
Q = "month<=5 | month>=9"
runs = []
for ages in (["16", "17"], ["18", "19"], ["16", "18"], ["16", "19"]):
    a = f"{ages[0]}{ages[1]}"
    runs.append(["--ages", *ages, "--outcome", "dropout", "--events", "unit", "--query", Q, "--tag", f"mw_{a}_dropout_unit_school"])
    runs.append(["--ages", *ages, "--outcome", "dropout", "--events", "unit", "--query", f"({Q}) & faminc<=740", "--tag", f"mw_{a}_dropout_unit_school_lowses"])
    runs.append(["--ages", *ages, "--outcome", "dropout", "--events", "unit", "--query", f"({Q}) & faminc>=820 & faminc<900", "--tag", f"mw_{a}_dropout_unit_school_highses"])
    runs.append(["--ages", *ages, "--outcome", "dropout", "--events", "unit", "--query", Q, "--ses", "rel_low", "--tag", f"mw_{a}_dropout_unit_school_lowsesrel"])
    runs.append(["--ages", *ages, "--outcome", "dropout", "--events", "unit", "--query", Q, "--ses", "rel_high", "--tag", f"mw_{a}_dropout_unit_school_highsesrel"])
    runs.append(["--ages", *ages, "--outcome", "enrolled", "--events", "unit", "--query", f"({Q}) & faminc<=740", "--tag", f"mw_{a}_enrolled_unit_school_lowses"])
    runs.append(["--ages", *ages, "--outcome", "enrolled", "--events", "unit", "--query", f"({Q}) & faminc>=820 & faminc<900", "--tag", f"mw_{a}_enrolled_unit_school_highses"])
def go(args):
    r = subprocess.run([sys.executable, str(PF / "python" / "32_stacked_events.py"), "--B", B] + args, capture_output=True, text=True, cwd=PF)
    tag = args[args.index("--tag") + 1]; (LOG / f"{tag}.log").write_text(r.stdout + r.stderr); return tag, r.returncode
with ThreadPoolExecutor(4) as ex:
    for tag, rc in ex.map(go, runs): print(("ok   " if rc == 0 else "FAIL ") + tag, flush=True)
print("done")
