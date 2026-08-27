# -*- coding: utf-8 -*-
"""
Step 6c: FXR cross-docking of top CW-BCS compounds (2 crystal structures)
to corroborate GNN predictions + final figures (herb ranking bar, tier map).
"""
import json, os, re, subprocess
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from rdkit import Chem, RDLogger
from rdkit.Chem import AllChem
from meeko import MoleculePreparation, PDBQTWriterLegacy

RDLogger.DisableLog('rdApp.*')
D = "D:/zcode-workspace/mash_research"
VINA = f"{D}/tools/vina_1.2.5_win.exe"
BOXES = json.load(open(f"{D}/docking/boxes.json"))
LIGD, OUTD = f"{D}/docking/ligands", f"{D}/docking/outputs"

MK = MoleculePreparation()
def embed_3d(smi, seed=42):
    m = Chem.MolFromSmiles(smi)
    if m is None: return None
    m = Chem.AddHs(m)
    p = AllChem.ETKDGv3(); p.randomSeed = seed
    if AllChem.EmbedMolecule(m, p) != 0:
        p.useRandomCoords = True
        if AllChem.EmbedMolecule(m, p) != 0: return None
    try: AllChem.MMFFOptimizeMolecule(m, mmffVariant='MMFF94s', maxIters=500)
    except Exception:
        try: AllChem.UFFOptimizeMolecule(m, maxIters=500)
        except Exception: pass
    return m
def to_pdbqt(mol, path):
    setups = MK(mol)
    s, ok, err = PDBQTWriterLegacy.write_string(setups[0])
    if not ok: return None
    open(path, "w").write(s)
    return path

AFF_RE = re.compile(r"^\s+\d+\s+(-?\d+\.\d+)\s+")
def run_vina(tag, lp, out, exh=16):
    b = BOXES[tag]; c, s = b["center"], b["size"]
    cmd = [VINA, "--receptor", f"{D}/docking/receptors/{tag}.pdbqt", "--ligand", lp,
           "--out", out, "--center_x", str(c[0]), "--center_y", str(c[1]), "--center_z", str(c[2]),
           "--size_x", str(s[0]), "--size_y", str(s[1]), "--size_z", str(s[2]),
           "--exhaustiveness", str(exh), "--seed", "42", "--num_modes", "9"]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    affs = [float(AFF_RE.match(l).group(1)) for l in r.stdout.splitlines() if AFF_RE.match(l)]
    return affs[0] if affs else None

pred = pd.read_csv(f"{D}/results/tables/compound_cwbcs_full.csv")
top = pred.sort_values("CW_BCS", ascending=False).head(10)
rows = []
for _, r in top.iterrows():
    smi = r.get("smiles")
    if not isinstance(smi, str):
        continue
    mol = embed_3d(smi)
    key = re.sub(r"[^A-Za-z0-9]+", "_", f"{r['herb']}_{r['name']}")[:60]
    lp = to_pdbqt(mol, f"{LIGD}/top_{key}.pdbqt")
    a1 = run_vina("FXR_3FLI", lp, f"{OUTD}/top_FXR3FLI_{key}_out.pdbqt")
    a2 = run_vina("FXR_1OSH", lp, f"{OUTD}/top_FXR1OSH_{key}_out.pdbqt")
    rows.append(dict(herb=r["herb"], name=r["name"], CW_BCS=r["CW_BCS"],
                     fxr_mu=r["fxr_mu_pIC50"], fxr_sigma=r["fxr_sigma"], tier=r["tier"],
                     dG_FXR_3FLI=a1, dG_FXR_1OSH=a2))
    print(f"{r['name']}: 3FLI {a1} | 1OSH {a2} (GNN mu={r['fxr_mu_pIC50']})")
xd = pd.DataFrame(rows)
xd.to_csv(f"{D}/results/tables/fxr_crossdocking_top10.csv", index=False)
if len(xd):
    from scipy.stats import spearmanr
    sp1 = spearmanr(xd["fxr_mu"], xd["dG_FXR_3FLI"]).statistic
    print(f"\nSpearman(GNN mu, Vina dG 3FLI) = {sp1:.3f} (expect negative: higher mu, more negative dG)")

# ---------- figures ----------
FIG = f"{D}/results/figures"
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False
rank = pd.read_csv(f"{D}/results/tables/herb_cwbcs_ranking.csv")
fig, ax = plt.subplots(figsize=(9, 5.5))
colors = ["#2563eb" if i < 5 else "#93c5fd" for i in range(len(rank))]
ax.barh(range(len(rank)), rank["herb_score"], color=colors[::-1])
ax.set_yticks(range(len(rank))); ax.set_yticklabels(rank["herb"][::-1], fontsize=9)
ax.set_xlabel("CW-BCS herb score")
ax.set_title("Confidence-weighted binding-coverage score (CW-BCS) herb ranking\n"
             "top-3 compounds geometric mean x (1 - structural redundancy penalty)")
for i, (h, s) in enumerate(zip(rank["herb"][::-1], rank["herb_score"][::-1])):
    ax.text(s + 0.008, i, f"{s:.3f}", va="center", fontsize=8)
plt.tight_layout(); plt.savefig(f"{FIG}/herb_cwbcs_ranking.png", dpi=180)

pred2 = pd.read_csv(f"{D}/results/tables/compound_cwbcs_full.csv")
tier_counts = pred2.groupby(["herb", "tier"]).size().unstack(fill_value=0)
tier_counts.plot(kind="barh", stacked=True, figsize=(9, 5.5),
                 color=["#dc2626", "#f59e0b", "#16a34a"])
plt.xlabel("n compounds"); plt.title("Three-tier confidence annotation per herb\n"
             "(leverage AD x MC-Dropout sigma)")
plt.tight_layout(); plt.savefig(f"{FIG}/tier_annotation.png", dpi=180)
print("figures saved")
