# -*- coding: utf-8 -*-
"""FASN canonical-assay multi-seed baseline for final strategy freeze.

This script is deliberately conservative:
- primary development scope = one human full-length FASN SPA assay (CHEMBL5731051)
- molecule-level median for duplicate records
- random split is reference only
- scaffold split is the decision-relevant internal test
- later-year data are only a heterogeneous sensitivity time split
- no external validation is silently substituted by the mirrored SPA assay
"""
from pathlib import Path
import json, math, warnings
from collections import defaultdict

import numpy as np
import pandas as pd
from rdkit import Chem, DataStructs
from rdkit.Chem import Crippen, Descriptors, Lipinski
from rdkit.Chem.AllChem import GetMorganGenerator
from rdkit.Chem.Scaffolds import MurckoScaffold
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import average_precision_score, mean_absolute_error, mean_squared_error, r2_score, roc_auc_score
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")
try:
    from xgboost import XGBRegressor
    HAVE_XGB = True
    XGB_ERROR = None
except Exception as exc:
    HAVE_XGB = False
    XGB_ERROR = repr(exc)

ROOT = Path(r"D:/zcode-workspace/aidd-repo-work/00-当前研究")
OUT = ROOT / "final_strategy_round_20260912"
MASTER = OUT / "FASN_activity_master.csv"
LIBRARY = ROOT.parent / "03-课题-MASH研究-v2/data/tcm/np_library_filtered.csv"
SEEDS = [20260912, 20260913, 20260914, 20260915, 20260916]
FP_GENERATOR = GetMorganGenerator(radius=2, fpSize=2048)


def parse(smiles):
    if smiles is None or str(smiles) == "nan":
        return None
    return Chem.MolFromSmiles(str(smiles))


def fp(smiles):
    molecule = parse(smiles)
    return FP_GENERATOR.GetFingerprint(molecule) if molecule is not None else None


def fp_matrix(smiles):
    out = np.zeros((len(smiles), 2048), dtype=np.float32)
    for i, smiles_i in enumerate(smiles):
        f = fp(smiles_i)
        if f is not None:
            DataStructs.ConvertToNumpyArray(f, out[i])
    return out


def descriptors(smiles):
    molecule = parse(smiles)
    if molecule is None:
        return [np.nan] * 10
    return [
        Descriptors.MolWt(molecule), Crippen.MolLogP(molecule), Descriptors.TPSA(molecule),
        Lipinski.NumHDonors(molecule), Lipinski.NumHAcceptors(molecule),
        Lipinski.NumRotatableBonds(molecule), Lipinski.RingCount(molecule),
        Lipinski.NumAromaticRings(molecule), Lipinski.FractionCSP3(molecule),
        Descriptors.HeavyAtomCount(molecule),
    ]


def scaffold(smiles):
    molecule = parse(smiles)
    if molecule is None:
        return ""
    value = MurckoScaffold.MurckoScaffoldSmiles(mol=molecule)
    return value or Chem.MolToSmiles(molecule, isomericSmiles=True)


def metrics(y_true, y_pred, threshold=6.0):
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    result = {
        "n": int(len(y_true)),
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": float(mean_squared_error(y_true, y_pred) ** 0.5),
        "r2": float(r2_score(y_true, y_pred)) if len(np.unique(y_true)) > 1 else None,
        "spearman": float(pd.Series(y_true).corr(pd.Series(y_pred), method="spearman")) if len(np.unique(y_pred)) > 1 else None,
    }
    y_binary = (y_true >= threshold).astype(int)
    if len(np.unique(y_binary)) == 2:
        result["roc_auc_at_pActivity_6"] = float(roc_auc_score(y_binary, y_pred))
        result["pr_auc_at_pActivity_6"] = float(average_precision_score(y_binary, y_pred))
    else:
        result["roc_auc_at_pActivity_6"] = None
        result["pr_auc_at_pActivity_6"] = None
    return result


def make_model(name, x_train, y_train, seed):
    if name == "mean":
        model = DummyRegressor(strategy="mean")
    elif name == "median":
        model = DummyRegressor(strategy="median")
    elif name == "descriptor_rf":
        model = RandomForestRegressor(n_estimators=500, max_features="sqrt", min_samples_leaf=2, random_state=seed, n_jobs=-1)
    elif name == "ecfp_rf":
        model = RandomForestRegressor(n_estimators=700, max_features="sqrt", min_samples_leaf=2, random_state=seed, n_jobs=-1)
    elif name == "ecfp_ridge":
        model = make_pipeline(StandardScaler(with_mean=False), Ridge(alpha=10.0))
    elif name == "ecfp_xgb" and HAVE_XGB:
        model = XGBRegressor(
            n_estimators=600, max_depth=5, learning_rate=0.03, subsample=0.8,
            colsample_bytree=0.7, reg_lambda=2.0, objective="reg:squarederror",
            random_state=seed, n_jobs=4,
        )
    else:
        return None, None
    model.fit(x_train, y_train)
    return model, model.predict


