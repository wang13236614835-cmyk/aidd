# -*- coding: utf-8 -*-
"""qualification_v1 运行清单生成器：记录本轮全部脚本/关键输入/输出的 SHA-256 与运行结论。

用法：python write_run_manifest.py  （在完成实际运行后调用，重写 RUN_MANIFEST.json）
"""
from __future__ import annotations

import hashlib
import io
import json
import sys
from datetime import datetime
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

OUT = Path(__file__).parent
QUAL = OUT.parent / "qualification_round_20260913"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()


def f(rec, rel: str):
    p = OUT / rel
    if not p.exists():
        rec["_missing"].append(rel)
        return
    rec["files"][rel] = {"sha256": sha256(p), "bytes": p.stat().st_size}


def main() -> None:
    runs = json.loads((OUT / "derived" / "gnn_benchmark_summary.json").read_text(encoding="utf-8"))
    prov = json.loads((OUT / "derived" / "provenance_audit.json").read_text(encoding="utf-8"))

    manifest = {
        "round": "qualification_v1",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "runs": [
            {
                "id": "assay_provenance_audit",
                "script": "audit_assay_provenance.py",
                "purpose": "FASN 全量数据 assay 级 lineage 审计（只读）",
                "verdict": prov["verdict"],
                "key_results": {
                    "master_records": prov["master_records"],
                    "master_assays": prov["master_assays"],
                    "records_missing_assay_id": prov["records_missing_assay_id"],
                    "canonical_activity_ids_not_in_master": prov["canonical_activity_ids_not_in_master"],
                    "external_overlapping_canonical_flagged": prov["external_overlapping_canonical_flagged"],
                },
            },
            {
                "id": "gnn_clean_benchmark",
                "script": "run_gnn_clean_benchmark.py",
                "purpose": "GNN vs 经典 baseline 同折对比（10 seed + Y-scrambling×20 + 外部 105 + MC-dropout）",
                "runtime_sec": runs.get("runtime_sec"),
                "verdict": "COMPLETED",
                "key_results": {
                    "split_identity_assert": runs["split_identity_assert"],
                    "y_scrambling": runs["y_scrambling"],
                    "summary_csv": "derived/GNN_benchmark_summary.csv",
                },
                "environment": runs["environment"],
            },
        ],
        "_missing": [],
        "files": {},
    }

    # 脚本与文档
    for rel in ["README.md", "RESEARCH_STATE.md", "ASSET_AUDIT.csv", "MASTER_EVIDENCE_MATRIX.csv",
                "QUALIFICATION_GATES.md", "RERUN_DECISION.md", "OPEN_ISSUES.md",
                "AGENT_PROGRESS.md", "GNN_clean_benchmark_report.md", "GNN_方法学习审计.md",
                "audit_assay_provenance.py", "run_gnn_clean_benchmark.py", "write_run_manifest.py",
                "run_qualification_qc.py"]:
        f(manifest, rel)
    # 产出
    for rel in ["derived/ASSAY_PROVENANCE.csv", "derived/provenance_audit.json",
                "derived/GNN_benchmark_10seed_results.csv", "derived/GNN_benchmark_summary.csv",
                "derived/GNN_y_scrambling_results.csv", "derived/GNN_external_validation.csv",
                "derived/gnn_benchmark_summary.json"]:
        f(manifest, rel)
    # 冻结输入（资格轮）
    for rel in ["FASN_canonical_clean.csv", "FASN_external_set.csv",
                "FASN_10seed_scaffold_results.csv"]:
        p = QUAL / rel
        if p.exists():
            manifest["files"][f"../qualification_round_20260913/{rel}"] = {
                "sha256": sha256(p), "bytes": p.stat().st_size}
        else:
            manifest["_missing"].append(rel)

    manifest["input_freeze_note"] = "训练/外部数据与资格轮同源同哈希输入；本 manifest 在 QC 之后生成则包含 QC 产物"
    (OUT / "RUN_MANIFEST.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"generated": manifest["generated_at"],
                      "files": len(manifest["files"]),
                      "missing": manifest["_missing"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
