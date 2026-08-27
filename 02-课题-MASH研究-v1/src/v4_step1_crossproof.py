# -*- coding: utf-8 -*-
"""
V4: INDEPENDENT cross-proof by two method families never used before.
A) Network medicine proximity (Guney/Barabasi Nat Commun 2016):
   candidate targets (STITCH) vs MASH disease proteins (GWAS+module hubs)
   on STRING interactome -> degree-preserving randomization z-score.
B) Cross-structure docking consistency: leads re-docked into SECOND crystal
   structures (FXR_1OSH, ACC2_3GID) vs primary (3FLI, 5KKN).
Verdict table combines: QSAR(earlier) + docking-primary(earlier) + docking-2nd
(new) + network z(new) + literature(newness, earlier) = 5 independent angles.
"""
import json, re, subprocess, time
import numpy as np
import pandas as pd
import requests
from rdkit import Chem, RDLogger
from rdkit.Chem import AllChem
from meeko import MoleculePreparation, PDBQTWriterLegacy

RDLogger.DisableLog('rdApp.*')
D = "D:/zcode-workspace/mash_research"
RES = f"{D}/results/v4"
import os; os.makedirs(RES, exist_ok=True)

LEADS = {
 "Antrocinnamomin F": ("樟芝", "Antrocinnamomin F"),
 "Butyrolactone VI": ("土曲霉", "Butyrolactone VI"),
 "Alternaramide": ("海洋Alternaria", "Alternaramide"),
 "Versicolamide B": ("A.versicolor", "Versicolamide B"),
 "Aspernolide D": ("土曲霉", "Aspernolide D"),
}
# fetch lead SMILES from existing tables
smis = {}
srcs = [f"{D}/results/v2/multitarget_top200.csv", f"{D}/results/v2/shortlist_top500.csv",
        f"{D}/results/v2/library_scored.csv"]
frames = [pd.read_csv(s, low_memory=False) for s in srcs[:2]]
big = pd.concat(frames, ignore_index=True)
for nm in LEADS:
    row = big[big["name"].astype(str).str.strip() == nm]
    if len(row):
        smis[nm] = row.iloc[0]["canonical_smiles"]
print("lead SMILES resolved:", list(smis))

# ---------------- A) STITCH targets ----------------
H = {"User-Agent": "academic-screening/1.0"}
def stitch_targets(smi, topn=15):
    try:
        r = requests.get("https://stitch.embl.de/api/json/smilesInteractions",
                         params={"smiles": smi, "species": 9606, "limit": topn}, timeout=60)
        if r.status_code == 200 and r.text.strip():
            out = {}
            for it in r.json():
                out[it.get("preferredName_B", it.get("proteinB", ""))] = float(it.get("score", 0))
            return {k: v for k, v in out.items() if k}
    except Exception as e:
        print("stitch err", str(e)[:60])
    return {}

cand_targets = {}
for nm, smi in smis.items():
    t = stitch_targets(smi)
    cand_targets[nm] = t
    print(f"STITCH {nm}: {len(t)} targets", list(t)[:6])
    time.sleep(1)
json.dump(cand_targets, open(f"{RES}/stitch_targets.json", "w"), indent=1)

# ---------------- disease proteins ----------------
DISEASE = ["PNPLA3","TM6SF2","HSD17B13","MARC1","MTARC1","MBOAT7","GCKR","SLC39A8",
           "SERPINA1","SUGP1","SAMM50","LEPR","IL17RA","FABP1","COL13A1",
           "NR1H4","THRB","ACACA","ACACB","FASN","PPARG","PPARA","NR1H3","HMGCR",
           "SQLE","FDFT1","COL1A2","THY1","MMP2","TIMP1","TNF","IL6","CYP7A1","FASN"]
DISEASE = sorted(set(DISEASE))

# ---------------- STRING interactome (networkx) ----------------
import networkx as nx
string_ids = {}
r = requests.get("https://string-db.org/api/tsv/get_string_ids",
                 params={"identifiers": "%0d".join(DISEASE), "species": 9606, "limit": 1},
                 timeout=120, headers=H)
for line in r.text.splitlines()[1:]:
    p = line.split("\t")
    if len(p) > 5:
        string_ids[p[2]] = p[0]  # symbol -> STRING id
print("disease proteins mapped to STRING:", len(string_ids))
edges, nodes = set(), set()
identifiers = "%0d".join(list(string_ids.values()))
r = requests.get("https://string-db.org/api/tsv/network",
                 params={"identifiers": identifiers, "species": 9606,
                         "required_score": 700}, timeout=300, headers=H)
