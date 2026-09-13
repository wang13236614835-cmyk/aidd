# -*- coding: utf-8 -*-
"""第六轮终检：交付完整性 / 禁用表述 / CSV 完整性 / 预算一致性 / 哈希清单"""
import csv, json, hashlib, sys
from pathlib import Path

BASE = Path("D:/zcode-workspace/aidd-repo-work/00-当前研究/sixth_round_20260912")
issues = []

# 1. 交付完整性（§14 的 13 个文件）
required = ["第六轮_执行总览.md","MoracinN_实验物料审计.csv","候选采购清单.csv","MASH细胞模型选择.md",
 "MoracinN_剂量设计.md","MoracinN_三级门控实验方案.md","Formononetin_FXR依赖性验证方案.md",
 "对照体系定义.md","实验统计预注册.md","最小实验预算.csv","Go_NoGo决策表.md",
 "导师审批版_一页实验方案.md","第六轮未完成项.md"]
missing = [f for f in required if not (BASE/f).exists()]
print("交付完整性:", "OK 13/13" if not missing else f"缺失 {missing}")
if missing: issues.append(f"missing:{missing}")

# 2. 禁用表述扫描（第五轮口径 + 第六轮叙事冻结）
banned = ["无人研究","零记录","零专利","完全空白","首次发现","唯一批准药物","计算最强","已证实候选",
          "MASH已验证","MASH 已验证","TRβ激动剂","TRβ 激动剂","亚型选择性","AI成功发现新药","AI 成功发现新药",
          "新型抗MASH药物","新型抗 MASH 药物","完整 MASH 模型","完整MASH模型","已验证候选","机制已证实"]
# 语境感知：禁令/否定行（禁止…、不得…、无任何…、永不…、非…）中的引用合法，豁免
ALLOW_CTX = ("禁止","不得","无任何","永不","严禁","非完整")
for f in required:
    p = BASE/f
    if p.suffix != ".md": continue
    t = p.read_text(encoding="utf-8")
    for b in banned:
        for i,l in enumerate(t.splitlines()):
            if b in l:
                if any(a in l for a in ALLOW_CTX):
                    continue  # 禁令/否定语境中的引用，合法
                issues.append(f"{f}:{i+1}: 含禁用表述「{b}」")
                print(f"  命中 {f}:{i+1} 「{b}」→ {l[:60]}")
print("禁用表述:", "OK 无命中" if not issues else f"{len(issues)} 处命中")

# 3. CSV 列完整性
def check_csv(name, expect_cols, expect_min_rows):
    with open(BASE/name, encoding="utf-8-sig") as fh:
        rows = list(csv.reader(fh))
    hdr, body = rows[0], rows[1:]
    if len(hdr) != expect_cols: issues.append(f"{name}: 表头 {len(hdr)} 列 ≠ 预期 {expect_cols}")
    bad = [i+2 for i,r in enumerate(body) if len(r) != len(hdr)]
    if bad: issues.append(f"{name}: 行 {bad} 列数不齐")
    if len(body) < expect_min_rows: issues.append(f"{name}: 数据行 {len(body)} < {expect_min_rows}")
    return hdr, body

h1,b1 = check_csv("MoracinN_实验物料审计.csv", 7, 20)
h2,b2 = check_csv("候选采购清单.csv", 12, 18)
h3,b3 = check_csv("最小实验预算.csv", 5, 30)
print(f"CSV: 物料审计 {len(b1)} 行 / 采购清单 {len(b2)} 行 / 预算 {len(b3)} 行（含小计）")

# 4. 预算一致性：CSV 合计 vs budget_summary.json vs 总览声明数字
totals = {}
for r in b3:
    if r[0] and r[1] == "合计":
        totals[r[0]] = int(r[3])
summ = json.loads((BASE/"derived/budget_summary.json").read_text(encoding="utf-8"))
def norm(s): return s.replace("（","(").replace("）",")")
summ_norm = {norm(k):v for k,v in summ["tiers_total_cny"].items()}
decl = {"最低":3685, "标准":4804, "扩展":8845}
for k,v in decl.items():
    match = [tk for tk in totals if tk.startswith(k)]
    if not match: issues.append(f"预算CSV缺合计行:{k}档")
    elif totals[match[0]] != v: issues.append(f"预算不一致 {k}档: CSV={totals[match[0]]} 声明={v}")
    sv = next((x for kk,x in summ_norm.items() if kk.startswith(k)), None)
    if sv != v: issues.append(f"budget_summary 不一致 {k}档: {sv} vs {v}")
print("预算一致性:", "OK 三档 3685/4804/8845" if not [i for i in issues if "预算" in i or "budget" in i] else "FAIL")

# 5. 关键数字交叉核对（总览/一页方案/门控方案中的预算与判据数字）
for f, nums in {"第六轮_执行总览.md":[3685,4804,8845,3419], "导师审批版_一页实验方案.md":[3685,4804,8845,3419]}.items():
    t = (BASE/f).read_text(encoding="utf-8")
    for n in nums:
        if str(n) not in t: issues.append(f"{f}: 缺关键数字 {n}")
for f, thr in {"MoracinN_三级门控实验方案.md":["25%","15%","70%","30%"], "实验统计预注册.md":["25%","15%"]}.items():
    t = (BASE/f).read_text(encoding="utf-8")
    for n in thr:
        if n not in t: issues.append(f"{f}: 缺预冻结阈值 {n}")

# 6. 哈希清单（全包，排除 manifest 自身）
manifest = {"generated":"2026-09-12","algorithm":"sha256","files":{}}
for p in sorted(BASE.rglob("*")):
    if p.is_file() and "manifest" not in p.parts:
        manifest["files"][str(p.relative_to(BASE)).replace("\\","/")] = hashlib.sha256(p.read_bytes()).hexdigest()
(BASE/"manifest/delivery_hashes.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"哈希: {len(manifest['files'])} 个文件 → manifest/delivery_hashes.json")

print("\n=== 终检结论 ===")
if issues:
    print("FAIL/需修复:")
    for i in issues: print(" -", i)
    sys.exit(1)
print("PASS：13 交付齐全、禁用表述零命中、CSV 列齐、预算三档一致、关键判据数字在位")
