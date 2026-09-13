# -*- coding: utf-8 -*-
"""Search-seed-only component: FIX the seed42 ligand start conformer, vary ONLY
the Vina search seed (7/123/20260909) for the 13 hits x 3 targets.
Decomposes the protocol-repeatability variance: same start + different search
seed isolates search stochasticity from ETKDG-start stochasticity.
"""
import csv, json, re, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "screening_dry_20260909"))
from run_screening import vina_dock, TARGETS
from rdkit import RDLogger
RDLogger.DisableLog("rdApp.*")

HERE = Path(__file__).resolve().parent
PRIMARY = HERE.parent.parent / "screening_dry_20260909"
HITS = ["moracin N", "daidzein", "formononetin", "3'-methoxydaidzein", "daidzin",
        "moracin M", "piceid", "biochanin A", "genistin", "epicatechin",
        "capillarisin", "isorhamnetin", "toralactone"]
SEARCH_SEEDS = [7, 123, 20260909]

def main():
    results, t0 = [], time.time()
    for name in HITS:
        safe = re.sub(r"[^A-Za-z0-9_-]+", "_", name)[:40]
        fixed = PRIMARY / "ligands_pdbqt" / f"{safe}.pdbqt"   # seed42 conformer
        assert fixed.exists(), fixed
        for tgt, cfg in TARGETS.items():
            for ss in SEARCH_SEEDS:
                tdir = HERE / "search_seed_only" / tgt; tdir.mkdir(parents=True, exist_ok=True)
                pose = tdir / f"{safe}_q42s{ss}_out.pdbqt"; log = tdir / f"{safe}_q42s{ss}.log"
                try:
                    # patch: vina_dock uses SEED constant; temporarily override
                    import run_screening
                    old = run_screening.SEED; run_screening.SEED = ss
                    _, affs = vina_dock(cfg["receptor"], fixed, pose, cfg["center"], cfg["size"], log)
                    run_screening.SEED = old
                    results.append(dict(name=name, target=tgt, ligand_seed=42, search_seed=ss,
                                        status="completed", best_affinity=affs[0]))
                    print(f"{name} x {tgt} fixedStart q42 search{ss}: {affs[0]:.2f}", flush=True)
                except Exception as e:
                    results.append(dict(name=name, target=tgt, ligand_seed=42, search_seed=ss,
                                        status=f"failed:{e}"))
                    print(f"{name} x {tgt} search{ss}: FAILED {e}", flush=True)
        (HERE / "search_seed_only_results.partial.json").write_text(json.dumps(results), encoding="utf-8")
    (HERE / "search_seed_only_results.json").write_text(
        json.dumps(dict(design="fixed seed42 ETKDG start; vary vina search seed only",
                        n=len(results), elapsed=round(time.time() - t0, 1),
                        results=results), ensure_ascii=False), encoding="utf-8")
    print("DONE", len(results), "in", round(time.time() - t0), "s", flush=True)

if __name__ == "__main__":
    main()
