# -*- coding: utf-8 -*-
"""FASN provenance-aware baselines for the final strategic freeze.

The script intentionally keeps three scopes separate:
1) SPA full-length human FASN family: primary homogeneous-ish development scope;
2) broad full-length-stated subset: time sensitivity only;
3) all exact nM IC50: heterogeneity sensitivity, never a release model.
"""
from pathlib import Path
import json, math, warnings
from collections import Counter

import numpy as np
import pandas as pd
from rdkit import Chem, DataStructs
from rdkit.Chem import AllChem, Crippen, Descriptors, Lipinski
from rdkit.Chem.Scaffolds import MurckoScaffold
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import average_precision_score, mean_absolute_error, mean_squared_error, r2_score, roc_auc_score
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge

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
SEED = 20260912


def parse_mol(smiles):
    if not smiles or str(smiles) == "nan":
        return None
    try:
        return Chem.MolFromSmiles(str(smiles))
    except Exception:
        return None


def fingerprint(smiles):
    mol = parse_mol(smiles)
    if mol is None:
        return None
    return AllChem.GetMorganFingerprintAsBitVect(mol, radius=2, nBits=2048)


def fingerprint_matrix(smiles):
    arr = np.zeros((len(smiles), 2048), dtype=np.float32)
    for i, smiles_i in enumerate(smiles):
        fp = fingerprint(smiles_i)
        if fp is not None:
            DataStructs.ConvertToNumpyArray(fp, arr[i])
    return arr


def descriptor_vector(smiles):
    mol = parse_mol(smiles)
    if mol is None:
        return [np.nan] * 10
    return [
        Descriptors.MolWt(mol), Crippen.MolLogP(mol), Descriptors.TPSA(mol),
        Lipinski.NumHDonors(mol), Lipinski.NumHAcceptors(mol),
        Lipinski.NumRotatableBonds(mol), Lipinski.RingCount(mol),
        Lipinski.NumAromaticRings(mol), Lipinski.FractionCSP3(mol),
        Descriptors.HeavyAtomCount(mol),
    ]


def murcko_scaffold(smiles):
    mol = parse_mol(smiles)
    if mol is None:
        return ""
    scaffold = MurckoScaffold.MurckoScaffoldSmiles(mol=mol)
    return scaffold or Chem.MolToSmiles(mol, isomericSmiles=True)


def metric_dict(y_true, y_pred, threshold=6.0):
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    out = {
        "n": int(len(y_true)),
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": float(mean_squared_error(y_true, y_pred) ** 0.5),
        "r2": float(r2_score(y_true, y_pred)) if len(np.unique(y_true)) > 1 else None,
        "spearman": float(pd.Series(y_true).corr(pd.Series(y_pred), method="spearman")) if len(np.unique(y_pred)) > 1 else None,
    }
    y_class = (y_true >= threshold).astype(int)
    if len(np.unique(y_class)) == 2:
        out["roc_auc_at_pActivity_6"] = float(roc_auc_score(y_class, y_pred))
        out["pr_auc_at_pActivity_6"] = float(average_precision_score(y_class, y_pred))
    else:
        out["roc_auc_at_pActivity_6"] = None
        out["pr_auc_at_pActivity_6"] = None
    return out


def fit_model(name, x_train, y_train, x_test):
    if name == "mean":
        model = DummyRegressor(strategy="mean")
    elif name == "median":
        model = DummyRegressor(strategy="median")
    elif name == "descriptor_rf":
        model = RandomForestRegressor(
            n_estimators=500, max_features="sqrt", min_samples_leaf=2,
            random_state=SEED, n_jobs=-1,
        )
    elif name == "ecfp_rf":
        model = RandomForestRegressor(
            n_estimators=700, max_features="sqrt", min_samples_leaf=2,
            random_state=SEED, n_jobs=-1,
        )
    elif name == "ecfp_ridge":
        model = make_pipeline(StandardScaler(with_mean=False), Ridge(alpha=10.0))
    elif name == "ecfp_xgb" and HAVE_XGB:
        model = XGBRegressor(
            n_estimators=600, max_depth=5, learning_rate=0.03,
            subsample=0.8, colsample_bytree=0.7, reg_lambda=2.0,
            objective="reg:squarederror", random_state=SEED, n_jobs=4,
        )
    else:
        return None, None
    model.fit(x_train, y_train)
    return model, model.predict(x_test)


