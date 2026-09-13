# -*- coding: utf-8 -*-
"""Multi-seed robustness recheck for the 13 triple-top20 hits (seeds 7/123/20260909).

Seed 42 already exists in screening_dry_20260909 (primary screen). Output feeds a
per-ligand mean+/-sd of best affinity and rank-stability table. Positive controls
are the co-crystal ligands (gate evidence already archived separately).
"""
import csv, json, re, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "screening_dry_20260909"))
from run_screening import prepare_ligand, vina_dock, TARGETS, VINA, SEED  # reuse verified pipeline
from rdkit import RDLogger
RDLogger.DisableLog("rdApp.*")

HERE = Path(__file__).resolve().parent
PRIMARY = Path(__file__).resolve().parents[1] / "screening_dry_20260909"
HITS = ["moracin N", "daidzein", "formononetin", "3'-methoxydaidzein", "daidzin",
        "moracin M", "piceid", "biochanin A", "genistin", "epicatechin",
        "capillarisin", "isorhamnetin", "toralactone"]
SEEDS = [7, 123, 20260909]

def main():
    lig_dir = PRIMARY / "ligands_pdbqt"
    rows = {r["name"].strip(): r for r in csv.DictReader(
        open(Path(TARGETS["THRB"]["receptor"]).parents[2] / "data/tcm/np_library_filtered.csv", encoding="utf-8"))}
    results = []
    t0 = time.time()
    for name in HITS:
        safe = re.sub(r"[^A-Za-z0-9_-]+", "_", name)[:40]
        lq = lig_dir / f"{safe}.pdbqt"
        if not lq.exists():  # reprepare from SMILES with per-seed embedding
            for seed in SEEDS:
                pass
        for seed in SEEDS:
            # independent 3D start per seed (embedding depends on seed)
            text = prepare_ligand(rows[name]["smiles"].strip(), seed=seed)
            sp = HERE / "ligands" / f"{safe}_seed{seed}.pdbqt"
            sp.parent.mkdir(exist_ok=True); sp.write_text(text)
            for tgt, cfg in TARGETS.items():
                tdir = HERE / "docking" / tgt; tdir.mkdir(parents=True, exist_ok=True)
                pose = tdir / f"{safe}_seed{seed}_out.pdbqt"; log = tdir / f"{safe}_seed{seed}.log"
                try:
                    cmd, affs = vina_dock(cfg["receptor"], sp, pose, cfg["center"], cfg["size"], log)
                    results.append(dict(name=name, herb=rows[name]["herb"], target=tgt, seed=seed,
                                        status="completed", best_affinity=affs[0],
                                        all_affinities=[round(a, 3) for a in affs]))
                    print(f"{name} x {tgt} seed{seed}: {affs[0]:.2f}", flush=True)
                except Exception as e:
                    results.append(dict(name=name, target=tgt, seed=seed, status=f"failed:{e}"))
                    print(f"{name} x {tgt} seed{seed}: FAILED {e}", flush=True)
            (HERE / "multiseed_results.partial.json").write_text(
                json.dumps(results, ensure_ascii=False), encoding="utf-8")
    (HERE / "multiseed_results.json").write_text(
        json.dumps(dict(seeds=SEEDS, primary_seed=42, vina_sha256=None, n=len(results),
                        elapsed=round(time.time() - t0, 1), results=results), ensure_ascii=False, indent=1),
        encoding="utf-8")
    print("DONE", len(results), "in", round(time.time() - t0), "s", flush=True)

if __name__ == "__main__":
    main()
