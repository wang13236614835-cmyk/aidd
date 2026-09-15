# -*- coding: utf-8 -*-
"""用标准 CSV quoting 生成第五轮方向资格矩阵。"""
from __future__ import annotations

import csv
from pathlib import Path

OUT = Path(__file__).parent
COLUMNS = [
    "Target/Task", "direction_role", "data_sample_size", "endpoint_consistency", "assay_count",
    "activity_distribution", "duplicate_leakage_risk", "scaffold_diversity",
    "external_validation_feasibility", "MASH_link", "clinical_pharmacology_evidence",
    "natural_product_value", "modeling_value", "data_quality_score", "endpoint_consistency_score",
    "sample_size_score", "scaffold_diversity_score", "external_validation_score", "mash_link_score",
    "natural_product_value_score", "modeling_value_score", "current_status", "overall_decision",
    "source_refs", "notes",
]


def row(name, role, sample, endpoint, assays, activity, leak, scaffold, external, mash, clinical, natural, modeling, scores, status, decision, source, notes):
    score_fields = ["data_quality_score", "endpoint_consistency_score", "sample_size_score", "scaffold_diversity_score", "external_validation_score", "mash_link_score", "natural_product_value_score", "modeling_value_score"]
    return dict(zip(COLUMNS, [name, role, sample, endpoint, assays, activity, leak, scaffold, external, mash, clinical, natural, modeling, *scores, status, decision, source, notes]))

