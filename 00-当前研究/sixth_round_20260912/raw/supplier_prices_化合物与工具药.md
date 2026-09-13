# 第六轮化合物/工具药价格证据（页面或快照核实，2026-09-12）

所有条目注明来源层级：页面渲染（webReader）/ 搜索快照（TokenHub）/ 不可得（blocked）。下单前均需人工复核价格与货号。

## ML385（Nrf2 抑制剂，Gate3 因果裁决用）

- 供应商: MCE 中国站，**货号 HY-100523**（注意：本项目早前笔记中记为 HY-100622，是错的，本轮页面核实更正）
- CAS 846557-71-9，纯度 99.96%，NRF2 抑制 IC50 = 1.9 μM，文献常用浓度 5-10 μM（MCE 页面引用）
- DMSO 溶解 25 mg/mL（48.87 mM），粉末 -20°C 3 年
- 价格（页面渲染，MCE 中国站，免运费）: 10 mM×1mL(DMSO) ¥844；**1 mg ¥300；5 mg ¥750；10 mg ¥1300；25 mg ¥2400**，均 In-stock
- 交叉参考: Selleck/Fisher 渠道 5mg ≈ $169（第五轮快照）；科学网博客转 MCE 国际站货号同为 HY-100523、纯度 99.96%
- **采购决策: 1 mg ¥300 即足够**（1.955 μmol ≈ 10 μM×100 μL×~2000 孔次）

## Formononetin 刺芒柄花素（FMN，FXR 依赖性单问题用）

- 供应商: MCE 中国站，**货号 HY-N0183**（注意：早前笔记记为 HY-N0177，本轮页面核实更正）
- CAS 485-72-3，纯度 98.99%，MW 268.26，DMSO ≥35 mg/mL（130.47 mM）
- 价格（页面渲染，MCE 中国站）: **5 mg ¥299；10 mg ¥448；10 mM×1 mL ¥500；50 mg ¥900；100 mg ¥1200**，In-stock
- 关键毒性锚点（页面引用）: HepG2 24 h MTT IC50 = 60.5 μM（PMID 24974349）→ 直接支撑本项目 FMN 浓度上限 ≤50 μM
- FGFR2 IC50 ~4.31 μM（页面标注）→ 与本项目无关，不作为机制依据

## Ferrostatin-1（Fer-1，铁死亡阳性对照）

- 供应商: GlpBio（韩文镜像站页面渲染，产品同源）: **5 mg US$32 ≈ ¥235；25 mg $120；50 mg $227；100 mg $411**，均现货
- 交叉参考: Selleck 5 mg $147（第五轮快照）→ GlpBio 显著更便宜
- 活性锚点: HT-1080 铁死亡 EC50 = 60 nM（Selleck datasheet）；常用工作浓度 1 μM
- 货号未在镜像页核实到 → 下单时以 Ferrostatin-1/CAS 347174-05-4 复核

## Guggulsterone（FXR 拮抗剂，仅扩展档）

- (-)-(E)-Guggulsterone: FXR 拮抗 IC50 = 24.06 μM（MCE 页面）——**弱拮抗剂**，工作浓度需 10-25 μM 且需自带毒性对照
- Z/E 混合物 MCE 中国站: 10 mg ¥1100；25 mg ¥1760（快照）
- **Ambeed（更便宜）: 5 mg ¥441；10 mg ¥770；25 mg ¥1232（快照）**
- 若导师平台已有 FXR siRNA 或 Z-Guggulsterone，优先用平台存量，不新增采购

## C11-BODIPY 581/591（脂质过氧化探针，仅扩展档）

- Thermo D3861: $218.65/1 mg ≈ ¥1580（第五轮快照，本轮未变）
- CST 95978: $253/1 mg（第五轮快照）
- 决策: 标准档用 DCFH-DA + GSH + GPX4 替代；C11 仅在流式平台确认可用后采购

## Moracin N 汇总（详见 supplier_mce_moracinN_页面提取.md）

- 首选: GlpBio 1 mg $72≈¥520（快照，In-stock）
- 备选: MCE CN HY-N11849 1 mg ¥2320 现货（快照）
- 杠杆: MCE 机构免费试用装（25 μL×10 mM）；GlpBio 随单 25 μL 样品液

## 检索边界（不写成"没有"）

- glpbio.com/moracin-n.html 与 medchemexpress.cn/moracin-n.html 站点直连 WebFetch 分别 403/412 → 经渲染通道/快照获取，整页价格表未全部验证
- TargetMol 有 moracin M（25 mg $220）/moracin O 页面，moracin N 页面本轮未取得 → 记录为未核实，不虚构
- Sigma-Aldrich 恰诺菲 formononetin ₹9,560.01（印度站快照，规格未标）→ 仅作存在性证据
