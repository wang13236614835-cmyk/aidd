# -*- coding: utf-8 -*-
"""Build fifth-round developability audit CSV (2026-09-12).

Every value carries a provenance tag: predicted (tool+version) / experimental /
literature-measured (PMID) / not assessed / blocked. No mixing.
"""
import csv, json
from pathlib import Path

ROOT = Path(r"D:\zcode-workspace\aidd-repo-work\00-当前研究\fifth_round_20260912")
props = json.loads((ROOT/"derived"/"rdkit_props_pains.json").read_text(encoding="utf-8"))
K3 = "3'-methoxydaidzein"  # key containing an apostrophe
out = ROOT / "候选可开发性审计.csv"

HEAD = ["compound","MW","cLogP","TPSA","HBD","HBA","rotatable bonds","PAINS","aggregation risk",
        "reactive groups","assay interference","solubility","ADMET-AI","CYP","hERG","PPB","BBB",
        "oral exposure","known PK","standard availability","supplier","purity","approximate cost",
        "sources and caveats"]

FLAV_POLYPH = "类风险（多酚/黄酮）：氧化还原循环、自身吸光/荧光、胶体聚集、报告基因非靶抑制——本体未实测，须过 Gate 0 无细胞前置"
ISO_POLYPH = "类风险（黄酮醇多酚）+ 本项目 Week1 干扰综述结论：本体干扰阈值未测；聚集/浊度须先排除（isorhamnetin_interference_literature_review.md）"
NAVISSUE = "已证实 off-target：NaV1.7/1.8/1.3 亚微摩尔功能抑制（本体电生理，PMID 31262454）；另 NaV1.5 2.63 μM"

def P(name, k):
    return f"{props[name][k]} [predicted: RDKit 2026.03.3]"

def PN(name):
    return f"{props[name]['PAINS_alert']} [predicted: RDKit FilterCatalog PAINS A/B/C]"

