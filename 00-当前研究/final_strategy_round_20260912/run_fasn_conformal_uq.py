# -*- coding: utf-8 -*-
"""FASN conformal/UQ diagnostic for the final strategic freeze.

This is a diagnostic, not a candidate-release model.  Train/calibration/test
are scaffold-disjoint.  The mirrored SPA assay is deliberately not used as
an external test set.
"""
from pathlib import Path
import json
import warnings

import numpy as np
import pandas as pd
from rdkit import Chem, DataStructs
from rdkit.Chem.AllChem import GetMorganGenerator
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GroupShuffleSplit

warnings.filterwarnings("ignore")
try:
    from xgboost import XGBRegressor
    HAVE_XGB = True
except Exception:
    HAVE_XGB = False

ROOT = Path(r"D:/zcode-workspace/aidd-repo-work/00-当前研究")
OUT = ROOT / "final_strategy_round_20260912"
DATA = OUT / "derived/FASN_canonical_primary_dataset.csv"
LIBRARY = ROOT.parent / "03-课题-MASH研究-v2/data/tcm/np_library_filtered.csv"
FPGEN = GetMorganGenerator(radius=2, fpSize=2048)
SEEDS = [20260912, 20260913, 20260914, 20260915, 20260916]


def parse(s):
    return Chem.MolFromSmiles(str(s))


def fp(s):
    return FPGEN.GetFingerprint(parse(s))


def matrix(smiles):
    out = np.zeros((len(smiles), 2048), dtype=np.float32)
    for i, s in enumerate(smiles):
        DataStructs.ConvertToNumpyArray(fp(s), out[i])
    return out


def fit(name, x, y, seed):
    if name == "ecfp_rf":
        model = RandomForestRegressor(
            n_estimators=700, max_features="sqrt", min_samples_leaf=2,
            random_state=seed, n_jobs=-1,
        )
    elif name == "ecfp_xgb" and HAVE_XGB:
        model = XGBRegressor(
            n_estimators=600, max_depth=5, learning_rate=0.03,
            subsample=0.8, colsample_bytree=0.7, reg_lambda=2.0,
            objective="reg:squarederror", random_state=seed, n_jobs=4,
        )
    else:
        return None
    model.fit(x, y)
    return model


def conformal_quantile(residuals, alpha):
    residuals = np.sort(np.asarray(residuals, dtype=float))
    n = len(residuals)
    # finite-sample split-conformal upper order statistic
    rank = int(np.ceil((n + 1) * (1.0 - alpha))) - 1
    rank = min(max(rank, 0), n - 1)
    return float(residuals[rank])


def run_one(data, seed, model_name):
    # First hold out test scaffolds, then split the remaining scaffolds for calibration.
    first = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=seed)
    train_cal, test = next(first.split(data, groups=data.scaffold))
    train_cal_data = data.iloc[train_cal]
    second = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=seed + 1000)
    train_rel, cal_rel = next(second.split(train_cal_data, groups=train_cal_data.scaffold))
    train = train_cal[train_rel]
    cal = train_cal[cal_rel]
    x = matrix(data.canonical_smiles.tolist())
    y = data.pActivity_calc.to_numpy(float)
    model = fit(model_name, x[train], y[train], seed)
    if model is None:
        return None
    pred_cal = model.predict(x[cal])
    pred_test = model.predict(x[test])
    rows = []
    for alpha in [0.10, 0.20]:
        q = conformal_quantile(np.abs(y[cal] - pred_cal), alpha)
        coverage = float(np.mean((y[test] >= pred_test - q) & (y[test] <= pred_test + q)))
        rows.append({
            "model": model_name, "seed": seed, "alpha": alpha,
            "train_n": int(len(train)), "cal_n": int(len(cal)), "test_n": int(len(test)),
            "train_scaffolds": int(data.iloc[train].scaffold.nunique()),
            "cal_scaffolds": int(data.iloc[cal].scaffold.nunique()),
            "test_scaffolds": int(data.iloc[test].scaffold.nunique()),
            "q_abs_residual_pActivity": q,
            "test_coverage": coverage,
            "mean_interval_width_pActivity": float(2 * q),
            "test_mae": float(np.mean(np.abs(y[test] - pred_test))),
            "test_rmse": float(np.sqrt(np.mean((y[test] - pred_test) ** 2))),
        })
    return rows


def main():
    data = pd.read_csv(DATA)
    data["pActivity_calc"] = data["pActivity_calc"].astype(float)
    result = []
    for seed in SEEDS:
        for model_name in ["ecfp_rf", "ecfp_xgb"]:
            rows = run_one(data, seed, model_name)
            if rows:
                result.extend(rows)
    result_df = pd.DataFrame(result)
    result_df.to_csv(OUT / "derived/FASN_conformal_uq_results.csv", index=False, encoding="utf-8-sig")
    # Library AD diagnostic against all canonical training molecules.
    library = pd.read_csv(LIBRARY)
    train_fps = [fp(s) for s in data.canonical_smiles]
    ad_rows = []
    for _, row in library.iterrows():
        f = fp(row.smiles)
        similarities = DataStructs.BulkTanimotoSimilarity(f, train_fps)
        ad_rows.append({
            "herb": row.herb, "name": row["name"],
            "max_Tanimoto_to_canonical_training": float(max(similarities)),
            "AD_status": "exploratory_OOD_no_release_threshold",
        })
    ad_df = pd.DataFrame(ad_rows)
    ad_df.to_csv(OUT / "derived/FASN_canonical_library_AD.csv", index=False, encoding="utf-8-sig")
    summary = {
        "date": "2026-09-12",
        "dataset": "CHEMBL5731051 one-row-per-molecule canonical SPA assay",
        "n_molecules": int(len(data)),
        "n_scaffolds": int(data.scaffold.nunique()),
        "seeds": SEEDS,
        "results": result,
        "library_AD": {
            "n": int(len(ad_df)),
            "min_max_Tanimoto": float(ad_df.max_Tanimoto_to_canonical_training.min()),
            "median_max_Tanimoto": float(ad_df.max_Tanimoto_to_canonical_training.median()),
            "max_max_Tanimoto": float(ad_df.max_Tanimoto_to_canonical_training.max()),
        },
        "interpretation": "Scaffold-disjoint split-conformal diagnostic only; no external validation and no candidate release.",
    }
    (OUT / "derived/FASN_conformal_uq_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / "logs/run_fasn_conformal_uq.log").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
