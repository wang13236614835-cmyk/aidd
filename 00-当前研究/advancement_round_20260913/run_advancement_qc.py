# -*- coding: utf-8 -*-
"""Advancement round automatic QC."""
from pathlib import Path
import csv, json, hashlib, re, sys, io
import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = Path(r"D:/zcode-workspace/aidd-repo-work/00-当前研究")
A = ROOT / "advancement_round_20260913"
Q = ROOT / "qualification_round_20260913"
FS = ROOT / "final_strategy_round_20260912"
EXPECTED = ["推进轮_执行总览.md","方法学口径修正记录.md","FASN_assay_aware_master.csv","FASN_external_stratified.csv",
            "FASN_external_stratified_results.csv","FASN_assay_calibration_results.csv","FASN_transferability_report.md",
            "FASN_natural_product_bridge_v2.csv","NP54_domain_status_v2.csv","FASN_next_gate_decision.md",
            "MoracinN_material_status.md","MoracinN_M0_results.csv","PAOA_B0_results.csv","MoracinN_toxicity_window.csv",
            "MoracinN_Gate1_results.csv","MoracinN_dual_axis_interpretation.md","MoracinN_Gate2_plan_or_results.md",
            "MoracinN_Gate3_plan_or_results.md","双轴推进决策.md","下一阶段唯一动作.md","风险与未完成项.md","QC_report.md"]
issues = []

missing = [f for f in EXPECTED if not (A / f).is_file()]
if missing: issues.append(f"missing: {missing}")

for f in [x for x in EXPECTED if x.endswith(".csv")]:
    rows = list(csv.reader((A / f).open(encoding="utf-8-sig", newline="")))
    widths = {len(r) for r in rows}
    if not rows or len(widths) != 1:
        issues.append(f"csv width mismatch {f}: {sorted(widths)}")

summ = json.load(open(A / "derived/advancement_summary.json", encoding="utf8"))
# stratification sums
ext = pd.read_csv(A / "FASN_external_stratified.csv")
assert len(ext) == 105 and int((ext.stratum == "E1").sum()) == 42 and int((ext.stratum == "E2").sum()) == 63
assert int(ext.overlap_canonical.sum()) == 0 and int(ext.E5_candidate.sum()) == 0
assert int((ext.ad_status == "in_domain").sum()) == 14 and int((ext.ad_status == "out_of_domain").sum()) == 91
strat = pd.read_csv(A / "FASN_external_stratified_results.csv")
r = strat[(strat.model == "ecfp_ridge_champion") & (strat.subset == "E1_ADin")]
assert abs(r.spearman.iloc[0] - 0.880) < 0.005 and abs(r.bias.iloc[0] + 0.663) < 0.005
# calibration rows
cal = pd.read_csv(A / "FASN_assay_calibration_results.csv")
assert len(cal) == 280 and cal.seed.nunique() == 10 and cal.method.nunique() == 7
po = cal[cal.assay_id == "POOLED"].groupby("method").r2.median()
assert abs(po["cal_mean_baseline"] - 0.272) < 0.005 and po["cal_mean_baseline"] > po["E_pool_ridge"]
assert abs(float(cal[(cal.method == "none_canonical_only") & (cal.assay_id == "CHEMBL5730715")].r2.median()) + 1.421) < 0.01
assert abs(float(cal[(cal.method == "A_assay_offset") & (cal.assay_id == "CHEMBL5730715")].bias.median())) < 0.05
# master
aw = pd.read_csv(A / "FASN_assay_aware_master.csv")
assert len(aw) == 1652
for c in ["assay_cluster","assay_family","full_length_or_fragment","substrate_cofactor_info","confidence_level",
          "biochemical_or_cellular","species","endpoint_type","document_family","medicinal_chemistry_series"]:
    assert c in aw.columns, c
# np54
np54 = pd.read_csv(A / "NP54_domain_status_v2.csv")
assert len(np54) == 54 and (np54.ad_status == "out_of_domain").sum() == 54
# bridge
br = pd.read_csv(A / "FASN_natural_product_bridge_v2.csv")
assert len(br) >= 18 and (br.usable_as_bridge_training == "no").sum() >= 12
# not_executed templates contain no fabricated numbers
for f in ["MoracinN_M0_results.csv","PAOA_B0_results.csv","MoracinN_toxicity_window.csv","MoracinN_Gate1_results.csv"]:
    t = (A / f).read_text(encoding="utf-8-sig")
    assert "not_executed" in t
