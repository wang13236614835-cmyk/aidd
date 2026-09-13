"""Fresh fixed-box docking screen of the 54-herb natural-product library.

Protocol (all gates verified 2026-09-09, see validation/dockscope_verify_20260909):
- Ligands: SMILES -> ETKDGv3 (seed 42) -> MMFF -> Meeko PDBQT (rdkit 2026.03.3 / meeko 0.7.1)
- Receptors/boxes: archived crystallographic boxes, fixed per target
- Engine: DockScope bundled vina.exe (sha256 e0c4b271..., byte-identical to project vina 1.2.7)
- Gate: FXR/FEX redock must recover < 2.0 A before screening proceeds
- Output: per-pose scores only; NO weighted candidate fusion (audit item A11)
Run:  python run_screening.py --gate   (FXR gate only)
      python run_screening.py --screen (gate + 54x3 docking)
"""
import argparse, csv, hashlib, json, re, subprocess, sys, time
from pathlib import Path
from rdkit import Chem, RDLogger
from rdkit.Chem import AllChem, rdMolAlign
from rdkit.Geometry import Point3D
from meeko import MoleculePreparation, PDBQTWriterLegacy, PDBQTMolecule
from meeko.rdkit_mol_create import RDKitMolCreate

RDLogger.DisableLog("rdApp.*")
HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent  # aidd-repo-work
VINA = Path(r"D:\dockscope\DockScopeLicensed\resources\tools\vina.exe")
SEED = 42
EXHAUSTIVENESS = 8
CPU = 8

TARGETS = {
    "THRB": dict(receptor=REPO / "03-课题-MASH研究-v2/docking/receptors/THRB_2J4A.pdbqt",
                 center=(4.25, 20.95, 32.03), size=(31.6, 29.8, 25.0),
                 gate_note="verified 20260909: 5/5 pose recovery 0.61-0.73 A"),
    "FASN": dict(receptor=REPO / "03-课题-MASH研究-v2/docking/receptors/FASN_7MHD.pdbqt",
                 center=(1.43, 61.22, 170.07), size=(23.0, 26.8, 26.9),
                 gate_note="verified 20260909: platform fixed-box 1.654 A; seed-sensitive (1/4) - rank marginally"),
    "FXR": dict(receptor=Path(r"D:\zcode-workspace\final-aidd-screening\docking\receptors\FXR_LBD_1OSH.pdbqt"),
                center=(5.23, 29.0, 53.67), size=(19.4, 22.5, 24.8),
                gate_note="archived snapshot gate 0.735 A; re-verified by this run's --gate step"),
}
LIBRARY = REPO / "03-课题-MASH研究-v2/data/tcm/np_library_filtered.csv"
FXR_CRYSTAL = Path(r"D:\zcode-workspace\final-aidd-screening\docking\receptors\FXR_LBD_1OSH_FEX_crystal.sdf")


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def prepare_ligand(smiles: str, seed: int = SEED):
    """SMILES -> independently embedded 3D PDBQT text (no crystal-geometry memory)."""
    m = Chem.MolFromSmiles(smiles)
    if m is None:
        raise ValueError("SMILES parse failed")
    m = Chem.AddHs(m)
    p = AllChem.ETKDGv3(); p.randomSeed = seed
    if AllChem.EmbedMolecule(m, p) != 0:
        raise ValueError("ETKDG failed")
    if AllChem.MMFFOptimizeMolecule(m, maxIters=1000) != 0:
        raise ValueError("MMFF not converged")
    text, ok, err = PDBQTWriterLegacy.write_string(MoleculePreparation()(m)[0])
    if not ok:
        raise ValueError(err)
    return text


def vina_dock(receptor: Path, ligand_pdbqt: Path, out_pose: Path, center, size, log: Path, ex=EXHAUSTIVENESS):
    cmd = [str(VINA), "--receptor", str(receptor), "--ligand", str(ligand_pdbqt), "--out", str(out_pose)]
    for k, v in (("center", center), ("size", size)):
        for ax, val in zip("xyz", v):
            cmd += [f"--{k}_{ax}", str(val)]
    cmd += ["--seed", str(SEED), "--exhaustiveness", str(ex), "--num_modes", "9", "--cpu", str(CPU)]
    r = subprocess.run(cmd, capture_output=True, text=True, errors="replace", timeout=1800)
    log.write_text(r.stdout + "\n" + r.stderr, encoding="utf-8")
    if r.returncode != 0 or not out_pose.exists():
        raise RuntimeError(f"vina failed rc={r.returncode}; see {log}")
    affs = [float(m) for _, m in re.findall(r"^\s+(\d+)\s+(-?\d+\.\d+)", r.stdout, re.M)]
    return cmd, affs


def pose_rmsd(pose_pdbqt: Path, ref_mol) -> float:
    text = pose_pdbqt.read_text()
    m = re.search(r"MODEL.*?ENDMDL", text, re.S)
    mol = RDKitMolCreate.from_pdbqt_mol(PDBQTMolecule(m.group(0) + "\n", skip_typing=True))[0]
    return float(rdMolAlign.CalcRMS(Chem.RemoveHs(mol), ref_mol))


