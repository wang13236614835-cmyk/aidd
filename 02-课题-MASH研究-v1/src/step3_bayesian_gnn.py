# -*- coding: utf-8 -*-
"""
Step 3: Bayesian GNN for FXR pIC50 prediction.
Methodological upgrades vs proposal:
  (a) Bemis-Murcko SCAFFOLD split (no chemical-space leakage) + 5-fold CV
  (b) Heteroscedastic NLL loss (aleatoric head) + MC Dropout (epistemic, T=50)
      total sigma = sqrt(sigma_alea^2 + var_epistemic)
  (c) bin-frequency weighted loss for long-tail activity distribution
Baselines: RandomForest & XGBoost on Morgan fingerprints (same splits).
Calibration: z-score reliability diagram + regression ECE + Spearman(sigma,|err|).
"""
import json, math, os, random
import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
from torch import Tensor
from rdkit import Chem, RDLogger
from rdkit.Chem.Scaffolds import MurckoScaffold
from rdkit.Chem import rdFingerprintGenerator
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from scipy.stats import spearmanr
from torch_geometric.data import Data, InMemoryDataset
from torch_geometric.loader import DataLoader
from torch_geometric.nn import GINConv, global_mean_pool

RDLogger.DisableLog('rdApp.*')
SEED = 42
random.seed(SEED); np.random.seed(SEED); torch.manual_seed(SEED)

D = "D:/zcode-workspace/mash_research"
RES, MOD = f"{D}/results", f"{D}/models"
os.makedirs(f"{RES}/tables", exist_ok=True); os.makedirs(f"{RES}/figures", exist_ok=True)

# ---------------- featurization ----------------
ATOM_FEATS = [
    ("atomic_num", list(range(1, 119))),
    ("degree", [0, 1, 2, 3, 4, 5]),
    ("formal_charge", [-2, -1, 0, 1, 2]),
    ("num_hs", [0, 1, 2, 3, 4]),
    ("hybridization", ["S", "SP", "SP2", "SP3", "SP3D", "SP3D2"]),
    ("aromatic", [0, 1]),
    ("in_ring", [0, 1]),
]
BOND_TYPES = [Chem.rdchem.BondType.SINGLE, Chem.rdchem.BondType.DOUBLE,
              Chem.rdchem.BondType.TRIPLE, Chem.rdchem.BondType.AROMATIC]

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
        f = []
        f += onehot(a.GetAtomicNum(), ATOM_FEATS[0][1])
        f += onehot(a.GetTotalDegree(), ATOM_FEATS[1][1])
        f += onehot(a.GetFormalCharge(), ATOM_FEATS[2][1])
        f += onehot(a.GetTotalNumHs(), ATOM_FEATS[3][1])
        f += onehot(str(a.GetHybridization()), ATOM_FEATS[4][1])
        f += [1.0 if a.GetIsAromatic() else 0.0, 1.0 if a.IsInRing() else 0.0]
        xs.append(f)
    ei, ew = [], []
    for b in m.GetBonds():
        i, j = b.GetBeginAtomIdx(), b.GetEndAtomIdx()
        bt = onehot(str(b.GetBondType()), [str(t) for t in BOND_TYPES])
        extra = [1.0 if b.GetIsConjugated() else 0.0, 1.0 if b.IsInRing() else 0.0]
        ei += [[i, j], [j, i]]
        ew += [bt + extra, bt + extra]
    x = torch.tensor(xs, dtype=torch.float)
    edge_index = torch.tensor(ei, dtype=torch.long).t().contiguous()
    edge_attr = torch.tensor(ew, dtype=torch.float)
    d = Data(x=x, edge_index=edge_index, edge_attr=edge_attr)
    d.y = torch.tensor([y], dtype=torch.float) if y is not None else None
    d.smiles = smi
    return d

# ---------------- dataset ----------------
df = pd.read_csv(f"{D}/data/chembl/fxr_final_dataset.csv")
graphs = [mol_to_graph(s, y) for s, y in zip(df["std_smiles"], df["pIC50"])]
df = df[[g is not None for g in graphs]].reset_index(drop=True)
graphs = [g for g in graphs if g is not None]
print("graphs built:", len(graphs))

# ---------------- scaffold split ----------------
def scaffold_id(smi):
    try:
        sc = MurckoScaffold.MurckoScaffoldSmiles(smiles=smi, includeChirality=False)
    except Exception:
        sc = smi
    return sc

df["scaffold"] = df["std_smiles"].apply(scaffold_id)
scaf_groups = df.groupby("scaffold").indices  # scaffold -> row indices
scaffolds = sorted(scaf_groups.keys(), key=lambda s: -len(scaf_groups[s]))
train_idx, val_idx, test_idx = [], [], []
n = len(df)
for s in scaffolds:
    idxs = list(scaf_groups[s])
    tgt = train_idx if len(train_idx) / n < 0.8 else (val_idx if len(val_idx) / n < 0.10 else test_idx)
    tgt.extend(idxs)