def split_random(data, seed):
    splitter = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=seed)
    train, test = next(splitter.split(data, groups=data["molecule_id"]))
    return train, test, {"split_group": "molecule_id", "seed": seed}


def split_scaffold(data, seed):
    splitter = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=seed)
    train, test = next(splitter.split(data, groups=data["scaffold"]))
    return train, test, {"split_group": "scaffold", "seed": seed}


def prepare_primary(master):
    data = master[
        (master.assay_id == "CHEMBL5731051")
        & (master.activity_type == "IC50")
        & (master.unit.str.lower() == "nm")
        & (master.relation == "=")
        & (master.standardized_nM > 0)
        & (master.is_valid_smiles == 1)
    ].copy()
    data["pActivity_calc"] = -np.log10(data.standardized_nM.astype(float) * 1e-9)
    data["scaffold"] = data.canonical_smiles.map(scaffold)
    data = data.groupby("molecule_id", as_index=False).agg({
        "canonical_smiles": "first", "pActivity_calc": "median", "scaffold": "first",
        "document_year": "first", "assay_id": "first", "assay_format": "first",
        "construct": "first", "assay_description": "first",
    })
    data["scope"] = "canonical_single_assay_CHEMBL5731051"
    return data.reset_index(drop=True)


def prepare_broad(master):
    data = master[
        (master.construct == "full_length_human_FASN_stated_in_assay_description")
        & (master.activity_type == "IC50")
        & (master.unit.str.lower() == "nm")
        & (master.relation == "=")
        & (master.standardized_nM > 0)
        & (master.is_valid_smiles == 1)
    ].copy()
    data["pActivity_calc"] = -np.log10(data.standardized_nM.astype(float) * 1e-9)
    data["scaffold"] = data.canonical_smiles.map(scaffold)
    data = data.sort_values(["molecule_id", "document_year", "activity_id"], na_position="last")
    data = data.groupby("molecule_id", as_index=False).agg({
        "canonical_smiles": "first", "pActivity_calc": "median", "scaffold": "first",
        "document_year": "min", "assay_id": lambda x: ";".join(sorted(set(x))),
        "assay_format": "first", "construct": "first", "assay_description": "first",
    })
    data["scope"] = "broad_full_length_stated_sensitivity"
    return data.reset_index(drop=True)


def evaluate_scope(data, scope, split_kind, seed):
    smiles = data.canonical_smiles.tolist()
    y = data.pActivity_calc.to_numpy(float)
    x_fp = fp_matrix(smiles)
    x_desc = np.asarray([descriptors(x) for x in smiles], dtype=float)
    if split_kind == "random":
        train, test, split_meta = split_random(data, seed)
    elif split_kind == "scaffold":
        train, test, split_meta = split_scaffold(data, seed)
    else:
        raise ValueError(split_kind)
    result_rows = []
    prediction_rows = []
    feature_sets = {
        "mean": x_fp, "median": x_fp, "descriptor_rf": x_desc,
        "ecfp_rf": x_fp, "ecfp_ridge": x_fp, "ecfp_xgb": x_fp,
    }
    for model_name, features in feature_sets.items():
        model, predict = make_model(model_name, features[train], y[train], seed)
        if model is None:
            continue
        pred = predict(features[test])
        row = metrics(y[test], pred)
        row.update({
            "scope": scope, "split": split_kind, "model": model_name,
            "seed": seed, "train_n": int(len(train)), "test_n": int(len(test)),
            "train_scaffolds": int(data.iloc[train].scaffold.nunique()),
            "test_scaffolds": int(data.iloc[test].scaffold.nunique()),
            **split_meta,
        })
        result_rows.append(row)
        for idx, value in zip(test, pred):
            prediction_rows.append({
                "scope": scope, "split": split_kind, "model": model_name, "seed": seed,
                "molecule_id": data.iloc[idx].molecule_id,
                "y_true": float(y[idx]), "prediction": float(value),
            })
    return result_rows, prediction_rows


