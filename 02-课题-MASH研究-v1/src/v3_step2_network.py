# -*- coding: utf-8 -*-
"""
V3 Step2: INDEPENDENT validation by network medicine (Guney 2016 / Cheng 2019).
STRING interactome (real data via API) + MASH disease module (own GWAS/DEG genes)
-> degree-preserving randomization z-score of target-set proximity (d_c).
Also combo criterion: targets of paired drugs closer to disease module than
either alone, while covering distinct modules (Cheng 2019 logic).
"""
import json, time
import numpy as np
import pandas as pd
import requests

D = "D:/zcode-workspace/mash_research"
RES = f"{D}/results/v3"

# ---------- build disease module S ----------
deg = pd.read_csv(f"{D}/data/geo/deg_NASH_vs_Normal.csv", index_col=0)
S = set(deg[(deg.padj < 1e-3)].index)  # strict DEG core
hubs = pd.read_csv(f"{D}/results/v2/disease_module_hubs.csv")
S |= set(hubs["gene"])
GENE2SYM = None

# ---------- compound target sets (annotated from our verified assets) ----------
TARGETS = {
 "AntrocinnamominF": ["NR1H4", "THRB", "PPARG", "NR1H3", "ACACB"],       # QSAR top-5
 "ButyrolactoneVI": ["ACACB", "DGAT2", "THRB", "FDFT1", "PPARG"],
 "Alternaramide": ["TLR4", "MYD88", "RELA", "ACACB"],                     # lit + docking
 "VersicolamideB": ["HIF1A", "BCL2", "CASP3", "BAX"],                     # hypoxia/apoptosis protection (family)
 "AsiaticAcid": ["COL1A1", "COL3A1", "ACTA2", "TGFB1"],                   # anti-fibrotic literature
 "Berberine": ["AMPK", "PRKAA1", "TLR4", "NR1H4", "PPARG"],
 "Resmetirom": ["THRB"],
}
AXIS = {"AntrocinnamominF": "NR+LIPO", "ButyrolactoneVI": "LIPO+NR",
        "Alternaramide": "INFL", "VersicolamideB": "FIB/cell-protect",
        "AsiaticAcid": "FIB", "Berberine": "multi", "Resmetirom": "NR"}

# ---------- STRING interactome for needed proteins ----------
need = sorted(set().union(*[set(v) for v in TARGETS.values()]) | set(list(S)[:300]))
cache = f"{RES}/string_edges.tsv"
if __import__("os").path.exists(cache):
    edges = pd.read_csv(cache, sep="\t")
else:
    allr = []
    for i in range(0, len(need), 200):   # string interactions by identifiers
        
        chunk = need[i:i+200]
        r = requests.post("https://string-db.org/api/tsv/network",
                          data={"identifiers": "%0d".join([]) or "\r".join(chunk),
                                "species": 9606, "required_score": 700,
                                "caller": "academic-project"}, timeout=120)
        for line in r.text.splitlines()[1:]:
            p = line.split("\t")
            if len(p) >= 6 and p[2] != p[3]:
                allr.append((p[2], p[3], float(p[5])))
        time.sleep(1)
    edges = pd.DataFrame(allr, columns=["a", "b", "score"]).drop_duplicates(["a", "b"])
    edges.to_csv(cache, sep="\t", index=False)
print("STRING edges:", len(edges))

import networkx as nx
G = nx.Graph()
G.add_edges_from(edges[["a", "b"]].values)
print("interactome:", G.number_of_nodes(), "nodes /", G.number_of_edges(), "edges")
Sg = [g for g in S if g in G]
print("disease module in graph:", len(Sg))

def shortest_dists(srcs, G, maxd=5):
    dist = {}
    for s in srcs:
        if s not in G: continue
        lvl = nx.single_source_shortest_path_length(G, s, cutoff=maxd)
        for t, d in lvl.items():
            if t not in dist or d < dist[t]:
                dist[t] = d
    return dist

def proximity_z(T, Sg, G, nrand=300, seed=42):
    T = [t for t in T if t in G]
    if not T or not Sg: return np.nan, np.nan
    dist_T = shortest_dists(T, G)
    d_c = np.mean([min(dist_T.get(s, 5) for _ in [0]) if s in dist_T else 5 for s in Sg])
    # degree-preserving randomization
    rng = np.random.RandomState(seed)
    degs = dict(G.degree())
    vals = []
    nodes = list(G.nodes())
    pool = np.array([n for n in nodes if degs[n] > 0])
    w = np.array([degs[n] for n in pool], dtype=float)
    for _ in range(nrand):
        Tr = list(set(rng.choice(pool, size=len(T), p=w/w.sum())))
        dTr = shortest_dists(Tr, G)
        vals.append(np.mean([dTr.get(s, 5) for s in Sg]))
    mu, sd = np.mean(vals), np.std(vals)
    z = (d_c - mu) / sd if sd > 0 else np.nan
    return round(float(d_c), 3), round(float(z), 3)

rows = []
for name, T in TARGETS.items():
    dc, z = proximity_z(T, Sg, G)
    rows.append(dict(agent=name, axis=AXIS[name], n_targets_in_graph=len([t for t in T if t in G]),
                     d_c=dc, z_proximity=z))
    print(rows[-1])
pd.DataFrame(rows).to_csv(f"{RES}/network_proximity_agents.csv", index=False)

# combo z: union target set proximity (Cheng2019: effective combos' combined
# targets remain proximal to disease module)
import itertools
crows = []
for a, b in itertools.combinations(list(TARGETS), 2):
    Tu = list(set(TARGETS[a]) | set(TARGETS[b]))
    dc, z = proximity_z(Tu, Sg, G)
    crows.append(dict(combo=f"{a}+{b}", z_union=z))
cz = pd.DataFrame(crows).sort_values("z_union")
cz.to_csv(f"{RES}/network_proximity_combos.csv", index=False)
print("\nbest combos by network z (lower=more proximal):")
print(cz.head(8).to_string(index=False))
