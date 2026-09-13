"""Fifth-round WT TRB discrimination gate (preregistered 2026-09-12).

Reuses the project-standard ligand PDBQTs prepared for the historical 2J4A gate
(p0_refs/gate_run/*.pdbqt; RDKit ETKDGv3 seed42 -> MMFF -> Meeko), docks them
against the 3GWS-derived WT receptor (H1Valid WTheavy, sha256 ce0390...),
T3 crystal box, Vina 1.2.7, exhaustiveness 8, seed 20260912, and computes the
locked metrics. Selection is re-derived deterministically from
chembl_tr_reference_raw.json per the preregistration (same rule as P0 doc).
"""
import json, math, os, random, re, subprocess, sys, time
from pathlib import Path

ROOT = Path(r"D:\zcode-workspace\aidd-repo-work\00-当前研究\fifth_round_20260912")
GATE = ROOT / "derived" / "wt_gate_run"
GATE.mkdir(parents=True, exist_ok=True)
VINA = r"D:\dockscope\DockScopeLicensed\resources\tools\vina.exe"
REC_SRC = Path(r"C:\DockScopeData\workspace\dockscope\data\jobs\H1Valid_20260910_104825_329168\run\prepared\proteins\WTheavy\receptor.pdbqt")
REC = GATE / "receptor_WTheavy_3GWS.pdbqt"
LIGDIR = Path(r"D:\zcode-workspace\p0_refs\gate_run")
REF = json.loads(Path(r"D:\zcode-workspace\p0_refs\chembl_tr_reference_raw.json").read_text(encoding="utf-8"))
BOX = ["--center_x", "5.157", "--center_y", "20.080", "--center_z", "29.010",
       "--size_x", "22.156", "--size_y", "19.867", "--size_z", "20.893"]
SEED = 20260912
CPU = 8

if not REC.exists():
    import shutil
    shutil.copy2(REC_SRC, REC)

def sha256(p: Path) -> str:
    import hashlib
    return hashlib.sha256(p.read_bytes()).hexdigest()

trb = REF["TRB_human"]
actives, smiles = trb["actives"], trb["smiles"]

def layer(v):
    return 0 if v <= 10 else (1 if v <= 100 else 2)

by_layer = {0: [], 1: [], 2: []}
for mid, (tag, val, units, st, doc) in actives.items():
    if mid in smiles:
        by_layer[layer(val)].append((val, mid))
sel = []
for k in (0, 1, 2):
    by_layer[k].sort()
    sel += [(m, actives[m][1]) for _, m in by_layer[k][:15]]
negs = [(m, v[1]) for m, v in trb["inactives_floor"].items() if m in smiles]
print("selected actives:", len(sel), "per-layer:", [len(by_layer[k][:15]) for k in (0, 1, 2)], "floor negatives:", len(negs), flush=True)

records = []
def dock(pq: Path, name, label, extra):
    lg = GATE / f"{name}.log"
    out = GATE / f"{name}_out.pdbqt"
    cmd = [VINA, "--receptor", str(REC), "--ligand", str(pq), *BOX,
           "--cpu", str(CPU), "--exhaustiveness", "8", "--num_modes", "9",
           "--seed", str(SEED), "--out", str(out)]
    t0 = time.time()
    r = subprocess.run(cmd, capture_output=True, timeout=1800)
    stdout = (r.stdout or b"").decode("utf-8", errors="replace")
    stderr = (r.stderr or b"").decode("utf-8", errors="replace")
    lg.write_text(stdout + stderr, encoding="utf-8")
    ms = re.findall(r"^\s+\d+\s+(-?\d+\.\d+)", stdout, re.M)
    best = float(ms[0]) if ms else None
    rec = {"id": name, "label": label, "score": best, "returncode": r.returncode,
           "n_modes": len(ms), "seconds": round(time.time() - t0, 1), **extra}
    records.append(rec)
    print(name, label, best, f"{rec['seconds']}s", flush=True)

missing = []
for mid, val in sel:
    pq = LIGDIR / f"{mid}.pdbqt"
    if pq.exists():
        dock(pq, mid, "active", {"potency_nM": val, "layer": layer(val)})
    else:
        missing.append(mid); records.append({"id": mid, "label": "active", "score": None, "prep_missing": True})
for mid, val in negs:
    pq = LIGDIR / f"{mid}_neg.pdbqt"
    if pq.exists():
        dock(pq, mid + "_neg", "negative_floor", {"floor_nM": val})
    else:
        missing.append(mid); records.append({"id": mid, "label": "negative_floor", "score": None, "prep_missing": True})
# reference anchors (reported separately, not in ROC)
for nm in ("T3_liothyronine", "resmetirom"):
    pq = LIGDIR / f"{nm}.pdbqt"
    if pq.exists():
        dock(pq, nm, "anchor", {})

json.dump(records, open(GATE / "raw_results.json", "w"), indent=1)

