import csv, json, hashlib, shutil, os
from pathlib import Path
from datetime import datetime, timezone

ROOT=Path(r'D:\zcode-workspace\aidd-repo-work\00-当前研究\candidate_decision_20260910')
WS=Path(r'D:\zcode-workspace')
H1=WS/'h1_mash'
P0=WS/'p0_refs'
JOB=Path(r'C:\DockScopeData\workspace\dockscope\data\jobs\H1Valid_20260910_104825_329168')

def sha(p):
    p=Path(p)
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()
def info(path, scope, note=''):
    p=Path(path)
    d={'path':str(p),'scope':scope,'exists':p.exists(),'note':note}
    if p.exists() and p.is_file():
        st=p.stat(); d.update({'size':st.st_size,'mtime':datetime.fromtimestamp(st.st_mtime).isoformat(),'sha256':sha(p)})
    return d

def copy(src, dst):
    dst=Path(dst); dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)

# Required Chinese filenames and stable aliases.
aliases={
 'conclusion_one_page.md':'结论一页纸.md',
 'evidence_matrix.csv':'全库证据矩阵.csv',
 'candidate_comparison.md':'候选比较与淘汰理由.md',
 'method_verdict.md':'方法验收报告.md',
 'minimal_experiment_plan.md':'最小实验验证方案.md',
 'research_increment_vs_literature.md':'研究增量与已有文献对照.md',
 'search_log.md':'检索记录.md',
}
for src,dst in aliases.items(): copy(ROOT/src,ROOT/dst)

# Formal audit files and provenance copies.
rawcopy=ROOT/'raw'/'audits'; rawcopy.mkdir(parents=True,exist_ok=True)
for name in ['repair_audit.json','completion_audit.json','final_receptor_audit.json','protocol_before_results.json','run_valid_created.json','platform_run_final.json','repeat_results.json','repeat_table.json','t3_pose_rmsd_per_seed.json','meo_4seed.json','wt_full54_t3box.json','platform_autopocket_not_used.json']:
    src=H1/name
    if src.exists(): copy(src,rawcopy/name)
for name in ['t3_platform_redock.json','t3_seed7.pdbqt','t3_seed42.pdbqt','t3_seed123.pdbqt','t3_seed20260910.pdbqt']:
    src=H1/name
    if src.exists(): copy(src,rawcopy/name)

# Receptor audit combines the original audit JSONs without altering them.
def load_json(p): return json.loads(Path(p).read_text(encoding='utf-8'))
receptor={
 'generated_at':datetime.now(timezone.utc).isoformat(),
 'run_id':'H1Valid_20260910_104825_329168',
 'scope':'formal limited technical validation; not a scientific activity gate',
 'source_structure':info(P0/'wt_3GWS.pdb','input'),
 'repair_audit':load_json(H1/'repair_audit.json'),
 'completion_audit':load_json(H1/'completion_audit.json'),
 'final_receptor_audit':load_json(H1/'final_receptor_audit.json'),
 'prepared_files':[info(H1/'WTstrict.pdbqt','formal_input'),info(H1/'receptor_final.pdbqt','formal_input'),info(H1/'WTheavy.pdb','formal_input')],
 'limitations':['252-263 intentionally unmodeled gap','PDBFixer pH7.4 hydrogens were intermediate only','final docking uses Meeko templates/Gasteiger, not PROPKA or pH/tautomer ensemble','no WT locked discrimination benchmark'],
 'verdict':'receptor/input preparation passes within formal H1Valid scope; activity/selectivity/efficacy not validated'
}
(ROOT/'receptor_audit.json').write_text(json.dumps(receptor,ensure_ascii=False,indent=2),encoding='utf-8')

