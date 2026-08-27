# -*- coding: utf-8 -*-
"""
V5 FINAL: unified transparent scoring -> TOP5 overall + TOP5 TCM.
FinalScore = 0.35*Act + 0.25*Dock + 0.20*Evidence + 0.10*Novelty + 0.10*Obtain
All coefficients explicit; every sub-score documented.
"""
import json, re, subprocess
import numpy as np
import pandas as pd
from rdkit import Chem, RDLogger
from rdkit.Chem import AllChem
from meeko import MoleculePreparation, PDBQTWriterLegacy

RDLogger.DisableLog('rdApp.*')
D = "D:/zcode-workspace/mash_research"
RES = f"{D}/results/v5"; import os; os.makedirs(RES, exist_ok=True)
BOXES = json.load(open(f"{D}/docking/boxes.json"))
MK = MoleculePreparation()

def prep(smi, path):
    m = Chem.MolFromSmiles(smi)
    if m is None: return None
    m = Chem.AddHs(m); p = AllChem.ETKDGv3(); p.randomSeed = 42
    if AllChem.EmbedMolecule(m, p) != 0:
        p.useRandomCoords = True
        if AllChem.EmbedMolecule(m, p) != 0: return None
    try: AllChem.MMFFOptimizeMolecule(m, mmffVariant='MMFF94s', maxIters=500)
    except Exception: pass
    s, ok, _ = PDBQTWriterLegacy.write_string(MK(m)[0])
    if not ok: return None
    open(path, 'w').write(s); return path

AFF = re.compile(r'^\s+\d+\s+(-?\d+\.\d+)\s+')
def dock_all(smi, key):
    lp = prep(smi, f"{D}/docking/ligands/{key}.pdbqt")
    if lp is None: return None, None
    out = {}
    for tag in ["FXR_3FLI", "ACC2_5KKN"]:
        b = BOXES[tag]; c, s = b["center"], b["size"]
        rr = subprocess.run([f"{D}/tools/vina_1.2.5_win.exe",
            "--receptor", f"{D}/docking/receptors/{tag}.pdbqt", "--ligand", lp,
            "--out", f"{D}/docking/outputs/{key}_{tag}.pdbqt",
            "--center_x", str(c[0]), "--center_y", str(c[1]), "--center_z", str(c[2]),
            "--size_x", str(s[0]), "--size_y", str(s[1]), "--size_z", str(s[2]),
            "--exhaustiveness", "8", "--seed", "42", "--num_modes", "9"],
            capture_output=True, text=True, timeout=1200)
        a = [float(AFF.match(l).group(1)) for l in rr.stdout.splitlines() if AFF.match(l)]
        out[tag] = a[0] if a else None
    return out["FXR_3FLI"], out["ACC2_5KKN"]

# ---------- dock TCM top components ----------
T = pd.read_csv(f"{D}/results/v4/tcm_multitarget_top300.csv")
# pick best named-or-not per herb, top 10 herbs, plus known asiatic acid
picks = []
seen = set()
for _, r in T.sort_values("MTS", ascending=False).iterrows():
    if r["tcm"] in seen: continue
    seen.add(r["tcm"]); picks.append(r)
    if len(picks) >= 10: break
rows = []
for i, r in enumerate(picks):
    fx, ac = dock_all(r["canonical_smiles"], f"tcmfinal{i}")
    rows.append(dict(pool="TCM", id=str(r["name"])[:40], herb=r["tcm"],
                     smiles=r["canonical_smiles"], MTS=float(r["MTS"]),
                     n_active=int(r["n_active"]), dG_FXR=fx, dG_ACC=ac))
    print(rows[-1])
pd.DataFrame(rows).to_csv(f"{RES}/tcm_final_docking.csv", index=False)

# ---------- unified candidate table (all docked assets) ----------
def C(pool, idd, MTS, fx, ac, ev, ev_note, nov, obt, obt_note):
    ds = [abs(x) for x in (fx, ac) if x is not None and x < 0]
    dockn = min(np.mean(ds) / 10.0, 1.0) if ds else 0.0
    act = min(MTS / 45.0, 1.0)
    return dict(pool=pool, id=idd, MTS=MTS, dG_FXR=fx, dG_ACC=ac,
                Act=round(act, 3), Dock=round(dockn, 3), Evidence=ev,
                Evidence_note=ev_note, Novelty=nov, Obtain=obt, Obtain_note=obt_note,
                FINAL=round(0.35*act + 0.25*dockn + 0.20*ev + 0.10*nov + 0.10*obt, 3))

cands = [
 C("ALL", "Antrocinnamomin F (樟芝)", 34.4, -8.01, -8.93, 1.0, "来源有NASH RCT(PMID 32657670)+AMPK/SREBP机制", 0.2, 1.0, "菌丝体+标样可购"),
 C("ALL", "Aspergillus terreus丁内酯(Aspernolide D族)", 35.6, -8.63, -8.97, 0.3, "纯计算(PKA抑制家族史)", 1.0, 0.7, "土曲霉发酵"),
 C("ALL", "07H239-A (内生真菌)", 7.39*3, -8.06, -9.00, 0.3, "纯计算(细胞毒家族史)", 1.0, 0.7, "菌种发酵"),
 C("ALL", "Alisiaquinol (海绵)", 7.39*3, -7.10, -9.85, 0.3, "纯计算(醌类隐患)", 1.0, 0.1, "深水海绵难"),
 C("ALL", "Aspergicin (内生曲霉)", 6.67*3, -8.09, -9.42, 0.3, "纯计算(结构撤稿争议)", 1.0, 0.7, "发酵"),
 C("ALL", "Alternaramide (海洋环肽)", 6.67*3, -6.51, -8.25, 0.5, "TLR4/NF-κB机制文献(身份需复核)", 1.0, 0.7, "发酵"),
]
for r in rows:
    fx, ac = r["dG_FXR"], r["dG_ACC"]
    C_ = C("TCM", f'{r["herb"]}:{r["id"]}', r["MTS"], fx, ac,
           0.7 if r["herb"] in ("积雪草",) else 0.5,
           "积雪草=直接HSC/TGFβ文献" if r["herb"] == "积雪草" else "中药传统肝效用+计算命中",
           0.8, 1.0, "药材商品可购")
    C_.update(pool="TCM", id=f'{r["herb"]} | {r["id"]}')
    cands.append(C_)
# add asiatic acid (previous asset, fibrosis axis)
cands.append(C("TCM", "积雪草 | asiatic acid", 0.0, None, None, 0.7,
               "TGFβ/Smad+HSC直接文献(PMID 35963324)", 0.8, 1.0, "商品可购"))

df = pd.DataFrame(cands).sort_values("FINAL", ascending=False)
df.to_csv(f"{RES}/final_unified_scores.csv", index=False)
print("\n===== TOP5 ALL-SOURCE =====")
print(df[df.pool == "ALL"].head(5)[["id", "Act", "Dock", "Evidence", "Novelty", "Obtain", "FINAL"]].to_string(index=False))
print("\n===== TOP5 TCM =====")
print(df[df.pool == "TCM"].head(5)[["id", "Act", "Dock", "Evidence", "Novelty", "Obtain", "FINAL"]].to_string(index=False))
