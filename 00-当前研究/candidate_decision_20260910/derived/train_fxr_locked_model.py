from __future__ import annotations
import json, hashlib, joblib, warnings
from pathlib import Path
import numpy as np
import pandas as pd
from rdkit import Chem, DataStructs
from rdkit.Chem import AllChem, Descriptors, Lipinski, rdMolDescriptors
from rdkit.Chem.Scaffolds import MurckoScaffold
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.dummy import DummyRegressor, DummyClassifier
from sklearn.metrics import (mean_absolute_error, mean_squared_error, roc_auc_score,
                             average_precision_score, precision_recall_curve, brier_score_loss)
from scipy.stats import spearmanr
from sklearn.model_selection import GroupShuffleSplit
from sklearn.inspection import permutation_importance
warnings.filterwarnings('ignore')

ROOT=Path(r'D:\zcode-workspace\aidd-repo-work\00-当前研究\candidate_decision_20260910')
DATA=ROOT/'derived'/'chembl_numeric_nM_exact_candidates.csv'
OUT=ROOT/'derived'/'fxr_locked_model'
OUT.mkdir(parents=True,exist_ok=True)
ASSAY='CHEMBL5735838'
TARGET='fxr'
ENDPOINT='EC50'
BAO='single protein format'
SEED=20260910
N_BITS=2048
THRESHOLD=8.0 # pActivity (nM scale): 100 nM; assay-specific exploratory label only
TOP_K=10

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def mol_from_smiles(s):
    try: return Chem.MolFromSmiles(str(s))
    except Exception: return None
def fp(m): return np.asarray(AllChem.GetMorganFingerprintAsBitVect(m,2,nBits=N_BITS),dtype=np.uint8)
def desc(m):
    return np.array([Descriptors.MolWt(m),Descriptors.MolLogP(m),rdMolDescriptors.CalcTPSA(m),Lipinski.NumHDonors(m),Lipinski.NumHAcceptors(m),Lipinski.NumRotatableBonds(m),rdMolDescriptors.CalcNumAromaticRings(m)],dtype=float)
def scaffold(s):
    m=mol_from_smiles(s)
    if m is None: return ''
    x=MurckoScaffold.MurckoScaffoldSmiles(mol=m)
    return x or '[NO_SCAFFOLD]'
def build_features(smiles):
    Xfp=[]; Xd=[]; keep=[]
    for i,s in enumerate(smiles):
        m=mol_from_smiles(s)
        if m is None: continue
        Xfp.append(fp(m)); Xd.append(desc(m)); keep.append(i)
    return np.asarray(Xfp),np.asarray(Xd),keep

df=pd.read_csv(DATA,low_memory=False)
x=df[(df.target_label==TARGET)&(df.standard_type==ENDPOINT)&(df.bao_label==BAO)&(df.assay_chembl_id==ASSAY)&(df.standard_flag==1)&(df.standard_relation=='=')& (df.potential_duplicate==0)].copy()
x=x.dropna(subset=['canonical_smiles','pActivity_nM'])
x=x.drop_duplicates(subset=['molecule_chembl_id'],keep='first').reset_index(drop=True)
x['scaffold']=x.canonical_smiles.map(scaffold)
x['label']=(x.pActivity_nM>=THRESHOLD).astype(int)
Xfp,Xd,keep=build_features(x.canonical_smiles.tolist())
x=x.iloc[keep].reset_index(drop=True)
assert len(x)==len(Xfp)==len(Xd)
y=x.pActivity_nM.to_numpy(float); yc=x.label.to_numpy(int); groups=x.scaffold.to_numpy(str)

# Deterministic group split with a predeclared fallback list; no score-based seed search.
split_log=[]
for split_seed in [SEED,42,123,7,20260911]:
    g1=GroupShuffleSplit(n_splits=1,test_size=0.20,random_state=split_seed)
    trdev,te=next(g1.split(Xfp,y,groups))
    g2=GroupShuffleSplit(n_splits=1,test_size=0.25,random_state=split_seed+1)
    trrel,devrel=next(g2.split(Xfp[trdev],y[trdev],groups[trdev]))
    tr=trdev[trrel]; dev=trdev[devrel]
    split_log.append({'seed':split_seed,'train':len(tr),'dev':len(dev),'test':len(te),'test_classes':sorted(set(yc[te].tolist())),'train_scaffolds':len(set(groups[tr])),'dev_scaffolds':len(set(groups[dev])),'test_scaffolds':len(set(groups[te]))})
    if len(set(yc[te]))==2 and len(set(yc[tr]))==2:
        break
