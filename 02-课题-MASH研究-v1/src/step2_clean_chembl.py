# -*- coding: utf-8 -*-
"""
Step 2: Clean ChEMBL FXR IC50 data (real data only).
Pipeline: exact-relation filter -> RDKit standardization -> salt/mixture removal
-> dedup by canonical SMILES (mean pIC50) -> PAINS filter (FilterCatalog A/B/C)
-> pIC50 conversion -> 2D descriptors + PCA/Leverage AD boundary.
Outputs: clean dataset + AD reference (saved for natural-product OOD warning).
"""
import json
import numpy as np
import pandas as pd
from rdkit import Chem, RDLogger
from rdkit.Chem import Descriptors, Crippen, Lipinski, rdFingerprintGenerator
from rdkit.Chem import FilterCatalog
from rdkit import DataStructs
from sklearn.decomposition import PCA

RDLogger.DisableLog('rdApp.*')
rng = np.random.RandomState(42)

OUT = "D:/zcode-workspace/mash_research/data/chembl"
RES = "D:/zcode-workspace/mash_research/results"

df = pd.read_csv(f"{OUT}/fxr_chembl2047_ic50_raw.csv")
print("raw:", df.shape)

# ---------- 1. exact numeric IC50 in nM ----------
df = df[(df["standard_relation"] == "=") & (df["standard_units"] == "nM")].copy()
df = df[df["canonical_smiles"].notna() & df["standard_value"].notna()]
df["standard_value"] = df["standard_value"].astype(float)
df = df[df["standard_value"] > 0]
print("after exact nM IC50 filter:", df.shape)

# ---------- 2. RDKit standardization ----------
def standardize_smiles(smi):
    try:
        m = Chem.MolFromSmiles(smi)
        if m is None:
            return None, None
        # disconnect metals then keep largest organic fragment (salts)
        from rdkit.Chem.SaltRemover import SaltRemover
        remover = SaltRemover()
        m = remover.StripMol(m, dontRemoveEverything=True)
        frags = Chem.GetMolFrags(m, asMols=True, sanitizeFrags=True)
        if len(frags) == 0:
            return None, None
        if len(frags) > 1:
            return "MIXTURE", None  # multiple organic fragments -> exclude mixtures
        m = frags[0]
        Chem.SanitizeMol(m)
        # normalize charges / tautomers skipped (keep as reported)
        cano = Chem.MolToSmiles(m)
        mw = Descriptors.MolWt(m)
        return cano, mw
    except Exception:
        return None, None

std = df["canonical_smiles"].apply(standardize_smiles)
df["std_smiles"] = [s[0] for s in std]
df["mw"] = [s[1] for s in std]
n_mix = (df["std_smiles"] == "MIXTURE").sum()
df = df[(df["std_smiles"].notna()) & (df["std_smiles"] != "MIXTURE")]
print(f"removed {n_mix} mixtures / invalid -> {df.shape}")

# drop overly tiny fragments (inorganic remnants)
df = df[df["mw"] >= 100]
print("after MW>=100:", df.shape)

# ---------- 3. pIC50 ----------
df["pIC50"] = 9.0 - np.log10(df["standard_value"])  # nM -> M: -log10(v*1e-9)

# ---------- 4. dedup by canonical SMILES (mean of replicates) ----------
g = df.groupby("std_smiles").agg(
    pIC50=("pIC50", "mean"),
    n_act=("pIC50", "size"),
    std_pic50=("pIC50", "std"),
    mol_ids=("molecule_chembl_id", lambda x: ";".join(sorted(set(x)))),
    assay_n=("assay_chembl_id", lambda x: len(set(x))),
).reset_index()
g = g[g["n_act"] >= 1]
print("unique compounds after dedup:", g.shape)
print("pIC50 range:", g["pIC50"].min().round(2), "-", g["pIC50"].max().round(2))
print("replicate stats: max n_act =", g["n_act"].max(),
      "| median replicate std =", g["std_pic50"].median().round(3))

# ---------- 5. PAINS filter (FilterCatalog PAINS_A+B+C) ----------
fc_names = ["PAINS_A", "PAINS_B", "PAINS_C"]
params = FilterCatalog.FilterCatalogParams()
params.AddCatalog(FilterCatalog.FilterCatalogParams.FilterCatalogs.PAINS_A)
params.AddCatalog(FilterCatalog.FilterCatalogParams.FilterCatalogs.PAINS_B)
params.AddCatalog(FilterCatalog.FilterCatalogParams.FilterCatalogs.PAINS_C)
fcat = FilterCatalog.FilterCatalog(params)

