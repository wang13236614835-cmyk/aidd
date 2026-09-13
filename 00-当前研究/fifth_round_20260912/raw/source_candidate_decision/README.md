# 抗MASH候选裁决研究包（2026-09-10）

## 结论
- [结论一页纸 v2](结论一页纸.md)：当前不发布单一已验证候选；首轮疾病验证面板为 **scoparone、alisol B、hyperoside、puerarin、isorhamnetin、formononetin**。
- 第二轮为 **isoquercitrin、1-deoxynojirimycin、ursolic acid、moracin N**；这是实验优先级，不是药效排名。
- 这是“最值得验证的研究候选”，不是已验证药物。无湿实验结果，不宣称药效、机制确证或临床安全性。

## 核心交付
- [全库证据矩阵](全库证据矩阵.csv)：54条全部覆盖；未知与阴性分开。
- [候选比较与淘汰理由](候选比较与淘汰理由.md)
- [方法验收报告](方法验收报告.md)
- [最小实验验证方案](最小实验验证方案.md)
- [研究增量与已有文献对照](研究增量与已有文献对照.md)
- [检索记录](检索记录.md)
- [执行状态](执行状态.json)
- [原始结果索引与哈希](原始结果索引与哈希.json)
- [交付目录文件哈希](delivery_hashes.json)

## 结构化结果
- `library_identity.csv` / `ligand_audit.csv`：PubChem CID、IUPAC、SMILES、InChI、InChIKey、理化字段；54条人工来源/部位/立体来源仍 pending。
- `evidence_matrix.csv` / `candidate_computation.csv` / `compound_feasibility.csv` / `excluded_candidates.csv`：全库证据、描述性计算、可开发性和暂缓记录。
- `receptor_audit.json` / `benchmark_manifest.csv` / `pose_validation.csv` / `benchmark_results.json`：受体、批次、姿态和计算审计。

## 原始数据与失败记录
- `raw/audits/` 保存关键H1 JSON审计/协议/重复结果副本；原始文件的绝对路径和SHA-256在 `原始结果索引与哈希.json`。
- `raw/dockscope_job_manifest.json` 索引正式H1Valid DockScope作业243个文件。
- `derived/pubchem_properties_by_cid_complete.jsonl`、`derived/pubchem_synonyms.jsonl`、`derived/pubmed_54_search.jsonl` 保留身份与检索记录；首轮无效PubChem SMILES端点的失败记录也保留在 `derived/pubchem_properties.jsonl`。
- H1WT/H1Full、旧2J4A N331S门控失败、自动口袋与WT-full54未审批摘要均保留并明确降级，未删除或回填。

## 计算边界
H1Valid正式批次只支持3GWS派生WT受体上的受体输入审计、T3最高评分姿态恢复和技术重复性；未完成锁定WT区分能力验证。Vina分数不转换为Kd，不证明TRβ激动/选择性或MASH疗效。

## Week 1 增量交付
- [Week 1状态/风险地图](week1_status_risk_map.md)
- [重点分子身份审计](priority_compounds_identity_audit.csv)
- [采购与人工核验建议](procurement_recommendation.md)
- [isorhamnetin干扰风险](isorhamnetin_interference_literature_review.md)
- [无细胞前置protocol](interference_pretest_protocol.md)
- [竞争者Top10初筛](extended_screening_top10.csv)
- [竞争者证据摘要](top10_evidence_summary.md)
- [ChEMBL数据摘要](data_collection_summary.md)
- [最终模型就绪性报告](model_readiness_report.md)

Week 1已新增scoparone、alisol B、hyperoside、ursolic acid、puerarin、isoquercitrin、1-deoxynojirimycin为A/A-级竞争复核对象；它们尚未完成全文、身份、可开发性和实验放行。供应商公开页面核查受验证码/403/登录限制阻断，未采购、未虚构规格。

## Week 1后续执行
- [竞争者初筛](extended_screening_top10.csv) / [竞争者摘要](top10_evidence_summary.md)：A类竞争者进入全文、身份和可测性复核，不直接放行。
- [候选状态矩阵](research_status_matrix.csv) / [失败模式树](failure_mode_tree.md)
- [实验室交接包](wetlab_handover_package.md) / [干扰前置protocol](interference_pretest_protocol.md)
- [ChEMBL模型冻结协议](chembl_model_freeze_protocol.md) / [模型就绪性报告](model_readiness_report.md)
- [ChEMBL数据摘要](data_collection_summary.md)：原始目标activity表和严格候选集已保存。

## 后续裁决 v2
- [候选裁决 v2](candidate_decision_v2.md)：疾病证据面板扩大为6个首轮对象。
- [A类竞争者证据升级](tierA_evidence_upgrade_v2.csv) / [证据矩阵 v2](evidence_matrix_v2.csv)
- [开放全文审计](derived/europepmc_fulltext_audit_v2.json)
- [候选实验面板](wetlab_candidate_panel_v2.csv) / [下一轮实验顺序](next_experiment_order_v2.md)
- [FXR模型卡](model_card_fxr_v1.md) / [适用域拒判报告](model_domain_assessment.md)
- [TRβ/TRα配对基准](derived/trb_tra_paired_benchmark.csv)

模型敏感性分析显示天然产物54/54均低于FXR训练域拒判阈值，因此模型不参与当前候选排序；所有疾病候选需先通过身份/可测性和PA/OA表型门控。
