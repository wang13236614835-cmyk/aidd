# Moracin N Gate 3 计划（结果未执行）

**日期：2026-09-13｜状态：plan_frozen / not_executed——Gate 2 通过才解锁执行**

## 实验组（单板四组 + 对照）

| 组 | 内容 |
|---|---|
| G3-1 | Model（PA/OA） |
| G3-2 | Model + Moracin N（取 Gate1/2 有效浓度，单浓度主裁决 + 剂量确认板可选） |
| G3-3 | Model + ML385（5 μM，**须先有 ML385-alone 毒性对照**且自身不伤模型） |
| G3-4 | Model + Moracin N + ML385 |
| 附加必需 | **NRF2 downstream readout ≥1**（NQO1 / HO-1 / GCLC / GPX4 / SLC7A11 按平台条件选一）：证明 ML385 确实压制了 NRF2 信号（工具药生效证明，缺失则 Gate 3 无效） |

## 削减率判据（预冻结）

以 Model→MN 保护量为分母：(G3-2 效应 − G3-4 效应)/G3-2 效应：

- **≥70%**：允许表述 **"supports NRF2 signaling involvement"**（药理阻断层面）；
- **30–70%**：中间带 → 重复批次 + 正交验证（siNRF2）后才可表态；
- **<30%**：撤销"NRF2 主要介质"表述；候选不连带出局（回退按 A 轴对象处理）。

## 表述边界（按本轮口径修正）

- 允许：`supports NRF2 signaling involvement`、`NRF2-dependent protection is supported by pharmacological blockade`；
- 禁止：`NRF2 因果机制完全证实`、`Moracin N 激活/靶向 NRF2`、`直接 KEAP1 结合`；
- 因果等级升级唯一路径：siNRF2（Level 4），条件允许时作为正交验证追加，不与药理阻断混写。

## 预算与采购联动

ML385（HY-100523 ¥300/1mg 或试用装）在 Gate2 过关后才下单（分期条款维持）；siNRF2/转染试剂仅在导师批准扩展时进入。
