import pandas as pd, numpy as np, json, joblib
from pathlib import Path
from rdkit import Chem
from rdkit.Chem.Scaffolds import MurckoScaffold
from rdkit.Chem import AllChem
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupShuffleSplit
ROOT=Path(r'D:\zcode-workspace\aidd-repo-work\00-当前研究\candidate_decision_20260910')
SRC=ROOT/'derived'/'chembl_numeric_nM_exact_candidates.csv'
df=pd.read_csv(SRC,low_memory=False)
strata=[('fxr','EC50','single protein format'),('thrb','IC50','single protein format'),('thra','IC50','single protein format')]
metrics=[]; lock=[]
for target,typ,bao in strata:
 x=df[(df.target_label==target)&(df.standard_type==typ)&(df.bao_label==bao)].copy()
 x=x.dropna(subset=['canonical_smiles','pActivity_nM']).drop_duplicates(subset=['molecule_chembl_id','assay_chembl_id','standard_value','standard_relation'])
 scaffold=[]; X=[]; keep=[]
 for idx,s in zip(x.index,x.canonical_smiles):
  m=Chem.MolFromSmiles(str(s))
  if m is None: continue
  sm=MurckoScaffold.MurckoScaffoldSmiles(mol=m,includeChirality=False)
  fp=AllChem.GetMorganFingerprintAsBitVect(m,2,nBits=1024)
  scaffold.append(sm or 'ACYCLIC'); X.append(np.asarray(fp,dtype=np.uint8)); keep.append(idx)
 x=x.loc[keep].copy(); x['scaffold_id']=scaffold; X=np.asarray(X); y=x.pActivity_nM.to_numpy(float); groups=x.scaffold_id.to_numpy()
 # deterministic scaffold group split; choose first split with both test and train sizes meaningful
 split=GroupShuffleSplit(n_splits=20,test_size=.2,random_state=20260910)
 chosen=None
 for tr,te in split.split(X,y,groups=groups):
  if len(tr)>=30 and len(te)>=10 and len(set(groups[te]))>=3:
   chosen=(tr,te); break
 if chosen is None: raise RuntimeError((target,typ,bao,len(x)))
 tr,te=chosen
 model=RandomForestRegressor(n_estimators=400,random_state=20260910,n_jobs=8,min_samples_leaf=2,max_features='sqrt')
 model.fit(X[tr],y[tr]); pred=model.predict(X[te])
 baseline=np.repeat(np.mean(y[tr]),len(te))
 m={'target_label':target,'standard_type':typ,'bao_label':bao,'n_records':len(x),'n_scaffolds':len(set(groups)),'n_train':len(tr),'n_test':len(te),'train_scaffolds':len(set(groups[tr])),'test_scaffolds':len(set(groups[te])),'mae_model':mean_absolute_error(y[te],pred),'mae_mean_baseline':mean_absolute_error(y[te],baseline),'rmse_model':mean_squared_error(y[te],pred)**0.5,'r2_model':r2_score(y[te],pred) if len(te)>1 else None,'seed':20260910,'split':'Bemis-Murcko scaffold group holdout; exploratory lock','status':'pilot_locked_stratum_not_external_validation'}
 metrics.append(m)
 for i in tr: lock.append({'target_label':target,'standard_type':typ,'bao_label':bao,'molecule_chembl_id':x.iloc[i].molecule_chembl_id,'scaffold_id':x.iloc[i].scaffold_id,'split':'development'})
 for i in te: lock.append({'target_label':target,'standard_type':typ,'bao_label':bao,'molecule_chembl_id':x.iloc[i].molecule_chembl_id,'scaffold_id':x.iloc[i].scaffold_id,'split':'locked_test'})
 joblib.dump(model,ROOT/'derived'/f'pilot_model_{target}_{typ}_{bao.replace(" ","_")}.joblib')
# outputs
pd.DataFrame(metrics).to_csv(ROOT/'derived'/'chembl_locked_scaffold_metrics.csv',index=False,encoding='utf-8-sig')
pd.DataFrame(lock).to_csv(ROOT/'derived'/'chembl_locked_scaffold_manifest.csv',index=False,encoding='utf-8-sig')
(ROOT/'derived'/'chembl_locked_scaffold_summary.json').write_text(json.dumps({'generated_at':'2026-09-10','strata':metrics,'limitations':['locked test is computational holdout, not external prospective validation','assay heterogeneity is reduced but not eliminated','no tuning after locked split; this pilot does not authorize candidate ranking','future final model requires manual assay/endpoint review and true independent validation']},ensure_ascii=False,indent=2),encoding='utf-8')
print(pd.DataFrame(metrics).to_string(index=False))
