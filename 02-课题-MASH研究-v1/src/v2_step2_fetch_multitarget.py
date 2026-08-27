# -*- coding: utf-8 -*-
"""
V2 Step2: fetch ChEMBL activity data for 12 liver-relevant targets (QSAR training).
Targets anchored by: disease modules (HMGCR/SQLE/FDFT1 from module13; PLIN2/FGF21
adjacent metabolic axis) + genetic targets (agents verifying) + prior pipeline
(FXR/THRB/ACC). assay_type=B, exact relation, nM units, dedup by canonical SMILES.
"""
import json, os, time
import numpy as np
import pandas as pd
import requests
from rdkit import Chem, RDLogger

RDLogger.DisableLog('rdApp.*')
D = "D:/zcode-workspace/mash_research"
OUT = f"{D}/data/v2"
os.makedirs(OUT, exist_ok=True)
BASE = "https://www.ebi.ac.uk/chembl/api/data"

TARGETS = {
    "CHEMBL2047": "FXR", "CHEMBL1947": "THRb", "CHEMBL3351": "ACC1",
    "CHEMBL4829": "ACC2", "CHEMBL1957": "FASN", "CHEMBL4016": "HMGCR",
    "CHEMBL3559": "SQLE", "CHEMBL2891": "DGAT2",
}
# verify/correct IDs via API search by target name first
NAME2TID = {}
for name, tid in [("Fatty acid synthase", "FASN"), ("Squalene monooxygenase", "SQLE"),
                  ("HMG-CoA reductase", "HMGCR"), ("Diacylglycerol O-acyltransferase 2", "DGAT2"),
                  ("Squalene synthase", "FDFT1"), ("Stearoyl-CoA desaturase", "SCD"),
                  ("PPAR gamma", "PPARG"), ("Liver X receptor alpha", "LXRa"),
                  ("Acetyl-CoA carboxylase 1", "ACC1"), ("Acetyl-CoA carboxylase 2", "ACC2")]:
    try:
        r = requests.get(f"{BASE}/target/search.json", params={"q": name, "limit": 5}, timeout=60)
        for t in r.json().get("targets", []):
            if t.get("target_type") == "SINGLE PROTEIN" and t.get("organism") == "Homo sapiens":
                NAME2TID[tid] = t["target_chembl_id"]
                break
    except Exception as e:
        print("search fail", name, str(e)[:60])
    time.sleep(0.3)
print("resolved:", NAME2TID)

TARGETS = {"CHEMBL2047": "FXR", "CHEMBL1947": "THRb"}
for nm, tid in NAME2TID.items():
    TARGETS[tid] = nm
print("final targets:", TARGETS)

def fetch_target(tid, nm):
    rows, offset = [], 0
    for st in ["IC50", "Ki", "EC50"]:
        offset = 0
        while True:
            r = requests.get(f"{BASE}/activity.json", params={
                "target_chembl_id": tid, "assay_type": "B", "standard_type": st,
                "format": "json", "limit": 1000, "offset": offset}, timeout=90)
            if r.status_code != 200:
                break
            acts = r.json().get("activities", [])
            rows.extend([a for a in acts if a.get("standard_relation") == "="
                         and a.get("standard_units") == "nM"
                         and a.get("canonical_smiles") and a.get("standard_value")])
            if len(acts) < 1000:
                break
            offset += 1000
            time.sleep(0.25)
    df = pd.DataFrame(rows)
    if not len(df):
        print(f"{nm}({tid}): NO DATA"); return None
    df = df[["canonical_smiles", "standard_value", "standard_type"]].copy()
    df["standard_value"] = df["standard_value"].astype(float)
    df = df[(df.standard_value > 0)]
    df["pAct"] = 9.0 - np.log10(df.standard_value)
    df = df.groupby("canonical_smiles").agg(pAct=("pAct", "mean"), n=("pAct", "size"),
                                            types=("standard_type", lambda x: ",".join(set(x)))).reset_index()
    df["target"] = nm; df["tid"] = tid
    print(f"{nm}({tid}): {len(df)} unique compounds")
    return df

allrows = []
for tid, nm in TARGETS.items():
    df = fetch_target(tid, nm)
    if df is not None:
        df.to_csv(f"{OUT}/chembl_{nm}_{tid}.csv", index=False)
        allrows.append(df)
    time.sleep(0.5)
big = pd.concat(allrows, ignore_index=True)
big.to_csv(f"{OUT}/chembl_multitarget_all.csv", index=False)
print("TOTAL:", len(big), "across", big.target.nunique(), "targets")
print(big.groupby("target").size().sort_values(ascending=False).to_string())
