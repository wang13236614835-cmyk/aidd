import csv,json,hashlib,re
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(r'D:\zcode-workspace\aidd-repo-work\00-当前研究\candidate_decision_20260910')
WS=Path(r'D:\zcode-workspace')
RAW=WS/'ds_in'/'np54_ligands.csv'
IDR=WS/'aidd-repo-work'/'00-当前研究'/'data_review'/'np_identity_review.csv'

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def jl(p): return [json.loads(x) for x in Path(p).read_text(encoding='utf-8').splitlines() if x.strip()]
raw=list(csv.DictReader(RAW.open(encoding='utf-8-sig')))
ids=list(csv.DictReader(IDR.open(encoding='utf-8-sig')))
pub={x['row']:x for x in jl(ROOT/'derived'/'pubchem_properties_by_cid_complete.jsonl')}
syn={x['row']:x for x in jl(ROOT/'derived'/'pubchem_synonyms.jsonl')}
pm={x['record_id']:x for x in jl(ROOT/'derived'/'pubmed_54_search.jsonl')}
identity=[]
for i,(r,ir) in enumerate(zip(raw,ids),1):
    pr=pub[i]['result']; rec=(pr.get('records') or [{}])[0] if pr.get('ok') else {}
    sr=syn[i]['result']; srec=(sr.get('records') or [{}])[0] if sr.get('ok') else {}
    syns=srec.get('Synonym',[]) if isinstance(srec,dict) else []
    m=re.match(r'^(.*?)\((.*?)\)$',ir.get('herb','')); latin=m.group(1) if m else ir.get('herb',''); cn=m.group(2) if m else ''
    identity.append({'record_id':f'NP54-{i:03d}','library_version':'np54_current','brd_id_raw':r['brd_id'],'preferred_name':ir['name'],'name_source':'np_library_filtered.csv / np_identity_review.csv','synonyms':json.dumps(syns[:15],ensure_ascii=False),'source_herb_cn':cn,'source_species_latin':latin,'source_plant_part':'未知','source_provenance_note':'库表仅给药材/物种标签；植物部位、批次、提取/分离原始文献未提供；人工来源审核仍pending_review','pubchem_cid':ir['cid'],'pubchem_iupac':rec.get('IUPACName',''),'formula':rec.get('MolecularFormula',''),'mw_pubchem':rec.get('MolecularWeight',''),'xlogp_pubchem':rec.get('XLogP',''),'tpsa_pubchem':rec.get('TPSA',''),'hbd_pubchem':rec.get('HBondDonorCount',''),'hba_pubchem':rec.get('HBondAcceptorCount',''),'rotb_pubchem':rec.get('RotatableBondCount',''),'canonical_smiles_nonisomeric':rec.get('ConnectivitySMILES',''),'isomeric_smiles_pubchem':rec.get('SMILES',''),'inchi':rec.get('InChI',''),'inchikey':rec.get('InChIKey',''),'stereo_status':'有手性标记' if '@' in r['smiles'] else '未见手性标记','tautomer_salt_form':'母体结构/未建盐型；互变异构未系统枚举','formal_charge':'0（输入SMILES未见电荷）','source_library_path':str(RAW),'source_row':i+1,'source_smiles_raw':r['smiles'],'source_record_sha256':r['source_sha256'],'source_file_hash':sha(RAW),'structure_match_pubchem_smiles':'exact_string' if rec.get('SMILES','')==r['smiles'] else 'not_exact_string_but_recorded','identity_check_method':'PubChem CID property + synonym REST query; local input retained','identity_check_date':'2026-09-10','automatic_identity_status':'PASS at PubChem/CID/structure layer','manual_tier':'B pending','review_status':'pending_manual_source_review','reviewer':'','review_date':'','identity_risk':'高（来源/部位/分离物真实性未人工签核）','notes':("3'-methoxydaidzein: B环3'-OMe/4'-OH、A环7-OH；不可并入calycosin/formononetin/biochanin A" if ir['name']=="3'-methoxydaidzein" else '')})
