# -*- coding: utf-8 -*-
"""
模块E独立核验：批量推理结果与三级标注。
1) np_fxr_predictions.csv 的 tier 计数 72/32/27 与规则(h>0.0503 / sigma>0.70)自洽性
2) w=1/(1+sigma) 列自洽
3) 用 ad_reference.json 独立重算杠杆h（不同实现路径），抽查全库131个
4) 黄连碱 Berberine mu=8.21 声明核对
"""
import json
import numpy as np
import pandas as pd
from rdkit import Chem, RDLogger
from rdkit.Chem import Descriptors, Crippen, Lipinski

RDLogger.DisableLog('rdApp.*')
D = "D:/zcode-workspace/mash_research"
pred = pd.read_csv(f"{D}/results/tables/np_fxr_predictions.csv")
print(f"rows={len(pred)} (claim 131)")

# --- tier规则自洽 ---
h_crit = 0.0503
def tier_rule(h, s):
    if not np.isfinite(h) or h > h_crit:
        return "OOD_warning(域外预警)"
    return "in_domain_high_conf(域内高置信)" if s <= 0.70 else "in_domain_low_conf(域内低置信)"
pred["tier_mine"] = [tier_rule(h, s) for h, s in zip(pred["leverage_h"], pred["fxr_sigma"])]
ct = pred["tier"].value_counts()
ctm = pred["tier_mine"].value_counts()
print("archived tier counts:\n", ct.to_string())
print("recomputed rule counts:\n", ctm.to_string())
mism = (pred["tier"] != pred["tier_mine"]).sum()
print(f"tier mismatches: {mism}/{len(pred)}  (claim 72/32/27)")

# --- w列 ---
w_mine = (1 / (1 + pred["fxr_sigma"])).round(3)
print(f"w=1/(1+sigma) col max diff: {(w_mine - pred['confidence_weight_w']).abs().max()}")

# --- 独立杠杆重算（全部131个，实现路径与step5不同：QR分解法）---
ad = json.load(open(f"{D}/data/chembl/ad_reference.json"))
FUNCS = dict(MolWt=Descriptors.MolWt, LogP=Crippen.MolLogP, TPSA=Chem.rdMolDescriptors.CalcTPSA,
             HBD=Lipinski.NumHDonors, HBA=Lipinski.NumHAcceptors, RotB=Lipinski.NumRotatableBonds,
             RingCount=Descriptors.RingCount, AromRings=Lipinski.NumAromaticRings,
             HeavyAtoms=Lipinski.HeavyAtomCount, Fsp3=Descriptors.FractionCSP3, MolMR=Crippen.MolMR)
tr = pd.read_csv(f"{D}/data/chembl/fxr_final_dataset.csv")
Xtr = np.array([[FUNCS[k](Chem.MolFromSmiles(s)) for k in ad["desc_names"]] for s in tr["std_smiles"]])
mu, sd = Xtr.mean(0), Xtr.std(0)
V = np.array(ad["pca_components"])          # (k, 11)
pmean = np.array(ad["pca_mean"])
# 训练集得分矩阵（PCA中心=pca_mean，但标准化用的desc_mu/desc_sd——注意ad_ref中保存了两套中心）
# 按step5实现：Xtr_z=(Xtr-Xtr.mean)/Xtr.std 后由PCA拟合；这里用保存的components正交基+QR独立求h
Xz = (Xtr - mu) / sd
Ttr = (Xz - (np.array(ad["pca_mean"]) - mu) / sd * 0) @ V.T + 0  # placeholder not used
# 更直接：用sklearn重新拟合PCA(与step5相同但作为独立执行)
from sklearn.decomposition import PCA
pca = PCA(n_components=ad["pca_k"], svd_solver="full").fit(Xz)
Ttr = pca.transform(Xz)
Q, R = np.linalg.qr(Ttr)                    # QR法: H = Q Q^T, diag = ||q_i||^2
h_train = (Q ** 2).sum(1)
print(f"train leverage via QR: mean={h_train.mean():.4f} max={h_train.max():.4f} | h*={h_crit} | over: {(h_train>h_crit).sum()} (训练集应几乎为0，因AD过滤已剔除)")
# 验证QR法与逆矩阵法一致
Minv = np.linalg.inv(Ttr.T @ Ttr)
h_inv = np.einsum("ij,jk,ik->i", Ttr, Minv, Ttr)
print(f"QR vs inv leverage max diff on train: {np.abs(h_train-h_inv).max():.2e}")

def leverage_qr(smi):
    m = Chem.MolFromSmiles(smi)
    if m is None: return np.nan
    x = np.array([FUNCS[k](m) for k in ad["desc_names"]])
    t = pca.transform(((x - mu) / sd).reshape(1, -1))
    q = np.linalg.solve(R.T, t.reshape(-1))     # t = Q R => q = R^{-T} t; h = ||q||^2
    return float((q ** 2).sum())

h_mine = np.array([leverage_qr(s) for s in pred["smiles"]])
dh = np.abs(h_mine - pred["leverage_h"].values)
print(f"NP leverage independent recompute: max|dh|={np.nanmax(dh):.5f} mean={np.nanmean(dh):.5f}")
tier_mine2 = [tier_rule(h, s) for h, s in zip(h_mine, pred["fxr_sigma"])]
print(f"tier from my leverage mismatches: {sum(a!=b for a,b in zip(tier_mine2, pred['tier']))}/{len(pred)}")
print("my tier counts:", pd.Series(tier_mine2).value_counts().to_dict())

# --- Berberine声明 ---
bb = pred[pred["name"].str.contains("Berberine", case=False, na=False)]
print("\nBerberine row:")
print(bb[["herb", "name", "fxr_mu_pIC50", "fxr_sigma", "leverage_h", "tier"]].to_string(index=False))