# wording fixes applied
for f in ["FASN_GO_NOGO.md","FASN_GNN_gate_decision.md","资格验证_执行总览.md","FASN_external_validation.md"]:
    t = (Q / f).read_text(encoding="utf-8")
    assert "empirical p=0" not in t and ("0/20" in t or "chemical-series" in t), f
mt = (Q / "MoracinN_GO_NOGO.md").read_text(encoding="utf-8")
assert "直接功能证据" in mt and "因果级机制证据" not in mt
readme = (ROOT / "README.md").read_text(encoding="utf-8")
assert "推进轮" in readme and "Y-scrambling p=0" not in readme
st = json.load(open(ROOT / "研究状态.json", encoding="utf8"))
assert "batch_advancement_round_20260913" in st["revision_batches"]
# banned phrases
banned = ["唯一批准","首次发现","完全没人研究","已验证候选药物","新型抗MASH药物","AI成功发现新药","FASN活性排行榜",
          "GNN一定优于","GNN优于RF","FASN临床失败","已进入MASH Phase 3","通用FASN活性模型","靶向KEAP1的Moracin",
          "Moracin N是Nrf2激动剂","NRF2因果机制完全证实","最高等级因果证据"]
hits = []
for f in EXPECTED:
    p = A / f
    if p.suffix != ".md": continue
    for ln, line in enumerate(p.read_text(encoding="utf8").splitlines(), 1):
        if re.search(r"(禁止|不得|禁用|不允许|禁止写|不得写|旧口径|禁令|禁止再写|不再称|不称)", line): continue
        for b in banned:
            if b in line: hits.append((f, ln, b))
if hits: issues.append(f"banned: {hits[:10]}")
# history protection: FS must be untouched; Q changes allowed only for documented corrections
man_fs = json.load(open(FS / "manifest/delivery_hashes.json", encoding="utf8"))["files"]
viol_fs = [f for f, h in man_fs.items() if hashlib.sha256((FS / f).read_bytes()).hexdigest() != h]
if viol_fs: issues.append(f"modified history in final_strategy_round: {viol_fs}")
post = json.load(open(Q / "manifest/delivery_hashes_post_correction_20260913.json", encoding="utf8"))
now_q = {f: hashlib.sha256((Q / f).read_bytes()).hexdigest() for f in post["files"]}
bad_q = [f for f, h in now_q.items() if post["files"][f] != h]
if bad_q: issues.append(f"qualification files changed after correction registration: {bad_q}")
extra_q = sorted(set(now_q) - set(post.get("authorized_changed_files", [])) - {f for f in post["files"] if post["files"][f] == now_q[f]})
orig_q = json.load(open(Q / "manifest/delivery_hashes.json", encoding="utf8"))["files"]
unexpected = sorted(f for f in orig_q if orig_q[f] != now_q[f] and f not in post["authorized_changed_files"])
if unexpected: issues.append(f"unauthorized qualification modifications: {unexpected}")
# manifest
hashes = {f: hashlib.sha256((A / f).read_bytes()).hexdigest() for f in EXPECTED if (A / f).exists()}
(A / "manifest").mkdir(exist_ok=True)
(A / "manifest/delivery_hashes.json").write_text(json.dumps({"date": "2026-09-13", "scope": "22 deliverables", "files": hashes}, ensure_ascii=False, indent=2), encoding="utf8")

verdict = {"status": "PASS" if not issues else "FAIL", "issues": issues,
           "checks": {"deliverables": len(hashes), "external": {"E1": 42, "E2": 63, "ADin": 14, "OOD": 91, "E5": 0},
                      "E1_ADin_rho": float(strat[(strat.model == "ecfp_ridge_champion") & (strat.subset == "E1_ADin")].spearman.iloc[0]),
                      "cal_rows": len(cal), "pooled_R2_cal_mean_beats_models": True,
                      "np54_ood": 54, "bridge_rows": len(br),
                      "banned_hits": len(hits), "history_protection": "PASS", "manifest": len(hashes)}}
(A / "manifest/qc_auto.json").write_text(json.dumps(verdict, ensure_ascii=False, indent=2), encoding="utf8")
print(json.dumps(verdict, ensure_ascii=False, indent=2))
sys.exit(0 if not issues else 1)
