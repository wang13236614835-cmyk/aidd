# -*- coding: utf-8 -*-
"""第六轮 CSV 交付物生成器：MoracinN_实验物料审计 / 候选采购清单 / 最小实验预算
数据来源见 raw/supplier_*；价格状态列明 页面核实/快照/常规市价/试用装政策。
"""
import csv, json, hashlib
from pathlib import Path

BASE = Path("D:/zcode-workspace/aidd-repo-work/00-当前研究/sixth_round_20260912")
D = "2026-09-12"

def write_csv(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)

# ---------- 1. MoracinN_实验物料审计.csv ----------
h1 = ["类别","字段","值","来源/依据","核实方式","核实日期","状态"]
r1 = [
    ["身份","规范名","Moracin N","第五轮 PubChem raw (CID 641376)","PubChem PUG API","2026-09-10","已核实"],
    ["身份","CAS","135248-05-4","MCE 页面 + 第五轮 PubChem raw","页面渲染+API","2026-09-12","已核实"],
    ["身份","分子式 / MW","C19H18O4 / 310.34","MCE 页面；RDKit 310.35 计算值一致","页面渲染+RDKit 2026.03.3","2026-09-12","已核实"],
    ["身份","InChIKey","WBSCSIABHGPAMC-UHFFFAOYSA-N","第五轮 PubChem raw","PubChem PUG API","2026-09-10","已核实"],
    ["身份","PubChem CID","641376","第五轮 PubChem raw","PubChem PUG API","2026-09-10","已核实"],
    ["身份","canonical SMILES","CC(=CCC1=C(C=C2C(=C1)C=C(O2)C3=CC(=CC(=C3)O)O)C)C","第五轮 PubChem raw","PubChem PUG API","2026-09-10","已核实"],
    ["身份","外观","白色至类白色固体","MCE 页面","页面渲染",D,"页面核实"],
    ["身份","立体化学风险","无手性中心；异戊烯基双键 E/Z 几何未在 PubChem/MCE 立体指定（两来源 SMILES 均无立体标记）","PubChem/MCE SMILES 对比","交叉核对",D,"已识别-低风险"],
    ["溶解储运","DMSO 溶解","100 mg/mL（322.39 mM，需超声）","MCE 页面溶解表","页面渲染",D,"页面核实"],
    ["溶解储运","水溶性","未提供；clogP 4.73（RDKit）→ 不可假设水相直接溶解","MCE 页面未列水溶性","RDKit 预测",D,"预测值"],
    ["溶解储运","粉末保存","-20°C 避光 3 年（MCE）；GlpBio 同 -20°C 避光","两供应商页面","页面渲染",D,"页面核实"],
    ["溶解储运","溶液保存","-80°C 6 个月 / -20°C 1 个月；建议 10 mM DMSO 母液分装避光","MCE 页面","页面渲染",D,"页面核实"],
    ["已知浓度","神经保护(HT22 erastin)","EC50 < 0.5 μM","PMID 34281775（MCE 页面引用）","文献",D,"文献值"],
    ["已知浓度","肿瘤系自噬/凋亡(A549/PC9/HeLa-GFP-LC3/L929-tfLC3)","10-45 μM, 6-24 h","PMID 32477104 等（MCE Bioactivity 节）","文献",D,"文献值"],
    ["已知浓度","肿瘤系直接毒性(A2780/A549/BGC-823/Bel-7402/HCT-8, 96h MTT)","IC50 > 10 μg/mL（≈>32 μM）","PMID 25461329（MCE 页面引用）","文献",D,"文献值"],
    ["已知浓度","体内(MCAO 小鼠)","20 mg/kg/day 脑室给药","PMID 40972263","文献","2026-09-10","文献值"],
    ["供应商","首选：GlpBio","GC71917, 1 mg, $72≈¥520, In-stock, 提供 COA；随单提供 10 mM×25 μL 样品溶液","glpbio.com/moracin-n.html","搜索快照+页面渲染（直连 403）",D,"快照核实-需下单确认"],
    ["供应商","备选1：MCE 中国站","HY-N11849, 1 mg ¥2320 In-stock / 5 mg 询价现货, 纯度 98.74%（批间至 99.74%）, COA 提供","medchemexpress.cn/moracin-n.html","页面渲染+搜索快照（直连 412）",D,"页面/快照核实"],
    ["供应商","备选2：MCE 免费试用装","同一机构一年内可免费申领 3 个不同产品试用装（10 mM×25 μL = 77.6 μg）","MCE 中国站试用装政策","页面渲染",D,"政策核实-需申请"],
    ["供应商","其他","AbMole 有售（规格价格未取得）；TargetMol moracin N 页面未取得（有 moracin M/O）","搜索命中","搜索",D,"unverified"],
    ["采购风险","风险评级","中-高：稀有化合物、供应商少；GlpBio 直连 403 到货周期未验证；MCE 单价 ¥2320/mg 显著高于预算舒适区；E/Z 未指定需收货 COA+LC-MS/NMR 复核","本表综合","综合评估",D,"已评估"],
    ["用量核算","全项目需求","Gate1 全量(7 浓度×3 生物学重复)≈0.27 mg；Gate2/3 窄浓度≈0.15 mg；1 mg 足够全部门控；试用装 77.6 μg 仅够 Gate1+部分 Gate2，过关后需正式采购","本方案剂量设计","计算",D,"已计算"],
]
write_csv(BASE/"MoracinN_实验物料审计.csv", h1, r1)

