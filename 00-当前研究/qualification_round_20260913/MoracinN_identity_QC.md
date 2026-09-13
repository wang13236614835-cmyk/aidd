# Moracin N 身份 QC

**日期：2026-09-13｜来源：第五/六轮原始审计（PubChem API raw + 供应商页面快照），本轮复核无冲突**

## 一、身份链（全部已核实，多库一致）

| 字段 | 值 | 核实方式 | 状态 |
|---|---|---|---|
| 规范名 | Moracin N | PubChem PUG API | ✅ |
| CAS | 135248-05-4 | MCE 页面 + PubChem raw 交叉 | ✅ |
| 分子式 / MW | C19H18O4 / 310.34（RDKit 310.35 一致） | MCE 页面 + RDKit 2026.03.3 | ✅ |
| InChIKey | WBSCSIABHGPAMC-UHFFFAOYSA-N | PubChem API | ✅ |
| PubChem CID | 641376 | PubChem API | ✅ |
| canonical SMILES | CC(=CCC1=C(C=C2C(=C1)C=C(O2)C3=CC(=CC(=C3)O)O)C)C | PubChem API；与库内 np_library 54 表一致 | ✅ |
| ChEMBL | CHEMBL465881（结构登记，无 TR/FXR 活性记录） | ChEMBL REST | ✅ |
| 外观 | 白色至类白色固体 | MCE 页面 | 页面核实 |
| 立体化学 | 无手性中心；异戊烯基双键 E/Z 未在两来源指定 | PubChem/MCE SMILES 对比（均无立体标记） | 已识别-低风险 |

**结构/命名歧义：无。**唯一开口是 E/Z 几何未指定 → 收货后须 COA+LC-MS/NMR 复核（已列入 Gate M0 采购条款）。

## 二、理化与可操作性

| 项 | 值 | 层级 |
|---|---|---|
| DMSO 溶解 | 100 mg/mL（322.39 mM，需超声） | MCE 页面实测 |
| cLogP / TPSA / HBD / HBA / RotB | 4.73 / 73.83 / 3 / 4 / 3 | RDKit 预测 |
| PAINS | 无命中（FilterCatalog A/B/C） | RDKit 预测 |
| 粉末保存 | −20°C 避光 3 年 | 供应商页面 |
| 溶液保存 | −80°C 6 个月 / −20°C 1 个月；10 mM DMSO 分装 | 供应商页面 |
| 工作浓度上限依据 | 30 μM（cLogP 4.73 靠上限+培养基预稀释控制沉淀） | 第六轮剂量设计 |

## 三、已知浓度窗（全部文献值，直接引用）

| 体系 | 浓度 | 方向 | 来源 |
|---|---|---|---|
| HT22 erastin 神经元 | EC50 < 0.5 μM | 保护 | PMID 34281775 |
| MCAO 小鼠 | 20 mg/kg/day 脑室内×3d | 保护（ML385 可阻断） | PMID 40972263 |
| A549/PC9 等肿瘤系 | 10–45 μM, 6–24 h | **促** ROS/凋亡（NAC 可逆） | PMID 32477104 |
| 五肿瘤系 96h MTT | IC50 > 10 μg/mL（≈>32 μM） | 低直接毒性 | PMID 25461329 |
| 无关酶 | tyrosinase 0.92 μM；lipase 29.7 μM；aromatase 31.1 μM；α-glucosidase 2.76 μM | 背景 | BindingDB/BioAssay |

→ 剂量窗 0.1–30 μM（第六轮 7 点设计）下界锚神经元亚微摩尔活性、上界锚肿瘤系毒性窗，成立。

## 四、供应商与预算资格

| 供应商 | 货号/规格 | 价格 | 状态 |
|---|---|---|---|
| GlpBio | GC71917, 1 mg | $72≈¥520 | 快照核实（直连 403，下单前邮件确认） |
| MCE 中国站 | HY-N11849, 1 mg | ¥2320（纯度 98.74–99.74%，COA 提供） | 页面/快照核实 |
| MCE 试用装 | HY-N11849, 10 mM×25 μL | 免费（机构年 3 名额，77.6 μg 够 Gate1） | 政策核实-需申请 |

用量：Gate1 全量 ≈0.27 mg；1 mg 覆盖全部 Gate 0–3。**物料资格：≥2 家可供应，无阻断。**

## 五、身份 QC 结论

**PASS——无身份歧义、无溶解阻断、有剂量窗锚点、有可执行供应链。**风险仅两项且已有预案：E/Z 待 COA 复核（Gate M0 条款）；稀有化合物采购周期（先试用装/邮件确认）。
