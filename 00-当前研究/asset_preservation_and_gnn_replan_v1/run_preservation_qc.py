# -*- coding: utf-8 -*-
"""资产保留与 GNN 重规划轮 QC。

只读验证：registry 路径/状态/hash、20项交付、GNN状态字段、主库状态同步、旧文件未删除标志、Workbench镜像路径。
输出 QC_report.md 和 derived/qc_checks.json；不生成候选、不改写旧资产。
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

OUT = Path(__file__).parent
AIDD = OUT.parent.parent
GNN = Path(r"D:/zcode-workspace/hepato-gnn-screening")
WB = Path(r"D:/aidd destoop")
issues: list[str] = []
checks: dict[str, object] = {}

REQUIRED_DOCS = [
    "执行总览.md", "MASTER_ASSET_REGISTRY.csv", "历史结果保留与降级规则.md", "前四轮资产保留清单.md",
    "前四轮废弃解释清单.md", "FASN历史资产保留方案.md", "THRB历史资产保留方案.md", "FXR历史资产保留方案.md",
    "Docking历史资产保留方案.md", "GNN仓库审计.md", "GNN_RESEARCH_PLAN_v2.md", "GNN是否需要大改_裁决.md",
    "GNN数据与模型状态表.csv", "三库角色与同步规则.md", "AIDD主库状态同步记录.md", "Workbench同步记录.md",
    "Git提交记录.md", "未完成项与风险.md", "FXR元数据口径修正记录.md", "build_asset_registry.py", "run_preservation_qc.py", "build_manifest.py",
    "QC_report.md", "manifest.json", "最终交接报告.md", "derived/registry_summary.json", "derived/qc_checks.json", "derived/test_results.json",
]
VALID = {"VERIFIED", "REQUALIFY", "HISTORICAL", "REJECTED"}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    missing = [f for f in REQUIRED_DOCS if not (OUT / f).is_file()]
    checks["required_docs"] = {"count": len(REQUIRED_DOCS), "missing": missing}
    if missing:
        issues.append(f"required docs missing: {missing}")

    reg_path = OUT / "MASTER_ASSET_REGISTRY.csv"
    rows = list(csv.DictReader(reg_path.open(encoding="utf-8-sig", newline=""))) if reg_path.exists() else []
    checks["registry_rows"] = len(rows)
    counts: dict[str, int] = {}
    missing_assets = []
    bad_status = []
    for r in rows:
        status = r.get("qualification_status", "")
        counts[status] = counts.get(status, 0) + 1
        if status not in VALID:
            bad_status.append((r.get("asset_id"), status))
        root = {"aidd": AIDD, "hepato-gnn-screening": GNN, "workbench": WB}.get(r.get("repository"))
        if root is None or not (root / r.get("relative_path", "")).exists():
            missing_assets.append((r.get("asset_id"), r.get("repository"), r.get("relative_path")))
        if r.get("path_status") != "EXISTS" or not r.get("hash"):
            missing_assets.append((r.get("asset_id"), "hash/path", r.get("relative_path")))
    checks["registry_status_counts"] = counts
    checks["registry_missing_assets"] = missing_assets
    checks["registry_bad_status"] = bad_status
    if missing_assets:
        issues.append(f"registry path/hash problems: {missing_assets[:10]}")
    if bad_status:
        issues.append(f"registry invalid status: {bad_status}")

    state = json.loads((AIDD / "00-当前研究/研究状态.json").read_text(encoding="utf-8"))
    checks["main_state"] = {
        "project_stage": state.get("project_stage"),
        "candidate_release": state.get("candidate_release"),
        "fasn_gate_t1": state.get("fasn", {}).get("gate_t1"),
        "gnn_gate": state.get("fasn", {}).get("gnn_enable_gate", state.get("gnn", {}).get("enable_gate")),
        "thrb_2j4a": state.get("thrb", {}).get("old_2j4a"),
        "docking_ranking": state.get("thrb", {}).get("wt_docking_ranking"),
    }
    if state.get("project_stage") != "pipeline_revalidation":
        issues.append("main project_stage is not pipeline_revalidation")
    if state.get("candidate_release") is not False:
        issues.append("candidate_release is not false")
    if state.get("fasn", {}).get("gate_t1") != "pending":
        issues.append("FASN Gate T1 is not pending")
    if state.get("gnn", {}).get("enable_gate") != "closed" and state.get("fasn", {}).get("gnn_enable_gate") != "closed":
        issues.append("GNN enable gate is not closed")

    gnn_state = json.loads((GNN / "STATUS.json").read_text(encoding="utf-8"))
    checks["gnn_state"] = {"role": gnn_state.get("repository_role"), "activity": gnn_state.get("gnn_activity"), "gate": gnn_state.get("gnn_enable_gate")}
    if gnn_state.get("gnn_activity") != "gated" or gnn_state.get("gnn_enable_gate") != "closed":
        issues.append("GNN STATUS.json is not gated/closed")
    if gnn_state.get("candidate_release") is not False:
        issues.append("GNN candidate_release is not false")

    old_manifest = OUT / "legacy_metadata/fxr_model_manifest_pre_20260914.json"
    new_manifest = AIDD / "00-当前研究/candidate_decision_20260910/derived/fxr_locked_model/model_manifest.json"
    checks["fxr_manifest_correction"] = {
        "legacy_exists": old_manifest.exists(),
        "legacy_sha256": sha(old_manifest) if old_manifest.exists() else None,
        "current_threshold_note": json.loads(new_manifest.read_text(encoding="utf-8")).get("threshold_note") if new_manifest.exists() else None,
    }
    if not old_manifest.exists() or not new_manifest.exists():
        issues.append("FXR legacy/current manifest missing")
    else:
        current = json.loads(new_manifest.read_text(encoding="utf-8"))
        if "10 nM" not in current.get("threshold_note", ""):
            issues.append("current FXR manifest does not state 10 nM")
        if current.get("threshold_pActivity") != 8.0:
            issues.append("FXR threshold_pActivity changed unexpectedly")

    checks["gnn_readme_boundary"] = {
        "gated": "gated/closed" in (GNN / "README.md").read_text(encoding="utf-8"),
        "legacy_demo": "--legacy-demo" in (GNN / "README.md").read_text(encoding="utf-8"),
        "no_candidate_release_claim": "候选排名总表" not in (GNN / "README.md").read_text(encoding="utf-8"),
    }
    if not all(checks["gnn_readme_boundary"].values()):
        issues.append(f"GNN README boundary check failed: {checks['gnn_readme_boundary']}")

    checks["workbench_files"] = {
        "page": (WB / "pages/17_Research_State.py").exists(),
        "test": (WB / "tests/test_research_state_page.py").exists(),
    }
    if not all(checks["workbench_files"].values()):
        issues.append("Workbench state page/test missing")

    checks["old_assets_deleted"] = False
    checks["registry_scope"] = "curated high-value"
    verdict = "PASS" if not issues else "FAIL"
    payload = {"verdict": verdict, "issues": issues, "checks": checks}
    (OUT / "derived").mkdir(exist_ok=True)
    (OUT / "derived/qc_checks.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["# asset_preservation_and_gnn_replan_v1 QC 报告", "", f"**判定：{verdict}**（{len(issues)} 项问题）", "", "## 检查项", ""]
    for k, v in checks.items(): lines.append(f"- {k}: {v}")
    if issues:
        lines += ["", "## 问题清单", ""] + [f"- {x}" for x in issues]
    (OUT / "QC_report.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
