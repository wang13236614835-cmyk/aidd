# -*- coding: utf-8 -*-
"""
Step 9: OBSCURE-HERB exploration (user-directed innovation search).
Build a compound library for 7 less-known herbs with putative MASH relevance
(evidence verified separately by research agents), resolve REAL structures via
PubChem, ADMET-filter, then run the PRODUCTION Bayesian GNN (FXR) with
three-tier confidence annotation. Docking of top hits follows in step10.
Selection criteria (user): credible + not common knowledge + no approved drug.
"""
import json, math, os, time, urllib.parse
import numpy as np
import pandas as pd
import requests
from rdkit import Chem, RDLogger
from rdkit.Chem import Descriptors, Crippen, Lipinski
from rdkit.Chem import FilterCatalog
import torch
import torch.nn.functional as F
from torch_geometric.data import Data
from torch_geometric.loader import DataLoader
from torch_geometric.nn import GINConv, global_mean_pool

RDLogger.DisableLog('rdApp.*')
D = "D:/zcode-workspace/mash_research"
OUT = f"{D}/data/tcm"

# ---------------- obscure herb compound lists ----------------
HERBS = {
 "Antrodia cinnamomea(樟芝)": [
  ("antcin A",""),("antcin B",""),("antcin C",""),("antcin H",""),("antcin K",""),
  ("antrodin A",""),("antrodin B",""),("antrodin C",""),
  ("eburicoic acid",""),("dehydroeburicoic acid",""),("sulphurenic acid",""),
  ("zhankuic acid A","UNCERTAIN"),("methyl antcinate K","UNCERTAIN"),
  ("antcin I",""),("antcin L","UNCERTAIN")],
 "Inonotus obliquus(桦褐孔菌)": [
  ("inotodiol",""),("trametenolic acid",""),("betulinic acid","note:mid-known"),
  ("betulin",""),("lanosterol",""),("inonotsuside A","UNCERTAIN"),
  ("3beta-hydroxylanosta-8,24-dien-21-al","UNCERTAIN"),("trametenic acid","UNCERTAIN")],
 "Swertia spp.(当药/青叶胆/藏茵陈)": [
  ("swertiamarin",""),("sweroside",""),("amarogentin",""),("amaroswerin",""),
  ("gentiopicroside",""),("bellidifolin",""),("demethylbellidifolin","UNCERTAIN"),
  ("methylswertianin",""),("decussatin","UNCERTAIN"),("swertianolin",""),
  ("mangiferin","note:mid-known"),("1,5,8-trihydroxy-3-methoxyxanthone","UNCERTAIN")],
 "Ampelopsis grossedentata(藤茶)": [
  ("dihydromyricetin","flag:flavanonol-skeleton"),
  ("dihydroquercetin","flag:flavanonol"),("dihydrokaempferol","flag:flavanonol")],
 "Phyllanthus niruri(叶下珠)": [
  ("phyllanthin",""),("hypophyllanthin",""),("nirtetralin",""),("phyltetralin",""),
  ("niranthin",""),("norsecurinine",""),
  ("isointetralin","UNCERTAIN"),("lintetralin","UNCERTAIN")],
 "Centella asiatica(积雪草)": [
  ("asiatic acid",""),("madecassic acid",""),("asiaticoside","glycoside-MW"),
  ("madecassoside","glycoside-MW"),("terminolic acid","UNCERTAIN")],
 "Ilex kudingcha(苦丁茶)": [
  ("ursolic acid","note:mid-known"),("kudinogenin A","UNCERTAIN"),
  ("kudinoside A","glycoside-MW"),("ilexgenin A","UNCERTAIN"),
  ("rotundic acid","UNCERTAIN"),("ilexolic acid A","UNCERTAIN")],
}

HEADERS = {"User-Agent": "academic-virtual-screening/1.0 (university research project)"}
PUG = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name"

def pubchem_lookup(name):
    q = urllib.parse.quote(name)
    url = f"{PUG}/{q}/property/IsomericSMILES,MolecularFormula,MolecularWeight/JSON"
    last = None
    for att in range(5):
        try:
            r = requests.get(url, timeout=30, headers=HEADERS)
            last = r.status_code
            if r.status_code == 200 and "PropertyTable" in r.text:
                p = r.json()["PropertyTable"]["Properties"][0]
                return (p.get("IsomericSMILES") or p.get("SMILES"),
                        p.get("MolecularFormula"), p.get("CID"))
            if r.status_code == 404:
                return None, None, None
            time.sleep(2.0 * (att + 1))
        except Exception:
            time.sleep(1.5 * (att + 1))
    return None, None, None

