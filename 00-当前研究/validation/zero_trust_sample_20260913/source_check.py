import ast, json, hashlib, subprocess
from pathlib import Path
import numpy as np
import pandas as pd
from rdkit import Chem, DataStructs
from rdkit.Chem import rdFingerprintGenerator
from rdkit.Chem.Scaffolds import MurckoScaffold
from rdkit.ML.Cluster import Butina
from sklearn.metrics import roc_auc_score

W=Path(r'D:\zcode-workspace'); R=W/'aidd-repo-work'; H=W/'整理/03-课题-MASH研究-v2/mash_v2_new'; D=R/'03-课题-MASH研究-v2'; OUT=Path(__file__).parent
sha=lambda b:hashlib.sha256(b).hexdigest()
files=['data/chembl/FASN_clean.csv','src/s2_chembl.py','src/s3_qsar.py','results/tables/FASN_cluster_split_testpred.csv','results/tables/s3_qsar_metrics.json','docking/receptors/THRB_2J4A.pdbqt','data/pdb/2J4A.pdb','results/tables/np_docking_raw_new.csv']
hashes=[]
for name in files:
    original=(H/name).read_bytes(); current=(D/name).read_bytes(); git=subprocess.check_output(['git','show','1c0a37a:03-课题-MASH研究-v2/'+name],cwd=R)
    hashes.append(dict(file=name,historical_sha=sha(original),current_sha=sha(current),git_sha=sha(git),original_current_equal=original==current,original_git_equal=original==git,original_git_text_equal=original.replace(b'\r\n',b'\n')==git.replace(b'\r\n',b'\n')))
code=(H/'src/s3_qsar.py').read_text(encoding='utf-8-sig'); tree=ast.parse(code)
ns=dict(np=np,pd=pd,Butina=Butina,DataStructs=DataStructs)
for node in tree.body:
    if isinstance(node,ast.FunctionDef) and node.name in ['butina_clusters','cluster_split']:
        exec(compile(ast.Module(body=[node],type_ignores=[]),'<original functions only>','exec'),ns)
df=pd.read_csv(H/'data/chembl/FASN_clean.csv'); gen=rdFingerprintGenerator.GetMorganGenerator(radius=2,fpSize=2048)
fps=[gen.GetFingerprint(Chem.MolFromSmiles(s)) for s in df.std_smiles]
tr,va,te=ns['cluster_split'](ns['butina_clusters'](fps),seed=42)
pred=pd.read_csv(H/'results/tables/FASN_cluster_split_testpred.csv')
sims=[max(DataStructs.BulkTanimotoSimilarity(fps[i],[fps[j] for j in tr])) for i in te]
sc=[MurckoScaffold.MurckoScaffoldSmiles(smiles=s) for s in df.std_smiles]
sample=df.iloc[tr].sample(10,random_state=913)
sample.assign(original_row_id=sample.index,provenance='no persisted per-activity mapping in original pipeline').to_csv(OUT/'source_ten_training_molecules.csv',index=False)
gate=pd.read_json(W/'p0_refs/gate_run/raw_results.json'); gate=gate[gate.label.isin(['active','negative_floor'])&gate.score.notna()]; resid=gate.score-np.polyval(np.polyfit(gate.mw,gate.score,1),gate.mw)
gatecopy=R/'00-当前研究/fifth_round_20260912/raw/source_old_gate_metrics'
fx=R/'00-当前研究/candidate_decision_20260910/derived/fxr_locked_model'; p=pd.read_csv(fx/'locked_test_predictions.csv')
report={'hashes':hashes,'FASN_original_split':dict(n=list(map(len,[tr,va,te])),seed_argument=42,seed_used_for_random_assignment=False,saved_y_equal=bool(np.allclose(df.pIC50.iloc[te],pred.y)),similarity_ge08=sum(s>=.8 for s in sims),shared_scaffold=sum(sc[i] in {sc[j] for j in tr} for i in te),row_overlap=len(set(tr)&set(te)),persisted_split_files=[str(p.relative_to(H)) for p in H.rglob('*split*') if p.is_file()]),'provenance':{'sample_n':10,'persisted_columns':list(df.columns),'sample_replicates':sample.n_rep.tolist(),'complete_activity_mapping_found':False},'gate':{'original_code':str(W/'p0_refs/run_discrimination.py'),'saved':json.loads((W/'p0_refs/gate_run/gate_metrics.json').read_text()),'correct_residual_AUC':roc_auc_score(gate.label.eq('active'),-resid),'copied_metrics_hash_equal':sha(gatecopy.read_bytes())==sha((W/'p0_refs/gate_run/gate_metrics.json').read_bytes())},'FXR':{'labels_equal_ge8':bool(np.array_equal(p.observed_label,p.observed_pActivity_nM>=8)),'labels_different_from_ge7':int(np.sum(p.observed_label!=(p.observed_pActivity_nM>=7))),'threshold_nM':10**(9-8),'original_separate_asset_found':False}}
(OUT/'source_results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
