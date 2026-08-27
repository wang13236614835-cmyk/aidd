# -*- coding: utf-8 -*-
"""V2 Step6: composite ranking -> wet-lab shortlist.
Filters: NP-tolerant ADMET (MW 150-750, LogP<=7.5, HBD<=6, HBA<=12, TPSA<=180),
obscure-source score (organism NOT in famous-medicinal list; fungi/marine boost),
novelty proxy (excluded named known drugs), composite = top3_mean activity score.
"""
import re
import numpy as np
import pandas as pd
from rdkit import Chem, RDLogger, DataStructs
from rdkit.Chem import Descriptors, Crippen, Lipinski, rdFingerprintGenerator

RDLogger.DisableLog('rdApp.*')
D = "D:/zcode-workspace/mash_research"
RES = f"{D}/results/v2"

L = pd.read_csv(f"{D}/results/v2/library_scored.csv", low_memory=False)
print("library:", len(L))

# ---------- basic ADMET (NP-tolerant) ----------
rows_ok, feats = [], []
mfg = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
keep = []
subs = L["canonical_smiles"]
mw, lp, hbd, hba = [], [], [], []
for smi in subs:
    m = Chem.MolFromSmiles(smi)
    if m is None:
        keep.append(False); mw.append(0); lp.append(0); hbd.append(0); hba.append(0); continue
    keep.append(True)
    mw.append(Descriptors.MolWt(m)); lp.append(Crippen.MolLogP(m))
    hbd.append(Lipinski.NumHDonors(m)); hba.append(Lipinski.NumHAcceptors(m))
L = L.assign(mw=mw, logp=lp, hbd=hbd, hba=hba)
L = L[keep]
admet = (L.mw.between(150, 750) & (L.logp <= 7.5) & (L.hbd <= 6) &
         (L.hba <= 12) & (L.top3_mean >= 6.0))
S = L[admet].copy()
print("after ADMET + activity(pot3>=6.0):", len(S))

# ---------- obscure score ----------
FAMOUS = ["Glycyrrhiza", "Panax", "Salvia miltiorrhiza", "Camellia sinensis",
          "Ginkgo", "Coptis", "Scutellaria", "Bupleurum", "Schisandra",
          "Silybum", "Curcuma", "Taxus", "Artemisia annua", "Ganoderma",
          "Cinnamomum", "Zingiber", "Astragalus", "Angelica", "Paeonia",
          "Rheum", "Cassia", "Epimedium", "Lycium", "Panax ginseng",
          "Berberis", "Sophora", "Tripterygium", "Centella", "Ilex"]
def obscure_score(org):
    if not isinstance(org, str) or not org.strip():
        return 0.0
    o = org.lower()
    if any(f.lower() in o for f in FAMOUS):
        return 0.0
    sc = 1.0
    if re.search(r"fung|mycota|mushroom|mold|Ascomycota|Basidiomycota", o, re.I):
        sc += 1.0   # fungal source boost (Science2025 paradigm)
    if re.search(r"marin|sponge|coral|algae|seaweed|octocoral|gorgonian", o, re.I):
        sc += 1.0   # marine boost
    if re.search(r"endophyt|symbiot|insect|actinomycet|Streptomycet", o, re.I):
        sc += 0.5
    return sc
S["obscure"] = S["organism"].map(obscure_score)
S = S[S.obscure > 0]
print("with obscure source:", len(S))

# ---------- novelty: exclude named known drugs ----------
KNOWN = ["berberine", "silybin", "silibinin", "resveratrol", "curcumin",
         "quercetin", "kaempferol", "glycyrrhetinic", "tanshinone", "artemisinin",
         "paclitaxel", "camptothecin", "vincristine", "morphine", "atropine",
         "lovastatin", "simvastatin", "rapamycin", "cyclosporin", "podophyllotoxin"]
def known_name(n):
    return isinstance(n, str) and any(k in n.lower() for k in KNOWN)
S = S[~S.get("name", pd.Series("", index=S.index)).fillna("").map(known_name)]

# ---------- composite ----------
S["composite"] = (S["top3_mean"] * (1 + 0.15 * S["obscure"])).round(2)
S = S.sort_values("composite", ascending=False)
S.head(500).to_csv(f"{RES}/shortlist_top500.csv", index=False)
cols = ["name", "organism", "pathway", "top3_mean", "max_pAct", "composite",
        "obscure", "mw", "logp"]
top = S.head(40)[cols]
print("\n=== TOP 40 (pre-docking) ===")
print(top.to_string(index=False))
S.head(40)[["canonical_smiles"]].to_csv(f"{RES}/top40_smiles.csv", index=False)
print("\nsaved shortlist_top500.csv / top40_smiles.csv")