def make_group_split(data, group_column="scaffold", test_size=0.2):
    splitter = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=SEED)
    train_idx, test_idx = next(splitter.split(data, groups=data[group_column]))
    meta = {
        "seed": SEED,
        "test_size": test_size,
        "train_n": int(len(train_idx)),
        "test_n": int(len(test_idx)),
        "train_scaffolds": int(data.iloc[train_idx][group_column].nunique()),
        "test_scaffolds": int(data.iloc[test_idx][group_column].nunique()),
        "split_group": group_column,
    }
    return train_idx, test_idx, meta


def make_random_split(data, test_size=0.2):
    # Data are already one row per molecule, so molecule-level random split is leakage-safe.
    splitter = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=SEED)
    train_idx, test_idx = next(splitter.split(data, groups=data["molecule_id"]))
    meta = {
        "seed": SEED,
        "test_size": test_size,
        "train_n": int(len(train_idx)),
        "test_n": int(len(test_idx)),
        "train_scaffolds": int(data.iloc[train_idx].scaffold.nunique()),
        "test_scaffolds": int(data.iloc[test_idx].scaffold.nunique()),
        "split_group": "molecule_id",
    }
    return train_idx, test_idx, meta


def prepare_scope(master, scope):
    df = master[(master.activity_type == "IC50") & (master.standardized_nM > 0) & (master.is_valid_smiles == 1)].copy()
    df["pActivity_calc"] = -np.log10(df.standardized_nM.astype(float) * 1e-9)
    df["year_num"] = pd.to_numeric(df.document_year, errors="coerce")
    df["scaffold"] = df.canonical_smiles.map(murcko_scaffold)
    if scope == "spa_family":
        assays = {"CHEMBL5731051", "CHEMBL5734379"}
        df = df[df.assay_id.isin(assays) & df.unit.str.lower().eq("nm")].copy()
        # Median per molecule is explicit; raw assay records remain in master.
        df = df.groupby("molecule_id", as_index=False).agg({
            "canonical_smiles": "first", "pActivity_calc": "median", "scaffold": "first",
            "year_num": "min", "assay_id": lambda x: ";".join(sorted(set(x))),
            "assay_format": "first", "construct": "first", "assay_description": "first",
        })
        df["scope_note"] = "two full-length human FASN SPA assays; molecule-level median; primary development scope, still assay-family not identical assay"
    elif scope == "full_length_stated":
        df = df[(df.construct == "full_length_human_FASN_stated_in_assay_description") & df.unit.str.lower().eq("nm")].copy()
        df = df.sort_values(["molecule_id", "year_num", "activity_id"], na_position="last").groupby("molecule_id", as_index=False).agg({
            "canonical_smiles": "first", "pActivity_calc": "median", "scaffold": "first",
            "year_num": "min", "assay_id": lambda x: ";".join(sorted(set(x))),
            "assay_format": "first", "construct": "first", "assay_description": "first",
        })
        df["scope_note"] = "broad full-length-stated subset; assay heterogeneity retained as sensitivity analysis"
    elif scope == "all_ic50_nM":
        df = df[df.unit.str.lower().eq("nm")].copy()
        df = df.sort_values(["molecule_id", "year_num", "activity_id"], na_position="last").groupby("molecule_id", as_index=False).agg({
            "canonical_smiles": "first", "pActivity_calc": "median", "scaffold": "first",
            "year_num": "min", "assay_id": lambda x: ";".join(sorted(set(x))),
            "assay_format": "first", "construct": "first", "assay_description": "first",
        })
        df["scope_note"] = "all exact nM IC50; heterogeneous assay family; sensitivity only, not a release dataset"
    else:
        raise ValueError(scope)
    return df.reset_index(drop=True)


