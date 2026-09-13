# 最终训练模型就绪性报告（Week 1）

## 当前可用数据
- 人源FXR CHEMBL2047：13,588条原始activity；严格nM候选4,208条。
- 人源TRβ CHEMBL1947：8,122条原始activity；严格nM候选6,805条，其中Potency assay占大多数。
- 人源TRα CHEMBL1860：1,080条原始activity；严格nM候选574条。
- 完整记录：`derived/chembl_activity_all_targets.csv`、`chembl_fxr_data.csv`、`chembl_thrb_data.csv`、`chembl_thra_data.csv`。
- 严格候选集：`derived/chembl_numeric_nM_exact_candidates.csv`。

## Pilot结果
在同一target/standard_type/BAO format strata内，按molecule_chembl_id分组留出训练随机森林基线，生成：
- `derived/chembl_pilot_model_metrics.csv`
- `derived/chembl_pilot_predictions.csv`
- `derived/chembl_pilot_model_summary.json`

不同strata误差明显不同：FXR EC50单蛋白MAE约0.44 pActivity，TRβ Potency assay MAE约1.10 pActivity。不能把所有数据混合训练后用一个AUC代表模型质量。

## 不得宣称
- pilot不是最终训练模型；
- molecule-group holdout不是外部验证；
- pActivity≥6的AUC是探索性标签，不是通用药效阈值；
- 未完成按文献/assay/时间冻结的锁定测试集；
- 未完成TRβ/TRα配对选择性标签的构建；
- 不能用该pilot直接发布54分子候选排名。

## 下一轮模型冻结条件
1. 按endpoint/assay format/构建体/物种分层；
2. 选择可重复、记录数足够且方向明确的strata；
3. 按化合物骨架或时间冻结开发/验证集，避免同一分子泄漏；
4. 预注册主指标、PR-AUC基线、Top-K富集、理化属性基线和bootstrap区间；
5. 独立锁定测试集揭盲前不得调参；
6. 达不到ROC-AUC下限>0.5和Top-K超过随机时，模型不参与候选决策；
7. 模型权重、特征、数据版本、代码和失败结果一并保存。

现阶段建议先用实验优先级和疾病证据决定首轮化合物，不等待“最终AI模型”再做最小身份/干扰实验；模型工作并行推进，但不能替代湿实验。
