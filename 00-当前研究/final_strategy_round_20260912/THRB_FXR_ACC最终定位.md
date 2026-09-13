# THRβ、FXR、ACC 最终定位

## 一、THRβ

### 疾病价值

THRβ 是 MASH 临床验证最强的靶点之一。resmetirom 已获 FDA 加速批准，VK2809 的 Phase 2b 公司公告也报告了肝脂和组织学结果。这个事实用于临床机制参照，不自动迁移给任何天然产物。

### 为什么不做长期主 AIDD 轴

- human THRB CHEMBL1947 全量 activity虽有8,122条，但其中5,954条为Potency，另外混有IC50、EC50、Ki、Kd和不同assay format；
- single-protein IC50可形成329条记录/约225个分子的探索性子集，但功能方向（激动、拮抗、T3敏化）不能从IC50自动确定；
- TRβ/TRα paired benchmark目前只有39对，不足以为54个天然产物建立可靠选择性预测器；
- WT docking discrimination gate为ROC-AUC 0.472（95% CI 0.341–0.607），不能继续依赖Vina；
- 天然产物与已有训练空间距离较远，双亚型reporter和干扰控制会提高实验成本。

### 最终角色

**临床机制参照/高价值备选靶点/现成平台reporter裁决线。** 若平台已有双荧光素酶、质粒、转染和TRα同步体系，可以做Moracin N最小单点/敏化实验；不新增大规模docking、不以分数做优先级。

## 二、FXR

### 疾病和临床价值

FXR是MASH胆汁酸、脂质和炎症调节的重要机制。OCA的MASH开发经历FDA拒批，瘙痒、LDL等问题说明靶点价值与产品成功必须分开；FXR314仍有公司管线活动，但公开页面缺少完整临床统计。

### 项目内证据

- formononetin：CJNM 2024已报告FXR SPR KD 1.323 μM和Ostβ报告基因EC50 0.1972 μM；
- biochanin A：已有FXR SPR/报告基因和脂毒性功能验证；
- human FXR最新精确记录4,252、去重分子3,338；
- 同一LanthaScreen模型324分子/101骨架内部表现可审计，但54个天然产物全部低于Tanimoto 0.7805拒判阈值。

### 最终角色

**疾病机制锚点、已知阳性体系和FXR依赖性比较轴。** formononetin回答的是FXR阻断后表型残留有多大，biochanin A负责板级QC；不再重复做“新FXR天然产物发现”主线。

## 三、ACC1/ACC2

### 事实

- ACACA/ACC1：总activity1,137、精确IC50 689、去重分子547；
- ACACB/ACC2：总activity6,083、精确IC50 4,220、去重分子约4,003；
- firsocostat早期研究显示DNL抑制和MRI-PDFF下降，但高甘油三酯是明确安全信号；
- 项目内ACC2结构redock不能外推天然产物抑制，旧ACC2 QSAR为随机split历史结果。

### 最终角色

**DNL背景和FASN比较附录。** 不采购ACC实验材料，不启动ACC大规模MD或新结构筛选；只有FASN需要比较ACC1/ACC2时，才重新建立assay-specific模型。

## 四、定位总表

| 方向 | 最终角色 | 不承担的任务 |
|---|---|---|
| THRβ | 临床机制参照/备选reporter线 | docking总榜、天然产物选择性排序 |
| FXR | 疾病机制锚点/阳性QC/比较轴 | 新天然产物主发现 |
| ACC1/2 | DNL附录/FASN竞争参照 | 当前主线实验和候选发布 |
| FASN | 长期主AIDD资格轴 | 在外部验证前发布天然产物总榜 |
| Moracin N–NRF2/ferroptosis | 近期高创新功能验证轴 | 伪造直接靶点GNN、直接KEAP1结论 |