def fxr_gate(out_dir: Path) -> dict:
    """FXR/FEX pose-recovery gate with this pipeline's own ligand prep."""
    out_dir.mkdir(parents=True, exist_ok=True)
    ref = Chem.RemoveHs(Chem.MolFromMolFile(str(FXR_CRYSTAL), removeHs=False))
    ref_block = FXR_CRYSTAL.read_text(encoding="utf-8")
    ref = Chem.RemoveHs(Chem.MolFromMolBlock(ref_block, removeHs=False))
    smiles = ref  # template for connectivity
    # independent start from FEX connectivity (from crystal mol, strip coords)
    start = Chem.Mol(smiles)
    start.RemoveAllConformers()
    start = Chem.AddHs(start)
    p = AllChem.ETKDGv3(); p.randomSeed = SEED
    assert AllChem.EmbedMolecule(start, p) == 0
    assert AllChem.MMFFOptimizeMolecule(start, maxIters=1000) == 0
    text, ok, err = PDBQTWriterLegacy.write_string(MoleculePreparation()(start)[0])
    assert ok, err
    lq = out_dir / "FXR_FEX_initial.pdbqt"; lq.write_text(text)
    cmd, affs = vina_dock(TARGETS["FXR"]["receptor"], lq, out_dir / "FXR_FEX_pose.pdbqt",
                          TARGETS["FXR"]["center"], TARGETS["FXR"]["size"], out_dir / "FXR_FEX.log", ex=16)
    rmsd = pose_rmsd(out_dir / "FXR_FEX_pose.pdbqt", ref)
    rec = dict(target="FXR_1OSH_FEX", best_affinity=affs[0], rmsd_no_alignment=round(rmsd, 4),
               gate_pass=bool(rmsd < 2.0), seed=SEED, exhaustiveness=16, command=cmd,
               receptor_sha256=sha(TARGETS["FXR"]["receptor"]), vina_sha256=sha(VINA))
    (out_dir / "fxr_gate.json").write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
    return rec


def screen(out_root: Path):
    lig_dir = out_root / "ligands_pdbqt"; lig_dir.mkdir(parents=True, exist_ok=True)
    rows = list(csv.DictReader(open(LIBRARY, encoding="utf-8")))
    results = []
    t0 = time.time()
    for i, row in enumerate(rows, 1):
        name = row["name"].strip()
        herb = row["herb"].strip()
        smiles = row["smiles"].strip()
        safe = re.sub(r"[^A-Za-z0-9_-]+", "_", name)[:40]
        try:
            text = prepare_ligand(smiles)
        except Exception as e:
            results.append(dict(herb=herb, name=name, status=f"prep_failed:{e}"))
            print(f"[{i}/{len(rows)}] {name}: PREP FAILED {e}", flush=True)
            continue
        lq = lig_dir / f"{safe}.pdbqt"; lq.write_text(text)
        for tgt, cfg in TARGETS.items():
            tdir = out_root / "docking" / tgt; tdir.mkdir(parents=True, exist_ok=True)
            pose = tdir / f"{safe}_out.pdbqt"; log = tdir / f"{safe}.log"
            try:
                cmd, affs = vina_dock(cfg["receptor"], lq, pose, cfg["center"], cfg["size"], log)
                results.append(dict(herb=herb, name=name, target=tgt, status="completed",
                                    best_affinity=affs[0], all_affinities=[round(a, 3) for a in affs],
                                    smiles=smiles, mw=row.get("mw"), logp=row.get("logp"),
                                    hbd=row.get("hbd"), hba=row.get("hba"), rotb=row.get("rotb"),
                                    tpsa=row.get("tpsa"), admet_fail=row.get("admet_fail", ""),
                                    ligand_pdbqt=str(lq), pose=str(pose)))
                print(f"[{i}/{len(rows)}] {name} x {tgt}: {affs[0]:.2f} kcal/mol", flush=True)
            except Exception as e:
                results.append(dict(herb=herb, name=name, target=tgt, status=f"dock_failed:{e}"))
                print(f"[{i}/{len(rows)}] {name} x {tgt}: DOCK FAILED {e}", flush=True)
        (out_root / "screening_results.partial.json").write_text(
            json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
    meta = dict(seed=SEED, exhaustiveness=EXHAUSTIVENESS, cpu=CPU, vina_sha256=sha(VINA),
                library=str(LIBRARY), library_sha256=sha(LIBRARY), targets={
                    t: dict(receptor_sha256=sha(c["receptor"]), center=list(c["center"]),
                            size=list(c["size"]), gate_note=c["gate_note"]) for t, c in TARGETS.items()},
                elapsed_sec=round(time.time() - t0, 1), n_ligands=len(rows))
    (out_root / "screening_results.json").write_text(
        json.dumps(dict(meta=meta, results=results), ensure_ascii=False, indent=1), encoding="utf-8")
    print("DONE", len(results), "records in", round(time.time() - t0), "s", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--gate", action="store_true")
    ap.add_argument("--screen", action="store_true")
    a = ap.parse_args()
    if a.gate or a.screen:
        rec = fxr_gate(HERE / "gate")
        print("FXR gate:", json.dumps({k: rec[k] for k in ("best_affinity", "rmsd_no_alignment", "gate_pass")}), flush=True)
        if not rec["gate_pass"]:
            sys.exit("FXR gate FAILED - screening blocked")
    if a.screen:
        screen(HERE)