# Ligand audit combines 54 identity records and computation inclusion flags.
ident=list(csv.DictReader((ROOT/'library_identity.csv').open(encoding='utf-8-sig')))
formal={'isorhamnetin':'ish','daidzein':'dai','formononetin':'fmn','biochanin A':'bca','moracin N':'mrn'}
controls={'liothyronine':'t3','sobetirome':'gc1','resmetirom':'res'}
with (ROOT/'ligand_audit.csv').open('w',newline='',encoding='utf-8-sig') as f:
    fields=['record_id','preferred_name','brd_id_raw','source_smiles_raw','inchikey','pubchem_cid','automatic_identity_status','manual_tier','review_status','formal_H1Valid_inclusion','formal_brd_id','control_or_candidate','supplementary_full54_summary','identity_risk','calculation_note']
    w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
    for r in ident:
        n=r['preferred_name']; isformal=n in formal or n in controls
        w.writerow({'record_id':r['record_id'],'preferred_name':n,'brd_id_raw':r['brd_id_raw'],'source_smiles_raw':r['source_smiles_raw'],'inchikey':r['inchikey'],'pubchem_cid':r['pubchem_cid'],'automatic_identity_status':r['automatic_identity_status'],'manual_tier':r['manual_tier'],'review_status':r['review_status'],'formal_H1Valid_inclusion':'yes' if isformal else 'no','formal_brd_id':formal.get(n,controls.get(n,'')),'control_or_candidate':'disease_candidate' if n in formal else ('reference_control' if n in controls else 'library_member'),'supplementary_full54_summary':'yes' if n in set(x['preferred_name'] for x in ident) else 'unknown','identity_risk':r['identity_risk'],'calculation_note':'4-seed formal crystal-box result' if isformal else ('WT full54 summary only; incomplete provenance' if n else '')})

# Benchmark manifest, including excluded and failed/blocked batches.
manifest=[
 {'batch_id':'H1Valid_20260910_104825_329168','scope':'formal','target':'3GWS-derived WT THRB','ligands':'8','seeds':'7,42,123,20260910','box':'T3 crystal box [5.157,20.08,29.01] / [22.156,19.867,20.893]','status':'completed','completed':'8','failed':'0','use':'technical repeatability and descriptive poses','exclusion_reason':''},
 {'batch_id':'H1WT_20260910_104421_a8c74f','scope':'diagnostic','target':'3GWS-derived WT THRB','ligands':'8','seeds':'7','box':'unknown from creation snapshot','status':'not_accepted','completed':'0','failed':'0','use':'failure/creation record only','exclusion_reason':'creation JSON remained queued/0 completed in inspected assets'},
 {'batch_id':'H1Full_20260910_104716_d0d5c3','scope':'diagnostic','target':'3GWS-derived WT THRB','ligands':'8','seeds':'7','box':'unknown from creation snapshot','status':'not_accepted','completed':'0','failed':'0','use':'failure/creation record only','exclusion_reason':'creation JSON remained queued/0 completed in inspected assets'},
 {'batch_id':'H1WT-full54_20260910_110607_d3a0cb','scope':'supplementary_unapproved','target':'3GWS-derived WT THRB','ligands':'54','seeds':'single seed summary','box':'T3 crystal box (summary only)','status':'completed_summary','completed':'54','failed':'0','use':'exploratory object selection only','exclusion_reason':'not approved for candidate ranking; summary lacks complete provenance'},
 {'batch_id':'AIDD-TRBWT-3GWS-limval3_20260909_230017_889500','scope':'diagnostic','target':'3GWS WT THRB','ligands':'3','seeds':'varied','box':'historical validation','status':'completed_limited','completed':'3','failed':'0','use':'historical pose recovery only','exclusion_reason':'not same formal H1Valid protocol'},
 {'batch_id':'P0_gate_20260909','scope':'diagnostic','target':'2J4A N331S THRB','ligands':'old benchmark','seeds':'historical','box':'historical','status':'failed_gate','completed':'n/a','failed':'n/a','use':'failure retained','exclusion_reason':'ROC-AUC 0.346; MW residual AUC 0.3527; EF@Top15 1.4637; mutant cannot support WT conclusion'},
]
with (ROOT/'benchmark_manifest.csv').open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.DictWriter(f,fieldnames=list(manifest[0])); w.writeheader(); w.writerows(manifest)

