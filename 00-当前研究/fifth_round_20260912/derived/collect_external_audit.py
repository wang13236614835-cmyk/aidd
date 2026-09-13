from __future__ import annotations
import csv, json, re, time, hashlib
from pathlib import Path
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from datetime import datetime, timezone

ROOT = Path(r"D:\zcode-workspace\aidd-repo-work\00-当前研究\fifth_round_20260912")
RAW = ROOT / "raw" / "external"
RAW.mkdir(parents=True, exist_ok=True)
LOG = ROOT / "logs" / "external_query_log.jsonl"

CANDS = [
    {"compound":"moracin N","cas":"135248-05-4","cid":"641376","inchikey":"WBSCSIABHGPAMC-UHFFFAOYSA-N","smiles":"CC(=CCC1=C(C=C2C(=C1)C=C(O2)C3=CC(=CC(=C3)O)O)O)C","synonyms":["moracin N","Moracin-N"]},
    {"compound":"formononetin","cas":"485-72-3","cid":"5280378","inchikey":"HKQYGTCOTHHOMP-UHFFFAOYSA-N","smiles":"COC1=CC=C(C=C1)C2=COC3=C(C2=O)C=CC(=C3)O","synonyms":["formononetin","Biochanin B","4'-O-methyldaidzein","4'-methoxydaidzein"]},
    {"compound":"3'-methoxydaidzein","cas":"21913-98-4","cid":"5319422","inchikey":"MUYAUELJBWQNDH-UHFFFAOYSA-N","smiles":"COC1=C(C=CC(=C1)C2=COC3=C(C2=O)C=CC(=C3)O)O","synonyms":["3'-methoxydaidzein","3-methoxydaidzein","7,4'-dihydroxy-3'-methoxyisoflavone","3'-methoxy daidzein"]},
    {"compound":"isorhamnetin","cas":"480-19-3","cid":"5281654","inchikey":"IZQSVPBOUDKVDZ-UHFFFAOYSA-N","smiles":"COC1=C(C=CC(=C1)C2=C(C(=O)C3=C(C=C(C=C3O2)O)O)O)O","synonyms":["isorhamnetin","3'-methoxyquercetin","3'-O-methylquercetin","quercetin 3'-methyl ether"]},
    {"compound":"biochanin A","cas":"491-80-5","cid":"5280373","inchikey":"WUADCCWRTIWANL-UHFFFAOYSA-N","smiles":"COC1=CC=C(C=C1)C2=COC3=CC(=CC(=C3C2=O)O)O","synonyms":["biochanin A","biochanin","4'-methylgenistein","genistein 4-methyl ether"]},
]

DISEASE = ["MASLD", "MASH", "NASH", "NAFLD", "fatty liver", "hepatic fibrosis"]
MECH = ["THRB", "thyroid hormone receptor", "TRβ", "THRA", "TRα", "FXR", "NR1H4", "Nrf2", "Keap1", "ferroptosis", "GPX4", "SLC7A11", "ACSL4", "ROS", "lipid peroxidation"]
EXTRA = {
    "3'-methoxydaidzein":["NaV1.7","NaV1.8","NaV1.3"],
    "moracin N":["GPX4","SLC7A11","ACSL4","ROS"],
}

session = datetime.now(timezone.utc).isoformat()

def sha(s: bytes) -> str:
    return hashlib.sha256(s).hexdigest()

def fetch(url: str, headers=None, timeout=35):
    hdr = {"User-Agent":"fifth-round-audit/2026.09 contact: research-audit"}
    if headers: hdr.update(headers)
    try:
        req = Request(url, headers=hdr)
        with urlopen(req, timeout=timeout) as r:
            body = r.read()
            return {"status": getattr(r,"status",200), "content_type":r.headers.get("Content-Type",""), "body":body, "error":None}
    except HTTPError as e:
        body = e.read() if hasattr(e,"read") else b""
        return {"status":e.code, "content_type":e.headers.get("Content-Type","") if e.headers else "", "body":body, "error":str(e)}
    except Exception as e:
        return {"status":None, "content_type":"", "body":b"", "error":repr(e)}

def save(cmpd, db, label, url, result, query, note=""):
    safe = re.sub(r"[^A-Za-z0-9_.-]+","_", f"{cmpd}_{db}_{label}")[:180]
    ext = ".json" if "json" in result.get("content_type","").lower() or db in {"pubmed","crossref","chembl","bindingdb","pubchem_bioassay","clinicaltrials"} else ".html"
    out = RAW / (safe + ext)
    out.write_bytes(result.get("body",b""))
    rec = {
      "timestamp_utc": datetime.now(timezone.utc).isoformat(), "compound":cmpd,
      "database":db, "label":label, "query":query, "url":url,
      "status_code":result.get("status"), "error":result.get("error"),
      "content_type":result.get("content_type"), "raw_file":str(out),
      "raw_sha256":sha(result.get("body",b"")), "note":note,
    }
    with LOG.open("a", encoding="utf-8") as fh: fh.write(json.dumps(rec,ensure_ascii=False)+"\n")
    return rec

def run_json(cmpd, db, label, url, query, note=""):
    r=fetch(url, headers={"Accept":"application/json"})
    return save(cmpd,db,label,url,r,query,note)

