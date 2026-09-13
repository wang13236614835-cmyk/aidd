# -*- coding: utf-8 -*-
"""Final strategy round: rebuild FASN_activity_master.csv with provenance."""
import csv, json, math, re, time, urllib.request, urllib.parse, hashlib
from pathlib import Path
from collections import Counter, defaultdict
from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors

ROOT=Path(r'D:/zcode-workspace/aidd-repo-work/00-当前研究')
OUT=ROOT/'final_strategy_round_20260912'
RAW=OUT/'raw/chembl_activity/FASN_exact_records.json'
OUT.mkdir(parents=True, exist_ok=True)
(OUT/'raw').mkdir(exist_ok=True); (OUT/'derived').mkdir(exist_ok=True); (OUT/'logs').mkdir(exist_ok=True); (OUT/'manifest').mkdir(exist_ok=True)
raw=json.loads(RAW.read_text(encoding='utf-8'))['records']

# Fetch document metadata for provenance (keep failure as unresolved, not negative)
doc_ids=sorted({r.get('document_chembl_id') for r in raw if r.get('document_chembl_id')})
doc_meta={}
for did in doc_ids:
    url=f'https://www.ebi.ac.uk/chembl/api/data/document/{did}.json'
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'MASH-final-strategy-audit/2026'})
        with urllib.request.urlopen(req,timeout=45) as h: doc_meta[did]=json.loads(h.read().decode('utf-8'))
    except Exception as e:
        doc_meta[did]={'_error':str(e)}
    time.sleep(0.15)
(OUT/'raw/chembl_document_metadata.json').write_text(json.dumps({'query_date':'2026-09-12','documents':doc_meta},ensure_ascii=False,indent=2),encoding='utf-8')

# Stable molecule-derived identifiers and explicit flags
def mol_info(smiles):
    m=Chem.MolFromSmiles(smiles) if smiles else None
    if m is None: return {'inchikey':'','mw_rdkit':'','fragment_count':'','is_valid_smiles':0,'canonical_smiles_rdkit':''}
    return {'inchikey':Chem.MolToInchiKey(m),'mw_rdkit':round(Descriptors.MolWt(m),5),'fragment_count':len(Chem.GetMolFrags(m)),'is_valid_smiles':1,'canonical_smiles_rdkit':Chem.MolToSmiles(m,isomericSmiles=True)}