rows = [
["moracin N", P("moracin N","rdkit_MW"), P("moracin N","clogP"), P("moracin N","TPSA"),
 P("moracin N","HBD"), P("moracin N","HBA"), P("moracin N","rotb"), PN("moracin N"),
 "not assessed [需无细胞浊度/DLS/离心上清实测；苯并呋喃酚类为聚集关注类]",
 "none flagged [predicted: RDKit PAINS；无共价弹头/醌/迈克尔受体警报]",
 FLAV_POLYPH + "；抗氧化类读数（DCFH/DPPP/CCK-8）假阳性风险高",
 "not assessed [无实测溶解度；桑叶天然含量 mg/100 g 级为含量而非溶解数据]",
 "not run [本轮未运行；环境不可复现时不得补猜]",
 "not assessed", "not assessed", "not assessed",
 "not assessed [cLogP4.73 提示中等]",
 "unknown [无口服数据；唯一体内证据为脑室内给药 20 mg/kg/day，PMID 40972263]",
 "无本体 PK 文献 [moracin C 有小鼠 PK（PMID 33498088），不可迁移]",
 "standard available [市场常识：标准品供应商可检索]",
 "blocked [供应商页面核查受验证码/403/登录限制；批次与货号未核验，见 procurement_blocker_log]",
 "blocked [纯度/批次未核验，不虚构]",
 "blocked [无有效公开报价；'便宜'表述冻结]",
 "PubChem XLogP 4.8 与 RDKit 4.73 一致；全部为预测层，实测项零"],

["formononetin", P("formononetin","rdkit_MW"), P("formononetin","clogP"), P("formononetin","TPSA"),
 P("formononetin","HBD"), P("formononetin","HBA"), P("formononetin","rotb"), PN("formononetin"),
 "not assessed [异黄酮苷元类风险低-中；仍需 Gate 0]",
 "none flagged [predicted；无反应性警报]",
 "类风险（异黄酮）：弱；主要关注荧光素酶体系直接效应与代谢（CYP 底物文献背景未系统核对）",
 "not assessed [文献有异黄酮低溶普遍描述但无本体数值]",
 "not run", "not systematically assessed [红车轴草人体研究提示 CYP 相互作用方向不一，本轮未提取]",
 "not assessed", "not assessed", "not assessed",
 "literature-mixed [红车轴草人体营养研究存在（ClinicalTrials 4 项），单体口服暴露数值未提取]",
 "literature: 大鼠肝组织检出结合态/苷元（见矩阵）——非治疗暴露，不作 PK 结论",
 "standard available", "blocked", "blocked", "blocked",
 "MW268/cLogP3.17/TPSA59.7 预测层；类药空间内；PK/临床暴露未闭环"],

[K3, P(K3,"rdkit_MW"), P(K3,"clogP"), P(K3,"TPSA"),
 P(K3,"HBD"), P(K3,"HBA"), P(K3,"rotb"), PN(K3),
 "not assessed", "none flagged [predicted]",
 NAVISSUE + "——任何细胞实验须带 NaV 表达对照或限浓度解释",
 "not assessed", "not run",
 "not assessed [NaV 论文未测 CYP]",
 "not assessed [NaV1.5 IC50 2.63 μM（PMID 31262454）为心脏通道离靶信号；hERG 未测]",
 "not assessed", "not assessed",
 "literature-measured [小鼠 50 mg/kg po 120 min 血浆≈1.83±0.25 μM，t1/2≈10 h（PMID 31262454）]",
 "literature: 单篇小鼠 PK；0.26–6.5 mg/kg ip 镇痛有效；800 mg/kg ip 非致死（同文）",
 "standard available [TBM/MCE/Ambeed/ApexBT 页面可见，含量级 5 mg 装]",
 "blocked [同上]", "blocked", "blocked",
 "理化预测干净≠可开发：决定性风险是已证实亚微摩尔 NaV 活性（见 历史错误与修正记录 E6）"],

["isorhamnetin", P("isorhamnetin","rdkit_MW"), P("isorhamnetin","clogP"), P("isorhamnetin","TPSA"),
 P("isorhamnetin","HBD"), P("isorhamnetin","HBA"), P("isorhamnetin","rotb"), PN("isorhamnetin"),
 "not assessed [黄酮醇多酚为经典胶体聚集关注类——须实测]",
 "none flagged [predicted；邻苯二酚结构提示中度氧化还原活性，非共价反应]",
 ISO_POLYPH,
 "not assessed [多酚低溶普遍；需 DMSO/介质梯度实测]",
 "not run", "not assessed", "not assessed", "not assessed",
 "not assessed [cLogP2.29 低]",
 "literature-mixed [槲皮素/异鼠李素口服低暴露文献背景广泛，本体数值未提取；NASH 小鼠 50 mg/kg po 有效（PMID 31700054）]",
 "literature: 50 mg/kg po 小鼠疾病模型有效剂量（同上）",
 "standard available", "blocked", "blocked", "blocked",
 "TPSA120/HBA7 偏高——口服暴露与聚集双风险；干扰门是第一关卡"],

["biochanin A", P("biochanin A","rdkit_MW"), P("biochanin A","clogP"), P("biochanin A","TPSA"),
 P("biochanin A","HBD"), P("biochanin A","HBA"), P("biochanin A","rotb"), PN("biochanin A"),
 "not assessed [同异黄酮类]", "none flagged [predicted]",
 "类风险（异黄酮）：弱；报告基因体系仍须空载体对照",
 "not assessed", "not run", "not assessed", "not assessed", "not assessed",
 "not assessed",
 "literature-mixed [DIO 小鼠膳食 0.05%×12 周有效（PMID 27145114）——膳食给药暴露，非灌胃 PK]",
 "literature: 同上；无治疗剂量 PK 数值",
 "standard available", "blocked", "blocked", "blocked",
 "定位=FXR 阳性对照：可开发性审计仅服务于对照批次质量"],
]

with out.open("w", newline="", encoding="utf-8-sig") as f:
    w=csv.writer(f); w.writerow(HEAD); w.writerows(rows)
print("rows:",len(rows),"->",out)
