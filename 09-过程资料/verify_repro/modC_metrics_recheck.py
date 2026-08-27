# -*- coding: utf-8 -*-
"""
模块C快检：从存档 gnn_metrics_v2.json 的 test_preds(y, mu, sigma)数组出发，
独立重算 R2/RMSE/MAE/Spearman/ECE/coverage，验证存档指标自身是否自洽。
同时独立重造两个划分（骨架/随机），检验划分互斥性与大小是否=284/36/34与283/35/36。
"""
import json, math
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from rdkit import Chem, RDLogger
from rdkit.Chem.Scaffolds import MurckoScaffold

RDLogger.DisableLog('rdApp.*')
D = "D:/zcode-workspace/mash_research"

def r2_np(y, p):
    y, p = np.asarray(y), np.asarray(p)
    return 1 - np.sum((y - p) ** 2) / np.sum((y - y.mean()) ** 2)

def rmse_np(y, p):
    return math.sqrt(np.mean((np.asarray(y) - np.asarray(p)) ** 2))

v2 = json.load(open(f"{D}/results/tables/gnn_metrics_v2.json"))
for split in ["scaffold", "random"]:
    b = v2[split]["BGNN"]
    tp = v2[split]["test_preds"]
    y, mu, sg = np.array(tp["y"]), np.array(tp["mu"]), np.array(tp["sigma"])
    r2m, rmsem = r2_np(y, mu), rmse_np(y, mu)
    maem = np.mean(np.abs(y - mu))
    spm = spearmanr(mu, y).statistic
    print(f"\n[{split}] n_test={len(y)} (archived split={v2[split]['split']})")
    print(f"  R2     mine={r2m:.4f}  archived={b['R2']:.4f}  d={abs(r2m-b['R2']):.2e}")
    print(f"  RMSE   mine={rmsem:.4f} archived={b['RMSE']:.4f}  d={abs(rmsem-b['RMSE']):.2e}")
    print(f"  MAE    mine={maem:.4f} archived={b['MAE']:.4f}  d={abs(maem-b['MAE']):.2e}")
    print(f"  Spm    mine={spm:.4f} archived={b['Spearman']:.4f}  d={abs(spm-b['Spearman']):.2e}")
    # ECE/coverage是pooled(val+test)口径，仅检验test-only近似口径供参考
    z = (y - mu) / np.clip(sg, 1e-6, None)
    cov_te = [float(np.mean(np.abs(z) <= q)) for q in (0.5, 1.0, 1.96)]
    ece_te = float(np.mean([abs(c - e) for c, e in zip(cov_te, (0.383, 0.683, 0.95))]))
    print(f"  test-only cov50/68/95={cov_te} (archived pooled {b['coverage']}) ECE_te={ece_te:.3f} (archived {b['ECE']:.3f})")

# ---- 划分独立重构 ----
df = pd.read_csv(f"{D}/data/chembl/fxr_final_dataset.csv")
df["scaffold"] = df["std_smiles"].apply(
    lambda s: MurckoScaffold.MurckoScaffoldSmiles(smiles=s, includeChirality=False))
groups = df.groupby("scaffold").indices
order = sorted(groups.keys(), key=lambda s: -len(groups[s]))
n = len(df); tr, va, te = [], [], []
for s in order:
    tgt = tr if len(tr) / n < 0.8 else (va if len(va) / n < 0.1 else te)
    tgt.extend(groups[s])
print(f"\n[scaffold split rebuilt] train={len(tr)} val={len(va)} test={len(te)} "
      f"(archived {v2['scaffold']['split']}) disjoint={len(set(tr)&set(va))==0 and len(set(tr)&set(te))==0 and len(set(va)&set(te))==0}")
# 骨架划分互斥性检查：同一骨架不得跨集合
lab = pd.Series(0, index=df.index)
lab.iloc[tr] = 0; lab.iloc[va] = 1; lab.iloc[te] = 2
cross = sum(df.groupby("scaffold")[df.columns[0]].apply(
    lambda x: lab.loc[x.index].nunique() > 1))
print(f"  scaffolds spanning multiple sets: {cross} (must be 0 for STRICT split)")

idx = np.random.RandomState(42).permutation(n)
print(f"[random split rebuilt] train={int(0.8*n)} val={int(0.9*n)-int(0.8*n)} test={n-int(0.9*n)} "
      f"(archived {v2['random']['split']})")
# test SMILES集合与存档一致性
arch_te = set(v2["random"]["test_preds"]["smiles"])
mine_te = set(df["std_smiles"].iloc[idx[int(0.9*n):]])
print(f"  random-split test SMILES match archived: {arch_te == mine_te} ({len(arch_te & mine_te)}/{len(arch_te)})")
arch_te_s = set(v2["scaffold"]["test_preds"]["smiles"])
mine_te_s = set(df["std_smiles"].iloc[te])
print(f"  scaffold-split test SMILES match archived: {arch_te_s == mine_te_s} ({len(arch_te_s & mine_te_s)}/{len(arch_te_s)})")

# ---- y值复核：test_preds.y 是否与数据集pIC50一致 ----
smap = dict(zip(df["std_smiles"], df["pIC50"]))
for split in ["scaffold", "random"]:
    tp = v2[split]["test_preds"]
    bad = sum(1 for s, y in zip(tp["smiles"], tp["y"]) if abs(smap[s] - y) > 1e-5)
    print(f"[{split}] test y vs dataset pIC50 mismatches: {bad}/{len(tp['y'])}")