with (ROOT/'library_identity.csv').open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.DictWriter(f,fieldnames=identity[0]); w.writeheader(); w.writerows(identity)
known={
'formononetin':('MCD-NASH小鼠治疗性干预：ALT/AST、TG、肝脂变和FAO改善；SIRT1/PGC-1α/PPARα干预/抑制实验（PMID 38185065，摘要；MCD为非典型代谢模型）','FXR直接结合/功能：SPR KD 1.323 μM、Ostβ报告基因EC50 0.1972 μM、SHP/Ostβ mRNA；CJNM 2024 DOI 10.1016/S1875-5364(24)60706-5正文全文；不是本项目新发现','本库无实测PK/肝暴露；文献给药/制剂与本项目试剂纯度未闭环','保留：疾病锚/机制桥接候选'),
'isorhamnetin':('NASH小鼠口服50 mg/kg：脂质/TG、肝损伤、胶原沉积和纤维化标志改善（PMID 31700054，摘要）；HFD-MASLD小鼠剂量依赖改善，FXR/胆汁酸/菌群轴与体外/MD支持（PMID 41763136，摘要）','FXR方向：41763136报告MD与体外实验支持interaction/signaling，但本轮未确认纯化受体KD；直接结合层级未知；多酚检测干扰/聚集待排除','NASH研究有口服50 mg/kg动物剂量；未建立本库化学形式的PK、肝暴露、溶解度和检测干扰','保留：疾病证据优先候选；机制需正交验证'),
'biochanin A':('DIO/HFD小鼠肝脂变、胰岛素抵抗和代谢通路改善（PMID 27145114；脂变级非MASH/NASH级）','FXR SPR KD 0.347 μM、报告基因EC50 0.4441 μM及双功能/抗炎实验；CJNM 2024全文；应作为体系阳性对照，不占候选位','动物膳食给药文献；本库无纯度/肝暴露/可购形式核验','保留：FXR体系阳性对照'),
'daidzein':('CCl4/BDL纤维化小鼠及TGFβ1-LX2 HSC模型，抑制integrin αVβ1/YAP（PMID 40407304，摘要）；非代谢性损伤，不等于MASH','Takeuchi 2009报告TRα/TRβ激动/拮抗均未见；Ariyani 2018报告genistein/daidzein增强T3-TR转录并直接作用TR-LBD（PMID 19182375/29688519，摘要级）；FXR单条件阴性记录来自旧矩阵，条件需全文复核','本库无实测PK/肝暴露；异黄酮代谢/结合蛋白等缺口','降级：非代谢纤维化/机制对照，不列最终候选'),
'moracin N':('本轮未找到moracin N与MASH/NASH/NAFLD/MASLD的直接疾病模型；家族/相近物不迁移','HT22 erastin模型中抗铁死亡，GPX4/ROS/铁/脂质过氧化和Keap1/Nrf2线索（PMID 34281775）；小鼠脑缺血为脑室内给药、神经铁死亡（PMID 40972263）；不外推肝保护/口服暴露；无直接TRβ/FXR实验证据','脑室内20 mg/kg/day不等于口服生物利用度；本体PK/肝暴露未知','探索性保留：只检验肝细胞铁死亡假说，不由对接升格'),
"3'-methoxydaidzein":("本轮PubMed精确疾病检索未找到MASH/NASH/NAFLD/MASLD直接模型；PMID 41344662为复方/药材成分与毒性暴露背景，PMID 9322358为QR分离研究，均非抗MASH疗效","FXR/TR直接实验未找到；邻近异黄酮formononetin/biochanin A的FXR证据不能转移；为3'位甲氧基SAR探针","无本体PK/肝暴露/溶解度实测；可开发性未知",'降级：SAR负/正结果均有信息，但无疾病锚')}
scores={'biochanin A':(-9.255,-9.261,-9.211),'daidzein':(-9.601,-9.606,-9.595),'formononetin':(-9.072,-9.078,-9.046),'isorhamnetin':(-8.244,-8.246,-8.234),'moracin N':(-10.875,-10.881,-10.853),'liothyronine':(-9.498,-9.503,-9.497),'sobetirome':(-10.232,-10.246,-10.226),'resmetirom':(-10.215,-10.231,-10.196),"3'-methoxydaidzein":(-9.741,-9.763,-9.727)}
rows=[]
for i,r in enumerate(raw,1):
    name=r['label']; qd=pm[i]['queries']['disease']['result']; qm=pm[i]['queries']['mechanism']['result']; k=known.get(name)
    if k: disease,mech,expo,status=k; level='全文' if name in ('formononetin','biochanin A') else '摘要/条件有限'
    else: disease=f'本轮精确PubMed检索命中{qd.get("count","")}条；仅为检索命中，未逐篇完成终点/模型核查，记为未知。'; mech=f'机制词检索命中{qm.get("count","")}条；未逐篇完成直接靶点/功能分层，记为未知。'; expo='未知：本轮未找到可直接回填的本体PK/肝暴露/溶解度/纯度记录'; status='暂不列短名单：证据矩阵未知，未满足保留门槛'; level='未知/未逐篇核查'
    sc=scores.get(name); calc=f'TRβ WT 3GWS派生受体，4种子中位={sc[0]:.3f}，范围=[{sc[1]:.3f},{sc[2]:.3f}]；仅描述性重复性，不是活性预测' if sc else '本轮未纳入正式4种子H1Valid；历史/全库摘要不得当作验证通过'
    rows.append({'record_id':f'NP54-{i:03d}','分子':name,'来源药材':r['brd_id'],'PubMed疾病检索命中数':qd.get('count',''),'PubMed机制检索命中数':qm.get('count',''),'疾病模型证据':disease,'疾病证据层级':level,'直接靶点与功能证据':mech,'靶点证据层级':level,'暴露与可开发性':expo,'计算支持':calc,'研究增量':'见候选比较文档；未知不等于阴性' if k else '先完成身份/全文筛选，再决定是否进入候选压缩','保留或降级理由':status,'证据状态':'已核查分层' if k else '未知（检索命中未等于阳性）','主要缺口':'来源/部位/纯度/PK未人工闭环；'+('聚集/检测干扰需排查' if name=='isorhamnetin' else '疾病模型/机制/暴露仍需按方案核验')})