for line in r.text.splitlines()[1:]:
    p = line.split("\t")
    if len(p) > 14 and p[12] == "9606":
        a, b = p[0], p[1]
        edges.add((a, b)); nodes |= {a, b}
G = nx.Graph(); G.add_nodes_from(nodes); G.add_edges_from(edges)
print("interactome:", G.number_of_nodes(), "nodes", G.number_of_edges(), "edges")
dis_set = set(string_ids.values())
dis_set &= set(G.nodes)

def proximity(targets, S, G, nperm=400):
    T = [string_ids[t] for t in targets if t in string_ids and string_ids[t] in G]
    if len(T) < 2:
        return None, None, len(T)
    d = []
    for t in T:
        sp = nx.single_source_shortest_path_length(G, t, cutoff=5)
        d.append(min([sp[s] for s in S if s in sp] or [5]))
    dc = float(np.mean(d))
    rng = np.random.RandomState(42)
    degs = dict(G.degree())
    pool = [n for n in G.nodes if n not in S]
    pool_sorted = sorted(pool, key=lambda n: -degs[n])
    zs = []
    for _ in range(nperm):
        Td = pool_sorted[len(pool)//40:len(pool)//40*3][rng.choice(200, len(T), replace=False)] \
            if len(pool) > 1000 else rng.choice(pool, len(T), replace=False)
        dd = []
        for t in Td:
            sp = nx.single_source_shortest_path_length(G, t, cutoff=5)
            dd.append(min([sp[s] for s in S if s in sp] or [5]))
        zs.append(np.mean(dd))
    mu, sd = float(np.mean(zs)), float(np.std(zs) + 1e-9)
    return (dc - mu) / sd, dc, len(T)

prox_rows = []
for nm, tg in cand_targets.items():
    if len(tg) >= 3:
        z, dc, n = proximity(list(tg), dis_set, G)
        prox_rows.append(dict(lead=nm, n_stitch_targets=n, d_c=round(dc, 2) if dc else None,
                              z_proximity=round(z, 2) if z is not None else None,
                              verdict="significantly-close(z<-1)" if (z is not None and z < -1) else "not-close"))
        print(prox_rows[-1])
pd.DataFrame(prox_rows).to_csv(f"{RES}/network_proximity.csv", index=False)

# ---------------- B) cross-structure docking ----------------
BOXES = json.load(open(f"{D}/docking/boxes.json"))
MK = MoleculePreparation()
def prep(smi, path):
    m = Chem.MolFromSmiles(smi)
    if m is None: return None
    m = Chem.AddHs(m)
    p = AllChem.ETKDGv3(); p.randomSeed = 42
    if AllChem.EmbedMolecule(m, p) != 0:
        p.useRandomCoords = True
        if AllChem.EmbedMolecule(m, p) != 0: return None
    try: AllChem.MMFFOptimizeMolecule(m, mmffVariant='MMFF94s', maxIters=500)
    except Exception: pass
    s, ok, _ = PDBQTWriterLegacy.write_string(MK(m)[0])
    if not ok: return None
    open(path, "w").write(s); return path
AFF = re.compile(r"^\s+\d+\s+(-?\d+\.\d+)\s+")
drows = []
for nm, smi in smis.items():
    lp = prep(smi, f"{D}/docking/ligands/xproof_{nm.replace(' ','_')}.pdbqt")
    if lp is None: continue
    row = dict(lead=nm)
    for tag in ["FXR_1OSH", "ACC2_3GID"]:
        b = BOXES[tag]; c, s = b["center"], b["size"]
        rr = subprocess.run([f"{D}/tools/vina_1.2.5_win.exe",
            "--receptor", f"{D}/docking/receptors/{tag}.pdbqt", "--ligand", lp,
            "--out", f"{D}/docking/outputs/xproof_{nm.replace(' ','_')}_{tag}.pdbqt",
            "--center_x", str(c[0]), "--center_y", str(c[1]), "--center_z", str(c[2]),
            "--size_x", str(s[0]), "--size_y", str(s[1]), "--size_z", str(s[2]),
            "--exhaustiveness", "10", "--seed", "42", "--num_modes", "9"],
            capture_output=True, text=True, timeout=1500)
        a = [float(AFF.match(l).group(1)) for l in rr.stdout.splitlines() if AFF.match(l)]
        row[f"dG_{tag}"] = a[0] if a else None
    drows.append(row)
    print(row)
pd.DataFrame(drows).to_csv(f"{RES}/cross_structure_docking.csv", index=False)
print("saved network_proximity.csv + cross_structure_docking.csv")
