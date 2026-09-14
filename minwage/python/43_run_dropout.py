"""43_run_dropout.py -- high school dropout (not enrolled, no diploma or GED), Smith's (2021) outcome: main and by family income."""
import subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
PF = Path(__file__).resolve().parents[1]; LOG = PF / "output" / "logs"
B = sys.argv[1] if len(sys.argv) > 1 else "99"
runs = []
for ages in (["16", "17"], ["18", "19"], ["16", "18"], ["16", "19"]):
    a = f"{ages[0]}{ages[1]}"
    runs.append(["--ages", *ages, "--outcome", "dropout", "--events", "unit"])
    runs.append(["--ages", *ages, "--outcome", "dropout", "--events", "post2009"])
    runs.append(["--ages", *ages, "--outcome", "dropout", "--events", "unit", "--query", "faminc<=740", "--tag", f"mw_{a}_dropout_unit_lowses"])
    runs.append(["--ages", *ages, "--outcome", "dropout", "--events", "unit", "--query", "faminc>=820 & faminc<900", "--tag", f"mw_{a}_dropout_unit_highses"])
    runs.append(["--ages", *ages, "--outcome", "dropout", "--events", "unit", "--ses", "rel_low", "--tag", f"mw_{a}_dropout_unit_lowsesrel"])
    runs.append(["--ages", *ages, "--outcome", "dropout", "--events", "unit", "--ses", "rel_high", "--tag", f"mw_{a}_dropout_unit_highsesrel"])
def go(args):
    r = subprocess.run([sys.executable, str(PF / "python" / "32_stacked_events.py"), "--B", B] + args, capture_output=True, text=True, cwd=PF)
    line = next((l for l in r.stdout.splitlines() if l.startswith("mw_")), ""); tag = args[args.index("--tag") + 1] if "--tag" in args else line.split(":")[0]
    (LOG / f"{tag}.log").write_text(r.stdout + r.stderr); return tag, r.returncode
with ThreadPoolExecutor(4) as ex:
    for tag, rc in ex.map(go, runs): print(("ok   " if rc == 0 else "FAIL ") + tag, flush=True)
print("done")
