import pandas as pd, numpy as np, json
from pathlib import Path
from sklearn.model_selection import GroupShuffleSplit
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.metrics import roc_auc_score, mean_absolute_error
from rdkit import Chem
from rdkit.Chem import AllChem, Descriptors
ROOT=Path(r'D:\zcode-workspace\aidd-repo-work\00-当前研究\candidate_decision_20260910')
p=ROOT/'derived'/'chembl_numeric_nM_exact_candidates.csv'
df=pd.read_csv(p,low_memory=False)
# Conservative pilot strata: separate target and assay format/end point; only strata with >=50 rows.
rows=[]; metrics=[]
for (target,typ,bao),x in df.groupby(['target_label','standard_type','bao_label'],dropna=False):
    if len(x)<50: continue
    x=x.dropna(subset=['canonical_smiles','pActivity_nM']).copy()
    if len(x)<50: continue
    # remove exact duplicate molecule rows only for a simple audit, not for production training
    x=x.drop_duplicates(subset=['molecule_chembl_id','assay_chembl_id','standard_value','standard_relation'])
    mols=x['molecule_chembl_id'].astype(str)
    # ECFP counts, no pooling across assays
    X=[]; keep=[]
    for idx,s in zip(x.index,x.canonical_smiles):
        m=Chem.MolFromSmiles(str(s))
        if m is None: continue
        fp=AllChem.GetMorganFingerprintAsBitVect(m,2,nBits=1024)
        X.append(np.asarray(fp,dtype=np.uint8)); keep.append(idx)
    if len(X)<50: continue
    x=x.loc[keep]; X=np.asarray(X); y=x.pActivity_nM.to_numpy(float)
    groups=x['molecule_chembl_id'].astype(str).to_numpy()
    # scaffold-like grouping proxy by molecule identity: held-out molecules, not a full scaffold split
    splitter=GroupShuffleSplit(n_splits=1,test_size=0.2,random_state=20260910)
    tr,te=next(splitter.split(X,y,groups=groups))
    model=RandomForestRegressor(n_estimators=200,random_state=20260910,n_jobs=8,min_samples_leaf=2)
    model.fit(X[tr],y[tr]); pred=model.predict(X[te])
    mae=mean_absolute_error(y[te],pred)
    # binary exploratory label at pActivity >= 6 (1 uM) only within this stratum
    yy=(y>=6).astype(int)
    auc=None
    if len(np.unique(yy[te]))==2:
        clf=RandomForestClassifier(n_estimators=200,random_state=20260910,n_jobs=8,min_samples_leaf=2,class_weight='balanced')
        clf.fit(X[tr],yy[tr]); prob=clf.predict_proba(X[te])[:,1]
        if len(np.unique(yy[tr]))==2: auc=roc_auc_score(yy[te],prob)
    metrics.append({'target_label':target,'standard_type':typ,'bao_label':bao,'n_after_dedupe':len(x),'n_train':len(tr),'n_test':len(te),'mae_pActivity_nM':mae,'exploratory_auc_threshold_pActivity6':auc,'split':'group by molecule_chembl_id; not external validation','status':'pilot_only_not_final_model'})
    # Save one representative pilot predictions table per stratum for audit
    for i,j in zip(te,pred): rows.append({'target_label':target,'standard_type':typ,'bao_label':bao,'molecule_chembl_id':x.iloc[i]['molecule_chembl_id'],'assay_chembl_id':x.iloc[i]['assay_chembl_id'],'observed_pActivity_nM':float(y[i]),'predicted_pActivity_nM':float(j)})

pd.DataFrame(metrics).to_csv(ROOT/'derived'/'chembl_pilot_model_metrics.csv',index=False,encoding='utf-8-sig')
pd.DataFrame(rows).to_csv(ROOT/'derived'/'chembl_pilot_predictions.csv',index=False,encoding='utf-8-sig')
(ROOT/'derived'/'chembl_pilot_model_summary.json').write_text(json.dumps({'generated_at':'2026-09-10','purpose':'auditable pilot only','metrics':metrics,'limitations':['no locked external validation set','no scaffold split yet','heterogeneous assay endpoints retained separately','not used to release candidate ranking','threshold pActivity=6 is exploratory and not a universal efficacy standard']},ensure_ascii=False,indent=2),encoding='utf-8')
print(pd.DataFrame(metrics).to_string(index=False))
