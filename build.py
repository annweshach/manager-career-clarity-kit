"""Builds the dashboard (index.html) from a people-data CSV.

  python build.py                      -> generates SYNTHETIC data, then builds
  python build.py --csv path/to.csv    -> builds from your own HRIS export

Required columns:
  employee_id, manager_id, function, tenure_months,
  engagement_score (1-5), months_since_promotion, left_within_12m (0/1)

Synthetic mode: manager quality is a hidden variable with a MODERATE effect on
engagement, promotion wait and exits, plus function and tenure effects and
plenty of noise, so the picture looks like real people data (messy, partial
signal), not a perfect story.
"""
import argparse, csv, json, math, os, random

FUNCTIONS = ["Engineering", "Operations", "Sales"]
FUNC_ATTR_SHIFT = {"Engineering": 0.0, "Operations": 0.15, "Sales": 0.35}
N_MANAGERS = 60

def clip(x, lo, hi):
    return max(lo, min(hi, x))

def generate(path):
    random.seed(7)
    rows, emp_id = [], 1
    for m in range(1, N_MANAGERS + 1):
        fn = FUNCTIONS[(m - 1) % 3]
        quality = random.gauss(0, 1)                 # hidden manager quality
        team = random.choice([4, 5, 6, 7, 8, 9, 10, 12])
        for _ in range(team):
            tenure = int(clip(random.expovariate(1 / 28) + 3, 3, 84))
            engagement = clip(3.7 + 0.30 * quality + random.gauss(0, 0.75), 1, 5)
            msp = int(clip(random.gauss(19 - 2.5 * quality, 9), 2, 60))
            logit = (-1.75 - 0.40 * quality + 0.015 * (msp - 18)
                     + FUNC_ATTR_SHIFT[fn] + (0.35 if tenure < 12 else 0)
                     - 0.25 * (engagement - 3.7))
            left = 1 if random.random() < 1 / (1 + math.exp(-logit)) else 0
            rows.append({
                "employee_id": f"E{emp_id:04d}", "manager_id": f"M{m:02d}",
                "function": fn, "tenure_months": tenure,
                "engagement_score": round(engagement, 1),
                "months_since_promotion": msp, "left_within_12m": left,
            })
            emp_id += 1
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", help="use your own HRIS export instead of synthetic data")
    args = ap.parse_args()
    path = args.csv or "data/employees.csv"
    synthetic = args.csv is None
    if synthetic:
        generate(path)
    with open(path) as f:
        data = list(csv.DictReader(f))
    for r in data:
        r["tenure_months"] = int(r["tenure_months"])
        r["engagement_score"] = float(r["engagement_score"])
        r["months_since_promotion"] = int(r["months_since_promotion"])
        r["left_within_12m"] = int(r["left_within_12m"])
    with open("template.html") as f:
        html = f.read()
    html = html.replace("/*DATA*/[]", json.dumps(data, separators=(",", ":")))
    html = html.replace("/*SYNTH*/true", "true" if synthetic else "false")
    with open("index.html", "w") as f:
        f.write(html)
    print(f"{len(data)} employees -> index.html ({'synthetic' if synthetic else 'your data'})")

if __name__ == "__main__":
    main()
