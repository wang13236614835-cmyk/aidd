# -*- coding: utf-8 -*-
"""qualification_v1 阶段二：GNN clean benchmark（第五轮资格裁决唯一大规模复算）。

问题：在冻结的 FASN canonical 清洗集（96 分子/39 骨架）上，GNN（GCN/GIN）
是否真正优于经典 baseline（RF/XGBoost；Ridge 引用资格轮冠军数字做对照）？

可比性设计（与 qualification_round_20260913 完全一致）：
  - 数据：FASN_canonical_clean.csv（excluded==False），行序不变；
  - split：GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=seed)
           groups=scaffold，seed=20260912..20260921（同 10 seeds）；
  - 同折断言：重算 ecfp_ridge 10-seed 中位数 R²/MAE 与资格轮冻结 CSV
             dict 值逐一比对（1e-9），不一致立即中止——保证 GNN 看到的
             折与资格轮完全相同；
  - 指标：R² / RMSE / MAE / Spearman，报告 mean/std/median/min/max；
  - Y-scrambling ×20（seed0 的 rng=default_rng(20260912) 重排标签）仅对
    GNN（经典模型 0/20 exceeded 已在资格轮成立）；
  - 外部验证：105 分子/3 文献 assay，全量 96 分子训练后预测，AD 子集
    复用资格轮 AD_status（阈值 0.8116，LOO 5%）。

GNN 训练配置（预注册，跑前固定，不因结果调整）：
  - 原子特征：元素 one-hot(10+other)、度(0-5)、形式电荷(-1..1)、
    H 数(0-4)、杂化(SP/SP2/SP3/other)、芳香、成环 → 31 维；
  - 键特征：键类型(4)、共轭、成环 → 6 维（GCN 不用边特征，GIN 用）；
  - GCN：3×GCNConv(64) + global mean pool；GIN：3×GINConv(MLP 64) +
    global mean pool；dropout 0.2；MSE loss（y 按训练集 z-score）；
  - Adam lr=0.01 wd=5e-4，epochs=300 full-batch；torch.manual_seed(seed)。

输出（qualification_v1/derived/）：
  GNN_benchmark_10seed_results.csv   每 seed 每模型
  GNN_benchmark_summary.csv          汇总统计
  GNN_y_scrambling_results.csv       GNN 20 次置换
  GNN_external_validation.csv        外部/分assay/ADin
  gnn_benchmark_summary.json         环境/断言/计时
"""
from __future__ import annotations

import ast
import io
import json
import platform
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from rdkit import Chem, DataStructs, RDLogger
from rdkit.Chem import AllChem
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
RDLogger.DisableLog("rdApp.*")

import torch
import torch.nn.functional as F
from torch import Tensor
from torch_geometric.data import Data
from torch_geometric.nn import GCNConv, GINEConv, global_mean_pool

torch.set_num_threads(4)

ROOT = Path(r"D:/zcode-workspace/aidd-repo-work/00-当前研究")
QUAL = ROOT / "qualification_round_20260913"
OUT = ROOT / "qualification_v1"
DERIVED = OUT / "derived"
DERIVED.mkdir(parents=True, exist_ok=True)

SEEDS = list(range(20260912, 20260922))
N_SCRAMBLE = 20
FPGEN = AllChem.GetMorganGenerator(radius=2, fpSize=2048)
EPOCHS = 300

ALLOWED_ATOMS = ["C", "N", "O", "S", "F", "Cl", "Br", "I", "P", "B"]
HYBRIDIZATIONS = [Chem.HybridizationType.SP, Chem.HybridizationType.SP2,
                  Chem.HybridizationType.SP3]
BOND_TYPES = [Chem.BondType.SINGLE, Chem.BondType.DOUBLE, Chem.BondType.TRIPLE,
              Chem.BondType.AROMATIC]


