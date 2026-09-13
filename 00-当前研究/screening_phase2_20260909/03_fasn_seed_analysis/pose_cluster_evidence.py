# -*- coding: utf-8 -*-
"""FASN two-pose-cluster HYPOTHESIS: full-mode clustering across all seeds.

Reports (kept exploratory, not claimed as proven energy basins):
- all 9 modes per seed (5 sources), RMSD-to-crystal distribution
- pairwise pose RMSD matrix + agglomerative clustering at 2.0 A cutoff
- affinity-vs-RMSD per mode (score separation between clusters)
- symmetric-molecule caveat: CalcRMS uses symmetry-corrected mapping; cluster
  distinction relies on heavy-atom geometry, atom mapping documented as
  RDKit CalcRMS substructure match (not manual atom correspondence)
- gap-to-box distance for internal missing residues 452-456 (pocket relevance)
"""
import json, re
import numpy as np
from pathlib import Path
from rdkit import Chem, RDLogger
from rdkit.Chem import rdMolAlign
from meeko import PDBQTMolecule
from meeko.rdkit_mol_create import RDKitMolCreate

RDLogger.DisableLog("rdApp.*")
HERE = Path(__file__).resolve().parent
BASE = HERE.parent.parent / "validation/dockscope_verify_20260909"
RECEPTOR = Path(r"D:\zcode-workspace\aidd-repo-work\03-课题-MASH研究-v2\docking\receptors\FASN_7MHD.pdbqt")
BOX_CENTER = np.array([1.43, 61.22, 170.07]); BOX_HALF = np.array([23.0, 26.8, 26.9]) / 2

def all_poses(p):
    text = Path(p).read_text()
    out = []
    for i, m in enumerate(re.finditer(r"MODEL.*?ENDMDL", text, re.S), 1):
        mol = RDKitMolCreate.from_pdbqt_mol(PDBQTMolecule(m.group(0) + "\n", skip_typing=True))[0]
        out.append(Chem.RemoveHs(mol))
    return out

def affinities(p):
    log = Path(str(p).replace("_out", "")).with_suffix(".log") if "_out" in p.name else None
    return log

def main():
    ref = Chem.RemoveHs(Chem.MolFromMolBlock(
        (BASE / "FASN_corrected_crystal.sdf").read_text(encoding="utf-8"), removeHs=False))
    sources = {f"seed42": BASE / "protocol_seed42/FASN_pose.pdbqt",
               "seed7": BASE / "protocol_seed7/FASN_pose.pdbqt",
               "seed123": BASE / "protocol_seed123/FASN_pose.pdbqt",
               "seed20260909": BASE / "protocol_seed20260909/FASN_pose.pdbqt",
               "platform_seed1": BASE / "dockscope_FASN/FASN_crystalbox_docked.pdbqt"}
    # affinity per mode from logs
    aff = {}
    for k, p in sources.items():
        logp = p.parent / (p.stem.replace("_docked", "") + ".log")
        cands = [p.with_suffix(".log")]
        if k == "platform_seed1":
            cands = [BASE / "dockscope_FASN" / "all_docking_results.csv"]
        txt = None
        for c in [p.parent / "FASN.log", p.with_suffix(".log")]:
            if c.exists():
                txt = c.read_text(); break
        if txt:
            aff[k] = [float(m) for _, m in re.findall(r"^\s+(\d+)\s+(-?\d+\.\d+)", txt, re.M)]
    mols, labels = [], []
    for k, p in sources.items():
        for i, m in enumerate(all_poses(p), 1):
            mols.append(m); labels.append(f"{k}:mode{i}")
    n = len(mols)
    D = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            D[i, j] = D[j, i] = rdMolAlign.CalcRMS(mols[i], mols[j])
    rmsd_crystal = np.array([rdMolAlign.CalcRMS(m, ref) for m in mols])
    # agglomerative single-linkage clusters at 2.0 A
    unassigned = list(range(n)); clusters = []
    while unassigned:
        seed = unassigned.pop(0)
        cl = [seed]
        for u in list(unassigned):
            if min(D[u, c] for c in cl) <= 2.0:
                cl.append(u); unassigned.remove(u)
        clusters.append(cl)
    print(f"total poses: {n} from 5 sources; clusters at 2.0A single-linkage: {len(clusters)}")
    cluster_info = []
    for ci, cl in enumerate(clusters, 1):
        rms = rmsd_crystal[cl]
        members = [labels[i] for i in cl]
        cluster_info.append(dict(cluster=ci, n=len(cl), members=members,
                                  rmsd_to_crystal=[round(float(r), 2) for r in rms],
                                  best_mode_count=sum(1 for i in cl if labels[i].endswith("mode1"))))
        print(f"  cluster {ci}: n={len(cl)} rmsd_crystal {rms.min():.2f}-{rms.max():.2f} "
              f"members={members[:6]}{'...' if len(members)>6 else ''}")
    # affinity separation between the two largest clusters (best modes only)
    best = [i for i in range(n) if labels[i].endswith("mode1")]
    big2 = sorted(clusters, key=len, reverse=True)[:2]
    aff_by_seed = {k: aff.get(k, []) for k in sources}
    a1 = [aff_by_seed[labels[i].split(":")[0]][0] for i in big2[0] if i in best and aff_by_seed[labels[i].split(":")[0]]]
    a2 = [aff_by_seed[labels[i].split(":")[0]][0] for i in big2[1] if i in best and aff_by_seed[labels[i].split(":")[0]]]
    print(f"\nbest-mode affinity: clusterA {a1} vs clusterB {a2}")
    # internal-gap-to-box check
    rec_xyz = []
    for line in RECEPTOR.read_text(errors="replace").splitlines():
        if line.startswith(("ATOM", "HETATM")):
            num = int(line[22:26])
            if 448 <= num <= 460:
                rec_xyz.append([float(line[30:38]), float(line[38:46]), float(line[46:54])])
    if rec_xyz:
        d = np.abs(np.array(rec_xyz) - BOX_CENTER).max(1).min()
        gap_note = f"residues 448-460 nearest box-surface distance (max-axis) = {d:.1f} A"
    else:
        gap_note = "residues 448-460 absent from receptor file (missing region not modeled)"
    print("\ninternal gap 452-456:", gap_note)
    out = dict(n_poses=n, linkage="single @2.0A heavy-atom CalcRMS (symmetry-corrected)",
               clusters=cluster_info, best_mode_affinity_clusterA=a1, best_mode_affinity_clusterB=a2,
               gap_452_456_note=gap_note,
               caveat="two-pose-cluster is a geometrical observation (HYPOTHESIS); not a proven two-basin energy landscape; atom mapping via RDKit symmetry-corrected match; all failing seeds retained")
    (HERE / "pose_cluster_evidence.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

if __name__ == "__main__":
    main()
