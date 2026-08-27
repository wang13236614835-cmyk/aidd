# -*- coding: utf-8 -*-
"""第三轮圆桌修复 · 数据存档包：p值补档/CID差异点名/requirements/数据库快照/图源数据。"""
import json
import subprocess
import sys
import urllib.request
import numpy as np
import pandas as pd
from scipy import stats

D = "D:/zcode-workspace/mash_research"
V6 = f"{D}/results/v6"
PCN = "D:/zcode-workspace/paper"

# ---------- 1. baseline_recheck 补 p 值 ----------
j = json.load(open(f"{D}/results/tables/gnn_metrics_v2.json", encoding="utf-8"))
rc = json.load(open(f"{V6}/baseline_recheck.json", encoding="utf-8"))
df = pd.read_csv(f"{D}/data/chembl/fxr_final_dataset.csv")
from rdkit import Chem, RDLogger
from rdkit.Chem.Scaffolds import MurckoScaffold
from rdkit.Chem import rdFingerprintGenerator
RDLogger.DisableLog("rdApp.*")
df["scaffold"] = df["std_smiles"].apply(
    lambda s: MurckoScaffold.MurckoScaffoldSmiles(smiles=s, includeChirality=False))

def scaffold_split_idx(df):
    groups = df.groupby("scaffold").indices
    order = sorted(groups.keys(), key=lambda s: -len(groups[s]))
    n = len(df); tr, va, te = [], [], []
    for s in order:
        tgt = tr if len(tr) / n < 0.8 else (va if len(va) / n < 0.1 else te)
        tgt.extend(groups[s])
    return np.array(tr), np.array(va), np.array(te)

tr, va, te = scaffold_split_idx(df)
n_te = len(te)
for key in ["scaffold_RF", "scaffold_XGB"]:
    rho = rc["recheck"][key]["Spearman"]
    t = rho * np.sqrt((n_te - 2) / (1 - rho ** 2))
    p = 2 * (1 - stats.t.cdf(abs(t), n_te - 2))
    rc["recheck"][key]["Spearman_p"] = float(f"{p:.2e}")
    print(key, "rho=%.4f p=%.2e n=%d" % (rho, p, n_te))
rc["note_pvalues"] = "scaffold-split Spearman p-values recomputed from v6c recheck (n=34)"
json.dump(rc, open(f"{V6}/baseline_recheck.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)

# ---------- 2. CID 129/131 差异点名存档 ----------
old = pd.read_csv(f"{D}/results/tables/np_fxr_predictions.csv")[["name", "cid", "smiles"]]
new = pd.read_csv(f"{D}/data/tcm/tcm_library_filtered.csv")
m = old.merge(new, on="cid", how="left", suffixes=("_paper", "_rebuild2026"))
diff = m[m["name_rebuild2026"].isna() | (m["name_paper"] != m["name_rebuild2026"])]
mismatch = old[~old["cid"].isin(new["cid"])]
rows = []
for _, r in mismatch.iterrows():
    cand = new[new["name"].str.lower() == r["name"].lower()]
    new_cid = int(cand["cid"].iloc[0]) if len(cand) else None
    rows.append({"name_paper": r["name"], "cid_paper": r["cid"],
                 "cid_rebuild": new_cid,
                 "note": "PubChem identifier versioning" if new_cid else "not resolved by name in rebuild"})
pd.DataFrame(rows).to_csv(f"{V6}/cid_concordance_diff.csv", index=False, encoding="utf-8-sig")
print("CID mismatches:", len(rows), "->", f"{V6}/cid_concordance_diff.csv")

# ---------- 3. requirements.txt ----------
req = """# Python environment for the full pipeline (tested on Windows, CPython 3.x)
# Core scientific stack
numpy
pandas
scipy
scikit-learn
xgboost
statsmodels
# Chemistry
rdkit
# Deep learning (CPU)
torch==2.2.*
torch_geometric==2.5.*
# Docking helpers
meeko==0.7.*
prody
# AutoDock Vina 1.2.5 official Windows executable placed in tools/ (not pip)
# Visualization
matplotlib
"""
open(f"{D}/requirements.txt", "w", encoding="utf-8").write(req)
print("requirements.txt written")

# ---------- 4/5. KEGG + ChEMBL 快照（网络失败则记录说明） ----------
def fetch(url, path, note):
    try:
        req_ = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        data = urllib.request.urlopen(req_, timeout=30).read().decode("utf-8", "ignore")
        open(path, "w", encoding="utf-8").write(
            f"# fetched 2026-08-23 (roundtable-3 archival)\n# {note}\n" + data)
        return True
    except Exception as e:
        print("fetch failed:", url, e)
        return False

import os
os.makedirs(f"{D}/data/kegg", exist_ok=True)
ok1 = fetch("https://rest.kegg.jp/list/pathway/hsa", f"{D}/data/kegg/pathway_hsa_list_20260823.txt",
            "KEGG REST hsa pathway list snapshot")
ok2 = fetch("https://www.ebi.ac.uk/chembl/api/status.json", f"{D}/data/chembl/chembl_status_20260823.json",
            "ChEMBL release status AT RE-ARCHIVAL TIME (release number was NOT logged during original 2026-08-17 retrieval)")
print("KEGG snapshot:", ok1, "| ChEMBL status:", ok2)

# ---------- 6. 图源数据 CSV ----------
# fig1
f1 = []
for split in ["random", "scaffold"]:
    tp = j[split]["test_preds"]
    f1.append(pd.DataFrame({"split": split, "y": tp["y"], "mu": tp["mu"], "sigma": tp["sigma"]}))
pd.concat(f1).to_csv(f"{PCN}/figs/fig1_source_data.csv", index=False)
# fig2
v6 = json.load(open(f"{V6}/conformal_calibration.json", encoding="utf-8"))
rows2 = []
for lab, key in [("M0", "M0_raw_sigma"), ("M1", "M1_leverage_inflated"),
                 ("M2", "M2_split_conformal_flat")]:
    v = v6["methods"][key]
    rows2.append([lab, v["coverage95"], *v["coverage95_wilson_CI"], v["mean_half_width"]])
v5m = v6["scaffold_val_calibration_M5"]["methods"]["M5_scaffoldval_flat_conformal"]
rows2.append(["M5", v5m["coverage95"], *v5m["coverage95_wilson_CI"], v5m["mean_half_width"]])
pd.DataFrame(rows2, columns=["method", "coverage95", "ci_low", "ci_high", "mean_half_width"]).to_csv(
    f"{PCN}/figs/fig2_source_data.csv", index=False)
# fig3
c = pd.read_csv(f"{D}/results/tables/compound_cwbcs_full.csv")
tiers = ["in_domain_high_conf(域内高置信)", "in_domain_low_conf(域内低置信)", "OOD_warning(域外预警)"]
pd.DataFrame([{"tier": t, "count": int((c["tier"] == t).sum()),
               "median_sigma": round(float(c.loc[c["tier"] == t, "fxr_sigma"].median()), 3)}
              for t in tiers]).to_csv(f"{PCN}/figs/fig3_source_data.csv", index=False)
# fig4
h = pd.read_csv(f"{D}/results/tables/herb_cwbcs_ranking_fix.csv")
h[["herb", "n_compounds", "herb_score", "herb_score_shrunk", "rep_fix"]].to_csv(
    f"{PCN}/figs/fig4_source_data.csv", index=False, encoding="utf-8-sig")
print("figure source data written (4 csv)")
