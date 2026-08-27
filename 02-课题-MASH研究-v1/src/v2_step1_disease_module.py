# -*- coding: utf-8 -*-
"""
V2 Step1: disease-module discovery on GSE135251 (top-journal logic:
genotype-anchored + disease module hub genes).
WGCNA-lite in numpy: top-variable genes -> correlation -> hierarchical
modules -> eigengene-trait correlation (NAS, fibrosis) -> hub genes.
Real data, all inputs from prior verified pipeline.
"""
import gzip, re, json
import numpy as np
import pandas as pd
from scipy import stats, cluster

D = "D:/zcode-workspace/mash_research"
GEO, RES = f"{D}/data/geo", f"{D}/results/v2"
import os; os.makedirs(RES, exist_ok=True)

# metadata
txt = gzip.open(f"{GEO}/GSE135251_series_matrix.txt.gz", "rt", encoding="utf-8",
                errors="ignore").read()
samples, chars = None, {}
for line in txt.splitlines():
    if line.startswith("!Sample_geo_accession"):
        samples = [x.strip('"') for x in line.split("\t")[1:]]
    elif line.startswith("!Sample_characteristics_ch1"):
        vals = [x.strip('"') for x in line.split("\t")[1:]]
        key = re.sub(r":.*$", "", vals[0]).strip()
        chars[key] = [re.sub(r"^[^:]*:\s*", "", v).strip() for v in vals]
meta = pd.DataFrame(chars, index=samples)
nas = pd.to_numeric(meta["nas score"], errors="coerce")
fib = pd.to_numeric(meta["fibrosis stage"], errors="coerce")
grp = meta["group in paper"]

X = pd.read_csv(f"{GEO}/lognorm_matrix.csv.gz", index_col=0)
X = X[[c for c in X.columns if c in meta.index]]
nas, fib, grp = nas[X.columns], fib[X.columns], grp[X.columns]
print("matrix:", X.shape, "| NAS available:", nas.notna().sum())

# top 5000 variable genes
var = X.var(1).sort_values(ascending=False)
top = var.head(5000).index
V = X.loc[top].T.values  # samples x genes

# correlation -> distance -> modules
C = np.corrcoef(V.T)  # gene x gene
C = np.nan_to_num(C)
DIST = 1 - C
from scipy.spatial.distance import squareform
Z = cluster.hierarchy.linkage(squareform(DIST, checks=False), method="average")
labels = cluster.hierarchy.fcluster(Z, 18, criterion="maxclust")
lab = pd.Series(labels, index=top)
print("modules:", lab.nunique(), "| size range:", lab.value_counts().min(), "-",
      lab.value_counts().max())

# eigengene-trait correlations
rows = []
for m, genes in lab.groupby(lab):
    if len(genes) < 30:
        continue
    G = X.loc[genes.index].T.values
    eg = np.linalg.svd(G - G.mean(0), full_matrices=False)[0][:, 0]
    eg = eg * np.sign(np.corrcoef(eg, G.mean(1))[0, 1])  # orient
    r_nas = stats.spearmanr(eg, nas).statistic
    r_fib = stats.spearmanr(eg, fib).statistic
    # hub genes = |cor with eigengene| top
    mm = np.array([np.corrcoef(G[:, j], eg)[0, 1] for j in range(G.shape[1])])
    hub_idx = np.argsort(-np.abs(mm))[:15]
    hubs = [(genes.index[i], round(float(mm[i]), 2)) for i in hub_idx]
    rows.append(dict(module=m, n_genes=len(genes),
                     r_NAS=round(float(r_nas), 3), r_fib=round(float(r_fib), 3),
                     hub_genes=";".join(h[0] for h in hubs)))
modres = pd.DataFrame(rows).sort_values("r_NAS", key=abs, ascending=False)
modres.to_csv(f"{RES}/disease_modules.csv", index=False)
print(modres.to_string(index=False))

# hub-gene union from modules with |r_NAS| >= 0.5
sig = modres[modres["r_NAS"].abs() >= 0.5]
hub_union = []
for _, r in sig.iterrows():
    hub_union += r["hub_genes"].split(";")
hub_union = sorted(set(hub_union))
# differential expression check for hubs (reuse DEG table)
deg = pd.read_csv(f"{GEO}/deg_NASH_vs_Normal.csv", index_col=0)
hub_info = []
for g in hub_union:
    if g in deg.index:
        r = deg.loc[g]
        hub_info.append(dict(gene=g, module_r_NAS=None, log2FC=round(r.log2FC, 2),
                             padj=f"{r.padj:.1e}"))
pd.DataFrame(hub_info).to_csv(f"{RES}/disease_module_hubs.csv", index=False)
print(f"\nhub genes in significant modules (|r_NAS|>=0.5): {len(hub_union)}")
json.dump(dict(n_modules=int(lab.nunique()),
               n_sig_modules=int(len(sig)),
               hub_genes=hub_union[:100]),
          open(f"{RES}/module_summary.json", "w"), indent=1)
