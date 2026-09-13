# Moracin N — MCE 供应商页面字段提取

- 检索日期: 2026-09-12 (第六轮)
- 访问方式: 站点直连 WebFetch 返回 403/412（与第四/五轮采购墙一致），改经页面渲染通道获取字段；价格来自 medchemexpress.cn 搜索快照
- URL: https://www.medchemexpress.com/moracin-n.html / https://www.medchemexpress.cn/moracin-n.html
- 本文件为页面渲染提取的字段记录，非整页存档；下单前需人工复核

## 商品与身份字段（页面核实）

| 字段 | 值 |
|---|---|
| 目录号 | HY-N11849 |
| CAS | 135248-05-4 |
| 分子式 / MW | C19H18O4 / 310.34 |
| 外观 | Solid, white to off-white |
| 纯度 | 98.74%（批间可选至 99.74%） |
| SMILES（页面版，异戊烯基 E/Z 未指定） | OC1=CC(C2=CC3=C(C=C(C(C/C=C(C)\C)=C3)O)O2)=CC(O)=C1 |
| PubChem CID | 641376（第五轮 PubChem raw 核实；canonical SMILES CC(=CCC1=C(C=C2C(=C1)C=C(O2)C3=CC(=CC(=C3)O)O)C)C） |
| InChIKey | WBSCSIABHGPAMC-UHFFFAOYSA-N |

## 溶解 / 储运（页面核实）

| 字段 | 值 |
|---|---|
| DMSO 溶解 | 100 mg/mL（322.39 mM，需超声） |
| 水溶性 | 页面未给出（clogP 4.73，水相直接溶解不可假设） |
| 粉末保存 | -20°C，避光，3 年 |
| 溶液保存 | -80°C 6 个月 / -20°C 1 个月 |
| 运输 | 室温（美国本土） |
| 体内配方可参考 | 10% DMSO + 90% SBE-β-CD，≥2.5 mg/mL（本项目暂不需要） |

## 价格（登录墙外仅部分可见，来源=搜索快照）

| 渠道 | 规格 | 价格 | 状态 | 来源层级 |
|---|---|---|---|---|
| MCE 中国站 (HY-N11849) | 1 mg | ¥2320 | In-stock | 搜索快照（medchemexpress.cn/moracin-n.html 标题下价格表） |
| MCE 中国站 | 5 mg | 询价 | 现货 | 同上 |
| MCE 国际站 | 1/5/10 mg | 登录后可见 | In-stock | 页面渲染（价格登录墙） |
| GlpBio (GC71917) | 1 mg | $72 ≈ ¥520 | In-stock | 搜索快照（glpbio.com/moracin-n.html） |
| GlpBio | 10 mM × 25 μL DMSO 样品液 | 免费样品通道（页面明示随单提供 25 μL 样品溶液） | — | 页面渲染 |
| AbMole | 未核实到规格价格 | — | 页面未取得 | 搜索命中存在，标记 unverified |

## 对本项目可用的实验浓度证据（MCE 页面"Bioactivity"节，均有 PMID 溯源）

1. HT22 海马神经元 erastin 模型: EC50 < 0.5 μM（神经保护；PMID 34281775）
2. A549/PC9/HeLa-GFP-LC3/L929-tfLC3: 10-45 μM，6-24 h，激活溶酶体功能/自噬（PMID 32477104 等）
3. 肿瘤系 A2780/A549/BGC-823/Bel-7402/HCT-8: 96 h MTT IC50 > 10 μg/mL（≈ >32 μM，基本无直接细胞毒性；PMID 25461329）
4. 小鼠 MCAO 模型: 20 mg/kg/day 脑室给药 + ML385 阻断（PMID 40972263）——第五轮已收

## 采购风险记录

- 稀有化合物，供应商少、单价高（MCE ¥2320/mg 显著超出本科预算舒适区；GlpBio $72/1mg 为可行价）
- GlpBio 页面直连 403，下单流程与到货周期未验证 → 标记采购风险中-高
- MCE 中国站有"同一机构一年内可免费申领三个不同产品试用装"政策 → 优先申请试用装（25 μL×10 mM = 77.6 μg，足够 Gate1+Gate2 预试）
- 异戊烯基双键 E/Z 几何未在两个来源中立体指定 → 收货后以 COA + LC-MS/1H-NMR 与 CID 641376 比对确认
