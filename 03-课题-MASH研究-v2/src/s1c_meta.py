# -*- coding: utf-8 -*-
"""
S1c: 跨队列meta-DE + 靶点证据总表 + 基于meta-DEG的KEGG ORA + 纤维化/NAS相关。
GSE48452(NASH vs Control, n=18/14) 与 GSE63067(NASH vs Healthy, n=9/7) 的z值Stouffer合并。
"""
import json
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

D = "D:/zcode-workspace/mash_v2_new"
GEO, RES = f"{D}/data/geo", f"{D}/results"

r1 = pd.read_csv(f"{GEO}/deg_GSE48452_NASHvsControl.csv", index_col=0)
r2 = pd.read_csv(f"{GEO}/deg_GSE63067_NASHvsHealthy.csv", index_col=0)
g1 = pd.read_csv(f"{GEO}/GSE48452_gene_expr.csv.gz", index_col=0)
meta1 = pd.read_csv(f"{GEO}/GSE48452_meta.csv", index_col=0)

common = r1.index.intersection(r2.index)
print(f"common genes: {len(common)}")

def to_z(p, lfc):
    z = stats.norm.isf(p / 2) * np.sign(lfc)
    return z

z1 = to_z(r1.loc[common, "p"].values, r1.loc[common, "log2FC"].values)
z2 = to_z(r2.loc[common, "p"].values, r2.loc[common, "log2FC"].values)
w1, w2 = np.sqrt(18 / 32), np.sqrt(9 / 16)   # 按有效样本比例加权
zmeta = (w1 * z1 + w2 * z2) / np.sqrt(w1 ** 2 + w2 ** 2)
pmeta = 2 * stats.norm.sf(np.abs(zmeta))
lfc_meta = (r1.loc[common, "log2FC"].values + r2.loc[common, "log2FC"].values) / 2
padj_meta = multipletests(pmeta, method="fdr_bh")[1]
meta = pd.DataFrame({"z_GSE48452": z1, "z_GSE63067": z2, "z_meta": zmeta,
                     "p_meta": pmeta, "padj_meta": padj_meta,
                     "log2FC_meta": lfc_meta,
                     "log2FC_1": r1.loc[common, "log2FC"].values,
                     "log2FC_2": r2.loc[common, "log2FC"].values},
                    index=common)
sig = meta[(meta.padj_meta < 0.05) & (meta.log2FC_meta.abs() > 0.5)]
print(f"meta-DEG: {len(sig)} (up {(sig.log2FC_meta>0).sum()} / down {(sig.log2FC_meta<0).sum()})")
meta.to_csv(f"{GEO}/deg_meta_two_cohorts.csv")
sig.to_csv(f"{GEO}/deg_meta_significant.csv")

# ---------- 靶点证据表 ----------
fib = pd.to_numeric(meta1["fibrosis"], errors="coerce")
nas = pd.to_numeric(meta1["nas"], errors="coerce")
TARGETS = {
    "THRB": "THR-b(靶点1,激动)", "FASN": "FASN(靶点2,抑制)", "SCD": "SCD1(靶点3,抑制)",
    "THRA": "THR-a(参考)", "DGAT2": "DGAT2(备选)", "ACACA": "ACC1(参考)",
    "ACACB": "ACC2(参考)", "PPARA": "PPARa(参考)", "SREBF1": "SREBP1c(参考)",
    "COL1A1": "纤维化对照", "TIMP1": "纤维化对照", "TNF": "炎症对照",
    "IL6": "炎症对照", "CCL2": "炎症对照", "CYP7A1": "代谢参考", "SORBS1": "代谢参考",
}
rows = []
for gene, role in TARGETS.items():
    if gene not in meta.index:
        rows.append(dict(gene=gene, role=role, note="not on array"))
        continue
    m = meta.loc[gene]
    rho_f = rho_n = np.nan
    if gene in g1.index:
        rho_f = stats.spearmanr(fib, g1.loc[gene, fib.index]).statistic
        rho_n = stats.spearmanr(nas, g1.loc[gene, nas.index]).statistic
    rows.append(dict(
        gene=gene, role=role,
        LFC_cohort1=round(float(m.log2FC_1), 3),
        LFC_cohort2=round(float(m.log2FC_2), 3),
        LFC_meta=round(float(m.log2FC_meta), 3),
        p_meta=f"{m.p_meta:.2e}", padj_meta=f"{m.padj_meta:.2e}",
        direction_consistent="Y" if np.sign(m.log2FC_1) == np.sign(m.log2FC_2) else "N",
        spearman_fibrosis=None if not np.isfinite(rho_f) else round(float(rho_f), 3),
        spearman_NAS=None if not np.isfinite(rho_n) else round(float(rho_n), 3)))
tg = pd.DataFrame(rows)
tg.to_csv(f"{RES}/tables/target_validation_new.csv", index=False)
print("\n===== 靶点证据总表 =====")
print(tg.to_string(index=False))

# ---------- ORA on meta-DEG ----------
pw = json.load(open(f"{D}/data/kegg/pathways_symbol.json"))
import gzip
pnames = {}
for line in open(f"{D}/data/kegg/list_pathway_hsa.txt", encoding="utf-8"):
    parts = line.rstrip("\n").split("\t")
    if len(parts) >= 2:
        pnames[parts[0].replace("path:", "")] = parts[1]
m2p = {p: set(v) for p, v in pw.items()}
sig_genes = set(sig.index)
universe = set(g1.index) & set().union(*m2p.values())
sig_u = sig_genes & universe
N = len(universe)
print(f"\nORA universe={N}, meta-DEG∩universe={len(sig_u)}")
enr = []
for pid, gset in m2p.items():
    ov = sig_u & gset
    if len(ov) < 4:
        continue
    K = len(gset & universe)
    p = stats.hypergeom.sf(len(ov) - 1, N, K, len(sig_u))
    enr.append(dict(pathway=pid, name=pnames.get(pid, pid)[:58], overlap=len(ov), size=K, p=p))
if enr:
    enr = pd.DataFrame(enr)
    enr["padj"] = multipletests(enr.p, method="fdr_bh")[1]
    enr.sort_values("p").head(25).to_csv(f"{RES}/tables/kegg_ora_new.csv", index=False)
    print(enr.sort_values("p").head(15).to_string(index=False))
else:
    print("ORA: no pathway passed overlap>=4")

json.dump(dict(meta_deg=int(len(sig)),
               up=int((sig.log2FC_meta > 0).sum()), down=int((sig.log2FC_meta < 0).sum())),
          open(f"{RES}/tables/s1_summary.json", "w"), indent=1)
print("\nS1c complete.")