else:
    # retain first split if class balance is structurally unavailable, but mark AUC unavailable
    split_seed=SEED; trdev,te=next(GroupShuffleSplit(n_splits=1,test_size=0.20,random_state=SEED).split(Xfp,y,groups)); trrel,devrel=next(GroupShuffleSplit(n_splits=1,test_size=0.25,random_state=SEED+1).split(Xfp[trdev],y[trdev],groups[trdev])); tr=trdev[trrel]; dev=trdev[devrel]

# Fixed hyperparameters; dev is not used for tuning in this first locked model.
rf_params={'n_estimators':500,'random_state':SEED,'n_jobs':8,'min_samples_leaf':2,'max_features':'sqrt'}
reg=RandomForestRegressor(**rf_params)
reg.fit(Xfp[tr],y[tr]); pred_te=reg.predict(Xfp[te]); pred_dev=reg.predict(Xfp[dev])
# Simple descriptor baseline and mean baseline.
dreg=RandomForestRegressor(**rf_params); dreg.fit(Xd[tr],y[tr]); dpred=dreg.predict(Xd[te])
meanreg=DummyRegressor(strategy='mean').fit(Xfp[tr],y[tr]); mpred=meanreg.predict(Xfp[te])
# Classifier for exploratory threshold, fixed and independent from regression.
clf=RandomForestClassifier(**rf_params,class_weight='balanced_subsample'); clf.fit(Xfp[tr],yc[tr]); prob_te=clf.predict_proba(Xfp[te])[:,1] if len(clf.classes_)==2 else np.repeat(float(clf.classes_[0]),len(te))
dclf=RandomForestClassifier(**rf_params,class_weight='balanced_subsample'); dclf.fit(Xd[tr],yc[tr]); dprob=dclf.predict_proba(Xd[te])[:,1] if len(dclf.classes_)==2 else np.repeat(float(dclf.classes_[0]),len(te))

# Metrics.
def regmetrics(yv,pv):
    return {'MAE':float(mean_absolute_error(yv,pv)),'RMSE':float(mean_squared_error(yv,pv)**0.5),'Spearman':float(spearmanr(yv,pv).statistic) if len(set(yv))>1 else None}
def clfmetrics(yv,pv):
    if len(set(yv))<2: return {'ROC_AUC':None,'PR_AUC':None,'Brier':None,'positive_rate':float(np.mean(yv)),'reason':'locked test has one class'}
    return {'ROC_AUC':float(roc_auc_score(yv,pv)),'PR_AUC':float(average_precision_score(yv,pv)),'Brier':float(brier_score_loss(yv,pv)),'positive_rate':float(np.mean(yv))}

def bootstrap_metric(yv,pv,kind,n=2000):
    rng=np.random.default_rng(SEED+99); vals=[]; N=len(yv)
    for _ in range(n):
        ix=rng.integers(0,N,N); yy=yv[ix]; pp=pv[ix]
        try:
            v=roc_auc_score(yy,pp) if kind=='auc' and len(set(yy))==2 else average_precision_score(yy,pp) if kind=='pr' and len(set(yy))==2 else mean_absolute_error(yy,pp) if kind=='mae' else None
            if v is not None and np.isfinite(v): vals.append(float(v))
        except Exception: pass
    if len(vals)<100: return {'n_boot':len(vals),'lo':None,'median':None,'hi':None}
    q=np.quantile(vals,[.025,.5,.975]); return {'n_boot':len(vals),'lo':float(q[0]),'median':float(q[1]),'hi':float(q[2])}

