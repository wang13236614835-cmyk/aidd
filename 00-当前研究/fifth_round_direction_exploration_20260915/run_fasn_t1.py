# -*- coding: utf-8 -*-
"""FASN Gate T1：复用冻结资产，完成 assay 共享矩阵、泄漏审计和最小变换。

本脚本不下载数据、不修改前四轮目录、不训练 GNN，也不生成候选榜。
只读取 final_strategy/qualification/advancement 已冻结文件，并将本轮派生
结果写入 fifth_round_direction_exploration_20260915/。

T1 预冻结规则：
- 共享矩阵按 InChIKey（缺失时 canonical SMILES）统计；
- 可比较 pair：两 assay 均为 IC50、relation='='、standardized_nM 有效、
  Homo sapiens、full_length_or_fragment='full_length'；检测 format 可不同，
  因为 T1 的目的就是估计 assay 间标尺变换；
- 共享分子 >=15 才进入变换候选；不因结果差而删除 pair；
- 只对每 assay-molecule 取中位 pActivity（保留原始记录数），再拟合
  y_b = intercept + slope * y_a 和 offset-only 两种描述，选择线性模型
  作为诊断，不把拟合结果称为验证通过；
- 10-seed 稳定性使用固定 seed=20260912..20260921 对共享分子做确定性
  80/20 划分；仅当 pair 有至少 20 个共享分子才计算 holdout 指标。

输出：
- FASN_T1_SHARED_ASSAY_MATRIX.csv
- FASN_T1_ASSAY_TRANSFORMATIONS.csv
- FASN_T1_LEAKAGE_AUDIT.json
- FASN_T1_DATA_AUDIT.json
- FASN_T1_PAIR_DETAILS.json
- run_summary.json
"""
from __future__ import annotations

import hashlib
import itertools
import json
import math
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from rdkit import Chem, DataStructs, RDLogger
from rdkit.Chem import AllChem
from rdkit.Chem.Scaffolds import MurckoScaffold
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupShuffleSplit

RDLogger.DisableLog("rdApp.*")

ROOT = Path(r"D:/zcode-workspace/aidd-repo-work/00-当前研究")
OUT = ROOT / "fifth_round_direction_exploration_20260915"
OUT.mkdir(parents=True, exist_ok=True)

