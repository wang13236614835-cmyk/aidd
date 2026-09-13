# -*- coding: utf-8 -*-
"""qualification_v1 阶段一：FASN 数据 assay-level provenance 审计（只读）。

输入（全部已冻结资产，不修改）：
  - final_strategy_round_20260912/FASN_activity_master.csv   1652 条记录级 lineage
  - qualification_round_20260913/FASN_canonical_clean.csv    canonical 清洗集
  - qualification_round_20260913/FASN_external_set.csv       外部验证集
  - advancement_round_20260913/FASN_assay_aware_master.csv   assay 感知主表

输出：
  - derived/ASSAY_PROVENANCE.csv  每个 assay 一行：规模/类型/物种/文档/年份/角色/被谁使用
  - derived/provenance_audit.json 审计结论（覆盖检查、缺失 lineage 计数）
"""
from __future__ import annotations

import io
import json
import platform
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(r"D:/zcode-workspace/aidd-repo-work/00-当前研究")
OUT = ROOT / "qualification_v1"
DERIVED = OUT / "derived"
DERIVED.mkdir(parents=True, exist_ok=True)

MASTER = ROOT / "final_strategy_round_20260912/FASN_activity_master.csv"
CANON = ROOT / "qualification_round_20260913/FASN_canonical_clean.csv"
EXT = ROOT / "qualification_round_20260913/FASN_external_set.csv"
ASSAY_AWARE = ROOT / "advancement_round_20260913/FASN_assay_aware_master.csv"

CANONICAL_ASSAY = "CHEMBL5731051"
MIRROR_ASSAY = "CHEMBL5734379"


def main() -> None:
    master = pd.read_csv(MASTER)
    canon = pd.read_csv(CANON)
    ext = pd.read_csv(EXT)

    clean = canon[canon.excluded.astype(str).str.lower() == "false"].copy()
    ext_ok = ext[ext.excluded.astype(str).str.lower() == "false"].copy()

    # canonical / external 实际用到的 assay 集合
    canon_assays = set(clean.activity_ids.astype(str).str.split(";").explode()) if "activity_ids" in clean else set()
    ext_assays = set()
    for s in ext_ok.assay_ids.astype(str):
        ext_assays.update(a for a in s.split(";") if a)

    rows = []
    for aid, g in master.groupby("assay_id"):
        docs = sorted(set(g.document_id.astype(str)))
        years = sorted(set(g.document_year.dropna().astype(int)))
        pmids = sorted({p for p in g.PMID.dropna().astype(str) if p and p.lower() != "nan"})
        if aid == CANONICAL_ASSAY:
            role = "canonical_training"
        elif aid == MIRROR_ASSAY:
            role = "mirror_excluded"
        elif aid in ext_assays:
            role = "external_validation"
        elif aid in canon_assays:
            role = "canonical_merged_records"
        else:
            role = "unused_by_frozen_sets"
        rows.append({
            "assay_id": aid,
            "n_records": int(len(g)),
            "n_molecules": int(g.molecule_id.nunique()),
            "assay_type": ";".join(sorted(set(g.assay_type.astype(str)))),
            "assay_format": ";".join(sorted(set(g.assay_format.astype(str)))),
            "biochemical_or_cellular": ";".join(sorted(set(g.biochemical_or_cellular.astype(str)))),
            "species": ";".join(sorted(set(g.species.astype(str)))),
            "activity_types": ";".join(sorted(set(g.activity_type.astype(str)))),
            "n_documents": len(docs),
            "document_ids": ";".join(docs),
            "years": ";".join(map(str, years)),
            "pmids": ";".join(pmids),
            "role_in_frozen_pipeline": role,
        })
    prov = pd.DataFrame(rows).sort_values(["role_in_frozen_pipeline", "n_records"], ascending=[True, False])
    prov.to_csv(DERIVED / "ASSAY_PROVENANCE.csv", index=False, encoding="utf-8-sig")

    # 覆盖检查：训练/外部用到的每个分子-活性记录是否都有 assay lineage
    missing_lineage = int(master.assay_id.isna().sum())
    canon_activity_ids = set()
    for s in clean.activity_ids.astype(str):
        canon_activity_ids.update(a for a in s.split(";") if a)
    uncovered_canon = len([a for a in canon_activity_ids if a not in set(master.activity_id.astype(str))])

    ext_overlap = int(ext_ok.overlaps_canonical_training.astype(str).str.lower().eq("true").sum()) if "overlaps_canonical_training" in ext_ok else -1

    audit = {
        "date": "2026-09-13",
        "environment": {"python": platform.python_version(), "pandas": pd.__version__, "numpy": np.__version__},
        "master_records": int(len(master)),
        "master_assays": int(master.assay_id.nunique()),
        "records_missing_assay_id": missing_lineage,
        "canonical_clean_molecules": int(len(clean)),
        "canonical_activity_ids_not_in_master": uncovered_canon,
        "external_molecules": int(len(ext_ok)),
        "external_assays": sorted(ext_assays),
        "external_overlapping_canonical_flagged": ext_overlap,
        "role_counts": prov.role_in_frozen_pipeline.value_counts().to_dict(),
        "verdict": "PASS" if (missing_lineage == 0 and uncovered_canon == 0 and ext_overlap == 0) else "CHECK",
        "notes": [
            "canonical=CHEMBL5731051 (96分子/39骨架)；mirror=CHEMBL5734379 已排除",
            "外部集 3 个文献 assay，与 canonical 训练重叠分子已在资格轮排除",
            "未进入冻结训练/外部集的 assay 记录保留在 master 中作历史/复评池",
        ],
    }
    (DERIVED / "provenance_audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(audit, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
