# 54库临时长名单与候选压缩（2026-09-10）

## 全库覆盖
- 54/54 条均完成定向 PubMed 疾病词和机制词检索；原始查询、日期、命中数和前20 PMID 保存在 `derived/pubmed_54_search.jsonl`。
- 命中数不等于阳性；未逐篇全文筛选者在 `evidence_matrix.csv` 中写为未知。
- 54条身份结构层自动通过 PubChem CID/SMILES/InChIKey 查询，但药材真实性、植物部位、分离文献、批次和人工签核仍 pending_review。

## 压缩后
1. **isorhamnetin：疾病证据优先主候选**——NASH脂变+纤维化（31700054）和新的MASLD/FXR-胆汁酸方向线索（41763136）；主要风险是多酚聚集/检测干扰和直接结合层级不足。
2. **formononetin：独立理由支持的备选/疾病锚**——MCD-NASH改善（38185065）+FXR SPR/报告基因全文证据（CJNM 2024）；主要风险是MCD模型外推及FXR与疾病表型桥接。
3. **moracin N：探索性候选**——本体MASH证据缺失，但肝病外的细胞/脑铁死亡证据给出可检验的肝细胞脂质过氧化/铁依赖假说；计算分数不用于升格。

## 暂缓
- 3'-methoxydaidzein：有明确3'位异黄酮SAR问题但本体疾病/FXR证据空白；因探索位已给moracin N，暂作SAR负/正对照。
- biochanin A：FXR体系阳性对照，不占候选位。
- daidzein：非代谢性纤维化和TR敏化对照，不能当MASH首选。
- 其余分子：保留全库记录，未证明无效；证据和/或可操作性未达到最终短名单门槛。