# Pose validation table.
t3=load_json(H1/'t3_pose_rmsd_per_seed.json')
pose=[]
for seed,d in t3.items():
    pose.append({'batch_id':'H1Valid_20260910_104825_329168','ligand':'liothyronine/T3','reported_seed':seed,'engine_seed':'1' if seed=='7' else seed,'metric':'top-scored-pose heavy-atom symmetry-aware RMSD in original receptor frame','rmsd_A':d['rmsd_top_scored_pose'],'threshold_A':2.0,'pass_descriptive':d['rmsd_top_scored_pose']<=2.0,'all_modes_rmsd_A':json.dumps(d['rmsd_all_modes']),'note':'Other modes include ~8 Å; only top-scored pose gate passed'})
with (ROOT/'pose_validation.csv').open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.DictWriter(f,fieldnames=list(pose[0])); w.writeheader(); w.writerows(pose)

# Benchmark results JSON.
repeat=load_json(H1/'repeat_results.json')
repeat_table=load_json(H1/'repeat_table.json')
benchmark={
 'generated_at':datetime.now(timezone.utc).isoformat(),
 'formal_batch':'H1Valid_20260910_104825_329168',
 'protocol':load_json(H1/'protocol_before_results.json'),
 'repeat_table':repeat_table,
 'repeat_records_count':len(repeat),
 'pose_validation':pose,
 'method_verdict':{'receptor_input':'pass_limited','pose_recovery':'descriptive_pass','repeatability':'pass_technical','discrimination':'fail_or_insufficient','candidate_prediction':'not_applicable'},
 'interpretation':'Scores support descriptive pocket-occupancy/reproducibility only; not TRβ activity, TRα selectivity, Kd, MASH efficacy, or safety.',
 'full54_summary':{'path':str(H1/'wt_full54_t3box.json'),'scope':'supplementary_unapproved','records':54,'provenance_complete':False},
 'supplementary_meo':load_json(H1/'meo_4seed.json')
}
(ROOT/'benchmark_results.json').write_text(json.dumps(benchmark,ensure_ascii=False,indent=2),encoding='utf-8')

# Raw results and hash index.
source_paths=[
 (P0/'wt_3GWS.pdb','input receptor'),(H1/'WTfix.pdb','repaired receptor'),(H1/'WTfull.pdb','PDBFixer intermediate'),(H1/'WTheavy.pdb','formal receptor input'),(H1/'WTstrict.pdbqt','formal receptor'),(H1/'receptor_final.pdbqt','formal receptor'),(H1/'lig.csv','formal raw ligand CSV'),(H1/'repeat_results.json','formal repeat results'),(H1/'repeat_table.json','formal score summary'),(H1/'t3_pose_rmsd_per_seed.json','formal pose validation'),(H1/'meo_4seed.json','supplementary'),(H1/'wt_full54_t3box.json','supplementary unapproved'),(H1/'platform_run_final.json','formal platform status'),(H1/'repair_audit.json','formal audit'),(H1/'completion_audit.json','formal audit'),(H1/'final_receptor_audit.json','formal audit'),(H1/'protocol_before_results.json','formal protocol'),(H1/'run_valid_created.json','creation snapshot'),(H1/'run_created.json','H1WT creation/failure record'),(H1/'run_full_created.json','H1Full creation/failure record'),(ROOT/'derived'/'pubchem_properties_by_cid_complete.jsonl','generated API-derived identity'),(ROOT/'derived'/'pubchem_synonyms.jsonl','generated API-derived synonyms'),(ROOT/'derived'/'pubmed_54_search.jsonl','generated search log'),(ROOT/'evidence'/'pubmed_focus_abstracts.json','saved abstracts'),(ROOT/'library_identity.csv','generated identity table'),(ROOT/'evidence_matrix.csv','generated evidence matrix'),(ROOT/'candidate_computation.csv','generated computation summary'),(ROOT/'compound_feasibility.csv','generated feasibility'),(ROOT/'excluded_candidates.csv','generated exclusion/defer table')]
