# -*- coding: utf-8 -*-
"""
Step 6a: receptor preparation for docking.
For each target PDB: keep the chain that contains the co-crystal ligand,
remove waters/other hetero/other chains, compute box center from the ligand
centroid, then prepare receptor PDBQT with meeko (Gasteiger charges).
Also save the crystal ligand as SDF (ideal-bond-order template + crystal pose).
"""
import json, os, subprocess
import numpy as np
from prody import parsePDB, writePDB
from rdkit import Chem, RDLogger
from rdkit.Chem import AllChem

RDLogger.DisableLog('rdApp.*')
D = "D:/zcode-workspace/mash_research"
REC = f"{D}/docking/receptors"
MK_REC = r"C:\Users\user\AppData\Roaming\Python\Python312\Scripts\mk_prepare_receptor.exe"

# target -> (pdb, ligand_resname, chain_hint)
TARGETS = {
    "FXR_3FLI": ("3FLI.pdb", "33Y", "A"),
    "FXR_1OSH": ("1OSH.pdb", "FEX", "A"),
    "THRB_3GWS": ("3GWS.pdb", "T3", "X"),
    "ACC2_5KKN": ("5KKN.pdb", "6U3", "B"),
    "ACC2_3GID": ("3GID.pdb", "S1A", "A"),
}

def download_ligand_ideal(resname):
    """ideal-state SDF from RCSB Components API (real data)"""
    out = f"{REC}/{resname}_ideal.sdf"
    if not os.path.exists(out):
        import requests
        r = requests.get(f"https://files.rcsb.org/ligands/view/{resname}_ideal.sdf", timeout=30)
        if r.status_code != 200:
            raise RuntimeError(f"no ideal SDF for {resname}")
        open(out, "wb").write(r.content)
    return out

boxes = {}
for tag, (pdbf, lig, chain_hint) in TARGETS.items():
    print(f"\n===== {tag} =====")
    full = parsePDB(f"{REC}/{pdbf}")
    lig_all = full.select(f"resname {lig}")
    if lig_all is None:
        print("!! ligand not found"); continue
    chains = sorted(set(lig_all.getChids()))
    print("ligand chains:", chains, "| lig atoms:", lig_all.numAtoms())
    chain = chain_hint if chain_hint in chains else chains[0]
    # restrict to one copy: the chosen chain, first resnum, first altloc
    lig_atoms = full.select(f"resname {lig} and chain {chain}")
    resnums = sorted(set(lig_atoms.getResnums()))
    lig_atoms = full.select(f"resname {lig} and chain {chain} and resnum {resnums[0]}")
    print(f"using chain {chain} resnum {resnums[0]}: {lig_atoms.numAtoms()} atoms")
    cen = lig_atoms.getCoords().mean(axis=0)
    print(f"box center from {lig} centroid: {np.round(cen,2).tolist()}")

    # crystal ligand mol (for redocking RMSD): coords + ideal template bond orders
    ideal = download_ligand_ideal(lig)
    tmpl = Chem.SDMolSupplier(ideal, removeHs=False)[0]
    pdb_block = writePDBString = None
    from prody import writePDB
    lf = f"{REC}/{tag}_{lig}_crystal.pdb"
    writePDB(lf, lig_atoms)
    cryst = Chem.MolFromPDBFile(lf, removeHs=False, proximityBonding=True)
    if cryst is not None:
        try:
            cryst = AllChem.AssignBondOrdersFromTemplate(tmpl, cryst)
            w = Chem.SDWriter(f"{REC}/{tag}_{lig}_crystal.sdf"); w.write(cryst); w.close()
            print("crystal ligand SDF saved with template bond orders")
        except Exception as e:
            print("bond order assignment failed:", str(e)[:100])

    # clean receptor: chain w/ ligand, protein only
    sel = full.select(f"chain {chain} and protein")
    cf = f"{REC}/{tag}_clean.pdb"
    writePDB(cf, sel)
    print("clean receptor:", sel.numAtoms(), "atoms ->", cf)

    # meeko receptor prep -> pdbqt
    cmd = [MK_REC, "--read_pdb", cf, "-o", f"{REC}/{tag}",
           "-p", f"{REC}/{tag}.pdbqt", "--charge_model", "gasteiger",
           "-a", "--default_altloc", "A"]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    ok = os.path.exists(f"{REC}/{tag}.pdbqt")
    print("meeko rc:", r.returncode, "| pdbqt exists:", ok)
    if not ok:
        print(r.stdout[-1500:]); print(r.stderr[-1500:])
    ext = np.array(lig_atoms.getCoords())
    span = ext.max(0) - ext.min(0)
    size = np.clip(span + 10.0, 18.0, 30.0)  # ligand span + 10A padding, 18-30A
    boxes[tag] = dict(center=[round(float(c), 2) for c in cen],
                      size=[round(float(s), 2) for s in size],
                      ligand=lig, pdb=pdbf.replace(".pdb", ""), chain=chain)

json.dump(boxes, open(f"{D}/docking/boxes.json", "w"), indent=2)
print("\nboxes:", json.dumps(boxes, indent=1))
