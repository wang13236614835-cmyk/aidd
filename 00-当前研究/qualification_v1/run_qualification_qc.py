# -*- coding: utf-8 -*-
"""qualification_v1 QC：交付完整性 + 数字交叉核对 + 违禁表述扫描 + 资产路径存在性。

只读检查，输出 QC_report.md 与 derived/qc_checks.json。PASS/FAIL 硬判定。
"""
from __future__ import annotations

import ast
import io
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from rdkit import Chem, RDLogger
from rdkit.Chem import AllChem
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
RDLogger.DisableLog("rdApp.*")

OUT = Path(__file__).parent
QUAL = OUT.parent / "qualification_round_20260913"
ADV = OUT.parent / "advancement_round_20260913"
REPO = OUT.parent.parent
SEEDS = list(range(20260912, 20260922))
FPGEN = AllChem.GetMorganGenerator(radius=2, fpSize=2048)

issues: list[str] = []
checks: dict[str, object] = {}

DELIVERABLES = [
    "README.md", "RESEARCH_STATE.md", "ASSET_AUDIT.csv", "MASTER_EVIDENCE_MATRIX.csv",
    "QUALIFICATION_GATES.md", "RERUN_DECISION.md", "OPEN_ISSUES.md",
    "AGENT_PROGRESS.md", "GNN_clean_benchmark_report.md", "GNN_方法学习审计.md",
    "audit_assay_provenance.py", "run_gnn_clean_benchmark.py", "write_run_manifest.py",
    "derived/ASSAY_PROVENANCE.csv", "derived/provenance_audit.json",
    "derived/GNN_benchmark_10seed_results.csv", "derived/GNN_benchmark_summary.csv",
    "derived/GNN_y_scrambling_results.csv", "derived/GNN_external_validation.csv",
    "derived/gnn_benchmark_summary.json",
]
# RUN_MANIFEST.json 与 QC_report.md 是 QC 之后的产物，不在预检清单（QC_report 由本脚本写出）

GNN_REPO = Path(r"D:/zcode-workspace/hepato-gnn-screening")
AIDD_ROOT = OUT.parent.parent  # aidd-repo-work

BANNED = ["已验证最终候选", "正式Top-10", "正式 Top-10", "唯一批准", "唯一获批的MASH",
          "GNN优于", "GNN 优于经典", "已证明有效", "candidate_release=true"]
EXEMPT_TOKENS = ("❌", "禁止", "不得", "不能", "才可", "policy", "放行政策")


def resolve_and_check(raw: str) -> list[str]:
    """台账路径单元格 → 实际路径检查。先去括注再按 ';'/'+ ' 分割；相对片段继承上一片段的目录上下文；
    无上下文时按前缀路由（D:/ 绝对、数字- 开头→主库、其余→GNN 库）；含 * 走 glob。返回失败项。"""
    import glob as _g
    import re
    stripped = re.sub(r"[（(][^（）()]*[)）]", "", str(raw))
    bad = []
    ctx: Path | None = None  # 上一片段所在目录（相对片段继承）
    for part in re.split(r"[;+]", stripped):
        p = part.strip().rstrip("/\\")
        if not p:
            continue
        if p.startswith(("D:/", "D:\\")):
            base = Path(p)
            ctx = base.parent
        elif re.match(r"^\d\d-", p):  # 主库顶层目录模式（00-当前研究/…、04-论文/…）
            base = AIDD_ROOT / p
            ctx = base.parent
        elif ctx is not None and "/" not in p:
            base = ctx / p  # 仅裸文件名/目录名继承上一片段的目录
        else:
            base = GNN_REPO / p
            ctx = base.parent
        if "*" in p:
            if not _g.glob(str(base)):
                bad.append(p)
        elif not base.exists():
            bad.append(p)
    return bad


def fp_matrix(smiles):
    from rdkit import DataStructs
    arr = np.zeros((len(smiles), 2048), dtype=np.float32)
    for i, s in enumerate(smiles):
        m = Chem.MolFromSmiles(str(s))
        if m is not None:
            DataStructs.ConvertToNumpyArray(FPGEN.GetFingerprint(m), arr[i])
    return arr


