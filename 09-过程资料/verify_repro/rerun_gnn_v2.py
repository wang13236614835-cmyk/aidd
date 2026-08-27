# -*- coding: utf-8 -*-
"""
独立复跑 step3b_bayesian_gnn_v2.py（贝叶斯GNN双划分评估）。
代码原样复制自原脚本，仅修改输出路径到 verify_repro/outputs，不覆盖原结果。
目的：验证 R2(scaffold)=-0.610 / R2(random)=0.790 等指标可否从同一数据+同一代码复现。
"""
import json, math, random
import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
from rdkit import Chem, RDLogger
from rdkit.Chem.Scaffolds import MurckoScaffold
from rdkit.Chem import rdFingerprintGenerator
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from scipy.stats import spearmanr
from torch_geometric.data import Data
from torch_geometric.loader import DataLoader
from torch_geometric.nn import GINConv, global_mean_pool

RDLogger.DisableLog('rdApp.*')
SEED = 42
random.seed(SEED); np.random.seed(SEED); torch.manual_seed(SEED)
D = "D:/zcode-workspace/mash_research"
OUT = "D:/zcode-workspace/verify_repro/outputs"

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

def random_split_idx(df, frac_tr=0.8, frac_va=0.1, seed=SEED):
    idx = np.random.RandomState(seed).permutation(len(df))
    n = len(df); a, b = int(frac_tr * n), int((frac_tr + frac_va) * n)
    return idx[:a], idx[a:b], idx[b:]

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
    return mean, np.sqrt(epist + alea), epist, alea

def train_once_real(train_g, val_g, seed, epochs=500, lr=5e-4, patience=60):
    torch.manual_seed(seed)
    y_tr = np.array([float(g.y) for g in train_g])
    ym, ys = y_tr.mean(), y_tr.std()
    for g in train_g: g.y = torch.tensor([(float(g.y) - ym) / ys])
    for g in val_g: g.y = torch.tensor([(float(g.y) - ym) / ys])
    wvec = bin_weights(y_tr)
    for g, w in zip(train_g, wvec): g.w = torch.tensor([w], dtype=torch.float)
    model = BayesianGIN(NODE_DIM)
    opt = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-6)
    tr_loader = DataLoader(train_g, batch_size=64, shuffle=True)
    best_val, best_state, bad = 1e9, None, 0
    for ep in range(epochs):
        model.train()
        for d in tr_loader:
            opt.zero_grad()
            mu, lv = model(d.x, d.edge_index, d.batch)
            loss = hetero_nll(mu, lv, d.y.view(-1), d.w.view(-1))
            loss.backward(); opt.step()
        m, _, _, _ = mc_predict(model, val_g, T=10, y_mean=ym, y_std=ys)
        yv = np.array([float(g.y) * ys + ym for g in val_g])
        rmse = math.sqrt(np.mean((m - yv) ** 2))
        if rmse < best_val - 1e-4:
            best_val, bad = rmse, 0
            best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
        else:
            bad += 1
            if bad >= patience: break
    model.load_state_dict(best_state)
    for g in train_g + val_g: g.y = torch.tensor([float(g.y) * ys + ym])
    return model, best_val, (ym, ys)

