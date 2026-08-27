# -*- coding: utf-8 -*-
"""
模块B独立复算：ChEMBL FXR(CHEMBL2047) IC50 清洗链 548 → 354。
不复用原脚本代码，独立实现（scipy/numpy路径、自己的BH、自己的去重逻辑），
与原声明逐环节对账：
  声明链: 548 raw → 449精确('='&nM) → 盐剥离/混合物剔除/MW>=100 → 367独特(按规范SMILES去重,均值)
          → PAINS剔除9 → 358 → 杠杆AD(h>3(k+1)/n=0.0503)剔除4 → 最终354, pIC50 3.38–9.96
"""
import json
import numpy as np
import pandas as pd
from rdkit import Chem, RDLogger
from rdkit.Chem import Descriptors, Crippen, Lipinski
from rdkit.Chem import FilterCatalog
from rdkit.Chem.SaltRemover import SaltRemover
from sklearn.decomposition import PCA

RDLogger.DisableLog('rdApp.*')
D = "D:/zcode-workspace/mash_research"

raw = pd.read_csv(f"{D}/data/chembl/fxr_chembl2047_ic50_raw.csv")
print(f"[1] raw records: {len(raw)}  (claim 548)")

# --- 精确关系过滤 ---
m = (raw["standard_relation"] == "=") & (raw["standard_units"] == "nM") \
    & raw["canonical_smiles"].notna() & raw["standard_value"].notna()
d = raw[m].copy()
d["standard_value"] = pd.to_numeric(d["standard_value"], errors="coerce")
d = d[d["standard_value"] > 0]
print(f"[2] exact '=' nM records: {len(d)}  (claim 449)")

# --- 标准化：盐剥离+最大有机片段 / 混合物剔除 / MW>=100 ---
remover = SaltRemover()
def std1(smi):
    mol = Chem.MolFromSmiles(smi)
    if mol is None:
        return None, None
    mol = remover.StripMol(mol, dontRemoveEverything=True)
    frags = Chem.GetMolFrags(mol, asMols=True, sanitizeFrags=True)
    if len(frags) == 0:
        return None, None
    if len(frags) > 1:
        return "MIXTURE", None
    try:
        Chem.SanitizeMol(frags[0])
        return Chem.MolToSmiles(frags[0]), Descriptors.MolWt(frags[0])
    except Exception:
        return None, None

pairs = d["canonical_smiles"].map(std1)
d["std_smiles"] = [p[0] for p in pairs]
d["mw"] = [p[1] for p in pairs]
n_mix = int((d["std_smiles"] == "MIXTURE").sum())
d = d[d["std_smiles"].notna() & (d["std_smiles"] != "MIXTURE")]
print(f"[3] after salt/mixture removal: {len(d)}  (mixtures/invalid removed: {n_mix})")
d = d[d["mw"] >= 100]
print(f"[4] after MW>=100: {len(d)}")

# --- pIC50 独立换算（数学等价检查: pIC50 = -log10(IC50_M) = 9 - log10(nM值)）---
d["pIC50_mine"] = -np.log10(d["standard_value"] * 1e-9)

# --- 按规范SMILES去重（重复取均值）---
g = d.groupby("std_smiles").agg(pIC50=("pIC50_mine", "mean"),
                                n_rep=("pIC50_mine", "size")).reset_index()
print(f"[5] unique compounds: {len(g)}  (claim 367)  max reps: {g['n_rep'].max()} (claim 7)")

# --- PAINS A/B/C ---
p = FilterCatalog.FilterCatalogParams()
for c in [p.FilterCatalogs.PAINS_A, p.FilterCatalogs.PAINS_B, p.FilterCatalogs.PAINS_C]:
    p.AddCatalog(c)
cat = FilterCatalog.FilterCatalog(p)
def is_pains(smi):
    mol = Chem.MolFromSmiles(smi)
    return mol is not None and len(list(cat.GetMatches(mol))) > 0
g["pains"] = g["std_smiles"].map(is_pains)
n_pains = int(g["pains"].sum())
clean = g[~g["pains"]].reset_index(drop=True)
print(f"[6] PAINS removed: {n_pains} (claim 9) -> {len(clean)} (claim 358)")

# --- 描述符 + PCA + 杠杆（独立实现：直接构造帽子矩阵对角元）---
FUNCS = [Descriptors.MolWt, Crippen.MolLogP, Chem.rdMolDescriptors.CalcTPSA,
         Lipinski.NumHDonors, Lipinski.NumHAcceptors, Lipinski.NumRotatableBonds,
         Descriptors.RingCount, Lipinski.NumAromaticRings, Lipinski.HeavyAtomCount,
         Descriptors.FractionCSP3, Crippen.MolMR]
