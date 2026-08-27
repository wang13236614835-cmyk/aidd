# -*- coding: utf-8 -*-
"""
端到端复验：重载 models/bgnn_production.pt（五种子生产集成），
对中药库抽样做MC推理，与 np_fxr_predictions.csv 的 mu/sigma 对账。
（不重训，验证"存档模型→存档推理表"环节可复现）
"""
import math
import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
from rdkit import Chem, RDLogger
from torch_geometric.data import Data
from torch_geometric.loader import DataLoader
from torch_geometric.nn import GINConv, global_mean_pool

RDLogger.DisableLog('rdApp.*')
torch.manual_seed(0)
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
    try: v[choices.index(val)] = 1.0
    except ValueError: v[-1] = 1.0
    return v
def mol_to_graph(smi):
    m = Chem.MolFromSmiles(smi)
    if m is None: return None
    xs = [onehot(a.GetAtomicNum(), ATOM_FEATS[0][1]) + onehot(a.GetTotalDegree(), ATOM_FEATS[1][1])
          + onehot(a.GetFormalCharge(), ATOM_FEATS[2][1]) + onehot(a.GetTotalNumHs(), ATOM_FEATS[3][1])
          + onehot(str(a.GetHybridization()), ATOM_FEATS[4][1])
          + [1.0 if a.GetIsAromatic() else 0.0, 1.0 if a.IsInRing() else 0.0] for a in m.GetAtoms()]
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

ck = torch.load(f"{D}/models/bgnn_production.pt", map_location="cpu")
ym, ys = ck["ym"], ck["ys"]
models = []
for sd in ck["models"]:
    m = BayesianGIN(ck["node_dim"])
    m.load_state_dict(sd)
    m.eval()
    models.append(m)
print(f"loaded production ensemble: {len(models)} seeds, ym={ym:.4f}, ys={ys:.4f}")

pred = pd.read_csv(f"{D}/results/tables/np_fxr_predictions.csv")
# 抽样: 每味药抽2个 + 小檗碱族全部
sample = (pred.groupby("herb", group_keys=False).apply(lambda g: g.head(2))
          if len(pred) else pred)
extra = pred[pred["herb"].str.contains("黄连")]
sample = pd.concat([sample, extra]).drop_duplicates(subset=["herb", "name"]).reset_index(drop=True)
print(f"sample size: {len(sample)}")

graphs = [mol_to_graph(s) for s in sample["smiles"]]
loader = DataLoader(graphs, batch_size=128, shuffle=False)
outs = []
with torch.no_grad():
    for model in models:
        mus_all, ales_all = [], []
        for d in loader:
            tm, ta = [], []
            for _ in range(50):
                mu, lv = model(d.x, d.edge_index, d.batch)
                tm.append(mu.numpy()); ta.append(np.exp(lv.numpy()))
            mus_all.append(np.stack(tm)); ales_all.append(np.stack(ta))
        mu_all = np.concatenate(mus_all, 1); al_all = np.concatenate(ales_all, 1)
        mean = mu_all.mean(0) * ys + ym
        var = mu_all.var(0) * ys ** 2 + al_all.mean(0) * ys ** 2
        outs.append((mean, np.sqrt(var)))
mean = np.mean([o[0] for o in outs], 0)
sigma = np.sqrt(np.mean([o[1] ** 2 for o in outs], 0) + np.var([o[0] for o in outs], 0))

sample = sample.copy()
sample["mu_mine"] = mean
sample["sigma_mine"] = sigma
sample["d_mu"] = (sample["mu_mine"] - sample["fxr_mu_pIC50"]).abs()
sample["d_sig"] = (sample["sigma_mine"] - sample["fxr_sigma"]).abs()
print(f"\nmu:  max|d|={sample['d_mu'].max():.4f} mean={sample['d_mu'].mean():.4f}")
print(f"sig: max|d|={sample['d_sig'].max():.4f} mean={sample['d_sig'].mean():.4f}")
print("(存档表保留3位小数; MC随机性导致逐次略有波动, 应<<0.1)")
print(sample[["herb", "name", "fxr_mu_pIC50", "mu_mine", "fxr_sigma", "sigma_mine"]].head(24).to_string(index=False))
