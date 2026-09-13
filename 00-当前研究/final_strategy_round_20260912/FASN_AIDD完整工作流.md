# FASN AIDD 完整工作流

## 总体问题

> 天然产物能否通过可追溯的 FASN 直接抑制，减少 de novo lipogenesis，并在肝细胞脂毒性中降低脂质负荷？

## 工作流

### 1. 数据获取

从ChEMBL、BindingDB、PubChem BioAssay和文献补充获取：

- molecule、activity、assay、document和target ID；
- canonical SMILES、InChIKey、物种和构建体；
- activity type、relation、value、unit；
- assay description、substrate、cofactor、反应时间、读出；
- DOI、PMID、来源数据库和日期。

本轮已保存 ChEMBL FASN 5,541条全量activity和1,652条精确主表，分别位于 `raw/FASN_all_activity_records.json` 和 `FASN_activity_master.csv`。

### 2. provenance和清洗

- 物种固定为Homo sapiens；
- 精确模型只用relation=`=`；
- `<`、`>`、缺失关系保留作删失审计；
- IC50、Ki、Kd分层，不直接平均；
- nM直接转换，µg/mL只有在MW可追溯时显式换算；
- 逐activity保留，模型层再按分子/assay聚合；
- 不把cell extract、全长、KR、TE混合。

### 3. 结构和化学空间

- RDKit解析、规范化和InChIKey；
- 盐、碎片、混合物、未定义立体和潜在聚集标记；
- Murcko scaffold；
- ECFP/Morgan radius 2、2048 bits；
- 训练域相似度和最近邻适用域。

### 4. assay-specific baseline

顺序固定：

1. mean/median；
2. physicochemical descriptors + RF；
3. ECFP + RF；
4. ECFP + Ridge/XGBoost；
5. 只有在条件满足后才考虑GNN。

### 5. 验证

- molecule-level random split仅作参考；
- scaffold split是主内部外推测试；
- time split用于新文献/时间漂移敏感性；
- external test在调参前锁定；
- 指标包括MAE、RMSE、R²、Spearman、PR-AUC/ROC-AUC、校准、UQ覆盖。

### 6. UQ和拒判

- split-conformal或ensemble spread；
- 最近邻Tanimoto、scaffold覆盖和化学空间距离；
- prediction interval必须和AD并列输出；
- OOD样本输出拒判，而不是精确pIC50。

### 7. 天然产物预测

只有当模型资格门通过后，才对Tier 1/2/3库预测。输出：

- 模型预测；
- 模型不确定性；
- 训练域相似度；
- 来源和结构证据；
- 干扰风险；
- 结论级别：在域探索、域外拒判、待身份审核或不建议检测。

### 8. 实验验证

- 先测直接FASN酶活阳性参照；
- 同批设置机制阴性、光学干扰、胶体聚集和非特异性抑制对照；
- 再测肝细胞PA/OA模型中的TG、脂滴和DNL支持读出；
- 活力与暴露窗口并列；
- 酶阳性/细胞阳性、酶阳性/细胞阴性和酶阴性/细胞阳性分开解释。

### 9. 结构解释

docking仅可在实验结果之后帮助解释口袋、姿态和结构关系；不能重新成为候选排序核心。

### 10. 释放与发表

- 先发布数据和方法卡，再发布候选；
- 把失败的外部验证、模型不增益和OOD拒判作为结果；
- 不写“发现FASN新药”；
- 若只有内部模型信号，文章定位为assay-aware数据与方法研究；
- 若直接酶+细胞实验形成闭环，才讨论天然产物FASN抑制的机制和转化意义。

## 与Moracin N轴的关系

FASN轴负责“脂质生成”；Moracin N轴负责“脂质过氧化损伤防御”。两条线共同围绕 hepatic lipid burden → lipotoxic injury，但实验和模型结果互不替代。
