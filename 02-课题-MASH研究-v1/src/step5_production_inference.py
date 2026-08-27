# -*- coding: utf-8 -*-
"""
Step 5: Production Bayesian GNN (trained on ALL clean ChEMBL FXR data, 5-seed
ensemble) -> batch MC inference on the natural-product library -> three-tier
confidence annotation (domain-in high-conf / domain-in low-conf / OOD warning)
using BOTH 2D-descriptor leverage (linear AD, from step2 reference) and
MC-Dropout sigma (nonlinear), i.e. the proposal's dual-layer AD mechanism.
"""
import json, math, random
import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
from rdkit import Chem, RDLogger
from torch_geometric.data import Data
from torch_geometric.loader import DataLoader
from torch_geometric.nn import GINConv, global_mean_pool

RDLogger.DisableLog('rdApp.*')
SEED = 42
random.seed(SEED); np.random.seed(SEED); torch.manual_seed(SEED)
D = "D:/zcode-workspace/mash_research"

# ---------- featurization (same as step3b) ----------
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
def mol_to_graph(smi, y=None):
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
    d.y = torch.tensor([y], dtype=torch.float) if y is not None else None
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

def hetero_nll(mu, logvar, y, weight):
    var = torch.exp(logvar).clamp(1e-6, 1e4)
    nll = 0.5 * (torch.log(var) + (y - mu) ** 2 / var) + 0.5 * math.log(2 * math.pi)
    return (nll * weight).mean()
def bin_weights(y, edges=(5, 6, 7, 8, 9)):
    b = np.digitize(y, edges)
    freq = np.bincount(b, minlength=len(edges) + 1).astype(float)
    w = 1.0 / np.maximum(freq[b], 1.0)
    return torch.tensor(w / w.mean(), dtype=torch.float)

# ---------- train production ensemble on ALL data ----------
df = pd.read_csv(f"{D}/data/chembl/fxr_final_dataset.csv")
y_all = df["pIC50"].values
graphs = [mol_to_graph(s, y) for s, y in zip(df["std_smiles"], y_all)]
graphs = [g for g in graphs if g is not None]
NODE_DIM = graphs[0].x.shape[1]
n = len(graphs)
perm = np.random.RandomState(SEED).permutation(n)
va_idx, tr_idx = perm[:max(int(0.1 * n), 10)], perm[max(int(0.1 * n), 10):]
tr_g, va_g = [graphs[i] for i in tr_idx], [graphs[i] for i in va_idx]
ym, ys = y_all[tr_idx].mean(), y_all[tr_idx].std()
for g in tr_g + va_g:
    g.y = torch.tensor([(float(g.y) - ym) / ys])
wv = bin_weights(y_all[tr_idx])
for g in graphs: g.w = torch.tensor([1.0], dtype=torch.float)  # uniform key everywhere
for g, w in zip(tr_g, wv): g.w = torch.tensor([w], dtype=torch.float)

models = []
for seed in [42, 7, 2024, 11, 99]:
    torch.manual_seed(seed)
    model = BayesianGIN(NODE_DIM)
    opt = torch.optim.Adam(model.parameters(), lr=5e-4, weight_decay=1e-6)
    loader = DataLoader(tr_g, batch_size=64, shuffle=True)
    best_val, best_state, bad = 1e9, None, 0
    yv = np.array([float(g.y) * ys + ym for g in va_g])
    for ep in range(500):
        model.train()
        for d in loader:
            opt.zero_grad()
            mu, lv = model(d.x, d.edge_index, d.batch)
            loss = hetero_nll(mu, lv, d.y.view(-1), d.w.view(-1))
            loss.backward(); opt.step()
        model.eval()
        with torch.no_grad():
            vloader = DataLoader(va_g, batch_size=128, shuffle=False)
            preds = []
            for d in vloader:
                mu, _ = model(d.x, d.edge_index, d.batch)
                preds += mu.tolist()
        rmse = math.sqrt(np.mean((np.array(preds) * ys + ym - yv) ** 2))
        if rmse < best_val - 1e-4:
            best_val, bad = rmse, 0
            best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
        else:
            bad += 1
            if bad >= 60: break
    model.load_state_dict(best_state)
    models.append(model)
    print(f"seed {seed}: holdout val RMSE {best_val:.3f}")

torch.save({"models": [m.state_dict() for m in models], "node_dim": NODE_DIM,
            "ym": float(ym), "ys": float(ys)}, f"{D}/models/bgnn_production.pt")
print("production ensemble saved (5 seeds, trained on full 354-compound set)")