with (ROOT/'evidence_matrix.csv').open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.DictWriter(f,fieldnames=rows[0]); w.writeheader(); w.writerows(rows)
comp=[]
for n,(med,mi,ma) in scores.items(): comp.append({'candidate':n,'target':'TRβ/THRB WT 3GWS-derived','median_kcal_mol':med,'min_kcal_mol':mi,'max_kcal_mol':ma,'range_kcal_mol':round(ma-mi,3),'seeds':'7,42,123,20260910','completed':'yes','source':'H1Valid formal 4 nominal seeds' if n!='3\'-methoxydaidzein' else 'supplementary meo_4seed','interpretation':'Descriptive pocket-occupancy/reproducibility only; no activity/Kd/efficacy conversion'})
with (ROOT/'candidate_computation.csv').open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.DictWriter(f,fieldnames=comp[0]); w.writeheader(); w.writerows(comp)
feas=[]
for i,r in enumerate(raw,1):
 n=r['label']; ident=identity[i-1]
 if n=='isorhamnetin': risk='多酚聚集/荧光素酶或氧化还原检测干扰；溶解度和真实肝暴露未知'; level='中高'; dec='先做聚集/干扰、溶解度和PA/OA表型/FXR依赖性'
 elif n=='formononetin': risk='MCD模型外推和FXR-疾病表型桥接未统一；PK/纯度未知'; level='中'; dec='先做FXR依赖性脂毒性表型+FXR正交结合/功能'
 elif n=='moracin N': risk='无肝病证据；神经/脑室内给药不能外推；多酚/抗氧化检测假阳性'; level='高'; dec='只在低成本肝细胞铁死亡区分实验后升级'
 elif n=="3'-methoxydaidzein": risk="疾病/靶点本体数据空白；3'位命名/文件主键风险；来源/暴露未知"; level='高'; dec='作为SAR探索，先做身份/溶解度和FXR报告基因+直接结合'
 elif n=='biochanin A': risk='疾病证据主要脂变级且已有FXR文献；不应冒充新候选'; level='低到中'; dec='体系阳性对照'
 else: risk='未知：需实测溶解度、细胞耐受、检测干扰和准确可购形式'; level='未知'; dec='不进入最终短名单，除非新证据改变'
 feas.append({'record_id':ident['record_id'],'candidate':n,'manual_identity_status':ident['review_status'],'availability':'未核查具体供应商/批次/纯度（不采购）','solubility_aggregation_risk':risk,'risk_level':level,'decision_use':dec,'note':'理化/PAINS仅作预警，不作药效或安全结论'})
with (ROOT/'compound_feasibility.csv').open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.DictWriter(f,fieldnames=feas[0]); w.writeheader(); w.writerows(feas)
ex=[]
for i,r in enumerate(raw,1):
 n=r['label']
 if n in {'isorhamnetin','formononetin','moracin N','biochanin A','liothyronine','sobetirome','resmetirom'}: continue
 reason='未形成可核查的MASH/NASH直接证据与可操作机制假说；本轮仅记录检索命中，不将未知当阴性'
 if n=='daidzein': reason='有非代谢性CCl4/BDL纤维化证据和TR敏化文献，但与总问题的MASH疾病锚不够直接'
 elif n in {'genistin','daidzin','ononin','puerarin'}: reason='糖苷/异黄酮有方向线索，但疾病、直接靶点和暴露条件尚未按本轮标准闭环'
 ex.append({'record_id':f'NP54-{i:03d}','candidate':n,'reason':reason,'disease_query_hits':pm[i]['queries']['disease']['result'].get('count',0),'mechanism_query_hits':pm[i]['queries']['mechanism']['result'].get('count',0),'status':'excluded_or_deferred_not_proven_inactive'})
with (ROOT/'excluded_candidates.csv').open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.DictWriter(f,fieldnames=ex[0]); w.writeheader(); w.writerows(ex)
print('built tables',len(identity),len(rows),len(comp),len(feas),len(ex))
