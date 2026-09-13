# FASN 路线深度审计

## 一、路线定义

FASN 路线回答的问题是：**以 de novo lipogenesis 的核心酶 FASN 为直接计算/实验靶点，能否从可追溯天然产物中建立 assay-specific 活性模型，并把预测与直接酶抑制、肝细胞脂质读出连接起来。**

本路线不是“把旧 FASN docking 榜单重新启用”，也不是把 FASN 预测 pIC50 当成抗 MASH 药效。

## 二、疾病和临床证据

- FASN 处于肝脏 de novo lipogenesis 的关键节点，MASH 的脂质合成和脂毒性机制使其具有疾病相关性。
- denifanstat/TVB-2640 的 FASCINATE-2 Phase 2b 在 F2/F3 MASH 中报告了活检组织学信号；项目 WP1 记录的结果为 MASH 消退 26% vs 4% 安慰剂。该结果支持 FASN 临床转化潜力，但不等于已获批。
- 2025-05 SEC/公司披露称 FDA End-of-Phase-2 沟通支持进入 MASH Phase 3，同时明确在资金到位前不启动 F2/F3 MASH Phase 3；同期把中国痤疮 Phase 3 单独列出。2026 可访问公司更新中明确的 Phase 3 计划指向痤疮，因此 MASH Phase 3 当前状态应写为“有 Phase 3 计划/资金条件限制，是否已启动需另行用注册信息闭合”。
- FASN 的临床路线存在真实信号，但也存在“临床阳性≠天然产物可抑制”和“脂肪合成抑制的系统安全/代谢后果”两层转化风险。

## 三、天然产物证据

已有天然产物或多酚 FASN 证据，但多数不是本项目 54 库内直接、同一 assay、同一疾病模型的证据：

- phloretin：PMID 40949263，2025，生化 FASN IC50 4.90±0.66 μM；主要细胞情境为乳腺癌，不是 MASH。
- EGCG：PMID 19189648，绿茶儿茶素抑制 FASN的肿瘤/动物背景；不是 Moracin N 的证据。
- asiatic acid、quercetin、kaempferol：PMID 37854347 报告分离后 FAS 抑制，IC50 分别约 9.52、43.09、36.90 μg/mL；对象不在当前 54 库。
- baicalein：PMID 35847050 在果糖诱导大鼠肝脂变中降低 FASN/ACC 等脂生成分子，但这属于肝脂变机制证据，不等同纯化 FASN 直接抑制。
- 本轮 PubMed 指定检索式下，未发现 Moracin N×FASN 或 Formononetin×FASN 的直接标题/摘要证据；这不是“全世界无研究”的证明。

结论：天然产物×FASN 的创新空间存在，但需要从“已有多酚先例”中提出具体问题，例如**来源可追溯的天然产物对同一重组人 FASN assay 的直接抑制及其肝细胞 DNL 读出**，而不是笼统声称天然 FASN 抑制剂空白。

## 四、项目内结构和 docking 证据的审计

- 历史 FASN 使用 7MHD/ZEP；历史保存参考的 ZEP 化学式与 CCD 不一致，结构审计标为 `invalid_reference_chemistry`。
- 2026-09 多 seed 结果：固定晶体盒位置基本正确，但 4 个项目协议 seed 只有 1/4 低于 2 Å；最佳姿态约 1.63–2.09 Å，接触残基重合约 95–100%。
- “双盆地/dual-basin”表述已撤回；当前只支持连续构象梯度和 Vina 分辨率有限。
- 54×FASN docking 的 Moracin N 第一名（−10.20）只表示指定协议下的相对分数，不能写成 FASN 抑制剂。

因此 FASN 路线不能从 docking 直接启动采购，必须从数据 provenance 和直接酶 assay 重新开始。

## 五、ChEMBL 数据和可建模性

2026-09-12 新鲜审计：

- CHEMBL4158（human FASN）总 activity 5,541。
- 精确标准记录 1,652：IC50 1,630、Ki 20、Kd 2；EC50=0。
- 去重分子 1,139；assay 51；document 34。
- 1,652 条中 1,637 条为可直接转 nM 的记录，另有 15 条 ug/mL 需单独处理或排除。

数量上，FASN 足以建立 assay-specific RF/XGBoost 训练集。但历史 clean 表只留下 `std_smiles,pIC50,n_rep`，不同 assay/document/construct 可能被合并平均。旧 FASN 模型结果（如随机或错误 cluster split 下 R²≈0.638/0.651）不能直接作为当前性能。

## 六、推荐 AIDD 路线

1. 重新下载并保存 activity_id、assay_id、document_id、assay description、target component/construct、standard_type、relation、unit、molecule ID、canonical SMILES/InChIKey。
2. 优先选择同一人源全长或同一重组构建体、同一底物和读出体系的 IC50 子集；不能把不同结构域和细胞裂解物直接平均。
3. 以分子骨架/时间冻结开发集和锁定测试集；保留文献与 assay 级外部验证。
4. 先做均值/理化描述符、Morgan-RF、Morgan-XGBoost；只有 GNN 在严格 scaffold/time/external 条件下提供增量才考虑。
5. 输出最近邻适用域、conformal prediction interval、拒判规则。天然产物 OOD 时只做候选生成，不输出虚假精确 pIC50。
6. 扩展库应加入有直接 FASN 证据且来源/结构可追溯的参照（phloretin、EGCG、kaempferol、quercetin 等）和明确阴性/机制对照；不把它们自动写成 MASH 候选。
7. 直接实验至少包括：重组 FASN 酶抑制、FASN 阳性药理对照、肝细胞脂质/DNL 读出、活力和探针干扰控制。

## 七、为什么本轮不选 FASN 主线

FASN 的“数据量+临床成熟度”优于主线 A，但它需要先修复数据链、扩展或重构候选库、重新建立模型、采购直接酶 assay，并解决天然多酚非特异性/胶体/氧化还原干扰。它是最合理的 Plan B，不是当前 1–3 个月内最小因果问题。

## 八、Plan B 启用条件

同时满足以下条件才把 FASN 升为主线：

- assay-frozen 数据可追溯且严格外推 RF/XGB 相对于基线有稳定增益；
- 至少一个直接 FASN 阳性对照在实验平台复现；
- 现有或扩展天然产物中至少一个候选完成 Gate 0 干扰与身份门；
- 预算和实验平台能够承受酶抑制+肝细胞两级验证；
- Moracin N 主线已因材料失败、Gate1失败或 Gate3机制失败而停止，而不是为了增加工作量并行铺开。
