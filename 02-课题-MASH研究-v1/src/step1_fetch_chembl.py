# -*- coding: utf-8 -*-
"""
Step 1: Fetch real FXR activity data from ChEMBL REST API.
Target verification + full IC50 download (paginated).
"""
import json
import time
import requests
import pandas as pd

BASE = "https://www.ebi.ac.uk/chembl/api/data"
OUT = "D:/zcode-workspace/mash_research/data/chembl"

def get_json(url, params=None, retries=4):
    for i in range(retries):
        try:
            r = requests.get(url, params=params, timeout=60)
            if r.status_code == 200:
                return r.json()
            print(f"  HTTP {r.status_code} for {url} {params}")
        except Exception as e:
            print(f"  retry {i+1}: {str(e)[:120]}")
        time.sleep(5 * (i + 1))
    raise RuntimeError(f"failed: {url} {params}")

# ---- 1. verify target identity ----
tgt = get_json(f"{BASE}/target/CHEMBL2047.json")
print("=== Target verification ===")
print("target_chembl_id:", tgt["target_chembl_id"])
print("pref_name:", tgt["pref_name"])
print("target_type:", tgt["target_type"])
print("organism:", tgt["organism"])
for tc in tgt.get("target_components", []):
    c = tc.get("component", tc)
    print("uniprot:", c.get("accession"), "| type:", c.get("accession_type"),
          "| desc:", str(c.get("target_component_description"))[:60])

# ---- 2. count activities (endpoint does not support standard_type filter; use paged totals) ----
print("\n(activity/count.json does not accept these filters; total comes from pagination)")

# ---- 3. download all IC50 activities (paginated) ----
rows, offset, limit = [], 0, 1000
while True:
    js = get_json(f"{BASE}/activity.json",
                  {"target_chembl_id": "CHEMBL2047", "assay_type": "B",
                   "standard_type": "IC50", "format": "json",
                   "limit": limit, "offset": offset})
    acts = js.get("activities", [])
    rows.extend(acts)
    print(f"fetched offset={offset}, got {len(acts)} (total so far {len(rows)})")
    if len(acts) < limit:
        break
    offset += limit
    time.sleep(1)

df = pd.DataFrame(rows)
keep = ["activity_id", "assay_chembl_id", "assay_type", "assay_description", "assay_organism",
        "assay_variant_accession", "molecule_chembl_id", "canonical_smiles",
        "standard_type", "standard_relation", "standard_value", "standard_units",
        "pchembl_value", "potential_duplicate", "data_validity_comment"]
df = df[[c for c in keep if c in df.columns]]
df.to_csv(f"{OUT}/fxr_chembl2047_ic50_raw.csv", index=False)
print("\nSaved raw:", df.shape)
print(df["standard_relation"].value_counts(dropna=False))
print(df["standard_units"].value_counts(dropna=False))
print("with SMILES:", df["canonical_smiles"].notna().sum())
print("with value:", df["standard_value"].notna().sum())
