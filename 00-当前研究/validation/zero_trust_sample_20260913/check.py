import json, math, importlib.util, concurrent.futures
from pathlib import Path
import numpy as np
import pandas as pd
from rdkit import Chem, DataStructs
from rdkit.Chem import rdFingerprintGenerator
from rdkit.Chem.Scaffolds import MurckoScaffold
from rdkit.ML.Cluster import Butina
from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import roc_auc_score

OUT=Path(__file__).parent; ROOT=OUT.parent.parent; OLD=ROOT.parent/'03-课题-MASH研究-v2'
spec=importlib.util.spec_from_file_location('rest',r'C:\Users\user\.agents\skills\chembl-skill\scripts\rest_request.py'); rest=importlib.util.module_from_spec(spec); spec.loader.exec_module(rest)
def query(params,limit=10):
    return rest.execute(dict(base_url='https://www.ebi.ac.uk/chembl/api/data',path='activity.json',params={**params,'limit':limit},record_path='activities',max_items=max(limit,60),max_depth=12,timeout_sec=50))
def metrics(y,p):
    y=np.array(y); p=np.array(p); return dict(n=len(y),RMSE=float(np.sqrt(np.mean((y-p)**2))),R2=float(1-np.sum((y-p)**2)/np.sum((y-y.mean())**2)))
summary={}
f=pd.read_csv(OLD/'data/chembl/FASN_clean.csv'); pred=pd.read_csv(OLD/'results/tables/FASN_cluster_split_testpred.csv')
summary['FASN_metrics']=metrics(pred.y,pred.pred)
gen=rdFingerprintGenerator.GetMorganGenerator(radius=2,fpSize=2048)
fps=[gen.GetFingerprint(Chem.MolFromSmiles(s)) for s in f.std_smiles]
# Reconstruct archived split only; no fitting. Deliberately reproduce its wrong upper-triangle order.
dist=[1-DataStructs.TanimotoSimilarity(fps[i],fps[j]) for i in range(len(fps)) for j in range(i+1,len(fps))]
cl=Butina.ClusterData(dist,len(fps),.4,isDistData=True); labels=np.zeros(len(f),int)
for k,ids in enumerate(cl): labels[list(ids)]=k
tr=[]; va=[]; te=[]
for k in pd.Series(labels).value_counts().index:
    dest=tr if len(tr)/len(f)<.8 else va if len(va)/len(f)<.1 else te
    dest.extend(np.where(labels==k)[0].tolist())
sims=[max(DataStructs.BulkTanimotoSimilarity(fps[i],[fps[j] for j in tr])) for i in te]
sc=[MurckoScaffold.MurckoScaffoldSmiles(smiles=s) for s in f.std_smiles]
summary['FASN_split']=dict(counts=list(map(len,[tr,va,te])),saved_y_matches=bool(len(te)==len(pred) and np.allclose(f.pIC50.iloc[te],pred.y)),row_overlap=len(set(tr)&set(te)),smiles_overlap=len(set(f.std_smiles.iloc[tr])&set(f.std_smiles.iloc[te])),test_similarity_ge_08=sum(s>=.8 for s in sims),test_shared_scaffold=sum(sc[i] in {sc[j] for j in tr} for i in te),max_similarity=float(max(sims)) if sims else None)
d=ROOT/'candidate_decision_20260910/derived'; x=pd.read_csv(d/'chembl_numeric_nM_exact_candidates.csv',low_memory=False)
fx=x[(x.target_label=='fxr')&(x.standard_type=='EC50')&(x.bao_label=='single protein format')&(x.assay_chembl_id=='CHEMBL5735838')&(x.standard_flag==1)&(x.standard_relation=='=')&(x.potential_duplicate==0)].dropna(subset=['canonical_smiles','pActivity_nM']).drop_duplicates('molecule_chembl_id').copy()
fx['scaffold']=fx.canonical_smiles.map(lambda s:MurckoScaffold.MurckoScaffoldSmiles(smiles=s))
a,b=next(GroupShuffleSplit(n_splits=1,test_size=.2,random_state=20260910).split(fx,groups=fx.scaffold))
p=pd.read_csv(d/'fxr_locked_model/locked_test_predictions.csv')
summary['FXR_metrics']={**metrics(p.observed_pActivity_nM,p.predicted_pActivity_nM),'AUC':roc_auc_score(p.observed_label,p.predicted_active_probability),'threshold8_label_matches':bool(np.array_equal(p.observed_label,p.observed_pActivity_nM>=8))}
summary['FXR_split']=dict(test_ids_match=set(fx.iloc[b].molecule_chembl_id)==set(p.molecule_chembl_id),molecule_overlap=len(set(fx.iloc[a].molecule_chembl_id)&set(fx.iloc[b].molecule_chembl_id)),scaffold_overlap=len(set(fx.iloc[a].scaffold)&set(fx.iloc[b].scaffold)),canonical_overlap=len(set(fx.iloc[a].canonical_smiles)&set(fx.iloc[b].canonical_smiles)))
g=pd.read_json(r'D:\zcode-workspace\p0_refs\gate_run\raw_results.json'); g=g[g.score.notna() & g.label.isin(['active','negative_floor'])]; yy=g.label.eq('active').astype(int)
res=g.score-np.polyval(np.polyfit(g.mw,g.score,1),g.mw)
summary['old_docking_gate']={'AUC_negative_score':roc_auc_score(yy,-g.score),'MW_residual_AUC_negative_residual':roc_auc_score(yy,-res)}
# Fixed-seed stratified sample of 12 archived activity records, independently refetched by ID.
raw=pd.read_csv(d/'chembl_activity_all_targets.csv',low_memory=False)
sample=pd.concat([raw[(raw.target_label==t)&raw.standard_value.notna()].sample(6,random_state=913) for t in ['thrb','fxr']])
def check_group(z):
    out=query({'activity_id__in':','.join(z.activity_id.astype(int).astype(str))})
    return out
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
    jobs=[pool.submit(check_group,z) for _,z in sample.groupby('target_label')]
    fj=pool.submit(query,{'target_chembl_id':'CHEMBL4158','standard_type':'IC50','standard_relation':'=','standard_units':'nM','assay_type':'B','offset':int(np.random.default_rng(913).integers(0,500))})
    online=[j.result() for j in jobs]; fas=fj.result()
