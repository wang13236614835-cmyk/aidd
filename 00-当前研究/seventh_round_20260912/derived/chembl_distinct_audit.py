# -*- coding: utf-8 -*-
"""精确值活性去重统计：distinct molecules / assays / 文献来源，评估真实可建模规模"""
import json, time, urllib.request, urllib.parse, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
BASE = "https://www.ebi.ac.uk/chembl/api/data"

def get_all(target, std_types):
    mols, assays, docs, recs = set(), set(), set(), 0
    for std in std_types:
        offset = 0
        while True:
            params = {"target_chembl_id": target, "standard_type": std,
                      "standard_relation": "=", "limit": 1000, "offset": offset}
            url = BASE + "/activity.json?" + urllib.parse.urlencode(params)
            try:
                with urllib.request.urlopen(url, timeout=90) as r:
                    d = json.loads(r.read().decode('utf-8'))
            except Exception as e:
                print(f"  ERROR {target} {std} offset={offset}: {e}"); break
            acts = d.get("activities", [])
            for a in acts:
                if a.get("molecule_chembl_id"): mols.add(a["molecule_chembl_id"])
                if a.get("assay_chembl_id"): assays.add(a["assay_chembl_id"])
                if a.get("document_chembl_id"): docs.add(a["document_chembl_id"])
                recs += 1
            total = d.get("page_meta", {}).get("total_count", 0)
            offset += 1000
            if offset >= total or not acts: break
            time.sleep(0.5)
    return {"distinct_molecules": len(mols), "distinct_assays": len(assays),
            "distinct_documents": len(docs), "records": recs}

PANEL = {
    "FASN_human": ("CHEMBL4158", ["IC50", "Ki", "Kd"]),
    "THRB_human": ("CHEMBL1947", ["IC50", "EC50", "Ki", "Kd"]),
    "FXR_human":  ("CHEMBL2047", ["IC50", "EC50", "Kd"]),
    "KEAP1_human":("CHEMBL2069156", ["IC50", "EC50", "Ki", "Kd"]),
    "ACACB_human":("CHEMBL4829", ["IC50"]),
    "ACACA_human":("CHEMBL3351", ["IC50"]),
    "THRA_human": ("CHEMBL2035", ["IC50", "EC50", "Ki", "Kd"]),
}
out = {}
for name, (tid, stds) in PANEL.items():
    r = get_all(tid, stds)
    out[name] = {"target_chembl_id": tid, "std_types": stds, **r}
    print(f"{name}: {r}")
    time.sleep(1)
with open("D:/zcode-workspace/aidd-repo-work/00-当前研究/seventh_round_20260912/raw/chembl_distinct_molecules.json", "w", encoding="utf-8") as f:
    json.dump({"query_date": "2026-09-12", "results": out}, f, ensure_ascii=False, indent=2)
print("saved")
