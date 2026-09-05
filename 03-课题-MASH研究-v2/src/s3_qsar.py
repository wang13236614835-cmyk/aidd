# -*- coding: utf-8 -*-
"""
S3: 三靶点QSAR（全新方法设计）。
特征: Morgan FP r=2 2048bit。
模型: XGBoost + RandomForest 等权平均集成。
评估: Butina聚类划分(Tanimoto 0.4, 整簇分配, 主) + 随机划分(次);
      指标 RMSE/R2/Spearman + split-conformal 95%区间覆盖率。
域外判据: 对训练集最大Tanimoto相似度(kNN-AD)。
输出: 各靶点模型指标 + NP库54化合物预测(μ, conformal区间, kNN-AD)。
"""

# Historical pipeline: its outputs are invalidated; corrected code lives in 00-当前研究.
raise RuntimeError("此历史入口已停用以保留原数据与结果；请使用仓库00-当前研究中的诊断/修订流程。")
import json, math
import numpy as np
import pandas as pd
import xgboost as xgb
from rdkit import Chem, DataStructs, RDLogger
from rdkit.Chem import rdFingerprintGenerator
from rdkit.ML.Cluster import Butina
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_squared_error
from scipy.stats import spearmanr

RDLogger.DisableLog('rdApp.*')
D = "D:/zcode-workspace/mash_v2_new"
mfg = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)

def fp(smi):
    m = Chem.MolFromSmiles(smi)
    return mfg.GetFingerprint(m) if m else None

def fps_mat(smiles):
    fs = [fp(s) for s in smiles]
    X = np.zeros((len(fs), 2048), dtype=np.int8)
    for i, f in enumerate(fs):
        if f is not None:
            X[i] = np.array(f, dtype=np.int8)
    return X, fs

def butina_clusters(fps, cutoff=0.4):
    n = len(fps)
    sims = []
    for i in range(n):
        for j in range(i + 1, n):
            sims.append(1.0 - DataStructs.TanimotoSimilarity(fps[i], fps[j]))
    cs = Butina.ClusterData(sims, n, cutoff, isDistData=True)
    labels = np.zeros(n, dtype=int)
    for ci, cluster in enumerate(cs):
        for idx in cluster:
            labels[idx] = ci
    return labels

def cluster_split(labels, frac_tr=0.8, frac_va=0.1, seed=42):
    rng = np.random.RandomState(seed)
    sizes = pd.Series(labels).value_counts()
    order = sizes.index.tolist()
    n = len(labels)
    tr, va, te = [], [], []
    for c in order:
        idx = np.where(labels == c)[0]
        tgt = tr if len(tr) / n < frac_tr else (va if len(va) / n < frac_va else te)
        tgt.extend(idx.tolist())
    return np.array(tr), np.array(va), np.array(te)

def ens_fit_predict(Xtr, ytr, Xte, Xva=None, seed=42):
    m1 = xgb.XGBRegressor(n_estimators=600, max_depth=5, learning_rate=0.05,
                          subsample=0.8, colsample_bytree=0.8, random_state=seed,
                          tree_method="hist", objective="reg:squarederror", n_jobs=8)
    m2 = RandomForestRegressor(n_estimators=500, random_state=seed, n_jobs=8)
    m1.fit(Xtr, ytr); m2.fit(Xtr, ytr)
    def pred(X):
        return (m1.predict(X) + m2.predict(X)) / 2
    return pred(Xte), (pred(Xva) if Xva is not None else None), (m1, m2)