# ---------- AD leverage for NPs (2D descriptor layer) ----------
from rdkit.Chem import Descriptors, Crippen, Lipinski
ad_ref = json.load(open(f"{D}/data/chembl/ad_reference.json"))
FUNCS = dict(MolWt=Descriptors.MolWt, LogP=Crippen.MolLogP,
             TPSA=Chem.rdMolDescriptors.CalcTPSA,
             HBD=Lipinski.NumHDonors, HBA=Lipinski.NumHAcceptors,
             RotB=Lipinski.NumRotatableBonds, RingCount=Descriptors.RingCount,
             AromRings=Lipinski.NumAromaticRings, HeavyAtoms=Lipinski.HeavyAtomCount,
             Fsp3=Descriptors.FractionCSP3, MolMR=Crippen.MolMR)
pca_mu = np.array(ad_ref["pca_mean"]); comps = np.array(ad_ref["pca_components"])
h_crit = ad_ref["h_crit"]; desc_mu = np.array(ad_ref["desc_mu"]); desc_sd = np.array(ad_ref["desc_sd"])

# rebuild training-space leverage exactly from training descriptors
tr_df = pd.read_csv(f"{D}/data/chembl/fxr_final_dataset.csv")
Xtr = np.array([[FUNCS[k](Chem.MolFromSmiles(s)) for k in ad_ref["desc_names"]]
                for s in tr_df["std_smiles"]])
Xtr_z = (Xtr - Xtr.mean(0)) / Xtr.std(0)
from sklearn.decomposition import PCA as PCA2
pca = PCA2(n_components=ad_ref["pca_k"], svd_solver="full").fit(Xtr_z)
Ttr = pca.transform(Xtr_z)
U, S, Vt = np.linalg.svd(Ttr, full_matrices=False)
# leverage h(x) = t (T'T)^-1 t' = sum_k (u_k . t_norm)^2 ... direct formula:
TtT_inv = np.linalg.inv(Ttr.T @ Ttr)
def leverage(smi):
    m = Chem.MolFromSmiles(smi)
    if m is None: return np.nan
    x = np.array([FUNCS[k](m) for k in ad_ref["desc_names"]])
    t = pca.transform(((x - Xtr.mean(0)) / Xtr.std(0)).reshape(1, -1))
    return float(t @ TtT_inv @ t.T)

# sanity: training-set leverage distribution
tr_h = np.array([leverage(s) for s in tr_df["std_smiles"]])
print(f"train leverage: mean={tr_h.mean():.4f} p95={np.percentile(tr_h,95):.4f} h*={h_crit:.4f}")

# ---------- NP library inference ----------
lib = pd.read_csv(f"{D}/data/tcm/tcm_library_filtered.csv")
print("NP library:", lib.shape)
np_graphs, keep_rows = [], []
for i, r in lib.iterrows():
    g = mol_to_graph(r["smiles"])
    if g is not None:
        g.w = torch.tensor([1.0]); np_graphs.append(g); keep_rows.append(i)
lib = lib.loc[keep_rows].reset_index(drop=True)

def mc_ensemble(graphs, T=50):
    loader = DataLoader(graphs, batch_size=128, shuffle=False)
    outs = []
    for model in models:
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
        mean = mu_all.mean(0) * ys + ym
        var_ep = mu_all.var(0) * ys ** 2 + al_all.mean(0) * ys ** 2
        outs.append((mean, np.sqrt(var_ep)))
    mean = np.mean([o[0] for o in outs], 0)
    sigma = np.sqrt(np.mean([o[1] ** 2 for o in outs], 0) + np.var([o[0] for o in outs], 0))
    return mean, sigma

mu_np, sd_np = mc_ensemble(np_graphs, T=50)
lib["fxr_mu_pIC50"] = mu_np.round(3)
lib["fxr_sigma"] = sd_np.round(3)
lib["leverage_h"] = [round(leverage(s), 4) for s in lib["smiles"]]
lib["confidence_weight_w"] = (1.0 / (1.0 + sd_np)).round(3)

def tier(h, s):
    if not np.isfinite(h) or h > h_crit:
        return "OOD_warning(域外预警)"
    return "in_domain_high_conf(域内高置信)" if s <= 0.70 else "in_domain_low_conf(域内低置信)"
lib["tier"] = [tier(h, s) for h, s in zip(lib["leverage_h"], lib["fxr_sigma"])]
lib.to_csv(f"{D}/results/tables/np_fxr_predictions.csv", index=False)
print(lib["tier"].value_counts().to_string())
print("\ntop 15 by mu within high-confidence tier:")
hi = lib[lib["tier"].str.startswith("in_domain_high")]
print(hi.sort_values("fxr_mu_pIC50", ascending=False)
      [["herb", "name", "fxr_mu_pIC50", "fxr_sigma", "leverage_h"]].head(15).to_string(index=False))