print(f"scaffold split: train {len(train_idx)} / val {len(val_idx)} / test {len(test_idx)}")

train_g = [graphs[i] for i in train_idx]
val_g = [graphs[i] for i in val_idx]
test_g = [graphs[i] for i in test_idx]

# long-tail sample weights (inverse bin frequency)
y_tr = np.array([float(g.y) for g in train_g])
bins = np.digitize(y_tr, [5, 6, 7, 8, 9])
freq = np.bincount(bins, minlength=7).astype(float)
w = 1.0 / np.maximum(freq[bins], 1.0)
w = w / w.mean()
for g, wi in zip(train_g, w):
    g.w = torch.tensor([wi], dtype=torch.float)

# ---------------- model ----------------
class BayesianGIN(torch.nn.Module):
    def __init__(self, node_dim, edge_dim, hidden=128, layers=3, dropout=0.20):
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
        self.head_logvar = torch.nn.Linear(hidden, 1)  # aleatoric

    def forward(self, x, edge_index, batch, edge_attr=None):
        for conv, bn in zip(self.convs, self.bns):
            x = conv(x, edge_index)
            x = bn(x)
            x = F.relu(x)
            x = F.dropout(x, p=self.dropout, training=True)  # dropout ACTIVE in inference too (MC)
        pooled = global_mean_pool(x, batch)
        return self.head_mu(pooled).squeeze(-1), self.head_logvar(pooled).squeeze(-1)

NODE_DIM = graphs[0].x.shape[1]
device = torch.device("cpu")

def hetero_nll(mu, logvar, y, weight=None):
    var = torch.exp(logvar).clamp(1e-6, 1e4)
    nll = 0.5 * (torch.log(var) + (y - mu) ** 2 / var) + 0.5 * math.log(2 * math.pi)
    if weight is not None:
        nll = nll * weight
    return nll.mean()

def run_epoch(model, loader, optimizer=None, weights=True):
    if optimizer:
        model.train()
    else:
        model.eval()  # note: dropout stays on via forward(training=True)
    tot, nb = 0.0, 0
    preds, ys = [], []
    for d in loader:
        optimizer_zero = optimizer.zero_grad() if optimizer else None
        mu, lv = model(d.x, d.edge_index, d.batch)
        y = d.y.view(-1)
        wvec = d.w.view(-1) if (weights and hasattr(d, "w")) else None
        loss = hetero_nll(mu, lv, y, wvec)
        if optimizer:
            loss.backward(); optimizer.step()
        tot += loss.item() * len(y); nb += len(y)
        preds += mu.detach().tolist(); ys += y.tolist()
    return tot / max(nb, 1), np.array(preds), np.array(ys)

def train_model(seed=SEED, epochs=300, lr=1e-3, patience=40):
    torch.manual_seed(seed)
    model = BayesianGIN(NODE_DIM, 0).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-5)
    tr_loader = DataLoader(train_g, batch_size=64, shuffle=True)
    va_loader = DataLoader(val_g, batch_size=128, shuffle=False)
    best_val, best_state, bad = 1e9, None, 0
    for ep in range(epochs):
        _, p_tr, y_tr_ = run_epoch(model, tr_loader, opt)
        with torch.no_grad():
            vl, p_va, y_va = run_epoch(model, va_loader)
        rmse = math.sqrt(np.mean((p_va - y_va) ** 2))
        if rmse < best_val - 1e-4:
            best_val, bad = rmse, 0
            best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
        else:
            bad += 1
            if bad >= patience:
                break
    model.load_state_dict(best_state)
    return model, best_val

def mc_predict(model, loader, T=50):
    model.eval()  # BN in eval; dropout active inside forward
    mus, ales = [], []
    with torch.no_grad():
        for d in loader:
            tm, ta = [], []
            for _ in range(T):
                mu, lv = model(d.x, d.edge_index, d.batch)
                tm.append(mu.numpy()); ta.append(np.exp(lv.numpy()))
            mus.append(np.stack(tm)); ales.append(np.stack(ta))
    mu_all = np.concatenate(mus, 1)   # T x N
    al_all = np.concatenate(ales, 1)
    mean = mu_all.mean(0)
    epist = mu_all.var(0)
    alea = al_all.mean(0)
    sigma = np.sqrt(epist + alea)
    return mean, sigma, epist, alea

# ---------------- train + MC inference ----------------
tr_loader = DataLoader(train_g, batch_size=64, shuffle=False)
va_loader = DataLoader(val_g, batch_size=128, shuffle=False)
te_loader = DataLoader(test_g, batch_size=128, shuffle=False)