def topk_enrichment(yv,pv,k):
    k=min(k,len(yv)); order=np.argsort(-pv)[:k]; hit=int(yv[order].sum()); rate=float(np.mean(yv)); expected=k*rate; ef=float(hit/expected) if expected>0 else None
    return {'k':k,'hits':hit,'test_positive_rate':rate,'random_expected_hits':float(expected),'enrichment_factor':ef,'theoretical_max_enrichment':float(min(k,int(yv.sum()))/expected) if expected>0 else None}

metrics={'locked_test_regression':regmetrics(y[te],pred_te),'descriptor_baseline_regression':regmetrics(y[te],dpred),'mean_baseline_regression':regmetrics(y[te],mpred),'locked_test_classification':clfmetrics(yc[te],prob_te),'descriptor_baseline_classification':clfmetrics(yc[te],dprob),'topk':topk_enrichment(yc[te],prob_te,TOP_K),'bootstrap':{'ROC_AUC':bootstrap_metric(yc[te],prob_te,'auc'),'PR_AUC':bootstrap_metric(yc[te],prob_te,'pr'),'MAE':bootstrap_metric(y[te],pred_te,'mae')}}
# Use dev only as a separately reported development diagnostic.
metrics['development_regression']=regmetrics(y[dev],pred_dev); metrics['development_classification']=clfmetrics(yc[dev],clf.predict_proba(Xfp[dev])[:,1] if len(clf.classes_)==2 else np.repeat(0.0,len(dev)))

# Locked test table.
def pred_rows(ix,pred,prob):
 out=[]
 for j,p,q in zip(ix,pred,prob): out.append({'molecule_chembl_id':x.iloc[j].molecule_chembl_id,'assay_chembl_id':x.iloc[j].assay_chembl_id,'scaffold':x.iloc[j].scaffold,'observed_pActivity_nM':float(y[j]),'observed_label':int(yc[j]),'predicted_pActivity_nM':float(p),'predicted_active_probability':float(q)})
 return out