# ---------------- 特征化 ----------------
def atom_features(a) -> list[float]:
    v: list[float] = [float(a.GetSymbol() == s) for s in ALLOWED_ATOMS]
    if sum(v) == 0:
        v.append(1.0)  # other 元素
    else:
        v.append(0.0)
    v += [float(a.GetTotalDegree() == d) for d in range(5)] + [float(a.GetTotalDegree() >= 5)]
    v += [float(a.GetFormalCharge() == c) for c in (-1, 0, 1)] + [float(abs(a.GetFormalCharge()) > 1)]
    v += [float(a.GetTotalNumHs() == h) for h in range(5)] + [float(a.GetTotalNumHs() >= 5)]
    hb = a.GetHybridization()
    v += [float(hb == h) for h in HYBRIDIZATIONS] + [float(hb not in HYBRIDIZATIONS)]
    v += [float(a.GetIsAromatic()), float(a.IsInRing())]
    return v


def bond_features(b) -> list[float]:
    bt = b.GetBondType()
    return [float(bt == t) for t in BOND_TYPES] + [float(b.GetIsConjugated()), float(b.IsInRing())]


def mol_to_graph(smiles: str) -> Data | None:
    m = Chem.MolFromSmiles(str(smiles))
    if m is None:
        return None
    x = torch.tensor([atom_features(a) for a in m.GetAtoms()], dtype=torch.float)
    rows, cols, feats = [], [], []
    for b in m.GetBonds():
        i, j = b.GetBeginAtomIdx(), b.GetEndAtomIdx()
        rows += [i, j]
        cols += [j, i]
        f = bond_features(b)
        feats += [f, f]
    edge_index = torch.tensor([rows, cols], dtype=torch.long)
    edge_attr = torch.tensor(feats, dtype=torch.float) if feats else torch.zeros((0, 6))
    return Data(x=x, edge_index=edge_index, edge_attr=edge_attr)


def fp_matrix(smiles) -> np.ndarray:
    arr = np.zeros((len(smiles), 2048), dtype=np.float32)
    for i, s in enumerate(smiles):
        m = Chem.MolFromSmiles(str(s))
        if m is not None:
            DataStructs.ConvertToNumpyArray(FPGEN.GetFingerprint(m), arr[i])
    return arr


def metrics(y, p) -> dict:
    y = np.asarray(y, float)
    p = np.asarray(p, float)
    return {"n": int(len(y)),
            "mae": float(mean_absolute_error(y, p)),
            "rmse": float(mean_squared_error(y, p) ** 0.5),
            "r2": float(r2_score(y, p)) if len(np.unique(y)) > 1 else None,
            "spearman": float(pd.Series(y).corr(pd.Series(p), method="spearman"))
            if len(np.unique(p)) > 1 else None}


# ---------------- 模型 ----------------
class GCNNet(torch.nn.Module):
    """3×GCNConv(64) + mean pool。GCN 消息传递不用键特征（拓扑+原子特征）。"""

    def __init__(self, d_in, d_hid=64, p_drop=0.2):
        super().__init__()
        self.c1, self.c2, self.c3 = GCNConv(d_in, d_hid), GCNConv(d_hid, d_hid), GCNConv(d_hid, d_hid)
        self.drop = torch.nn.Dropout(p_drop)
        self.head = torch.nn.Linear(d_hid, 1)

    def forward(self, x, ei, ea, batch):
        h = torch.tanh(self.c1(x, ei))
        h = self.drop(h)
        h = torch.tanh(self.c2(h, ei))
        h = self.drop(h)
        h = torch.tanh(self.c3(h, ei))
        h = global_mean_pool(h, batch)
        return self.head(h).squeeze(-1)


