# ChEMBL数据摘要 v2（2026-09-10）

## 原始记录
- 人源FXR CHEMBL2047：13,588条原始activity；严格nM候选4,208条。
- 人源TRβ CHEMBL1947：8,122条原始activity；严格nM候选6,805条，其中Potency assay占多数。
- 人源TRα CHEMBL1860：1,080条原始activity；严格nM候选574条。
- 全集：`derived/chembl_activity_all_targets.csv`，严格候选集：`derived/chembl_numeric_nM_exact_candidates.csv`。

## 受控层
- `derived/chembl_clean_target_records_v2.csv` 在严格候选集基础上，去除描述明确的污染词（thrombin/TGF-β/TRAF等）并保留target_label/standard_type/bao_label/molecule_chembl_id/standard_relation/standard_units/potential_duplicate过滤。
- 仍包含同口径多文档混集，不假装为单一注释。

## 已训练/可复现的锁定模型
- FXR_LanthaScreen_EC50_ECFP_RF_v1：CHEMBL5735838单assay，324分子、101骨架；10次预先声明骨架分组留出均值ROC-AUC约0.864（0.755–0.990）；MAE均值约0.547；Top-10 EF均值约1.54。
- 适用域拒判阈值（训练分子留一最近邻ECFP Tanimoto 5百分位=0.7805）。
- 54/54天然产物低于该阈值，全部为域外探索性预测。
- 结论：FXR LanthaScreen模型可用于同一assay化学空间审计和方法学展示，不参与54库候选排序。

## TRβ/TRα配对基准
- 同一ChEMBL文献 CHEMBL1140629：
  - TRβ单蛋白IC50 CHEMBL925135；
  - TRα单蛋白IC50 CHEMBL925134。
- 39对配对分子；ΔpActivity(TRβ−TRα)中位数约1.30，37/39在Δ≥0.5；样本量小、构建体/条件需全文审计后才能用于选择性声明。

## 数据集文件
- `derived/chembl_fxr_data.csv`、`derived/chembl_thrb_data.csv`、`derived/chembl_thra_data.csv`：按靶点拆分。
- `derived/chembl_numeric_nM_exact_candidates.csv`：包含fingerprint和额外字段。
- `derived/chembl_clean_target_records_v2.csv`：污染物过滤后候选。
- `derived/chembl_pre_registered_strata.json`：预注册strata边界。