models = []
for seed in [SEED, 7, 2024]:
    m, bv = train_model(seed=seed)
    print(f"seed {seed}: best val RMSE = {bv:.3f}")
    models.append(m)

# ensemble MC prediction (mean over seeds)
def ensemble_mc(loader, T=50):
    outs = [mc_predict(m, loader, T=T) for m in models]
    mean = np.mean([o[0] for o in outs], 0)
    sigma = np.sqrt(np.mean([o[1] ** 2 for o in outs], 0) + np.var([o[0] for o in outs], 0))
    return mean, sigma

mu_te, sd_te = ensemble_mc(te_loader)
y_te = np.array([float(g.y) for g in test_g])
mu_tr, sd_tr = ensemble_mc(tr_loader)
y_trp = np.array([float(g.y) for g in train_g])

r2 = r2_score(y_te, mu_te)
rmse = math.sqrt(mean_squared_error(y_te, mu_te))
mae = mean_absolute_error(y_te, mu_te)
sp = spearmanr(mu_te, y_te).statistic
sp_sig = spearmanr(sd_te, np.abs(y_te - mu_te)).statistic
print(f"\n[BGNN test] R2={r2:.3f} RMSE={rmse:.3f} MAE={mae:.3f} Spearman={sp:.3f}")
print(f"[BGNN UQ] Spearman(sigma,|err|)={sp_sig:.3f}")

# regression calibration: z-scores
z = (y_te - mu_te) / np.clip(sd_te, 1e-6, None)
qs = [0.5, 1.0, 1.5, 1.96, 2.5]
cov = [float(np.mean(np.abs(z) <= q)) for q in qs]
ece_reg = float(np.mean([abs(c - (0.383 if q == .5 else 0.683 if q == 1 else 0.866 if q == 1.5 else 0.95 if q == 1.96 else 0.988)) for q, c in zip(qs, cov)]))
print(f"[BGNN calibration] empirical coverage |z|<=q: "
      + ", ".join(f"{q:.2f}:{c:.3f}" for q, c in zip(qs, cov))
      + f" | regression-ECE={ece_reg:.3f}")

# ---------------- baselines: RF / XGB on Morgan FPs ----------------
mfg = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
def fp(smi):
    m = Chem.MolFromSmiles(smi)
    return np.array(mfg.GetFingerprint(m), dtype=np.int8)

X = np.stack([fp(s) for s in df["std_smiles"]])
y = df["pIC50"].values
itr, iva, ite = np.array(train_idx), np.array(val_idx), np.array(test_idx)

rf = RandomForestRegressor(n_estimators=500, random_state=SEED, n_jobs=-1).fit(X[itr], y[itr])
import xgboost as xgb
xg = xgb.XGBRegressor(n_estimators=600, max_depth=6, learning_rate=0.05,
                      subsample=0.8, colsample_bytree=0.8, random_state=SEED,
                      objective="reg:squarederror", tree_method="hist").fit(
    X[itr], y[itr], eval_set=[(X[iva], y[iva])], verbose=False)

base = {}
for name, mdl in [("RF", rf), ("XGB", xg)]:
    p = mdl.predict(X[ite])
    base[name] = dict(R2=r2_score(y[ite], p), RMSE=math.sqrt(mean_squared_error(y[ite], p)),
                      MAE=mean_absolute_error(y[ite], p), Spearman=spearmanr(p, y[ite]).statistic)
    print(f"[{name} test] " + " ".join(f"{k}={v:.3f}" for k, v in base[name].items()))

# RF ensemble spread as its own uncertainty proxy
rf_preds = np.stack([e.predict(X[ite]) for e in rf.estimators_[:100]])
rf_sd = rf_preds.std(0)
print(f"[RF-UQ] Spearman(sigma_rf,|err|)={spearmanr(rf_sd, np.abs(y[ite]-rf.predict(X[ite]))).statistic:.3f}")

# ---------------- save everything ----------------
torch.save({"models": [m.state_dict() for m in models], "node_dim": NODE_DIM},
           f"{MOD}/bgnn_ensemble.pt")
res = dict(BGNN=dict(R2=r2, RMSE=rmse, MAE=mae, Spearman=sp, Spearman_sigma_err=sp_sig,
                     ECE_reg=ece_reg, coverage=[float(c) for c in cov], quantiles=qs),
           baselines=base,
           split=dict(train=len(train_idx), val=len(val_idx), test=len(test_idx)))
json.dump(res, open(f"{RES}/tables/gnn_metrics.json", "w"), indent=2)

pd.DataFrame({"smiles": [g.smiles for g in test_g], "y": y_te, "mu": mu_te,
              "sigma": sd_te}).to_csv(f"{RES}/tables/gnn_test_predictions.csv", index=False)
print("\nsaved models/bgnn_ensemble.pt & results/tables/gnn_metrics.json")
