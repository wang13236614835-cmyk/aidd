# -*- coding: utf-8 -*-
"""Full-library protocol-repeatability runs: remaining 41 library compounds x 3
targets x seeds {7,123,20260909}.

Scope note: each seed changes BOTH the ETKDG ligand start conformation AND the
Vina search seed (same protocol as primary screen seed42). Results therefore
estimate PROTOCOL repeatability, not a pure search-seed effect.
"""
import csv, json, re, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "screening_dry_20260909"))
from run_screening import prepare_ligand, vina_dock, TARGETS
from rdkit import RDLogger
RDLogger.DisableLog("rdApp.*")

HERE = Path(__file__).resolve().parent
LIB = Path(TARGETS["THRB"]["receptor"]).parents[2] / "data/tcm/np_library_filtered.csv"
ALREADY = ["moracin N", "daidzein", "formononetin", "3'-methoxydaidzein", "daidzin",
           "moracin M", "piceid", "biochanin A", "genistin", "epicatechin",
           "capillarisin", "isorhamnetin", "toralactone"]
SEEDS = [7, 123, 20260909]

def main():
    rows = list(csv.DictReader(open(LIB, encoding="utf-8")))
    todo = [r for r in rows if r["name"].strip() not in ALREADY]
    print(f"remaining compounds: {len(todo)}", flush=True)
    results, t0 = [], time.time()
    for i, row in enumerate(todo, 1):
        name, safe = row["name"].strip(), re.sub(r"[^A-Za-z0-9_-]+", "_", row["name"].strip())[:40]
        for seed in SEEDS:
            text = prepare_ligand(row["smiles"].strip(), seed=seed)
            sp = HERE / "ligands" / f"{safe}_seed{seed}.pdbqt"
            sp.parent.mkdir(exist_ok=True); sp.write_text(text)
            for tgt, cfg in TARGETS.items():
                tdir = HERE / "docking" / tgt; tdir.mkdir(parents=True, exist_ok=True)
                pose, log = tdir / f"{safe}_seed{seed}_out.pdbqt", tdir / f"{safe}_seed{seed}.log"
                try:
                    _, affs = vina_dock(cfg["receptor"], sp, pose, cfg["center"], cfg["size"], log)
                    results.append(dict(name=name, herb=row["herb"], target=tgt, seed=seed,
                                        status="completed", best_affinity=affs[0]))
                    print(f"[{i}/{len(todo)}] {name} x {tgt} seed{seed}: {affs[0]:.2f}", flush=True)
                except Exception as e:
                    results.append(dict(name=name, target=tgt, seed=seed, status=f"failed:{e}"))
                    print(f"[{i}/{len(todo)}] {name} x {tgt} seed{seed}: FAILED {e}", flush=True)
            (HERE / "full_library_results.partial.json").write_text(json.dumps(results), encoding="utf-8")
    (HERE / "full_library_results.json").write_text(
        json.dumps(dict(seeds=SEEDS, n_compounds=len(todo), elapsed=round(time.time() - t0, 1),
                        results=results), ensure_ascii=False), encoding="utf-8")
    print("DONE", len(results), "in", round(time.time() - t0), "s", flush=True)

if __name__ == "__main__":
    main()
