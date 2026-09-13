# -*- coding: utf-8 -*-
"""T3: merge seed42 primary screen with 3 extra seeds; per-ligand per-target
affinity mean+/-sd and rank stability (median, IQR) across 4 seeds.
Rank computed within the 54-compound library per target per seed (seed42 = full
library; other seeds only the 13 hits, so within-hit ranks are absolute positions
from seed42 full ranking held fixed - ranks for hits across seeds are recomputed
among the 13 hits for a self-consistent stability measure, plus seed42 full-library
rank retained for context).
"""
import csv, json, statistics as st
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRIMARY = HERE.parent.parent / "screening_dry_20260909"
SEEDS = [42, 7, 123, 20260909]

# seed42 full-library affinities (primary screen)
primary = json.loads((PRIMARY / "screening_results.json").read_text(encoding="utf-8"))["results"]
full = {(r["name"], r["target"]): r["best_affinity"] for r in primary if r["status"] == "completed"}
full_rank = {}
for tgt in ("FXR", "THRB", "FASN"):
    items = sorted(((v, k[0]) for k, v in full.items() if k[1] == tgt))
    full_rank.update({(name, tgt): i + 1 for i, (_, name) in enumerate(items)})

multi = json.loads((HERE / "multiseed_results.json").read_text(encoding="utf-8"))["results"]
extra = {(r["name"], r["target"], r["seed"]): r["best_affinity"] for r in multi if r["status"] == "completed"}

hits = sorted({r["name"] for r in multi})
rows = []
for name in hits:
    for tgt in ("FXR", "THRB", "FASN"):
        affs = [full[(name, tgt)]] + [extra[(name, tgt, s)] for s in SEEDS[1:]]
        ranks13 = []
        # rank among the 13 hits per seed
        peers = {h: [full.get((h, tgt))] + [extra.get((h, tgt, s)) for s in SEEDS[1:]] for h in hits}
        for si in range(4):
            order = sorted(range(len(hits)), key=lambda hi: peers[hits[hi]][si])
            ranks13.append(order.index(hits.index(name)) + 1)
        rows.append(dict(
            name=name, target=tgt,
            aff_seed42=round(affs[0], 2), aff_seed7=round(affs[1], 2),
            aff_seed123=round(affs[2], 2), aff_seed20260909=round(affs[3], 2),
            aff_mean=round(st.mean(affs), 2), aff_sd=round(st.stdev(affs), 2),
            aff_range=round(max(affs) - min(affs), 2),
            rank_full_library_seed42=full_rank.get((name, tgt)),
            rank_among13_median=st.median(ranks13),
            rank_among13_iqr=round(st.quantiles(ranks13, n=4)[2] - st.quantiles(ranks13, n=4)[0], 1),
            S1_stable_20_iqr10=bool(st.median(ranks13) <= 20 and
                                    (st.quantiles(ranks13, n=4)[2] - st.quantiles(ranks13, n=4)[0]) <= 10)))

with open(HERE / "multiseed_stability.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)

print(f"records: {len(rows)} (13 hits x 3 targets); failed records: "
      f"{sum(r['status'] != 'completed' for r in multi)}")
print("\n=== affinity stability (mean±sd, range across 4 seeds) ===")
for tgt in ("FXR", "THRB", "FASN"):
    print(f"\n[{tgt}]")
    sub = sorted([r for r in rows if r["target"] == tgt], key=lambda r: r["aff_mean"])
    for r in sub:
        flag = "" if r["aff_sd"] <= 0.3 else "  <-- sd>0.3"
        print(f"  {r['name']:<22s} {r['aff_mean']:+.2f} ±{r['aff_sd']:.2f} "
              f"(range {r['aff_range']:.2f}) rank13 med={r['rank_among13_median']:.0f} "
              f"IQR={r['rank_among13_iqr']}{flag}")
sd_high = [r for r in rows if r["aff_sd"] > 0.3]
print(f"\ncompounds with sd>0.3 kcal/mol: {sorted({r['name'] for r in sd_high})}")
print("S1 (median<=20 & IQR<=10) pass count:", sum(r["S1_stable_20_iqr10"] for r in rows), "/", len(rows))
