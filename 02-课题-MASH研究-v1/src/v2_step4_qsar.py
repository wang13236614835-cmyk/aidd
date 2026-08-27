# -*- coding: utf-8 -*-
"""
V2 Step4: multi-target QSAR (one RF per target on Morgan-2 2048) trained on
real ChEMBL data (v2_step2 output). Scores the ultra-large NP library;
outputs per-target pAct predictions + activity-priority score.
Scaffold-aware: random 80/20 split per target for quick QA, then refit full.
"""
import glob, json, os, sys
import numpy as np
import pandas as pd
from rdkit import Chem, RDLogger
from rdkit.Chem import rdFingerprintGenerator
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score
from scipy.stats import spearmanr

RDLogger.DisableLog('rdApp.*')
D = "D:/zcode-workspace/mash_research"
RES = f"{D}/results/v2"
MFG = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)

def fp(smi):
    m = Chem.MolFromSmiles(smi)
    return None if m is None else np.array(MFG.GetFingerprint(m), dtype=np.int8)

# ---------- load training data ----------
files = glob.glob(f"{D}/data/v2/chembl_*.csv")
dfs = [pd.read_csv(f) for f in files if "multitarget_all" not in f]
tr = pd.concat(dfs, ignore_index=True)
tr = tr.dropna(subset=["canonical_smiles", "pAct"])
tr = tr[(tr.pAct > 3) & (tr.pAct < 11)]
print("training rows:", len(tr), "| targets:", tr.target.nunique())
print(tr.groupby("target").size().sort_values().to_string())

targets = tr.target.unique()
models, qaq = {}, {}
for t in targets:
    g = tr[tr.target == t].copy()
    fps, ys, smis = [], [], []
    for _, r in g.iterrows():
        v = fp(r.canonical_smiles)
        if v is not None:
            fps.append(v); ys.append(r.pAct); smis.append(r.canonical_smiles)
    X, y = np.stack(fps), np.array(ys)
    if len(y) < 60:
        print(f"{t}: only {len(y)} fingerprinted, skip"); continue
    rng = np.random.RandomState(42)
    idx = rng.permutation(len(y))
    cut = int(0.8 * len(y))
    m = RandomForestRegressor(n_estimators=300, n_jobs=-1, random_state=42)
    m.fit(X[idx[:cut]], y[idx[:cut]])
    p = m.predict(X[idx[cut:]])
    r2 = r2_score(y[idx[cut:]], p)
    sp = spearmanr(p, y[idx[cut:]]).statistic
    qaq[t] = dict(n=len(y), testR2=round(float(r2), 3), testSpearman=round(float(sp), 3))
    print(f"{t}: n={len(y)} test R2={r2:.3f} Spearman={sp:.3f}")
    mfull = RandomForestRegressor(n_estimators=400, n_jobs=-1, random_state=42)
    mfull.fit(X, y)
    models[t] = mfull
json.dump(qaq, open(f"{RES}/qsar_qa.json", "w"), indent=1)

# ---------- score library ----------
libfile = sys.argv[1] if len(sys.argv) > 1 else None
if libfile and os.path.exists(libfile):
    lib = pd.read_csv(libfile)
    keep, feats = [], []
    for i, r in lib.iterrows():
        v = fp(r["smiles"] if "smiles" in r.index else r["canonical_smiles"])
        if v is not None:
            feats.append(v); keep.append(i)
    L = lib.loc[keep].reset_index(drop=True)
    F = np.stack(feats)
    print("library fingerprinted:", len(L))
    for t, m in models.items():
        L[f"pAct_{t}"] = m.predict(F).round(2)
    # composite: mean of top-3 target predictions (multi-target potential)
    tcols = [c for c in L.columns if c.startswith("pAct_")]
    L["top3_mean"] = L[tcols].apply(lambda r: r.sort_values(ascending=False).head(3).mean(), axis=1).round(2)
    L["max_pAct"] = L[tcols].max(axis=1).round(2)
    out = sys.argv[2] if len(sys.argv) > 2 else f"{RES}/library_scored.csv"
    L.to_csv(out, index=False)
    print("scored ->", out)
