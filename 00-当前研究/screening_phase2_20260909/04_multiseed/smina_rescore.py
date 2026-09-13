# -*- coding: utf-8 -*-
"""Orthogonal rescoring (method-sensitivity check): smina --score_only with
vinardo scoring on the seed42 best poses of the 13 hits + the three co-crystal
controls. This is FIXED-POSE rescoring (no re-docking): it asks whether the
ranking is robust to the scoring function, given the same poses. It does NOT
validate binding and divergence means scoring-function sensitivity only.
Controls: OEF/ZEP/FEX crystal-pose rescoring as anchors (same box receptors).
"""
import csv, json, re, subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRIMARY = HERE.parent.parent / "screening_dry_20260909"
SMINA = Path(r"D:\dockscope\DockScopeLicensed\resources\tools\smina-runtime\smina.exe")
RECEPTORS = {
    "THRB": Path(r"D:\zcode-workspace\aidd-repo-work\03-课题-MASH研究-v2\docking\receptors\THRB_2J4A.pdbqt"),
    "FASN": Path(r"D:\zcode-workspace\aidd-repo-work\03-课题-MASH研究-v2\docking\receptors\FASN_7MHD.pdbqt"),
    "FXR": Path(r"D:\zcode-workspace\final-aidd-screening\docking\receptors\FXR_LBD_1OSH.pdbqt"),
}
HITS = ["moracin N", "daidzein", "formononetin", "3'-methoxydaidzein", "daidzin",
        "moracin M", "piceid", "biochanin A", "genistin", "epicatechin",
        "capillarisin", "isorhamnetin", "toralactone"]

def best_mode_pose(pose_pdbqt: Path, out_dir: Path, tag: str) -> Path:
    text = pose_pdbqt.read_text(errors="replace").replace("\x00", "")
    m = re.search(r"MODEL.*?ENDMDL", text, re.S)
    block = "\n".join(l.rstrip(" \r\t") for l in m.group(0).splitlines()
                      if l.strip() and not l.strip().startswith(("MODEL", "ENDMDL", "REMARK")))
    out = out_dir / f"{tag}_best.pdbqt"
    out.write_text(block + "\n")
    return out
    return out

def score(receptor: Path, ligand: Path):
    r = subprocess.run([str(SMINA), "--score_only", "--receptor", str(receptor),
                        "--ligand", str(ligand), "--scoring", "vinardo"],
                       capture_output=True, text=True, errors="replace", timeout=300)
    m = re.search(r"Affinity:\s*(-?\d+\.\d+)", r.stdout) or re.search(
        r"Estimated Free Energy of Binding\s*:\s*(-?\d+\.\d+)", r.stdout)
    return (float(m.group(1)) if m else None), r.returncode, r.stdout[-400:] + r.stderr[-200:]

def main():
    tmp = HERE / "rescore_tmp"; tmp.mkdir(exist_ok=True)
    rows = []
    for name in HITS:
        safe = re.sub(r"[^A-Za-z0-9_-]+", "_", name)[:40]
        for tgt, rec in RECEPTORS.items():
            pose = PRIMARY / "docking" / tgt / f"{safe}_out.pdbqt"
            if not pose.exists():
                rows.append(dict(name=name, target=tgt, status="pose_missing")); continue
            lig = best_mode_pose(pose, tmp, f"{safe}_{tgt}")
            val, rc, log = score(rec, lig)
            rows.append(dict(name=name, target=tgt, method="smina_vinardo_score_only",
                             vina_affinity_seed42=None, smina_vinardo=val, returncode=rc,
                             status="completed" if val is not None else f"parse_fail"))
            print(f"{name:<22s} {tgt:<5s} vinardo={val}", flush=True)
    # co-crystal controls (crystal conformers, for anchor context)
    controls = {"THRB_OEF": (RECEPTORS["THRB"], PRIMARY.parent / "validation/dockscope_verify_20260909/input/THRB_initial.pdbqt"),
                "FASN_ZEP": (RECEPTORS["FASN"], PRIMARY.parent / "validation/dockscope_verify_20260909/input/FASN_initial.pdbqt"),
                "FXR_FEX": (RECEPTORS["FXR"], PRIMARY / "gate/FXR_FEX_initial.pdbqt")}
    for tag, (rec, ligq) in controls.items():
        val, rc, _ = score(rec, ligq)
        rows.append(dict(name=tag, target=tag.split("_")[0], method="smina_vinardo_score_only_control",
                         smina_vinardo=val, returncode=rc, status="completed"))
        print(f"CONTROL {tag:<10s} vinardo={val}", flush=True)
    (HERE / "smina_rescore_results.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    # merge vina seed42 affinities for correlation
    prim = json.loads((PRIMARY / "screening_results.json").read_text(encoding="utf-8"))["results"]
    vina = {(r["name"], r["target"]): r["best_affinity"] for r in prim if r["status"] == "completed"}
    pairs = [(vina[(r["name"], r["target"])], r["smina_vinardo"]) for r in rows
             if r.get("smina_vinardo") is not None and (r["name"], r["target"]) in vina]
    if len(pairs) >= 5:
        from scipy.stats import spearmanr
        rho, p = spearmanr([a for a, _ in pairs], [b for _, b in pairs])
        print(f"\nSpearman(vina_seed42_best, smina_vinardo_rescore) over {len(pairs)} pairs: "
              f"rho={rho:.3f} p={p:.4f}")
        meta = dict(n_pairs=len(pairs), spearman_rho=round(float(rho), 3), p=round(float(p), 5),
                    interpretation="fixed-pose scoring-function sensitivity only; not binding validation; "
                                   "divergent compounds flagged for method-sensitivity review")
        (HERE / "smina_rescore_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")

if __name__ == "__main__":
    main()