results = {}
models_store = {}
for tgt in ["THRB", "FASN", "SCD1"]:
    df = pd.read_csv(f"{D}/data/chembl/{tgt}_clean.csv")
    X, fs = fps_mat(df.std_smiles.tolist())
    y = df.pIC50.values
    ok = np.array([f is not None for f in fs])
    X, y, fs = X[ok], y[ok], [f for f, o in zip(fs, ok) if o]
    labels = butina_clusters(fs, cutoff=0.4)
    print(f"\n===== {tgt}: n={len(y)} clusters={labels.max()+1} =====")

    out = {}
    # --- 主: Butina聚类划分 ---
    tr, va, te = cluster_split(labels, seed=42)
    mean_base = np.sqrt(np.mean((y[te] - y[tr].mean()) ** 2))
    p_te, p_va, models = ens_fit_predict(X[tr], y[tr], X[te], X[va])
    rmse = math.sqrt(mean_squared_error(y[te], p_te))
    q95 = np.quantile(np.abs(y[va] - p_va), min(1.0, np.ceil((len(va) + 1) * 0.95) / len(va)))
    cov = float(np.mean(np.abs(y[te] - p_te) <= q95))
    out["cluster_split"] = dict(
        n=[int(len(tr)), int(len(va)), int(len(te))], n_clusters=int(labels.max() + 1),
        RMSE=round(rmse, 3), mean_baseline_RMSE=round(mean_base, 3),
        R2=round(r2_score(y[te], p_te), 3),
        Spearman=round(spearmanr(p_te, y[te]).statistic, 3),
        conformal_q95=round(float(q95), 3), coverage95=round(cov, 3))
    models_store[tgt] = dict(models=None, tr_idx=tr.tolist(), q95=float(q95))
    # --- 次: 随机划分 ---
    rng = np.random.RandomState(42)
    perm = rng.permutation(len(y))
    a, b = int(0.8 * len(y)), int(0.9 * len(y))
    tr2, va2, te2 = perm[:a], perm[a:b], perm[b:]
    p_te2, p_va2, _ = ens_fit_predict(X[tr2], y[tr2], X[te2], X[va2])
    q95b = np.quantile(np.abs(y[va2] - p_va2), min(1.0, np.ceil((len(va2) + 1) * 0.95) / len(va2)))
    out["random_split"] = dict(
        n=[int(len(tr2)), int(len(va2)), int(len(te2))],
        RMSE=round(math.sqrt(mean_squared_error(y[te2], p_te2)), 3),
        R2=round(r2_score(y[te2], p_te2), 3),
        Spearman=round(spearmanr(p_te2, y[te2]).statistic, 3),
        conformal_q95=round(float(q95b), 3),
        coverage95=round(float(np.mean(np.abs(y[te2] - p_te2) <= q95b)), 3))
    print("cluster:", out["cluster_split"])
    print("random :", out["random_split"])
    results[tgt] = out

    # --- 保存测试预测供核验 ---
    pd.DataFrame(dict(y=y[te], pred=p_te)).to_csv(
        f"{D}/results/tables/{tgt}_cluster_split_testpred.csv", index=False)

json.dump(results, open(f"{D}/results/tables/s3_qsar_metrics.json", "w"), indent=1)

# ---------- NP库批量预测(全数据重训) ----------
print("\n===== NP library prediction (full-data models) =====")
lib = pd.read_csv(f"{D}/data/tcm/np_library_filtered.csv")
Xnp, fsnp = fps_mat(lib.smiles.tolist())
for tgt in ["THRB", "FASN", "SCD1"]:
    df = pd.read_csv(f"{D}/data/chembl/{tgt}_clean.csv")
    Xtr, ftr = fps_mat(df.std_smiles.tolist())
    ytr = df.pIC50.values
    m1 = xgb.XGBRegressor(n_estimators=600, max_depth=5, learning_rate=0.05,
                          subsample=0.8, colsample_bytree=0.8, random_state=42,
                          tree_method="hist", n_jobs=8)
    m2 = RandomForestRegressor(n_estimators=500, random_state=42, n_jobs=8)
    m1.fit(Xtr, ytr); m2.fit(Xtr, ytr)
    lib[f"{tgt}_pIC50"] = ((m1.predict(Xnp) + m2.predict(Xnp)) / 2).round(3)
    # kNN-AD: 对训练集最大Tanimoto
    sims = []
    for f in fsnp:
        if f is None:
            sims.append(np.nan)
        else:
            sims.append(max(DataStructs.TanimotoSimilarity(f, g) for g in ftr))
    lib[f"{tgt}_maxTan_train"] = np.round(sims, 3)
    # conformal半宽(聚类划分校准的q95)
    lib[f"{tgt}_ci95_halfwidth"] = round(results[tgt]["cluster_split"]["conformal_q95"], 2)

lib.to_csv(f"{D}/results/tables/np_predictions_new.csv", index=False)
print(lib[["herb", "name", "THRB_pIC50", "FASN_pIC50", "SCD1_pIC50",
           "THRB_maxTan_train", "FASN_maxTan_train", "SCD1_maxTan_train"]].to_string(index=False))
print("\nS3 complete.")
