# -*- coding: utf-8 -*-
"""下载并审计竞争靶点的 ChEMBL 精确标准活性记录，保存原始数据与质量统计。"""
import json, time, urllib.request, urllib.parse, os, csv, collections, math
BASE='https://www.ebi.ac.uk/chembl/api/data'
OUT='D:/zcode-workspace/aidd-repo-work/00-当前研究/seventh_round_20260912'
PANEL={'FASN':'CHEMBL4158','THRB':'CHEMBL1947','FXR':'CHEMBL2047','KEAP1':'CHEMBL2069156','ACC1':'CHEMBL3351','ACC2':'CHEMBL4829'}
STDS={'FASN':['IC50','Ki','Kd'],'THRB':['IC50','EC50','Ki','Kd','Potency'],'FXR':['IC50','EC50','Kd'],'KEAP1':['IC50','EC50','Ki','Kd'],'ACC1':['IC50','EC50','Kd'],'ACC2':['IC50','Kd']}
os.makedirs(OUT+'/raw/chembl_activity',exist_ok=True)

def fetch(url):
    for k in range(4):
        try:
            req=urllib.request.Request(url, headers={'User-Agent':'MASH-strategic-audit/2026'})
            with urllib.request.urlopen(req,timeout=120) as r: return json.loads(r.read().decode('utf-8'))
        except Exception as e:
            if k==3: raise
            time.sleep(2**k)

def get_all(name, tid, stds):
    out=[]
    for std in stds:
        offset=0
        while True:
            params={'target_chembl_id':tid,'standard_type':std,'standard_relation':'=','limit':1000,'offset':offset}
            d=fetch(BASE+'/activity.json?'+urllib.parse.urlencode(params))
            acts=d.get('activities',[])
            out.extend(acts)
            total=d.get('page_meta',{}).get('total_count',0)
            if offset+len(acts)>=total or not acts: break
            offset+=len(acts); time.sleep(.2)
        print(name,std,'=',len([a for a in out if a.get('standard_type')==std]))
    # de-dupe by activity id because none overlap across std normally
    unique={a.get('activity_id',id(a)):a for a in out}
    out=list(unique.values())
    with open(f'{OUT}/raw/chembl_activity/{name}_exact_records.json','w',encoding='utf-8') as f:
        json.dump({'query_date':'2026-09-12','target':tid,'records':out},f,ensure_ascii=False)
    return out

def summarize(name, tid, acts):
    def vals(key): return collections.Counter(str(a.get(key)) for a in acts)
    mols={a.get('molecule_chembl_id') for a in acts if a.get('molecule_chembl_id')}
    assays={a.get('assay_chembl_id') for a in acts if a.get('assay_chembl_id')}
    docs={a.get('document_chembl_id') for a in acts if a.get('document_chembl_id')}
    units=vals('standard_units'); types=vals('standard_type'); relations=vals('standard_relation')
    # values convertible to p standard only if nM and positive
    convertible=0; nonpositive=0
    for a in acts:
        try:
            x=float(a.get('standard_value'))
            if x>0 and str(a.get('standard_units')).lower() in ('nm','nanomolar'): convertible+=1
            elif x<=0: nonpositive+=1
        except: pass
    # assay endpoint/description may be absent in activity response; assay IDs still count
    # distribution of source target IDs and BAO formats
    summary={'route':name,'target_chembl_id':tid,'exact_records':len(acts),'distinct_molecules':len(mols),'distinct_assays':len(assays),'distinct_documents':len(docs),'standard_type':dict(types),'standard_units':dict(units),'standard_relation':dict(relations),'positive_nM_convertible':convertible,'nonpositive_numeric':nonpositive,'molecules_with_multiple_records':sum(1 for m in mols if sum(1 for a in acts if a.get('molecule_chembl_id')==m)>1)}
    return summary

summ=[]
for name,tid in PANEL.items():
    acts=get_all(name,tid,STDS[name])
    s=summarize(name,tid,acts); summ.append(s); print(s); time.sleep(1)
with open(OUT+'/derived/chembl_activity_quality_summary.json','w',encoding='utf-8') as f: json.dump({'query_date':'2026-09-12','summaries':summ},f,ensure_ascii=False,indent=2)
# csv for direct report use
fields=['route','target_chembl_id','exact_records','distinct_molecules','distinct_assays','distinct_documents','positive_nM_convertible','nonpositive_numeric','molecules_with_multiple_records','standard_type','standard_units','standard_relation']
with open(OUT+'/derived/chembl_activity_quality_summary.csv','w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
    for s in summ:
        row={k:s.get(k) for k in fields};
        for k in ['standard_type','standard_units','standard_relation']: row[k]=json.dumps(row[k],ensure_ascii=False)
        w.writerow(row)