params = FilterCatalog.FilterCatalogParams()
for cat in [FilterCatalog.FilterCatalogParams.FilterCatalogs.PAINS_A,
            FilterCatalog.FilterCatalogParams.FilterCatalogs.PAINS_B,
            FilterCatalog.FilterCatalogParams.FilterCatalogs.PAINS_C]:
    params.AddCatalog(cat)
fcat = FilterCatalog.FilterCatalog(params)

rows = []
for herb, comps in HERBS.items():
    for name, note in comps:
        if note == "DROP":
            continue
        smi, formula, cid = pubchem_lookup(name)
        time.sleep(0.65)
        if smi is None:
            rows.append(dict(herb=herb, name=name, status="PUBCHEM_MISS", note=note))
            print(f"[miss] {herb} | {name}")
            continue
        m = Chem.MolFromSmiles(smi)
        if m is None:
            rows.append(dict(herb=herb, name=name, status="RDKIT_INVALID", note=note,
                             cid=cid, smiles=smi))
            continue
        mw, logp = Descriptors.MolWt(m), Crippen.MolLogP(m)
        hbd, hba = Lipinski.NumHDonors(m), Lipinski.NumHAcceptors(m)
        pains = [e.GetDescription() for e in fcat.GetMatches(m)]
        ok = (150 < mw < 500) and (logp < 5.5) and (hbd <= 5) and (hba <= 10)
        rows.append(dict(herb=herb, name=name, status="OK", note=note, cid=cid,
                         smiles=smi, formula=formula, mw=round(mw, 2),
                         logp=round(logp, 2), hbd=hbd, hba=hba,
                         admet_pass=bool(ok), pains=";".join(pains)))
        print(f"{herb} | {name} | CID {cid} | MW {mw:.0f} | pass {ok}"
              + (f" | PAINS {pains}" if pains else ""))

df = pd.DataFrame(rows)
df.to_csv(f"{OUT}/obscure_herbs_raw.csv", index=False)
lib = df[(df["status"] == "OK") & (df["admet_pass"] == True)].reset_index(drop=True)
lib.to_csv(f"{OUT}/obscure_herbs_filtered.csv", index=False)
print(f"\nobscure library: {len(lib)}/{len(df)} ADMET-passed across "
      f"{lib['herb'].nunique()} herbs")
print(lib.groupby("herb").size())

# ---------------- GNN inference with production ensemble ----------------
ATOM_FEATS = [
    ("atomic_num", list(range(1, 119))),
    ("degree", [0, 1, 2, 3, 4, 5]),
    ("formal_charge", [-2, -1, 0, 1, 2]),
    ("num_hs", [0, 1, 2, 3, 4]),
    ("hybridization", ["S", "SP", "SP2", "SP3", "SP3D", "SP3D2"]),
    ("aromatic", [0, 1]), ("in_ring", [0, 1]),
]
def onehot(val, choices):
    v = [0.0] * (len(choices) + 1)
    try: v[choices.index(val)] = 1.0
    except ValueError: v[-1] = 1.0
    return v
def mol_to_graph(smi):
    m = Chem.MolFromSmiles(smi)
    if m is None: return None
    xs = []
    for a in m.GetAtoms():
        xs.append(onehot(a.GetAtomicNum(), ATOM_FEATS[0][1])
                  + onehot(a.GetTotalDegree(), ATOM_FEATS[1][1])
                  + onehot(a.GetFormalCharge(), ATOM_FEATS[2][1])
                  + onehot(a.GetTotalNumHs(), ATOM_FEATS[3][1])
                  + onehot(str(a.GetHybridization()), ATOM_FEATS[4][1])
                  + [1.0 if a.GetIsAromatic() else 0.0, 1.0 if a.IsInRing() else 0.0])
    ei = []
    for b in m.GetBonds():
        i, j = b.GetBeginAtomIdx(), b.GetEndAtomIdx()
        ei += [[i, j], [j, i]]
    return Data(x=torch.tensor(xs, dtype=torch.float),
                edge_index=torch.tensor(ei, dtype=torch.long).t().contiguous())

class BayesianGIN(torch.nn.Module):
    def __init__(self, node_dim, hidden=96, layers=3, dropout=0.15):
        super().__init__()
        self.convs, self.bns = torch.nn.ModuleList(), torch.nn.ModuleList()
        for i in range(layers):
            nin = node_dim if i == 0 else hidden
            self.convs.append(GINConv(torch.nn.Sequential(
                torch.nn.Linear(nin, hidden), torch.nn.ReLU(),
                torch.nn.Linear(hidden, hidden))))
            self.bns.append(torch.nn.BatchNorm1d(hidden))
        self.dropout = dropout
        self.head_mu = torch.nn.Linear(hidden, 1)
        self.head_logvar = torch.nn.Linear(hidden, 1)
    def forward(self, x, edge_index, batch):
        for conv, bn in zip(self.convs, self.bns):
            x = F.relu(bn(conv(x, edge_index)))
            x = F.dropout(x, p=self.dropout, training=True)
        p = global_mean_pool(x, batch)
        return self.head_mu(p).squeeze(-1), self.head_logvar(p).squeeze(-1)

