"""Build the messy student file (people_raw.csv) from the clean answer key.

Every corruption is logged to injected_errors.csv so the instructor can check
student work. Run from this directory: python make_raw.py
"""
import csv
import random

random.seed(2026)

SEX = {"male": 1, "female": 2}
RACE = {"white": 1, "black": 2, "asian": 3, "hispanic": 4, "other": 5}
MARITAL = {"never married": 1, "married": 2, "divorced": 3, "widowed": 4}
EDUC = {"less than high school": 1, "high school": 2, "some college": 3,
        "bachelor's": 4, "master's": 5, "doctorate": 6}

# Text variants that a sloppy data-entry process might produce instead of codes
SEX_TXT = {"male": ["M", "male", "Male ", "m"], "female": ["F", "female", " Female", "f"]}
RACE_TXT = {"white": ["White", "white "], "black": ["Black", "African American"],
            "asian": ["Asian", "asian"], "hispanic": ["Hispanic", "Latino", "hispanic "],
            "other": ["Other", "other"]}
MARITAL_TXT = {"never married": ["Single", "never married"], "married": ["Married", "married "],
               "divorced": ["Divorced"], "widowed": ["Widowed"]}
EDUC_TXT = {"less than high school": ["no diploma", "<HS"], "high school": ["HS", "high school", "GED"],
            "some college": ["some college", "Some College"], "bachelor's": ["BA", "Bachelors", "B.S."],
            "master's": ["MA", "Masters"], "doctorate": ["PhD", "doctorate"]}

with open("people_clean.csv") as f:
    clean = list(csv.DictReader(f))

log = []


def note(rid, var, true, raw, problem):
    log.append({"id": rid, "variable": var, "true_value": true, "raw_value": raw, "problem": problem})


raw_rows = []
for r in clean:
    rid = r["id"]
    out = {
        "ID": rid,
        "Age": r["age"],
        "Sex": SEX[r["sex"]],
        "Race": RACE[r["race"]],
        "Marital": MARITAL[r["marital_status"]],
        "Educ": EDUC[r["education"]],
        "Income": r["income"],
        "Parents' Income": r["parents_income"],
        "IQ": r["iq"],
    }

    # Categorical variables: ~12% entered as text labels instead of numeric codes
    for col, key, txt in [("Sex", "sex", SEX_TXT), ("Race", "race", RACE_TXT),
                          ("Marital", "marital_status", MARITAL_TXT), ("Educ", "education", EDUC_TXT)]:
        if random.random() < 0.12:
            out[col] = random.choice(txt[r[key]])
            note(rid, col, r[key], out[col], "text label instead of numeric code")

    # Income: currency formatting, "k" shorthand, decimals
    u = random.random()
    inc = int(r["income"])
    if u < 0.15:
        out["Income"] = f"${inc:,}"
        note(rid, "Income", inc, out["Income"], "dollar sign / thousands separator")
    elif u < 0.20:
        out["Income"] = f"{inc / 1000:g}k"
        note(rid, "Income", inc, out["Income"], "'k' shorthand")
    elif u < 0.25:
        out["Income"] = f"{inc}.00"
        note(rid, "Income", inc, out["Income"], "decimal formatting")

    # Parents' income: a few entered in thousands rather than dollars
    if random.random() < 0.05:
        out["Parents' Income"] = f"{int(r['parents_income']) / 1000:g}"
        note(rid, "Parents' Income", r["parents_income"], out["Parents' Income"],
             "entered in thousands of dollars")

    # Age: occasional "yrs" suffix
    if random.random() < 0.05:
        out["Age"] = f"{r['age']} yrs"
        note(rid, "Age", r["age"], out["Age"], "units text in numeric field")

    raw_rows.append(out)


def pick(n, exclude=()):
    pool = [i for i in range(len(raw_rows)) if i not in exclude]
    return random.sample(pool, n)


used = set()

# Documented missing-value codes (-8 refused, -9 don't know) and blanks
for col, n in [("Income", 6), ("Parents' Income", 9), ("IQ", 5), ("Age", 2)]:
    for i in pick(n, used):
        used.add(i)
        true = raw_rows[i][col]
        raw_rows[i][col] = random.choice(["-8", "-9", ""])
        note(raw_rows[i]["ID"], col, true, raw_rows[i][col] or "(blank)",
             "missing (codebook code or blank)")

# Out-of-range / implausible values (data-entry typos)
typo_specs = [
    ("Age", lambda v: str(int(v) * 10), "extra digit typed"),
    ("Age", lambda v: "999", "undocumented missing code (999)"),
    ("Age", lambda v: str(int(v))[0], "digit dropped"),
    ("Income", lambda v: "-" + v, "negative sign"),
    ("Income", lambda v: v + "0", "extra zero typed"),
    ("IQ", lambda v: "999", "undocumented missing code (999)"),
    ("IQ", lambda v: "0", "zero entered for unknown"),
    ("IQ", lambda v: v[:-1] if len(v) == 3 else v + "0", "digit dropped / added"),
]
for col, f, why in typo_specs:
    i = pick(1, used)[0]
    used.add(i)
    base = raw_rows[i][col].replace(" yrs", "")
    if not base.lstrip("-").isdigit():
        base = clean[i][col.lower()]
    raw_rows[i][col] = f(base)
    note(raw_rows[i]["ID"], col, clean[i][col.lower()], raw_rows[i][col], why)

# Logical inconsistencies across variables
young = [k for k in range(len(raw_rows)) if k not in used and int(clean[k]["age"]) < 25]
if young:
    k = young[0]; used.add(k)
    raw_rows[k]["Educ"] = "6"
    note(raw_rows[k]["ID"], "Educ", clean[k]["education"], "6", f"doctorate at age {clean[k]['age']}")
    if len(young) > 1:
        k = young[1]; used.add(k)
        raw_rows[k]["Marital"] = "4"
        note(raw_rows[k]["ID"], "Marital", clean[k]["marital_status"], "4",
             f"widowed at age {clean[k]['age']} (possible but worth flagging)")

# One ID collision: a different person entered with an existing ID
i, j = pick(2)
true_id = raw_rows[j]["ID"]
raw_rows[j]["ID"] = raw_rows[i]["ID"]
note(true_id, "ID", true_id, raw_rows[j]["ID"], "ID mistyped; collides with another respondent")


# Exact duplicate records, inserted at random positions
for i in pick(4):
    dup = dict(raw_rows[i])
    raw_rows.insert(random.randrange(len(raw_rows)), dup)
    note(dup["ID"], "(row)", "", "", "exact duplicate record")

with open("../people_raw.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(raw_rows[0].keys()))
    w.writeheader()
    w.writerows(raw_rows)

with open("injected_errors.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["id", "variable", "true_value", "raw_value", "problem"])
    w.writeheader()
    w.writerows(sorted(log, key=lambda d: int(d["id"])))

print(len(raw_rows), "raw rows;", len(log), "logged problems")
