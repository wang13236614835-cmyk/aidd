# FXR 与 ACC 降级审计

## 一、FXR：从主发现线降为机制锚点/比较轴

### 已确认价值

- FXR 是 MASH 胆汁酸、脂质和炎症调节的重要核受体，疾病生物学价值真实。
- formononetin 已有 FXR SPR KD 1.323 μM、Ostβ报告基因 EC50 0.1972 μM；biochanin A 也有直接 SPR/报告基因和脂毒性功能证据（CJNM 2024，PMID 39510639）。这两者的 FXR 激动身份不是本项目的新发现。
- human FXR ChEMBL 最新精确记录 4,252，去重分子 3,338；同一 LanthaScreen assay 子集 324分子/101骨架可建立探索性RF。

### 为什么不做主发现线

- FXR 的天然产物文献拥挤；当前库内 formononetin/biochanin A 已有已发表验证，重复筛选的边际创新性低。
- OCA 的 MASH开发失败/拒批和瘙痒、LDL等问题说明靶点价值不能替代产品/机制选择。
- 新 FXR RF 在同一 assay 的内部 scaffold留出性能较好，但 54/54天然产物低于Tanimoto拒判阈值0.7805，最近邻范围0.0632–0.1705；模型不能主导现有库排序。
- 旧 FXR GNN随机切分表现好而scaffold外推崩溃，不能将历史AUC写成天然产物泛化。

### 保留的工作

- biochanin A作为FXR板级阳性/QC，而不是创新候选。
- formononetin作为疾病证据锚点，研究FXR阻断后表型残留和FXR–SIRT1因果层级；该支线回答“已知FXR激动剂在本模型中FXR依赖性有多大”，不回答“新发现FXR药物”。
- FXR模型只用于同一 assay的数据审计、方法教学和拒判示范。

## 二、ACC1/ACC2：从计划中的靶点降为附录比较线

### 数据和疾病信号

- human ACC1/ACACA：总activity 1,137；精确IC50 689；去重分子547。
- human ACC2/ACACB：总activity 6,083；精确IC50 4,220；去重分子约4,003。
- 项目旧GEO中 ACACA/ACACB有上调关联，但关联不等于药理因果。
- firsocostat早期临床研究有DNL抑制和肝脂下降信号，同时有高甘油三酯风险；这些证据支持“值得审计”，不支持当前主线。

### 为什么不优于FASN

- ACC1/2需要严格区分亚型和机制方向；ACC2数据量大但并没有形成当前项目内的天然产物候选、assay冻结模型和直接实验闭环。
- 既有ACC2 redock只说明历史共晶配体姿态可恢复，不能外推天然产物抑制。
- 与FASN相比，ACC没有更强的当前天然产物证据、更清晰的现有候选或更低的实验成本。
- 旧ACC2 QSAR n=892、R²=0.514是历史随机split，不能作为天然产物外推证据。

### 之后只做什么

- 保留 ACC1/ACC2 ChEMBL数据审计和GEO关联作为附录。
- 若FASN Plan B需要比较DNL靶点，才建立 ACC1/ACC2 assay-specific RF/XGB；不合并ACC1/ACC2，不用dock分数排天然产物。
- 不采购ACC专用实验材料，不启动ACC大规模MD或新结构筛选。

## 三、降级不是否定

FXR和ACC分别保留为：

- FXR：已知机制阳性体系/比较轴。
- ACC：DNL机制背景和FASN Plan B的竞争参照。

“降级”表示它们不再承担本项目未来1–2年的主发现预算和候选排序，不表示它们在MASH生物学上无价值。