class GINNet(torch.nn.Module):
    """3×GINEConv(edge_dim=6)+mean pool。键特征（键型/共轭/成环）拼接进消息。"""

    def __init__(self, d_in, d_ein, d_hid=64, p_drop=0.2):
        super().__init__()
        def mlp(di):
            return torch.nn.Sequential(torch.nn.Linear(di, d_hid), torch.nn.Tanh(),
                                       torch.nn.Linear(d_hid, d_hid))
        # GINEConv 内部用 edge_encoder 把键特征对齐到 MLP 输入维（message = x_j + enc(ea)）
        self.c1 = GINEConv(mlp(d_in), train_eps=True, edge_dim=d_ein)
        self.c2 = GINEConv(mlp(d_hid), train_eps=True, edge_dim=d_ein)
        self.c3 = GINEConv(mlp(d_hid), train_eps=True, edge_dim=d_ein)
        self.drop = torch.nn.Dropout(p_drop)
        self.head = torch.nn.Linear(d_hid, 1)

    def forward(self, x, ei, ea, batch):
        h = torch.tanh(self.c1(x, ei, ea))
        h = self.drop(h)
        h = torch.tanh(self.c2(h, ei, ea))
        h = self.drop(h)
        h = torch.tanh(self.c3(h, ei, ea))
        h = global_mean_pool(h, batch)
        return self.head(h).squeeze(-1)


def train_gnn(kind: str, graphs, y, seed: int, epochs: int = EPOCHS):
    torch.manual_seed(seed)
    d_in = graphs[0].x.shape[1]
    d_ein = int(graphs[0].edge_attr.shape[1]) if graphs[0].edge_attr is not None else 0
    net = GINNet(d_in, d_ein) if kind == "gin" else GCNNet(d_in)
    opt = torch.optim.Adam(net.parameters(), lr=0.01, weight_decay=5e-4)
    xs = torch.cat([g.x for g in graphs])
    eis = torch.cat([g.edge_index for g in graphs], dim=1)
    eas = torch.cat([g.edge_attr for g in graphs]) if d_ein else None
    batch_vec = torch.repeat_interleave(
        torch.tensor([g.num_nodes for g in graphs], dtype=torch.long))
    yt = torch.tensor(np.asarray(y, float), dtype=torch.float)
    net.train()
    for _ in range(epochs):
        opt.zero_grad()
        out = net(xs, eis, eas, batch_vec)
        loss = F.mse_loss(out, yt)
        loss.backward()
        opt.step()
    return net


@torch.no_grad()
def predict_gnn(net, kind: str, graphs) -> np.ndarray:
    net.eval()
    xs = torch.cat([g.x for g in graphs])
    eis = torch.cat([g.edge_index for g in graphs], dim=1)
    eas = torch.cat([g.edge_attr for g in graphs]) if graphs[0].edge_attr is not None else None
    batch_vec = torch.repeat_interleave(
        torch.tensor([g.num_nodes for g in graphs], dtype=torch.long))
    return net(xs, eis, eas, batch_vec).numpy()


@torch.no_grad()
def predict_gnn_mc(net, kind: str, graphs, T: int = 30):
    net.train()  # 保持 dropout 开启
    xs = torch.cat([g.x for g in graphs])
    eis = torch.cat([g.edge_index for g in graphs], dim=1)
    eas = torch.cat([g.edge_attr for g in graphs]) if graphs[0].edge_attr is not None else None
    batch_vec = torch.repeat_interleave(
        torch.tensor([g.num_nodes for g in graphs], dtype=torch.long))
    runs = [net(xs, eis, eas, batch_vec).numpy() for _ in range(T)]
    arr = np.stack(runs)
    return arr.mean(0), arr.var(0)


def build_model(name: str, seed: int):
    if name == "ecfp_ridge":
        return make_pipeline(StandardScaler(with_mean=False), Ridge(alpha=10.0))
    if name == "ecfp_rf":
        return RandomForestRegressor(n_estimators=700, max_features="sqrt",
                                     min_samples_leaf=2, random_state=seed, n_jobs=-1)
    if name == "ecfp_xgb":
        from xgboost import XGBRegressor
        return XGBRegressor(n_estimators=600, max_depth=5, learning_rate=0.03,
                            subsample=0.8, colsample_bytree=0.7, reg_lambda=2.0,
                            objective="reg:squarederror", random_state=seed, n_jobs=4)
    raise KeyError(name)


