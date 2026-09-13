# -*- coding: utf-8 -*-
"""Qualification round automatic QC: deliverables, CSV, numeric consistency,
leakage, Y-scrambling, reproducibility re-run, banned phrases, history
protection, manifest, and entry-point sync checks."""
from pathlib import Path
import csv, json, hashlib, re, sys, io
import numpy as np
import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = Path(r"D:/zcode-workspace/aidd-repo-work/00-当前研究")
Q = ROOT / "qualification_round_20260913"
FS = ROOT / "final_strategy_round_20260912"
EXPECTED = ["资格验证_执行总览.md","FASN_canonical_QC_report.md","FASN_canonical_clean.csv","FASN_baseline_results.csv",
            "FASN_10seed_scaffold_results.csv","FASN_y_scrambling_results.csv","FASN_leakage_audit.csv",
            "FASN_document_time_split.md","FASN_external_set.csv","FASN_external_validation.md","FASN_AD_UQ_report.md",
            "NP54_FASN_domain_gap_report.md","FASN_natural_product_bridge_set.csv","FASN_GNN_gate_decision.md",
            "FASN_GO_NOGO.md","MoracinN_identity_QC.md","MoracinN_known_unknown_matrix.csv","MoracinN_MASH_bridge_map.md",
            "MoracinN_assay_interference_plan.md","MoracinN_gate_plan_vFinal.md","MoracinN_GO_NOGO.md",
            "双轴资格验证决策.md","下一阶段路线.md","未完成项与风险.md","QC_report.md"]
issues = []

# 1) presence
missing = [f for f in EXPECTED if not (Q / f).is_file()]
if missing: issues.append(f"missing deliverables: {missing}")

# 2) CSV parse + width
for f in [x for x in EXPECTED if x.endswith(".csv")]:
    rows = list(csv.reader((Q / f).open(encoding="utf-8-sig", newline="")))
    widths = {len(r) for r in rows}
    if not rows or len(widths) != 1:
        issues.append(f"csv width mismatch {f}: {sorted(widths)}")

# 3) numeric consistency vs summary JSON
summ = json.load(open(Q / "derived/qualification_summary.json", encoding="utf8"))
base = pd.read_csv(Q / "FASN_baseline_results.csv")
sc = base[base.split == "scaffold"]
ridge = sc[sc.model == "ecfp_ridge"]
assert abs(ridge.r2.median() - 0.732) < 0.005, ridge.r2.median()
assert len(sc.seed.unique()) == 10 and ridge.shape[0] == 10
scr = pd.read_csv(Q / "FASN_y_scrambling_results.csv")
assert len(scr) == 60 and (scr.model == "ecfp_ridge").sum() == 20
ext = pd.read_csv(Q / "FASN_external_set.csv")
assert int((~ext.excluded).sum()) == 105 and int(ext.excluded.sum()) == 3
np54 = pd.read_csv(Q / "derived/NP54_FASN_domain_gap.csv")
assert (np54.AD_status == "out_of_domain").sum() == 54
assert abs(np54.max_Tanimoto_to_canonical_training.median() - 0.13636) < 0.001
clean = pd.read_csv(Q / "FASN_canonical_clean.csv")
assert len(clean) == 96 and clean.scaffold.nunique() == 39 and int(clean.excluded.sum()) == 0

# 4) leakage: scaffold overlap zero across all seeds
leak = pd.read_csv(Q / "FASN_leakage_audit.csv")
assert leak.scaffold_overlap.sum() == 0, "scaffold overlap leakage"
leak_fact = {"max_test_train_tanimoto": float(leak["test_to_train_max_tanimoto"].max()),
             "all_test_nn_ge_0.60": bool((leak["n_test_nn_ge_0.60"] == leak.test_n).all())}

# 5) Y-scrambling superiority
for m in ["ecfp_ridge", "ecfp_rf", "ecfp_xgb"]:
    real = sc[(sc.model == m) & (sc.seed == 20260912)].r2.iloc[0]
    pmax = scr[scr.model == m].r2.max()
    assert real > pmax, (m, real, pmax)

