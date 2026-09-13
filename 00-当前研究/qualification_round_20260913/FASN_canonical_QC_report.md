# FASN canonical assay QC 报告

**日期：2026-09-13｜数据：CHEMBL5731051（人源全长 FASN SPA，document CHEMBL5725564，2017）｜状态：QC PASS**

## 一、assay 身份核验

| 项 | 值 |
|---|---|
| assay_id | CHEMBL5731051 |
| document | CHEMBL5725564（单文献） |
| 年份 | 2017 |
| 靶点 | CHEMBL4158 / Fatty acid synthase / Homo sapiens |
| 构建体 | 人全长 FASN（full length, 300 ng, 体外纯化；assay description 原文） |
| 底物/辅因子 | ³H-acetyl-CoA + malonyl-CoA + NADPH（100 mM KH₂PO₄ pH 7.5, 1 mM DTT, 60 min） |
| 检测 | ³H-palmitate scintillation proximity assay（LEADseeker） |
| endpoint | IC50，relation 全部 `=`，unit 全部 nM |
| 浓度拟合 | 4 参数 logistic，pIC50=−log(IC50)（描述原文） |

结论：**该 assay 适合承担 canonical assay-specific 建模任务，不更换。**它同时满足：单一文献、单一构建体、单一检测体系、精确关系、nM 单位、人源全长酶。

## 二、完整性 QC 结果（97 条记录 / 96 个分子）

| 检查项 | 结果 | 处理 |
|---|---|---|
| 重复 SMILES / 重复 InChIKey 分子 | 0 组 | 无需处理 |
| 立体异构体对（同 InChIKey 前 14 位、不同全 Key） | 0 对 | 无需处理 |
| 多片段/盐/混合物记录 | 0 条 | 无需处理 |
| 同分子重复活性记录 | 1 个分子（2 条记录） | 建模集取中位数，两条原始 activity_id 保留于 clean 表 |
| MAD×3 离群记录 | 0 条 | 无 |
| 不可能值（pActivity<2 或 >12；nM≤0） | 0 条 | 无 |
| 单位不一致 | 0 条（97/97 nM） | 无 |
| 错误靶点映射 | 0 条（97/97 CHEMBL4158 人源） | 无 |
| SMILES 解析失败 | 0 条 | 无 |

## 三、清洗集

`FASN_canonical_clean.csv`：96 个分子 / 39 个 Murcko scaffold；每分子一行；列含 canonical_smiles、inchikey、scaffold、pActivity（重复取中位数）、n_records、activity_ids、qc_flags、excluded、exclusion_reason。

**本轮零删除**：所有 QC 异常项为零；唯一重复记录分子按预注册规则取中位数，不删除。若未来出现排除，clean 表必须保留原始值、理由与 activity_id。

## 四、必须一起读的两个数据事实（影响解释，不影响 QC）

1. **单文献单系列**：96 个分子全部来自同一文献（同一药物化学战役），训练集内分子间 LOO 最近邻 Tanimoto 中位 **0.885**——这是一个紧密类似物系列，不是 FASN 化学空间的代表样本。
2. **镜像 assay 警戒**：CHEMBL5734379 与本 assay 共享 89 个分子且数值高度一致，已在本轮外部验证中被明确排除，不得作为独立外部测试。

## 五、结论

canonical assay 数据质量合格、provenance 完整、清洗规则可复现，**作为 assay-specific 建模主数据通过 QC**。模型资格的最终裁决见 `FASN_GO_NOGO.md`（其中外部泛化与泄漏审计结果不属于本 QC 范畴）。