def predict_library(primary):
    library = pd.read_csv(LIBRARY)
    x_train = fp_matrix(primary.canonical_smiles.tolist())
    y_train = primary.pActivity_calc.to_numpy(float)
    x_library = fp_matrix(library.smiles.tolist())
    train_fps = [fp(x) for x in primary.canonical_smiles]
    rows = []
    for model_name in ["ecfp_rf", "ecfp_xgb"]:
        model, predict = make_model(model_name, x_train, y_train, SEEDS[0])
        if model is None:
            continue
        values = predict(x_library)
        if model_name == "ecfp_rf":
            tree_values = np.vstack([tree.predict(x_library) for tree in model.estimators_])
            spread = tree_values.std(axis=0)
        else:
            spread = np.full(len(library), np.nan)
        for i, value in enumerate(values):
            f = fp(library.iloc[i].smiles)
            sims = DataStructs.BulkTanimotoSimilarity(f, train_fps) if f is not None else []
            rows.append({
                "model": model_name, "herb": library.iloc[i].herb,
                "name": library.iloc[i]["name"], "prediction_pActivity": float(value),
                "tree_sd_exploratory": None if np.isnan(spread[i]) else float(spread[i]),
                "max_Tanimoto_to_primary_training": float(max(sims)) if sims else None,
                "AD_status": "exploratory_only_no_release_threshold",
            })
    return pd.DataFrame(rows)


def main():
    OUT.joinpath("derived").mkdir(exist_ok=True)
    OUT.joinpath("logs").mkdir(exist_ok=True)
    master = pd.read_csv(MASTER)
    primary = prepare_primary(master)
    broad = prepare_broad(master)
    metrics_rows, prediction_rows = [], []
    for seed in SEEDS:
        for split_kind in ["random", "scaffold"]:
            rows, preds = evaluate_scope(primary, "canonical_single_assay", split_kind, seed)
            metrics_rows.extend(rows); prediction_rows.extend(preds)
    # One broad sensitivity time split. It is not external validation.
    time_rows = []
    if broad.document_year.nunique() >= 2:
        years = sorted(int(x) for x in broad.document_year.dropna().unique())
        cutoff = years[len(years) // 2 - 1] if len(years) > 2 else years[0]
        train = np.where((broad.document_year <= cutoff).to_numpy())[0]
        test = np.where((broad.document_year > cutoff).to_numpy())[0]
        if len(train) >= 20 and len(test) >= 10:
            smiles = broad.canonical_smiles.tolist(); y = broad.pActivity_calc.to_numpy(float); x = fp_matrix(smiles)
            for model_name in ["mean", "ecfp_rf", "ecfp_xgb"]:
                model, predict = make_model(model_name, x[train], y[train], SEEDS[0])
                if model is None: continue
                pred = predict(x[test])
                row = metrics(y[test], pred)
                row.update({
                    "scope": "broad_full_length_stated", "split": "time", "model": model_name,
                    "seed": SEEDS[0], "cutoff_year": cutoff, "train_n": int(len(train)),
                    "test_n": int(len(test)), "train_years": sorted(set(int(v) for v in broad.iloc[train].document_year)),
                    "test_years": sorted(set(int(v) for v in broad.iloc[test].document_year)),
                    "note": "heterogeneous sensitivity only; not primary model and not external validation",
                })
                time_rows.append(row); metrics_rows.append(row)
                for idx, value in zip(test, pred):
                    prediction_rows.append({"scope":"broad_full_length_stated","split":"time","model":model_name,"seed":SEEDS[0],"molecule_id":broad.iloc[idx].molecule_id,"y_true":float(y[idx]),"prediction":float(value)})
    library = predict_library(primary)
    primary.to_csv(OUT / "derived/FASN_canonical_primary_dataset.csv", index=False, encoding="utf-8-sig")
    broad.to_csv(OUT / "derived/FASN_broad_time_sensitivity_dataset.csv", index=False, encoding="utf-8-sig")
    library.to_csv(OUT / "derived/FASN_canonical_54_exploratory_predictions.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(metrics_rows).to_csv(OUT / "derived/FASN_canonical_multiseed_metrics.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(prediction_rows).to_csv(OUT / "derived/FASN_canonical_multiseed_predictions.csv", index=False, encoding="utf-8-sig")
    summary = {
        "query_date": "2026-09-12", "primary_scope": {
            "assay": "CHEMBL5731051", "molecules": int(len(primary)), "scaffolds": int(primary.scaffold.nunique()),
            "raw_exact_nM_records": 97, "mirror_assay_not_used_as_external_validation": True,
        },
        "broad_time_sensitivity": {"molecules": int(len(broad)), "years": sorted(set(int(x) for x in broad.document_year)), "results": time_rows},
        "seeds": SEEDS, "metrics": metrics_rows,
        "xgboost_available": HAVE_XGB, "xgboost_error": XGB_ERROR,
        "external_validation": {"status": "not_available_in_this_round", "reason": "the second largest SPA assay is a mirrored record set with 89 shared molecules and near-identical values; it was not treated as independent validation"},
        "candidate_release": "not_released; primary natural-product predictions are exploratory and carry no universal AD threshold",
    }
    (OUT / "derived/FASN_canonical_multiseed_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / "logs/run_fasn_canonical_multiseed.log").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
