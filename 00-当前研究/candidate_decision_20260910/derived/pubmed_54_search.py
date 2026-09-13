import csv, json, requests, time, re
from pathlib import Path
from datetime import datetime, timezone
src=Path(r"D:\zcode-workspace\ds_in\np54_ligands.csv")
out=Path(r"D:\zcode-workspace\aidd-repo-work\00-当前研究\candidate_decision_20260910\derived\pubmed_54_search.jsonl")
rows=list(csv.DictReader(src.open(encoding="utf-8-sig")))
s=requests.Session(); s.headers["User-Agent"]="MASH-evidence-audit/2026.09 (authorized research audit)"
def esearch(term):
    try:
        r=s.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",params={"db":"pubmed","term":term,"retmode":"json","retmax":20},timeout=30)
        r.raise_for_status(); d=r.json()["esearchresult"]
        return {"ok":True,"count":int(d.get("count",0)),"ids":d.get("idlist",[]),"translation":d.get("querytranslation","")}
    except Exception as e: return {"ok":False,"error":str(e)}
terms={
 "disease": '(MASH OR NASH OR NAFLD OR MASLD OR steatohepatitis OR "fatty liver")',
 "mechanism": '(FXR OR NR1H4 OR "thyroid hormone receptor" OR TRbeta OR TRβ OR TRalpha OR ferroptosis OR "lipid peroxidation" OR "hepatic stellate")'
}
with out.open('w',encoding='utf-8') as f:
 for i,row in enumerate(rows,1):
  name=row['label']
  # exact title/abstract phrase; PubMed will retain exact query in log
  rec={"record_id":i,"brd_id":row['brd_id'],"name":name,"herb":row['source_file'],"date_utc":datetime.now(timezone.utc).isoformat(),"queries":{}}
  for k,t in terms.items():
   q=f'"{name}"[Title/Abstract] AND {t}'
   rec['queries'][k]={"query":q,"result":esearch(q)}
   time.sleep(0.08)
  f.write(json.dumps(rec,ensure_ascii=False)+'\n'); f.flush(); print(i,name,rec['queries']['disease']['result'].get('count'),rec['queries']['mechanism']['result'].get('count'))
print(out)
