# AIDD 方法最终选择

## 最终方法

本项目最终采用：

> **证据驱动的机制重定位（evidence-driven repositioning）+ assay/化学空间审计 + 适用域与干扰控制 + 最小因果实验验证。**

它仍然属于计算辅助药物研究，但不把 AIDD 等同于 docking，也不强行把每条机制路线改造成GNN回归。

## 为什么主线不训练 KEAP1/NRF2 GNN

- KEAP1 ChEMBL有615条精确记录、460个去重分子，但包含肽竞争、PPI阻断、Kd/Ki/IC50等不同层级和构建体，不能直接拼成一个统一“NRF2活性”标签。
- NRF2、GPX4、SLC7A11和ACSL4在本路线中主要是通路节点和功能读出，不是同一直接小分子结合靶点。
- Moracin N的直接证据是神经元抗铁死亡和Nrf2因果阻断，不是KEAP1直接结合数据。
- 没有统一、高质量、与当前天然产物化学空间相匹配的 direct binding/activity dataset 时，训练深度模型会把机制异质性伪装成样本量。

## 主线的计算步骤

1. **疾病问题定义。** 只研究“MASH相关肝细胞脂质蓄积+脂毒性氧化应激”，不把单一细胞板称为完整MASH。
2. **证据图谱。** 分开整理 Moracin N神经元直接机制、MASH铁死亡独立证据、跨疾病迁移缺口和反向安全提示。
3. **分子身份和来源。** CAS、CID、InChIKey、规范SMILES、供应商COA、药材来源证据分级；database-only不写成实验分离。
4. **无细胞可测性/干扰审计。** 浊度、光谱、探针淬灭、溶剂、聚集和报告系统干扰先于机制实验。
5. **结构解释。** 既有TRβ/FASN/FXR docking只用于口袋可容纳性、姿态和候选历史解释；不进入优先级、激动/拮抗预测或亚型选择性结论。
6. **预注册实验。** 依次 Gate 0 → Gate 1表型 → Gate 2机制方向 → Gate 3 ML385因果，保存阴性和未完成状态。
7. **不确定性报告。** 对所有结果报告原始点、重复数、效应区间、适用模型边界，不用人工综合分。

## FASN Plan B 的计算步骤

若主线触发切换：

1. 新鲜下载 FASN activity，并保留 activity/assay/document/construct/standard relation/unit。
2. 选择单一、可复现的 human full-length/recombinant enzyme assay；不同结构域和cell lysate不混合。
3. 先做均值基线、描述符RF、ECFP/Morgan RF、XGBoost；scaffold split、时间锁定和外部文献验证先于任何GNN。
4. 输出 pIC50预测、conformal区间、最近邻Tanimoto、拒判状态；天然产物域外时输出“不可判”而不是精确活性。
5. 只有在基线严格外推集上稳定、且有外部增益时才加入GNN；否则GNN不产生额外科学价值。
6. 用有直接FASN证据的天然产物/参照建立阳性体系，再做现有库和扩展库。

## THRβ保留线的计算步骤

- 只冻结单一 endpoint/assay/construct，例如 human THRβ single-protein IC50；不混合5,954条Potency。
- RF/XGB优先；同步做TRα paired counter-screen，但39对仅作基准。
- 功能reporter结果必须独立于任何Vina分数；docking只作结构解释。

## 模型验收硬规则

- 不能用随机切分单独放行。
- 必须报告 scaffold/time split、外部验证、baseline、AD、uncertainty和拒判。
- 训练标签、活性方向、单位、assay格式、构建体和文献来源不完整，模型状态为“未放行”。
- GNN只有在RF/XGB和均值基线之后有严格外推增量才启动。
- 禁止人工加权综合总分；决策使用证据类别、门控和角色。

## 方法结论

本项目不是放弃AIDD，而是把AIDD从“打分即排序”修正为“计算提出可证伪机制问题，实验完成因果裁决”。这比继续在一个已经失败区分门控的对接体系上增加计算更符合正确性、可验证性和两年完成约束。
