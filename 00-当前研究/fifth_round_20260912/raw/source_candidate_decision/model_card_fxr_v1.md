# FXR模型卡 v1（2026-09-10）

## 模型身份
- 模型：`FXR_LanthaScreen_EC50_ECFP_RF_v1`
- 目标：人源FXR/NR1H4（CHEMBL2047）
- assay：CHEMBL5735838，纯化FXR-LBD LanthaScreen EC50/coactivator FRET
- 输入：324个独立ChEMBL分子、101个Murcko骨架；Morgan/ECFP radius 2，2048 bits；随机森林回归/分类
- 训练源：`derived/chembl_numeric_nM_exact_candidates.csv`，源哈希见`derived/fxr_locked_model/model_manifest.json`

## 内部评估
10个预先声明的骨架分组留出敏感性分析（每次60 train scaffold、20 development、21 locked test scaffold）结果：
- ROC-AUC：均值 0.864，范围 0.755–0.990
- PR-AUC：均值 0.926，范围 0.887–0.988
- 回归MAE：均值 0.547，范围 0.442–0.660
- Top-10 EF：均值 1.542，范围 1.098–2.174

## 适用域与拒判
留一最近邻ECFP Tanimoto的训练集5百分位为0.7805；54库天然产物最近训练分子相似度为0.0632–0.1705，54/54低于拒判阈值。其模型预测均为域外探索性值，不能作为FXR活性阴性或阳性。

## 使用规则
- 该模型可用于同一LanthaScreen assay化学空间的数据审计、方法展示和实验假说生成。
- 不可用作54库候选排序主导证据；不转换为Kd/EC50真实值，不证明疾病疗效。
- 未完成真正外部验证；内部骨架切分结果不能替代外部验证。
- 若用于论文，需同时报告每种子结果、适用域拒判、理化属性基线和失败记录。
