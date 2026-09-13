"""Summarize screening results into transparent per-target rankings.

No weighted fusion (audit A11): output is per-target Vina ranking plus an
equal-weight mean-rank column labeled as browsing aid only.
"""
import csv, json
from pathlib import Path

HERE = Path(__file__).resolve().parent
data = json.loads((HERE / "screening_results.json").read_text(encoding="utf-8"))
rows = [r for r in data["results"] if r.get("status") == "completed"]

# long table: one row per ligand x target
long_rows = []
by_target = {}
for r in rows:
    by_target.setdefault(r["target"], []).append(r)
for tgt, lst in by_target.items():
    lst.sort(key=lambda r: r["best_affinity"])
    for rank, r in enumerate(lst, 1):
        long_rows.append(dict(rank_in_target=rank, target=tgt, name=r["name"], herb=r["herb"],
                              best_affinity_kcal_mol=r["best_affinity"],
                              smiles=r["smiles"], mw=r.get("mw"), logp=r.get("logp"),
                              hbd=r.get("hbd"), hba=r.get("hba"), rotb=r.get("rotb"),
                              tpsa=r.get("tpsa"), admet_fail=r.get("admet_fail", "")))
with open(HERE / "results_per_target_long.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(long_rows[0].keys())); w.writeheader(); w.writerows(long_rows)

# wide table: ligand as row, per-target affinity + rank + mean rank (browsing aid only)
targets = ["FXR", "THRB", "FASN"]
info, aff, rk = {}, {}, {}
for tgt, lst in by_target.items():
    for rank, r in enumerate(lst, 1):
        key = (r["herb"], r["name"])
        aff[(key, tgt)] = r["best_affinity"]
        rk[(key, tgt)] = rank
        info[key] = r
wide = []
for key in sorted(info):
    r = info[key]
    row = dict(herb=r["herb"], name=r["name"])
    ranks = []
    for t in targets:
        row[f"{t}_affinity"] = aff.get((key, t))
        row[f"{t}_rank"] = rk.get((key, t))
        if rk.get((key, t)) is not None:
            ranks.append(rk[(key, t)])
    row["mean_rank_equal_weight_browsing_only"] = round(sum(ranks) / len(ranks), 1) if ranks else None
    row["all_three_top20"] = all(rk.get((key, t)) is not None and rk[(key, t)] <= 20 for t in targets)
    row["mw"], row["logp"], row["hbd"], row["hba"], row["rotb"] = r.get("mw"), r.get("logp"), r.get("hbd"), r.get("hba"), r.get("rotb")
    row["tpsa"], row["admet_fail"] = r.get("tpsa"), r.get("admet_fail", "")
    wide.append(row)
wide.sort(key=lambda x: (x["mean_rank_equal_weight_browsing_only"] is None,
                         x["mean_rank_equal_weight_browsing_only"] if x["mean_rank_equal_weight_browsing_only"] is not None else 0))
with open(HERE / "results_summary_wide.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(wide[0].keys())); w.writeheader(); w.writerows(wide)

print(f"completed records: {len(rows)}  (expect 162 = 54 x 3)")
print(f"docked ligands per target: " + ", ".join(f"{t}={len(l)}" for t, l in by_target.items()))
print("\n=== top 10 per target (Vina best affinity, kcal/mol) ===")
for tgt in targets:
    lst = by_target.get(tgt, [])
    print(f"\n[{tgt}]  (gate: {data['meta']['targets'][tgt]['gate_note']})")
    for rank, r in enumerate(lst[:10], 1):
        print(f"  {rank:2d}. {r['name']:<22s} {r['herb']:<24s} {r['best_affinity']:.2f}")
print("\n=== ligands in top-20 of ALL three targets ===")
for row in wide:
    if row["all_three_top20"]:
        print(f"  {row['name']:<22s} {row['herb']:<24s} mean_rank={row['mean_rank_equal_weight_browsing_only']}")
