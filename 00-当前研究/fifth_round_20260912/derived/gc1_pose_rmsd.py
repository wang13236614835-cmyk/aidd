"""Fifth-round GC-1 crystal-pose RMSD (final method).

Docked side: meeko PDBQTMolecule + RDKitMolCreate rebuilds the docked poses with
correct chemistry (template mol). Crystal side: B72 heavy-atom coordinates from
wt_3IMY.pdb are transferred onto the SAME template via an order/bond-insensitive
substructure match (AdjustQueryProperties makeBondsGeneric + makeAtomsGeneric off,
atom degree preserved by heavy-atom proximity rebuild). RMSD per seed uses the
top-scored pose (MODEL 1); all-mode values reported for transparency.
"""
import json, re
from pathlib import Path
from rdkit import Chem, RDLogger
from rdkit.Chem import AllChem, rdMolDescriptors
from rdkit.Chem import rdmolops
from meeko import PDBQTMolecule, RDKitMolCreate

RDLogger.DisableLog("rdApp.*")
ROOT = Path(r"D:\zcode-workspace\aidd-repo-work\00-当前研究\fifth_round_20260912")
IMY = Path(r"D:\zcode-workspace\aidd-repo-work\00-当前研究\wp_exec_20260909\00_task_ledger\wt_receptor_validation\wt_3IMY.pdb")
ELEM_OK = {"C", "N", "O", "S", "P", "F"}

def pdb_line(idx, sym, x, y, z):
    name = f"{sym}{idx}"
    return ("ATOM  " + f"{idx:5d}" + " " + f"{name:>4s}" + " " + "LIG" + " "
            + "A" + f"{1:4d}" + " " + "   "
            + f"{x:8.3f}{y:8.3f}{z:8.3f}" + f"{1.00:6.2f}" + f"{0.00:6.2f}"
            + " " * 10 + f"{sym:>2s}")

# template with correct chemistry from the docked file's embedded SMILES
pm0 = PDBQTMolecule.from_file(r"D:\zcode-workspace\h1_mash\gc1_seed7.pdbqt", skip_typing=True)
template = RDKitMolCreate.from_pdbqt_mol(pm0)[0]
template = Chem.RemoveHs(Chem.Mol(template))
print("template heavy atoms:", template.GetNumAtoms())

# crystal proximity mol (element-correct, bond-order-free)
xtal_atoms = []
for line in IMY.read_text(encoding="utf-8", errors="replace").splitlines():
    if line.startswith(("ATOM", "HETATM")) and line[17:20].strip() == "B72":
        el = line[76:78].strip().upper()
        if el in ELEM_OK:
            xtal_atoms.append((el, float(line[30:38]), float(line[38:46]), float(line[46:54])))
block = ("REMARK crystal B72 3IMY\n"
         + "\n".join(pdb_line(i, e, x, y, z) for i, (e, x, y, z) in enumerate(xtal_atoms, 1))
         + "\nEND\n")
mol_xtal_raw = Chem.MolFromPDBBlock(block, proximityBonding=True, removeHs=True, sanitize=False)
Chem.SanitizeMol(mol_xtal_raw, Chem.SanitizeFlags.SANITIZE_SYMMRINGS | Chem.SanitizeFlags.SANITIZE_SETCONJUGATION)
print("crystal proximity atoms:", mol_xtal_raw.GetNumAtoms())

params = rdmolops.AdjustQueryParameters.NoAdjustments()
params.makeBondsGeneric = True
params.makeAtomsGeneric = False
params.adjustDegree = False
query = rdmolops.AdjustQueryProperties(template, params)
matches = mol_xtal_raw.GetSubstructMatches(query, useChirality=False, maxMatches=10)
if not matches:
    raise SystemExit("no bond-insensitive match between crystal B72 and GC-1 template")
match = matches[0]  # template atom i <-> crystal atom match[i]
print("template->crystal mapping found, first match length:", len(match))

conf = Chem.Conformer(template.GetNumAtoms())
for t_i, x_i in enumerate(match):
    pos = mol_xtal_raw.GetConformer().GetAtomPosition(x_i)
    conf.SetAtomPosition(t_i, (pos.x, pos.y, pos.z))
mol_xtal = Chem.Mol(template)
mol_xtal.RemoveAllConformers()
mol_xtal.AddConformer(conf, assignId=True)
print("crystal coords transferred onto chemistry template")

out = {}
for seed in ("7", "42", "123", "20260910"):
    p = Path(rf"D:\zcode-workspace\h1_mash\gc1_seed{seed}.pdbqt")
    text = p.read_text(encoding="utf-8", errors="replace")
    top_score = float(re.search(r"REMARK VINA RESULT:\s+(-?\d+\.\d+)", text).group(1))
    pm = PDBQTMolecule.from_file(str(p), skip_typing=True)
    m = Chem.RemoveHs(RDKitMolCreate.from_pdbqt_mol(pm)[0])
    rmsds = []
    for ci in range(m.GetNumConformers()):
        frag = Chem.Mol(m)
        frag.RemoveAllConformers()
        c = Chem.Conformer(m.GetConformer(ci))
        frag.AddConformer(c, assignId=True)
        try:
            rmsds.append(round(AllChem.GetBestRMS(frag, mol_xtal), 3))
        except Exception:
            rmsds.append("ERR")
    out[seed] = {"top_score_kcal_mol": top_score, "n_models": m.GetNumConformers(),
                 "rmsd_top_scored_pose_A": rmsds[0] if rmsds else None,
                 "rmsd_all_modes_A": rmsds}
    print(seed, out[seed])

dest = ROOT / "derived" / "gc1_pose_rmsd_per_seed.json"
dest.write_text(json.dumps(out, indent=1), encoding="utf-8")
print("saved", dest)
