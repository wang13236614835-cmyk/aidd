# FASN 疾病与临床证据审计

## 一、问题定义

FASN（fatty acid synthase）是 de novo lipogenesis 的核心酶。本路线不从“FASN 是热门靶点”出发，而回答一个明确问题：

> 具有可追溯天然来源的分子，能否直接抑制人 FASN，并在肝细胞脂毒性模型中降低脂质生成/蓄积；酶抑制与细胞表型是否一致？

这与 Moracin N 的 NRF2/ferroptosis 功能验证轴互补：FASN 处理“脂质负荷生成”，Moracin N 处理“脂质过氧化损伤耐受”。

## 二、MASH 疾病合理性

### 1. 机制层

MASH 的脂质负荷、脂毒性、炎症和纤维化相互连接。FASN 位于脂肪酸新生合成关键节点，因此抑制 FASN 具有疾病机制合理性。但基因/蛋白表达关联不能自动证明药理抑制的疗效；必须区分：

- FASN 表达或转录关联；
- FASN 酶活抑制；
- 肝细胞 DNL/脂滴/TG 改变；
- 组织学 MASH 消退和纤维化改善。

### 2. 人体临床证据：denifanstat

PubMed PMID 39396529（Lancet Gastroenterology & Hepatology，2024）报告 denifanstat/TVB-2640 的 FASCINATE-2 Phase 2b：

- 多中心、随机、双盲、安慰剂对照；
- 100个临床中心；
- 活检确证 F2/F3 MASH；
- 50 mg、每日一次、52周；
- 168人随机：denifanstat 112人、安慰剂56人；
- NAS改善≥2分且纤维化不恶化：42/112（38%）vs 9/56（16%），风险差21.0%，95% CI 8.1–33.9，P=0.0035；
- MASH消退且NAS改善≥2分、纤维化不恶化：29/112（26%）vs 6/56（11%），风险差13.0%，95% CI 0.7–25.3，P=0.0173；
- 常见治疗期间事件包括脱发21/112（19%）和干眼10/112（9%）；研究摘要称药物相关事件均为1–2级。

该结果支持“FASN抑制具有临床转化信号”，但不等于天然产物 FASN 抑制已被证明。

### 3. 当前开发状态必须谨慎

2025-05 SEC/公司披露明确写出 FDA End-of-Phase-2沟通支持推进 MASH Phase 3，但 F2/F3 MASH Phase 3在获得足够资金前不启动；同一披露将中国痤疮 Phase 3 单独列出。2026可访问公司更新中明确的 Phase 3计划主要指向痤疮。因此本项目统一写：

> denifanstat 在 MASH Phase 2b有阳性组织学信号；MASH Phase 3存在计划/资金条件限制，当前是否已启动需以ClinicalTrials.gov或公司原始登记进一步闭合。

禁止写“FASN临床失败”，也禁止写“FASN已进入MASH Phase 3”。靶点临床验证与公司开发优先级不是同一件事。

## 三、天然产物证据

### 直接 FASN 酶抑制或相关证据

- phloretin：PMID 40949263（2025）报告生化 FASN IC50 4.90±0.66 μM；主要细胞情境为乳腺癌，不是 MASH。
- EGCG：PMID 19189648报告绿茶儿茶素抑制 FASN并有肿瘤/动物背景；不是当前54库的 Moracin N 证据。
- asiatic acid、quercetin、kaempferol：PMID 37854347报告从积雪草分离后 FAS 抑制，IC50约9.52、43.09、36.90 μg/mL；不是当前54库直接证据。
- baicalein：PMID 35847050在果糖诱导大鼠肝脂变中降低 FASN/ACC等脂生成分子，属于肝脂变机制证据，不能替代纯化 FASN 直接抑制。

本轮指定 PubMed 检索式下，未发现 Moracin N×FASN 或 Formononetin×FASN 的直接标题/摘要证据。该表述仅限指定数据库、检索式和日期，不等于证明全世界不存在相关研究。

## 四、项目内证据边界

- 54×FASN docking全部完成并有历史排名，但已知 docking discrimination 规则不足，不能用它证明天然产物抑制 FASN。
- 旧 FASN redock存在参考化学身份不一致、seed敏感和错误“dual-basin”表述撤回等问题。
- 当前可用的真实资产是 FASN ChEMBL provenance 主表和 baseline，而不是旧对接榜。

## 五、风险

1. FASN 数据主要来自肿瘤药化研究，assay条件、结构域、裂解物和全长重组酶不完全一致。
2. 天然多酚可能发生胶体聚集、荧光/吸光干扰或非特异性氧化还原反应。
3. FASN 酶抑制不保证细胞暴露、肝选择性或 MASH 组织学获益。
4. denifanstat 临床信号存在公司资金与开发优先级约束，不能把单个项目状态扩大为靶点成败。
5. 当前 FASN 外部验证尚未完成，模型不能放行天然产物总榜。

## 六、审计结论

FASN 同时具备疾病因果合理性、临床药理信号和足够的公开活性数据，**适合承担长期 AIDD 主轴**。但当前必须把“有资格建模”与“模型已泛化”分开：先重建 provenance、做严格 split/UQ/AD和外部验证，后做天然产物预测，再做直接酶与肝细胞实验。
