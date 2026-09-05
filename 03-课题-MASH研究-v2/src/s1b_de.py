# -*- coding: utf-8 -*-
"""
S1b: 探针注释 + limma风格差异分析 + 靶点方向验证 + KEGG ORA（全新实现）。
GSE48452 (GPL11532 HuGene1.1ST, 主): NASH(18) vs Control(14), 次对照NASH vs Healthy-obese(27)。
GSE63067 (GPL570 U133Plus2, 复验): NASH(9) vs Healthy(7)。
探针->基因: 每符号取IQR最大探针。DE: Welch t + BH。
"""

# Historical pipeline: its outputs are invalidated; corrected code lives in 00-当前研究.
raise RuntimeError("此历史入口已停用以保留原数据与结果；请使用仓库00-当前研究中的诊断/修订流程。")
import gzip, io, json, os, re, urllib.request
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

D = "D:/zcode-workspace/mash_v2_new"
GEO, RES = f"{D}/data/geo", f"{D}/results"
os.makedirs(f"{RES}/tables", exist_ok=True)

def fetch(url, path):
    if not os.path.exists(path):
        req = urllib.request.Request(url, headers={"User-Agent": "academic-research/2.0"})
        with urllib.request.urlopen(req, timeout=600) as r, open(path, "wb") as f:
            f.write(r.read())
    return path

# ---------- 平台注释 ----------
def load_gpl_annot(gpl):
    """GEO平台annot.gz -> DataFrame indexed by probe with 'Gene symbol' col"""
    pref = gpl[:-3] + "nnn"
    url = f"https://ftp.ncbi.nlm.nih.gov/geo/platforms/{pref}/{gpl}/annot/{gpl}.annot.gz"
    p = fetch(url, f"{GEO}/{gpl}.annot.gz")
    txt = gzip.open(p, "rt", encoding="utf-8", errors="ignore").read()
    header, rows, in_t = None, [], False
    for line in txt.splitlines():
        if line.startswith("!platform_table_begin"):
            in_t = True
        elif line.startswith("!platform_table_end"):
            break
        elif in_t:
            if header is None:
                header = line.split("\t")
            else:
                rows.append(line.split("\t"))
    df = pd.DataFrame(rows, columns=header)
    df = df.set_index(df.columns[0])
    sym_col = [c for c in df.columns if c.lower() in ("gene symbol", "gene_symbol", "symbol")][0]
    return df[[sym_col]].rename(columns={sym_col: "symbol"})

print("loading annotations ...")
ann1 = load_gpl_annot("GPL11532")
ann2 = load_gpl_annot("GPL570")
print("GPL11532 probes:", len(ann1), "| GPL570 probes:", len(ann2))

def collapse(expr, ann):
    expr = expr.copy()
    expr.index = expr.index.astype(str)
    ann = ann.copy()
    ann.index = ann.index.astype(str)
    m = expr.join(ann, how="inner")
    m = m[m["symbol"].notna() & (m["symbol"] != "")]
    iqr = m.drop(columns="symbol").std(1)   # 以std为活跃度代理
    m = m.assign(_s=iqr)
    m = m.sort_values("_s", ascending=False).drop_duplicates("symbol")
    out = m.drop(columns="_s").set_index("symbol")
    return out.sort_index()

e1 = pd.read_csv(f"{GEO}/GSE48452_expr_raw.csv.gz", index_col=0)
e2 = pd.read_csv(f"{GEO}/GSE63067_expr_raw.csv.gz", index_col=0)
g1 = collapse(e1, ann1)
g2 = collapse(e2, ann2)
print("gene-level:", g1.shape, g2.shape)
print("value range check (应已在log2量级):",
      float(np.nanmin(g1.values)), "-", float(np.nanmax(g1.values)))

g1.to_csv(f"{GEO}/GSE48452_gene_expr.csv.gz", compression="gzip")
g2.to_csv(f"{GEO}/GSE63067_gene_expr.csv.gz", compression="gzip")

meta1 = pd.read_csv(f"{GEO}/GSE48452_meta.csv", index_col=0)
meta2 = pd.read_csv(f"{GEO}/GSE63067_meta.csv", index_col=0)

