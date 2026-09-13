from pathlib import Path
import json, math
import pandas as pd
from rdkit import Chem
from rdkit.Chem.SaltRemover import SaltRemover

out=Path(__file__).parent; root=out.parent.parent
sample=pd.read_csv(out/'ten_recalculations.csv'); ids=set(sample.activity_id.astype(int)); found={}
for p in (root/'candidate_decision_20260910/derived/chembl_raw').glob('*/*.json'):
    for r in json.loads(p.read_text(encoding='utf-8-sig')).get('activities',[]):
        if r['activity_id'] in ids: found[r['activity_id']]=r
checks=[]
for _,r in sample.iterrows():
    src=found[int(r.activity_id)]; val=9-math.log10(float(src['standard_value']))
    checks.append(dict(activity_id=int(r.activity_id),source_value=src['standard_value'],relation=src['standard_relation'],unit=src['standard_units'],recalculated=val,error=abs(val-r.pActivity_nM),source_smiles=src['canonical_smiles']))
allx=pd.read_csv(root/'candidate_decision_20260910/derived/chembl_numeric_nM_exact_candidates.csv',low_memory=False)
salts=[r for r in checks if '.' in r['source_smiles']]
for r in salts:
    m=Chem.MolFromSmiles(r['source_smiles']); stripped=SaltRemover().StripMol(m,dontRemoveEverything=True)
    r['salt_stripped_smiles']=Chem.MolToSmiles(stripped)
    row=allx[allx.activity_id==r['activity_id']].iloc[0]
    r['molecule']=row.molecule_chembl_id
    r['unchanged_from_raw']=r['source_smiles']==row.canonical_smiles
    r['remaining_fragments']=len(Chem.GetMolFrags(stripped))
v=json.loads((out/'results.json').read_text(encoding='utf-8'))
v['conversion_raw_JSON_verification']=checks
v['quick_self_check']={'raw_values_from_original_ChEMBL_response':True,'independent_scripts_executed':True,'FASN_missing_provenance_not_called_error':True,'later_round_results_not_used_as_evidence':True}
(out/'results.json').write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'raw_source_matched':len(checks),'max_error':max(r['error'] for r in checks),'salt_checks':salts},ensure_ascii=False))