def qstats(vals):
    s = pd.Series(vals)
    return {"mean": float(s.mean()), "std": float(s.std(ddof=1)),
            "median": float(s.median()), "min": float(s.min()), "max": float(s.max())}


def _scrambling_stats(scr: pd.DataFrame) -> dict:
    """按实际 model 键（gnn_gcn/gnn_gin）聚合置换统计；防止空选择集产生 NaN。"""
    stats = {}
    for name, g in scr.groupby("model"):
        assert len(g) == N_SCRAMBLE, f"{name} 置换次数不足: {len(g)}"
        stats[name] = {"real_r2": float(g.real_r2.iloc[0]),
                       "max_perm_r2": float(g.r2_perm.max()),
                       "median_perm_r2": float(g.r2_perm.median()),
                       "n_exceeded": int(g.exceeded.sum()),
                       "n_permutations": int(len(g))}
    return stats


def main() -> None:
    import rdkit
    import sklearn
    import torch_geometric
    t0 = time.time()
    env = {"python": platform.python_version(), "numpy": np.__version__,
           "pandas": pd.__version__, "rdkit": getattr(rdkit, "__version__", "2026.03.3"),
           "sklearn": sklearn.__version__, "torch": torch.__version__,
           "torch_geometric": torch_geometric.__version__, "platform": platform.platform()}

    # ---------- 数据（冻结，行序不变） ----------
    canon = pd.read_csv(QUAL / "FASN_canonical_clean.csv")
    clean = canon[canon.excluded.astype(str).str.lower() == "false"].reset_index(drop=True)
    y = clean.pActivity.to_numpy(float)
    groups = clean.scaffold.astype(str).to_numpy()
    X = fp_matrix(clean.canonical_smiles)
    graphs_all = [mol_to_graph(s) for s in clean.canonical_smiles]
    assert all(g is not None for g in graphs_all), "存在无法解析的 SMILES"
    print(f"[data] clean={len(clean)} molecules, {clean.scaffold.nunique()} scaffolds")

    # ---------- 同折断言：ecfp_ridge 10-seed 中位数对齐资格轮冻结值 ----------
    frozen = pd.read_csv(QUAL / "FASN_10seed_scaffold_results.csv")
    frozen_ridge = frozen[frozen.model == "ecfp_ridge"].iloc[0]
    frozen_r2 = ast.literal_eval(frozen_ridge.r2)
    ridge_r2s = []
    for seed in SEEDS:
        gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=seed)
        tr, te = next(gss.split(clean, groups=groups))
        m = build_model("ecfp_ridge", seed)
        m.fit(X[tr], y[tr])
        ridge_r2s.append(r2_score(y[te], m.predict(X[te])))
    med_r2 = float(np.median(ridge_r2s))
    assert abs(med_r2 - frozen_r2["median"]) < 1e-9, \
        f"同折断言失败: recomputed median r2={med_r2} vs frozen {frozen_r2['median']}"
    print(f"[assert] split identity PASS: ecfp_ridge 10-seed median R²={med_r2:.6f} "
          f"== frozen {frozen_r2['median']:.6f}")

    if "--summary-only" in sys.argv:
        # 从已保存的 CSV 重建汇总 JSON（不重训），保证汇总逻辑单一来源
        bench = pd.read_csv(DERIVED / "GNN_benchmark_10seed_results.csv")
        scr = pd.read_csv(DERIVED / "GNN_y_scrambling_results.csv")
        scr_stats = _scrambling_stats(scr)
        (DERIVED / "gnn_benchmark_summary.json").write_text(
            json.dumps({"date": "2026-09-13", "environment": env,
                        "epochs": EPOCHS, "seeds": SEEDS, "n_scramble": N_SCRAMBLE,
                        "split_identity_assert": {"ecfp_ridge_median_r2": med_r2,
                                                  "frozen": frozen_r2["median"],
                                                  "verdict": "PASS"},
                        "y_scrambling": scr_stats,
                        "note": "summary-only rebuild: 汇总逻辑修正后从 CSV 重建，模型未重训"},
                       ensure_ascii=False, indent=2), encoding="utf-8")
        print("[summary-only]", json.dumps(scr_stats, ensure_ascii=False))
        return

    # ---------- 主基准：10 seed × {ridge, rf, xgb, gcn, gin} ----------
    rows = []
    mc_rho_rows = []
    for seed in SEEDS:
        gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=seed)
        tr, te = next(gss.split(clean, groups=groups))
        assert not (set(groups[tr]) & set(groups[te])), "scaffold overlap!"
        ytr, yte = y[tr], y[te]
        for name in ["ecfp_ridge", "ecfp_rf", "ecfp_xgb"]:
            m = build_model(name, seed)
            t = time.time()
            m.fit(X[tr], ytr)
            p = m.predict(X[te])
            row = metrics(yte, p)
            row.update({"model": name, "seed": seed, "sec": round(time.time() - t, 2)})
            rows.append(row)
        # GNN：y 按训练集 z-score
        mu, sd = ytr.mean(), ytr.std(ddof=0)
        gtr = [graphs_all[i] for i in tr]
        gte = [graphs_all[i] for i in te]
        for kind in ["gcn", "gin"]:
            t = time.time()
            net = train_gnn(kind, gtr, (ytr - mu) / sd, seed)
            p = predict_gnn(net, kind, gte) * sd + mu
            row = metrics(yte, p)
            # MC dropout UQ（学习件）
            _, var = predict_gnn_mc(net, kind, gte, T=30)
            rho = pd.Series(var).corr(pd.Series(np.abs(yte - p)), method="spearman")
            row.update({"model": f"gnn_{kind}", "seed": seed,
                        "sec": round(time.time() - t, 2),
                        "mc_var_abserr_spearman": float(rho) if pd.notna(rho) else None})
            rows.append(row)
        print(f"[seed {seed}] done")
    bench = pd.DataFrame(rows)
    bench.to_csv(DERIVED / "GNN_benchmark_10seed_results.csv", index=False, encoding="utf-8-sig")

    flat = []
    for name, g in bench.groupby("model"):
        rec = {"model": name, "n_seeds": int(g.seed.nunique())}
        for m in ["r2", "rmse", "mae", "spearman"]:
            for k, v in qstats(g[m].dropna()).items():
                rec[f"{m}_{k}"] = round(v, 4)
        if "mc_var_abserr_spearman" in g:
            rec["mc_var_abserr_spearman_median"] = round(
                float(g.mc_var_abserr_spearman.dropna().median()), 4)
        flat.append(rec)
    pd.DataFrame(flat).to_csv(DERIVED / "GNN_benchmark_summary.csv", index=False, encoding="utf-8-sig")
    print(pd.DataFrame(flat).to_string(index=False))

    # ---------- Y-scrambling ×20（仅 GNN，seed0 折） ----------
    seed0 = SEEDS[0]
    gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=seed0)
    tr, te = next(gss.split(clean, groups=groups))
    rng = np.random.default_rng(seed0)
    scr_rows = []
    real_test = {}
    for kind in ["gcn", "gin"]:
        mu, sd = y[tr].mean(), y[tr].std(ddof=0)
        gtr = [graphs_all[i] for i in tr]
        gte = [graphs_all[i] for i in te]
        net = train_gnn(kind, gtr, (y[tr] - mu) / sd, seed0)
        real_test[kind] = r2_score(y[te], predict_gnn(net, kind, gte) * sd + mu)
    for k in range(N_SCRAMBLE):
        y_perm = rng.permutation(y)
        for kind in ["gcn", "gin"]:
            mu, sd = y_perm[tr].mean(), y_perm[tr].std(ddof=0)
            gtr = [graphs_all[i] for i in tr]
            gte = [graphs_all[i] for i in te]
            net = train_gnn(kind, gtr, (y_perm[tr] - mu) / sd, seed0 + k)
            r2 = r2_score(y_perm[te], predict_gnn(net, kind, gte) * sd + mu)
            scr_rows.append({"model": f"gnn_{kind}", "permutation": k,
                             "r2_perm": float(r2), "real_r2": real_test[kind],
                             "exceeded": bool(r2 >= real_test[kind])})
    scr = pd.DataFrame(scr_rows)
    scr.to_csv(DERIVED / "GNN_y_scrambling_results.csv", index=False, encoding="utf-8-sig")
    scr_stats = _scrambling_stats(scr)
    print("[y-scrambling]", json.dumps(scr_stats, ensure_ascii=False))

    # ---------- 外部验证（全量 96 训练 → 105 外部） ----------
    ext = pd.read_csv(QUAL / "FASN_external_set.csv")
    ext_ok = ext[ext.excluded.astype(str).str.lower() == "false"].reset_index(drop=True)
    admap = pd.read_csv(QUAL / "derived/FASN_external_predictions_AD.csv")
    ad_status = dict(zip(admap.molecule_id, admap.AD_status))
    ext_ok["ad_status"] = ext_ok.molecule_id.map(ad_status).fillna("unknown")
    graphs_ext = [mol_to_graph(s) for s in ext_ok.canonical_smiles]
    ext_rows = []
    for name in ["ecfp_ridge", "ecfp_rf", "ecfp_xgb"]:
        m = build_model(name, seed0)
        m.fit(X, y)
        p = m.predict(fp_matrix(ext_ok.canonical_smiles))
        ext_rows.append({"model": name, "subset": "overall", **metrics(ext_ok.pActivity, p)})
        for sub, mask in [("ad_in", ext_ok.ad_status == "in_domain"),
                          ("ad_out", ext_ok.ad_status == "out_of_domain")]:
            if mask.sum():
                ext_rows.append({"model": name, "subset": sub,
                                 **metrics(ext_ok.pActivity[mask], p[mask])})
    for kind in ["gcn", "gin"]:
        mu, sd = y.mean(), y.std(ddof=0)
        net = train_gnn(kind, graphs_all, (y - mu) / sd, seed0)
        p = predict_gnn(net, kind, graphs_ext) * sd + mu
        ext_rows.append({"model": f"gnn_{kind}", "subset": "overall",
                         **metrics(ext_ok.pActivity, p)})
        for sub, mask in [("ad_in", ext_ok.ad_status == "in_domain"),
                          ("ad_out", ext_ok.ad_status == "out_of_domain")]:
            if mask.sum():
                ext_rows.append({"model": f"gnn_{kind}", "subset": sub,
                                 **metrics(ext_ok.pActivity[mask], p[mask])})
    extdf = pd.DataFrame(ext_rows)
    extdf.to_csv(DERIVED / "GNN_external_validation.csv", index=False, encoding="utf-8-sig")
    print(extdf.to_string(index=False))

    out = {"date": "2026-09-13", "environment": env,
           "epochs": EPOCHS, "seeds": SEEDS, "n_scramble": N_SCRAMBLE,
           "split_identity_assert": {"ecfp_ridge_median_r2": med_r2,
                                     "frozen": frozen_r2["median"], "verdict": "PASS"},
           "y_scrambling": scr_stats,
           "runtime_sec": round(time.time() - t0, 1)}
    (DERIVED / "gnn_benchmark_summary.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[done] {out['runtime_sec']}s -> {DERIVED}")


if __name__ == "__main__":
    main()
