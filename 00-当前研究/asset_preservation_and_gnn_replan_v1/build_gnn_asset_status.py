# -*- coding: utf-8 -*-
"""Generate GNN_ASSET_STATUS.csv in the same preservation directory.

This file complements MASTER_ASSET_REGISTRY.csv by mapping the hepato-gnn-screening
assets to the canonical four-state scheme (VERIFIED / REQUALIFY / HISTORICAL /
REJECTED). Rows with the legacy `NEEDS_HUMAN_CHECK` value are normalised to
REQUALIFY with `human_review = pending`; no row is silently upgraded.

Run as ``python build_gnn_asset_status.py``. The script is read-only against the
hepato-gnn-screening repository; it only writes the CSV into the AIDD preservation
directory.
"""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

OUT = Path(__file__).parent
GNN_ROOT = Path(r"D:/zcode-workspace/hepato-gnn-screening")

LEGACY_SOURCE_CSV = OUT / "GNN数据与模型状态表.csv"

FIELD_MAP = {
    "VERIFIED": ("VERIFIED", "passed", "不需要人工复核"),
    "HISTORICAL": ("HISTORICAL", "passed", "不需要人工复核"),
    "REJECTED": ("REJECTED", "passed", "不需要人工复核"),
    "REQUALIFY": ("REQUALIFY", "passed", "不需要人工复核"),
    "NEEDS_HUMAN_CHECK": ("REQUALIFY", "pending", "组员逐条人工核验未完成；本轮不自动签名"),
}


def _status_row(raw_status: str) -> tuple[str, str, str]:
    mapped = FIELD_MAP.get(raw_status)
    if mapped is None:
        return ("REQUALIFY", "pending", f"未知状态 {raw_status!r}，按 REQUALIFY/pending 记录")
    canonical, review, note = mapped
    if raw_status == "NEEDS_HUMAN_CHECK":
        note = "NEEDS_HUMAN_CHECK 已规范为 REQUALIFY；52 连接/43 分子式/4 立体化学差异需组员逐条核验"
    return canonical, review, note


def _sha(path: Path) -> tuple[str, int, int, str]:
    if path.is_file():
        return hashlib.sha256(path.read_bytes()).hexdigest(), path.stat().st_size, 1, "EXISTS"
    if path.is_dir():
        rows: list[str] = []
        total = 0
        count = 0
        for child in sorted(p for p in path.rglob("*") if p.is_file()):
            rel = child.relative_to(path).as_posix()
            digest = hashlib.sha256(child.read_bytes()).hexdigest()
            rows.append(f"{rel}\t{digest}\t{child.stat().st_size}")
            total += child.stat().st_size
            count += 1
        h = hashlib.sha256("\n".join(rows).encode("utf-8")).hexdigest() if rows else ""
        return h, total, count, "EXISTS" if rows else "MISSING"
    return "", 0, 0, "MISSING"


def main() -> None:
    if not LEGACY_SOURCE_CSV.exists():
        raise SystemExit(f"legacy source CSV missing: {LEGACY_SOURCE_CSV}")
    out_rows: list[dict[str, object]] = []
    with LEGACY_SOURCE_CSV.open(encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            raw = row.get("qualification_status", "")
            canonical, human_review, note = _status_row(raw)
            rel = row.get("relative_path", "")
            target = GNN_ROOT / rel
            sha, size, count, path_status = _sha(target)
            out_rows.append({
                "asset_id": row.get("asset_id", ""),
                "relative_path": rel,
                "asset_type": row.get("asset_type", ""),
                "legacy_status": raw,
                "qualification_status": canonical,
                "human_review": human_review,
                "current_role": row.get("current_role", ""),
                "can_enter_formal_training": row.get("can_enter_formal_training", "false"),
                "hash": sha,
                "bytes": size,
                "file_count": count,
                "path_status": path_status,
                "reason": row.get("reason", ""),
                "human_review_note": note,
                "source_of_truth": row.get("source_of_truth", ""),
            })

    counts: dict[str, int] = {}
    for r in out_rows:
        counts[str(r["qualification_status"])] = counts.get(str(r["qualification_status"]), 0) + 1

    out_csv = OUT / "GNN_ASSET_STATUS.csv"
    fields = [
        "asset_id", "relative_path", "asset_type", "legacy_status",
        "qualification_status", "human_review", "current_role",
        "can_enter_formal_training", "hash", "bytes", "file_count",
        "path_status", "reason", "human_review_note", "source_of_truth",
    ]
    with out_csv.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(out_rows)

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "purpose": "Map hepato-gnn-screening assets to canonical four-state scheme with human_review column",
        "row_count": len(out_rows),
        "status_counts": counts,
        "human_review_counts": {
            "pending": sum(1 for r in out_rows if r["human_review"] == "pending"),
            "passed": sum(1 for r in out_rows if r["human_review"] == "passed"),
        },
        "gnn_root": str(GNN_ROOT),
        "note": "NEEDS_HUMAN_CHECK 已规范为 REQUALIFY/pending；旧 split / 旧标签 / 旧 Top-10 不重新升格。",
    }
    (OUT / "derived/gnn_asset_status_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()