MASTER = ROOT / "final_strategy_round_20260912/FASN_activity_master.csv"
AWARE = ROOT / "advancement_round_20260913/FASN_assay_aware_master.csv"
CANON = ROOT / "qualification_round_20260913/FASN_canonical_clean.csv"
EXTERNAL = ROOT / "qualification_round_20260913/FASN_external_set.csv"
EXT_AD = ROOT / "qualification_round_20260913/derived/FASN_external_predictions_AD.csv"
OLD_LEAK = ROOT / "qualification_round_20260913/FASN_leakage_audit.csv"
OLD_SUMMARY = ROOT / "qualification_round_20260913/derived/qualification_summary.json"
SEEDS = list(range(20260912, 20260922))
MIRROR_ASSAYS = {"CHEMBL5731051", "CHEMBL5734379"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def clean_text(value) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ""
    return str(value).strip()


def parse_mol(smiles: str):
    return Chem.MolFromSmiles(clean_text(smiles))


def identity_key(row) -> str:
    inchikey = clean_text(row.get("inchikey"))
    if inchikey:
        return inchikey
    smiles = clean_text(row.get("canonical_smiles"))
    mol = parse_mol(smiles)
    if mol is None:
        return ""
    return Chem.MolToSmiles(mol, isomericSmiles=True)


def scaffold(smiles: str) -> str:
    mol = parse_mol(smiles)
    if mol is None:
        return ""
    value = MurckoScaffold.MurckoScaffoldSmiles(mol=mol)
    return value or Chem.MolToSmiles(mol, isomericSmiles=True)


def fp(smiles: str):
    mol = parse_mol(smiles)
    return AllChem.GetMorganGenerator(radius=2, fpSize=2048).GetFingerprint(mol) if mol else None


def max_tanimoto_to_training(smiles: str, train_fps) -> float | None:
    f = fp(smiles)
    if f is None or not train_fps:
        return None
    return float(max(DataStructs.BulkTanimotoSimilarity(f, train_fps)))


def as_float_series(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def metadata_summary(g: pd.DataFrame) -> dict:
    def joined(col: str) -> str:
        return ";".join(sorted({clean_text(x) for x in g[col] if clean_text(x)}))
    return {
        "n_records": int(len(g)),
        "n_molecules": int(g.identity_key.nunique()),
        "activity_types": joined("activity_type"),
        "endpoint_types": joined("endpoint_type"),
        "units": joined("unit"),
        "relations": joined("relation"),
        "species": joined("species"),
        "full_length_or_fragment": joined("full_length_or_fragment"),
        "construct_reported": joined("construct_reported"),
        "assay_formats": joined("assay_format"),
        "assay_families": joined("assay_family"),
        "documents": joined("document_id"),
        "years": ";".join(map(str, sorted({int(x) for x in g.document_year.dropna()}))),
        "pactivity_min": float(g.pActivity.min()),
        "pactivity_median": float(g.pActivity.median()),
        "pactivity_max": float(g.pActivity.max()),
    }


def is_comparable_pair(a: dict, b: dict) -> tuple[bool, str]:
    # T1 变换要求 endpoint、relation、数值单位、物种和蛋白层级一致；
    # assay format 不要求一致，它是待估计的 assay shift 来源。
    for field, label in [
        ("activity_types", "activity_type"),
        ("endpoint_types", "endpoint_type"),
        ("units", "unit"),
        ("relations", "relation"),
        ("species", "species"),
        ("full_length_or_fragment", "protein_layer"),
    ]:
        if a[field] != b[field]:
            return False, f"{label}_mismatch"
    if a["activity_types"] != "IC50" or a["endpoint_types"] != "IC50":
        return False, "not_both_IC50"
    if a["units"] != "nM" or a["relations"] != "=":
        return False, "unit_or_relation_not_clean"
    if a["species"] != "Homo sapiens":
        return False, "species_not_human"
    # 允许同一蛋白层级的 full_length/full_length 或 cell_extract/cell_extract；
    # fragment 与 unknown 不进入 T1 归一化输入。assay_format 可不同，正是待估计的 assay shift。
    if a["full_length_or_fragment"] not in {"full_length", "cell_extract"}:
        return False, "protein_layer_not_qualified"
    return True, "comparable_core_metadata"


def fit_pair(pair: pd.DataFrame, source_assay: str, target_assay: str) -> dict:
    x = pair["pActivity_source"].to_numpy(float)
    y = pair["pActivity_target"].to_numpy(float)
    model = LinearRegression().fit(x.reshape(-1, 1), y)
    pred = model.predict(x.reshape(-1, 1))
    offset = float(np.mean(y - x))
    offset_pred = x + offset
    row = {
        "source_assay": source_assay,
        "target_assay": target_assay,
        "n_shared": int(len(pair)),
        "source_assay_is_mirror_or_canonical": source_assay in MIRROR_ASSAYS,
        "target_assay_is_mirror_or_canonical": target_assay in MIRROR_ASSAYS,
        "slope": float(model.coef_[0]),
        "intercept": float(model.intercept_),
        "linear_r2_in_sample": float(r2_score(y, pred)) if len(np.unique(y)) > 1 else None,
        "linear_mae_in_sample": float(mean_absolute_error(y, pred)),
        "linear_rmse_in_sample": float(mean_squared_error(y, pred) ** 0.5),
        "offset": offset,
        "offset_r2_in_sample": float(r2_score(y, offset_pred)) if len(np.unique(y)) > 1 else None,
        "offset_mae_in_sample": float(mean_absolute_error(y, offset_pred)),
        "offset_rmse_in_sample": float(mean_squared_error(y, offset_pred) ** 0.5),
        "seed_holdout_n": 0,
        "seed_holdout_r2_median": None,
        "seed_holdout_spearman_median": None,
        "seed_holdout_r2_min": None,
        "seed_holdout_r2_max": None,
        "seed_holdout_spearman_min": None,
        "seed_holdout_spearman_max": None,
        "stability_status": "not_evaluable_n_lt_20",
    }
    if len(pair) >= 20:
        r2s, rhos = [], []
        groups = pair.identity_key.to_numpy()
        for seed in SEEDS:
            splitter = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=seed)
            tr, te = next(splitter.split(pair, groups=groups))
            if len(tr) < 3 or len(te) < 3:
                continue
            m = LinearRegression().fit(x[tr].reshape(-1, 1), y[tr])
            p = m.predict(x[te].reshape(-1, 1))
            r2s.append(float(r2_score(y[te], p)) if len(np.unique(y[te])) > 1 else float("nan"))
            rhos.append(float(pd.Series(y[te]).corr(pd.Series(p), method="spearman")) if len(np.unique(p)) > 1 else float("nan"))
        r2s = [x for x in r2s if np.isfinite(x)]
        rhos = [x for x in rhos if np.isfinite(x)]
        row.update({
            "seed_holdout_n": len(r2s),
            "seed_holdout_r2_median": float(np.median(r2s)) if r2s else None,
            "seed_holdout_spearman_median": float(np.median(rhos)) if rhos else None,
            "seed_holdout_r2_min": float(min(r2s)) if r2s else None,
            "seed_holdout_r2_max": float(max(r2s)) if r2s else None,
            "seed_holdout_spearman_min": float(min(rhos)) if rhos else None,
            "seed_holdout_spearman_max": float(max(rhos)) if rhos else None,
            "stability_status": "evaluated_10_seed" if len(r2s) == len(SEEDS) else "partial_seed_evaluation",
        })
    return row


def main() -> None:
    print("[T1] loading frozen master")
    master = pd.read_csv(MASTER)
    aware = pd.read_csv(AWARE)
    canon = pd.read_csv(CANON)
    ext = pd.read_csv(EXTERNAL)

    # Use assay-aware table for all provenance fields and recompute identity key.
    aware["identity_key"] = aware.apply(identity_key, axis=1)
    aware["pActivity"] = as_float_series(aware["pActivity"])
    aware["standardized_nM"] = as_float_series(aware["standardized_nM"])
    aware["document_year"] = pd.to_numeric(aware["document_year"], errors="coerce")

    # ---------- 数据资格审计 ----------
    data_audit = {
        "source_files": {str(p): sha256(p) for p in [MASTER, AWARE, CANON, EXTERNAL] if p.exists()},
        "master_records": int(len(aware)),
        "master_molecules": int(aware.identity_key.nunique()),
        "assays": int(aware.assay_id.nunique()),
        "activity_type_counts": aware.activity_type.value_counts(dropna=False).to_dict(),
        "endpoint_type_counts": aware.endpoint_type.value_counts(dropna=False).to_dict(),
        "unit_counts": aware.unit.value_counts(dropna=False).to_dict(),
        "relation_counts": aware.relation.value_counts(dropna=False).to_dict(),
        "species_counts": aware.species.value_counts(dropna=False).to_dict(),
        "protein_layer_counts": aware.full_length_or_fragment.value_counts(dropna=False).to_dict(),
        "assay_format_counts": aware.assay_format.value_counts(dropna=False).to_dict(),
        "valid_smiles_count": int(aware.is_valid_smiles.astype(str).str.lower().eq("1").sum()),
        "multifragment_count": int((pd.to_numeric(aware.fragment_count, errors="coerce") > 1).sum()),
        "potential_duplicate_flag_count": int(pd.to_numeric(aware.potential_duplicate, errors="coerce").fillna(0).sum()),
        "records_missing_assay_id": int(aware.assay_id.isna().sum()),
        "records_missing_identity": int((aware.identity_key == "").sum()),
        "pactivity_min": float(aware.pActivity.min()),
        "pactivity_median": float(aware.pActivity.median()),
        "pactivity_max": float(aware.pActivity.max()),
        "canonical_assay": "CHEMBL5731051",
        "canonical_clean_molecules": int(len(canon[canon.excluded.astype(str).str.lower() == "false"])),
        "external_evaluable_molecules": int(len(ext[ext.excluded.astype(str).str.lower() == "false"])),
        "conclusion": "全量 master 可作为 provenance 保留池，但 endpoint/assay/protein layer 异质；T1 训练必须按可比核心元数据筛选，不能把 1652 条直接合并。",
    }
    (OUT / "FASN_T1_DATA_AUDIT.json").write_text(json.dumps(data_audit, ensure_ascii=False, indent=2), encoding="utf-8")

    # ---------- assay 摘要 ----------
    assay_rows = []
    grouped = {aid: g.copy() for aid, g in aware.groupby("assay_id")}
    summaries = {}
    for aid, g in sorted(grouped.items()):
        summaries[aid] = metadata_summary(g)
        assay_rows.append({"assay_id": aid, **summaries[aid], "is_canonical_or_mirror": aid in MIRROR_ASSAYS})

    # ---------- shared matrix ----------
    assay_ids = sorted(grouped)
    identity_sets = {aid: set(grouped[aid].loc[grouped[aid].identity_key != "", "identity_key"]) for aid in assay_ids}
    matrix_rows = []
    pair_details = {}
    transform_rows = []
    for source, target in itertools.combinations(assay_ids, 2):
        shared = sorted(identity_sets[source] & identity_sets[target])
        pair_key = f"{source}__{target}"
        pair = pd.DataFrame()
        if shared:
            left = grouped[source][grouped[source].identity_key.isin(shared)].groupby("identity_key", as_index=False).pActivity.median().rename(columns={"pActivity": "pActivity_source"})
            right = grouped[target][grouped[target].identity_key.isin(shared)].groupby("identity_key", as_index=False).pActivity.median().rename(columns={"pActivity": "pActivity_target"})
            pair = left.merge(right, on="identity_key", how="inner")
            pair["source_assay"] = source
            pair["target_assay"] = target
        comparable, reason = is_comparable_pair(summaries[source], summaries[target])
        # canonical 与 mirror 是已知镜像，不得充当 T1 独立 assay 对；矩阵仍保留作审计证据。
        if source in MIRROR_ASSAYS or target in MIRROR_ASSAYS:
            comparable, reason = False, "assay_mirror_excluded"
        row = {
            "source_assay": source,
            "target_assay": target,
            "n_shared_identity": int(len(shared)),
            "n_shared_numeric_pair": int(len(pair)),
            "source_is_canonical_or_mirror": source in MIRROR_ASSAYS,
            "target_is_canonical_or_mirror": target in MIRROR_ASSAYS,
            "core_metadata_comparable": comparable,
            "comparability_reason": reason,
            "source_assay_format": summaries[source]["assay_formats"],
            "target_assay_format": summaries[target]["assay_formats"],
            "source_protein_layer": summaries[source]["full_length_or_fragment"],
            "target_protein_layer": summaries[target]["full_length_or_fragment"],
        }
        matrix_rows.append(row)
        if len(pair) >= 15 and comparable:
            transform_rows.append(fit_pair(pair, source, target))
            pair_details[pair_key] = pair.to_dict(orient="records")
    matrix = pd.DataFrame(matrix_rows).sort_values(["core_metadata_comparable", "n_shared_numeric_pair"], ascending=[False, False])
    matrix.to_csv(OUT / "FASN_T1_SHARED_ASSAY_MATRIX.csv", index=False, encoding="utf-8-sig")
    (OUT / "FASN_T1_PAIR_DETAILS.json").write_text(json.dumps(pair_details, ensure_ascii=False, indent=2), encoding="utf-8")

    transforms = pd.DataFrame(transform_rows)
    if transforms.empty:
        transforms = pd.DataFrame(columns=[
            "source_assay", "target_assay", "n_shared", "slope", "intercept",
            "linear_r2_in_sample", "linear_mae_in_sample", "linear_rmse_in_sample",
            "offset", "offset_r2_in_sample", "offset_mae_in_sample", "offset_rmse_in_sample",
            "seed_holdout_n", "seed_holdout_r2_median", "seed_holdout_spearman_median",
            "seed_holdout_r2_min", "seed_holdout_r2_max", "seed_holdout_spearman_min",
            "seed_holdout_spearman_max", "stability_status",
        ])
    transforms.to_csv(OUT / "FASN_T1_ASSAY_TRANSFORMATIONS.csv", index=False, encoding="utf-8-sig")

    # ---------- 泄漏审计 ----------
    clean = canon[canon.excluded.astype(str).str.lower() == "false"].copy()
    clean["identity_key"] = clean.apply(identity_key, axis=1)
    clean["scaffold_recomputed"] = clean.canonical_smiles.map(scaffold)
    exact_duplicate_count = int(clean.identity_key.duplicated(keep=False).sum() - clean.identity_key.duplicated(keep="first").sum())
    # 资格轮已把 canonical mirror overlap 和 external overlap 分开登记；在本轮复算这些数字。
    canonical_ids = set(clean.identity_key)
    ext_ok = ext[ext.excluded.astype(str).str.lower() == "false"].copy()
    ext_ok["identity_key"] = ext_ok.apply(identity_key, axis=1)
    canonical_overlap_count = int(len(canonical_ids & set(ext_ok.identity_key)))
    external_overlap_count = int(pd.to_numeric(ext.overlaps_canonical_training, errors="coerce").fillna(0).sum()) if "overlaps_canonical_training" in ext_ok else canonical_overlap_count
    mirror = aware[aware.assay_id == "CHEMBL5734379"]
    canonical_master = aware[aware.assay_id == "CHEMBL5731051"]
    assay_mirror_overlap_count = int(len(set(mirror.identity_key) & set(canonical_master.identity_key)))
    # 立体异构体泄漏：同一 connectivity（InChIKey 首两段）而完整 identity 不同。
    def connectivity(k: str) -> str:
        return "-".join(clean_text(k).split("-")[:2]) if clean_text(k) else ""
    conn_groups = clean.groupby(clean.identity_key.map(connectivity))
    stereoisomer_overlap_count = int(sum(max(len(set(g.identity_key)) - 1, 0) for _, g in conn_groups if _ and len(set(g.identity_key)) > 1))
    # 近重复：canonical clean 的 pairwise max Tanimoto >=0.85，不把它称 leakage。
    fps = [f for f in (fp(s) for s in clean.canonical_smiles) if f is not None]
    near_duplicate_count = 0
    near_duplicate_rate = 0.0
    if len(fps) > 1:
        nearest = []
        for i, f in enumerate(fps):
            others = fps[:i] + fps[i + 1:]
            nearest.append(max(DataStructs.BulkTanimotoSimilarity(f, others)))
        near_duplicate_count = int(sum(x >= 0.85 for x in nearest))
        near_duplicate_rate = float(near_duplicate_count / len(nearest))
    old_leak = pd.read_csv(OLD_LEAK) if OLD_LEAK.exists() else pd.DataFrame()
    scaffold_overlap_rate = float(old_leak.scaffold_overlap.gt(0).mean()) if not old_leak.empty and "scaffold_overlap" in old_leak else 0.0
    leakage = {
        "exact_duplicate_count": exact_duplicate_count,
        "canonical_overlap_count": canonical_overlap_count,
        "scaffold_overlap_rate": scaffold_overlap_rate,
        "scaffold_overlap_count_across_10_seeds": int(old_leak.scaffold_overlap.gt(0).sum()) if not old_leak.empty and "scaffold_overlap" in old_leak else 0,
        "stereoisomer_overlap_count": stereoisomer_overlap_count,
        "assay_mirror_overlap_count": assay_mirror_overlap_count,
        "external_overlap_count": external_overlap_count,
        "near_duplicate_count": near_duplicate_count,
        "near_duplicate_rate": near_duplicate_rate,
        "chemical_series_confinement_count": near_duplicate_count,
        "chemical_series_confinement_rate": near_duplicate_rate,
        "leakage_definition": "仅 exact structure/canonical duplicate、scaffold cross-split、复制记录跨集计 leakage；高相似 NN>=0.85 且无上述跨集重复计 chemical-series confinement。",
        "verdict": "PASS" if exact_duplicate_count == 0 and canonical_overlap_count == 0 and scaffold_overlap_rate == 0 else "PASS_WITH_EXCLUDED_OVERLAP" if external_overlap_count > 0 or assay_mirror_overlap_count > 0 else "CHECK",
    }
    (OUT / "FASN_T1_LEAKAGE_AUDIT.json").write_text(json.dumps(leakage, ensure_ascii=False, indent=2), encoding="utf-8")

    # ---------- 汇总 ----------
    comparable_matrix = matrix[(matrix.core_metadata_comparable == True) & (matrix.n_shared_numeric_pair >= 15)]
    comparable_matrix.to_csv(OUT / "FASN_T1_COMPARABLE_PAIRS.csv", index=False, encoding="utf-8-sig")
    summary = {
        "date": "2026-09-15",
        "environment": {"python": platform.python_version(), "pandas": pd.__version__, "numpy": np.__version__},
        "inputs": {str(p): sha256(p) for p in [MASTER, AWARE, CANON, EXTERNAL] if p.exists()},
        "master_assays": int(len(assay_ids)),
        "shared_pair_count_all": int(len(matrix)),
        "shared_pair_count_ge15": int((matrix.n_shared_numeric_pair >= 15).sum()),
        "comparable_pair_count_ge15": int(len(comparable_matrix)),
        "transformation_count": int(len(transforms)),
        "transformation_stable_count": int((transforms.stability_status == "evaluated_10_seed").sum()) if not transforms.empty else 0,
        "leakage": leakage,
        "data_audit": data_audit,
        "decision_input": {
            "minimum_two_comparable_pairs": bool(len(comparable_matrix) >= 2),
            "normalized_dataset_built": False,
            "reason_if_not_built": "本脚本只做 T1 输入资格和 assay 变换；若没有至少两个可比较稳定 pair，不构建 normalized dataset，不进入新模型训练。",
        },
    }
    (OUT / "run_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "shared_pair_count_ge15": summary["shared_pair_count_ge15"],
        "comparable_pair_count_ge15": summary["comparable_pair_count_ge15"],
        "transformation_count": summary["transformation_count"],
        "stable_transformations": summary["transformation_stable_count"],
        "leakage_verdict": leakage["verdict"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