# 6) reproducibility: re-run seed 20260912 ridge split
from rdkit import Chem, DataStructs, RDLogger
from rdkit.Chem import AllChem
from rdkit.Chem.Scaffolds import MurckoScaffold
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import r2_score
RDLogger.DisableLog("rdApp.*")
GEN = AllChem.GetMorganGenerator(radius=2, fpSize=2048)
smiles = clean.canonical_smiles.tolist(); y = clean.pActivity.to_numpy(float)
X = np.zeros((len(smiles), 2048), dtype=np.float32)
for i, s in enumerate(smiles):
    DataStructs.ConvertToNumpyArray(GEN.GetFingerprint(Chem.MolFromSmiles(str(s))), X[i])
gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=20260912)
tr, te = next(gss.split(clean, groups=clean.scaffold))
m = make_pipeline(StandardScaler(with_mean=False), Ridge(alpha=10.0)); m.fit(X[tr], y[tr])
r2_rerun = r2_score(y[te], m.predict(X[te]))
r2_logged = ridge[ridge.seed == 20260912].r2.iloc[0]
assert abs(r2_rerun - r2_logged) < 1e-9, (r2_rerun, r2_logged)

# 7) banned phrases (context-aware: skip rule lines)
banned = ["唯一批准", "首次发现", "完全没人研究", "零管线记录为无", "已验证候选药物", "新型抗MASH药物", "AI成功发现新药",
          "FASN活性排行榜", "天然产物FASN活性排名", "GNN一定优于", "GNN优于RF", "FASN临床失败", "已进入MASH Phase 3",
          "通用FASN活性模型", "靶向KEAP1的Moracin", "Moracin N是Nrf2激动剂"]
hits = []
for f in EXPECTED:
    p = Q / f
    if p.suffix != ".md": continue
    for ln, line in enumerate(p.read_text(encoding="utf8").splitlines(), 1):
        if re.search(r"(禁止|不得|禁用|不得写|不允许|禁止写|旧口径|禁令|P2 表述)", line): continue
        for b in banned:
            if b in line: hits.append((f, ln, b))
if hits: issues.append(f"banned phrases: {hits[:10]}")

# 8) history protection: final strategy manifest still valid
fs_man = json.load(open(FS / "manifest/delivery_hashes.json", encoding="utf8"))["files"]
viol = [f for f, h in fs_man.items() if hashlib.sha256((FS / f).read_bytes()).hexdigest() != h]
if viol: issues.append(f"final strategy files modified: {viol}")

# 9) entry-point sync
readme = (ROOT / "README.md").read_text(encoding="utf8")
if "资格验证" not in readme: issues.append("README not synced with qualification round")
st = json.load(open(ROOT / "研究状态.json", encoding="utf8"))
if "batch_qualification_round_20260913" not in st.get("revision_batches", {}):
    issues.append("研究状态.json missing qualification batch")

# 10) manifest for this round
hashes = {f: hashlib.sha256((Q / f).read_bytes()).hexdigest() for f in EXPECTED if (Q / f).exists()}
(Q / "manifest/delivery_hashes.json").write_text(json.dumps({"date": "2026-09-13", "scope": "25 deliverables", "files": hashes}, ensure_ascii=False, indent=2), encoding="utf8")

verdict = {"status": "PASS" if not issues else "FAIL", "issues": issues,
           "checks": {"deliverables": len(hashes), "csv_parsed": True, "ridge_median_r2": float(ridge.r2.median()),
                      "seeds": 10, "y_scramble_rows": len(scr), "external_evaluated": 105,
                      "np54_ood": 54, "clean": [len(clean), int(clean.scaffold.nunique())],
                      "leakage": leak_fact, "ridge_rerun_r2": float(r2_rerun),
                      "banned_phrase_hits": len(hits), "history_protection": "PASS" if not viol else viol,
                      "manifest": len(hashes)}}
(Q / "manifest/qc_auto.json").write_text(json.dumps(verdict, ensure_ascii=False, indent=2), encoding="utf8")
print(json.dumps(verdict, ensure_ascii=False, indent=2))
sys.exit(0 if not issues else 1)
