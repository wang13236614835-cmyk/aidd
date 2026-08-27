# -*- coding: utf-8 -*-
"""
Step 5b: GNNExplainer interpretability for top predicted natural products +
calibration/reliability figures + y-vs-mu scatter (model evidence pack).
"""
import json, math
import numpy as np
import pandas as pd
import torch
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

D = "D:/zcode-workspace/mash_research"
FIG = f"{D}/results/figures"

# ---------- figures from saved v2 metrics/predictions ----------
met = json.load(open(f"{D}/results/tables/gnn_metrics_v2.json"))
tp = pd.DataFrame(met["random"]["test_preds"])

fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
# (a) scatter with error bars
ax = axes[0]
err = ax.errorbar(tp.y, tp.mu, yerr=tp.sigma, fmt="o", ms=4, alpha=0.6,
                  ecolor="lightgray", elinewidth=1, capsize=2)
lim = [3, 10]
ax.plot(lim, lim, "r--", lw=1)
ax.set_xlabel("experimental pIC50"); ax.set_ylabel("predicted pIC50 (BGNN)")
ax.set_title(f"BGNN test set (random split)\nR2={met['random']['BGNN']['R2']:.2f}, "
             f"RMSE={met['random']['BGNN']['RMSE']:.2f}")
# (b) reliability diagram (binned sigma vs mean |z|)
ax = axes[1]
z = np.abs((tp.y - tp.mu) / np.clip(tp.sigma, 1e-6, None))
qs = np.array([0.383, 0.683, 0.866, 0.95, 0.988])
emp = np.array([np.mean(z <= q) for q in qs])
ax.bar(np.arange(5) - 0.18, qs, 0.36, label="ideal (Gaussian)")
ax.bar(np.arange(5) + 0.18, emp, 0.36, label="BGNN empirical")
ax.set_xticks(np.arange(5)); ax.set_xticklabels(["50%", "68%", "87%", "95%", "98.8%"])
ax.set_ylim(0, 1.05); ax.legend(frameon=False)
ax.set_title("z-score reliability (pooled val+test)")
# (c) sigma vs |error|
ax = axes[2]
ax.scatter(tp.sigma, np.abs(tp.y - tp.mu), s=18, alpha=0.7)
r = np.corrcoef(tp.sigma, np.abs(tp.y - tp.mu))[0, 1]
ax.set_xlabel("predicted sigma"); ax.set_ylabel("|error|")
ax.set_title(f"uncertainty vs error (Pearson r={r:.2f})")
plt.tight_layout(); plt.savefig(f"{FIG}/gnn_calibration_pack.png", dpi=180)
print("figure saved:", f"{FIG}/gnn_calibration_pack.png")

# ---------- GNNExplainer on top NP predictions ----------
import sys
sys.path.insert(0, f"{D}/src")
from rdkit import Chem, RDLogger
from torch_geometric.explain import Explainer, GNNExplainer
from torch_geometric.data import Data

# rebuild model class (import from step5 module without running its main)
import importlib.util
spec = importlib.util.spec_from_file_location("s5", f"{D}/src/step5_production_inference.py")
# can't import (it trains). Recreate minimal model here instead:
import torch.nn.functional as F
from torch_geometric.nn import GINConv, global_mean_pool
RDLogger.DisableLog('rdApp.*')

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
    d = Data(x=torch.tensor(xs, dtype=torch.float),
             edge_index=torch.tensor(ei, dtype=torch.long).t().contiguous())
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
            x = F.dropout(x, p=self.dropout, training=False)  # deterministic for explain
        p = global_mean_pool(x, batch)
        return self.head_mu(p).squeeze(-1)

ckpt = torch.load(f"{D}/models/bgnn_production.pt", map_location="cpu")
model = BayesianGIN(ckpt["node_dim"])
model.load_state_dict(ckpt["models"][0])
model.eval()

explainer = Explainer(
    model=model,
    algorithm=GNNExplainer(epochs=120),
    explanation_type="model",
    node_mask_type="attributes",
    edge_mask_type="object",
    model_config=dict(mode="regression", task_level="graph", return_type="raw"),
)

pred = pd.read_csv(f"{D}/results/tables/np_fxr_predictions.csv")
top = pred[pred["tier"].astype(str).str.startswith("in_domain_high")] \
    .sort_values("fxr_mu_pIC50", ascending=False).head(8)
rows = []
for _, r in top.iterrows():
    g = mol_to_graph(r["smiles"])
    if g is None: continue
    g.batch = torch.zeros(g.x.size(0), dtype=torch.long)
    exp = explainer(g.x, g.edge_index, batch=g.batch)
    node_imp = exp.node_mask.sum(1).detach().numpy()  # per-atom importance
    node_imp = (node_imp - node_imp.min()) / (np.ptp(node_imp) + 1e-9)
    mol = Chem.MolFromSmiles(r["smiles"])
    order = np.argsort(-node_imp)[:6]
    atoms = [f"{mol.GetAtomWithIdx(int(i)).GetSymbol()}{int(i)}({node_imp[i]:.2f})"
             for i in order]
    rows.append(dict(herb=r["herb"], compound=r["name"], mu=r["fxr_mu_pIC50"],
                     sigma=r["fxr_sigma"], top_atoms="; ".join(atoms)))
    print(f"{r['herb']} | {r['name']}: top atoms {atoms}")

pd.DataFrame(rows).to_csv(f"{D}/results/tables/gnnexplainer_top_atoms.csv", index=False)
print("saved: results/tables/gnnexplainer_top_atoms.csv")