def run_scope(data, scope, split_names):
    smiles = data.canonical_smiles.tolist()
    y = data.pActivity_calc.to_numpy(float)
    x_fp = fingerprint_matrix(smiles)
    x_desc = np.asarray([descriptor_vector(x) for x in smiles], dtype=float)
    results = []
    prediction_rows = []
    for split_name in split_names:
        if split_name == "random":
            train_idx, test_idx, split_meta = make_random_split(data)
        elif split_name == "scaffold":
            train_idx, test_idx, split_meta = make_group_split(data, "scaffold")
        else:
            raise ValueError(split_name)
        feature_sets = {"descriptor_rf": x_desc, "ecfp_rf": x_fp, "ecfp_ridge": x_fp, "ecfp_xgb": x_fp, "mean": x_fp, "median": x_fp}
        for model_name, features in feature_sets.items():
            if model_name in {"mean", "median"} or not np.isfinite(features).all():
                if model_name in {"mean", "median"}:
                    model, pred = fit_model(model_name, features[train_idx], y[train_idx], features[test_idx])
                else:
                    continue
            else:
                model, pred = fit_model(model_name, features[train_idx], y[train_idx], features[test_idx])
            if model is None:
                continue
            metrics = metric_dict(y[test_idx], pred)
            metrics.update({"scope": scope, "split": split_name, "model": model_name, **split_meta})
            results.append(metrics)
            for idx, value in zip(test_idx, pred):
                prediction_rows.append({
                    "scope": scope, "split": split_name, "model": model_name,
                    "molecule_id": data.iloc[idx].molecule_id,
                    "y_true": float(y[idx]), "prediction": float(value),
                })
    return results, prediction_rows


def predict_library(strict_data):
    library = pd.read_csv(LIBRARY)
    library["scaffold"] = library.smiles.map(murcko_scaffold)
    x_train = fingerprint_matrix(strict_data.canonical_smiles.tolist())
    y_train = strict_data.pActivity_calc.to_numpy(float)
    x_library = fingerprint_matrix(library.smiles.tolist())
    train_fps = [fingerprint(x) for x in strict_data.canonical_smiles]
    rows = []
    for model_name in ["ecfp_rf", "ecfp_xgb"]:
        model, pred = fit_model(model_name, x_train, y_train, x_library)
        if model is None:
            continue
        if model_name == "ecfp_rf":
            tree_values = np.vstack([tree.predict(x_library) for tree in model.estimators_])
            uncertainty = tree_values.std(axis=0)
        else:
            uncertainty = np.full(len(library), np.nan)
        for i, value in enumerate(pred):
            fp_i = fingerprint(library.iloc[i].smiles)
            similarities = DataStructs.BulkTanimotoSimilarity(fp_i, train_fps) if fp_i is not None else []
            rows.append({
                "model": model_name,
                "herb": library.iloc[i].herb,
                "name": library.iloc[i]["name"],
                "prediction_pActivity": float(value),
                "tree_sd_exploratory": None if np.isnan(uncertainty[i]) else float(uncertainty[i]),
                "max_Tanimoto_to_primary_training": float(max(similarities)) if similarities else None,
                "AD_status": "exploratory_OOD_or_unassessed",
            })
    return pd.DataFrame(rows)