if LOG.exists(): LOG.unlink()
summary=[]
for c in CANDS:
    cmpd=c["compound"]
    terms=[]
    for syn in c["synonyms"]:
        terms += [syn, f'"{syn}"', f'{syn} {c["cas"]}']
    # exact PubMed combinations (name + disease/target); use all canonical synonyms but avoid duplicate terms
    queries=[]
    for syn in dict.fromkeys(c["synonyms"]):
        for term in DISEASE + MECH + EXTRA.get(cmpd,[]):
            queries.append(f'"{syn}"[Title/Abstract] AND "{term}"[Title/Abstract]')
    for q in dict.fromkeys(queries):
        url="https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?"+urlencode({"db":"pubmed","term":q,"retmode":"json","retmax":"100","sort":"relevance"})
        rec=run_json(cmpd,"pubmed","esearch",url,q,"exact name/synonym query")
        summary.append(rec); time.sleep(0.18)
    # PubMed broader disease and mechanism combined query, one per candidate
    for label, q in [("disease_broad",f'({" OR ".join([quote(s) for s in c["synonyms"][:4]])}) AND (MASLD OR MASH OR NASH OR NAFLD OR "fatty liver" OR "hepatic fibrosis")'),
                     ("mechanism_broad",f'({" OR ".join([quote(s) for s in c["synonyms"][:4]])}) AND (THRB OR THRA OR "thyroid hormone receptor" OR FXR OR NR1H4 OR Nrf2 OR Keap1 OR ferroptosis OR GPX4 OR SLC7A11 OR ACSL4)')]:
        url="https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?"+urlencode({"db":"pubmed","term":q,"retmode":"json","retmax":"100","sort":"relevance"})
        summary.append(run_json(cmpd,"pubmed",label,url,q,"broad synonym query")); time.sleep(0.18)
    # Crossref exact-ish bibliographic searches for primary literature and reviews
    for q in [f'"{c["compound"]}" MASH', f'"{c["compound"]}" NASH', f'"{c["compound"]}" THRB', f'"{c["compound"]}" FXR', f'"{c["compound"]}" ferroptosis', c["cas"]]:
        url="https://api.crossref.org/works?"+urlencode({"query.bibliographic":q,"rows":"20","select":"DOI,title,author,published,container-title,URL,type"})
        summary.append(run_json(cmpd,"crossref","works",url,q,"bibliographic search")); time.sleep(0.25)
    # ChEMBL molecule text search and activity snapshots where a molecule is found
    for q in [c["compound"], c["cas"], c["inchikey"]]:
        url="https://www.ebi.ac.uk/chembl/api/data/molecule/search.json?"+urlencode({"q":q,"limit":"20"})
        rec=run_json(cmpd,"chembl","molecule_search",url,q,"text/CAS/InChIKey search")
        summary.append(rec)
        try:
            data=json.loads((RAW / Path(rec["raw_file"]).name).read_text(encoding="utf-8",errors="replace"))
            mols=data.get("molecules",[])
            for m in mols[:5]:
                mid=m.get("molecule_chembl_id")
                if mid:
                    au="https://www.ebi.ac.uk/chembl/api/data/activity.json?"+urlencode({"molecule_chembl_id":mid,"limit":"1000"})
                    summary.append(run_json(cmpd,"chembl",f"activity_{mid}",au,q,f"activity records for {mid}"))
        except Exception: pass
        time.sleep(0.35)
    # BindingDB by canonical SMILES; include response=application/json
    for label, params in [("smiles",{"smiles":c["smiles"],"cutoff":"0.99","response":"application/json"}),
                          ("uniprot",{"uniprot":"P10828","response":"application/json"})]:
        path="rest/getLigandsBySmiles" if label=="smiles" else "rest/getLigandsByUniprots"
        url="https://bindingdb.org/"+path+"?"+urlencode(params)
        summary.append(run_json(cmpd,"bindingdb",label,url,params.get("smiles",params.get("uniprot")),"BindingDB REST query")); time.sleep(0.25)
    # PubChem BioAssay summary by CID (endpoint may be unsupported; failure is retained)
    url=f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{c['cid']}/assaysummary/JSON"
    summary.append(run_json(cmpd,"pubchem_bioassay","assaysummary",url,c["cid"],"CID assay summary")); time.sleep(0.25)
    # ClinicalTrials.gov v2
    for q in [c["compound"], c["cas"]]:
        url="https://clinicaltrials.gov/api/v2/studies?"+urlencode({"query.term":q,"pageSize":"100","format":"json"})
        summary.append(run_json(cmpd,"clinicaltrials","studies",url,q,"compound/CAS clinical pipeline search")); time.sleep(0.3)
    # Google Scholar / Google Patents / WIPO / CNIPA / CNKI reachability and query boundaries
    for db, base, param in [
        ("google_scholar","https://scholar.google.com/scholar","q"),
        ("google_patents","https://patents.google.com/","q"),
        ("wipo","https://patentscope.wipo.int/search/en/search.jsf","query"),
        ("cnipa","https://pss-system.cponline.cnipa.gov.cn/conventionalSearch","searchWord"),
        ("cnki","https://kns.cnki.net/kns8s/defaultresult/index","kw")]:
        q=f'"{c["compound"]}" {c["cas"]}'
        url=base+"?"+urlencode({param:q})
        summary.append(save(cmpd,db,"reachability",url,fetch(url),q,"search endpoint reachability; block/HTML/manual review boundary")); time.sleep(0.4)
    # PubChem synonym endpoint raw for this round
    url=f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{c['cid']}/synonyms/JSON"
    summary.append(run_json(cmpd,"pubchem","synonyms",url,c["cid"],"canonical synonym refresh")); time.sleep(0.25)

(ROOT/"derived"/"external_query_summary.json").write_text(json.dumps({"generated_utc":session,"records":len(summary),"by_database":{db:sum(1 for x in summary if x["database"]==db) for db in sorted(set(x["database"] for x in summary))}},ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps({"generated_utc":session,"records":len(summary),"log":str(LOG),"raw_dir":str(RAW)},ensure_ascii=False,indent=2))