index={'generated_at':datetime.now(timezone.utc).isoformat(),'delivery_root':str(ROOT),'source_files':[info(p,scope) for p,scope in source_paths if Path(p).exists()],'dockscope_job_manifest':info(ROOT/'raw'/'dockscope_job_manifest.json','formal provenance'),'external_sources':[{'type':'PubMed','query_log':str(ROOT/'derived'/'pubmed_54_search.jsonl')},{'type':'PubChem PUG REST','records':str(ROOT/'derived'/'pubchem_properties_by_cid_complete.jsonl')},{'type':'CJNM 2024','doi':'10.1016/S1875-5364(24)60706-5','local_source':str(WS/'aidd-repo-work'/'00-当前研究'/'wp_exec_20260909'/'02_wp2_asset_audit'/'cjnm2024_60706-5_fulltext.pdf')},{'type':'FDA background','url':'https://content.govdelivery.com/accounts/USFDA/bulletins/3ee537d'}],'hash_policy':'SHA-256 of bytes as inspected; original files remain in their source directories; copied raw audit files are retained under raw/audits'}
(ROOT/'原始结果索引与哈希.json').write_text(json.dumps(index,ensure_ascii=False,indent=2),encoding='utf-8')

# Execution state.
state={'generated_at':datetime.now(timezone.utc).isoformat(),'task_file':str(WS/'抗MASH完整研究执行任务_GLM.md'),'delivery_root':str(ROOT),'overall':'completed_with_blockers','candidate_release':False,'wetlab_executed':False,'statuses':[
 {'id':'inventory_and_scope','status':'completed','time':'2026-09-10','input_version':'task file v2026-09-10 + current repo rules','next_step':'none'},
 {'id':'identity_54_pubchem_layer','status':'completed','time':'2026-09-10','input_version':str(WS/'aidd-repo-work'/'00-当前研究'/'data_review'/'np_identity_review.csv'),'next_step':'manual source/stereo/plant-part review remains pending'},
 {'id':'identity_manual_source_review','status':'blocked','time':'2026-09-10','input_version':'np_identity_review.csv','next_step':'reviewer must confirm plant part, isolation provenance, stereochemistry, lot/purity'},
 {'id':'pubmed_full_coverage_search','status':'completed','time':'2026-09-10','input_version':'PubMed E-utilities exact disease/mechanism queries','next_step':'full-text screening if experimental team prioritizes a compound'},
 {'id':'focus_literature_review','status':'completed','time':'2026-09-10','input_version':'PMID list + local CJNM full text','next_step':'manual full-text review for non-CJNM abstracts if needed'},
 {'id':'H1Valid_receptor_and_protocol_audit','status':'completed','time':'2026-09-10','input_version':'3GWS-derived WTheavy / H1Valid','next_step':'PROPKA/pH ensemble and domain-context review if formal gate is reopened'},
 {'id':'H1Valid_pose_and_repeatability','status':'completed','time':'2026-09-10','input_version':'H1Valid 8 ligands x 4 nominal seeds','next_step':'none for current descriptive package'},
 {'id':'WT_discrimination_benchmark','status':'failed','time':'2026-09-10','input_version':'old P0 2J4A N331S gate + no locked WT set','next_step':'freeze assay-level TRα/TRβ benchmark before any ranking; do not tune on revealed set'},
 {'id':'H1WT_H1Full_diagnostic_batches','status':'failed','time':'2026-09-10','input_version':'run_created.json/run_full_created.json','next_step':'do not resubmit; retain queued creation records as failures'},
 {'id':'WT_full54_summary','status':'blocked','time':'2026-09-10','input_version':'wt_full54_t3box.json','next_step':'retain as unapproved supplementary summary; no candidate migration'},
 {'id':'candidate_comparison','status':'completed','time':'2026-09-10','input_version':'54 evidence matrix + formal technical results','next_step':'run minimal wet validation if/when approved'},
 {'id':'wetlab_validation','status':'not_run','time':'2026-09-10','input_version':'no materials/approval','next_step':'experiment owner confirms identity, purity, model, controls, budget and primary endpoint'},
 {'id':'animal_or_human_study','status':'not_run','time':'2026-09-10','input_version':'out of scope','next_step':'only after first three experimental gates'},
 {'id':'initial_pubchem_smiles_endpoint','status':'failed','time':'2026-09-10','input_version':'PUG REST smiles path','next_step':'replaced by valid CID property queries; failed JSONL retained'}],
 'open_items':['manual 54-compound source/stereo review','locked WT/TRα/TRβ discrimination benchmark','isorhamnetin aggregation/interference','compound-specific solubility/purity/PK','wet-lab approval and materials'],
 'decision':'isorhamnetin first; formononetin independent backup; moracin N exploratory; if decisive experiments fail or are uninterpretable, return no qualified candidate rather than force a ranking'}
