# -*- coding: utf-8 -*-
"""Step 8: final figures - target gene boxplots + volcano + KEGG ORA bar."""
import gzip, json, re
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False
D = "D:/zcode-workspace/mash_research"
GEO, FIG = f"{D}/data/geo", f"{D}/results/figures"

# reload metadata + lognorm
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
grp = meta[[c for c in meta.columns if "group" in c][0]]
grp_groups = {"Normal": grp[grp.str.contains("control", case=False)].index,
              "NAFL": grp[grp == "NAFL"].index,
              "NASH F0-F1": grp[grp == "NASH_F0-F1"].index,
              "NASH F2": grp[grp == "NASH_F2"].index,
              "NASH F3-F4": grp[grp.isin(["NASH_F3", "NASH_F4"])].index}
logn = pd.read_csv(f"{GEO}/lognorm_matrix.csv.gz", index_col=0)

fig, axes = plt.subplots(2, 4, figsize=(16, 7))
targets = ["NR1H4", "THRB", "ACACA", "ACACB", "FASN", "CYP7A1", "COL1A1", "TNF"]
roles = ["FXR(主靶点)", "THR-β(靶点)", "ACC1(靶点)", "ACC2(靶点)",
         "FASN(对照↑)", "CYP7A1(FXR下游)", "COL1A1(纤维化)", "TNF(炎症)"]
for ax, g, rl in zip(axes.flat, targets, roles):
    if g not in logn.index:
        ax.set_visible(False); continue
    data, labels = [], []
    for name, ids in grp_groups.items():
        v = logn.loc[g, [i for i in ids if i in logn.columns]]
        data.append(v.values); labels.append(f"{name}\n(n={len(v)})")
    bp = ax.boxplot(data, labels=labels, patch_artist=True,
                    boxprops=dict(facecolor="#dbeafe"), medianprops=dict(color="#1d4ed8"))
    ax.set_title(f"{g} — {rl}", fontsize=10)
    ax.tick_params(axis="x", labelsize=6.5)
    ax.set_ylabel("log2 norm counts")
plt.suptitle("GSE135251 (n=216): 靶点基因在不同肝病理分组中的表达", fontsize=13)
plt.tight_layout(); plt.savefig(f"{FIG}/target_genes_boxplots.png", dpi=170)
print("saved target_genes_boxplots.png")

# volcano
res = pd.read_csv(f"{GEO}/deg_NASH_vs_Normal.csv", index_col=0)
fig, ax = plt.subplots(figsize=(8, 6.5))
sig = (res.padj < 0.05) & (res.log2FC.abs() > 0.5)
ax.scatter(res.log2FC[~sig], -np.log10(res.p.clip(lower=1e-300))[~sig],
           s=3, alpha=0.25, c="#94a3b8")
up = res.log2FC > 0.5; dn = res.log2FC < -0.5
ax.scatter(res.log2FC[sig & up], -np.log10(res.p.clip(lower=1e-300))[sig & up],
           s=3, alpha=0.5, c="#dc2626", label=f"up {int((sig&up).sum())}")
ax.scatter(res.log2FC[sig & dn], -np.log10(res.p.clip(lower=1e-300))[sig & dn],
           s=3, alpha=0.5, c="#2563eb", label=f"down {int((sig&dn).sum())}")
for g in ["NR1H4", "THRB", "ACACA", "ACACB", "FASN", "CYP7A1", "COL1A1"]:
    if g in res.index:
        ax.annotate(g, (res.loc[g, "log2FC"], -np.log10(res.loc[g, "p"])),
                    fontsize=9, fontweight="bold",
                    xytext=(4, 4), textcoords="offset points")
ax.axhline(-np.log10(0.05), ls="--", lw=0.7, c="gray")
ax.axvline(0.5, ls="--", lw=0.7, c="gray"); ax.axvline(-0.5, ls="--", lw=0.7, c="gray")
ax.set_xlabel("log2FC (NASH vs Normal)"); ax.set_ylabel("-log10 p")
ax.set_title(f"MASH vs Normal肝组织DEG火山图 (GSE135251)\nDEG总数 {int(sig.sum())}")
ax.legend(frameon=False)
plt.tight_layout(); plt.savefig(f"{FIG}/volcano_nash_vs_normal.png", dpi=170)
print("saved volcano_nash_vs_normal.png")

# KEGG ORA bar (with canonical names for top hits)
KEGG_NAMES = {"hsa04976": "Bile secretion", "hsa05171": "Measles signaling",
              "hsa04978": "Mineral absorption", "hsa04382": "Adherens junction",
              "hsa04540": "Gap junction", "hsa04022": "cGMP-PKG signaling",
              "hsa04371": "Apelin signaling", "hsa02010": "ABC transporters",
              "hsa05222": "Small cell lung cancer", "hsa03273": "Type III secretion",
              "hsa04820": "Cytoskeleton in muscle contraction", "hsa05218": "Melanoma",
              "hsa00600": "Sphingolipid metabolism", "hsa00430": "Taurine & hypotaurine metabolism",
              "hsa04924": "Cortisol synthesis & secretion"}
ora = pd.read_csv(f"{D}/results/tables/kegg_ora_top25.csv").head(15)
ora["label"] = ora["pathway"].map(lambda p: KEGG_NAMES.get(p, p))
fig, ax = plt.subplots(figsize=(8.5, 5.5))
ax.barh(range(len(ora)), -np.log10(ora["p"]), color="#0d9488")
ax.set_yticks(range(len(ora))); ax.set_yticklabels(ora["label"][::-1], fontsize=8.5)
ax.set_xlabel("-log10 (hypergeometric p)")
ax.set_title("KEGG通路富集 (NASH vs Normal DEGs, GSE135251)")
plt.tight_layout(); plt.savefig(f"{FIG}/kegg_ora.png", dpi=170)
print("saved kegg_ora.png")
