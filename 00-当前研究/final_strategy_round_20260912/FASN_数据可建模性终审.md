# FASN 数据可建模性终审

## 一、数据审计快照

查询日期：2026-09-12；靶点：人源 FASN，CHEMBL4158，UniProt P49327。

| 层级 | 数量/状态 |
|---|---:|
| ChEMBL全量 activity | 5,541 |
| 全量 relation=`=` | 3,197 |
| 全量 relation为 `<`、`>`、`<=`、`>=` 或缺失 | 2,344 |
| 全量 IC50 | 3,926 |
| 全量 Ki | 21 |
| 全量 Kd | 2 |
| 全量 standard_units=nM | 3,903 |
| 精确主表记录 | 1,652 |
| 精确主表分子 | 1,139 |
| 精确主表 assay | 51 |
| 精确主表 document | 34 |
| 精确主表 endpoint | IC50 1,630；Ki 20；Kd 2 |
| 精确主表单位 | nM 1,637；ug.mL-1 15 |
| 主表有效SMILES | 1,652/1,652 |
| 主表多片段SMILES | 2条，已标记 |

主表位置：`FASN_activity_master.csv`。全量 relation/censor 原始下载：`raw/FASN_all_activity_records.json`；审计：`derived/FASN_all_activity_quality_audit.json`。

## 二、assay provenance 不是可忽略的细节

精确主表跨 51 个 assay 和34个文献来源。按 assay 描述的保守分类：

- cell-extract相关：1,139条记录；804个去重分子；
- full-length-stated：302条记录；208个去重分子；
- KR domain：2条记录；
- TE domain：24条记录；
- 其他或无法从 activity 描述安全归类：185条记录。

这一分类是文献/assay描述的审计标签，不代表每条记录都完成构建体人工确认。尤其不能把 cell extract、full-length enzyme、KR domain和TE domain平均成一个“FASN IC50”。

## 三、canonical开发集与镜像记录

为减少跨 assay 混合，先选最大的同类 FASN-SPA assay：

- canonical assay：CHEMBL5731051；
- 97条精确nM IC50记录；
- 96个去重分子；
- 39个Murcko scaffold；
- 1个分子在同一 assay内有重复记录，模型前按分子取中位数。

第二个大型 SPA assay CHEMBL5734379有97条记录、96个分子，与 canonical assay共享89个分子，数值高度镜像；因此不把它当作独立 external test。若将其作为外部验证，会高估泛化能力。

## 四、真实 baseline 结果

代码：`run_fasn_canonical_multiseed.py`；seed：20260912–20260916；特征：Morgan/ECFP radius 2、2048 bits。

### canonical assay随机 split（5 seed中位数）

| 模型 | MAE | RMSE | R² | Spearman |
|---|---:|---:|---:|---:|
| 均值 | 0.518 | 0.654 | −0.047 | 不适用 |
| 描述符RF | 0.382 | 0.477 | 0.440 | 0.660 |
| ECFP-RF | 0.407 | 0.510 | 0.394 | 0.765 |
| ECFP-Ridge | 0.252 | 0.345 | 0.722 | 0.882 |
| ECFP-XGBoost | 0.254 | 0.351 | 0.729 | 0.908 |

### canonical assay scaffold split（5 seed中位数）

| 模型 | MAE | RMSE | R² | Spearman |
|---|---:|---:|---:|---:|
| 均值 | 0.579 | 0.705 | −0.016 | 不适用 |
| 描述符RF | 0.451 | 0.567 | 0.490 | 0.516 |
| ECFP-RF | 0.450 | 0.549 | 0.336 | 0.583 |
| ECFP-Ridge | 0.261 | 0.307 | 0.736 | 0.844 |
| ECFP-XGBoost | 0.331 | 0.448 | 0.626 | 0.755 |

### time sensitivity

使用 full-length-stated宽口径，按分子最早年份分组；2017训练、2018–2019测试；这是异质性敏感性分析，不是external validation：

- 均值：R² −0.231；
- ECFP-RF：R² −0.061，Spearman 0.226；
- ECFP-XGBoost：R² −0.423，Spearman 0.251。

## 五、UQ/适用域

scaffold-disjoint split-conformal诊断显示：

- ECFP-RF在alpha=0.10时测试覆盖率中位约0.923，范围0.889–1.000；区间宽度中位约1.93 pActivity；
- ECFP-XGBoost在alpha=0.10时覆盖率中位约0.955，但范围0.722–1.000；区间宽度中位约1.86 pActivity；
- alpha=0.20时覆盖率随seed下降并波动，说明小样本校准不稳定；
- 54个天然产物到canonical训练集最大Tanimoto：中位约0.136，范围约0.078–0.171。

这里不人为设置普适相似度阈值，不把这些预测放行为候选排序。天然产物输出统一标记为探索性/OOD或未评估。

## 六、终审结论

FASN的结论是：

1. **数量资格：通过。** 公开数据足以支撑长期数据工程和传统机器学习开发。
2. **provenance资格：有条件通过。** 主表已保留 activity/assay/document/单位/关系等字段，但仍需进一步人工确认构建体和实验家族。
3. **可学习性：初步支持。** canonical assay的严格 scaffold split下，ECFP-XGBoost和ECFP-Ridge显示可学习信号，但模型和样本量仍小。
4. **外推资格：未通过。** time sensitivity为负，54库明显远离canonical训练域，尚无独立external validation。
5. **候选释放：不通过。** 不得用当前FASN模型预测直接发布54个天然产物总榜。
6. **GNN：暂不启用。** 只有完成新数据冻结、严格外部验证和基线增益后再审。

因此 FASN 可以作为长期主 AIDD 轴，但必须写成“资格赛进行中”，而不是“模型已经成功”。
