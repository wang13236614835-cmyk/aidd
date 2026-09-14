# -*- coding: utf-8 -*-
"""构建 asset_preservation_and_gnn_replan_v1 的统一资产登记表。

只读扫描三个仓库中已存在的高价值文件/目录 bundle；不移动、不改写、不删除旧资产。
目录 bundle 的 hash 是按相对路径+文件 SHA-256 排序后计算的清单哈希，便于审计而不复制大型结果树。
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

AIDD = Path(r"D:/zcode-workspace/aidd-repo-work")
GNN = Path(r"D:/zcode-workspace/hepato-gnn-screening")
WB = Path(r"D:/aidd destoop")
OUT = AIDD / "00-当前研究/asset_preservation_and_gnn_replan_v1"

FIELDS = [
    "asset_id", "repository", "relative_path", "asset_type", "target",
    "source_round", "qualification_status", "evidence_level", "current_role",
    "superseded_by", "hash", "bytes", "file_count", "path_status", "notes",
]

# 高价值资产登记：状态针对“能支持什么”，不等同于文件是否存在。
SPECS = [
    ("AIDD-FASN-RAW-001", "aidd", "00-当前研究/final_strategy_round_20260912/raw/FASN_all_activity_records.json", "raw_activity", "FASN", "最终战略冻结轮", "VERIFIED", "high", "原始响应保留", "", "ChEMBL 全量原始快照；不把派生聚合标签倒写回原始层"),
    ("AIDD-FASN-MASTER-001", "aidd", "00-当前研究/final_strategy_round_20260912/FASN_activity_master.csv", "master_table", "FASN", "最终战略冻结轮", "VERIFIED", "high", "当前 assay-aware 数据入口", "", "1652 条/51 assay；记录级 provenance 完整"),
    ("AIDD-FASN-AWARE-001", "aidd", "00-当前研究/advancement_round_20260913/FASN_assay_aware_master.csv", "assay_aware_table", "FASN", "推进轮", "VERIFIED", "high", "Gate T1 的输入候选", "", "新增 assay family/检测体系字段；unknown 不猜测"),
    ("AIDD-FASN-CANON-001", "aidd", "00-当前研究/qualification_round_20260913/FASN_canonical_clean.csv", "qualified_dataset", "FASN", "资格验证轮", "VERIFIED", "high", "当前 canonical 模型数据", "", "96 分子/39 scaffold；仅限 CHEMBL5731051"),
    ("AIDD-FASN-EXT-001", "aidd", "00-当前研究/qualification_round_20260913/FASN_external_set.csv", "external_dataset", "FASN", "资格验证轮", "VERIFIED", "high", "独立外部验证输入", "", "105 分子/3 文献 assay；与训练不重叠"),
    ("AIDD-FASN-OLD-SPLIT-001", "aidd", "00-当前研究/validation/20260905/FASN_diagnostic_split.csv", "historical_split", "FASN", "诊断轮", "HISTORICAL", "medium", "历史 split/错误分析参考", "00-当前研究/qualification_round_20260913/FASN_canonical_clean.csv", "旧 split 不能支持当前泛化主张；原文件和 hash 保留"),
    ("AIDD-FASN-OLD-PRED-001", "aidd", "03-课题-MASH研究-v2/results/tables/FASN_cluster_split_testpred.csv", "historical_predictions", "FASN", "MASH v2", "HISTORICAL", "low", "历史方法对照/复盘", "00-当前研究/qualification_round_20260913/derived/GNN_benchmark_10seed_results.csv", "旧聚类 split 预测可读；不作为当前 external/scaffold 证据"),
    ("AIDD-FASN-BENCH-001", "aidd", "00-当前研究/qualification_round_20260913/FASN_10seed_scaffold_results.csv", "benchmark_results", "FASN", "资格验证轮", "VERIFIED", "high", "canonical baseline 证据", "", "Ridge/RF/XGB/mean；10 seed scaffold"),
    ("AIDD-FASN-GNN-001", "aidd", "00-当前研究/qualification_v1/derived/GNN_benchmark_summary.csv", "benchmark_results", "FASN/GNN", "qualification_v1", "VERIFIED", "high", "GNN enable gate 阴性证据", "", "同折 GCN/GINE 未优于 Ridge/XGB；只限当前数据规模"),
    ("AIDD-FASN-Y-001", "aidd", "00-当前研究/qualification_round_20260913/FASN_y_scrambling_results.csv", "permutation_results", "FASN", "资格验证轮", "VERIFIED", "high", "非伪学习证据", "", "0/20 exceeded 经典 baseline"),
    ("AIDD-FASN-LEAK-001", "aidd", "00-当前研究/qualification_round_20260913/FASN_leakage_audit.csv", "leakage_audit", "FASN", "资格验证轮", "VERIFIED", "high", "同折泄漏审计", "", "结构重复/scaffold 共享/复制跨集为零；高相似另标 chemical-series confinement"),
    ("AIDD-FASN-EXTRES-001", "aidd", "00-当前研究/qualification_round_20260913/FASN_external_validation.md", "external_validation", "FASN", "资格验证轮", "VERIFIED", "high", "跨 assay 阴性证据", "", "Ridge R² 0.180；分 assay 全负；不得重写成泛化通过"),
    ("AIDD-FASN-ADUQ-001", "aidd", "00-当前研究/qualification_round_20260913/FASN_AD_UQ_report.md", "ad_uq_report", "FASN", "资格验证轮", "VERIFIED", "high", "AD/UQ 限定证据", "", "内部有效/外部 conformal 失效"),
    ("AIDD-FASN-SCRIPT-001", "aidd", "00-当前研究/final_strategy_round_20260912/run_fasn_canonical_multiseed.py", "reproduction_code", "FASN", "最终战略冻结轮", "VERIFIED", "medium", "历史/当前复现参考代码", "", "不覆盖新 qualification_v1 脚本"),
    ("AIDD-FXR-DATA-001", "aidd", "00-当前研究/candidate_decision_20260910/chembl_fxr_data.csv", "activity_table", "FXR", "候选决策轮", "VERIFIED", "medium", "FXR evidence-anchor 数据", "", "实际模型过滤条件和 assay 需按 manifest 读取"),
    ("AIDD-FXR-MODEL-001", "aidd", "00-当前研究/candidate_decision_20260910/derived/fxr_locked_model", "model_bundle", "FXR", "候选决策轮", "VERIFIED", "medium", "内部 scaffold reproducibility reference", "", "模型可读且 locked test 未用于训练；不是外部验证/候选放行"),
    ("AIDD-FXR-MANIFEST-001", "aidd", "00-当前研究/candidate_decision_20260910/derived/fxr_locked_model/model_manifest.json", "model_manifest", "FXR", "候选决策轮", "VERIFIED", "high", "FXR 模型 provenance", "", "threshold_pActivity=8；10 nM 是该 assay-specific label，不作普适阈值；2026-09-14 仅修正文案并加入 metadata_correction"),
    ("AIDD-FXR-MANIFEST-LEGACY-001", "aidd", "00-当前研究/asset_preservation_and_gnn_replan_v1/legacy_metadata/fxr_model_manifest_pre_20260914.json", "legacy_metadata", "FXR", "asset preservation v1", "HISTORICAL", "medium", "修正前元数据审计保留", "00-当前研究/candidate_decision_20260910/derived/fxr_locked_model/model_manifest.json", "旧 threshold_note 含 100 nM；SHA-256=305f49757f2250e70e898ce41b49431397de1b9b59896a808462e0d01e5e40fb"),
    ("AIDD-THRB-2J4A-001", "aidd", "03-课题-MASH研究-v2/data/pdb/2J4A.pdb", "receptor_structure", "THRβ", "历史结构线", "HISTORICAL", "medium", "mutant_receptor_exploratory 原始结构", "00-当前研究/h1_mash/WTfull.pdb", "2J4A/N331S 历史受体；保留原始 PDB，不支持 WT 泛化"),
    ("AIDD-THRB-2J4A-002", "aidd", "03-课题-MASH研究-v2/docking/receptors/THRB_2J4A.pdbqt", "prepared_receptor", "THRβ", "历史结构线", "HISTORICAL", "medium", "历史对接复现输入", "", "N331S mutant receptor prepared file"),
    ("AIDD-THRB-WT-GATE-001", "aidd", "00-当前研究/fifth_round_20260912/derived/wt_gate_run", "docking_bundle", "THRβ", "第五轮候选审计", "VERIFIED", "high", "docking ranking failure evidence", "", "78 配体日志/输出；WT ROC-AUC 0.472，证明排序门失败"),
    ("AIDD-THRB-OLD-PRED-001", "aidd", "03-课题-MASH研究-v2/results/tables/THRB_cluster_split_testpred.csv", "historical_predictions", "THRβ", "MASH v2", "HISTORICAL", "low", "历史模型/方法对照", "00-当前研究/fifth_round_20260912/WT_gate_results.md", "不得用于 candidate ranking 或 selectivity 结论"),
    ("AIDD-DOCK-JOBS-001", "aidd", "00-当前研究/candidate_decision_20260910/raw/dockscope_job_manifest.json", "docking_manifest", "多靶点", "候选决策轮", "VERIFIED", "medium", "历史执行 provenance", "", "保留任务参数和文件映射；docking 只作结构假说"),
    ("AIDD-DOCK-RANK-001", "aidd", "00-当前研究/fifth_round_20260912/候选榜单_v3_释放版.md", "candidate_ranking_interpretation", "多靶点", "第五轮候选审计", "REJECTED", "high", "历史错误解释留档", "00-当前研究/qualification_v1/RESEARCH_STATE.md", "旧 docking/综合榜单解释不得继续作为科学结论"),
    ("AIDD-LIT-MATRIX-001", "aidd", "00-当前研究/qualification_v1/MASTER_EVIDENCE_MATRIX.csv", "evidence_matrix", "MASH/FASN/Moracin N", "qualification_v1", "VERIFIED", "high", "唯一正式 claim-evidence 链", "", "主库权威证据入口"),
    ("AIDD-STATE-001", "aidd", "00-当前研究/qualification_v1/RESEARCH_STATE.md", "research_state", "项目", "qualification_v1", "VERIFIED", "high", "当前状态唯一入口", "", "与研究状态.json 同步"),
    ("GNN-RAW-001", "hepato-gnn-screening", "data/raw/tcm_seed_compounds.csv", "raw_labeled_table", "GNN/历史分类", "GNN 历史线", "HISTORICAL", "medium", "旧输入保留", "", "88 条一般保肝旧标签；不是 MASH assay-level 标签"),
    ("GNN-RAW-002", "hepato-gnn-screening", "data/raw/novel_terpenes_lignans.csv", "raw_unlabeled_pool", "GNN/历史分类", "GNN 历史线", "HISTORICAL", "low", "旧筛选池保留", "", "12 条旧无标签池；不转为当前 NP54 FASN 候选"),
    ("GNN-CUR-001", "hepato-gnn-screening", "data/curation/compound_registry.csv", "curation_registry", "GNN/结构身份", "GNN 审计", "REQUALIFY", "high", "人工结构/标签审核入口", "", "100/100 identity pending_review、label unresolved；不自动签名"),
    ("GNN-FIX-001", "hepato-gnn-screening", "final-aidd-screening/data/smiles_fix.json", "structure_correction", "GNN/结构身份", "GNN 审计", "REQUALIFY", "medium", "待人工复核的结构建议", "", "5 条 PubChem 建议结构；不能绕过注册表审核"),
    ("GNN-VAL-001", "hepato-gnn-screening", "results/validation", "validation_bundle", "GNN/审计", "GNN 审计", "VERIFIED", "high", "软件/诊断/门控失败证据", "", "包含 GNN diagnostic、FXR/KEAP1 redock 和修复批次；不等于科学放行"),
    ("GNN-VERIFY-LEGACY-001", "aidd", "00-当前研究/asset_preservation_and_gnn_replan_v1/legacy_metadata/software_checks_pre_20260914.json", "legacy_validation_snapshot", "GNN/审计", "asset preservation v1", "HISTORICAL", "medium", "修复前软件回归快照", "hepato-gnn-screening/results/validation/software_checks.json", "原始 hash d8345829...；本轮修复空 CSV 后 9/9 通过；科学验证仍 not_granted"),
    ("GNN-WEIGHT-001", "hepato-gnn-screening", "results/validation/gnn_model_diagnostic/results/metrics/gnn_weights.npz", "model_artifact", "GNN/历史分类", "GNN 审计", "HISTORICAL", "low", "旧 NumPy 权重可读性参考", "", "13→32→16→1；无 PyG checkpoint，不作当前主模型"),
    ("GNN-REVISED-001", "hepato-gnn-screening", "final-aidd-screening/run_revised.py", "reproduction_code", "GNN/诊断", "GNN 审计", "VERIFIED", "medium", "reviewed 阻断/diagnostic 复现入口", "", "默认阻断未审核数据；diagnostic 仅旧标签方法诊断"),
    ("GNN-CODE-NP-001", "hepato-gnn-screening", "src/models/gnn.py", "model_code", "GNN/历史分类", "GNN 历史线", "VERIFIED", "medium", "教学/方法实现", "", "真实 numpy GCN、手写反向和 MC dropout；不等于正式科学资格"),
    ("GNN-DATASET-001", "hepato-gnn-screening", "src/models/dataset.py", "data_loader_code", "GNN/历史分类", "GNN 历史线", "REQUALIFY", "medium", "方法学习参考", "", "元素未知值回退碳槽位；旧标签和旧 split 另行降级"),
    ("GNN-SPLIT-001", "hepato-gnn-screening", "data/splits", "split_bundle", "GNN/历史分类", "GNN 历史线", "HISTORICAL", "low", "历史复现参考", "", "train/test 实测共享 2 个 Murcko scaffold；不可作泛化证据"),
    ("GNN-RESULTS-001", "hepato-gnn-screening", "results", "results_bundle", "GNN/历史分类", "GNN 历史线", "HISTORICAL", "low", "旧结果/错误分析/教学", "D:/zcode-workspace/aidd-repo-work/00-当前研究/qualification_v1/derived/GNN_benchmark_summary.csv", "旧 Top-10/旧标签/旧模型输出全部保留但不发布"),
    ("GNN-STATUS-001", "hepato-gnn-screening", "docs/PROJECT_STATUS.md", "research_state", "GNN", "GNN 历史线", "VERIFIED", "high", "历史状态与限制说明", "", "已明确旧榜不能作为 V1 投稿结论"),
    ("GNN-STATE-001", "hepato-gnn-screening", "RESEARCH_STATE.md", "research_state", "GNN", "asset preservation v1", "VERIFIED", "high", "本仓库当前状态入口", "D:/zcode-workspace/aidd-repo-work/00-当前研究/qualification_v1/RESEARCH_STATE.md", "gated/closed；不替代 AIDD 主库"),
    ("GNN-STATUSJSON-001", "hepato-gnn-screening", "STATUS.json", "state_json", "GNN", "asset preservation v1", "VERIFIED", "high", "本仓库机器状态", "D:/zcode-workspace/aidd-repo-work/00-当前研究/研究状态.json", "candidate_release=false；旧资产分层"),
    ("GNN-PLAN-001", "hepato-gnn-screening", "GNN_RESEARCH_PLAN_v2.md", "research_plan", "GNN", "asset preservation v1", "VERIFIED", "high", "GNN 当前计划", "D:/zcode-workspace/aidd-repo-work/00-当前研究/asset_preservation_and_gnn_replan_v1/GNN_RESEARCH_PLAN_v2.md", "T1 前不启用 GNN 主模型"),
    ("GNN-AUDIT-001", "hepato-gnn-screening", "GNN仓库审计.md", "repo_audit", "GNN", "asset preservation v1", "VERIFIED", "high", "仓库定位裁决", "", "小修即可；不改名、不搬目录"),
    ("GNN-ASSET-001", "hepato-gnn-screening", "GNN数据与模型状态表.csv", "asset_status_table", "GNN", "asset preservation v1", "VERIFIED", "high", "旧代码/数据/模型状态表", "D:/zcode-workspace/aidd-repo-work/00-当前研究/asset_preservation_and_gnn_replan_v1/MASTER_ASSET_REGISTRY.csv", "旧标签/旧 split/旧结果降级"),
    ("WB-STATE-001", "workbench", "pages/17_Research_State.py", "state_mirror_code", "平台", "qualification_v1", "VERIFIED", "high", "主库只读镜像", "", "缺主库目录即 BLOCKED，不生成候选"),
    ("WB-STATE-002", "workbench", "tests/test_research_state_page.py", "test_code", "平台", "qualification_v1", "VERIFIED", "high", "镜像契约测试", "", "AppTest/数据契约"),
]

ROOTS = {"aidd": AIDD, "hepato-gnn-screening": GNN, "workbench": WB}


def file_hash(path: Path) -> tuple[str, int, int]:
    if path.is_file():
        h = hashlib.sha256(path.read_bytes()).hexdigest()
        return h, path.stat().st_size, 1
    if path.is_dir():
        rows = []
        total = 0
        count = 0
        for child in sorted(p for p in path.rglob("*") if p.is_file()):
            rel = child.relative_to(path).as_posix()
            digest = hashlib.sha256(child.read_bytes()).hexdigest()
            rows.append(f"{rel}\t{digest}\t{child.stat().st_size}")
            total += child.stat().st_size
            count += 1
        h = hashlib.sha256("\n".join(rows).encode("utf-8")).hexdigest()
        return h, total, count
    return "", 0, 0


def main() -> None:
    rows = []
    missing = []
    for spec in SPECS:
        (asset_id, repo, rel, asset_type, target, source_round, status,
         evidence, role, superseded, notes) = spec
        root = ROOTS[repo]
        path = root / rel
        if not path.exists():
            missing.append({"asset_id": asset_id, "repository": repo, "relative_path": rel})
            digest, size, count, path_status = "", 0, 0, "MISSING"
        else:
            digest, size, count = file_hash(path)
            path_status = "EXISTS"
        rows.append({
            "asset_id": asset_id, "repository": repo, "relative_path": rel,
            "asset_type": asset_type, "target": target, "source_round": source_round,
            "qualification_status": status, "evidence_level": evidence,
            "current_role": role, "superseded_by": superseded, "hash": digest,
            "bytes": size, "file_count": count, "path_status": path_status,
            "notes": notes,
        })
    out_csv = OUT / "MASTER_ASSET_REGISTRY.csv"
    with out_csv.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader(); w.writerows(rows)
    counts = {}
    for r in rows:
        counts[r["qualification_status"]] = counts.get(r["qualification_status"], 0) + 1
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "registry_scope": "curated high-value assets across the three repositories; directory rows use aggregate manifest hash",
        "asset_count": len(rows), "status_counts": counts,
        "missing": missing,
        "repositories": {k: str(v) for k, v in ROOTS.items()},
    }
    (OUT / "derived/registry_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