act = [r for r in records if r["label"] == "active" and r.get("score") is not None]
negv = [r for r in records if r["label"] == "negative_floor" and r.get("score") is not None]
# classifier direction locked BEFORE metrics: positive_score = -vina_score
def auc_mannwhitney(pos, neg):
    # mid-rank tie handling
    allv = sorted(pos + neg)
    rank = {}
    i = 0
    while i < len(allv):
        j = i
        while j + 1 < len(allv) and allv[j + 1] == allv[i]:
            j += 1
        r = (i + j) / 2 + 1
        for k in range(i, j + 1):
            rank[allv[k]] = r
        i = j + 1
    sp = sum(rank[v] for v in pos)
    n1, n2 = len(pos), len(neg)
    return (sp - n1 * (n1 + 1) / 2) / (n1 * n2)

pos_scores = [-r["score"] for r in act]
neg_scores = [-r["score"] for r in negv]
roc = auc_mannwhitney(pos_scores, neg_scores)

def pr_auc(pos, neg):
    # average precision (positive = higher positive_score)
    rows = sorted([(s, 1) for s in pos] + [(s, 0) for s in neg], key=lambda x: -x[0])
    P = len(pos)
    tp = fp = 0
    ap = 0.0
    prev_rec = 0.0
    for s, y in rows:
        if y: tp += 1
        else: fp += 1
        prec = tp / (tp + fp)
        rec_ = tp / P
        ap += prec * (rec_ - prev_rec)
        prev_rec = rec_
    return ap

pr = pr_auc(pos_scores, neg_scores)

def ef_topk(act, negv, K=15):
    rows = sorted(act + negv, key=lambda r: -(-r["score"]))
    # mid-rank on ties: expand to ranked list with deterministic id order for reporting only
    rows = sorted(act + negv, key=lambda r: ((r["score"]), r["id"]))
    rows = rows[::-1]
    top = rows[:K]
    hit = sum(1 for r in top if r["label"] == "active")
    prev = len(act) / (len(act) + len(negv))
    # mid-rank tie handling: count all records tied with the K-th score
    if len(rows) > K:
        kth = rows[K - 1]["score"]
        tied = [r for r in rows[K:] if r["score"] == kth]
        hit_tied = sum(1 for r in tied if r["label"] == "active")
        eff_k = K + len(tied)
        eff_hit = hit + hit_tied
    else:
        eff_k, eff_hit = len(rows), hit
    return {"K_requested": K, "effective_top_n": eff_k, "actives_in_top": eff_hit,
            "top_fraction": (eff_hit / len(act)) / (eff_k / len(rows)),
            "baseline_positive_rate": prev}

ef = ef_topk(act, negv, 15)

def bootstrap_ci(pos, neg, n=10000, seed=SEED):
    rng = random.Random(seed)
    aucs, prs = [], []
    valid = 0
    for _ in range(n):
        p = [rng.choice(pos) for _ in range(len(pos))]
        q = [rng.choice(neg) for _ in range(len(neg))]
        try:
            aucs.append(auc_mannwhitney(p, q))
            prs.append(pr_auc(p, q))
            valid += 1
        except ZeroDivisionError:
            continue
    aucs.sort(); prs.sort()
    return {"roc_ci95": [aucs[int(0.025 * valid)], aucs[int(0.975 * valid)]],
            "pr_ci95": [prs[int(0.025 * valid)], prs[int(0.975 * valid)]],
            "valid_replicates": valid}

ci = bootstrap_ci(pos_scores, neg_scores)

layer_auc = {}
for L in (0, 1, 2):
    sub = [r for r in act if r.get("layer") == L]
    if len(sub) >= 5:
        layer_auc[f"layer_{L}"] = round(auc_mannwhitney([-r["score"] for r in sub], neg_scores), 3)

out = {
 "run": {"date_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
         "receptor": str(REC), "receptor_sha256": sha256(REC),
         "box_center": [5.157, 20.080, 29.010], "box_size": [22.156, 19.867, 20.893],
         "vina": "1.2.7 (DockScope bundled vina.exe)", "seed": SEED,
         "exhaustiveness": 8, "cpu": CPU, "num_modes": 9,
         "score_direction": "positive_score = -vina_score (more positive = predicted active)",
         "tie_handling": "mid-rank Mann-Whitney; EF@Top15 includes all records tied with the 15th score",
         "bootstrap": "stratified resampling within labels, 10000 replicates, seed 20260912"},
 "n_active_docked": len(act), "n_negative_docked": len(negv),
 "missing_ligand_prep": missing,
 "ROC_AUC": round(roc, 4), "PR_AUC": round(pr, 4),
 "ROC_AUC_ci95": [round(x, 4) for x in ci["roc_ci95"]],
 "PR_AUC_ci95": [round(x, 4) for x in ci["pr_ci95"]],
 "bootstrap_valid": ci["valid_replicates"],
 "EF_at_Top15": {k: (round(v, 4) if isinstance(v, float) else v) for k, v in ef.items()},
 "layer_AUC": layer_auc,
 "anchors": {r["id"]: r["score"] for r in records if r["label"] == "anchor" and r.get("score") is not None},
}
json.dump(out, open(GATE / "gate_metrics.json", "w"), indent=1)
print(json.dumps(out, indent=1), flush=True)