# ---------- 2. 候选采购清单.csv ----------
h2 = ["序号","物料","供应商","货号/复核方式","规格","单价(元)","价格状态","库存","采购阶段","方案档位","用途","备注/替代"]
r2 = [
    ["1","Moracin N","GlpBio","GC71917","1 mg","520","快照($72, 直连403)","In-stock(快照)","Gate1 前","标准/扩展","主候选","下单前邮件确认价格运费；备选 MCE HY-N11849 ¥2320/mg"],
    ["2","Moracin N 免费试用装","MCE 中国站","HY-N11849","10 mM×25 μL","0","试用装政策","需申请","Gate1 前","最低","主候选","77.6 μg 够 Gate1；机构一年 3 个名额"],
    ["3","Formononetin","MCE 中国站","HY-N0183","5 mg","299","页面核实","In-stock","FMN 支线前","标准","FXR 依赖性","HepG2 24h IC50 60.5 μM（PMID 24974349）"],
    ["4","Formononetin 免费试用装","MCE 中国站","HY-N0183","10 mM×25 μL","0","试用装政策","需申请","FMN 支线前","最低","FXR 依赖性","与 2/6 竞争 3 个名额"],
    ["5","ML385","MCE 中国站","HY-100523（勿用 HY-100622 旧记）","1 mg","300","页面核实","In-stock","Gate3 前（Gate2 过关才下单）","标准/扩展","Nrf2 阻断","1.955 μmol 足够；纯度 99.96%"],
    ["6","ML385 免费试用装","MCE 中国站","HY-100523","10 mM×25 μL","0","试用装政策","需申请","Gate3 前","最低","Nrf2 阻断","—"],
    ["7","Ferrostatin-1","GlpBio","下单按 CAS 347174-05-4 复核","5 mg","235","镜像页面($32)","In-stock(快照)","Gate2 前","最低/标准/扩展","铁死亡阳性对照","比 Selleck($147/5mg) 省≈¥800；EC50 60 nM"],
    ["8","棕榈酸 PA","Sigma P0500 或国产","—","25 g","300","常规市价","常规","Gate1 前","全档","模型诱导","国产可降至约 ¥80"],
    ["9","油酸 OA","Sigma O1008 或国产","—","25 mL","400","常规市价","常规","Gate1 前","全档","模型诱导","—"],
    ["10","无脂肪酸 BSA","Solarbio/碧云天（Sigma A8806 备选）","—","25 g","450","常规市价","常规","Gate1 前","全档","FFA 载体偶联","Sigma 备选约 ¥900"],
    ["11","CCK-8 试剂盒","Biosharp BA00208 / 碧云天 C0038","—","500 T","400","常规市价","常规","Gate1 前","全档","细胞活力","—"],
    ["12","油红 O 染液","Solarbio G1262 或等效","—","100 mL","150","常规市价","常规","Gate1 前","全档","脂滴染色","—"],
    ["13","TG（甘油三酯）试剂盒","普利莱 E1013 / Applygen","—","96 T","500","常规市价","常规","Gate1 前","全档","Gate1 主端点","微孔板法"],
    ["14","GSH 试剂盒","碧云天 S0053","—","100 T","450","常规市价","常规","Gate2 前（Gate1 过关才下单）","全档","Gate2 读数","—"],
    ["15","DCFH-DA（ROS 探针）","碧云天 S0033","—","500 T","400","常规市价","常规","Gate2 前（同上）","全档","Gate2 读数","—"],
    ["16","96 孔板/枪头/离心管耗材","国产","—","20 板+耗材套装","400","常规市价","常规","全程","全档","通用","平台可部分抵扣"],
    ["17","Guggulsterone (Z/E)","Ambeed","下单按 CAS 复核","5 mg","441","快照","咨询","FMN 支线","扩展","FXR 药理学阻断","弱拮抗 IC50 24 μM；平台 siFXR 优先则不买"],
    ["18","C11-BODIPY 581/591","Thermo","D3861","1 mg","1580","第五轮快照","—","Gate2（可选）","扩展","脂质过氧化","流式平台确认可用后才买"],
    ["19","Biochanin A","平台存量优先，无则 MCE","下单按 CAS 491-80-5 复核","5-10 mg","250","常规市价","—","Gate1 同板","扩展（平台存量则 ¥0）","板级弱活性参照","非阳性对照；Fer-1 承担系统对照"],
    ["20","Moracin N 续购保险","GlpBio/MCE","同序号 1","1 mg","520","快照","In-stock(快照)","Gate2 过关后","扩展","余量保险","—"],
]
write_csv(BASE/"候选采购清单.csv", h2, r2)

