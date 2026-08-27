# -*- coding: utf-8 -*-
"""
B2 补充: 真正的"骨架域校准"——用已保存的 scaffold 集成模型在骨架 val(n=36) 上推理,
以 val 残差做 conformal 校准, 在骨架 test(n=34) 上评估 (M5)。
忠实复现 step3b 的特征化/划分/集成/MC 过程; 先对 test 复现值与 json 存储值做一致性抽查。
"""
import json
import math
import numpy as np
import pandas as pd
import torch
from rdkit import Chem, RDLogger
from rdkit.Chem.Scaffolds import MurckoScaffold
from torch_geometric.data import Data
from torch_geometric.loader import DataLoader
from torch_geometric.nn import GINConv, global_mean_pool
import torch.nn.functional as F

RDLogger.DisableLog("rdApp.*")
D = "D:/zcode-workspace/mash_research"

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
    try:
        v[choices.index(val)] = 1.0
    except ValueError:
        v[-1] = 1.0
    return v

def mol_to_graph(smi, y=None):
    m = Chem.MolFromSmiles(smi)
    if m is None:
        return None
    xs = []
    for a in m.GetAtoms():
        f = (onehot(a.GetAtomicNum(), ATOM_FEATS[0][1]) + onehot(a.GetTotalDegree(), ATOM_FEATS[1][1])
             + onehot(a.GetFormalCharge(), ATOM_FEATS[2][1]) + onehot(a.GetTotalNumHs(), ATOM_FEATS[3][1])
             + onehot(str(a.GetHybridization()), ATOM_FEATS[4][1])
             + [1.0 if a.GetIsAromatic() else 0.0, 1.0 if a.IsInRing() else 0.0])
        xs.append(f)
    ei = []
    for b in m.GetBonds():
        i, j = b.GetBeginAtomIdx(), b.GetEndAtomIdx()
        ei += [[i, j], [j, i]]
    d = Data(x=torch.tensor(xs, dtype=torch.float),
             edge_index=torch.tensor(ei, dtype=torch.long).t().contiguous())
    d.y = torch.tensor([y], dtype=torch.float) if y is not None else None
    d.smiles = smi
    return d

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

def mc_predict(model, graphs, T=50, batch=128, y_mean=0.0, y_std=1.0):
    loader = DataLoader(graphs, batch_size=batch, shuffle=False)
    model.eval()
    mus, ales = [], []
    with torch.no_grad():
        for d in loader:
            tm, ta = [], []
            for _ in range(T):
                mu, lv = model(d.x, d.edge_index, d.batch)
                tm.append(mu.numpy()); ta.append(np.exp(lv.numpy()))
            mus.append(np.stack(tm)); ales.append(np.stack(ta))
    mu_all = np.concatenate(mus, 1); al_all = np.concatenate(ales, 1)
    mean = mu_all.mean(0) * y_std + y_mean
    epist = mu_all.var(0) * y_std ** 2
    alea = al_all.mean(0) * y_std ** 2
    return mean, np.sqrt(epist + alea)

def ensemble_mc(models, graphs, T=50):
    torch.manual_seed(0)
    outs = [mc_predict(m, graphs, T=T, y_mean=ym, y_std=ys) for m, (ym, ys) in models]
    mean = np.mean([o[0] for o in outs], 0)
    sig = np.sqrt(np.mean([o[1] ** 2 for o in outs], 0) + np.var([o[0] for o in outs], 0))
    return mean, sig

# ---- data & split (faithful) ----
df = pd.read_csv(f"{D}/data/chembl/fxr_final_dataset.csv")
df["scaffold"] = df["std_smiles"].apply(
    lambda s: MurckoScaffold.MurckoScaffoldSmiles(smiles=s, includeChirality=False))
graphs_all = [mol_to_graph(s, y) for s, y in zip(df["std_smiles"], df["pIC50"])]
NODE_DIM = graphs_all[0].x.shape[1]

def scaffold_split_idx(df, frac_tr=0.8, frac_va=0.1):
    groups = df.groupby("scaffold").indices
    order = sorted(groups.keys(), key=lambda s: -len(groups[s]))
    n = len(df); tr, va, te = [], [], []
    for s in order:
        tgt = tr if len(tr) / n < frac_tr else (va if len(va) / n < frac_va else te)
        tgt.extend(groups[s])
    return np.array(tr), np.array(va), np.array(te)

tr_idx, va_idx, te_idx = scaffold_split_idx(df)
va_g = [graphs_all[i] for i in va_idx]
te_g = [graphs_all[i] for i in te_idx]

# ---- load checkpoint ----
ck = torch.load(f"{D}/models/bgnn_ensemble_scaffold.pt", map_location="cpu")
models = []
for sd, (ym, ys) in zip(ck["models"], ck["norm"]):
    m = BayesianGIN(ck["node_dim"])
    m.load_state_dict(sd)
    m.eval()
    models.append((m, (ym, ys)))
print("loaded %d models, node_dim=%d" % (len(models), ck["node_dim"]))