X = np.array([[f(Chem.MolFromSmiles(s)) for f in FUNCS] for s in clean["std_smiles"]])
Xz = (X - X.mean(0)) / X.std(0)
pca = PCA(n_components=0.95, svd_solver="full")
T = pca.fit_transform(Xz)
k, n = T.shape[1], T.shape[0]
# 独立杠杆实现：h_ii = t_i' (T'T)^-1 t_i（与原脚本的U^2求和法不同路径）
M = np.linalg.inv(T.T @ T)
h = np.einsum("ij,jk,ik->i", T, M, T)
h_crit = 3.0 * (k + 1) / n
print(f"[7] PCA k={k}, n={n}, h*={h_crit:.4f} (claim 0.0503), high-leverage removed: {(h>h_crit).sum()} (claim 4)")
final = clean[h <= h_crit].reset_index(drop=True)
print(f"[8] FINAL: {len(final)} compounds (claim 354), pIC50 {final['pIC50'].min():.2f}-{final['pIC50'].max():.2f} (claim 3.38-9.96)")

# 长尾声明: <5 有87个, >9 仅13个
lt5 = int((final["pIC50"] < 5).sum()); gt9 = int((final["pIC50"] > 9).sum())
print(f"[9] long-tail: pIC50<5: {lt5} (claim 87) | >9: {gt9} (claim 13)")

# --- 与存档最终数据集逐行对账 ---
ref = pd.read_csv(f"{D}/data/chembl/fxr_final_dataset.csv")
mg = final.merge(ref, on="std_smiles", how="outer", suffixes=("_mine", "_ref"), indicator=True)
both = mg[mg._merge == "both"]
dmax = float((both["pIC50_mine"] - both["pIC50_ref"]).abs().max())
print(f"[10] vs archived fxr_final_dataset.csv: rows mine={len(final)} ref={len(ref)} "
      f"both={len(both)} only_mine={(mg._merge=='left_only').sum()} only_ref={(mg._merge=='right_only').sum()} "
      f"| max|dPIC50|={dmax:.6f}")

# 去重均值抽查：找重复次数最多的化合物，用原始记录手工验证均值
top_rep = g.sort_values("n_rep", ascending=False).iloc[0]
sub = d[d["std_smiles"] == top_rep["std_smiles"]]
print(f"[11] spot-check dedup-mean for most-replicated compound: n={top_rep['n_rep']}, "
      f"mean(mine)={top_rep['pIC50']:.4f}, manual mean={sub['pIC50_mine'].mean():.4f}")

# 清洗前存档(fxr_clean_before_ad.csv)对账
ref2 = pd.read_csv(f"{D}/data/chembl/fxr_clean_before_ad.csv")
print(f"[12] fxr_clean_before_ad.csv rows={len(ref2)} (expect {len(clean)}), "
      f"SMILES集合一致: {set(ref2['std_smiles'])==set(clean['std_smiles'])}")

print("\nMODULE B VERDICT:")
checks = [
    ("raw=548", len(raw) == 548),
    ("exact=449", len(d) + 0 == 449 or True),  # d此时已经过MW过滤，改在下面检查
]
# 重新只做精确过滤数量（未做MW）
exact_only = raw[(raw["standard_relation"] == "=") & (raw["standard_units"] == "nM")
                 & raw["canonical_smiles"].notna() & raw["standard_value"].notna()]
exact_only = exact_only[pd.to_numeric(exact_only["standard_value"], errors="coerce") > 0]
print(f"    exact-relation count (pre-MW): {len(exact_only)}  claim 449 ->",
      "PASS" if len(exact_only) == 449 else "FAIL")
for name, ok, detail in [
    ("unique=367", len(g) == 367, f"got {len(g)}"),
    ("PAINS_removed=9", n_pains == 9, f"got {n_pains}"),
    ("after_pains=358", len(clean) == 358, f"got {len(clean)}"),
    ("h*=0.0503", abs(h_crit - 0.0503) < 0.0002, f"got {h_crit:.4f}"),
    ("leverage_removed=4", int((h > h_crit).sum()) == 4, f"got {int((h>h_crit).sum())}"),
    ("final=354", len(final) == 354, f"got {len(final)}"),
    ("longtail<5=87", lt5 == 87, f"got {lt5}"),
    ("longtail>9=13", gt9 == 13, f"got {gt9}"),
    ("rowwise_match_ref", dmax < 1e-6 and len(both) == 354,
     f"maxdiff={dmax:.2e}, both={len(both)}"),
]:
    print(f"    {name}: {'PASS' if ok else 'FAIL'} ({detail})")
