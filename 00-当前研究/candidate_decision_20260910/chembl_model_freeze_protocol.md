# ChEMBL分层模型冻结协议（下一轮执行，Week 1后）

## 目标
建立可复核、可解释、不会把不同assay混合的最终训练模型；模型只有在锁定测试集通过后才参与候选排序。

## 数据冻结
1. 人源目标固定：FXR CHEMBL2047、TRβ CHEMBL1947、TRα CHEMBL1860；排除啮齿类目标用于主模型。
2. 纳入条件：standard_flag=1、standard_relation='='、positive numeric standard_value、units=nM、canonical SMILES可解析。
3. 终点分层：EC50、IC50、Ki、Kd、Potency不得默认合并；single-protein、cell-based、assay format分别保存。
4. assay、document、activity、construct、mutation、bao_format全部保留；同一分子跨assay不得简单平均。
5. 训练/开发/锁定测试按照化合物骨架或时间冻结；锁定集揭盲后不调参。

## 主指标
- 回归：MAE/RMSE、Spearman、校准曲线；
- 分类：ROC-AUC、PR-AUC及阳性率基线、MCC、Top-K命中/富集；
- 与MW、LogP、TPSA等简单基线比较；
- bootstrap 95% CI；报告每个stratum的样本量和适用域。

## 模型角色
- 共享分子表征可以使用Morgan/图模型，但任务头按target×endpoint×assay format分开；
- 小样本stratum只做描述性模型，不合并补0；
- 任何stratum锁定测试AUC下限≤0.5或Top-K不超过随机时，该stratum不参与候选排序；
- GNN/RF/基线若高度相关，不称为独立证据；
- 当前Week 1 pilot仅是开发诊断，不是最终模型。

## 释放门槛
只有同时满足：
1. 锁定测试ROC-AUC 95%CI下限>0.5；
2. 预定Top-K富集超过随机且CI支持；
3. 相对简单理化属性基线有增量；
4. 化合物骨架/适用域泄漏审查通过；
5. 外部或真正未参与调参的锁定数据已完成；
才允许用模型协助候选排序。否则只作数据审计和假说生成。