def de(mat, a_ids, b_ids, label, d0=3.0):
    """limma风格: 经验贝叶斯方差收缩(Smyth 2004简化: 先验方差=中位数, 先验自由度d0)"""
    A = mat[a_ids].to_numpy(float)
    B = mat[b_ids].to_numpy(float)
    na, nb = A.shape[1], B.shape[1]
    lfc = np.nanmean(A, 1) - np.nanmean(B, 1)
    va = np.nanvar(A, axis=1, ddof=1)
    vb = np.nanvar(B, axis=1, ddof=1)
    sa2, sb2 = va / na, vb / nb
    s2 = sa2 + sb2                       # 差异方差估计
    d = na + nb - 2                      # 有效自由度(Welch近似简化为合并)
    s20 = np.nanmedian(s2)               # 先验方差
    s2_shrunk = (d0 * s20 + d * s2) / (d0 + d)
    t = lfc / np.sqrt(s2_shrunk)
    df = d + d0
    p = 2 * stats.t.sf(np.abs(t), df)
    padj = multipletests(p, method="fdr_bh")[1]
    res = pd.DataFrame({"log2FC": lfc, "p": p, "padj": padj}, index=mat.index)
    sig = res[(res.padj < 0.05) & (res.log2FC.abs() > 0.5)].dropna()
    print(f"[{label}] DEG={len(sig)} up={(sig.log2FC>0).sum()} down={(sig.log2FC<0).sum()}")
    return res

# 主比较
c1 = meta1["group"]
r_nash_ctrl = de(g1, c1[c1 == "Nash"].index, c1[c1 == "Control"].index, "GSE48452 NASH vs Control")
r_ss_ctrl = de(g1, c1[c1 == "Steatosis"].index, c1[c1 == "Control"].index, "GSE48452 SS vs Control")
r_nash_hob = de(g1, c1[c1 == "Nash"].index, c1[c1 == "Healthy obese"].index, "GSE48452 NASH vs HealthyObese")
c2 = meta2["disease status"]
r2_nash = de(g2, c2[c2 == "non-alcoholic steatohepatitis"].index,
             c2[c2 == "healthy"].index, "GSE63067 NASH vs Healthy")
r_nash_ctrl.to_csv(f"{GEO}/deg_GSE48452_NASHvsControl.csv")
r2_nash.to_csv(f"{GEO}/deg_GSE63067_NASHvsHealthy.csv")

# ---------- 靶点验证 ----------
print("\n===== 靶点方向验证 (主队列 GSE48452 NASH vs Control; 复验 GSE63067) =====")
fib_raw = meta1["fibrosis"].astype(str)
fib_map = {"0": 0, "1": 1, "1a": 1, "1b": 1, "2": 2, "2a": 2, "2b": 2, "3": 3, "4": 4}
fib = fib_raw.map(lambda v: fib_map.get(v.strip().lower(), np.nan))
TARGETS = {
    "THRB": "THR-b(靶点1, 激动)", "FASN": "FASN(靶点2, 抑制)", "SCD": "SCD1(靶点3, 抑制)",
    "THRA": "THR-a(参考)", "DGAT2": "DGAT2(备选记录)", "ACACA": "ACC1(参考)",
    "PPARA": "PPARa(参考)", "SREBF1": "SREBP1c(参考)",
    "COL1A1": "纤维化对照", "ACTA2": "纤维化对照", "TIMP1": "纤维化对照",
    "TNF": "炎症对照", "IL6": "炎症对照", "CYP7A1": "代谢参考",
}
rows = []
for gene, role in TARGETS.items():
    r = r_nash_ctrl.loc[gene] if gene in r_nash_ctrl.index else None
    r2 = r2_nash.loc[gene] if gene in r2_nash.index else None
    rho = np.nan
    if gene in g1.index and fib.notna().sum() > 5:
        rho = stats.spearmanr(fib, g1.loc[gene, fib.index]).statistic
    rows.append(dict(gene=gene, role=role,
                     log2FC=round(float(r.log2FC), 3) if r is not None else None,
                     padj=f"{r.padj:.2e}" if r is not None else None,
                     rep_log2FC=round(float(r2.log2FC), 3) if r2 is not None else None,
                     rep_padj=f"{r2.padj:.2e}" if r2 is not None else None,
                     spearman_fibrosis=round(float(rho), 3) if np.isfinite(rho) else None))
