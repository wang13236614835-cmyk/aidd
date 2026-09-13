# -*- coding: utf-8 -*-
"""Why does FASN/ZEP pose recovery pass only 1/4 seeds? Keep all failures.

Compare per-seed best poses (independent ETKDG starts, project protocol) and the
platform fixed-box pose: centroid offsets, internal conformational agreement,
contact-residue overlap with the crystal reference. No seed cherry-picking:
all four seeds reported with pass/fail as-is.
"""
import json, re
from pathlib import Path
import numpy as np
from rdkit import Chem, RDLogger
from rdkit.Chem import rdMolAlign
from meeko import PDBQTMolecule
from meeko.rdkit_mol_create import RDKitMolCreate

RDLogger.DisableLog("rdApp.*")
HERE = Path(__file__).resolve().parent
BASE = HERE.parent.parent / "validation/dockscope_verify_20260909"
RECEPTOR = Path(r"D:\zcode-workspace\aidd-repo-work\03-课题-MASH研究-v2\docking\receptors\FASN_7MHD.pdbqt")

def load_pose(p):
    text = Path(p).read_text()
    m = re.search(r"MODEL.*?ENDMDL", text, re.S)
    mol = RDKitMolCreate.from_pdbqt_mol(PDBQTMolecule(m.group(0) + "\n", skip_typing=True))[0]
    return Chem.RemoveHs(mol)

def centroid(mol):
    conf = mol.GetConformer()
    return np.array([list(conf.GetAtomPosition(i)) for i in range(mol.GetNumAtoms())]).mean(0)

def receptor_contacts(pose_mol, cutoff=4.5):
    pc = pose_mol.GetConformer()
    lig = np.array([list(pc.GetAtomPosition(i)) for i in range(pose_mol.GetNumAtoms())])
    res = set()
    for line in RECEPTOR.read_text(errors="replace").splitlines():
        if line.startswith(("ATOM", "HETATM")):
            xyz = np.array([float(line[30:38]), float(line[38:46]), float(line[46:54])])
            if np.linalg.norm(lig - xyz, axis=1).min() <= cutoff:
                res.add((line[21], line[22:26].strip()))
    return res

def main():
    ref = Chem.RemoveHs(Chem.MolFromMolBlock(
        (BASE / "FASN_corrected_crystal.sdf").read_text(encoding="utf-8"), removeHs=False))
    seeds = {}
    for seed in (42, 7, 123, 20260909):
        seeds[f"protocol_seed{seed}"] = BASE / f"protocol_seed{seed}/FASN_pose.pdbqt"
    seeds["platform_fixedbox_seed1"] = BASE / "dockscope_FASN/FASN_crystalbox_docked.pdbqt"
    known_rmsd = {"protocol_seed42": 2.0766, "protocol_seed7": 2.0878, "protocol_seed123": 2.0797,
                  "protocol_seed20260909": 1.6287, "platform_fixedbox_seed1": 1.654}
    ref_contacts = receptor_contacts(ref)
    out = {}
    mols = {}
    for k, p in seeds.items():
        m = load_pose(p); mols[k] = m
        c = centroid(m)
        inter = rdMolAlign.CalcRMS(m, ref)  # internal conf vs crystal (with symmetry)
        contacts = receptor_contacts(m)
        out[k] = dict(rmsd_to_crystal=round(float(inter), 3), known_best_mode_rmsd=known_rmsd[k],
                      gate_pass=(known_rmsd[k] < 2.0),
                      centroid=[round(float(x), 2) for x in c],
                      centroid_offset_A=round(float(np.linalg.norm(c - centroid(ref))), 2),
                      internal_conformation_rmsd_to_crystal=round(float(inter), 3),
                      n_contacts=len(contacts),
                      contact_overlap_with_crystal=round(len(contacts & ref_contacts) / max(1, len(ref_contacts)), 2),
                      shared_contacts=sorted(f"{ch}{ri}" for ch, ri in list(contacts & ref_contacts))[:12])
        print(f"{k:<26s} gate={'PASS' if out[k]['gate_pass'] else 'FAIL'} bestRMSD={known_rmsd[k]:.3f} "
              f"centroidOff={out[k]['centroid_offset_A']:.2f}A contacts={len(contacts)} "
              f"overlap={out[k]['contact_overlap_with_crystal']:.0%}", flush=True)
    # pairwise pose agreement between seeds
    ks = list(mols)
    pair = {}
    for i in range(len(ks)):
        for j in range(i + 1, len(ks)):
            pair[f"{ks[i]}|{ks[j]}"] = round(float(rdMolAlign.CalcRMS(mols[ks[i]], mols[ks[j]])), 2)
    out["_pairwise_pose_rmsd"] = pair
    out["_crystal_contact_count"] = len(ref_contacts)
    (HERE / "fasn_seed_analysis.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\npairwise best-pose RMSD:", pair, flush=True)

if __name__ == "__main__":
    main()
