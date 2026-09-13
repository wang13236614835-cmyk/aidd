import csv,json
from pathlib import Path
root=Path(r'D:\zcode-workspace\aidd-repo-work\00-当前研究\candidate_decision_20260910')
# Structured abstract-level upgrade, explicitly not full-text.
up={
'scoparone':('MCD-NASH小鼠4周治疗；AML12 PA脂毒性和RAW264.7 LPS模型；摘要报告NASH关键特征、自噬、炎症/凋亡/纤维化改善','ROS/P38/Nrf2、PI3K/AKT/mTOR、自噬；另一研究TLR4/NF-kB；HFD-MASLD有miR-3073a-3p/CAMKK2线索','摘要级本体证据；MCD与HFD模型均有，但剂量/组织学/偏倚需全文核查','A-tier竞争者：优先全文和身份/可测性复核'),
'alisol B':('HFD-MASLD小鼠和肝细胞；DIO+CCl4、CDA饮食NASH小鼠；摘要报告脂变、炎症和纤维化改善','Ces2a-AMPK/自噬/脂肪酸氧化；RARα-HNF4α-PPARγ-CD36；需区分母体与AB23A衍生物','摘要级本体证据；NASH病理较强，但来源/剂量/样本量待全文','A-tier竞争者：优先全文核查'),
'hyperoside':('高脂高糖NAFLD大鼠、HFD NASH纤维化小鼠、LX2焦亡模型；摘要报告脂变/纤维化和肝酶改善','Flot2/TLR4/NLRP3焦亡；菌群/胆汁酸/脂质代谢；摘要称CETSA/ITC等需全文核验','摘要级本体证据，纤维化覆盖较好；直接结合条件未核实','A-tier竞争者：优先全文、聚集/可测性核查'),
'ursolic acid':('HFD MASLD/NASH小鼠及脂毒性细胞；摘要报告脂变、炎症/缺氧和肝病理改善','SPP1-ITGB1/CD44-ERK-Th17；decorin-IGF-IR/HIF-1；部分SPR/pull-down/Co-IP线索需全文核查','摘要级本体证据；三萜溶解度/递送是主要风险','A-tier竞争者：优先全文和可开发性复核'),
'puerarin':('NASH小鼠、MAFLD小鼠、HFD-MASLD小鼠、AML12/巨噬细胞/斑马鱼；摘要报告肝病理、胶原/炎症或脂质改善','PAI-1-自噬-巨噬M2；SIRT1/Nrf2、铁死亡；肠道菌群/短链脂肪酸/屏障','摘要级本体证据较丰富；糖苷暴露和实验形式待核查','A-tier竞争者：优先全文和可测性复核'),
'isoquercitrin':('HFD-NASH小鼠、MCD脂肪性肝炎小鼠、IR-HepG2；摘要报告脂质/肝功能/炎症改善','galectin-3介导胰岛素抵抗/脂代谢；NLRP3-HSP90；AMPK/ACC线索','摘要级本体证据；需区分本体、α-glycosyl衍生物和提取物','A-tier竞争者：优先全文核查'),
'1-deoxynojirimycin':('CDAHFD-MASH小鼠和HFD-NASH小鼠；摘要报告肝损伤、脂变、炎症和纤维化改善','PI3K/AKT/mTOR-自噬；肠道菌群重塑；直接靶点仍未确认','摘要级本体证据；公开摘要对组织学和剂量需全文核查','A-tier竞争者：优先全文核查'),
}
with (root/'library_identity.csv').open(encoding='utf-8-sig',newline='') as f: ids={r['preferred_name']:r for r in csv.DictReader(f)}
out=root/'tierA_evidence_upgrade_v2.csv'
with out.open('w',newline='',encoding='utf-8-sig') as f:
 w=csv.writer(f); w.writerow(['record_id','candidate','disease_model_upgrade','mechanism_upgrade','evidence_level','decision_update','key_abstract_limit'])
 for n,(d,m,lim,dec) in up.items(): w.writerow([ids[n]['record_id'],n,d,m,'摘要级（未完成全文）',dec,lim])
# merge into v2 matrix without changing original matrix
with (root/'evidence_matrix.csv').open(encoding='utf-8-sig',newline='') as f: old=list(csv.DictReader(f))
upmap={r[1]:r for r in csv.reader((out).open(encoding='utf-8-sig'))}; next(iter(upmap),None)
# better read upgrade
with out.open(encoding='utf-8-sig',newline='') as f: ups={r['candidate']:r for r in csv.DictReader(f)}
for r in old:
 n=r['分子']
 if n in ups:
  u=ups[n]; r['疾病模型证据']=u['disease_model_upgrade']; r['疾病证据层级']='摘要级（A-tier升级，全文待核）'; r['直接靶点与功能证据']=u['mechanism_upgrade']; r['靶点证据层级']='摘要级/条件有限'; r['保留或降级理由']=u['decision_update']; r['证据状态']='摘要级升级，非全文确认'; r['主要缺口']=u['key_abstract_limit']+'；来源/部位/纯度/PK未人工闭环'
with (root/'evidence_matrix_v2.csv').open('w',newline='',encoding='utf-8-sig') as f:
 w=csv.DictWriter(f,fieldnames=old[0]); w.writeheader(); w.writerows(old)
(root/'tierA_evidence_upgrade_v2.md').write_text('''# A级竞争者证据升级（摘要级，2026-09-10）

本轮对scoparone、alisol B、hyperoside、ursolic acid、puerarin、isoquercitrin和1-deoxynojirimycin的PubMed相关结果进行了摘要级核查。结果支持它们进入下一轮全文、身份、可测性和暴露复核，但不构成实验放行，也不把药材/复方/衍生物证据转移给本体。

详细结构化结果见 `tierA_evidence_upgrade_v2.csv`，合并矩阵见 `evidence_matrix_v2.csv`。摘要不能替代全文中的随机化、剂量、组织学评分、样本量、偏倚和统计核查。
''',encoding='utf-8')
print('wrote',out,root/'evidence_matrix_v2.csv')
