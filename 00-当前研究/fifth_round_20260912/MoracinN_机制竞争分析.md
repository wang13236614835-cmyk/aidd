# Moracin N 机制竞争分析：H1（THRβ）vs H2（Nrf2/ferroptosis）（第五轮，2026-09-12）

**性质**：双机制竞争审计。禁止默认"docking 第一 → TRβ 候选"；两假说独立取证后比较，只给主假说/备选假说/暂不支持假说，不设人工权重得分。检索边界：PubMed（E-utilities 精确式）、Europe PMC、Crossref、Google Scholar 可见结果、ChEMBL、BindingDB、PubChem BioAssay、ClinicalTrials.gov、Google Patents/WIPO；截至 2026-09-12。

## 一、H1：THRβ 分支

**假说内容**：Moracin N 可能作为 THRβ 功能调节剂影响肝脂代谢。

### 直接证据检索结果

- PubMed 精确式 `"moracin N"[Title/Abstract] AND (THRB OR TRβ OR "thyroid hormone receptor" OR THRA OR TRα)`：**0 命中**（2026-09-12；原始响应 `raw/external/moracin_N_pubmed_*.json`）。
- ChEMBL CHEMBL465881：仅有结构登记，无 THRβ/TRα 活性记录。
- BindingDB BDBM50251014：可见靶点仅 mushroom tyrosinase（IC50 924 nM，PMID 25461329）、porcine pancreatic lipase（IC50 29.7 μM，PMID 25935644）、human aromatase（IC50 31.1 μM，PMID 11678652）——**无 THRβ/TRα/FXR**。
- PubChem BioAssay：AID 357965（aromatase）、1191279（α-glucosidase）、1191280（tyrosinase）、1204217（lipase）等，无 THR/Nrf2/ferroptosis assay。
- 结论（限定表述）：**截至 2026-09-12，在上述数据库与检索式下，未发现 Moracin N × THRβ/TRα 的直接结合或功能实验证据。**

### 计算支持现状

- WT 3GWS 派生受体 4 种子中位 −10.875（范围 −10.881~−10.853）：**仅技术重复性**；旧 N331S 区分门控 FAIL（AUC 0.346）保留；第五轮 WT gate 结果见 `WT_gate_results.md`。
- TRα 对照（3ILZ 紧盒）：moracin N TRB −11.297 / TRA −9.978，Δ=−1.319；口袋残基亚型间实质保守——**无结构选择性依据**，且区分门控失败后 Δ 分数不得解读为亚型倾向。
- **证据层级判定：THRβ structure-based hypothesis（纯结构假说）。不得称 TRβ 激动剂/配体/候选。**

## 二、H2：Nrf2 / ferroptosis 分支

**假说内容**：Moracin N 经 Keap1/Nrf2 → ferroptosis/lipid peroxidation → 肝细胞损伤 → MASH。

### Moracin N 已直接证实的部分（细胞/动物层）

| 证据 | 层级 | 关键结果 | 来源 |
|---|---|---|---|
| HT22 海马神经元 erastin 铁死亡 | 细胞 | 抗铁死亡 EC50 < 0.50 μM；抑制 GSH 耗竭、**GPx4 失活**、ROS、铁积累；上调抗氧化/谷胱甘肽合成基因，下调铁积累/脂质过氧化基因 | Wen L et al., Phytomedicine 2021;90:153641，PMID 34281775，DOI 10.1016/j.phymed.2021.153641 |
| 小鼠 MCAO 缺血再灌注 + 原代神经元 OGD | 动物+细胞 | 脑室内 20 mg/kg/day ×3d；降 FTH1、**ACSL4**、增 GSH 合成；**Keap1/Nrf2 激活；ML385（Nrf2 抑制剂）阻断保护效应** | Zhang J et al., Phytomedicine 2025;148:157253，PMID 40972263，DOI 10.1016/j.phymed.2025.157253 |
| 桑叶纯化本体抗氧化 | 化学/细胞 | 细胞抗氧化 EC50 24.92 μM，DPPH IC50 40.00 μM（一般抗氧化，非 Nrf2 靶向证据） | Tu J et al., Food Chem Toxicol 2019;132:110730，PMID 31369850，DOI 10.1016/j.fct.2019.110730 |
| 反向警示（肿瘤细胞） | 细胞 | A549/PC9 中 10–45 μM **诱导** ROS/凋亡（NAC 逆转）——细胞类型依赖，不能与神经元结果相加 | Gao C et al., Front Pharmacol 2020;11:391，PMID 32477104，DOI 10.3389/fphar.2020.00391 |

精确限制：Zhang 2025 摘要未给 ML385 剂量与原代神经元浓度，不能补写；Wen 2021 明确 GPx4，但未逐项列 SLC7A11/ACSL4 数值；脑室内给药不等于口服生物利用度。

### MASH 侧已证实的部分（与 Moracin N 无关的疾病证据）

