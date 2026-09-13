"""Pose-recovery check of DockScope-platform redocking vs CCD-corrected crystal references.

Protocol mirrors validate_docking.py: per-mode RDKit CalcRMS (no alignment) of the
Meeko-rebuilt pose against Chem.RemoveHs(CCD-corrected crystal ligand); gate < 2.0 A.
DockScope runs: AIDD-verify-THRB-2J4A-OEF-redock, AIDD-verify-FASN-7MHD-ZEP-redock.
"""
import csv, hashlib, json, re, shutil
from pathlib import Path
from rdkit import Chem
from rdkit.Chem import rdMolAlign
from meeko import PDBQTMolecule
from meeko.rdkit_mol_create import RDKitMolCreate

HERE = Path(__file__).resolve().parent
JOBS = Path(r"C:\DockScopeData\workspace\dockscope\data\jobs")

RUNS = {
    "THRB": dict(job="AIDD-verify-THRB-2J4A-OEF-redock", ref=HERE / "THRB_corrected_crystal.sdf",
                 project_rmsd=0.7192312541304148, project_pass=True),
    "FASN": dict(job="AIDD-verify-FASN-7MHD-ZEP-redock", ref=HERE / "FASN_corrected_crystal.sdf",
                 project_rmsd=2.076567383188259, project_pass=False),
}

def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def modes(pdbqt_text: str):
    """Yield MODEL..ENDMDL blocks in file order (= vina affinity order)."""
    for m in re.finditer(r"MODEL.*?ENDMDL", pdbqt_text, re.S):
        yield m.group(0) + "\n"

def main():
    out = {}
    for target, cfg in RUNS.items():
        job_dir = next(p for p in sorted(JOBS.glob(cfg["job"] + "_*")) if p.is_dir())
        task_dir = next((job_dir / "run" / "tasks").iterdir())
        docked = task_dir / "engines" / "vina_cpu" / "C1" / "docked.pdbqt"
        results_csv = job_dir / "run" / "all_docking_results.csv"
        row = next(csv.DictReader(open(results_csv, encoding="utf-8")))
        ref_block = cfg["ref"].read_text(encoding="utf-8")
        ref = Chem.RemoveHs(Chem.MolFromMolBlock(ref_block, removeHs=False))
        text = docked.read_text()
        per_mode = []
        for i, block in enumerate(modes(text), 1):
            mol = RDKitMolCreate.from_pdbqt_mol(PDBQTMolecule(block, skip_typing=True))[0]
            pose = Chem.RemoveHs(mol)
            per_mode.append(float(rdMolAlign.CalcRMS(pose, ref)))
        # archive provenance copies next to this script
        prov_dir = HERE / f"dockscope_{target}"
        prov_dir.mkdir(exist_ok=True)
        for f in (docked, task_dir / "pockets.json", results_csv, job_dir / "job.json"):
            shutil.copy2(f, prov_dir / f.name)
        best = per_mode[0]
        best_overall = min(per_mode)
        out[target] = {
            "dockscope_job_id": job_dir.name,
            "vina_best_affinity_kcal_mol": float(row["best_score"]),
            "pocket": json.loads((task_dir / "pockets.json").read_text(encoding="utf-8"))["pockets"][0],
            "rmsd_no_alignment_per_mode_A": [round(r, 4) for r in per_mode],
            "rmsd_best_mode_A": round(best, 4),
            "pose_threshold_pass_best_mode": bool(best < 2.0),
            "rmsd_min_any_mode_A": round(best_overall, 4),
            "project_ref_rmsd_seed42_A": round(cfg["project_rmsd"], 4),
            "project_ref_pass": cfg["project_pass"],
            "docked_sha256": sha(docked),
            "receptor_input_sha256": row["protein_sha256"],
            "ligand_input_sha256": row["ligand_sha256"],
            "command": row["command"],
        }
        print(target, "modes:", [round(r, 3) for r in per_mode],
              "best-mode", round(best, 3), "PASS" if best < 2 else "FAIL", flush=True)
    (HERE / "dockscope_redock_verification.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

if __name__ == "__main__":
    main()
