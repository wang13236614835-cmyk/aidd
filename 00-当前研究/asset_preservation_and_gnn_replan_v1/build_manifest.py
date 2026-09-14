# -*- coding: utf-8 -*-
"""生成 asset_preservation_and_gnn_replan_v1/manifest.json。

manifest 不包含自身 hash，避免自引用；其余交付文件逐个 SHA-256。
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent
AIDD = ROOT.parent.parent
GNN = Path(r"D:/zcode-workspace/hepato-gnn-screening")
WB = Path(r"D:/aidd destoop")


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def git_snapshot(path: Path) -> dict:
    out = {}
    try:
        out["head"] = subprocess.check_output(["git", "-C", str(path), "rev-parse", "HEAD"], text=True).strip()
        out["status_lines"] = len(subprocess.check_output(["git", "-C", str(path), "status", "--short"], text=True, errors="replace").splitlines())
    except Exception as exc:
        out["error"] = repr(exc)
    return out


def main() -> None:
    files = {}
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or path.name == "manifest.json" or "__pycache__" in path.parts:
            continue
        rel = path.relative_to(ROOT).as_posix()
        files[rel] = {"sha256": digest(path), "bytes": path.stat().st_size}
    summary_path = ROOT / "derived/registry_summary.json"
    qc_path = ROOT / "derived/qc_checks.json"
    tests_path = ROOT / "derived/test_results.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.exists() else {}
    qc = json.loads(qc_path.read_text(encoding="utf-8")) if qc_path.exists() else {}
    tests = json.loads(tests_path.read_text(encoding="utf-8")) if tests_path.exists() else {}
    manifest = {
        "round": "asset_preservation_and_gnn_replan_v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "purpose": "retain, downgrade, index and hash existing assets; no historical asset deletion",
        "registry": {
            "asset_count": summary.get("asset_count"),
            "status_counts": summary.get("status_counts", {}),
            "missing": summary.get("missing", []),
        },
        "qc": {"verdict": qc.get("verdict"), "issues": qc.get("issues", [])},
        "tests": tests,
        "repository_snapshots": {
            "aidd": git_snapshot(AIDD),
            "hepato-gnn-screening": git_snapshot(GNN),
            "workbench": git_snapshot(WB),
        },
        "files_excluding_manifest": files,
        "preservation_note": "旧数据/模型/split/log/PDB/PDBQT/docking输出均不因本轮降级而删除；REJECTED表示解释/用途废弃，不表示文件删除。",
    }
    (ROOT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"files": len(files), "registry": manifest["registry"], "qc": manifest["qc"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
