# Plan B：FASN / de novo lipogenesis 路线

## 触发条件

Plan B不是同时铺开的第二主线，而是主线A出现明确停止信号后的切换包。触发情形包括：

- Moracin N材料在合理时间内无法获得或COA不合格；
- Gate 1在无毒窗口内无预注册表型改善；
- Gate 3不支持Nrf2主要介质，且没有新的直接机制证据；
- 主线需要在1–3个月内换成更适合ligand-based AIDD的数据路线；
- 预算和平台确认能完成FASN直接酶抑制及肝细胞二级验证。

材料失败时先考虑现有54库的isorhamnetin（但必须过无细胞干扰门）；FASN不是材料失败后的自动替补，而是数据和实验条件满足后的战略切换。

## 目标问题

> 来源可追溯的天然产物是否能直接抑制人FASN，并在肝细胞脂毒性模型中降低DNL/脂质蓄积；其酶抑制与细胞表型是否一致？

## 第一个月：数据冻结

1. 重新获取human FASN CHEMBL4158记录，保存activity_id、assay_id、document_id、assay description、构建体/结构域、standard_type、relation、unit、molecule ID和canonical SMILES/InChIKey。
2. 优先选同一重组人FASN、同一底物和同一检测体系；不同结构域、细胞裂解物和全长酶数据分层保存，不平均混合。
3. 将最新1,652条精确记录作为审计入口；15条ug/mL记录单独换算或排除，不能无声拼接到nM。
4. 预注册数据清洗、pIC50计算、重复值处理、assay冲突处理和时间/骨架锁定。

## 第二个月：模型冻结

- 基线：均值、理化描述符RF。
- 主模型：ECFP/Morgan RF与XGBoost回归/分类。
- 验证：scaffold split、时间冻结、锁定外部文献/assay集；报告MAE/RMSE/Spearman/PR-AUC、bootstrap CI、conformal coverage、最近邻AD。
- 只有在基线严格外推集通过且GNN带来可重复增量时才建GNN；否则不建。
- 天然产物预测若属于训练域外，输出“拒判/探索性假说”，不输出虚假精确pIC50。

## 第三个月：候选与实验

优先选有直接FASN证据的参照和可追溯新候选：phloretin、EGCG、kaempferol、quercetin/asiatic acid等需确认可得性、纯度和疾病层级；现有54库只作为待测来源池，不按旧docking排序。

最小实验：

1. 重组FASN酶抑制（阳性参照+机制阴性/化学型对照）；
2. 直接酶读出与浓度反应；
3. HepG2 PA/OA脂质蓄积、TG/脂质合成支持读出；
4. 活力、浊度、荧光、胶体聚集和非特异性抑制控制；
5. 酶阳性但细胞阴性、酶阴性但细胞阳性分别记录，不强行解释为同一机制。

## 成功条件

- assay-frozen RF/XGB在严格外推验证中优于基线且不依赖单一骨架泄漏；
- 至少一个直接FASN阳性参照在平台复现；
- 至少一个可追溯天然产物在酶 assay中出现可重复浓度依赖；
- 肝细胞读出与酶抑制关系可被明确描述；
- 预算、材料和实验平台均可持续到第二批验证。

## Plan B的失败条件

- 数据清洗后没有可复现的同一assay子集；
- RF/XGB在严格外推集不优于均值/描述符基线；
- 只有多酚非特异性/探针干扰而无酶浓度依赖；
- 直接酶抑制不能复现或与细胞读出完全不一致；
- 实验成本超过两年/本科条件可承受范围。

## 与主线最大复用

复用：54库身份、来源审计、RDKit/ECFP/RF/XGB代码、AD/不确定性模板、HepG2 PA/OA脂毒性模型、统计预注册纪律。

不复用：THRβ/FXR/FASN旧docking排名、旧FASN错误cluster性能、无assay provenance的pIC50平均表、人工综合分。