(ROOT/'执行状态.json').write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf-8')

# README
(ROOT/'README.md').write_text('''# 抗MASH候选裁决研究包（2026-09-10）\n\n## 结论\n- [结论一页纸](结论一页纸.md)：首选 **isorhamnetin**；备选 **formononetin**；探索性 **moracin N**。\n- 这是“最值得验证的研究候选”，不是已验证药物。无湿实验结果，不宣称药效、机制确证或临床安全性。\n\n## 核心交付\n- [全库证据矩阵](全库证据矩阵.csv)：54条全部覆盖；未知与阴性分开。\n- [候选比较与淘汰理由](候选比较与淘汰理由.md)\n- [方法验收报告](方法验收报告.md)\n- [最小实验验证方案](最小实验验证方案.md)\n- [研究增量与已有文献对照](研究增量与已有文献对照.md)\n- [检索记录](检索记录.md)\n- [执行状态](执行状态.json)\n- [原始结果索引与哈希](原始结果索引与哈希.json)\n\n## 结构化结果\n- `library_identity.csv` / `ligand_audit.csv`：PubChem CID、IUPAC、SMILES、InChI、InChIKey、理化字段；54条人工来源/部位/立体来源仍 pending。\n- `evidence_matrix.csv` / `candidate_computation.csv` / `compound_feasibility.csv` / `excluded_candidates.csv`：全库证据、描述性计算、可开发性和暂缓记录。\n- `receptor_audit.json` / `benchmark_manifest.csv` / `pose_validation.csv` / `benchmark_results.json`：受体、批次、姿态和计算审计。\n\n## 原始数据与失败记录\n- `raw/audits/` 保存关键H1 JSON审计/协议/重复结果副本；原始文件的绝对路径和SHA-256在 `原始结果索引与哈希.json`。\n- `raw/dockscope_job_manifest.json` 索引正式H1Valid DockScope作业243个文件。\n- `derived/pubchem_properties_by_cid_complete.jsonl`、`derived/pubchem_synonyms.jsonl`、`derived/pubmed_54_search.jsonl` 保留身份与检索记录；首轮无效PubChem SMILES端点的失败记录也保留在 `derived/pubchem_properties.jsonl`。\n- H1WT/H1Full、旧2J4A N331S门控失败、自动口袋与WT-full54未审批摘要均保留并明确降级，未删除或回填。\n\n## 计算边界\nH1Valid正式批次只支持3GWS派生WT受体上的受体输入审计、T3最高评分姿态恢复和技术重复性；未完成锁定WT区分能力验证。Vina分数不转换为Kd，不证明TRβ激动/选择性或MASH疗效。\n''',encoding='utf-8')
print('artifacts complete')
