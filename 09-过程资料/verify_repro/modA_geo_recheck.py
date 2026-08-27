# -*- coding: utf-8 -*-
"""
模块A独立复算：GSE135251 DEG分析。
独立路径：scipy.stats.ttest_ind(逐基因, Welch) + 自写BH-FDR + 独立中位数比值标准化。
对账声明：
  分组 Normal 10 / NAFL 51 / NASH 155（README表格误写141，geo_summary=155）
  NASH_vs_Normal DEG=3909 (up1962/down1947); advFibrosis DEG=3859
  NR1H4: log2FC=-0.285 padj=1.03e-02 spearman=-0.145
  THRB: -0.315 / 1.99e-02 / -0.258; ACACA: +0.897 / 7.42e-05 / -0.070; ACACB: +0.631/4.23e-03/-0.179
  对照: FASN+2.47, CYP7A1+2.16, COL1A1+1.04(ρ=0.431), TNF+1.09
"""
import gzip, re
import numpy as np
import pandas as pd
from scipy import stats

D = "D:/zcode-workspace/mash_research"
GEO = f"{D}/data/geo"

# ---------- 计数矩阵 ----------
count = pd.read_csv(f"{GEO}/count_matrix_raw.csv.gz", index_col=0)
print(f"count matrix: {count.shape} | index example: {count.index[:3].tolist()}")

# ---------- series matrix 分组 ----------
txt = gzip.open(f"{GEO}/GSE135251_series_matrix.txt.gz", "rt",
                encoding="utf-8", errors="ignore").read()
samples, chars = None, {}
for line in txt.splitlines():
    if line.startswith("!Sample_geo_accession"):
        samples = [x.strip('"') for x in line.split("\t")[1:]]
    elif line.startswith("!Sample_characteristics_ch1"):
        vals = [x.strip('"') for x in line.split("\t")[1:]]
        key = re.sub(r":.*$", "", vals[0]).strip()
        chars[key] = [re.sub(r"^[^:]*:\s*", "", v).strip() for v in vals]
meta = pd.DataFrame(chars, index=samples)
grpcol = [c for c in meta.columns if "group in paper" in c][0]
print("group counts:\n", meta[grpcol].value_counts().to_string())

normal = meta.index[meta[grpcol].str.upper().str.contains("NORMAL|HEALTHY|CONTROL")]
nash = meta.index[meta[grpcol].str.startswith("NASH")]
nafl = meta.index[meta[grpcol] == "NAFL"]
print(f"Normal={len(normal)} NAFL={len(nafl)} NASH={len(nash)}  (claims 10/51/155, README误写141)")

fibcol = [c for c in meta.columns if "fibrosis" in c][0]
fib = meta[fibcol].astype(float)

# ---------- CPM过滤 + 中位数比值标准化（独立实现）----------
libsize = count.sum(0)
cpm_ok = ((count / (libsize / 1e6)) >= 1).sum(1) >= 10
cf = count[cpm_ok & count.index.isin(meta.index.map(str).union(count.index))]
cf = count[cpm_ok]
print("genes after CPM filter:", cf.shape[0])

# median-of-ratios：与原实现同公式，但用几何均值显式计算（exp(mean(log))）
with np.errstate(all="ignore"):
    gm = np.exp(np.log(cf.replace(0, np.nan)).mean(1))
ratio = cf.div(gm, axis=0)
sf = ratio.median(0).fillna(1)
norm = cf.div(sf, axis=1)
logn = np.log2(norm + 1)

# ---------- 独立Welch t检验（scipy逐基因）+ 自写BH ----------
def my_bh(p):
    p = np.asarray(p, float)
    n = len(p); o = np.argsort(p)
    q = np.empty(n)
    prev = 1.0
    for rank, i in enumerate(o[::-1]):
        r = n - rank
        val = min(prev, p[i] * n / r)
        q[i] = val; prev = val
    return q

def deg_indep(a_ids, b_ids, label):
    A = logn[list(a_ids)].to_numpy(float)   # genes x na
    B = logn[list(b_ids)].to_numpy(float)
    lfc = A.mean(1) - B.mean(1)
    p = np.empty(A.shape[0])
    for i in range(A.shape[0]):  # scipy Welch 逐基因，路径独立
        p[i] = stats.ttest_ind(A[i], B[i], equal_var=False).pvalue
    padj = my_bh(p)
    res = pd.DataFrame({"log2FC": lfc, "p": p, "padj": padj}, index=logn.index)
    sig = res[(res.padj < 0.05) & (res.log2FC.abs() > 0.5)]
    print(f"[{label}] my DEGs={len(sig)} up={(sig.log2FC>0).sum()} down={(sig.log2FC<0).sum()}"
          f"  (claims 3909/1962/1947 and 3859)")
    return res

res1 = deg_indep(nash, normal, "NASH_vs_Normal")
adv = meta.index[meta[grpcol].str.startswith(("NASH_F3", "NASH_F4"))]
res2 = deg_indep(adv, normal, "advFibrosis_vs_Normal")

# ---------- 靶点基因对账 ----------
ref = pd.read_csv(f"{D}/results/tables/target_genes_validation.csv")
print("\n=== TARGET GENES: mine vs archived ===")
rows = []
for g in ["NR1H4", "THRB", "ACACA", "ACACB", "FASN", "CYP7A1", "COL1A1", "TNF"]:
    if g not in res1.index:
        print(f"{g}: NOT in matrix!"); continue
    r = res1.loc[g]
    rho = stats.spearmanr(fib, logn.loc[g, fib.index]).statistic
    rr = ref[ref.gene == g]
    ref_lfc = float(rr.log2FC.iloc[0]) if len(rr) else np.nan
    ref_padj = float(rr.padj.iloc[0]) if len(rr) else np.nan
    ref_rho = float(rr.spearman_vs_fibrosis.iloc[0]) if (len(rr) and pd.notna(rr.spearman_vs_fibrosis.iloc[0])) else np.nan
    ok = (abs(r.log2FC - ref_lfc) < 0.006 and
          abs(r.padj - ref_padj) / max(ref_padj, 1e-12) < 0.02 and
          abs(rho - ref_rho) < 0.006)
    print(f"{g:8s} mine LFC={r.log2FC:+.3f} padj={r.padj:.2e} rho={rho:+.3f} || "
          f"ref LFC={ref_lfc:+.3f} padj={ref_padj:.2e} rho={ref_rho:+.3f} -> "
          f"{'PASS' if ok else 'CHECK'}")
    rows.append(dict(gene=g, lfc=r.log2FC, padj=r.padj, rho=rho))

# ---------- 与存档DEG表全表对账 ----------
arch = pd.read_csv(f"{GEO}/deg_NASH_vs_Normal.csv", index_col=0)
j = res1.join(arch, rsuffix="_arch", how="inner")
dl = (j.log2FC - j.log2FC_arch).abs().max()
dp = (j.p - j.p_arch).abs().max()
dq = (j.padj - j.padj_arch).abs().max()
print(f"\nfull-table vs archived deg_NASH_vs_Normal.csv (n={len(j)}): "
      f"max|dLFC|={dl:.2e} max|dp|={dp:.2e} max|dpadj|={dq:.2e}")
