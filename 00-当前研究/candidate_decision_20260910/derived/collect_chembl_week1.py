from __future__ import annotations
import csv, json, subprocess, sys, time, re
from pathlib import Path
from collections import Counter

ROOT=Path(r'D:\zcode-workspace\aidd-repo-work\00-当前研究\candidate_decision_20260910')
RAW=ROOT/'derived'/'chembl_raw'
RAW.mkdir(parents=True,exist_ok=True)
SCRIPT=Path(r'C:\Users\user\.agents\skills\chembl-skill\scripts\rest_request.py')
TARGETS={'fxr':'CHEMBL2047','thrb':'CHEMBL1947','thra':'CHEMBL1860'}

FIELDS=['target_label','target_chembl_id','target_pref_name','target_organism','target_tax_id','activity_id','record_id','molecule_chembl_id','parent_molecule_chembl_id','molecule_pref_name','canonical_smiles','assay_chembl_id','assay_description','assay_type','bao_format','bao_label','assay_variant_accession','assay_variant_mutation','document_chembl_id','document_journal','document_year','standard_type','standard_relation','standard_value','standard_units','standard_upper_value','pchembl_value','relation','value','units','text_value','data_validity_comment','potential_duplicate','standard_flag','src_id']

def run_request(payload, timeout=120):
    q=subprocess.run([sys.executable,str(SCRIPT)],input=json.dumps(payload),text=True,capture_output=True,timeout=timeout)
    try: return json.loads(q.stdout or '{}')
    except Exception: return {'ok':False,'error':{'code':'invalid_local_json','message':q.stdout[:1000],'stderr':q.stderr[:1000]}}

def fetch_target(label, tid):
    d=RAW/label; d.mkdir(parents=True,exist_ok=True)
    first_raw=d/'page_0000.json'
    payload={'base_url':'https://www.ebi.ac.uk/chembl/api/data','path':'activity.json','params':{'target_chembl_id':tid,'limit':1000,'offset':0},'record_path':'activities','max_items':1,'max_depth':2,'timeout_sec':60,'save_raw':True,'raw_output_path':str(first_raw)}
    outer=run_request(payload,180)
    if not outer.get('ok'):
        raise RuntimeError(f'{label} initial request failed: {outer}')
    first=json.loads(first_raw.read_text(encoding='utf-8'))
    total=int(first.get('page_meta',{}).get('total_count',0))
    activities=[]
    offset=0; page=0
    while True:
        p=d/f'page_{page:04d}.json'
        if not p.exists():
            payload['params']['offset']=offset; payload['raw_output_path']=str(p)
            out=run_request(payload,180)
            if not out.get('ok'): raise RuntimeError(f'{label} offset {offset} failed: {out}')
        data=json.loads(p.read_text(encoding='utf-8'))
        chunk=data.get('activities',[])
        activities.extend(chunk)
        meta=data.get('page_meta',{})
        print(label,'page',page,'offset',offset,'chunk',len(chunk),'total',total,flush=True)
        if not chunk or offset+len(chunk)>=total: break
        offset += len(chunk); page += 1
        time.sleep(0.15)
    return activities,total

allrows=[]; summaries=[]
for label,tid in TARGETS.items():
    acts,total=fetch_target(label,tid)
    for a in acts:
        row={k:a.get(k) for k in FIELDS}
        row['target_label']=label
        row['target_chembl_id']=tid
        allrows.append(row)
    by_type=Counter(str(a.get('standard_type') or 'UNKNOWN') for a in acts)
    by_unit=Counter(str(a.get('standard_units') or 'UNKNOWN') for a in acts)
    by_assay=Counter(str(a.get('assay_type') or 'UNKNOWN') for a in acts)
    valid=[a for a in acts if a.get('standard_flag')==1 and a.get('standard_value') not in (None,'') and a.get('canonical_smiles')]
    comparable=[a for a in valid if str(a.get('standard_type','')).upper() in {'IC50','EC50','KI','KD','AC50','POTENCY','INHIBITION'}]
    summaries.append({'target_label':label,'target_chembl_id':tid,'records_downloaded':len(acts),'page_total':total,'valid_standard_smiles_records':len(valid),'candidate_comparable_records':len(comparable),'standard_type_counts':dict(by_type),'standard_unit_counts':dict(by_unit),'assay_type_counts':dict(by_assay)})

out=ROOT/'derived'/'chembl_activity_all_targets.csv'
with out.open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.DictWriter(f,fieldnames=FIELDS); w.writeheader(); w.writerows(allrows)

# Stable candidate training table: retains only rows that can be numerically interpreted,
# but does not silently pool endpoints; endpoint/assay columns remain explicit.
train=[]
for r in allrows:
    try: val=float(r['standard_value'])
    except (TypeError,ValueError): continue
    if r['standard_flag'] not in (1,'1',True): continue
    if not r['canonical_smiles'] or not r['standard_type'] or not r['standard_units']: continue
    try: pv=float(r['pchembl_value']) if r['pchembl_value'] not in (None,'') else None
    except (TypeError,ValueError): pv=None
    rr=dict(r); rr['standard_value_numeric']=val; rr['pchembl_numeric']=pv
    rr['training_inclusion']='candidate_only_not_yet_frozen'
    rr['pooling_rule']='keep assay/endpoint/units separated; no cross-assay averaging'
    train.append(rr)
with (ROOT/'derived'/'chembl_training_candidates.csv').open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.DictWriter(f,fieldnames=FIELDS+['standard_value_numeric','pchembl_numeric','training_inclusion','pooling_rule']); w.writeheader(); w.writerows(train)

(ROOT/'derived'/'chembl_data_collection_summary.json').write_text(json.dumps({'generated_at':'2026-09-10','targets':summaries,'all_records':len(allrows),'training_candidate_records':len(train),'limitations':['ChEMBL records span heterogeneous assays/endpoints and constructs','no labels are pooled or converted into a final training target in Week 1','activity records require assay-level review and locked development/validation split','human FXR/TRβ/TRα target IDs are explicit; rodent targets excluded from this collection']},ensure_ascii=False,indent=2),encoding='utf-8')
print('DONE',len(allrows),len(train))
