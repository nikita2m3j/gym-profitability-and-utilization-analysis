import os
import numpy as np
import pandas as pd
from datetime import datetime

SEED = 42
rng = np.random.default_rng(SEED)

OUT_DIR = "data/raw"
os.makedirs(OUT_DIR, exist_ok=True)

# ---------- Settings ----------
start_date = pd.Timestamp("2023-01-01")
end_date = pd.Timestamp("2024-12-31")

N_CUSTOMERS = 2500
CAPACITY = 180

# ---------- Plans ----------
plans = pd.DataFrame([
    {"plan_id": 1, "plan_name": "Basic", "monthly_price": 2000, "access_type": "full"},
    {"plan_id": 2, "plan_name": "Premium", "monthly_price": 4500, "access_type": "full"},
    {"plan_id": 3, "plan_name": "Off-Peak", "monthly_price": 1000, "access_type": "off_peak"},
    {"plan_id": 4, "plan_name": "Student", "monthly_price": 1200, "access_type": "full"},
])

# ---------- Fixed costs ----------
fixed_costs = pd.DataFrame([
    {"cost_type": "rent", "monthly_cost": 300000},
    {"cost_type": "staff", "monthly_cost": 450000},
    {"cost_type": "utilities", "monthly_cost": 80000},
    {"cost_type": "marketing", "monthly_cost": 70000},
])

# ---------- Customers ----------
customer_ids = np.arange(1, N_CUSTOMERS + 1)

signup_days = rng.integers(0, (end_date - start_date).days + 1, size=N_CUSTOMERS)
signup_dates = (start_date + pd.to_timedelta(signup_days, unit="D")).normalize()

segments = rng.choice(["student", "adult", "senior"], size=N_CUSTOMERS, p=[0.22, 0.68, 0.10])
gender = rng.choice(["M", "F"], size=N_CUSTOMERS, p=[0.52, 0.48])

age = np.where(
    segments == "student",
    rng.integers(18, 26, size=N_CUSTOMERS),
    np.where(segments == "adult", rng.integers(26, 56, size=N_CUSTOMERS), rng.integers(56, 71, size=N_CUSTOMERS)),
)

customers = pd.DataFrame({
    "customer_id": customer_ids,
    "signup_date": signup_dates,
    "age": age,
    "gender": gender,
    "segment": segments,
})

# ---------- Subscriptions ----------
plan_probs = {
    "student": np.array([0.25, 0.15, 0.10, 0.50]),
    "adult":   np.array([0.55, 0.30, 0.12, 0.03]),
    "senior":  np.array([0.55, 0.15, 0.25, 0.05]),
}

plan_ids = plans["plan_id"].to_numpy()
plan_choice = [
    int(rng.choice(plan_ids, p=plan_probs[s] / plan_probs[s].sum()))
    for s in customers["segment"]
]

plan_churn = {1: 0.045, 2: 0.030, 3: 0.060, 4: 0.070}

subs = []
sub_id = 1

for cid, sdate, pid in zip(customers["customer_id"], customers["signup_date"], plan_choice):
    start = sdate
    months_alive = 1
    while rng.random() > plan_churn[pid] and months_alive < 24:
        months_alive += 1

    end = start + pd.DateOffset(months=months_alive)
    if end > end_date:
        end = None
        status = "active"
    else:
        status = "canceled"

    subs.append({
        "subscription_id": sub_id,
        "customer_id": cid,
        "plan_id": pid,
        "start_date": start,
        "end_date": end,
        "status": status,
    })
    sub_id += 1

subscriptions = pd.DataFrame(subs)

# ---------- Addons ----------
addons = []
for cid, seg in zip(customers["customer_id"], customers["segment"]):
    if rng.random() < (0.35 if seg == "student" else 0.28):
        addons.append({"customer_id": cid, "addon_type": "drinks", "monthly_price": 400})
    if rng.random() < (0.25 if seg == "adult" else 0.18):
        addons.append({"customer_id": cid, "addon_type": "sauna", "monthly_price": 1000})
    if rng.random() < 0.08:
        addons.append({"customer_id": cid, "addon_type": "personal_training", "monthly_price": 8000})

addons = pd.DataFrame(addons)

# ---------- Visits ----------
plan_access = plans.set_index("plan_id")["access_type"].to_dict()

def sample_checkin_time(access):
    if access == "off_peak":
        hours = np.array([7,8,9,10,11,12,13,14,15,16])
        probs = np.array([1]*10, dtype=float)
    else:
        hours = np.array([6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21])
        probs = np.array([1]*16, dtype=float)

    probs /= probs.sum()
    return int(rng.choice(hours, p=probs)), int(rng.integers(0, 60))

visits = []
visit_id = 1

for _, sub in subscriptions.iterrows():
    cid = sub.customer_id
    pid = sub.plan_id
    access = plan_access[pid]

    start = sub.start_date
    end = sub.end_date if sub.end_date else end_date

    d = start
    while d <= end:
        if rng.random() < 0.35:
            hour, minute = sample_checkin_time(access)
            duration = int(np.clip(rng.normal(70, 25), 30, 150))
            checkin = datetime(d.year, d.month, d.day, hour, minute)
            checkout = checkin + pd.Timedelta(minutes=duration)

            visits.append({
                "visit_id": visit_id,
                "customer_id": cid,
                "checkin_ts": checkin,
                "checkout_ts": checkout,
                "duration_min": duration,
            })
            visit_id += 1
        d += pd.Timedelta(days=1)

visits = pd.DataFrame(visits)

# ---------- Save ----------
customers.to_csv(f"{OUT_DIR}/customers.csv", index=False)
plans.to_csv(f"{OUT_DIR}/plans.csv", index=False)
subscriptions.to_csv(f"{OUT_DIR}/subscriptions.csv", index=False)
addons.to_csv(f"{OUT_DIR}/addons.csv", index=False)
visits.to_csv(f"{OUT_DIR}/visits.csv", index=False)
fixed_costs.to_csv(f"{OUT_DIR}/fixed_costs.csv", index=False)

print("DONE")
print("customers:", len(customers))
print("subscriptions:", len(subscriptions))
print("visits:", len(visits))
print("addons:", len(addons))
