# Moracin N 双轴判读框架（Gate 1 结果判读预冻结）

**日期：2026-09-13｜状态：框架冻结，结果 not_executed**

## 一、两条判读轴

| 轴 | 读数 | 判阳标准 |
|---|---|---|
| **Axis A（anti-steatotic）** | 细胞内 TG（蛋白归一）+ 油红 O | 无毒窗内任一浓度较 Model 下降且统计支持（预注册阈值优先） |
| **Axis B（anti-lipotoxic / anti-ferroptotic）** | C11-BODIPY 脂质过氧化 + 活力（+可选 GSH/GPX4） | 同上；方向须与 Fer-1 参照一致 |

## 二、四象限判读（预冻结，禁止事后修改）

| 组合 | 判读 | 后续动作 |
|---|---|---|
| **A+ B+** | 最佳：抗脂沉积与抗脂毒性/抗铁死亡信号并存 | 直接进 Gate 2（机制一致性） |
| **A− B+** | TG 不降但脂毒性保护存在 → 保留为 **anti-lipotoxic / anti-ferroptotic candidate** | 进 Gate 2；论文叙事按"保护表型非降脂"写 |
| **A+ B−** | 降脂但无铁死亡轴信号 → 提示机制**不是 ferroptosis 主导** | 不进 Gate 2/3 的 NRF2 链；重新评估机制假说（H2 需修正而非直接淘汰分子） |
| **A− B−** | 无可重复有效信号 | 候选优先级显著下降；核对模型资格与材料质量后按 B3 处理 |

**硬规则**：①"TG 没下降 = 候选失败"作为唯一判断是**禁止**的（A− B+ 是合法且可发表的结局）；②只有 Gate 1 出现 **B+** 才进入 Gate 2/3，B− 时不购买 NRF2 机制试剂（ML385/抗体），避免预算浪费；③活力 <80% 的浓度点在任何轴中均无效。

## 三、与三级门控的衔接

- Gate 1 = 本框架的读数产生层；
- Gate 2（ferroptosis consistency）= B+ 信号是否由 C11/GSH/GPX4 + Fer-1 同向支撑；
- Gate 3（NRF2 dependency）= ML385 四组 + NRF2 下游读出生效证明。

## 四、当前执行状态

**not_executed**——物料未到货（见 `MoracinN_material_status.md`）。本框架与 `MoracinN_Gate1_results.csv` 的结构列已在到货前冻结，避免结果出来后再定判读标准。
