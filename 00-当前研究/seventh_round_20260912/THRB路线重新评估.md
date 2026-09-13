# THRβ 路线重新评估

## 结论

THRβ 是高价值临床靶点，但**不再是本项目当前主线**。它保留为：

1. 疾病临床锚点（resmetirom 已验证 THRβ 激动的临床价值）；
2. 现成 reporter 平台允许时的最小机制裁决；
3. ligand-based assay-specific 模型的独立备选，不再由 docking 驱动。

## 临床价值和本项目适配度必须分开

- resmetirom 的批准和 VK2809 的 Phase 2b 结果说明 THRβ 具有强临床转化价值。
- 这只回答“THRβ 是值得开发的 MASH 靶点”，不回答“当前 54 个天然产物中的 Moracin N 是 THRβ 激动剂”。
- 肝选择性、TRα counter-screen、激动/拮抗方向、T3 协同和细胞报告系统干扰都是本项目必须面对的额外实验层。

## 直接证据和数据

- human THRB CHEMBL1947：最新总 activity 8,122；精确标准记录 6,839，主要为 Potency 5,954，另有 IC50 541、EC50 191、Ki 118、Kd 35；去重分子 5,669（按本轮下载口径）。
- 数据量大，但端点和 assay format 混合；不能将 Potency、IC50、EC50、Ki、Kd 合成一个“THRβ激动活性”标签。
- 可作为起点的子集是 single-protein IC50：329 条记录、约 225 个分子；该子集可以做 RF/XGBoost exploratory model，但不是外部验证。
- THRβ/TRα paired benchmark 只有 39 对，适合做 counter-screen 参考，不足以为 54 个天然产物建立可靠选择性预测器。

## Docking 门控后的硬结论

- 旧 2J4A N331S：ROC-AUC 0.346，且残差方向曾存在错误。
- WT 3GWS：ROC-AUC 0.472，95% CI 0.341–0.607；PR-AUC 0.693，分层 AUC 0.596/0.232/0.587。
- T3/GC-1 姿态恢复通过，只证明结构协议可近似重现晶体姿态。
- Moracin N docking 分数高不能升级为 TRβ 配体、激动剂、选择性分子或抗 MASH 候选。

## Moracin N×THRβ 证据审计

截至 2026-09-12，在指定 PubMed/ChEMBL/BindingDB/PubChem 检索边界与检索式下，未发现 Moracin N×THRβ/TRα 的直接结合或功能实验记录。现有信息为结构计算假说，不能与 Moracin N 的神经元 Nrf2/ferroptosis 直接实验证据等量齐观。

## 如果保留，正确的计算方法

- 只使用 assay-specific ligand model：single-protein IC50 或明确的功能 reporter assay，且不混合方向。
- 先 RF/ECFP 和 XGBoost，后考虑 GNN；采用 scaffold/time split、锁定外部验证、AD、uncertainty。
- 另建 TRα counter-model或使用 paired assay 数据；输出 activity 与 β/α selectivity 两个独立问题。
- docking 只做姿态/口袋解释，不进入排序、总榜或候选 release。

## 最小实验门

若导师平台已有双荧光素酶/质粒/转染条件，做：TRβ、TRα、空载体、T3阳性；Moracin N单点和T3亚饱和敏化臂；细胞活力和报告干扰对照。结果只回答“是否存在某种TR功能调节”，不直接等于亲和力或疗效。

## 为什么不当主线

THRβ 的疾病价值最高，但当前项目的实质未知量是天然产物能否产生清晰、低成本、可证伪的机制结果。THRβ 需要双亚型、双方向和报告系统干扰控制；Moracin N 侧没有直接 TR 证据；现有 docking 门控失败。相同预算下，Nrf2/ferroptosis 已有 Moracin N 直接机制锚，优先级更高。