# ---------- 3. 最小实验预算.csv（分期+分档，脚本计算小计保证算术一致） ----------
G1 = {"棕榈酸 PA":300,"油酸 OA":400,"无脂肪酸 BSA":450,"CCK-8":400,"油红O":150,"TG 试剂盒":500,"96孔板等耗材":400}
G2 = {"GSH 试剂盒":450,"DCFH-DA":400}
G3 = {"ML385 1mg":300,"Ferrostatin-1 5mg":235}
CMP_G1 = {"Moracin N 1mg (GlpBio)":520,"Formononetin 5mg (MCE)":299}
CMP_G2 = {}
CMP_G3 = {}

def block(tier, rows_out, compounds, g1x=G1, g2x=G2, g3x=G3, extra=None):
    s1 = s2 = s3 = 0
    for name, v in compounds.get("G1", {}).items():
        rows_out.append([tier,"Gate1 阶段下单",name,v,"化合物"])
        s1 += v
    for name, v in g1x.items():
        rows_out.append([tier,"Gate1 阶段下单",name,v,"试剂/耗材"])
        s1 += v
    rows_out.append([tier,"Gate1 小计","",s1,""])
    for name, v in compounds.get("G2", {}).items():
        rows_out.append([tier,"Gate2 阶段下单",name,v,"化合物"]); s2 += v
    for name, v in g2x.items():
        rows_out.append([tier,"Gate2 阶段下单",name,v,"试剂/耗材"]); s2 += v
    rows_out.append([tier,"Gate2 小计","",s2,""])
    for name, v in compounds.get("G3", {}).items():
        rows_out.append([tier,"Gate3 阶段下单",name,v,"化合物"]); s3 += v
    for name, v in g3x.items():
        rows_out.append([tier,"Gate3 阶段下单",name,v,"试剂/耗材"]); s3 += v
    rows_out.append([tier,"Gate3 小计","",s3,""])
    total = s1+s2+s3
    if extra:
        es = 0
        for name, v in extra.items():
            rows_out.append([tier,"扩展追加",name,v,"试剂/化合物"]); es += v
        rows_out.append([tier,"扩展小计","",es,""])
        total += es
    rows_out.append([tier,"合计",f"{s1}+{s2}+{s3}"+(f"+{es}" if extra else ""),total,""])
    return total

rows3 = []
# 最低档：三个 MCE 免费试用装（moracin N / formononetin / ML385）全部申请成功假设
t_min = block("最低档（试用装杠杆全成功）", rows3,
    compounds={"G1":{}, "G2":{}, "G3":{}},
    g1x=G1, g2x=G2, g3x={"Ferrostatin-1 5mg":235})
# 标准档：化合物全采购（不含 guggulsterone/C11）
t_std = block("标准档（全采购）", rows3,
    compounds={"G1":CMP_G1, "G2":CMP_G2, "G3":CMP_G3},
    g1x=G1, g2x=G2, g3x=G3)
# 扩展档
t_ext = block("扩展档", rows3,
    compounds={"G1":dict(CMP_G1), "G2":{}, "G3":{}},
    g1x=G1, g2x=G2, g3x=G3,
    extra={"Guggulsterone 5mg (Ambeed)":441,"C11-BODIPY 1mg (Thermo D3861)":1580,
           "Moracin N 续购 1mg":520,"抗体/试剂余量 (GPX4 等)":1200,"运费/汇率缓冲":300})
write_csv(BASE/"最小实验预算.csv", ["档位","阶段","物料","金额(元)","类别"], rows3)

summary = {
    "generated": "2026-09-12",
    "tiers_total_cny": {"最低档(试用装全成功)": t_min, "标准档(全采购)": t_std, "扩展档": t_ext},
    "standard_tier_lever": "若 MCE 试用装成功申领 formononetin（¥299），标准档降至 %d 元" % (t_std-299),
    "max_sunk_cost_if_gate1_fails": 520+299+sum(G1.values()),
    "stage_totals_standard": {"Gate1": 520+299+sum(G1.values()), "Gate2": sum(G2.values()), "Gate3": sum(G3.values())},
}
(BASE/"derived/budget_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(summary, ensure_ascii=False, indent=2))
