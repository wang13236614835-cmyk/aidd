# -*- coding: utf-8 -*-
"""
Step 10: obscure-herb follow-up.
(a) SENSITIVITY ARM (explicitly labeled): the proposal ADMET rule (LogP<5.5)
    structurally excludes ALL lanostane triterpenes (logP 7-8.5). To quantify
    what the rule excludes, run GNN inference on triterpenes that failed ONLY
    on LogP (relaxed rule: MW<600, LogP<8, HBD<=5, HBA<=10) - flagged as
    sensitivity results, NOT primary-screening results.
(b) Docking: top obscure candidates on THRB_3GWS + ACC2_5KKN (proxy scores)
    and FXR_3FLI for the top-5 (GNN-docking consistency).
"""
import json, re, subprocess
import numpy as np
import pandas as pd
from rdkit import Chem, RDLogger
from rdkit.Chem import AllChem
from rdkit.Chem import Descriptors, Crippen, Lipinski
from meeko import MoleculePreparation, PDBQTWriterLegacy
import torch
import torch.nn.functional as F
from torch_geometric.data import Data
from torch_geometric.loader import DataLoader
from torch_geometric.nn import GINConv, global_mean_pool

RDLogger.DisableLog('rdApp.*')
D = "D:/zcode-workspace/mash_research"
VINA = f"{D}/tools/vina_1.2.5_win.exe"
BOXES = json.load(open(f"{D}/docking/boxes.json"))
LIGD, OUTD = f"{D}/docking/ligands", f"{D}/docking/outputs"

# ---------- (a) sensitivity arm: triterpene GNN ----------
raw = pd.read_csv(f"{D}/data/tcm/obscure_herbs_raw.csv")
sens = raw[(raw["status"] == "OK") & (~raw["admet_pass"].astype(bool))].copy()
sens = sens[(sens["mw"] < 600) & (sens["logp"] < 8.0)
            & (sens["hbd"] <= 5) & (sens["hba"] <= 10)].reset_index(drop=True)
print("sensitivity arm compounds (failed only strict ADMET):", len(sens))
print(sens[["herb", "name", "mw", "logp"]].to_string(index=False))

ATOM_FEATS = [
    ("atomic_num", list(range(1, 119))),
    ("degree", [0, 1, 2, 3, 4, 5]),
    ("formal_charge", [-2, -1, 0, 1, 2]),
    ("num_hs", [0, 1, 2, 3, 4]),
    ("hybridization", ["S", "SP", "SP2", "SP3", "SP3D", "SP3D2"]),
    ("aromatic", [0, 1]), ("in_ring", [0, 1]),
]
def onehot(val, choices):
    v = [0.0] * (len(choices) + 1)
    try: v[choices.index(val)] = 1.0
    except ValueError: v[-1] = 1.0
    return v
def mol_to_graph(smi):
    m = Chem.MolFromSmiles(smi)
    if m is None: return None
    xs = []
    for a in m.GetAtoms():
        xs.append(onehot(a.GetAtomicNum(), ATOM_FEATS[0][1])
                  + onehot(a.GetTotalDegree(), ATOM_FEATS[1][1])
                  + onehot(a.GetFormalCharge(), ATOM_FEATS[2][1])
                  + onehot(a.GetTotalNumHs(), ATOM_FEATS[3][1])
                  + onehot(str(a.GetHybridization()), ATOM_FEATS[4][1])
                  + [1.0 if a.GetIsAromatic() else 0.0, 1.0 if a.IsInRing() else 0.0])
    ei = []
    for b in m.GetBonds():
        i, j = b.GetBeginAtomIdx(), b.GetEndAtomIdx()
        ei += [[i, j], [j, i]]
    return Data(x=torch.tensor(xs, dtype=torch.float),
                edge_index=torch.tensor(ei, dtype=torch.long).t().contiguous())

class BayesianGIN(torch.nn.Module):
    def __init__(self, node_dim, hidden=96, layers=3, dropout=0.15):
        super().__init__()
        self.convs, self.bns = torch.nn.ModuleList(), torch.nn.ModuleList()
        for i in range(layers):
            nin = node_dim if i == 0 else hidden
            self.convs.append(GINConv(torch.nn.Sequential(
                torch.nn.Linear(nin, hidden), torch.nn.ReLU(),
                torch.nn.Linear(hidden, hidden))))
            self.bns.append(torch.nn.BatchNorm1d(hidden))
        self.dropout = dropout
        self.head_mu = torch.nn.Linear(hidden, 1)
        self.head_logvar = torch.nn.Linear(hidden, 1)
    def forward(self, x, edge_index, batch):
        for conv, bn in zip(self.convs, self.bns):
            x = F.relu(bn(conv(x, edge_index)))
            x = F.dropout(x, p=self.dropout, training=True)
        p = global_mean_pool(x, batch)
        return self.head_mu(p).squeeze(-1), self.head_logvar(p).squeeze(-1)

