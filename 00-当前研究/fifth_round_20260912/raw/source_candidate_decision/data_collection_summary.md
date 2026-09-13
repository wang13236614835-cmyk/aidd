# ChEMBL FXR/TR Week 1 数据收集摘要

原始记录：22790；严格nM候选：11587。

| 目标 | 原始记录 | 严格nM候选 | 主要终点/格式 |
|---|---:|---:|---|
| fxr | 4208 | 4208（严格表中按target统计） | EC50:3715, IC50:469, AC50:16, Kd:8; formats=cell-based format:2529, single protein format:1495, assay format:184 |
| thrb | 6805 | 6805（严格表中按target统计） | Potency:5920, IC50:541, EC50:191, Ki:118, Kd:35; formats=assay format:6095, single protein format:499, cell-based format:210, cell-free format:1 |
| thra | 574 | 574（严格表中按target统计） | IC50:293, EC50:162, Ki:88, Kd:31; formats=single protein format:333, cell-based format:124, assay format:117 |

## 文件
- `chembl_fxr_data.csv`、`chembl_thrb_data.csv`、`chembl_thra_data.csv`：完整人源 target activity 记录。
- `derived/chembl_activity_all_targets.csv`：合并原始表。
- `derived/chembl_numeric_nM_exact_candidates.csv`：standard_flag=1、单位nM、关系符=、正数且有SMILES的候选。
- `derived/chembl_strata_counts.csv`：按target/endpoint/assay格式计数。
- `derived/chembl_pilot_model_metrics.csv`：分层Morgan/RF开发诊断。

## 重要限制
- FXR、TRβ、TRα数据横跨EC50/IC50/Ki/Kd/Potency及single-protein/cell-based/assay format，未合并为单一标签。
- pilot按molecule_chembl_id分组留出，但不是外部验证；未冻结最终开发/锁定测试集。
- 不把pilot指标用于释放54分子候选排名；最终模型必须在assay/终点/构建体分层和锁定测试集后训练。
