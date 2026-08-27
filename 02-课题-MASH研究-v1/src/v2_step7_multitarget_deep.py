# -*- coding: utf-8 -*-
"""
V2 Step7: MULTI-TARGET deep analysis (SCI framing).
MASH polypharmacology: true multi-target ligands = predicted active (pAct>=6.5
~<=300nM) on >=3 of 11 liver targets. Rank by multi-target score
MTS = sum(pAct over active targets). PAINS removal, known-drug exclusion,
NP ADMET, obscure-source annotation; merge prior docking where available;
dock new top-8 (3 receptors) for triangulation.
"""
import json, re, subprocess
import numpy as np
import pandas as pd
from rdkit import Chem, RDLogger
from rdkit.Chem import Descriptors, Crippen, Lipinski, AllChem
from rdkit.Chem import rdFingerprintGenerator, FilterCatalog
from meeko import MoleculePreparation, PDBQTWriterLegacy

RDLogger.DisableLog('rdApp.*')
D = "D:/zcode-workspace/mash_research"
RES = f"{D}/results/v2"
TCOLS = None

L = pd.read_csv(f"{D}/results/v2/library_scored.csv", low_memory=False,
                usecols=lambda c: c in {"canonical_smiles", "name", "organism",
                                        "pathway", "top3_mean", "max_pAct"}
                or c.startswith("pAct_"))
tcols = [c for c in L.columns if c.startswith("pAct_") and c != "pAct_"]
print("targets:", [c[5:] for c in tcols], "| library:", len(L))

THR = 6.5
act = L[tcols].ge(THR)
L["n_active"] = act.sum(1)
MT = L[L.n_active >= 3].copy()
print("multi-target ligands (>=3 targets @pAct>=6.5):", len(MT))
MT["MTS"] = MT[tcols].where(MT[tcols].ge(THR)).sum(1).round(2)

# ADMET + PAINS + validity
params = FilterCatalog.FilterCatalogParams()
for cat in [FilterCatalog.FilterCatalogParams.FilterCatalogs.PAINS_A,
            FilterCatalog.FilterCatalogParams.FilterCatalogs.PAINS_B,
            FilterCatalog.FilterCatalogParams.FilterCatalogs.PAINS_C]:
    params.AddCatalog(cat)
fcat = FilterCatalog.FilterCatalog(params)
keep, pains_flag, mwv = [], [], []
for smi in MT.canonical_smiles:
    m = Chem.MolFromSmiles(smi)
    if m is None:
        keep.append(False); pains_flag.append(True); mwv.append(0); continue
    w = Descriptors.MolWt(m); lp = Crippen.MolLogP(m)
    hbd = Lipinski.NumHDonors(m); hba = Lipinski.NumHAcceptors(m)
    ok = 150 < w < 750 and lp <= 7.5 and hbd <= 6 and hba <= 12
    keep.append(ok)
    pains_flag.append(len(fcat.GetMatches(m)) > 0)
    mwv.append(w)
MT = MT.assign(admet_ok=keep, pains=pains_flag, mw2=mwv)
MT = MT[MT.admet_ok & ~MT.pains]
print("after ADMET+PAINS:", len(MT))

KNOWN = ["berberine","silybin","resveratrol","curcumin","quercetin","kaempferol",
         "lovastatin","simvastatin","rapamycin","tanshinone","artemisinin","paclitaxel"]
def known(n): return isinstance(n, str) and any(k in n.lower() for k in KNOWN)
MT = MT[~MT["name"].fillna("").map(known)]

FAMOUS = ["Glycyrrhiza","Panax","Salvia miltiorrhiza","Camellia sinensis","Ginkgo",
          "Coptis","Scutellaria","Bupleurum","Schisandra","Silybum","Curcuma","Taxus",
          "Artemisia annua","Ganoderma","Cinnamomum","Zingiber","Astragalus","Angelica",
          "Paeonia","Rheum","Epimedium","Lycium","Berberis","Sophora","Tripterygium",
          "Rosmarinus","Mentha","Perilla"]
def obscure(o):
    if not isinstance(o, str) or not o.strip(): return 0.0
    if any(f.lower() in o.lower() for f in FAMOUS): return 0.0
    s = 1.0
    if re.search(r"fung|mycota|Ascomycota|Basidiomycota|mold", o, re.I): s += 1.0
    if re.search(r"marine|sponge|coral|algae|seaweed|mangrove", o, re.I): s += 1.0
    if re.search(r"endophyt|actinomycet|Streptomycet", o, re.I): s += 0.5
    return s
MT["obscure"] = MT.organism.map(obscure)
MT["final"] = (MT.MTS * (1 + 0.05 * MT.obscure)).round(2)
MT = MT.sort_values("final", ascending=False)
MT.head(200).to_csv(f"{RES}/multitarget_top200.csv", index=False)

show = ["name", "organism", "n_active", "MTS", "final"]
print("\n=== TOP 25 MULTI-TARGET LIGANDS ===")
print(MT.head(25)[show].to_string(index=False, max_colwidth=55))

# active-target profile for top-12
top12 = MT.head(12)
prof_rows = []
for _, r in top12.iterrows():
    acts = {c[5:]: r[c] for c in tcols if r[c] >= THR}
    prof_rows.append(dict(name=r["name"], organism=str(r["organism"])[:40],
                          n=r["n_active"], MTS=r["MTS"], profile=";".join(
                              f"{k}:{v:.1f}" for k, v in sorted(acts.items(), key=lambda x: -x[1]))))
pd.DataFrame(prof_rows).to_csv(f"{RES}/multitarget_top12_profiles.csv", index=False)
for p in prof_rows[:8]:
    print(p["name"], "|", p["profile"])

# ---- dock NEW top-8 (skip ones already in shortlist_docking) ----
old = set(pd.read_csv(f"{RES}/shortlist_docking.csv")["name"].fillna("")) if \
    __import__("os").path.exists(f"{RES}/shortlist_docking.csv") else set()
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
for i, r in top12.head(8).iterrows():
    if isinstance(r["name"], str) and r["name"] in old:
        continue
    lp = prep(r.canonical_smiles, f"{D}/docking/ligands/mt{i}.pdbqt")
    if lp is None: continue
    out = {}
    for tag in ["FXR_3FLI", "ACC2_5KKN", "THRB_3GWS"]:
        b = BOXES[tag]; c, s = b["center"], b["size"]
        rr = subprocess.run([f"{D}/tools/vina_1.2.5_win.exe",
            "--receptor", f"{D}/docking/receptors/{tag}.pdbqt", "--ligand", lp,
            "--out", f"{D}/docking/outputs/mt{i}_{tag}.pdbqt",
            "--center_x", str(c[0]), "--center_y", str(c[1]), "--center_z", str(c[2]),
            "--size_x", str(s[0]), "--size_y", str(s[1]), "--size_z", str(s[2]),
            "--exhaustiveness", "8", "--seed", "42", "--num_modes", "9"],
            capture_output=True, text=True, timeout=1200)
        affs = [float(AFF.match(l).group(1)) for l in rr.stdout.splitlines() if AFF.match(l)]
        out[tag] = affs[0] if affs else None
    drows.append(dict(name=r["name"], organism=str(r["organism"])[:50], n_active=r["n_active"],
                      MTS=r["MTS"], dG_FXR=out["FXR_3FLI"], dG_ACC=out["ACC2_5KKN"],
                      dG_THRB=out["THRB_3GWS"]))
    print("[dock]", drows[-1])
pd.DataFrame(drows).to_csv(f"{RES}/multitarget_docking_new.csv", index=False)
print("done")
