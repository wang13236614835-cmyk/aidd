# -*- coding: utf-8 -*-
"""
V2 Step3: signature-reversal repurposing (CMap logic via Enrichr LINCS L1000).
Disease signature: GSE135251 NASH-vs-Normal DEGs (up/down).
Reversal evidence A: disease-DOWN genes vs library LINCS_L1000_Chem_Pert_up
  (compound pushes those genes UP)
Reversal evidence B: disease-UP genes vs library LINCS_L1000_Chem_Pert_down
  (compound pushes those genes DOWN)
Connectivity-style reversal score from Enrichr combined scores of both sides.
"""
import requests
import numpy as np
import pandas as pd

D = "D:/zcode-workspace/mash_research"
RES = f"{D}/results/v2"
deg = pd.read_csv(f"{D}/data/geo/deg_NASH_vs_Normal.csv", index_col=0)
up = deg[(deg.padj < 0.05) & (deg.log2FC > 0.5)].index.tolist()
dn = deg[(deg.padj < 0.05) & (deg.log2FC < -0.5)].index.tolist()
print(f"signature: up={len(up)} down={len(dn)}")

def enrich(genes, lib, tag):
    r = requests.post("https://maayanlab.cloud/Enrichr/addList",
                      files={"list": (f"{tag}.txt", "\n".join(genes)),
                             "description": ("", "mash-signature")}, timeout=120)
    uid = r.json()["userListId"]
    r2 = requests.get("https://maayanlab.cloud/Enrichr/enrich",
                      params={"userListId": uid, "library": lib}, timeout=180)
    rows = r2.json()[lib]
    # cols: rank term overlap p adjust. p-old combined score genes
    return {row[1]: dict(p=float(row[3]), padj=float(row[4]), comb=float(row[6]),
                         overlap=row[2]) for row in rows}

A = enrich(dn, "LINCS_L1000_Chem_Pert_up", "down")   # reversal half A
B = enrich(up, "LINCS_L1000_Chem_Pert_down", "up")   # reversal half B
print(f"library A hits: {len(A)} | library B hits: {len(B)}")

rows = []
common = set(A) & set(B)
for term in set(A) | set(B):
    a, b = A.get(term), B.get(term)
    if a and b:  # full reversal requires both sides
        rows.append(dict(perturbagen=term,
                         comb_A=a["comb"], p_A=a["p"], ov_A=a["overlap"],
                         comb_B=b["comb"], p_B=b["p"], ov_B=b["overlap"],
                         reversal_score=round(np.sqrt(max(a["comb"], 0) * max(b["comb"], 0)), 1)))
rev = pd.DataFrame(rows).sort_values("reversal_score", ascending=False)
rev.to_csv(f"{RES}/lincs_signature_reversal.csv", index=False)
print(f"\nfull-reversal perturbagens (both sides): {len(rev)}")
print(rev.head(30).to_string(index=False))
# also single-side strong hits for reference
onlyA = pd.DataFrame([dict(perturbagen=t, comb=v["comb"], p=v["p"], side="A(dn-disease vs up-lib)")
                      for t, v in A.items() if t not in common]).sort_values("comb", ascending=False)
onlyA.head(100).to_csv(f"{RES}/lincs_sideA_only_top100.csv", index=False)
