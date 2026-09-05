# -*- coding: utf-8 -*-
"""
全新数据源勘察 v2（修正API用法）：
1) GEO: esearch gds 用 gse[Filter] 检索Series
2) ChEMBL: activity.json 用过滤参数而非q
3) RCSB: search API v2 用POST
"""
import json, time, urllib.request, urllib.parse

UA = {"User-Agent": "academic-drug-research/2.0 (fresh independent project)",
      "Content-Type": "application/json"}

def get(url, params=None, timeout=60):
    if params:
        url = url + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()

def post(url, body, timeout=90):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=UA, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()

# ---------- 1. GEO ----------
print("[1] GEO Series 检索")
term = ('("steatohepatitis"[Title] OR "NASH"[Title] OR "MASH"[Title] OR "fatty liver"[Title]) '
        'AND "Homo sapiens"[Organism] AND liver[All Fields] AND gse[Filter]')
js = json.loads(get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
                    {"db": "gds", "term": term, "retmax": 60, "retmode": "json"}))
ids = js["esearchresult"]["idlist"]
print(f"  hits: {len(ids)}")
time.sleep(0.6)
out = []
if ids:
    sm = json.loads(get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi",
                        {"db": "gds", "id": ",".join(ids[:60]), "retmode": "json"}))
    for uid in sm["result"]["uids"]:
        r = sm["result"][uid]
        out.append(dict(accession=r.get("accession"),
                        title=(r.get("title") or "")[:120],
                        n_samples=r.get("n_samples"), gtype=str(r.get("gtype") or "?"),
                        gpl=r.get("gpl"), pubdate=str(r.get("pubdate") or "?"),
                        summary=(r.get("summary") or "")[:200]))
json.dump(out, open("D:/zcode-workspace/mash_v2_new/research/geo_candidates.json", "w"),
          ensure_ascii=False, indent=1)
for r in sorted(out, key=lambda x: -(x["n_samples"] or 0))[:20]:
    print(f"  {r['accession']:11s} n={str(r['n_samples']):>3} {r['gtype'][:14]:14s} "
          f"{r['pubdate'][:4]} {str(r['gpl'])[:10]:10s} {r['title'][:62]}")

# ---------- 2. ChEMBL ----------
print("\n[2] ChEMBL 活性数据量 (过滤参数式查询)")
TARGETS = {
    "THRb": "CHEMBL1947", "FASN": "CHEMBL4158", "SCD1": "CHEMBL1275210",
    "DGAT2": "CHEMBL2439944", "DGAT1": "CHEMBL2029", "PPARA": "CHEMBL237",
    "PPARD": "CHEMBL203", "ACACA": "CHEMBL2494", "ACACB": "CHEMBL1075227",
}
report = {}
for name, tid in TARGETS.items():
    cnt = {}
    for act in ["IC50", "EC50", "Ki"]:
        try:
            js = json.loads(get(f"https://www.ebi.ac.uk/chembl/api/data/activity.json",
                                {"target_chembl_id__exact": tid, "standard_type__exact": act,
                                 "assay_type__exact": "B", "organism__exact": "Homo sapiens",
                                 "format": "json", "limit": 1}))
            cnt[act] = js["page_meta"]["total_count"]
        except Exception as e:
            cnt[act] = f"ERR"
        time.sleep(0.35)
    report[name] = dict(chembl_id=tid, counts=cnt)
    print(f"  {name:6s} {tid:14s} {cnt}")

# ---------- 3. RCSB (POST) ----------
print("\n[3] RCSB 结构检索 (人源, <=3.0A, 含配体)")
def rcsb_search(text_value, rows=30):
    body = {
        "query": {"type": "group", "logical_operator": "and", "nodes": [
            {"type": "terminal", "service": "full_text", "parameters": {
                "attribute": "text", "operator": "contains_words", "value": text_value}},
            {"type": "terminal", "service": "text", "parameters": {
                "attribute": "rcsb_entity_source_organism.taxonomy_lineage.name",
                "operator": "exact_match", "value": "Homo sapiens"}},
            {"type": "terminal", "service": "text", "parameters": {
                "attribute": "rcsb_entry_info.resolution_combined",
                "operator": "less_or_equal", "value": 3.0}},
            {"type": "terminal", "service": "text", "parameters": {
                "attribute": "rcsb_entry_info.nonpolymer_entity_count", "operator": "greater",
                "value": 0}},
        ]},
        "request_options": {"paginate": {"start": 0, "rows": rows},
                            "results_content_type": ["experimental"],
                            "scoring_strategy": "combined"},
        "return_type": "entry"}
    js = json.loads(post("https://search.rcsb.org/rcsbsearch/v2/query", body))
    return [h["identifier"] for h in js.get("result_set", [])]

for name, q in [("THRb", "thyroid hormone receptor beta"),
                ("FASN", "fatty acid synthase"),
                ("SCD1", "stearoyl-CoA desaturase"),
                ("DGAT2", "diacylglycerol acyltransferase 2"),
                ("DGAT1", "diacylglycerol acyltransferase 1")]:
    try:
        ids = rcsb_search(q)
        report[name]["pdb_le3A_with_ligand"] = ids
        print(f"  {name:6s}: {len(ids)} hits {ids[:12]}")
    except Exception as e:
        print(f"  {name:6s}: ERR {str(e)[:70]}")
    time.sleep(0.6)

json.dump(report, open("D:/zcode-workspace/mash_v2_new/research/chembl_pdb_scout.json", "w"), indent=1)
print("\nsaved.")
