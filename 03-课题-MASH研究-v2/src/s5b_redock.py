# -*- coding: utf-8 -*-
"""
S5b: 重对接门控(RMSD<2Å) + 阳性对照。
晶体配体(OEF/ZEP)原位坐标制备pdbqt -> Vina重对接(exh=16,seed=42) -> 与晶体构象GetBestRMS。
阳性对照: resmetirom(THRb获批药) / orlistat(FASN-TE经典抑制剂)。
"""
import json, os, re, subprocess
import numpy as np
from rdkit import Chem, RDLogger
from rdkit.Chem import AllChem, rdMolAlign
from meeko import MoleculePreparation, PDBQTWriterLegacy, PDBQTMolecule
from meeko.rdkit_mol_create import RDKitMolCreate

RDLogger.DisableLog('rdApp.*')
D = "D:/zcode-workspace/mash_v2_new"
VINA = f"{D}/tools/vina_1.2.5_win.exe"
RCP, LGD, OUT = f"{D}/docking/receptors", f"{D}/docking/ligands", f"{D}/docking/outputs"
boxes = json.load(open(f"{D}/docking/boxes.json"))
MK = MoleculePreparation()

def pdbqt_from_mol(m, path):
    setups = MK(m)
    s, ok, err = PDBQTWriterLegacy.write_string(setups[0])
    if not ok:
        return False
    open(path, "w").write(s)
    return True

def pdb_from_block(block):
    m = Chem.MolFromPDBBlock(block, removeHs=False, proximityBonding=True)
    return Chem.AddHs(m, addCoords=True) if m else None

def embed(smi, seed=42):
    m = Chem.MolFromSmiles(smi)
    if m is None:
        return None
    m = Chem.AddHs(m)
    p = AllChem.ETKDGv3(); p.randomSeed = seed
    if AllChem.EmbedMolecule(m, p) != 0:
        p.useRandomCoords = True
        if AllChem.EmbedMolecule(m, p) != 0:
            return None
    try:
        AllChem.MMFFOptimizeMolecule(m, mmffVariant="MMFF94s", maxIters=500)
    except Exception:
        pass
    return m

AFF_RE = re.compile(r"^\s+\d+\s+(-?\d+\.\d+)\s+")
def run_vina(tag, ligpdbqt, exh=8, seed=42, cpu=4):
    b = boxes[tag]
    outp = f"{OUT}/{os.path.basename(ligpdbqt).replace('.pdbqt','')}_{tag}_out.pdbqt"
    cmd = [VINA, "--receptor", f"{RCP}/{tag}_{'2J4A' if tag=='THRB' else '7MHD'}.pdbqt",
           "--ligand", ligpdbqt, "--out", outp,
           "--center_x", str(b["center"][0]), "--center_y", str(b["center"][1]),
           "--center_z", str(b["center"][2]),
           "--size_x", str(b["size"][0]), "--size_y", str(b["size"][1]),
           "--size_z", str(b["size"][2]),
           "--exhaustiveness", str(exh), "--seed", str(seed), "--num_modes", "9",
           "--cpu", str(cpu)]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    affs = [float(AFF_RE.match(l).group(1)) for l in r.stdout.splitlines() if AFF_RE.match(l)]
    return (affs[0] if affs else None), outp

def rmsd_to_crystal(outpdbqt, crystal_sdf):
    txt = open(outpdbqt).read()
    first = "MODEL" + txt.split("MODEL")[1].split("ENDMDL")[0] + "ENDMDL\n"
    pmol = PDBQTMolecule(first, skip_typing=True)
    mol = RDKitMolCreate.from_pdbqt_mol(pmol)[0]
    pose = Chem.RemoveHs(mol)
    ref = Chem.RemoveHs(Chem.SDMolSupplier(crystal_sdf, removeHs=False)[0])
    return float(rdMolAlign.GetBestRMS(pose, ref))

# ---------- 重对接门控 ----------
print("=== redock gate ===")
RED = {"THRB": ("OEF", f"{RCP}/THRB_2J4A_OEF_lig.pdb", f"{RCP}/THRB_2J4A_OEF_crystal.sdf"),
       "FASN": ("ZEP", f"{RCP}/FASN_7MHD_ZEP_lig.pdb", f"{RCP}/FASN_7MHD_ZEP_crystal.sdf")}
gate = {}
for tag, (lig, lp, sp) in RED.items():
    m = pdb_from_block(open(lp).read())
    lq = f"{LGD}/{tag}_{lig}_redock.pdbqt"
    if not pdbqt_from_mol(m, lq):
        print(f"{tag}: ligand prep FAILED"); continue
    aff, outp = run_vina(tag, lq, exh=16, cpu=8)
    rms = rmsd_to_crystal(outp, sp)
    gate[tag] = dict(ligand=lig, affinity=aff, rmsd=round(rms, 3),
                     pass_gate=bool(rms < 2.0))
    print(f"{tag} {lig}: affinity={aff} RMSD={rms:.2f}Å -> {'PASS' if rms < 2 else 'FAIL'}")
json.dump(gate, open(f"{D}/docking/redock_gate.json", "w"), indent=1)

# ---------- 阳性对照 ----------
print("\n=== positive controls ===")
import urllib.request, urllib.parse
def pubchem_smiles(name):
    q = urllib.parse.quote(name)
    r = urllib.request.urlopen(urllib.request.Request(
        f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{q}/property/SMILES/JSON",
        headers={"User-Agent": "academic/2.0"}), timeout=40)
    p = json.loads(r.read())["PropertyTable"]["Properties"][0]
    return p.get("SMILES")

CTRLS = {"THRB": ["resmetirom", "sobetirome"], "FASN": ["orlistat", "cerulenin"]}
ctrl_rows = []
for tag, names in CTRLS.items():
    for nm in names:
        try:
            smi = pubchem_smiles(nm)
        except Exception:
            smi = None
        if not smi:
            ctrl_rows.append(dict(target=tag, control=nm, affinity=None, note="PUBCHEM_MISS"))
            print(f"{tag} {nm}: PUBCHEM_MISS"); continue
        m = embed(smi)
        lq = f"{LGD}/ctrl_{nm.replace(' ','_').replace('-','_')}.pdbqt"
        if m is None or not pdbqt_from_mol(m, lq):
            ctrl_rows.append(dict(target=tag, control=nm, affinity=None, note="EMBED_FAIL"))
            continue
        aff, _ = run_vina(tag, lq, exh=8)
        ctrl_rows.append(dict(target=tag, control=nm, affinity=aff, note=""))
        print(f"{tag} {nm}: {aff} kcal/mol")
import pandas as pd
pd.DataFrame(ctrl_rows).to_csv(f"{D}/results/tables/positive_controls_docking_new.csv", index=False)
print("\nS5b done.")
