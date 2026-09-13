# -*- coding: utf-8 -*-
"""战略收敛轮：竞争靶点 ChEMBL 数据可建模性审计（只读查询，全部留痕）"""
import json, time, urllib.request, urllib.parse, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
BASE = "https://www.ebi.ac.uk/chembl/api/data"

def get(path, params):
    url = BASE + path + "?" + urllib.parse.urlencode(params)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return json.loads(r.read().decode('utf-8'))
        except Exception as e:
            if attempt == 2: return {"_error": str(e)}
            time.sleep(3)

# 靶点面板：来自本轮竞争路线 A/B/C/D + ACC
PANEL = {
    "FASN_human": "CHEMBL4158",
    "THRB_human": "CHEMBL1947",
    "THRA_human": "CHEMBL2035",
    "FXR_human":  "CHEMBL2047",
    "ACACA_human": None,   # 需先查
    "ACACB_human": None,
    "KEAP1_human": None,
}
# 先搜索不确定的靶点
for name in ["Acetyl-CoA carboxylase 1", "Acetyl-CoA carboxylase 2", "Kelch-like ECH-associated protein 1"]:
    d = get("/target/search.json", {"q": name, "limit": 10})
    hits = []
    for t in d.get("targets", []):
        if t.get("organism") == "Homo sapiens" and t.get("target_type") == "SINGLE PROTEIN":
            hits.append((t["target_chembl_id"], t["pref_name"]))
    print(f"SEARCH [{name}] human single-protein hits: {hits}")
    if hits:
        key = {"Acetyl-CoA carboxylase 1": "ACACA_human",
               "Acetyl-CoA carboxyclase 2": "ACACB_human",
               "Acetyl-CoA carboxylase 2": "ACACB_human",
               "Kelch-like ECH-associated protein 1": "KEAP1_human"}[name]
        PANEL[key] = hits[0][0]

results = {}
log = []
for name, tid in PANEL.items():
    if not tid:
        results[name] = {"target_chembl_id": None, "note": "no human single-protein entry found"}
        continue
    # 总活性数
    d = get("/activity.json", {"target_chembl_id": tid, "limit": 1})
    total = d.get("page_meta", {}).get("total_count")
    # 精确值(=) 且有标准 potency 的建模子集，按常用类型
    by_type = {}
    for std in ["IC50", "EC50", "Ki", "Kd", "AC50", "Potency"]:
        d2 = get("/activity.json", {"target_chembl_id": tid, "standard_type": std,
                                     "standard_relation": "=", "limit": 1})
        by_type[std] = d2.get("page_meta", {}).get("total_count")
    # 分子数（去重）:用 activity 的 distinct molecule count 不直接给，取 exact IC50/Ki/Kd 合并下载计数
    results[name] = {"target_chembl_id": tid, "total_activities": total,
                     "exact_eq_by_type": by_type}
    log.append({"target": name, "target_chembl_id": tid, "total_activities": total,
                "exact_eq_by_type": by_type})
    print(f"{name} ({tid}): total={total}, exact(=) IC50={by_type.get('IC50')} EC50={by_type.get('EC50')} Ki={by_type.get('Ki')} Kd={by_type.get('Kd')} AC50={by_type.get('AC50')} Potency={by_type.get('Potency')}")
    time.sleep(1)

out_dir = "D:/zcode-workspace/aidd-repo-work/00-当前研究/seventh_round_20260912"
with open(out_dir + "/raw/chembl_target_panel_audit.json", "w", encoding="utf-8") as f:
    json.dump({"query_date": "2026-09-12", "panel": results}, f, ensure_ascii=False, indent=2)
with open(out_dir + "/logs/chembl_target_panel_audit.log", "w", encoding="utf-8") as f:
    json.dump(log, f, ensure_ascii=False, indent=2)
print("saved raw/chembl_target_panel_audit.json")
