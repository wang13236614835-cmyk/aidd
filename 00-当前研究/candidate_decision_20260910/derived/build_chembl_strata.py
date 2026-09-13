import pandas as pd
from pathlib import Path
import json
ROOT=Path(r'D:\zcode-workspace\aidd-repo-work\00-当前研究\candidate_decision_20260910')
P=ROOT/'derived'/'chembl_activity_all_targets.csv'
df=pd.read_csv(P,low_memory=False)
# Keep strata separate. A classification-ready subset is defined only for numeric potency-like endpoints in nM and standard relation =.
valid=df[(df.standard_flag==1)&df.canonical_smiles.notna()&df.standard_value.notna()&df.standard_units.eq('nM')&df.standard_relation.eq('=')].copy()
valid['standard_value_nM']=pd.to_numeric(valid.standard_value,errors='coerce')
valid=valid[valid.standard_value_nM>0]
valid['pActivity_nM']=-__import__('numpy').log10(valid.standard_value_nM*1e-9)
valid['endpoint_stratum']=valid.target_label.astype(str)+'|'+valid.standard_type.astype(str)+'|'+valid.assay_type.astype(str)+'|'+valid.bao_label.fillna('NA').astype(str)+'|'+valid.assay_chembl_id.astype(str)
valid.to_csv(ROOT/'derived'/'chembl_numeric_nM_exact_candidates.csv',index=False,encoding='utf-8-sig')
# Deduplicated per exact activity record only; no cross-assay averaging.
counts=valid.groupby(['target_label','standard_type','assay_type','bao_label']).size().reset_index(name='n_records').sort_values('n_records',ascending=False)
counts.to_csv(ROOT/'derived'/'chembl_strata_counts.csv',index=False,encoding='utf-8-sig')
summary={'generated_at':'2026-09-10','source':str(P),'raw_records':int(len(df)),'numeric_exact_nM_candidates':int(len(valid)),'targets':{},'rules':['human targets only: FXR CHEMBL2047, TRβ CHEMBL1947, TRα CHEMBL1860','standard_flag=1, standard_units=nM, standard_relation==, numeric positive values','assay/endpoint/construct strata retained; no cross-assay averaging or label inversion','this is a candidate dataset, not a frozen final training set or external validation result']}
for t in ['fxr','thrb','thra']:
 x=valid[valid.target_label==t]
 summary['targets'][t]={'records':int(len(x)),'molecules':int(x.molecule_chembl_id.nunique()),'assays':int(x.assay_chembl_id.nunique()),'types':x.standard_type.value_counts().to_dict(),'bao_formats':x.bao_label.fillna('NA').value_counts().to_dict()}
(ROOT/'derived'/'chembl_numeric_dataset_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print(summary)
