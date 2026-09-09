"""
90_ipums_extract.py -- request the full-power extract for the paper.

NOT RUN in the build environment (api.ipums.org is blocked there).  Run
locally with an IPUMS API key:

    pip install ipumspy
    export IPUMS_API_KEY=...
    python code/90_ipums_extract.py            # submits, waits, downloads to data/raw/ipums/

Samples (IPUMS USA):
  us1980a   1980 5% state sample            (replicates Angrist-Evans 1998 exactly)
  us1990a   1990 5% sample
  us2000a   2000 5% sample
  us2005a - us2023a  ACS 1-year samples     (2020 is the experimental sample; keep but flag)

Variables: household weights and identifiers, person weights, relationship,
sex, age, marital status, race, Hispanic origin, education, fertility
(children ever born where available), employment status, weeks worked
(intervalled after 2007 -> use WKSWORK2), usual hours, labour income, and the
IPUMS family-interrelationship pointers (MOMLOC, POPLOC, NCHILD, ELDCH, YNGCH,
and NCHLT5), which make the mother-child linkage exact.

The output of 91_clean_ipums.py is in the same harmonised layout as the 1980
and CPS files, so 03_analysis.py runs unchanged with `--ipums`.
"""
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "raw" / "ipums"
OUT.mkdir(parents=True, exist_ok=True)

SAMPLES = ["us1980a", "us1990a", "us2000a"] + [f"us{y}a" for y in range(2005, 2024)]
VARIABLES = [
    "YEAR", "SAMPLE", "SERIAL", "HHWT", "STATEFIP", "METRO", "PERNUM", "PERWT",
    "FAMUNIT", "MOMLOC", "POPLOC", "SPLOC", "NCHILD", "NCHLT5", "ELDCH", "YNGCH",
    "RELATE", "SEX", "AGE", "MARST", "RACE", "HISPAN", "EDUC", "EDUCD",
    "EMPSTAT", "LABFORCE", "WKSWORK1", "WKSWORK2", "UHRSWORK", "INCWAGE", "INCEARN",
    "INCTOT", "FTOTINC",
]


def main():
    try:
        from ipumspy import IpumsApiClient, UsaExtract
    except ImportError:
        sys.exit("pip install ipumspy")
    key = os.environ.get("IPUMS_API_KEY")
    if not key:
        sys.exit("set IPUMS_API_KEY")
    client = IpumsApiClient(key)
    extract = UsaExtract(SAMPLES, VARIABLES,
                         description="Angrist-Evans same-sex IV, 1980-2023",
                         data_format="csv")
    client.submit_extract(extract)
    print("submitted extract", extract.extract_id)
    client.wait_for_extract(extract, inital_wait_time=30, max_wait_time=600, timeout=6 * 3600)
    client.download_extract(extract, download_dir=OUT)
    print("downloaded to", OUT)


if __name__ == "__main__":
    main()