# ---- reproduce test preds (sanity vs json) ----
j = json.load(open(f"{D}/results/tables/gnn_metrics_v2.json", encoding="utf-8"))
tp = j["scaffold"]["test_preds"]
mu_te_r, sig_te_r = ensemble_mc(models, te_g, T=50)
mu_te_s = np.array(tp["mu"]); sig_te_s = np.array(tp["sigma"])
from scipy.stats import spearmanr, pearsonr
sanity = {
    "mu_pearson_vs_stored": round(float(pearsonr(mu_te_r, mu_te_s).statistic), 4),
    "mu_mean_abs_diff": round(float(np.abs(mu_te_r - mu_te_s).mean()), 4),
    "sigma_mean_abs_diff": round(float(np.abs(sig_te_r - sig_te_s).mean()), 4),
    "y_match": bool(np.allclose([float(g.y) for g in te_g], tp["y"])),
    "smiles_match": [g.smiles for g in te_g] == tp["smiles"],
}
print("sanity(test vs stored):", sanity)

# ---- scaffold-val predictions (real out-of-domain calibration set) ----
mu_va, sig_va = ensemble_mc(models, va_g, T=50)
y_va = np.array([float(g.y) for g in va_g])
y_te = np.array([float(g.y) for g in te_g])

ad = json.load(open(f"{D}/data/chembl/ad_reference.json", encoding="utf-8"))
H_CRIT = ad["h_crit"]
lev = dict(zip(df["std_smiles"], df["leverage_h"]))
h_va = np.array([lev[g.smiles] for g in va_g])
h_te = np.array([lev[g.smiles] for g in te_g])

sig_inf_va = sig_va * np.sqrt(1 + h_va / H_CRIT)
sig_inf_te = sig_te_r * np.sqrt(1 + h_te / H_CRIT)

def conformal_q(resid, alpha):
    n = len(resid)
    return float(np.quantile(resid, min(1.0, math.ceil((n + 1) * (1 - alpha)) / n), method="higher"))

def wilson(k, n, z=1.959964):
    p = k / n
    denom = 1 + z * z / n
    c = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return [round(c - half, 4), round(c + half, 4)]

alpha = 0.05
out = {"reproduction_sanity": sanity,
       "val_metrics": {"n": len(y_va),
                       "R2": round(float(1 - ((y_va - mu_va) ** 2).sum() / ((y_va - y_va.mean()) ** 2).sum()), 4),
                       "RMSE": round(float(np.sqrt(((y_va - mu_va) ** 2).mean())), 4)},
       "methods": {}}

# M5a: flat conformal on scaffold-val residuals
q_abs_va = conformal_q(np.abs(y_va - mu_va), alpha)
cov = float((np.abs(y_te - mu_te_r) <= q_abs_va).mean())
out["methods"]["M5_scaffoldval_flat_conformal"] = {
    "q": round(q_abs_va, 4), "coverage95": round(cov, 4),
    "coverage95_wilson_CI": wilson(int(cov * len(y_te)), len(y_te)),
    "mean_half_width": round(q_abs_va, 4)}

# M5b: adaptive z-conformal (z = |err|/sigma_inf) on scaffold-val
z_va = np.abs(y_va - mu_va) / sig_inf_va
q_z_va = conformal_q(z_va, alpha)
hw = q_z_va * sig_inf_te
cov = float((np.abs(y_te - mu_te_r) <= hw).mean())
out["methods"]["M5_scaffoldval_z_conformal_sigma_inf"] = {
    "q_z": round(q_z_va, 4), "coverage95": round(cov, 4),
    "coverage95_wilson_CI": wilson(int(cov * len(y_te)), len(y_te)),
    "mean_half_width": round(float(hw.mean()), 4),
    "median_half_width": round(float(np.median(hw)), 4)}

# M5 raw-sigma variant
z_va_raw = np.abs(y_va - mu_va) / sig_va
q_z_raw = conformal_q(z_va_raw, alpha)
hw_raw = q_z_raw * sig_te_r
cov_raw = float((np.abs(y_te - mu_te_r) <= hw_raw).mean())
out["methods"]["M5_scaffoldval_z_conformal_rawsigma"] = {
    "q_z": round(q_z_raw, 4), "coverage95": round(cov_raw, 4),
    "coverage95_wilson_CI": wilson(int(cov_raw * len(y_te)), len(y_te)),
    "mean_half_width": round(float(hw_raw.mean()), 4)}

# 80% for the best variant
q_z80 = conformal_q(z_va, 0.20)
cov80 = float((np.abs(y_te - mu_te_r) <= q_z80 * sig_inf_te).mean())
out["alpha_020_scaffoldval_z"] = {"coverage80": round(cov80, 4)}

path = f"{D}/results/v6/conformal_calibration.json"
full = json.load(open(path, encoding="utf-8"))
full["scaffold_val_calibration_M5"] = out
json.dump(full, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

print("val R2/RMSE:", out["val_metrics"])
for k, v in out["methods"].items():
    print("%-38s cov=%.3f CI%s width_mean=%.3f" % (
        k, v["coverage95"], v["coverage95_wilson_CI"], v["mean_half_width"]))
print("80% (M5b):", out["alpha_020_scaffoldval_z"])
print("appended ->", path)