| 链节 | 证据 | 来源 |
|---|---|---|
| 铁死亡驱动 NASH 进展 | MCD 小鼠：RSL3 加重、硒酸钠/liproxstatin-1/去铁胺改善 NASH 与肝 GPX4/脂质过氧化 | Qi J et al., Am J Pathol 2020;190(1)，PMID 31610178，DOI 10.1016/j.ajpath.2019.09.011 |
| 肝铁死亡启动 NASH 炎症 | 肝细胞铁死亡→脂质过氧化/炎症触发 | Cell Death Dis 2019;10:449，DOI 10.1038/s41419-019-1678-y |
| NRF2–GSH 防线与 NAFLD | HFD 小鼠/肝细胞：NRF2 上调缓解脂质过氧化与铁死亡 | Liu P et al., Free Radic Biol Med 2023;196:18–31，PMID 36495698，PMC9731892 |
| 同通路天然产物先例（疾病链药理学可行性） | Hinokitiol 靶向肝 Nrf2 抑制肝细胞铁死亡改善 MASH | Phytomedicine 2025;139:156472，PMID 39922149 |

### 两者尚未连接的部分

- **Moracin N × 肝细胞/MASH/NAFLD/肝纤维化直接研究：0 命中**（PubMed 精确式，2026-09-12；`raw/external/moracin_N_pubmed_disease_broad.json`）；ClinicalTrials.gov 0 项；MASH/THRβ/Nrf2 治疗用途专利未检出（Google Patents 仅合成专利 CN118772094B、KR101558733B1）。
- Moracin N 的 Keap1/Nrf2 证据全部来自**脑/神经元**；肝细胞层零数据。
- 神经铁死亡 → 肝细胞脂毒性是**跨疾病机制迁移假设**，非已证实的肝病疗效链。

## 三、维度比较（事实陈述，不赋权）

| 维度 | H1：THRβ | H2：Nrf2/ferroptosis |
|---|---|---|
| Moracin N 直接证据 | 无（检索边界内未发现任何 TR 实验） | 有：神经元/脑缺血细胞+动物，含 ML385 因果阻断；但无肝细胞数据 |
| MASH 靶点证据 | THRβ 激动获批机制（resmetirom，FDA 2024-03）成立，但与 Moracin N 无连接实验 | Nrf2/ferroptosis×MASH 病理与药理（含天然产物先例）成立，与 Moracin N 无肝内连接实验 |
| 创新性 | 若真阳性则为"天然 TRβ 调节剂"新发现，但当前零直接证据、门控 FAIL | "天然抗铁死亡分子 × MASH 重定位"——桑叶来源+神经铁死亡证据已发表，肝侧为空白 |
| 计算支持 | WT 多种子重复性好+姿态恢复通过，但区分门控旧 FAIL/WT 见门控报告；无选择性结构依据 | 无需依赖 docking；证据来自已发表实验 |
| 湿实验成本 | 报告基因（TRβ/TRα/空载体/双阳性/干扰对照）成本中低 | 肝细胞 PA/OA+铁死亡读出+ML385/ferrostatin 救援，成本低，本科可完成 |
| 可证伪性 | 三读出全阴性即淘汰 H1（明确、单批次可裁决） | Nrf2 阻断不消除表型即淘汰 H2（ML385/siRNA 双保险） |
| 与原课题兼容 | 兼容原 THRB 申报主线 | 作为支线/机制扩展保存，不偷偷改写主线 |
| 发表潜力 | 若阳性：首报天然 TRβ 调节剂（高风险高回报） | 若阳性：机制重定位+跨疾病迁移的完整故事（中等风险稳妥回报） |

## 四、裁决

- **主假说：H2（Nrf2/ferroptosis × MASH 重定位）**。理由：Moracin N 侧唯一存在的直接实验证据（含因果阻断）全部在此分支；疾病侧链条有独立文献与天然产物先例；最小湿实验成本最低且单批可证伪。
- **备选假说：H1（THRβ structure-based hypothesis）**。理由：保留为纯结构假说；由 WT gate 结果决定其计算证据地位，只有 reporter 实验阳性才可升级。
- **暂不支持假说："Moracin N 为 TRβ 激动剂/亚型选择性调节剂"**。理由：无任何直接证据；口袋保守无选择性依据；旧 N331S 门控 FAIL 保留；该表述在获得实验证据前禁用。

## 五、定位重定义（按第五轮规则）

若 H2 通过肝细胞最小验证，Moracin N 的正式定位为：

> **AIDD 发现并结合既有药理学证据提出的抗 MASH 机制重定位候选**（抗铁死亡/Keap1-Nrf2 分支；桑叶来源，非口服暴露未知）。

该定位作为**支线/后续机制扩展**保存；原大创 THRB 申报主线不改写，只在结题/论文讨论中并列呈现"结构假说未获支持→转向机制重定位"的完整证据路径。

## 六、立即放弃条件

- **放弃 H1**：TRβ 与 TRα reporter 三读出（单药激动/T3 拮抗/T3 亚饱和敏化）全阴性，或 reporter 干扰对照不能排除假阳性。
- **放弃 H2**：肝细胞 PA/OA 模型中表型改善不被 ML385/Nrf2 敲低消除（即 Nrf2 非必要介质），或 ferrostatin-1 救援不能区分铁死亡特异性，或无毒窗口内无任何表型改善。
- **放弃 Moracin N 整体**：H1、H2 同时淘汰，且无新的直接证据出现。

## 七、来源索引

全部 PMID/DOI/URL 见 `外部研究与创新性矩阵.csv` moracin N 行；原始检索响应 `raw/external/moracin_N_*.json`、`logs/external_query_log.jsonl`；天然来源证据见 `候选天然来源审计.csv`（桑叶直接分离：PMID 20118592、31008101、31369850）。