pd.DataFrame(pred_rows(te,pred_te,prob_te)).to_csv(OUT/'locked_test_predictions.csv',index=False,encoding='utf-8-sig')
pd.DataFrame(pred_rows(dev,pred_dev,clf.predict_proba(Xfp[dev])[:,1] if len(clf.classes_)==2 else np.repeat(0.0,len(dev)))).to_csv(OUT/'development_predictions.csv',index=False,encoding='utf-8-sig')
# Refit fixed models on train+dev after locked test evaluation.
fit=np.concatenate([tr,dev]); reg_final=RandomForestRegressor(**rf_params).fit(Xfp[fit],y[fit]); clf_final=RandomForestClassifier(**rf_params,class_weight='balanced_subsample').fit(Xfp[fit],yc[fit])
joblib.dump(reg_final,OUT/'fxr_lantha_ec50_ecfp_rf_regressor.joblib'); joblib.dump(clf_final,OUT/'fxr_lantha_ec50_ecfp_rf_classifier.joblib')
# Feature/spec manifest.
manifest={'model_id':'FXR_LanthaScreen_EC50_ECFP_RF_v1','generated_at':'2026-09-10','target':'human FXR / CHEMBL2047','assay':'CHEMBL5735838','endpoint':'EC50','format':'single protein / purified FXR-LBD coactivator FRET (assay description retained in source table)','source_csv':str(DATA),'source_sha256':sha(DATA),'input_records_after_filter':len(x),'unique_molecules':int(x.molecule_chembl_id.nunique()),'unique_scaffolds':int(x.scaffold.nunique()),'filter':['standard_flag=1','standard_relation==','standard_units=nM','potential_duplicate=0','target_label=fxr','standard_type=EC50','bao_label=single protein format','assay_chembl_id=CHEMBL5735838','one median/first exact molecule record per molecule_chembl_id within this assay'], 'feature':'Morgan/ECFP radius2, 2048 bits','regressor':rf_params,'classifier':{**rf_params,'class_weight':'balanced_subsample'},'threshold_pActivity':THRESHOLD,'threshold_note':'exploratory assay-specific label (100 nM); not a universal efficacy threshold','split_seed_used':split_seed,'split_algorithm':'GroupShuffleSplit by Murcko scaffold; outer test=20%; inner dev=20% of total; fallback seeds predeclared [20260910,42,123,7,20260911] only to avoid one-class test','split_counts':{'train':len(tr),'development':len(dev),'locked_test':len(te)},'scaffold_counts':{'train':len(set(groups[tr])),'development':len(set(groups[dev])),'locked_test':len(set(groups[te]))},'split_log':split_log,'locked_test_not_used_for_training':True,'final_fit_records':len(fit),'status':'locked_internal_scaffold_test_completed; not external validation; release only if predefined lower-bound and enrichment criteria pass'}
(OUT/'model_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'locked_test_metrics.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2),encoding='utf-8')
# Candidate predictions: exploratory only, with nearest training similarity and RF uncertainty.
ident=pd.read_csv(ROOT/'library_identity.csv',encoding='utf-8-sig')
cs=[]; crows=[]
for _,r in ident.iterrows():
    m=mol_from_smiles(r['source_smiles_raw'])
    if m is None: continue
    f=fp(m); p=float(reg_final.predict(f.reshape(1,-1))[0]); prob=float(clf_final.predict_proba(f.reshape(1,-1))[:,1][0]) if len(clf_final.classes_)==2 else float(clf_final.classes_[0])
    sims=[]
    for z in fit:
        sims.append(DataStructs.TanimotoSimilarity(Chem.RDKFingerprint(m),Chem.RDKFingerprint(mol_from_smiles(x.iloc[z].canonical_smiles))))
    # ECFP nearest similarity for domain reporting; use the same ECFP bits via bit vectors.
    bv=AllChem.GetMorganFingerprintAsBitVect(m,2,nBits=N_BITS); sims2=[]
    for z in fit:
        mz=mol_from_smiles(x.iloc[z].canonical_smiles); sims2.append(DataStructs.TanimotoSimilarity(bv,AllChem.GetMorganFingerprintAsBitVect(mz,2,nBits=N_BITS)))
    # tree-wise spread as an informal uncertainty signal.
    tree_preds=np.array([est.predict(f.reshape(1,-1))[0] for est in reg_final.estimators_])
    crows.append({'record_id':r['record_id'],'candidate':r['preferred_name'],'inchikey':r['inchikey'],'predicted_pActivity_nM':p,'predicted_active_probability':prob,'rf_tree_sd_pActivity':float(np.std(tree_preds,ddof=1)),'nearest_train_tanimoto_ecfp':float(max(sims2) if sims2 else 0.0),'model_use':'exploratory hypothesis only; not candidate release'})
pd.DataFrame(crows).to_csv(ROOT/'derived'/'fxr_model_predictions_54_exploratory.csv',index=False,encoding='utf-8-sig')
# Overall verdict using predeclared release criteria.
auc=metrics['locked_test_classification']['ROC_AUC']; auc_ci=metrics['bootstrap']['ROC_AUC']['lo']; ef=metrics['topk']['enrichment_factor'];
verdict={'criteria':{'locked_test_roc_auc_lower_bound_gt_0.5':bool(auc_ci is not None and auc_ci>0.5),'topk_enrichment_over_random':bool(ef is not None and ef>1),'property_baseline_comparison_reported':True},'values':{'locked_test_roc_auc':auc,'locked_test_roc_auc_95ci':metrics['bootstrap']['ROC_AUC'],'topk':metrics['topk'],'regression':metrics['locked_test_regression'],'descriptor_baseline':metrics['descriptor_baseline_regression']},'decision':'eligible_for_exploratory_model_assisted_use' if (auc_ci is not None and auc_ci>0.5 and ef is not None and ef>1) else 'not_eligible_to_lead_candidate_ranking','reason':'criteria are project-specific development rules, not drug efficacy standards; this is an internal scaffold split, not external validation'}
(OUT/'model_verdict.json').write_text(json.dumps(verdict,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'records':len(x),'scaffolds':int(x.scaffold.nunique()),'split':manifest['split_counts'],'metrics':metrics,'verdict':verdict},ensure_ascii=False,indent=2))
