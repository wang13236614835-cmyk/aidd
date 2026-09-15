# -*- coding: utf-8 -*-
"""生成第五轮方向探索运行清单。manifest 不包含自身 hash。"""
from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

OUT = Path(__file__).parent
AIDD = OUT.parent.parent
GNN = Path(r"D:/zcode-workspace/hepato-gnn-screening")
WB = Path(r"D:/aidd destoop")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def snapshot(path: Path) -> dict:
    result = {}
    try:
        result["head"] = subprocess.check_output(["git", "-C", str(path), "rev-parse", "HEAD"], text=True).strip()
        status = subprocess.check_output(
            ["git", "-C", str(path), "status", "--short"],
            text=True,
            errors="replace",
        ).splitlines()
        result["status_lines"] = len(status)
        result["uncommitted_files"] = status
    except Exception as exc:
        result["error"] = repr(exc)
    return result


def file_record(path: Path) -> dict:
    record = {"path": str(path)}
    if path.is_file():
        record["sha256"] = sha256(path)
        record["bytes"] = path.stat().st_size
    else:
        record["missing"] = True
    return record


def main() -> None:
    files = {}
    for path in sorted(OUT.rglob("*")):
        if not path.is_file() or path.name == "RUN_MANIFEST.json" or "__pycache__" in path.parts:
            continue
        rel = path.relative_to(OUT).as_posix()
        files[rel] = {"sha256": sha256(path), "bytes": path.stat().st_size}
    state_path = AIDD / "00-当前研究/研究状态.json"
    decision_path = OUT / "GATE_DECISION.json"
    direction_matrix_path = OUT / "direction_exploration_matrix.csv"
    qc_checks_path = OUT / "derived/qc_checks.json"
    qc_report_path = OUT / "QC_report.md"
    decision = json.loads(decision_path.read_text(encoding="utf-8"))
    summary = json.loads((OUT / "run_summary.json").read_text(encoding="utf-8"))
    qc = json.loads(qc_checks_path.read_text(encoding="utf-8"))
    state = json.loads(state_path.read_text(encoding="utf-8"))
    source_paths = {
        "master": AIDD / "00-当前研究/final_strategy_round_20260912/FASN_activity_master.csv",
        "assay_aware": AIDD / "00-当前研究/advancement_round_20260913/FASN_assay_aware_master.csv",
        "canonical": AIDD / "00-当前研究/qualification_round_20260913/FASN_canonical_clean.csv",
        "external": AIDD / "00-当前研究/qualification_round_20260913/FASN_external_set.csv",
    }
    authoritative_paths = {
        "aidd_research_state": state_path,
        "gate_decision": decision_path,
        "direction_matrix": direction_matrix_path,
        "qc_checks": qc_checks_path,
        "qc_report": qc_report_path,
    }
    manifest = {
        "round": "fifth_round_direction_exploration_20260915",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "decision": decision["decision"],
        "scope": "FASN T1 shared-assay/leakage/transform audit plus direction qualification; no full historical rerun",
        "t1_summary": {
            "all_assay_pairs": summary["shared_pair_count_all"],
            "shared_pairs_ge15": summary["shared_pair_count_ge15"],
            "comparable_pairs_ge15": summary["comparable_pair_count_ge15"],
            "transformations": summary["transformation_count"],
            "stable_transformations": summary["transformation_stable_count"],
            "normalized_dataset_built": decision["pre_registered_criteria"]["normalized_dataset_built"],
            "leakage": summary["leakage"],
        },
        "direction_roles": {
            "primary": decision["consequence"]["primary_direction"],
            "secondary": decision["consequence"]["secondary_direction"],
            "reserve": decision["consequence"]["reserve_direction"],
            "rejected": state.get("fifth_round", {}).get("rejected_directions", []),
        },
        "qc": {"verdict": qc.get("verdict"), "issues": qc.get("issues", [])},
        "authoritative_artifacts": {
            name: file_record(path) for name, path in authoritative_paths.items()
        },
        "source_inputs": {
            name: file_record(path) for name, path in source_paths.items()
        },
        "state_assertions": {
            "project_stage": state.get("project_stage"),
            "current_stage": state.get("current_stage"),
            "gate_t1_decision": state.get("fasn", {}).get("gate_t1_decision"),
            "candidate_release": state.get("candidate_release"),
            "gnn_enable_gate": state.get("gnn", {}).get("enable_gate"),
        },
        "repository_snapshots": {
            "aidd": snapshot(AIDD),
            "hepato-gnn-screening": snapshot(GNN),
            "mash-aidd-workbench": snapshot(WB),
        },
        "files_excluding_manifest": files,
        "no_candidate_release": True,
        "no_gnn_training": True,
    }
    (OUT / "RUN_MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"decision": manifest["decision"], "qc": manifest["qc"], "files": len(files)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
