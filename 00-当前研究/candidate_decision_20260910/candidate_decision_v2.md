# 当前候选裁决 v2（2026-09-10，疾病证据优先）

## 裁决结论
原先的三候选不再足够覆盖当前证据。经 A 级竞争者摘要/开放全文升级后，首轮实验应采用“疾病证据面板”，而不是围绕单个 docking 高分分子做长周期开发。

### 首轮疾病验证面板（建议 6 个）
1. **scoparone**：本体 NASH/MASLD 证据密度高，开放摘要支持 MCD-NASH、HFD-MASLD、炎症/自噬/纤维化方向；主要限制是 MCD 模型外推和直接靶点未闭环。
2. **alisol B**：开放全文支持 DIO+CCl4 与 CDA 饮食 NASH 小鼠的脂肪变、炎症、纤维化改善；有 CD36/RARα-PPARγ 机制线索；必须区分母体和 AB23A。
3. **hyperoside**：开放全文/摘要支持 NASH/NAFLD 及纤维化改善，Flot2/TLR4/NLRP3、菌群/胆汁酸方向突出；糖苷可测性和直接结合条件需核查。
4. **puerarin**：本体 NASH/MASLD 证据丰富，涉及 PAI-1-自噬-巨噬 M2、SIRT1/Nrf2、铁死亡和肠-肝轴；糖苷暴露是主要缺口。
5. **isorhamnetin**：仍保留为疾病优先候选，但排在可测性前置之后；NASH/MASLD 证据强，FXR 方向有摘要线索，聚集/检测干扰必须先排除。
6. **formononetin**：作为独立机制锚与备选；MCD-NASH+SIRT1/FAO 证据及 FXR SPR/报告基因全文证据可追溯，但 FXR 与疾病表型桥接可能重复或失败。

### 第二轮/备选面板
- **isoquercitrin**：HFD-NASH/MCD steatohepatitis 开放全文支持，galectin-3/NLRP3 机制；本体、异构体和衍生物需分开。
- **1-deoxynojirimycin**：CDAHFD-MASH 与 HFD-NASH 支持，开放摘要提示纤维化改善；需全文核查剂量和组织学。
- **ursolic acid**：MASLD/NASH 本体研究及 SPP1/decorin 机制，但低溶解度/递送风险较高。
- **moracin N**：保留为唯一探索性铁死亡分支；无本体 MASH 证据，不进入疾病首轮面板的主排序。

## 为什么不采用单一首选
- scoparone/alisol B/hyperoside/puerarin 的疾病证据已足以构成同等级竞争者；原先将 isorhamnetin 单独置首选会低估候选池不确定性。
- isorhamnetin 的病理覆盖强，但直接结合和干扰风险尚未闭环；应通过前置可测性实验决定是否前移。
- formononetin 的机制证据最可追溯，但其 FXR 发现已发表，新增价值在疾病表型因果桥接。
- moracin N 的价值是低成本检验新假说，而不是已有疾病证据。

## 首轮实验排序（建议）
### Gate 0：身份与可测性
6 个首轮分子全部做：CoA/纯度/盐型/溶解性、培养基稳定性、浊度/离心上清、无细胞报告/检测试剂干扰、细胞活性。

### Gate 1：共同疾病表型
scoparone、alisol B、hyperoside、puerarin、isorhamnetin、formononetin 同一套 PA/OA 肝细胞模型；主终点 TG/油红 O 或等价脂质定量，辅以细胞活性/LDH。

### Gate 2：按证据分流
- FXR：isorhamnetin、formononetin、hyperoside、puerarin 中仅对 Gate 1 阳性且无干扰者做 FXR 敲低/拮抗、SHP/BSEP 和正交结合/功能。
- 炎症/纤维化：scoparone、alisol B、hyperoside、ursolic acid 在肝细胞与 LX2/HSC 中分开评价。
- 铁死亡：moracin N 和 puerarin 仅在相应表型有效后做 erastin/RSL3、C11-BODIPY、铁、GSH/GPX4、ferrostatin-1/DFO 救援。

### Gate 3：决定动物候选
只有身份/可测性、疾病表型、机制方向和初步暴露均支持者，才讨论动物模型；动物不由 docking 分数或模型概率决定。

## AI模型裁决
- FXR LanthaScreen 模型内部骨架留出性能有探索价值，但10次切分ROC-AUC范围0.755–0.990，且54/54天然产物低于训练域拒判阈值。
- 因此当前AI模型不能主导54库候选排序；用途限于方法学、域外拒判、实验假说和后续主动学习。
- 后续模型必须使用实验反馈、同口径 assay、骨架/时间锁定验证，且不允许在锁定集揭盲后调参。
