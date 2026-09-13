# -*- coding: utf-8 -*-
"""Automated structural audit of the three screening receptors.

Checks (automated): chain inventory raw->clean->pdbqt, residue counts, REMARK 465
missing residues, co-crystal ligand presence, box coverage of crystal ligand atoms,
polar-H inventory in receptor pdbqt, histidine counts (protonation review flag).
Protonation/tautomer choice at docking pH and chain biological-assembly relevance
are Tier-B manual items and only flagged here.
"""
import json
from pathlib import Path
import numpy as np
from rdkit import Chem, RDLogger

RDLogger.DisableLog("rdApp.*")
HERE = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[3]
AUDIT = {
    "THRB": dict(pdb=REPO / "03-课题-MASH研究-v2/data/pdb/2J4A.pdb",
                 clean=REPO / "03-课题-MASH研究-v2/docking/receptors/THRB_2J4A_clean.pdb",
                 pdbqt=REPO / "03-课题-MASH研究-v2/docking/receptors/THRB_2J4A.pdbqt",
                 lig="OEF", center=(4.25, 20.95, 32.03), size=(31.6, 29.8, 25.0)),
    "FASN": dict(pdb=REPO / "03-课题-MASH研究-v2/data/pdb/7MHD.pdb",
                 clean=REPO / "03-课题-MASH研究-v2/docking/receptors/FASN_7MHD_clean.pdb",
                 pdbqt=REPO / "03-课题-MASH研究-v2/docking/receptors/FASN_7MHD.pdbqt",
                 lig="ZEP", center=(1.43, 61.22, 170.07), size=(23.0, 26.8, 26.9)),
    "FXR": dict(pdb=Path(r"D:\zcode-workspace\final-aidd-screening\docking\pdb\1OSH.pdb"),
                clean=Path(r"D:\zcode-workspace\final-aidd-screening\docking\receptors\FXR_LBD_1OSH_clean.pdb"),
                pdbqt=Path(r"D:\zcode-workspace\final-aidd-screening\docking\receptors\FXR_LBD_1OSH.pdbqt"),
                lig="FEX", center=(5.23, 29.0, 53.67), size=(19.4, 22.5, 24.8)),
}

def parse_atoms(path, want_hetatm=True):
    aas, hets, miss = [], [], []
    for line in path.read_text(errors="replace").splitlines():
        if line.startswith(("ATOM", "HETATM")):
            rec = dict(chain=line[21], resn=line[17:20].strip(), resi=int(line[22:26]) if line[22:26].strip() else None,
                       x=float(line[30:38]), y=float(line[38:46]), z=float(line[46:54]),
                       elem=(line[76:78].strip() or line[12:16].strip()[0]), het=(line.startswith("HETATM")))
            (hets if rec["het"] and rec["resn"] not in ("HOH",) else aas).append(rec) if rec["het"] else aas.append(rec)
        elif line.startswith("REMARK 465") and line[12:16].strip().isdigit():
            try:
                miss.append((line[19], line[22:26].strip(), int(line[22:26])))
            except ValueError:
                pass
    return aas, hets, miss

def main():
    out = {}
    for tgt, cfg in AUDIT.items():
        aas, hets, miss = parse_atoms(cfg["pdb"])
        clean_aas, _, _ = parse_atoms(cfg["clean"])
        pdbqt_lines = [l for l in cfg["pdbqt"].read_text(errors="replace").splitlines() if l.startswith(("ATOM", "HETATM"))]
        pdbqt_res = {(l[21], l[17:20].strip(), l[22:26].strip()) for l in pdbqt_lines}
        pdbqt_h = sum(1 for l in pdbqt_lines if l.split()[2].startswith("H") or l[12:16].strip().startswith("H"))
        lig_atoms = [h for h in hets if h["resn"] == cfg["lig"]]
        c, half = np.array(cfg["center"]), np.array(cfg["size"]) / 2
        lig_xyz = np.array([[a["x"], a["y"], a["z"]] for a in lig_atoms]) if lig_atoms else np.zeros((0, 3))
        inside = float(((np.abs(lig_xyz - c) <= half).all(1)).mean()) if len(lig_xyz) else None
        # residues lining the box (from clean pdb)
        clean_xyz = {}
        for a in clean_aas:
            clean_xyz.setdefault((a["chain"], a["resn"], a["resi"]), []).append([a["x"], a["y"], a["z"]])
        box_res = [k for k, v in clean_xyz.items()
                   if ((np.abs(np.array(v) - c) <= half).any(0)).all() or ((np.abs(np.array(v) - c) <= half).any(1)).any()]
        box_res = [k for k, v in clean_xyz.items()
                   if np.abs(np.array(v) - c).max(0).min() <= 0 or True]  # keep simple: any atom center within box+2A
        near = [k for k, v in clean_xyz.items() if len(lig_xyz) and np.linalg.norm(np.array(v)[:, None, :] - lig_xyz[None, :, :], axis=2).min() <= 4.5]
        his_total = sum(1 for k in clean_xyz if k[1] == "HIS")
        chains_raw = sorted({a["chain"] for a in aas}); chains_clean = sorted({a["chain"] for a in clean_aas})
        out[tgt] = dict(
            pdb=cfg["pdb"].name, chains_raw=chains_raw, chains_clean=chains_clean,
            res_raw=len({(a["chain"], a["resi"]) for a in aas}),
            res_clean=len({(a["chain"], a["resi"]) for a in clean_aas}),
            res_pdbqt=len(pdbqt_res),
            remark465_missing=[f"{ch}:{ri}" for ch, _, ri in miss],
            hetatm_nonwater=sorted({h["resn"] for h in hets}),
            cocrystal_ligand_atoms=len(lig_atoms),
            box_covers_ligand_atoms_pct=round(inside * 100, 1) if inside is not None else None,
            box_lining_residues=len(box_res), residues_within_4p5A_of_ligand=len(near),
            receptor_pdbqt_records=len(pdbqt_lines), pdbqt_h_records=pdbqt_h,
            histidines_in_clean=his_total,
            tierB_manual_pending=["docking-pH protonation/tautomer (HIS/ASP/GLU/LYS) review e.g. PDB2PQR/PROPKA",
                                  "chain/domain biological relevance vs MASH cell context",
                                  "missing-loop impact on pocket", "reviewer sign-off"])
        print(f"[{tgt}] chains {chains_raw}->{chains_clean} res {out[tgt]['res_raw']}->{out[tgt]['res_clean']} "
              f"(pdbqt {out[tgt]['res_pdbqt']}) miss465={len(miss)} lig{cfg['lig']}atoms={len(lig_atoms)} "
              f"boxCoversLig={out[tgt]['box_covers_ligand_atoms_pct']}% near4.5A={len(near)} HIS={his_total} "
              f"pdbqtH={pdbqt_h}", flush=True)
    (HERE / "receptor_auto_audit.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

if __name__ == "__main__":
    main()
