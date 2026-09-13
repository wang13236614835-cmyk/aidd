# FASN 数据清洗规则

## 一、数据层级

保留三层，不覆盖历史文件：

1. **raw层**：ChEMBL API原始JSON，包含所有endpoint、relation、单位、缺失值和非活性/删失记录。
2. **master层**：逐activity记录的 provenance 表 `FASN_activity_master.csv`，只纳入本轮明确取得的精确标准活性记录。
3. **model层**：按预注册 assay、endpoint和分子聚合后的开发集；每个模型集必须指向master中的记录ID。

## 二、纳入规则

### 1. 靶点和物种

- target_chembl_id必须为CHEMBL4158；
- target organism必须为Homo sapiens；
- 记录target_id、target_name和原始activity_id；
- 其他物种或相近FAS家族记录不静默合并。

### 2. 关系符号

- 定量主模型只纳入 `standard_relation='='`；
- `<`、`>`、`<=`、`>=` 进入删失数据审计，可在未来采用censored regression时单独处理；
- relation缺失不得当作精确值；
- “Not active”或无standard_value的记录不得填成任意下限。

### 3. endpoint

- 主模型优先IC50；
- Ki/Kd另行保存，不与IC50无声混合；
- kon、k_off、Inhibition、Ratio、FC和ED50不进入IC50回归；
- EC50=0在本轮FASN人源数据中不是有效主endpoint，不补造。

### 4. 单位

- nM且value>0：直接转换为pActivity；
- ug.mL-1：只有分子量可追溯且换算假设明确时才可转换；本轮15条µg/mL记录保留 `conversion_method=derived_from_ug_per_mL_and_RDKit_MW`，不得与直接nM记录无标记混合；
- s-1、%、缺失单位不得转换为pIC50；
- 转换公式：`standardized_nM = value × 1,000,000 / MW(g/mol)`；`pActivity = −log10(standardized_nM × 10^-9)`。

## 三、结构标准化

- 保留ChEMBL canonical_smiles作为原始结构字段；
- 计算RDKit canonical/isomeric SMILES和InChIKey作为审计字段；
- 结构解析失败、多个片段、盐/混合物分别标记；不把碎片拼接；
- 立体化学未定义不自动视为同一化合物；
- structure identity与assay identity分开审核。

## 四、重复和矛盾

### 1. 逐activity保留

同一molecule在不同assay或document的记录不能先平均后丢失来源。master必须保留activity_id、assay_id、document_id。

### 2. 同一assay重复

同一分子、同一assay、同一endpoint的重复值，模型层按预注册规则取中位数；同时保留原始值和重复数。若重复值差异明显，进入矛盾记录，不用挑选有利值。

### 3. 跨assay聚合

只有在 assay 描述、构建体、底物/辅因子、读出和document谱系通过人工审核后，才可作为同一 assay family进行分层聚合；默认不跨 assay 平均。

### 4. 镜像数据

若两个ChEMBL assay共享大量相同分子且数值镜像，不得把一个当独立external validation。canonical SPA的CHEMBL5731051与CHEMBL5734379就是本轮示例。

## 五、assay provenance

至少保存：

- assay description；
- assay_type和BAO format；
- biochemical/cell-extract/unknown分类；
- construct/domain的原文线索；
- substrate/cofactor、反应时间和检测方式（若描述提供）；
- document、DOI、PMID、年份；
- data_validity_comment、potential_duplicate和standard_flag。

不同domain、cell extract、全长重组酶和未知来源不能自动混合。

## 六、数据划分

- molecule-level random split仅作参考；
- scaffold split为必须报告的内部外推检验；
- 有年份时做time split；
- external test必须在揭盲前锁定，且不能与训练文献或镜像数据重叠；
- 任何split都必须按molecule/scaffold分组，避免重复结构泄漏。

## 七、释放规则

- 记录清洗完成不等于模型通过；
- 模型通过不等于天然产物在适用域内；
- 天然产物预测必须同时报告AD、UQ和结构身份；
- OOD样本输出“拒判/探索性假说”，不输出看似精确的候选优先级；
- 所有清洗规则、删失记录、失败和未完成项均进入版本manifest。