ckpt = torch.load(f"{D}/models/bgnn_production.pt", map_location="cpu")
ym, ys = ckpt["ym"], ckpt["ys"]
models = []
for sd in ckpt["models"]:
    m = BayesianGIN(ckpt["node_dim"]); m.load_state_dict(sd); m.eval()
    models.append(m)

graphs, keep = [], []
for i, r in lib.iterrows():
    g = mol_to_graph(r["smiles"])
    if g is not None:
        graphs.append(g); keep.append(i)
lib = lib.loc[keep].reset_index(drop=True)

loader = DataLoader(graphs, batch_size=128, shuffle=False)
T = 50
outs = []
for model in models:
    mus, ales = [], []
    with torch.no_grad():
        for d in loader:
            tm, ta = [], []
            for _ in range(T):
                mu, lv = model(d.x, d.edge_index, d.batch)
                tm.append(mu.numpy()); ta.append(np.exp(lv.numpy()))
            mus.append(np.stack(tm)); ales.append(np.stack(ta))
    mu_all = np.concatenate(mus, 1); al_all = np.concatenate(ales, 1)
    mean = mu_all.mean(0) * ys + ym
    var = mu_all.var(0) * ys ** 2 + al_all.mean(0) * ys ** 2
    outs.append((mean, np.sqrt(var)))
mu_np = np.mean([o[0] for o in outs], 0)
sd_np = np.sqrt(np.mean([o[1] ** 2 for o in outs], 0) + np.var([o[0] for o in outs], 0))
lib["fxr_mu_pIC50"] = mu_np.round(3)
lib["fxr_sigma"] = sd_np.round(3)

# leverage AD
ad_ref = json.load(open(f"{D}/data/chembl/ad_reference.json"))
FUNCS = dict(MolWt=Descriptors.MolWt, LogP=Crippen.MolLogP,
             TPSA=Chem.rdMolDescriptors.CalcTPSA, HBD=Lipinski.NumHDonors,
             HBA=Lipinski.NumHAcceptors, RotB=Lipinski.NumRotatableBonds,
             RingCount=Descriptors.RingCount, AromRings=Lipinski.NumAromaticRings,
             HeavyAtoms=Lipinski.HeavyAtomCount, Fsp3=Descriptors.FractionCSP3,
             MolMR=Crippen.MolMR)
tr_df = pd.read_csv(f"{D}/data/chembl/fxr_final_dataset.csv")
Xtr = np.array([[FUNCS[k](Chem.MolFromSmiles(s)) for k in ad_ref["desc_names"]]
                for s in tr_df["std_smiles"]])
from sklearn.decomposition import PCA
pca = PCA(n_components=ad_ref["pca_k"], svd_solver="full").fit(
    (Xtr - Xtr.mean(0)) / Xtr.std(0))
Ttr = pca.transform((Xtr - Xtr.mean(0)) / Xtr.std(0))
TtT_inv = np.linalg.inv(Ttr.T @ Ttr)
def leverage(smi):
    m = Chem.MolFromSmiles(smi)
    x = np.array([FUNCS[k](m) for k in ad_ref["desc_names"]])
    t = pca.transform(((x - Xtr.mean(0)) / Xtr.std(0)).reshape(1, -1))
    return float((t @ TtT_inv @ t.T)[0, 0])

h_crit = ad_ref["h_crit"]
lib["leverage_h"] = [round(leverage(s), 4) for s in lib["smiles"]]
lib["confidence_weight_w"] = (1 / (1 + sd_np)).round(3)
def tier(h, s):
    if not np.isfinite(h) or h > h_crit:
        return "OOD_warning(域外预警)"
    return "in_domain_high_conf(域内高置信)" if s <= 0.70 else "in_domain_low_conf(域内低置信)"
lib["tier"] = [tier(h, s) for h, s in zip(lib["leverage_h"], lib["fxr_sigma"])]
lib.to_csv(f"{D}/results/tables/obscure_herbs_predictions.csv", index=False)

print("\n=== tier distribution ===")
print(lib["tier"].value_counts().to_string())
print("\n=== TOP by mu (any tier, with tier shown) ===")
cols = ["herb", "name", "fxr_mu_pIC50", "fxr_sigma", "leverage_h", "tier", "note"]
print(lib.sort_values("fxr_mu_pIC50", ascending=False)[cols].head(20).to_string(index=False))
print("\n=== TOP within high-confidence tier ===")
hi = lib[lib["tier"].str.startswith("in_domain_high")]
print(hi.sort_values("fxr_mu_pIC50", ascending=False)[cols].head(15).to_string(index=False))
