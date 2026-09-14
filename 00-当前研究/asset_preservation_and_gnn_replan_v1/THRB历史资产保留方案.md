# THRβ 历史资产保留方案

## 资产状态

- `2J4A.pdb`、`THRB_2J4A.pdbqt`、共晶配体和历史 docking 输出：保留，状态 `mutant_receptor_exploratory`；
- 3GWS-derived WT receptor、78 配体日志、raw_results、poses、gate metrics：保留为 VERIFIED 的方法学失败证据；
- 依赖 2J4A 或 docking score 形成的 ranking/TOPSIS：解释层 REJECTED/HISTORICAL。

## 当前可用角色

THRβ 保留为临床机制参照和备选 reporter 线；docking 只可支持几何占据/结构假说/技术复现，不可参与活性、候选或 selectivity 排序。

## 不做的动作

不删除 2J4A；不把 2J4A 改写成 WT；不把 WT gate 失败覆盖为通过；不因旧 ranking 失败而重跑全部 docking。
