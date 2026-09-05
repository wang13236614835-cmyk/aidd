# -*- coding: utf-8 -*-
"""
S5c: NP库批量对接（54化合物 × THRB/FASN）。
盒子使用门控验证过的: THRB(pad10) / FASN(pad8)。exh=8, seed=42, num_modes=9。
输出: results/tables/np_docking_raw_new.csv
"""
import json, os, re, subprocess
import numpy as np
import pandas as pd
from rdkit import Chem, RDLogger
from rdkit.Chem import AllChem
from meeko import MoleculePreparation, PDBQTWriterLegacy

RDLogger.DisableLog('rdApp.*')
D = "D:/zcode-workspace/mash_v2_new"
VINA = f"{D}/tools/vina_1.2.5_win.exe"
LGD, OUT = f"{D}/docking/ligands", f"{D}/docking/outputs"
MK = MoleculePreparation()
AFF_RE = re.compile(r"^\s+\d+\s+(-?\d+\.\d+)\s+")

# 门控验证盒子
BOX = {"THRB": dict(center=[4.25, 20.95, 32.03], size=[31.6, 29.8, 25.0],
                    receptor="docking/receptors/THRB_2J4A.pdbqt")}
c = []
for l in open(f"{D}/docking/receptors/FASN_7MHD_ZEP_lig.pdb"):
    if l.startswith("HETATM"):
        c.append([float(l[30:38]), float(l[38:46]), float(l[46:54])])
c = np.array(c)
BOX["FASN"] = dict(center=c.mean(0).round(2).tolist(),
                   size=(c.max(0) - c.min(0) + 16).round(1).tolist(),
                   receptor="docking/receptors/FASN_7MHD.pdbqt")

lib = pd.read_csv(f"{D}/data/tcm/np_library_filtered.csv")
print(f"NP library: {len(lib)}")

def embed_and_prep(smi, path, seed=42):
    m = Chem.MolFromSmiles(smi)
    if m is None:
        return False
    m = Chem.AddHs(m)
    p = AllChem.ETKDGv3(); p.randomSeed = seed
    if AllChem.EmbedMolecule(m, p) != 0:
        p.useRandomCoords = True
        if AllChem.EmbedMolecule(m, p) != 0:
            return False
    try:
        AllChem.MMFFOptimizeMolecule(m, mmffVariant="MMFF94s", maxIters=500)
    except Exception:
        pass
    try:
        setups = MK(m)
        s, ok, err = PDBQTWriterLegacy.write_string(setups[0])
        if not ok:
            return False
        open(path, "w").write(s)
        return True
    except Exception:
        return False

rows = []
done = 0
for i, r in lib.iterrows():
    safe = f"np{i:03d}_{str(r['name']).replace(' ', '_').replace('-', '_').replace(chr(39), '')[:30]}"
    lq = f"{LGD}/{safe}.pdbqt"
    if not os.path.exists(lq):
        if not embed_and_prep(r["smiles"], lq):
            rows.append(dict(herb=r["herb"], name=r["name"], target="BOTH", affinity=None,
                             note="PREP_FAIL"))
            continue
    for tag in ["THRB", "FASN"]:
        b = BOX[tag]
        outp = f"{OUT}/{safe}_{tag}.pdbqt"
        cmd = [VINA, "--receptor", b["receptor"], "--ligand", lq, "--out", outp,
               "--center_x", str(b["center"][0]), "--center_y", str(b["center"][1]),
               "--center_z", str(b["center"][2]),
               "--size_x", str(b["size"][0]), "--size_y", str(b["size"][1]),
               "--size_z", str(b["size"][2]),
               "--exhaustiveness", "8", "--seed", "42", "--num_modes", "9", "--cpu", "4"]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=1200)
            affs = [float(AFF_RE.match(l).group(1)) for l in res.stdout.splitlines()
                    if AFF_RE.match(l)]
            aff = affs[0] if affs else None
        except Exception:
            aff = None
        rows.append(dict(herb=r["herb"], name=r["name"], target=tag, affinity=aff,
                         note="" if aff is not None else "DOCK_FAIL"))
    done += 1
    if done % 10 == 0:
        print(f"progress {done}/{len(lib)}", flush=True)
        pd.DataFrame(rows).to_csv(f"{D}/results/tables/np_docking_raw_new.csv", index=False)

df = pd.DataFrame(rows)
df.to_csv(f"{D}/results/tables/np_docking_raw_new.csv", index=False)
print("done:", df.shape)
print(df.groupby("target").affinity.agg(["count", "min", "median"]))
print("\nS5c complete.")
