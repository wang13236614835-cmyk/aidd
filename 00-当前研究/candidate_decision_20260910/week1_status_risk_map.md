# Week 1 研究状态、风险地图与失败模式（2026-09-10）

## 当前完成度

| 工作包 | 状态 | 结论 |
|---|---|---|
| 54分子身份 PubChem 层 | 完成 | 54/54有CID、InChIKey、IUPAC和结构字段；人工来源/部位/批次仍pending |
| 重点分子商业可购性 | 进行中/公开信息受限 | 需要公开供应商页或人工登录核实；未采购、未把库存/价格当事实 |
| isorhamnetin干扰文献 | 进行中 | 本体与结构类似物证据分开；前置无细胞实验方案可执行，未声称实验已做 |
| 高命中竞争者初筛 | 摘要级完成 | 发现scoparone、alisol B、hyperoside、ursolic acid、puerarin、isoquercitrin、1-DNJ等有资格进入Top10复核池；仍需全文和身份/暴露核查 |
| ChEMBL数据收集 | 完成第一轮 | 人源FXR/TRβ/TRα共22,790条原始activity；11,587条进入严格nM数值候选集 |
| 最终训练模型 | 未完成 | 数据终点/assay异质，Week 1仅生成分层pilot，不能称最终模型 |

## 竞争者优先级更新

### A级：建议进入下一轮重点复核
- **scoparone**：本体NAFLD/NASH/MASLD证据密集，摘要级已有MCD-NASH、HFD-NAFLD和MASLD研究；至少有炎症/纤维化方向线索。
- **alisol B**：本体MASLD/NASH证据，Ces2a和RARα-HNF4α-PPARγ-CD36机制线索；必须区分母体与AB23A衍生物。
- **hyperoside**：本体NAFLD/NASH及纤维化证据，Flot2/TLR4/NLRP3和胆汁酸/FXR线索。
- **ursolic acid**：本体MASLD/NASH、SPP1-Th17和decorin-IGF-IR/HIF-1机制线索。
- **puerarin**：本体NASH/MASLD研究多，PAI-1、自噬、SIRT1/Nrf2和铁死亡线索。
- **isoquercitrin**：本体NASH/steatohepatitis研究，galectin-3和NLRP3机制线索。
- **1-deoxynojirimycin**：HFD-NASH及CDAHFD-MASH研究，菌群/自噬/PI3K-AKT-mTOR线索。

### B级：保留但需解决可开发性或病理深度
- vitexin：本体NAFLD/MASLD证据较多，但纤维化和直接靶点不足。
- epicatechin：有NASH/MASLD本体证据，但部分优势来自靶向纳米制剂，母体溶解度/暴露需单独评估。
- oleanolic acid：文献多但包含IRI、衍生物、复方和脂肪变邻近模型，需降级解释。

### 暂不升级
- catechin：命中数高，但前10主要是综述、绿茶提取物、EGCG或多酚混合物，不能转成catechin本体阳性。
- scopoletin：主要是脂肪变/高脂血症、酒精或体外邻近模型，缺少本体MASH纤维化锚。

## ChEMBL数据边界

- 人源FXR：CHEMBL2047，13,588条原始记录；严格nM候选4,208条。
- 人源TRβ：CHEMBL1947，8,122条原始记录；严格nM候选6,805条，其中Potency assay占5,920条。
- 人源TRα：CHEMBL1860，1,080条原始记录；严格nM候选574条。
- 严格候选条件：`standard_flag=1`、`standard_units=nM`、`standard_relation==`、数值为正、保留canonical SMILES。
- 仍不能直接合并：EC50、IC50、Ki、Kd、Potency；single-protein、cell-based和assay format；不同assay、构建体、文献。

### Pilot模型结论
- 仅在同一 target/endpoint/BAO strata 内训练随机森林基线，按 molecule_chembl_id 分组留出。
- 18个有足够记录的 strata 已生成 MAE 和探索性 AUC。
- 例如 FXR EC50 single-protein MAE约0.44 pActivity；TRβ Potency assay MAE约1.10，说明异质性显著。
- 这些是开发诊断，不是外部验证，也不是最终训练模型；不得据此宣称ROC-AUC达标或发布预测候选。

## 风险地图

| 候选/模块 | 疾病证据 | 直接机制 | 暴露/可开发性 | 身份/纯度 | 检测干扰 | 总风险 |
|---|---|---|---|---|---|---|
| isorhamnetin | NASH/MASLD摘要级较强 | FXR interaction摘要级，KD未知 | 未知 | 人工pending | 多酚风险未测 | 高 |
| formononetin | MCD-NASH摘要级 | FXR SPR/报告基因全文级 | 未知 | 人工pending | 未测 | 中-高 |
| moracin N | MASH本体未找到 | 神经铁死亡摘要，外推 | 未知 | 人工pending | 多酚/抗氧化干扰 | 高 |
| scoparone | 本体NASH/MASLD摘要级较强 | PPAR/炎症/氧化应激线索 | 未知 | 人工pending | 香豆素检测风险待测 | 中-高 |
| alisol B | 本体MASLD/NASH摘要级强 | Ces2a/RARα等线索 | 未知 | 母体/衍生物需分开 | 未测 | 中-高 |
| hyperoside | 本体NASH/纤维化摘要级强 | Flot2/TLR4/NLRP3等 | 未知；糖苷可开发性风险 | 人工pending | 多酚/糖苷干扰 | 高 |
| puerarin | 本体NASH/MASLD摘要级强 | PAI-1、自噬、铁死亡等 | 未知；水溶性/暴露需测 | 人工pending | 未测 | 中-高 |

## 失败模式树

1. **isorhamnetin聚集/检测干扰不可排除**
   - 先暂停荧光素酶/MTT结论；改用TG、油红O、C11-BODIPY、qPCR/Western等正交读出。
   - 若仍不可测，formononetin前移。

2. **formononetin FXR桥接失败**
   - 保留为已知疾病/FXR锚，不宣称新增机制。
   - 重新比较scoparone、alisol B、hyperoside、puerarin等A级竞争者。

3. **moracin N仅显示一般抗氧化**
   - 不称铁死亡机制；降级为方法学对照或退出候选。

4. **竞争者全文核查发现更强本体MASH证据**
   - 允许scoparone/alisol B/hyperoside/puerarin等进入Top10并行验证。
   - 不因旧榜单或docking排名排除。

5. **ChEMBL模型在外部锁定集失败**
   - 不调参刷分；模型降级为数据审计/探索性工具。
   - 研究主线转为实验验证与证据链，而不是AI预测排名。

6. **三候选实验均失败或不可解释**
   - 输出“暂无合格候选”，停止无边界换分子/换模型刷阳性。

## Week 1 下一步
1. 完成重点分子供应商页面和CAS/纯度/盐型公开证据；登录/地区限制字段列为待人工确认。
2. 完成 isorhamnetin 本体及结构类似物干扰证据报告和无细胞前置实验方案。
3. 对A级竞争者完成全文优先级核查，先核 scoparone、alisol B、hyperoside、puerarin、ursolic acid。
4. 冻结ChEMBL分层方案；下一轮只选择预注册strata建立外部/时间切分验证，不把pilot当最终模型。
