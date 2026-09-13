# 最终战略 QC 报告

**日期：2026-09-12**

## 一、文件完整性

用户要求的25个精确文件名：

1. 最终战略冻结_执行总览.md
2. 最终双轴战略矩阵.csv
3. FASN_疾病与临床证据审计.md
4. FASN_数据可建模性终审.md
5. FASN_activity_master.csv
6. FASN_数据清洗规则.md
7. FASN_baseline建模方案.md
8. FASN_GNN启用门控.md
9. 天然产物库重构方案.md
10. FASN_AIDD完整工作流.md
11. MoracinN_机制重定位最终审计.md
12. MoracinN_NRF2_ferroptosis证据链.md
13. MoracinN_最小验证闭环.md
14. THRB_FXR_ACC最终定位.md
15. Docking历史失败与方法学结论.md
16. Plan_B触发条件.md
17. 打卡体系映射_v2.md
18. GitHub项目架构调整建议.md
19. 未来24个月路线图.md
20. 课题题目最终建议.md
21. 成果与论文拆分规划.md
22. 导师审批版_最终战略冻结.md
23. 停止投入事项.md
24. 未完成项与风险登记.md
25. 最终战略_QC报告.md

应为25个，全部放在本目录根层（FASN_activity_master.csv已由数据构建步骤生成）。

## 二、数据 QC

- FASN_activity_master：1,652条记录；activity_id唯一1,652；
- 分子1,139；assay 51；document 34；
- endpoint：IC50 1,630、Ki 20、Kd 2；
- unit：nM 1,637、ug.mL-1 15；
- relation全部为`=`（这是精确主表，不代表全量activity全部为精确值）；
- SMILES解析有效1,652/1,652；多片段2条已标记；
- pActivity换算最大绝对误差约1.8×10^-15；
- 全量FASN raw另有2,344条不等、缺失或删失关系，未混入主表。

## 三、模型 QC

- baseline脚本已实际运行；
- canonical assay CHEMBL5731051：96个分子、39个骨架；
- 5 seed random/scaffold split已运行；
- canonical scaffold split中位：ECFP-RF R² 0.336、ECFP-XGBoost R² 0.626、ECFP-Ridge R² 0.736；
- broad time sensitivity：ECFP-RF R² −0.061、ECFP-XGBoost R² −0.423；
- conformal UQ已运行，覆盖率随seed变化；
- 54个天然产物最大Tanimoto中位约0.136，最高约0.171；
- 无独立external validation，未放行候选总榜；
- GNN未运行，符合门控要求。

## 四、战略一致性 QC

所有终版文件采用同一架构：

- 长期主AIDD轴：FASN/de novo lipogenesis；
- 近期高创新验证轴：Moracin N–NRF2-dependent ferroptosis regulation；
- THRβ：临床参照/备选reporter；
- FXR：机制锚点/QC；
- ACC：附录；
- docking：结构解释；
- FASN模型状态：有条件资格，尚未放行天然产物；
- Moracin N状态：无湿实验结果，机制重定位待验证。

## 五、执行层错误记录

- FASN baseline首次运行因候选库路径错误在模型计算完成后退出；
- 修正路径后相同seed成功运行；
- 该错误被保留在 `logs/run_fasn_baseline_first_attempt_note.md`，不被写成科学失败。

### 收尾修正（同日）

- 早期支持文件 `FASN_master_summary.json` 曾把 assay-family 写成 assay 数（cell_extract 5 等），已改为记录数（cell_extract 1,139 等）并另列 assay 数；
- `final_data_qc.json` 曾引用早期 spa_family（103分子/40骨架双assay）口径，已改为 canonical 单 assay CHEMBL5731051（96分子/39骨架）；旧口径保留在 `FASN_baseline_summary.json` 作为探索性历史运行；
- 两处修正均不改变任何科学结论：canonical 多种子与 conformal/UQ 结果始终以单 assay 为准。

## 六、外部检索边界

- ChEMBL、BindingDB、PubMed和PubChem均有原始响应留痕；
- Sagimet、Viking和Organovo部分公司页面存在访问超时、重定向或宣传性页面；
- 访问失败标为未完成，不推断临床终止或成功；
- denifanstat FASCINATE-2使用PubMed原始摘要和SEC披露；
- 本QC不声称完成所有临床注册信息闭合。

## 七、最终QC判定

**文件层：PASS（25/25应交付文件完成后确认）。**

**数据层：PASS WITH SCIENTIFIC GATES OPEN。** 主表和基线真实可复现，但外部验证、人工provenance、天然产物候选发布和湿实验均未完成。

**战略层：PASS。** 双轴架构符合正确性、可证伪性、创新性、数据质量和长期完成约束；没有把任何路线的未完成状态写成阴性。
