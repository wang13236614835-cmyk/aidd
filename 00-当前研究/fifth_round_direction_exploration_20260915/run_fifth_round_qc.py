# -*- coding: utf-8 -*-
"""第五轮方向探索 QC：只读核对 T1 输出、唯一裁决、方向表和状态边界。"""
from __future__ import annotations

import csv
import json
import hashlib
from pathlib import Path

OUT = Path(__file__).parent
AIDD = OUT.parent.parent
issues: list[str] = []
checks: dict[str, object] = {}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> int:
    required = [
        "run_fasn_t1.py", "FASN_T1_SHARED_ASSAY_MATRIX.csv",
        "FASN_T1_ASSAY_TRANSFORMATIONS.csv", "FASN_T1_COMPARABLE_PAIRS.csv",
        "FASN_T1_DATA_AUDIT.json", "FASN_T1_LEAKAGE_AUDIT.json",
        "FASN_T1_PAIR_DETAILS.json", "FASN_T1_DECISION.md",
        "FASN_T1_NORMALIZED_DATASET_NOT_BUILT.md", "GATE_DECISION.json",
        "direction_exploration_matrix.csv", "EXECUTION_OVERVIEW.md", "OPEN_ISSUES.md",
    ]
    missing = [x for x in required if not (OUT / x).is_file()]
    checks["required_outputs"] = {"count": len(required), "missing": missing}
    if missing:
        issues.append(f"缺少 T1/方向探索输出：{missing}")

    summary = json.loads((OUT / "run_summary.json").read_text(encoding="utf-8"))
    decision = json.loads((OUT / "GATE_DECISION.json").read_text(encoding="utf-8"))
    leakage = json.loads((OUT / "FASN_T1_LEAKAGE_AUDIT.json").read_text(encoding="utf-8"))
    data_audit = json.loads((OUT / "FASN_T1_DATA_AUDIT.json").read_text(encoding="utf-8"))
    checks["t1_counts"] = {
        "all_assay_pairs": summary["shared_pair_count_all"],
        "shared_ge15": summary["shared_pair_count_ge15"],
        "comparable_ge15": summary["comparable_pair_count_ge15"],
        "transformations": summary["transformation_count"],
        "stable_transformations": summary["transformation_stable_count"],
    }
    if summary["shared_pair_count_ge15"] != 4:
        issues.append("shared_ge15 不等于本轮实测 4")
    if summary["comparable_pair_count_ge15"] != 1 or summary["transformation_count"] != 1:
        issues.append("T1 可比 pair/变换数量不等于实测 1")
    if decision.get("decision") != "FAIL":
        issues.append("GATE_DECISION 不是唯一 FAIL")
    if not decision.get("pre_registered_criteria", {}).get("minimum_two_comparable_pairs", {}).get("passed") is False:
        issues.append("GATE_DECISION 未明确记录至少两对 pair 未通过")
    if decision.get("pre_registered_criteria", {}).get("normalized_dataset_built") is not False:
        issues.append("normalized dataset 不应在 pair 不足时被标为已构建")
    if decision.get("consequence", {}).get("gnn_gate") != "CLOSED":
        issues.append("T1 FAIL 后 GNN gate 未保持 CLOSED")
    if decision.get("consequence", {}).get("candidate_release") is not False:
        issues.append("T1 FAIL 后 candidate_release 不是 false")

    expected_leakage = {
        "exact_duplicate_count": 0,
        "canonical_overlap_count": 0,
        "scaffold_overlap_rate": 0.0,
        "stereoisomer_overlap_count": 0,
        "assay_mirror_overlap_count": 89,
        "external_overlap_count": 3,
        "near_duplicate_count": 82,
    }
    checks["leakage"] = leakage
    for key, value in expected_leakage.items():
        if leakage.get(key) != value:
            issues.append(f"泄漏数字 {key}={leakage.get(key)!r}，预期 {value!r}")
    if leakage.get("verdict") != "PASS":
        issues.append("evaluated boundary leakage verdict 不是 PASS")

    checks["data_audit"] = {
        "master_records": data_audit.get("master_records"),
        "master_molecules": data_audit.get("master_molecules"),
        "assays": data_audit.get("assays"),
        "activity_types": data_audit.get("activity_type_counts"),
        "protein_layers": data_audit.get("protein_layer_counts"),
    }
    for key, expected in [("master_records", 1652), ("master_molecules", 1139), ("assays", 51), ("valid_smiles_count", 1652)]:
        if data_audit.get(key) != expected:
            issues.append(f"数据审计 {key}={data_audit.get(key)!r}，预期 {expected!r}")

    matrix_path = OUT / "direction_exploration_matrix.csv"
    rows = list(csv.DictReader(matrix_path.open(encoding="utf-8-sig", newline="")))
    checks["direction_matrix"] = {"rows": len(rows), "roles": sorted({r.get("direction_role") for r in rows})}
    required_columns = {
        "Target/Task", "direction_role", "data_sample_size", "endpoint_consistency", "assay_count",
        "activity_distribution", "duplicate_leakage_risk", "scaffold_diversity",
        "external_validation_feasibility", "MASH_link", "clinical_pharmacology_evidence",
        "natural_product_value", "modeling_value", "overall_decision", "source_refs", "notes",
    }
    if rows and not required_columns <= set(rows[0]):
        issues.append(f"方向矩阵缺列：{sorted(required_columns - set(rows[0]))}")
    if len(rows) != 9:
        issues.append(f"方向矩阵行数 {len(rows)} != 9")
    roles = {r.get("direction_role") for r in rows}
    decisions = {r.get("overall_decision") for r in rows}
    if "Primary" not in roles or "Secondary" not in roles or "Reserve" not in roles or "Rejected" not in roles:
        issues.append(f"方向角色裁决不完整：roles={roles}")
    if not any("FAIL" in str(x) for x in decisions) or not any("REJECTED" in str(x) for x in decisions):
        issues.append(f"方向总体裁决缺少 T1 FAIL 或 REJECTED：{decisions}")

    state_path = AIDD / "00-当前研究/研究状态.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state_checks = {
        "project_stage": state.get("project_stage"),
        "current_stage": state.get("current_stage"),
        "fasn_gate_t1_decision": state.get("fasn", {}).get("gate_t1_decision"),
        "gnn_gate": state.get("gnn", {}).get("enable_gate"),
        "candidate_release": state.get("candidate_release"),
        "primary": state.get("fifth_round", {}).get("primary_direction"),
    }
    checks["main_state"] = state_checks
    if state.get("project_stage") != "fifth_round_direction_exploration":
        issues.append("主库 project_stage 未同步第五轮方向探索")
    if state.get("fasn", {}).get("gate_t1_decision") != "FAIL":
        issues.append("主库 FASN gate_t1_decision 不是 FAIL")
    if state.get("candidate_release") is not False:
        issues.append("主库 candidate_release 不是 false")
    if state.get("gnn", {}).get("enable_gate") != "closed":
        issues.append("主库 GNN gate 未保持 closed")

    # 保护关键前四轮输入仍存在，不检查其内容变化，避免把历史资产误当本轮输出。
    protected = [
        AIDD / "00-当前研究/final_strategy_round_20260912/FASN_activity_master.csv",
        AIDD / "00-当前研究/advancement_round_20260913/FASN_assay_aware_master.csv",
        AIDD / "00-当前研究/qualification_round_20260913/FASN_canonical_clean.csv",
        AIDD / "00-当前研究/qualification_round_20260913/FASN_external_set.csv",
    ]
    checks["protected_inputs_exist"] = all(p.exists() for p in protected)
    if not checks["protected_inputs_exist"]:
        issues.append("关键前四轮输入缺失")

    verdict = "PASS" if not issues else "FAIL"
    payload = {"verdict": verdict, "issues": issues, "checks": checks}
    (OUT / "derived").mkdir(exist_ok=True)
    (OUT / "derived/qc_checks.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["# 第五轮方向探索 QC 报告", "", f"**判定：{verdict}**（{len(issues)} 项问题）", "", "## 检查项", ""]
    lines += [f"- {k}: {v}" for k, v in checks.items()]
    if issues:
        lines += ["", "## 问题清单", ""] + [f"- {x}" for x in issues]
    (OUT / "QC_report.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