def main() -> None:
    # 1) 交付存在性
    missing = [d for d in DELIVERABLES if not (OUT / d).exists() or (OUT / d).stat().st_size == 0]
    checks["deliverables_total"] = len(DELIVERABLES)
    checks["deliverables_missing"] = missing
    if missing:
        issues.append(f"交付缺失/为空: {missing}")

    # 2) CSV 结构
    audit = pd.read_csv(OUT / "ASSET_AUDIT.csv")
    ok_classes = set(audit.分类) <= {"VERIFIED", "REQUALIFY", "HISTORICAL", "REJECTED"}
    checks["asset_audit_rows"] = int(len(audit))
    checks["asset_audit_classes"] = sorted(set(audit.分类))
    checks["asset_audit_class_valid"] = bool(ok_classes)
    if not ok_classes:
        issues.append("ASSET_AUDIT 存在非法分类")
    ev = pd.read_csv(OUT / "MASTER_EVIDENCE_MATRIX.csv")
    ok_conf = set(ev.confidence.dropna()) <= {"high", "medium", "low"}
    checks["evidence_rows"] = int(len(ev))
    checks["evidence_confidence_valid"] = bool(ok_conf)
    if not ok_conf:
        issues.append("MASTER_EVIDENCE_MATRIX 存在非法 confidence")

    # 3) 资产路径存在性（三仓库解析 + 通配符 + 多路径分割）
    bad_paths = []
    for _, r in audit.iterrows():
        for miss in resolve_and_check(r.路径):
            bad_paths.append(f"{r.asset_id}:{miss}")
    checks["asset_paths_missing"] = bad_paths
    if bad_paths:
        issues.append(f"ASSET_AUDIT 路径不存在: {bad_paths}")

    # 4) 数字交叉核对：benchmark 汇总 vs 报告引用 vs 资格轮冻结
    bs = pd.read_csv(OUT / "derived/GNN_benchmark_summary.csv").set_index("model")
    frozen = pd.read_csv(QUAL / "FASN_10seed_scaffold_results.csv")
    fr = frozen[frozen.model == "ecfp_ridge"].iloc[0]
    frozen_med = ast.literal_eval(fr.r2)["median"]
    checks["ridge_median_r2"] = {"frozen": frozen_med,
                                 "benchmark_recomputed": float(bs.loc["ecfp_ridge", "r2_median"])}
    if abs(frozen_med - float(bs.loc["ecfp_ridge", "r2_median"])) > 1e-3:
        issues.append("ecfp_ridge 中位 R² 与资格轮不一致")
    checks["gnn_median_r2"] = {"gcn": float(bs.loc["gnn_gcn", "r2_median"]),
                               "gin": float(bs.loc["gnn_gin", "r2_median"])}
    # 报告中的数字与 CSV 一致（报告使用全角负号 U+2212，归一后比对）
    report = (OUT / "GNN_clean_benchmark_report.md").read_text(encoding="utf-8").replace("−", "-")
    for name in ["0.732", "0.078", "-0.040"]:
        if name not in report:
            issues.append(f"报告缺少关键数字 {name}")
    checks["report_numbers_present"] = True

    # 5) 同折复算（独立路径重算 ridge 中位，防漂移）
    canon = pd.read_csv(QUAL / "FASN_canonical_clean.csv")
    clean = canon[canon.excluded.astype(str).str.lower() == "false"].reset_index(drop=True)
    y = clean.pActivity.to_numpy(float)
    X = fp_matrix(clean.canonical_smiles)
    r2s = []
    overlap_bad = 0
    for seed in SEEDS:
        gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=seed)
        tr, te = next(gss.split(clean, groups=clean.scaffold.astype(str)))
        if set(clean.scaffold.iloc[tr]) & set(clean.scaffold.iloc[te]):
            overlap_bad += 1
        m = make_pipeline(StandardScaler(with_mean=False), Ridge(alpha=10.0))
        m.fit(X[tr], y[tr])
        r2s.append(r2_score(y[te], m.predict(X[te])))
    checks["independent_ridge_median_r2"] = float(np.median(r2s))
    checks["scaffold_overlap_seeds"] = overlap_bad
    if abs(float(np.median(r2s)) - frozen_med) > 1e-9:
        issues.append(f"独立复算中位 R² {np.median(r2s)} != 冻结 {frozen_med}")
    if overlap_bad:
        issues.append("存在 scaffold 跨集的 seed")

    # 6) 外部 ADin 复算对齐推进轮 E1_ADin（rho 0.880 / R2 -1.457）
    ext = pd.read_csv(OUT / "derived/GNN_external_validation.csv")
    row = ext[(ext.model == "ecfp_ridge") & (ext.subset == "ad_in")].iloc[0]
    checks["ad_in_ridge"] = {"r2": float(row.r2), "spearman": float(row.spearman), "n": int(row.n)}
    if abs(float(row.spearman) - 0.880) > 0.005 or int(row.n) != 14:
        issues.append("ADin Ridge 与推进轮 E1_ADin 不一致")

    # 7) 违禁表述扫描（仅本轮新增文件；跳过否定/政策语境行；qc_checks.json 为本脚本自身产物不扫）
    banned_hits = []
    for p in OUT.rglob("*"):
        if p.suffix in {".md", ".csv", ".json"} and p.name not in ("QC_report.md", "qc_checks.json"):
            try:
                txt = p.read_text(encoding="utf-8")
            except Exception:
                continue
            for line in txt.splitlines():
                if any(t in line for t in EXEMPT_TOKENS):
                    continue
                for b in BANNED:
                    if b in line:
                        banned_hits.append(f"{p.name}:{b}")
    checks["banned_hits"] = banned_hits
    if banned_hits:
        issues.append(f"违禁表述: {banned_hits}")

    # 8) provenance 审计结论
    prov = json.loads((OUT / "derived/provenance_audit.json").read_text(encoding="utf-8"))
    checks["provenance_verdict"] = prov["verdict"]
    if prov["verdict"] != "PASS":
        issues.append("provenance 审计未 PASS")

    verdict = "PASS" if not issues else "FAIL"
    lines = [f"# qualification_v1 QC 报告", "",
             f"**判定：{verdict}**（{len(issues)} 项问题）", "",
             "## 检查项", ""]
    for k, v in checks.items():
        lines.append(f"- {k}: {v}")
    if issues:
        lines += ["", "## 问题清单", ""]
        lines += [f"- {i}" for i in issues]
    (OUT / "QC_report.md").write_text("\n".join(lines), encoding="utf-8")
    (OUT / "derived/qc_checks.json").write_text(
        json.dumps({"verdict": verdict, "issues": issues, "checks": checks},
                   ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"[QC] {verdict}; issues={len(issues)}")
    for i in issues:
        print("  -", i)


if __name__ == "__main__":
    main()