rows=[]; unit_counts=Counter(); invalid=[]
for r in raw:
    mi=mol_info(r.get('canonical_smiles'))
    units=(r.get('standard_units') or '').strip()
    value=float(r['standard_value']) if r.get('standard_value') not in (None,'') else None
    standardized_nM=None; conversion='direct_nM'
    if units.lower()=='nm': standardized_nM=value
    elif units.lower() in ('ug.ml-1','ug/ml','µg/ml') and value is not None and mi['mw_rdkit']:
        standardized_nM=value*1_000_000/float(mi['mw_rdkit'])
        conversion='derived_from_ug_per_mL_and_RDKit_MW'
    else:
        conversion='not_standardized'
    pactivity=-math.log10(standardized_nM*1e-9) if standardized_nM and standardized_nM>0 else None
    desc=r.get('assay_description') or ''
    low=desc.lower()
    if 'purified' in low or 'recombinant' in low or 'full length' in low or 'full-length' in low:
        bio='biochemical_recombinant_or_purified'
    elif 'cell extract' in low or 'cell derived' in low or 'cell-line' in low or 'cells' in low:
        bio='cell_extract_or_cellular'
    else:
        bio='unknown_biochemical_context'
    construct='not_reported_in_ChEMBL_activity_record'
    if 'full length' in low or 'full-length' in low: construct='full_length_human_FASN_stated_in_assay_description'
    elif 'ketoacyl reductase' in low or 'KR domain' in low: construct='KR_domain_stated_in_assay_description'
    elif 'thioster' in low or 'TE activity' in low: construct='TE_domain_stated_in_assay_description'
    elif 'cell extract' in low: construct='cell_extract_FASN_not_recombinant_construct'
    notes=[]
    if r.get('potential_duplicate'): notes.append('ChEMBL potential_duplicate flag')
    if mi['fragment_count'] and mi['fragment_count']>1: notes.append('multiple_SMILES_fragments')
    if not mi['is_valid_smiles']: notes.append('SMILES_parse_failed')
    if r.get('data_validity_comment'): notes.append('data_validity_comment_present')
    did=r.get('document_chembl_id'); dm=doc_meta.get(did,{})
    doi=dm.get('doi') or dm.get('doi_url') or ''
    pmid=dm.get('pubmed_id') or dm.get('pubmed_id') or ''
    # Preserve raw source fields and add derived provenance fields.
    rows.append({
        'molecule_id':r.get('molecule_chembl_id',''), 'canonical_smiles':r.get('canonical_smiles',''),
        'inchikey':mi['inchikey'],'activity_id':r.get('activity_id',''),'assay_id':r.get('assay_chembl_id',''),
        'document_id':did or '','target_id':r.get('target_chembl_id',''),'target_name':r.get('target_pref_name',''),
        'species':r.get('target_organism',''),'construct':construct,'assay_type':r.get('assay_type',''),
        'assay_format':r.get('bao_label',''),'biochemical_or_cellular':bio,'activity_type':r.get('standard_type',''),
        'relation':r.get('standard_relation',''),'value':value,'unit':units,'standardized_nM':standardized_nM,
        'pActivity':pactivity,'source':'ChEMBL REST activity.json snapshot 2026-09-12',
        'DOI':doi,'PMID':pmid,'confidence':'high_for_record_fields_low_for_cross_assay_comparability',
        'notes':';'.join(notes),'assay_description':desc,'document_year':r.get('document_year',''),
        'document_journal':r.get('document_journal',''),'standard_flag':r.get('standard_flag',''),
        'potential_duplicate':r.get('potential_duplicate',''),'fragment_count':mi['fragment_count'],
        'is_valid_smiles':mi['is_valid_smiles'],'conversion_method':conversion,
    })
    unit_counts[units]+=1

fields=list(rows[0].keys())
master=OUT/'FASN_activity_master.csv'
with master.open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore'); w.writeheader(); w.writerows(rows)

# Provenance summary by assay and assay family
assay=defaultdict(list)
for r in rows: assay[r['assay_id']].append(r)
assay_rows=[]
for aid, rr in sorted(assay.items(), key=lambda kv:-len(kv[1])):
    desc=rr[0]['assay_description']; low=desc.lower()
    if 'full length' in low or 'full-length' in low: family='full_length_stated'
    elif 'cell extract' in low or 'cell derived' in low or 'cell-line' in low: family='cell_extract'
    elif 'ketoacyl reductase' in low or 'kr domain' in low: family='KR_domain'
    elif 'thioster' in low or 'te activity' in low: family='TE_domain'
    else: family='other_or_unknown'
    assay_rows.append({'assay_id':aid,'records':len(rr),'distinct_molecules':len({x['molecule_id'] for x in rr}),'distinct_documents':len({x['document_id'] for x in rr}),'activity_types':';'.join(sorted({x['activity_type'] for x in rr})),'units':';'.join(sorted({x['unit'] for x in rr})),'assay_format':';'.join(sorted({x['assay_format'] for x in rr})),'family':family,'document_years':';'.join(sorted({str(x['document_year']) for x in rr})),'description':desc})
with (OUT/'derived/FASN_assay_provenance_summary.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(assay_rows[0].keys())); w.writeheader(); w.writerows(assay_rows)

summary={'query_date':'2026-09-12','raw_records':len(raw),'master_records':len(rows),'distinct_molecules':len({r['molecule_id'] for r in rows}),'distinct_assays':len(assay),'distinct_documents':len({r['document_id'] for r in rows}),'units':dict(unit_counts),'valid_smiles':sum(int(r['is_valid_smiles']) for r in rows),'multiple_fragments':sum(1 for r in rows if int(r['fragment_count'] or 0)>1),'assay_family_record_counts':dict(Counter(x['family'] for x in assay_rows))}
(OUT/'derived/FASN_master_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'logs/build_FASN_master.log').write_text(json.dumps({'summary':summary,'document_fetch_errors':{k:v for k,v in doc_meta.items() if '_error' in v}},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False,indent=2))
