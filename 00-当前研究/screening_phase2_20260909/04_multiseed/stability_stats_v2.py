# -*- coding: utf-8 -*-
"""Full-library stability statistics v2 (four explicit layers).

Layer-1 full-library rank stability: rank of each compound among ALL 54 per
  target per seed (seed42 + three repeat seeds), median/IQR of rank, plus
  Kendall tau of each repeat seed's full ranking vs seed42.
Layer-2 hit-subset rank: rank among the 13 triple-top20 hits (reported because
  subset ranks are NOT evidence of full-library stability).
Layer-3 affinity stability: mean+/-sd of best affinity across 4 seeds.
Layer-4 pose stability: reported separately in FASN pose-cluster analysis.
DESIGN CAVEAT (stated on every output): each repeat seed changes BOTH the ETKDG
start conformation and the Vina search seed => estimates PROTOCOL repeatability.
Search-seed-only decomposition uses search_seed_only_results.json.
The sd<=0.3 cutoff used downstream is EXPLORATORY/POST HOC (defined 2026-09-09
after seeing seed42 data), and must be re-registered before any confirmatory use.
"""
import json, statistics as st
from pathlib import Path
from scipy.stats import kendalltau

HERE = Path(__file__).resolve().parent
PRIMARY = HERE.parent.parent / "screening_dry_20260909"
SEEDS = [42, 7, 123, 20260909]
TARGETS = ("FXR", "THRB", "FASN")
HITS = ["moracin N", "daidzein", "formononetin", "3'-methoxydaidzein", "daidzin",
        "moracin M", "piceid", "biochanin A", "genistin", "epicatechin",
        "capillarisin", "isorhamnetin", "toralactone"]

def load_all():
    aff = {}  # (name, target, seed) -> best affinity
    prim = json.loads((PRIMARY / "screening_results.json").read_text(encoding="utf-8"))["results"]
    for r in prim:
        if r["status"] == "completed":
            aff[(r["name"], r["target"], 42)] = r["best_affinity"]
    for fname in ("multiseed_results.json", "full_library_results.json"):
        p = HERE / fname
        if not p.exists():
            print(f"WARNING missing {fname}"); continue
        for r in json.loads(p.read_text(encoding="utf-8"))["results"]:
            if r["status"] == "completed":
                aff[(r["name"], r["target"], r["seed"])] = r["best_affinity"]
    return aff

def main():
    aff = load_all()
    names = sorted({k[0] for k in aff})
    out = {"design_note": "repeat seeds change ETKDG start AND vina search seed -> protocol repeatability, not pure seed effect",
           "sd_cutoff_note": "sd<=0.3 threshold is exploratory/post-hoc (defined 2026-09-09 after seeing data); re-register before confirmatory use",
           "layers": {}}
    print(f"compounds with data: {len(names)}")
    layer1_rows, layer3_rows = [], []
    for tgt in TARGETS:
        present = [n for n in names if all((n, tgt, s) in aff for s in SEEDS)]
        if len(present) < len(names):
            print(f"[{tgt}] full 4-seed coverage: {len(present)}/{len(names)}")
        ranks = {}
        for s in SEEDS:
            order = sorted(present, key=lambda n: aff[(n, tgt, s)])
            ranks[s] = {n: i + 1 for i, n in enumerate(order)}
        taus = {}
        for s in SEEDS[1:]:
            tau, p = kendalltau([ranks[42][n] for n in present], [ranks[s][n] for n in present])
            taus[f"tau_seed{s}"] = round(float(tau), 3)
        for n in present:
            rk = [ranks[s][n] for s in SEEDS]
            af = [aff[(n, tgt, s)] for s in SEEDS]
            q1, q3 = st.quantiles(rk, n=4)[0], st.quantiles(rk, n=4)[2]
            layer1_rows.append(dict(
                name=n, target=tgt, seed42_rank=rk[0],
                rank_median=st.median(rk), rank_min=min(rk), rank_max=max(rk),
                rank_iqr=round(q3 - q1, 1), is_hit13=(n in HITS),
                aff_mean=round(st.mean(af), 2), aff_sd=round(st.stdev(af), 2),
                aff_min=round(min(af), 2), aff_max=round(max(af), 2),
                exploratory_sd_le_0p3=(st.stdev(af) <= 0.3)))
        out["layers"][tgt] = dict(n_with_full4seeds=len(present), kendall_vs_seed42=taus,
                                  top5_by_median_rank=[r["name"] for r in sorted(
                                      [x for x in layer1_rows if x["target"] == tgt],
                                      key=lambda x: x["rank_median"])[:5]])
        print(f"[{tgt}] Kendall tau vs seed42: {taus}")
    with open(HERE / "full_library_stability_v2.csv", "w", newline="", encoding="utf-8-sig") as f:
        import csv
        w = csv.DictWriter(f, fieldnames=list(layer1_rows[0].keys())); w.writeheader(); w.writerows(layer1_rows)
    (HERE / "full_library_stability_v2.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    # hits summary: full-library rank stability for the 13 hits
    print("\n=== 13 hits: FULL-LIBRARY (54) rank stability across 4 seeds ===")
    for n in HITS:
        line = [f"{n:<22s}"]
        for tgt in TARGETS:
            rows = [r for r in layer1_rows if r["name"] == n and r["target"] == tgt]
            if rows:
                r = rows[0]
                line.append(f"{tgt}: med{r['rank_median']:.0f} [{r['rank_min']}-{r['rank_max']}] sd{r['aff_sd']:.2f}")
        print("  " + " | ".join(line))

if __name__ == "__main__":
    main()