def main():
    OUT.joinpath("derived").mkdir(exist_ok=True)
    OUT.joinpath("logs").mkdir(exist_ok=True)
    master = pd.read_csv(MASTER)
    primary = prepare_scope(master, "spa_family")
    broad = prepare_scope(master, "full_length_stated")
    all_ic50 = prepare_scope(master, "all_ic50_nM")
    all_metrics = []
    all_predictions = []
    primary_metrics, primary_predictions = run_scope(primary, "spa_family", ["random", "scaffold"])
    all_metrics.extend(primary_metrics); all_predictions.extend(primary_predictions)
    broad_metrics, broad_predictions = run_scope(broad, "full_length_stated", ["random", "scaffold"])
    all_metrics.extend(broad_metrics); all_predictions.extend(broad_predictions)
    all_ic50_metrics, all_ic50_predictions = run_scope(all_ic50, "all_ic50_nM", ["random", "scaffold"])
    all_metrics.extend(all_ic50_metrics); all_predictions.extend(all_ic50_predictions)
    # Chronological sensitivity: broad subset grouped by molecule's earliest available year.
    time_metrics = []
    if broad.year_num.notna().sum() and broad.year_num.nunique() >= 2:
        years = sorted(broad.year_num.dropna().unique())
        cutoff = years[max(0, len(years) // 2 - 1)]
        train_idx = np.where((broad.year_num <= cutoff).to_numpy())[0]
        test_idx = np.where((broad.year_num > cutoff).to_numpy())[0]
        if len(train_idx) >= 20 and len(test_idx) >= 10:
            x = fingerprint_matrix(broad.canonical_smiles.tolist())
            y = broad.pActivity_calc.to_numpy(float)
            meta = {"scope": "full_length_stated", "split": "time", "cutoff_year": int(cutoff), "train_n": int(len(train_idx)), "test_n": int(len(test_idx)), "train_years": [int(v) for v in sorted(set(broad.iloc[train_idx].year_num))], "test_years": [int(v) for v in sorted(set(broad.iloc[test_idx].year_num))], "note": "sensitivity only; assay-family heterogeneity and small late cohort"}
            for model_name in ["mean", "ecfp_rf", "ecfp_xgb"]:
                model, pred = fit_model(model_name, x[train_idx], y[train_idx], x[test_idx])
                if model is None:
                    continue
                metric = metric_dict(y[test_idx], pred)
                metric.update({"model": model_name, **meta})
                time_metrics.append(metric)
                for idx, value in zip(test_idx, pred):
                    all_predictions.append({"scope": "full_length_stated", "split": "time", "model": model_name, "molecule_id": broad.iloc[idx].molecule_id, "y_true": float(y[idx]), "prediction": float(value)})
            all_metrics.extend(time_metrics)
    library_predictions = predict_library(primary)
    library_predictions.to_csv(OUT / "derived/FASN_primary_54_exploratory_predictions.csv", index=False, encoding="utf-8-sig")
    primary.to_csv(OUT / "derived/FASN_primary_SPA_family_dataset.csv", index=False, encoding="utf-8-sig")
    broad.to_csv(OUT / "derived/FASN_broad_full_length_dataset.csv", index=False, encoding="utf-8-sig")
    all_ic50.to_csv(OUT / "derived/FASN_all_IC50_nM_dataset.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(all_metrics).to_csv(OUT / "derived/FASN_baseline_metrics.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(all_predictions).to_csv(OUT / "derived/FASN_baseline_predictions.csv", index=False, encoding="utf-8-sig")
    summary = {
        "query_date": "2026-09-12",
        "primary_scope": {"name": "spa_family", "records_after_molecule_median": int(len(primary)), "scaffolds": int(primary.scaffold.nunique()), "assays": sorted(set(";".join(primary.assay_id).split(";")))},
        "broad_scope": {"name": "full_length_stated", "records_after_molecule_median": int(len(broad)), "scaffolds": int(broad.scaffold.nunique())},
        "all_ic50_scope": {"name": "all_ic50_nM", "records_after_molecule_median": int(len(all_ic50)), "scaffolds": int(all_ic50.scaffold.nunique())},
        "time_metrics": time_metrics,
        "metrics": all_metrics,
        "xgboost_available": HAVE_XGB,
        "xgboost_error": XGB_ERROR,
        "primary_library_prediction_rows": int(len(library_predictions)),
        "primary_library_AD_note": "No universal AD threshold was imposed; Tanimoto and RF tree spread are exploratory diagnostics only.",
    }
    (OUT / "derived/FASN_baseline_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / "logs/run_fasn_baseline.log").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