ckpt = torch.load(f"{D}/models/bgnn_production.pt", map_location="cpu")
ym, ys = ckpt["ym"], ckpt["ys"]
models = []
for sd in ckpt["models"]:
    m = BayesianGIN(ckpt["node_dim"]); m.load_state_dict(sd); m.eval()
    models.append(m)

def ensemble_mc(graphs, T=50):
    loader = DataLoader(graphs, batch_size=128, shuffle=False)
    outs = []
    for model in models:
        mus, ales = [], []
        with torch.no_grad():
            for d in loader:
                tm, ta = [], []
                for _ in range(T):
                    mu, lv = model(d.x, d.edge_index, d.batch)
                    tm.append(mu.numpy()); ta.append(np.exp(lv.numpy()))
                mus.append(np.stack(tm)); ales.append(np.stack(ta))
        mu_all = np.concatenate(mus, 1); al_all = np.concatenate(ales, 1)
        outs.append((mu_all.mean(0) * ys + ym,
                     np.sqrt(mu_all.var(0) * ys ** 2 + al_all.mean(0) * ys ** 2)))
    mean = np.mean([o[0] for o in outs], 0)
    sig = np.sqrt(np.mean([o[1] ** 2 for o in outs], 0) + np.var([o[0] for o in outs], 0))
    return mean, sig

graphs, keep = [], []
for i, r in sens.iterrows():
    g = mol_to_graph(r["smiles"])
    if g is not None: graphs.append(g); keep.append(i)
sens = sens.loc[keep].reset_index(drop=True)
if len(sens):
    mu_s, sd_s = ensemble_mc(graphs)
    sens["fxr_mu_pIC50"] = mu_s.round(3)
    sens["fxr_sigma"] = sd_s.round(3)
    # leverage
    ad_ref = json.load(open(f"{D}/data/chembl/ad_reference.json"))
    FUNCS = dict(MolWt=Descriptors.MolWt, LogP=Crippen.MolLogP,
                 TPSA=Chem.rdMolDescriptors.CalcTPSA, HBD=Lipinski.NumHDonors,
                 HBA=Lipinski.NumHAcceptors, RotB=Lipinski.NumRotatableBonds,
                 RingCount=Descriptors.RingCount, AromRings=Lipinski.NumAromaticRings,
                 HeavyAtoms=Lipinski.HeavyAtomCount, Fsp3=Descriptors.FractionCSP3,
                 MolMR=Crippen.MolMR)
    tr_df = pd.read_csv(f"{D}/data/chembl/fxr_final_dataset.csv")
    Xtr = np.array([[FUNCS[k](Chem.MolFromSmiles(s)) for k in ad_ref["desc_names"]]
                    for s in tr_df["std_smiles"]])
    from sklearn.decomposition import PCA
    pca = PCA(n_components=ad_ref["pca_k"], svd_solver="full").fit(
        (Xtr - Xtr.mean(0)) / Xtr.std(0))
    Ttr = pca.transform((Xtr - Xtr.mean(0)) / Xtr.std(0))
    inv = np.linalg.inv(Ttr.T @ Ttr)
    def lev(smi):
        x = np.array([FUNCS[k](Chem.MolFromSmiles(smi)) for k in ad_ref["desc_names"]])
        t = pca.transform(((x - Xtr.mean(0)) / Xtr.std(0)).reshape(1, -1))
        return float((t @ inv @ t.T)[0, 0])
    sens["leverage_h"] = [round(lev(s), 4) for s in sens["smiles"]]
    sens["tier"] = ["OOD_warning" if h > ad_ref["h_crit"] else
                    ("high_conf" if s <= 0.7 else "low_conf")
                    for h, s in zip(sens["leverage_h"], sens["fxr_sigma"])]
    sens["arm"] = "SENSITIVITY(relaxed ADMET: logP<8, MW<600)"
    sens.to_csv(f"{D}/results/tables/obscure_sensitivity_triterpenes.csv", index=False)
    print("\n=== SENSITIVITY ARM RESULTS (not primary screen) ===")
    print(sens[["herb", "name", "fxr_mu_pIC50", "fxr_sigma", "leverage_h", "tier"]]
          .sort_values("fxr_mu_pIC50", ascending=False).to_string(index=False))