ROWS = [
    row("Moracin N–NRF2/ferroptosis肝细胞机制验证", "Primary", "0个本项目肝细胞结果", "表型/机制实验线单独设计，不混QSAR endpoint", "不适用", "暂无MASH肝细胞活性分布；HT22 EC50<0.50μM不可迁移", "身份已审计；探针/光谱/聚集干扰待M0", "不适用", "计算external不适用；关键是实测肝细胞桥接", "高（MASH脂毒性/铁死亡疾病链）", "中高（HT22功能+ML385 pharmacological involvement；无肝/PK）", "高", "中（不做伪QSAR；按预注册Gate）", [2, 0, 0, 0, 0, 2, 2, 0], "实验启动资格/未执行", "GO（实验启动资格；非候选放行）", "qualification_v1/MASTER_EVIDENCE_MATRIX.csv;advancement_round_20260913/MoracinN_*", "唯一当前主发现方向；物料未到；siNRF2前不升因果等级"),
    row("FASN assay-aware T1/方法学线", "Methodology", "1652条/1139分子/51 assays", "IC50 1630/Ki20/Kd2；canonical单IC50", "n=51（共享矩阵）", "pActivity中位约6.996；canonical 96分子单系列", "canonical exact=0；evaluable external overlap=0；mirror overlap=89（排除）；near duplicate=82/96（series confinement）", "canonical 39 scaffold；全量assay混杂", "外部105/3 assays已有但Ridge R²=0.180且分assay全负", "高（DNL/FASN；denifanstat Phase 2b背景）", "中高（临床/病理支持；不等于NP）", "中（天然产物直接人源同assay点约0–5；NP54全OOD）", "中（canonical Ridge成立；跨assay失败；GNN不增益）", [2, 0, 1, 1, 1, 2, 0, 1], "T1 FAIL/canonical local方法学线", "FAIL（跨assay扩展门；保留canonical local方法线）", "qualification_round_20260913/FASN_10seed_scaffold_results.csv;fifth_round_direction_exploration_20260915/FASN_T1_*", "FASN原始资产保留；需第二可比pair才能重开T1；不做NP54定量扩展/GNN"),
    row("FXR evidence-anchor/Formononetin依赖性桥接 + Biochanin A QC", "Secondary", "当前LanthaScreen 324分子；全量4252条/3338分子", "当前模型单EC50/单LanthaScreen；全量EC50/IC50/Kd混杂", "290 assays全量；正式模型1 assay", "当前模型pActivity中位约8.25；内部locked test", "54 NP全OOD；无真正external", "内部scaffold可行；external未完成", "中（胆汁酸/脂质/炎症）", "中高（Formononetin/Biochanin A已有结合/功能；OCA临床失败警示）", "低中（文献拥挤；不做NP新发现）", "中（内部RF可作assay reference；不作NP排名）", "中（仅同一LanthaScreen assay reference；不作NP排名）", [1, 1, 2, 1, 0, 1, 1, 1], "证据锚点/QC", "CONDITIONAL（仅assay-specific evidence anchor）", "candidate_decision_20260910/fxr_locked_model;final_strategy_round_20260912/THRB_FXR_ACC最终定位.md", "Formononetin问题是FXR依赖性残留；Biochanin A只作QC；不做NP54新发现"),
    row("THRβ reporter/counter-screen", "Reserve", "6839条/5669分子；single-protein IC50约329记录/225分子", "Potency/IC50/EC50/Ki/Kd及功能方向混杂", "85 assays/50 documents；paired TRα/β仅39对", "pActivity约7.33（single-protein IC50）", "历史cluster R²=.843不可外推；WT docking AUC=.472", "需先冻结reporter方向/平台；当前无独立external", "高（临床THRβ/MASH）", "高（resmetirom；不能迁移给NP）", "中高（若有真实reporter阳性则有价值；当前直接证据薄）", "低（不做docking排序）", "低中（只在真实reporter平台可用时有建模价值）", [1, 1, 0, 0, 2, 1, 1, 1], "临床锚点/Reserve reporter线", "RESERVE（需reporter平台+TRα counter-screen）", "candidate_decision_20260910/chembl_thrb_data.csv;fifth_round_20260912/WT_gate_results.md", "需要T3阳性、TRα counter-screen、报告干扰和活力控制"),
    row("ACC1/ACC2 DNL比较附录", "Reserve", "ACC1 697条/555分子；ACC2 4222条/4003分子", "IC50主导但cell/single-protein/构建体混杂", "ACC1 49/ACC2 62 assays", "ACC1中位约7.01；ACC2中位约6.68", "多记录分子；跨亚型混合会造成标签错误", "ACC1约250/ACC2约1302 scaffold（估计）", "无当前external；需分别冻结亚型", "中（DNL背景）", "中（firsocostat早期信号；高TG限制；meta padj弱）", "低（项目无直接NP链）", "低中（历史ACC2 R²=.514仅随机split）", [1, 0, 2, 2, 0, 1, 0, 1], "附录/暂停", "RESERVE（仅作FASN/DNL竞争参照；不合并）", "final_strategy_round_20260912/THRB_FXR_ACC最终定位.md;seventh_round_20260912/FXR_ACC降级审计.md", "不合并ACC1/2；不采购/不启动专用实验"),
    row("SCD1历史QSAR/Reserve", "Reserve", "239分子", "全部IC50但assay/document lineage不完整", "未可靠冻结", "pIC50 4.36–8.40", "清洗表层级有限；需重建provenance", "约125 scaffold；NN中位约.77", "无真正external", "中高（v2两队列方向一致上调；padj=.158）", "中（DNL病理支持；无当前药理闭环）", "低中", "低（历史cluster R²=.651不可直接外推）", [1, 1, 1, 1, 0, 1, 1, 1], "历史QSAR-only/暂停", "HISTORICAL/RESERVE", "03-课题-MASH研究-v2/results/tables/s3_qsar_metrics.json;target_validation_new.csv", "只有补齐assay lineage后才可重资格化"),
    row("DGAT2历史比较/Reserve", "Reserve", "约261分子", "主要IC50；provenance不足", "未可靠冻结", "pAct约4.39–9.60", "重复/assay谱系未完成", "未可靠冻结", "无当前external", "中（meta LFC=.769/padj=.0629）", "中高（临床/药理背景；项目闭环缺失）", "低中", "低中（历史R²=.600）", [1, 0, 1, 1, 0, 1, 1, 0], "历史比较/暂停", "HISTORICAL/RESERVE", "02-课题-MASH研究-v1/data/v2;03-课题-MASH研究-v2/target_validation_new.csv", "不把历史QSAR成绩转成当前候选资格"),
    row("KEAP1/Nrf2直接结合模型", "Rejected", "615条/460分子/111 assays", "PPI/肽竞争/Ki/Kd/IC50/EC50混杂", "111 assays/49 docs", "活性分布不可同质解释", "PPI与结合记录混杂；无法用统一标签处理", "未可靠冻结", "无当前external", "高（NRF2通路背景）", "中（疾病链有价值；Moracin N无直接KEAP1结合）", "中（机制背景而非NP靶点筛选）", "低（不训练NRF2/GPX4伪GNN）", [2, 0, 0, 0, 0, 2, 1, 0], "机制背景/不建主模型", "REJECTED for model", "final_strategy_round_20260912/最终双轴战略矩阵.csv;seventh_round_20260912/靶点数据可建模性审计.csv", "只能写NRF2 involvement/hypothesis，不能写直接KEAP1配体"),
    row("3′-methoxydaidzein当前创新候选", "Rejected", "候选级无统一当前模型标签", "FXR/TR/MASH直接终点缺失", "不适用", "NaV1.7/1.8/1.3约181/397/505nM；NaV1.5约2.63μM", "当前无资格泄漏审计支持", "不适用", "当前MASH关联不足", "NaV本体电生理off-target已报告", "表型尚不支持", "低", "低（无统一当前模型标签）", [0, 0, 0, 0, 0, 0, 1, 0], "当前D/Rejected", "REJECTED for current innovation role", "fifth_round_20260912/外部研究与创新性矩阵.csv;PMID31262454", "只有独立FXR/TR阳性且完成NaV收益风险评估才可复议"),
]

with (OUT / "direction_exploration_matrix.csv").open("w", encoding="utf-8-sig", newline="") as fh:
    writer = csv.DictWriter(fh, fieldnames=COLUMNS)
    writer.writeheader()
    writer.writerows(ROWS)
print(f"wrote {len(ROWS)} rows")
