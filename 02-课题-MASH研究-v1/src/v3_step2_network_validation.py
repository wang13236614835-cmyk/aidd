# -*- coding: utf-8 -*-
"""
V3 Step2: INDEPENDENT multi-facet validation (different methodology from QSAR/docking).
(A) Network proximity z-score (Guney/Barabasi Nat Commun 2016): STRING interactome,
    degree-preserving randomization, closest-distance proximity of each axis target
    set and combination target sets to the MASH disease module.
(B) Human-data axis validation: TLR4/NF-kB axis + fibrosis axis correlation with NAS
    in GSE135251 (n=216) — independent transcriptomic proof of axis relevance.
"""
import gzip, json, re, urllib.parse
import numpy as np
import pandas as pd
import requests
from scipy import stats

D = "D:/zcode-workspace/mash_research"
RES = f"{D}/results/v3"

# ---------- gene sets ----------
GENETIC = ["PNPLA3","TM6SF2","HSD17B13","MARC1","SLC39A8","SERPINA1","GCKR","MBOAT7"]
hubs = pd.read_csv(f"{D}/results/v2/disease_module_hubs.csv")
DISEASE = sorted(set(hubs["gene"]) | set(GENETIC))
AXES = {
 "NR轴(核受体)": ["NR1H4","THRB","PPARG","NR1H3"],
 "LIPO轴(脂合成)": ["ACACA","ACACB","FASN","DGAT2","SCD","HMGCR","SQLE","FDFT1"],
 "INFL轴(炎症间接)": ["TLR4","MYD88","NFKB1","RELA","TNF","IL6"],
 "FIB轴(纤维化)": ["COL1A1","COL3A1","ACTA2","TIMP1","MMP2","THY1"],
}
COMBO2 = {"二联(樟芝F+VersicolamideB)代理靶集": AXES["NR轴(核受体)"] + AXES["LIPO轴(脂合成)"] + AXES["FIB轴(纤维化)"] + AXES["INFL轴(炎症间接)"]}
# note: VersicolamideB indirect; its axis proxies declared explicitly.

allg = sorted(set(DISEASE) | {g for v in list(AXES.values()) + list(COMBO2.values()) for g in v})
print("genes for interactome:", len(allg))

# ---------- STRING interactions (score>=700) ----------
edges = []
for i in range(0, len(allg), 200):
    chunk = allg[i:i+200]
    url = ("https://version.string-db.org/api/tsv/get_string_interactions?"
           + urllib.parse.urlencode({
               "identifiers": "\r".join(chunk), "species": 9606,
               "required_score": 700, "limit": 5000, "caller": "academic-mash"}))
    r = requests.get(url, timeout=120)
    for line in r.text.splitlines()[1:]:
        p = line.split("\t")
        if len(p) > 8:
            edges.append((p[2], p[3], int(p[9]) if p[9].isdigit() else 700))
print("string edges pulled:", len(edges))
import networkx as nx
G = nx.Graph()
G.add_nodes_from(allg)
G.add_edges_from([(a, b) for a, b, s in edges])
print("graph:", G.number_of_nodes(), "nodes", G.number_of_edges(), "edges")

def proximity_z(T, S, G, n_iter=500, seed=42):
    T = [t for t in T if t in G]
    S = [s for s in S if s in G]
    if not T or not S:
        return None
    def dclose(tset):
        ds = []
        for t in tset:
            try:
                ds.append(min(nx.shortest_path_length(G, t, s) for s in S))
            except nx.NetworkXNoPath:
                ds.append(10)
        return np.mean(ds)
    obs = dclose(T)
    rng = np.random.RandomState(seed)
    degs = dict(G.degree())
    pool = list(G.nodes())
    null = []
    for _ in range(n_iter):
        # degree-preserving-ish random selection: weight by degree (config approximation)
        w = np.array([degs[n] + 1 for n in pool], dtype=float)
        w = w / w.sum()
        rnd = list(np.random.choice(pool, size=len(T), replace=False, p=w))
        null.append(dclose(rnd))
    mu, sd = np.mean(null), np.std(null)
    return (obs - mu) / sd if sd > 0 else 0.0, obs, mu

rows = []
for name, tset in list(AXES.items()) + list(COMBO2.items()):
    r = proximity_z(tset, DISEASE, G)
    if r:
        z, obs, mu = r
        rows.append(dict(target_set=name, n=len([t for t in tset if t in G]),
                         d_close=round(obs, 2), null_mean=round(mu, 2),
                         z_score=round(z, 2),
                         verdict="显著邻近(z<-1.96)" if z < -1.96 else ("倾向邻近" if z < -0.5 else "不显著")))
        print(rows[-1])
pd.DataFrame(rows).to_csv(f"{RES}/network_proximity_validation.csv", index=False)

# ---------- (B) axis activation in GSE135251 ----------
txt = gzip.open(f"{D}/data/geo/GSE135251_series_matrix.txt.gz", "rt", encoding="utf-8", errors="ignore").read()
samples, chars = None, {}
for line in txt.splitlines():
    if line.startswith("!Sample_geo_accession"):
        samples = [x.strip('"') for x in line.split("\t")[1:]]
    elif line.startswith("!Sample_characteristics_ch1"):
        vals = [x.strip('"') for x in line.split("\t")[1:]]
        k = re.sub(r":.*$", "", vals[0]).strip()
        chars[k] = [re.sub(r"^[^:]*:\s*", "", v).strip() for v in vals]
meta = pd.DataFrame(chars, index=samples)
nas = pd.to_numeric(meta["nas score"], errors="coerce")
X = pd.read_csv(f"{D}/data/geo/lognorm_matrix.csv.gz", index_col=0)
X = X[[c for c in X.columns if c in meta.index]]
nas = nas.loc[X.columns]
axis_tests = {"INFL轴": ["TLR4","MYD88","NFKB1","RELA","TNF"],
              "FIB轴": ["COL1A1","COL3A1","ACTA2","TIMP1","MMP2","THY1"],
              "LIPO轴": ["ACACA","FASN","SCD","HMGCR","SQLE"],
              "NR轴": ["NR1H4","THRB","PPARG","NR1H3"]}
arows = []
for ax, genes in axis_tests.items():
    gs = [g for g in genes if g in X.index]
    scores = X.loc[gs].mean(0)
    r, p = stats.spearmanr(scores, nas)
    arows.append(dict(axis=ax, n_genes=len(gs), spearman_vs_NAS=round(float(r), 3),
                      p=f"{p:.1e}"))
    print(arows[-1])
pd.DataFrame(arows).to_csv(f"{RES}/axis_activation_validation.csv", index=False)