# ---------- (b) docking ----------
MK = MoleculePreparation()
def embed_3d(smi, seed=42):
    m = Chem.MolFromSmiles(smi)
    if m is None: return None
    m = Chem.AddHs(m)
    p = AllChem.ETKDGv3(); p.randomSeed = seed
    if AllChem.EmbedMolecule(m, p) != 0:
        p.useRandomCoords = True
        if AllChem.EmbedMolecule(m, p) != 0: return None
    try: AllChem.MMFFOptimizeMolecule(m, mmffVariant='MMFF94s', maxIters=500)
    except Exception:
        try: AllChem.UFFOptimizeMolecule(m, maxIters=500)
        except Exception: pass
    return m
def to_pdbqt(mol, path):
    s, ok, err = PDBQTWriterLegacy.write_string(MK(mol)[0])
    if not ok: return None
    open(path, "w").write(s)
    return path
AFF_RE = re.compile(r"^\s+\d+\s+(-?\d+\.\d+)\s+")
def run_vina(tag, lp, out, exh=12):
    b = BOXES[tag]; c, s = b["center"], b["size"]
    cmd = [VINA, "--receptor", f"{D}/docking/receptors/{tag}.pdbqt", "--ligand", lp,
           "--out", out, "--center_x", str(c[0]), "--center_y", str(c[1]),
           "--center_z", str(c[2]), "--size_x", str(s[0]), "--size_y", str(s[1]),
           "--size_z", str(s[2]), "--exhaustiveness", str(exh), "--seed", "42",
           "--num_modes", "9"]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    affs = [float(AFF_RE.match(l).group(1)) for l in r.stdout.splitlines() if AFF_RE.match(l)]
    return affs[0] if affs else None

# docking set: primary obscure library top-14 by mu + sensitivity triterpenes
prim = pd.read_csv(f"{D}/results/tables/obscure_herbs_predictions.csv")
top14 = prim.sort_values("fxr_mu_pIC50", ascending=False).head(14)
dock_set = [("primary", r) for _, r in top14.iterrows()]
if len(sens):
    dock_set += [("sensitivity", r) for _, r in sens.iterrows()]

rows = []
for arm, r in dock_set:
    key = re.sub(r"[^A-Za-z09]+", "_", f"{r['herb']}_{r['name']}")[:60]
    key = re.sub(r"[^A-Za-z0-9]+", "_", f"{r['herb']}_{r['name']}")[:60]
    mol = embed_3d(r["smiles"])
    lp = to_pdbqt(mol, f"{LIGD}/obs_{arm}_{key}.pdbqt") if mol is not None else None
    if lp is None:
        print("prep fail:", r["name"]); continue
    th = run_vina("THRB_3GWS", lp, f"{OUTD}/obs_THRB_{key}_out.pdbqt")
    ac = run_vina("ACC2_5KKN", lp, f"{OUTD}/obs_ACC_{key}_out.pdbqt")
    fx = None
    rows.append(dict(arm=arm, herb=r["herb"], name=r["name"],
                     fxr_mu=r["fxr_mu_pIC50"], fxr_sigma=r["fxr_sigma"],
                     tier=r["tier"], dG_THRB=th, dG_ACC=ac))
    print(f"[{arm}] {r['herb']} | {r['name']}: THRB {th} | ACC {ac}")

# FXR docking for top-5 primary
fx_rows = []
for _, r in top14.head(5).iterrows():
    key = re.sub(r"[^A-Za-z0-9]+", "_", f"{r['herb']}_{r['name']}")[:60]
    lp = f"{LIGD}/obs_primary_{key}.pdbqt"
    if not os.path.exists(lp):
        mol = embed_3d(r["smiles"])
        lp = to_pdbqt(mol, lp)
    if lp is None: continue
    fx = run_vina("FXR_3FLI", lp, f"{OUTD}/obs_FXR_{key}_out.pdbqt")
    fx_rows.append((r["name"], fx))
    print(f"[FXR] {r['name']}: {fx}")
import os
pd.DataFrame(rows).to_csv(f"{D}/results/tables/obscure_docking.csv", index=False)
print("\nsaved results/tables/obscure_docking.csv (+", len(fx_rows), "FXR cross-docks)")
for n, v in fx_rows:
    print(f"  FXR_3FLI {n}: {v}")