def run_experiment(name, split_fn):
    for g in graphs_all:
        g.w = torch.tensor([1.0], dtype=torch.float)
    tr_idx, va_idx, te_idx = split_fn(df)
    print(f"\n===== {name}: train {len(tr_idx)} / val {len(va_idx)} / test {len(te_idx)} =====", flush=True)
    tr_g = [graphs_all[i] for i in tr_idx]
    va_g = [graphs_all[i] for i in va_idx]
    te_g = [graphs_all[i] for i in te_idx]
    models, stats = [], []
    for seed in [42, 7, 2024, 11, 99]:
        m, bv, (ym, ys) = train_once_real(tr_g, va_g, seed)
        models.append((m, (ym, ys)))
        stats.append(bv)
        print(f"  seed {seed} done, best val RMSE {bv:.3f}", flush=True)

    def ensemble_mc(graphs, T=50):
        outs = [mc_predict(m, graphs, T=T, y_mean=ym, y_std=ys) for m, (ym, ys) in models]
        mean = np.mean([o[0] for o in outs], 0)
        sig = np.sqrt(np.mean([o[1] ** 2 for o in outs], 0)
                      + np.var([o[0] for o in outs], 0))
        return mean, sig

    mu_te, sd_te = ensemble_mc(te_g)
    y_te = np.array([float(g.y) for g in te_g])
    mu_pv, sd_pv = ensemble_mc(va_g + te_g)
    y_pv = np.array([float(g.y) for g in va_g + te_g])

    r2 = r2_score(y_te, mu_te); rmse = math.sqrt(mean_squared_error(y_te, mu_te))
    mae = mean_absolute_error(y_te, mu_te); sp = spearmanr(mu_te, y_te).statistic
    sp_uq = spearmanr(sd_pv, np.abs(y_pv - mu_pv)).statistic
    z = (y_pv - mu_pv) / np.clip(sd_pv, 1e-6, None)
    qs = [0.5, 1.0, 1.96]; exp = [0.383, 0.683, 0.95]
    cov = [float(np.mean(np.abs(z) <= q)) for q in qs]
    ece = float(np.mean([abs(c - e) for c, e in zip(cov, exp)]))
    print(f"[BGNN test] R2={r2:.3f} RMSE={rmse:.3f} MAE={mae:.3f} Spearman={sp:.3f}", flush=True)
    print(f"[BGNN UQ pooled n={len(y_pv)}] sp(sig,|err|)={sp_uq:.3f} cov={cov} ECE={ece:.3f}", flush=True)

    mfg = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
    X = np.stack([np.array(mfg.GetFingerprint(Chem.MolFromSmiles(s)), dtype=np.int8)
                  for s in df["std_smiles"]])
    y = df["pIC50"].values
    import xgboost as xgb
    base = {}
    for nm, mdl in [("RF", RandomForestRegressor(n_estimators=800, random_state=SEED, n_jobs=-1)),
                    ("XGB", xgb.XGBRegressor(n_estimators=800, max_depth=6, learning_rate=0.03,
                                             subsample=0.8, colsample_bytree=0.8, random_state=SEED,
                                             tree_method="hist", objective="reg:squarederror"))]:
        mdl.fit(X[tr_idx], y[tr_idx])
        p = mdl.predict(X[te_idx])
        base[nm] = dict(R2=r2_score(y[te_idx], p),
                        RMSE=math.sqrt(mean_squared_error(y[te_idx], p)),
                        MAE=mean_absolute_error(y[te_idx], p),
                        Spearman=spearmanr(p, y[te_idx]).statistic)
        print(f"[{nm} test] " + " ".join(f"{k}={v:.3f}" for k, v in base[nm].items()), flush=True)

    return dict(split=[int(len(tr_idx)), int(len(va_idx)), int(len(te_idx))],
                BGNN=dict(R2=r2, RMSE=rmse, MAE=mae, Spearman=sp,
                          Spearman_sigma_err=sp_uq, ECE=ece, coverage=cov),
                baselines=base,
                test_preds=dict(smiles=[g.smiles for g in te_g],
                                y=y_te.tolist(), mu=mu_te.tolist(), sigma=sd_te.tolist()))

res_scaffold = run_experiment("SCAFFOLD split (strict)", scaffold_split_idx)
res_random = run_experiment("RANDOM split (proposal-style)", random_split_idx)

out = dict(scaffold=res_scaffold, random=res_random)
json.dump(out, open(f"{OUT}/gnn_metrics_v2_rerun.json", "w"), indent=2)
print("\nsaved -> verify_repro/outputs/gnn_metrics_v2_rerun.json")
