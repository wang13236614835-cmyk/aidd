# 检索记录（2026-09-10）

## 数据库与日期
- PubMed E-utilities `esearch.fcgi`/`efetch.fcgi`，执行日 2026-09-10（UTC记录在 `derived/pubmed_54_search.jsonl`）。
- PubChem PUG REST，按54条既有CID查询 properties 与 synonyms；完整输出记录在 `derived/pubchem_properties_by_cid_complete.jsonl`、`derived/pubchem_synonyms.jsonl`。
- 本轮没有把检索命中自动标为阳性；没有为找阳性而更改判据。

## 全库检索式
每个分子分别执行：
- 疾病：`"NAME"[Title/Abstract] AND (MASH OR NASH OR NAFLD OR MASLD OR steatohepatitis OR "fatty liver")`
- 机制：`"NAME"[Title/Abstract] AND (FXR OR NR1H4 OR "thyroid hormone receptor" OR TRbeta OR TRβ OR TRalpha OR ferroptosis OR "lipid peroxidation" OR "hepatic stellate")`

## 重点摘要核查
已保存 PMID 38185065、31700054、41763136、40407304、34281775、40972263、27145114、38556609、33498088、41344662、9322358、42173416、19182375、29688519 的摘要和链接于 `evidence/pubmed_focus_abstracts.json`。

## 证据层级限制
- CJNM 2024 DOI 10.1016/S1875-5364(24)60706-5：本地正文全文核查（formononetin/biochanin A FXR结合与功能）。
- 其余重点文献主要为PubMed摘要级；摘要不能替代全文方法、剂量、随机化、样本量和偏倚评估。
- 41763136 可核实为 isorhamnetin 的 MASLD/菌群/胆汁酸/FXR方向论文；本轮不把其 MD/体外 interaction 自动等同纯化受体KD。
- moracin N 文献是神经细胞/脑缺血铁死亡；给药途径和细胞类型不支持直接外推肝保护。