tg = pd.DataFrame(rows)
tg.to_csv(f"{RES}/tables/target_validation_new.csv", index=False)
print(tg.to_string(index=False))

# ---------- KEGG ORA ----------
print("\nKEGG ORA (fresh download) ...")
os.makedirs(f"{D}/data/kegg", exist_ok=True)
link_path = f"{D}/data/kegg/link_pathway_hsa.txt"
fetch("https://rest.kegg.jp/link/pathway/hsa", link_path)
m2p = {}
for line in open(link_path, encoding="utf-8"):
    g, pth = line.split()
    m2p.setdefault(pth.split(":")[1], set()).add(g.split(":")[1])
name_path = f"{D}/data/kegg/list_pathway_hsa.txt"
fetch("https://rest.kegg.jp/list/pathway/hsa", name_path)
pnames = {}
for line in open(name_path, encoding="utf-8"):
    parts = line.rstrip("\n").split("\t")
    if len(parts) >= 2:
        pnames[parts[0].replace("path:", "")] = parts[1]
# entrez->symbol 映射: 用NCBI gene info (大文件) 或用已存GPL注释反查不可靠; 用EUtils批查
# 简化: 用KEGG的hsa基因全表 conv
conv_path = f"{D}/data/kegg/conv_hsa_ncbi.txt"
fetch("https://rest.kegg.jp/conv/hsa/ncbi-geneid", conv_path)
kegg2sym = {}
for line in open(conv_path, encoding="utf-8"):
    a, b = line.split()
    kegg2sym[b.split(":")[1]] = a.split(":")[1]  # ncbi_geneid -> hsa:K0? no: a=hsa:1234 b=ncbi-geneid:1234
# 上面格式: hsa:1234 ncbi-geneid:1234 —— 需要symbol: 改用KEGG list hsa? 已知返回全基因组符号表不可用。
# 用EUtils esummary批查symbol
import time
entrez_all = sorted({t for s in m2p.values() for t in s})
t2s = {}
for i in range(0, len(entrez_all), 300):
    chunk = entrez_all[i:i + 300]
    url = ("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=gene&id="
           + ",".join(chunk) + "&retmode=json")
    try:
        js = json.loads(urllib.request.urlopen(
            urllib.request.Request(url, headers={"User-Agent": "academic/2.0"}), timeout=60).read())
        for uid in js.get("result", {}).get("uids", []):
            nm = js["result"][uid].get("name", "")
            if nm:
                t2s[uid] = nm
    except Exception:
        pass
    time.sleep(0.4)
print("symbols resolved:", len(t2s))
m2p_sym = {p: {t2s[t] for t in s if t in t2s} for p, s in m2p.items()}
json.dump({p: sorted(s) for p, s in m2p_sym.items()}, open(f"{D}/data/kegg/pathways_symbol.json", "w"))

sig_genes = set(r_nash_ctrl[(r_nash_ctrl.padj < 0.05) & (r_nash_ctrl.log2FC.abs() > 0.5)].dropna().index)
universe = set(g1.index) & set().union(*m2p_sym.values())
N = len(universe)
sig_u = sig_genes & universe
enr = []
for pid, gset in m2p_sym.items():
    ov = sig_u & gset & universe
    if len(ov) < 5:
        continue
    K = len(gset & universe)
    p = stats.hypergeom.sf(len(ov) - 1, N, K, len(sig_u))
    enr.append(dict(pathway=pid, name=pnames.get(pid, pid)[:60], overlap=len(ov), size=K, p=p))
enr = pd.DataFrame(enr)
if len(enr) == 0:
    print("ORA: no pathway with overlap>=5 — DEG集过小, 记录为空")
    enr = pd.DataFrame(columns=["pathway", "name", "overlap", "size", "p", "padj"])
else:
    enr["padj"] = multipletests(enr.p, method="fdr_bh")[1]
enr.sort_values("p").head(25).to_csv(f"{RES}/tables/kegg_ora_new.csv", index=False)
if len(enr):
    print(enr.sort_values("p").head(12).to_string(index=False))
    print(f"\nuniverse={N}, DEG_in_universe={len(sig_u)}")

json.dump(dict(primary="GSE48452", replication="GSE63067",
               n_deg_primary=int(len(sig_genes))),
          open(f"{RES}/tables/s1_summary.json", "w"), indent=1)
print("\nS1 complete.")
