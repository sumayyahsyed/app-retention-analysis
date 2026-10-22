"""
run_analysis.py
---------------
One command that does the whole SQL pipeline:

  1. Loads data/users.csv and data/events.csv into a SQLite database
     (wealthview.db). SQLite is built into Python: nothing to install.
  2. Runs every file in sql/ in order.
  3. Prints each result and saves it to outputs/<query_name>.csv
     -> those CSVs are what you load into Tableau / Power BI.

Run:  python run_analysis.py
Requires: pandas   (pip install pandas)
"""

import glob
import os
import sqlite3
import time

import pandas as pd

ROOT = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(ROOT, "wealthview.db")
SQL_DIR = os.path.join(ROOT, "sql")
OUT_DIR = os.path.join(ROOT, "outputs")
os.makedirs(OUT_DIR, exist_ok=True)

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 20)
pd.set_option("display.max_rows", 60)

# ---- 1. Load raw CSVs -------------------------------------------------------
users_csv = os.path.join(ROOT, "data", "users.csv")
events_csv = os.path.join(ROOT, "data", "events.csv")
if not (os.path.exists(users_csv) and os.path.exists(events_csv)):
    raise SystemExit("Data not found. Run:  python data/generate_data.py  first.")

print("Loading CSVs into SQLite...")
con = sqlite3.connect(DB_PATH)
pd.read_csv(users_csv).to_sql("users", con, if_exists="replace", index=False)
pd.read_csv(events_csv).to_sql("events", con, if_exists="replace", index=False, chunksize=100_000)
con.commit()

# ---- 2. Run each SQL file in order -------------------------------------------
for path in sorted(glob.glob(os.path.join(SQL_DIR, "*.sql"))):
    name = os.path.splitext(os.path.basename(path))[0]
    with open(path) as f:
        sql = f.read()

    start = time.time()
    if "CREATE TABLE" in sql.upper():
        # setup scripts (cleaning) have several statements and no result
        con.executescript(sql)
        con.commit()
        print(f"\n=== {name} === (tables created in {time.time() - start:.1f}s)")
        continue

    df = pd.read_sql_query(sql, con)
    df.to_csv(os.path.join(OUT_DIR, f"{name}.csv"), index=False)
    print(f"\n=== {name} === ({len(df)} rows, {time.time() - start:.1f}s) -> outputs/{name}.csv")
    print(df.to_string(index=False) if len(df) <= 45 else df.head(45).to_string(index=False) + "\n...")

con.close()
print(f"\nDone. Database: {DB_PATH}\nDashboard-ready CSVs: {OUT_DIR}")