checks=[]
keys=['standard_value','standard_relation','standard_units','standard_type','assay_chembl_id','target_chembl_id','document_chembl_id','molecule_chembl_id']
for _,r in sample.iterrows():
    found=[v for o in online for v in o.get('records',[]) if str(v.get('activity_id'))==str(int(r.activity_id))]
    errors=[]
    if found:
        for k in keys:
            aa=r[k]; bb=found[0].get(k)
            if k=='standard_value': same=math.isclose(float(aa),float(bb),rel_tol=1e-10)
            else: same=('' if pd.isna(aa) else str(aa))==('' if bb is None else str(bb))
            if not same: errors.append(k)
    checks.append(dict(target=r.target_label,activity_id=int(r.activity_id),status='无法核验' if not found else '错误' if errors else '正确',mismatch=errors))
for r in fas.get('records',[])[:8]:
    smi=Chem.MolToSmiles(Chem.MolFromSmiles(r['canonical_smiles'])); match=f[f.std_smiles==smi]; pc=9-math.log10(float(r['standard_value']))
    # No archived activity IDs: exact single-replicate value match is corroboration, not full provenance verification.
    checks.append(dict(target='FASN',activity_id=r['activity_id'],status='无法核验',online_value=r['standard_value'],online_relation=r['standard_relation'],online_unit=r['standard_units'],assay=r['assay_chembl_id'],document=r['document_chembl_id'],target_id=r['target_chembl_id'],old_rows=len(match),old_nrep=match.n_rep.tolist(),old_pic50=match.pIC50.tolist(),recalculated=pc,value_matches=bool(len(match) and np.any(np.isclose(match.pIC50,pc)))))
conv=x[x.target_label.isin(['fxr','thrb'])].sample(10,random_state=913).copy(); conv['recalculated']=[9-math.log10(float(v)) for v in conv.standard_value]; conv['abs_error']=abs(conv.recalculated-conv.pActivity_nM)
summary['conversions']=dict(n=10,max_error=float(conv.abs_error.max()),nonexact_in_numeric=int((x.standard_relation!='=').sum()),non_nM=int((x.standard_units!='nM').sum()),invalid_smiles=sum(Chem.MolFromSmiles(s) is None for s in conv.canonical_smiles),salt_rows=int(conv.canonical_smiles.str.contains('.',regex=False).sum()))
summary['raw_sample']=checks; summary['api_errors']=[o for o in online+[fas] if not o.get('ok')]
(OUT/'results.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
conv[['activity_id','standard_value','standard_relation','standard_units','pActivity_nM','recalculated','abs_error']].to_csv(OUT/'ten_recalculations.csv',index=False)
print(json.dumps(summary,ensure_ascii=False,indent=2))
