# FASN GNN 启用门控

## 结论

**当前不启用 GNN。** FASN 长期主 AIDD 轴先用可审计的 RF/XGBoost/Ridge 完成资格赛。项目标题中曾有“贝叶斯图神经网络”，不能成为跳过数据和基线的理由。

## 启用前必须满足的八个条件

### 条件1：数据身份闭合

- molecule_id、canonical_smiles、InChIKey、activity_id、assay_id、document_id齐全；
- 物种、构建体/结构域、底物、辅因子、检测方式可追溯；
- relation、单位和删失值规则已冻结；
- 结构盐、混合物、碎片、立体化学已分别标记。

### 条件2：同质 assay 主集

- 不能将cell extract、全长重组酶、KR/TE domain和未知assay平均在一起；
- 主模型至少有一个可解释的同质 assay或assay family；
- 镜像数据不得冒充external test。

### 条件3：基线先行

必须先完成并保存：

- 均值/中位数；
- 理化描述符RF；
- ECFP-RF；
- ECFP-XGBoost；
- 可选ECFP-Ridge；
- 同一split、同一指标和同一预处理比较。

### 条件4：严格外推验证

- scaffold split至少5个seed或等价重复；
- 有时间信息时进行time split；
- 不能只报告random split；
- 指标包括RMSE、MAE、R²、Spearman、校准/覆盖和不确定性。

### 条件5：独立验证

外部集必须在模型调整前锁定。它不能来自：

- 同一分子重复记录；
- mirrored ChEMBL assay；
- 训练文献的另一种同源表示；
- 调参后才挑出的“好看”数据。

### 条件6：基线存在稳定结构信号

如果RF/XGBoost/Ridge在严格scaffold/time/external中均接近均值，或结果方向在seed间不稳定，则 GNN 的预期增益没有证据，门控失败。

### 条件7：GNN有可验证增益

GNN必须在锁定外部或严格外推集上，相对于最佳传统基线提供稳定增益，且：

- 不能只在random split增益；
- 不能只由一个seed支撑；
- 需要报告置信区间或多seed分布；
- 需要显示不确定性与误差相关，而非只显示AUC/R²。

### 条件8：天然产物适用域可解释

GNN输出必须同时给出：

- 最近邻相似度/距离；
- scaffold是否覆盖；
- 预测区间或ensemble spread；
- 拒判状态；
- 候选来源和结构证据。

## 当前运行结果对门控的影响

canonical FASN SPA assay（96分子、39骨架）的5 seed结果显示：

- ECFP-XGBoost scaffold R²中位0.626；
- ECFP-Ridge scaffold R²中位0.736；
- ECFP-RF scaffold R²中位0.336；
- seed间模型相对顺序和误差仍有差异；
- 宽口径time sensitivity的RF/XGB R²为负；
- 54个天然产物最大Tanimoto中位约0.136。

因此当前结论是“传统基线需要继续审计，天然产物外推未放行”，而不是“GNN可以解决外推”。

## GNN Go/No-Go

### Go

只有在上述八条件全部满足，且至少一个严格外部集上GNN稳定优于最佳RF/XGB/Ridge，才允许：

- 训练正式GNN；
- 保存模型卡和权重；
- 输出带UQ/AD的候选假说。

### No-Go

任一条件失败：

- 停止GNN投入；
- 保留传统模型和失败结果；
- 把项目定位为assay-aware传统QSAR/化学信息学；
- 不删除“GNN未带来增益”的事实；
- 不把更换网络结构当作翻案理由。

## 与原大创题目的关系

原题目可以通过标题修订保留“计算辅助/机器学习”方向，但不承诺GNN一定是最终最佳模型。方法真实性优先于题目中的算法名。