def pains_hits(smi):
    m = Chem.MolFromSmiles(smi)
    if m is None:
        return ["INVALID"]
    return [e.GetDescription() for e in fcat.GetMatches(m)]

g["pains"] = g["std_smiles"].apply(pains_hits)
g["is_pains"] = g["pains"].apply(len) > 0
print("PAINS flagged:", g["is_pains"].sum())
clean = g[~g["is_pains"]].reset_index(drop=True)
print("after PAINS filter:", clean.shape)
clean.to_csv(f"{OUT}/fxr_clean_before_ad.csv", index=False)

# ---------- 6. 2D descriptors + PCA/Leverage AD ----------
DESC_FUNCS = {
    "MolWt": Descriptors.MolWt, "LogP": Crippen.MolLogP,
    "TPSA": Chem.rdMolDescriptors.CalcTPSA,
    "HBD": Lipinski.NumHDonors, "HBA": Lipinski.NumHAcceptors,
    "RotB": Lipinski.NumRotatableBonds,
    "RingCount": Descriptors.RingCount,
    "AromRings": Lipinski.NumAromaticRings,
    "HeavyAtoms": Lipinski.HeavyAtomCount,
    "Fsp3": Descriptors.FractionCSP3,
    "MolMR": Crippen.MolMR,
}

def desc_vec(smi):
    m = Chem.MolFromSmiles(smi)
    return [f(Chem.Mol(m)) for f in DESC_FUNCS.values()]

X = np.array([desc_vec(s) for s in clean["std_smiles"]])
names = list(DESC_FUNCS.keys())
mu, sd = X.mean(0), X.std(0)
Xz = (X - mu) / sd
pca = PCA(n_components=0.95, svd_solver="full")
T = pca.fit_transform(Xz)          # scores
k = T.shape[1]
n = T.shape[0]
# leverage: H = T (T'T)^-1 T' ; diagonal via SVD of T
U, S, Vt = np.linalg.svd(T, full_matrices=False)
h = (U ** 2).sum(axis=1)
h_crit = 3.0 * (k + 1) / n
print(f"PCA components kept: {k}, leverage critical h* = 3(k+1)/n = {h_crit:.4f}")
clean["leverage_h"] = h
clean["ood_train"] = h > h_crit
print("high-leverage outliers removed:", clean["ood_train"].sum())

final = clean[~clean["ood_train"]].reset_index(drop=True)
final.to_csv(f"{OUT}/fxr_final_dataset.csv", index=False)
print("FINAL dataset:", final.shape,
      "| pIC50", final["pIC50"].min().round(2), "-", final["pIC50"].max().round(2))

# AD reference for natural products
ad_ref = {"desc_names": names, "desc_mu": mu.tolist(), "desc_sd": sd.tolist(),
          "pca_mean": pca.mean_.tolist(), "pca_components": pca.components_.tolist(),
          "pca_k": int(k), "h_crit": float(h_crit), "n_train": int(n)}
json.dump(ad_ref, open(f"{OUT}/ad_reference.json", "w"))
print("AD reference saved: k=%d, h*=%.4f" % (k, h_crit))

# distribution summary table
bins = pd.cut(final["pIC50"], [0, 5, 6, 7, 8, 9, 100],
              labels=["<5", "5-6", "6-7", "7-8", "8-9", ">9"])
summ = bins.value_counts().sort_index()
print("\npIC50 binned distribution (long-tail check):\n", summ)
with open(f"{RES}/tables/dataset_summary.txt", "w", encoding="utf-8") as f:
    f.write(f"ChEMBL FXR (CHEMBL2047) Homo sapiens IC50 (assay_type=B)\n")
    f.write(f"raw exact-relation nM records: {len(df)}\n")
    f.write(f"unique compounds (dedup): {len(g)}\n")
    f.write(f"PAINS removed: {g['is_pains'].sum()}\n")
    f.write(f"high-leverage removed: {clean['ood_train'].sum()}\n")
    f.write(f"FINAL: {len(final)} compounds, pIC50 "
            f"{final['pIC50'].min():.2f}-{final['pIC50'].max():.2f}\n")
    f.write(f"PCA k={k}, h*={h_crit:.4f}\n\npIC50 binned:\n{summ.to_string()}\n")
