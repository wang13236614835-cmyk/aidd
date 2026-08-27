# -*- coding: utf-8 -*-
"""V3 Step2b: network proximity on KEGG co-pathway functional network
(STRING API inaccessible from this env - honest substitution, declared)."""
import json, time
import numpy as np
import pandas as pd
import requests as rq
from scipy import stats

D = "D:/zcode-workspace/mash_research"
RES = f"{D}/results/v3"
import networkx as nx

GENETIC = ["PNPLA3","TM6SF2","HSD17B13","MARC1","SLC39A8","SERPINA1","GCKR","MBOAT7"]
hubs = pd.read_csv(f"{D}/results/v2/disease_module_hubs.csv")
DISEASE = sorted(set(hubs["gene"]) | set(GENETIC))
AXES = {
 "NR": ["NR1H4","THRB","PPARG","NR1H3"],
 "LIPO": ["ACACA","ACACB","FASN","DGAT2","SCD","HMGCR","SQLE","FDFT1"],
 "INFL": ["TLR4","MYD88","NFKB1","RELA","TNF","IL6"],
 "FIB": ["COL1A1","COL3A1","ACTA2","TIMP1","MMP2","THY1"],
}
allg = sorted(set(DISEASE) | {g for v in AXES.values() for g in v})

# entrez<->symbol via eutils (batch), then kegg link pathways
import time
H = {"User-Agent": "academic-mash/1.0"}
def jget(url, params, tries=5):
    for i in range(tries):
        try:
            r = rq.get(url, params=params, headers=H, timeout=90)
            if r.status_code == 200 and r.text.strip().startswith("{"):
                return r.json()
        except Exception:
            pass
        time.sleep(2 * (i + 1))
    raise RuntimeError("eutils failed")
res = jget("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
           {"db": "gene", "term": " OR ".join(f"{g}[Gene Name]" for g in allg),
            "retmax": 500, "retmode": "json"})
uids = res["esearchresult"]["idlist"]
sm_r = {"result": {"uids": []}}
for k in range(0, len(uids), 80):
    part = jget("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi",
                {"db": "gene", "id": ",".join(uids[k:k+80]), "retmode": "json"})
    sm_r["result"]["uids"] += part["result"]["uids"]
    time.sleep(0.5)
sm = sm_r
e2s, s2e = {}, {}
for uid in sm["result"]["uids"]:
    nm = sm["result"][uid].get("name", "")
    if nm in allg:
        e2s[uid] = nm; s2e[nm] = uid
print("mapped", len(s2e), "/", len(allg))

# pathway membership from KEGG (link file cached earlier)
import os
lp = f"{D}/data/geo/kegg_link_cache.tsv"
if not os.path.exists(lp):
    import urllib.request
    txt = urllib.request.urlopen("https://rest.kegg.jp/link/pathway/hsa", timeout=180).read().decode()
    open(lp, "w").write(txt)
pw = {}
for line in open(lp):
    g, p = line.split()
    pw.setdefault(s2e.get(g.split(":")[1], ""), set()).add(p)
pw.pop("", None)

G = nx.Graph()
G.add_nodes_from(s2e.values())
for a in s2e.values():
    for b in s2e.values():
        if a < b and pw.get(a, set()) & pw.get(b, set()):
            G.add_edge(a, b)
print("KEGG co-pathway network:", G.number_of_nodes(), "nodes", G.number_of_edges(), "edges")
Dn = [s2e[g] for g in DISEASE if g in s2e]

def dclose(tset):
    ds = []
    for t in tset:
        try:
            ds.append(min(nx.shortest_path_length(G, t, s) for s in Dn))
        except nx.NetworkXNoPath:
            ds.append(10)
    return np.mean(ds)

rng = np.random.RandomState(42)
rows = []
for name, genes in list(AXES.items()) + [{"二联组合靶集": sum(AXES.values(), [])}]:
    T = [s2e[g] for g in genes if g in s2e]
    if not T:
        continue
    obs = dclose(T)
    pool = list(G.nodes())
    degs = np.array([G.degree(n) + 1 for n in pool], float)
    w = degs / degs.sum()
    null = [dclose(list(np.random.choice(pool, size=len(T), replace=False, p=w))) for _ in range(300)]
    mu, sd = np.mean(null), np.std(null)
    z = (obs - mu) / sd if sd > 0 else 0
    rows.append(dict(target_set=name, n=len(T), d_close=round(obs, 2),
                     null=round(mu, 2), z=round(z, 2),
                     verdict="显著邻近(z<-1.96)" if z < -1.96 else ("倾向邻近" if z < -0.5 else "不显著")))
    print(rows[-1])
pd.DataFrame(rows).to_csv(f"{RES}/network_proximity_kegg.csv", index=False)
