import csv, json
from pathlib import Path
ROOT=Path(r'D:\zcode-workspace\aidd-repo-work\00-当前研究\candidate_decision_20260910')
rows=[
('scoparone',16,10,'32000066;31421545;41933743;39368602','本体NASH/NAFLD/MASLD摘要级证据；MCD-NASH有炎症/凋亡/纤维化线索；ROS/p38/Nrf2、PI3K-AKT-mTOR、自噬、TLR4/NF-kB、PPARα','A','进入Top10全文复核'),
('alisol B',18,10,'40327987;40582207;35745142;27773935','本体MASLD/NASH证据；Ces2a、RARα-HNF4α-PPARγ-CD36机制；AB23A衍生物证据必须与母体分开','A','进入Top10全文复核'),
('hyperoside',16,10,'41411733;41601885;33611063;35024184;40349961','本体NAFLD/NASH与纤维化；Flot2/TLR4/NLRP3、FXR/LXR/胆汁酸、菌群；摘要称ITC/CETSA需全文核查','A','进入Top10全文复核'),
('ursolic acid',52,10,'38623614;34560554;25418615','本体MASLD/NASH/NAFLD；SPP1-ITGB1/CD44-ERK-Th17、decorin-IGF-IR/HIF-1、PPARα/自噬','A','进入Top10全文复核'),
('puerarin',50,10,'38515289;38001459;40121054;40750240','本体NASH/MASLD；PAI-1-自噬-巨噬细胞M2、SIRT1/Nrf2、铁死亡、菌群/屏障','A','进入Top10全文复核'),
('isoquercitrin',19,10,'38056146;37240141;36771140','本体HFD-NASH/MCD脂肪性肝炎；galectin-3、NLRP3-HSP90、AMPK/ACC；需区分衍生物和提取物','A-','进入Top10全文复核'),
('1-deoxynojirimycin',19,10,'41592295;31272028;37087566','本体CDAHFD-MASH/HFD-NASH；纤维化改善摘要线索；菌群、自噬、PI3K-AKT-mTOR；直接靶点仍未知','A-','进入Top10全文复核'),
('vitexin',8,8,'35034930;35328564;31472955;32544504','本体NAFLD/MASLD；自噬、ER应激、线粒体、AMPK/PPARα；部分制剂化证据','B+','保留为第二梯队'),
('epicatechin',52,10,'32007822;40619009;41404381','本体NASH/MASLD；Paigen+果糖模型有气球样变/胶原/炎症改善；母体可开发性和递送需核查','B+','保留为第二梯队'),
('oleanolic acid',42,10,'34251802;30351048;38972213','文献多但含IRI、复方、衍生物和脂肪变邻近模型；母体NASH纤维化优势不清','B','暂缓，不进入首轮实验'),
('scopoletin',11,10,'39571916;28921708;34979142','主要脂肪变/高脂血症、酒精或体外邻近模型；本体MASH纤维化锚不足','C','暂缓'),
('catechin',110,10,'31503268;30832407;35323719','前10主要是综述、绿茶提取物、EGCG或多酚混合物；不能归因于catechin本体','C','不进入候选池'),
]
out=ROOT/'extended_screening_top10.csv'
fields=['candidate','disease_query_hits','abstracts_checked','key_pmids','evidence_summary','tier','screening_decision']
with out.open('w',newline='',encoding='utf-8-sig') as f:
 w=csv.writer(f); w.writerow(fields); w.writerows(rows)
(ROOT/'top10_evidence_summary.md').write_text('''# 高命中竞争分子摘要级初筛（2026-09-10）

## 结论
本轮前10相关摘要核查改变了候选池：scoparone、alisol B、hyperoside、ursolic acid、puerarin、isoquercitrin、1-deoxynojirimycin均达到进入下一轮全文/身份/暴露复核的条件。它们尚未替代原三候选，也未获得实验放行。

## 进入Top10复核池
- scoparone：本体NASH/NAFLD/MASLD证据最密集之一，MCD-NASH有炎症/纤维化线索。
- alisol B：本体MASLD/NASH及RARα/Ces2a机制线索；母体与AB23A衍生物必须严格分开。
- hyperoside：本体NASH纤维化和Flot2/TLR4/NLRP3线索；摘要中ITC/CETSA需全文核查。
- ursolic acid：本体MASLD/NASH和SPP1/decorin机制线索；纤维化优势仍需核实。
- puerarin：本体NASH/MASLD，PAI-1、自噬、SIRT1/Nrf2、铁死亡等方向。
- isoquercitrin：本体HFD-NASH/MCD脂肪性肝炎，两篇较直接的研究。
- 1-deoxynojirimycin：CDAHFD-MASH/HFD-NASH和纤维化摘要线索。

## 第二梯队
vitexin、epicatechin保留；epicatechin部分优势来自靶向纳米制剂，不能直接迁移给游离母体。oleanolic acid文献多但模型和身份混杂，暂缓。

## 排除或降级
catechin的高命中数主要来自综述、绿茶/EGCG/多酚混合物；scopoletin主要是脂肪变、酒精或体外邻近模型。本轮不把它们列为首轮实验对象。

## 限制
本筛选为摘要级快速初筛，不是系统综述；未逐篇完成随机化、盲法、样本量、完整组织学和暴露核查。药材、复方、衍生物、制剂结果未转移给本体。
''',encoding='utf-8')
print('wrote',out)
