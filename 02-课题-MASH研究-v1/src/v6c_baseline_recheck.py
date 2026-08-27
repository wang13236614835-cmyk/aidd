# -*- coding: utf-8 -*-
"""独立复算 RF/XGB 基线（m3 问题H：存储值未独立复算）——不触碰任何原始文件。
只重训指纹基线（确定性 random_state=42），输出到 results/v6/baseline_recheck.json。"""
import json
import math
import numpy as np
import pandas as pd
from rdkit import Chem, RDLogger
from rdkit.Chem import rdFingerprintGenerator
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from scipy.stats import spearmanr
from rdkit.Chem.Scaffolds import MurckoScaffold

RDLogger.DisableLog("rdApp.*")
D = "D:/zcode-workspace/mash_research"
SEED = 42

df = pd.read_csv(f"{D}/data/chembl/fxr_final_dataset.csv")
df["scaffold"] = df["std_smiles"].apply(
    lambda s: MurckoScaffold.MurckoScaffoldSmiles(smiles=s, includeChirality=False))

def random_split_idx(df, seed=SEED):
    idx = np.random.RandomState(seed).permutation(len(df))
    n = len(df); a = int(0.8 * n); b = int(0.9 * n)
    return idx[:a], idx[a:b], idx[b:]

def scaffold_split_idx(df):
    groups = df.groupby("scaffold").indices
    order = sorted(groups.keys(), key=lambda s: -len(groups[s]))
    n = len(df); tr, va, te = [], [], []
    for s in order:
        tgt = tr if len(tr) / n < 0.8 else (va if len(va) / n < 0.1 else te)
        tgt.extend(groups[s])
    return np.array(tr), np.array(va), np.array(te)

mfg = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
X = np.stack([np.array(mfg.GetFingerprint(Chem.MolFromSmiles(s)), dtype=np.int8)
              for s in df["std_smiles"]])
y = df["pIC50"].values

import xgboost as xgb
out = {}
for name, split_fn in [("random", random_split_idx), ("scaffold", scaffold_split_idx)]:
    tr, va, te = split_fn(df)
    for nm, mdl in [
        ("RF", RandomForestRegressor(n_estimators=800, random_state=SEED, n_jobs=-1)),
        ("XGB", xgb.XGBRegressor(n_estimators=800, max_depth=6, learning_rate=0.03,
                                 subsample=0.8, colsample_bytree=0.8, random_state=SEED,
                                 tree_method="hist", objective="reg:squarederror"))]:
        mdl.fit(X[tr], y[tr])
        p = mdl.predict(X[te])
        out[f"{name}_{nm}"] = dict(
            n_test=int(len(te)),
            R2=round(float(r2_score(y[te], p)), 4),
            RMSE=round(float(math.sqrt(mean_squared_error(y[te], p))), 4),
            MAE=round(float(mean_absolute_error(y[te], p)), 4),
            Spearman=round(float(spearmanr(p, y[te]).statistic), 4))

stored = json.load(open(f"{D}/results/tables/gnn_metrics_v2.json", encoding="utf-8"))
cmp = {}
for k, v in out.items():
    splt, nm = k.split("_")
    st = stored[splt]["baselines"][nm]
    cmp[k] = {"recheck": v,
              "stored": {kk: round(st[kk], 4) for kk in ["R2", "RMSE", "MAE", "Spearman"]},
              "match": all(abs(v[kk] - round(st[kk], 4)) < 0.01 for kk in ["R2", "RMSE", "MAE", "Spearman"])}
json.dump({"recheck": out, "comparison": cmp},
          open(f"{D}/results/v6/baseline_recheck.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)
print(json.dumps(cmp, indent=1))
