# -*- coding: utf-8 -*-
"""
Step 7: CW-BCS (confidence-weighted binding-coverage score) + herb ranking.
Inputs: np_fxr_predictions.csv (GNN mu/sigma/tier), np_docking_raw.csv
(Vina affinities for THRB/ACC).
Formula (faithful to proposal + explicit normalization):
  s_FXR  = minmax(FXR mu_pIC50)            (model score, direction: higher better)
  s_THRB = minmax(-dG_THRB)                (docking proxy, higher better)
  s_ACC  = minmax(-dG_ACC)
  w      = 1 / (1 + sigma_FXR)             (confidence weight, in (0,1])
  CW-BCS_compound = ( (w * s_FXR) * s_THRB * s_ACC )^(1/3)
Herb score = geometric mean of top-K(3) compounds' CW-BCS
             x (1 - structural redundancy penalty of those compounds)
Redundancy: mean pairwise MaxMin Tanimoto (Morgan2) among the herb's top-K;
penalty = max(0, (mean_similarity - 0.6) / 0.4) capped at 0.5.
Outputs: compound-level 4-dim table (herb-compound-targets-confidence),
herb ranking, top-5 herbs with representative compounds.
"""
import json
import numpy as np
import pandas as pd
from rdkit import Chem, DataStructs, RDLogger
from rdkit.Chem import rdFingerprintGenerator

RDLogger.DisableLog('rdApp.*')
D = "D:/zcode-workspace/mash_research"

pred = pd.read_csv(f"{D}/results/tables/np_fxr_predictions.csv")
dock = pd.read_csv(f"{D}/results/tables/np_docking_raw.csv")

thrb = dock[dock.target == "THRB_3GWS"][["herb", "name", "affinity"]].rename(
    columns={"affinity": "dG_THRB"})
acc = dock[dock.target == "ACC2_5KKN"][["herb", "name", "affinity"]].rename(
    columns={"affinity": "dG_ACC"})

df = (pred.merge(thrb, on=["herb", "name"], how="outer")
         .merge(acc, on=["herb", "name"], how="outer"))
print("merged table:", df.shape)
print("with FXR mu:", df["fxr_mu_pIC50"].notna().sum(),
      "| with THRB dG:", df["dG_THRB"].notna().sum(),
      "| with ACC dG:", df["dG_ACC"].notna().sum())

def minmax(s):
    s = s.astype(float)
    lo, hi = np.nanmin(s), np.nanmax(s)
    return (s - lo) / (hi - lo) if hi > lo else s * 0 + 0.5

df["s_FXR"] = minmax(df["fxr_mu_pIC50"])
df["s_THRB"] = minmax(-df["dG_THRB"])
df["s_ACC"] = minmax(-df["dG_ACC"])
df["w_conf"] = 1.0 / (1.0 + df["fxr_sigma"].fillna(3.0))

eps = 1e-3  # avoid zero-roots destroying the geometric mean
df["CW_BCS"] = ((np.clip(df["w_conf"] * df["s_FXR"], eps, None)
                 * np.clip(df["s_THRB"], eps, None)
                 * np.clip(df["s_ACC"], eps, None)) ** (1 / 3)).round(4)

# absolute-quality flags (interpretability layer, beyond normalized rank)
df["flag_FXR_active"] = df["fxr_mu_pIC50"] >= 6.5      # ~ <=316 nM
df["flag_THRB_good"] = df["dG_THRB"] <= -7.0           # kcal/mol
df["flag_ACC_good"] = df["dG_ACC"] <= -7.0
df["n_targets_covered"] = (df[["flag_FXR_active", "flag_THRB_good", "flag_ACC_good"]]
                           .fillna(False).sum(axis=1))

mfg = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
def fps(smis):
    out = {}
    for s in smis:
        m = Chem.MolFromSmiles(s) if isinstance(s, str) else None
        out[s] = mfg.GetFingerprint(m) if m is not None else None
    return out

herb_rows = []
K = 3
for herb, g in df.groupby("herb"):
    g2 = g.sort_values("CW_BCS", ascending=False)
    top = g2.head(K)
    fp_cache = fps(top["smiles"].tolist() if "smiles" in top else top.index.tolist())
    fps_list = [fp_cache[s] for s in (top["smiles"].tolist() if "smiles" in top else [])]
    sims = []
    for i in range(len(fps_list)):
        for j in range(i + 1, len(fps_list)):
            if fps_list[i] is not None and fps_list[j] is not None:
                sims.append(DataStructs.TanimotoSimilarity(fps_list[i], fps_list[j]))
    mean_sim = float(np.mean(sims)) if sims else 0.0
    redun = min(max((mean_sim - 0.6) / 0.4, 0.0), 0.5)
    geo = float(np.exp(np.mean(np.log(top["CW_BCS"].clip(lower=1e-4)))))
    herb_rows.append(dict(
        herb=herb,
        n_compounds=int(len(g)),
        topK_CW_BCS_geo=round(geo, 4),
        redundancy_penalty=round(redun, 3),
        mean_topK_tanimoto=round(mean_sim, 3),
        herb_score=round(geo * (1 - redun), 4),
        best_compound=top.iloc[0]["name"] if len(top) else None,
        best_CW_BCS=float(top.iloc[0]["CW_BCS"]) if len(top) else None,
        best_tier=top.iloc[0]["tier"] if len(top) else None,
        coverage_any=int((g["n_targets_covered"] >= 1).sum()),
        coverage_multi=int((g["n_targets_covered"] >= 2).sum()),
    ))

rank = pd.DataFrame(herb_rows).sort_values("herb_score", ascending=False).reset_index(drop=True)
rank.insert(0, "rank", rank.index + 1)
rank.to_csv(f"{D}/results/tables/herb_cwbcs_ranking.csv", index=False)
df.sort_values("CW_BCS", ascending=False).to_csv(
    f"{D}/results/tables/compound_cwbcs_full.csv", index=False)

print("\n===== HERB RANKING (CW-BCS) =====")
print(rank.to_string(index=False))
print("\n===== TOP 20 COMPOUNDS =====")
cols = ["herb", "name", "CW_BCS", "fxr_mu_pIC50", "fxr_sigma", "tier",
        "dG_THRB", "dG_ACC", "n_targets_covered"]
print(df.sort_values("CW_BCS", ascending=False)[cols].head(20).to_string(index=False))
json.dump(dict(K=K, eps=eps, threshold_FXR=6.5, threshold_dG=-7.0,
               redundancy_rule="max(0,(meanTan-0.6)/0.4) capped 0.5"),
          open(f"{D}/results/tables/cwbcs_params.json", "w"), indent=2)
