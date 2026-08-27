# -*- coding: utf-8 -*-
"""
结果可视化PDF：聚焦排名与研究过程，直观展示。
"""
import json, os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib import rcParams
rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
rcParams["axes.unicode_minus"] = False

D = "D:/zcode-workspace/mash_v2_new"
FIG = f"{D}/results/figures"
os.makedirs(FIG, exist_ok=True)

# 色板
C_MAIN = "#2563EB"    # 蓝
C_SEC  = "#059669"    # 绿
C_ACC  = "#D97706"    # 橙
C_RED  = "#DC2626"    # 红
C_GRAY = "#6B7280"
C_LGRAY= "#F3F4F6"
C_WHITE= "#FFFFFF"

# ==================== 图1: 研究流程一图总览 ====================
def chart_process():
    fig, ax = plt.subplots(figsize=(14, 7))
    ax.set_xlim(0, 14); ax.set_ylim(0, 7)
    ax.axis("off")
    fig.patch.set_facecolor(C_WHITE)

    # 标题
    ax.text(7, 6.6, "抗MASH天然药物筛选 —— 研究流程", ha="center", fontsize=18,
            fontweight="bold", color=C_MAIN)

    # 流程节点
    steps = [
        (1.5, 4.5, "文献调研\n2024-2026 MASH格局\nresmetirom获批\nION224 Lancet", C_MAIN),
        (4.0, 4.5, "靶点确证\nGSE48452+GSE63067\n双队列Meta分析\nFASN↑ SCD1↑ THRB↓", C_SEC),
        (6.5, 4.5, "数据构建\nTHRβ 403条\nFASN 1110条\nSCD1 239条", C_ACC),
        (9.0, 4.5, "QSAR建模\nXGB+RF集成\nButina聚类划分\nR² 0.65-0.84", C_MAIN),
        (11.5, 4.5, "天然产物库\n10味新中药\n54化合物\nPubChem+ADMET", C_SEC),
        (4.0, 1.8, "分子对接\n2J4A(THRβ) 0.56Å\n7MHD(FASN) 1.62Å\n108次批量对接", C_ACC),
        (7.0, 1.8, "TOPSIS排序\n7准则加权\n化合物+药材\n两级优先级", C_MAIN),
        (10.0, 1.8, "结果输出\nTop3化合物\nTop3药材\n全部假设生成级", C_RED),
    ]
    for x, y, text, color in steps:
        box = FancyBboxPatch((x - 1.1, y - 0.7), 2.2, 1.4,
                             boxstyle="round,pad=0.1", facecolor=color, alpha=0.12,
                             edgecolor=color, linewidth=2)
        ax.add_patch(box)
        ax.text(x, y, text, ha="center", va="center", fontsize=8.5,
                fontweight="bold", color=color, linespacing=1.4)

    # 箭头
    arrows = [(2.6, 4.5, 2.9, 0), (5.1, 4.5, 2.9, 0), (7.6, 4.5, 2.9, 0),
              (10.1, 4.5, 1.4, 0),
              (11.5, 3.8, 0, -1.3), (10.4, 1.8, -0.4, 0), (8.5, 1.8, -0.4, 0)]
    for x, y, dx, dy in arrows:
        ax.annotate("", xy=(x+dx, y+dy), xytext=(x, y),
                    arrowprops=dict(arrowstyle="->", color=C_GRAY, lw=2))

    # 底部结论
    ax.text(7, 0.3, "核心发现：54个天然产物全部处于药物化学空间之外（最大Tanimoto 0.17-0.29）—— 所有预测属假设生成级",
            ha="center", fontsize=10, color=C_RED, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.4", facecolor=C_RED, alpha=0.08, edgecolor=C_RED))

    plt.tight_layout()
    plt.savefig(f"{FIG}/result_process.png", dpi=180, bbox_inches="tight", facecolor=C_WHITE)
    plt.close()

# ==================== 图2: 药材排名 ====================
def chart_herb_rank():
    herb = pd.read_csv(f"{D}/results/tables/herb_priority_new.csv")
    herb = herb.sort_values("priority_score", ascending=True)

    fig, ax = plt.subplots(figsize=(10, 5.5))
    fig.patch.set_facecolor(C_WHITE)

    y = range(len(herb))
    colors = []
    for _, r in herb.iterrows():
        if r.evidence >= 0.9: colors.append(C_MAIN)       # A级
        elif r.evidence >= 0.5: colors.append(C_SEC)       # B级
        else: colors.append(C_ACC)                         # C级

    bars = ax.barh(y, herb.priority_score.values, color=colors, edgecolor="white",
                   height=0.6, linewidth=0.5)

    # 标注
    for i, (_, r) in enumerate(herb.iterrows()):
        score = r.priority_score
        ev = "A级" if r.evidence >= 0.9 else ("B级" if r.evidence >= 0.5 else "C+级")
        n = int(r.n_library)
        ax.text(score + 0.01, i, f"{score:.3f}  ({n}个化合物, {ev})",
                va="center", fontsize=9, color="#374151")

    ax.set_yticks(y)
    ax.set_yticklabels([h.split("(")[0] for h in herb.herb.values], fontsize=12, fontweight="bold")
    ax.set_xlabel("优先级得分", fontsize=12)
    ax.set_title("药材级优先级排序", fontsize=16, fontweight="bold", color=C_MAIN, pad=15)
    ax.set_xlim(0, 1.15)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.axvline(0.5, color=C_GRAY, ls="--", lw=0.8, alpha=0.4)

    # 图例
    from matplotlib.patches import Patch
    legend_elements = [Patch(facecolor=C_MAIN, label="A级证据(系统综述级RCT)"),
                       Patch(facecolor=C_SEC, label="B级证据(临床前/小样本临床)"),
                       Patch(facecolor=C_ACC, label="C+级证据(有限证据)")]
    ax.legend(handles=legend_elements, loc="lower right", fontsize=9, framealpha=0.8)

    plt.tight_layout()
    plt.savefig(f"{FIG}/result_herb_rank.png", dpi=180, bbox_inches="tight", facecolor=C_WHITE)
    plt.close()

# ==================== 图3: 化合物Top10 ====================
def chart_compound_top():
    top = pd.read_csv(f"{D}/results/tables/top20_priority.csv").head(10)

    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5), gridspec_kw={"width_ratios": [2, 1.2]})
    fig.patch.set_facecolor(C_WHITE)

    # 左: 横向条形图
    ax = axes[0]
    names = []
    for _, r in top.iloc[::-1].iterrows():
        herb_short = r.herb.split("(")[0][:4]
        names.append(f"{r['name']}  ({herb_short})")
    vals = top.iloc[::-1]["topsis"].values
    colors_bar = [C_MAIN if "T2" in str(t) else C_GRAY for t in top.iloc[::-1].confidence_tier]

    bars = ax.barh(range(len(names)), vals, color=colors_bar, edgecolor="white", height=0.65)
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names, fontsize=10)
    ax.set_xlabel("TOPSIS贴近度", fontsize=11)
    ax.set_title("化合物级TOP-10", fontsize=14, fontweight="bold", color=C_MAIN, pad=10)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_xlim(0, 0.85)

    # 标注数值
    for i, v in enumerate(vals):
        ax.text(v + 0.01, i, f"{v:.3f}", va="center", fontsize=9, fontweight="bold", color="#374151")

    # 右: TOP3详情卡片
    ax2 = axes[1]
    ax2.axis("off")
    ax2.set_xlim(0, 1); ax2.set_ylim(0, 1)

    top3 = top.head(3)
    card_colors = [C_MAIN, C_SEC, C_ACC]
    for i, (_, r) in enumerate(top3.iterrows()):
        y_base = 0.95 - i * 0.33
        # 卡片背景
        rect = FancyBboxPatch((0.02, y_base - 0.28), 0.96, 0.28,
                              boxstyle="round,pad=0.02", facecolor=card_colors[i], alpha=0.08,
                              edgecolor=card_colors[i], linewidth=1.5)
        ax2.add_patch(rect)
        # 排名
        ax2.text(0.08, y_base - 0.05, f"#{i+1}", fontsize=20, fontweight="bold",
                color=card_colors[i], ha="center", va="center")
        # 化合物名
        ax2.text(0.18, y_base - 0.05, str(r["name"])[:20], fontsize=11,
                fontweight="bold", color="#1F2937", va="center")
        # 药材
        herb = r.herb.split("(")[0]
        ax2.text(0.18, y_base - 0.15, f"来源: {herb}", fontsize=9, color=C_GRAY, va="center")
        # 数值
        ax2.text(0.85, y_base - 0.05, f"TOPSIS={r.topsis:.3f}", fontsize=10,
                fontweight="bold", color=card_colors[i], ha="right", va="center")
        ax2.text(0.85, y_base - 0.15, f"THRβ={r.THRB_pIC50:.1f}  FASN dG={r.dG_FASN:.1f}",
                fontsize=8.5, color=C_GRAY, ha="right", va="center")
        tier = "边缘" if "T2" in str(r.confidence_tier) else "域外"
        ax2.text(0.85, y_base - 0.22, f"置信: T2({tier})", fontsize=8,
                color=C_GRAY, ha="right", va="center")

    plt.tight_layout()
    plt.savefig(f"{FIG}/result_compound_top.png", dpi=180, bbox_inches="tight", facecolor=C_WHITE)
    plt.close()

# ==================== 图4: 关键靶点证据 ====================
def chart_target_evidence():
    tg = pd.read_csv(f"{D}/results/tables/target_validation_new.csv")
    targets = ["THRB", "FASN", "SCD", "DGAT2"]
    tg = tg[tg.gene.isin(targets)].copy()

    fig, axes = plt.subplots(1, 3, figsize=(13, 4.5))
    fig.patch.set_facecolor(C_WHITE)

    # 左: meta log2FC
    ax = axes[0]
    lfc = tg.LFC_meta.values.astype(float)
    gene_labels = [f"{r.gene}\n({r.role.split('(')[0]})" for _, r in tg.iterrows()]
    colors_bar = [C_SEC if x > 0 else C_RED for x in lfc]
    bars = ax.bar(range(len(targets)), lfc, color=colors_bar, edgecolor="white", width=0.6)
    ax.set_xticks(range(len(targets)))
    ax.set_xticklabels(gene_labels, fontsize=10, fontweight="bold")
    ax.axhline(0, color=C_GRAY, lw=0.8)
    ax.set_ylabel("log2FC (MASH vs 正常)")
    ax.set_title("转录组变化方向", fontsize=12, fontweight="bold", color=C_MAIN)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    for i, v in enumerate(lfc):
        ax.text(i, v + (0.05 if v > 0 else -0.1), f"{v:+.2f}", ha="center",
                fontsize=10, fontweight="bold", color=colors_bar[i])
    # 标注含义
    ax.text(0.5, 0.02, "↑上调=靶点活性升高 → 应抑制\n↓下调=受体表达下降 → 应激动",
            transform=ax.transAxes, fontsize=8, color=C_GRAY, ha="center", va="bottom")

    # 中: NAS Spearman
    ax = axes[1]
    rho = pd.to_numeric(tg.spearman_NAS, errors="coerce").fillna(0).values
    colors_rho = [C_SEC if x > 0 else C_RED for x in rho]
    ax.bar(range(len(targets)), rho, color=colors_rho, edgecolor="white", width=0.6)
    ax.set_xticks(range(len(targets)))
    ax.set_xticklabels(gene_labels, fontsize=10, fontweight="bold")
    ax.axhline(0, color=C_GRAY, lw=0.8)
    ax.set_ylabel("Spearman ρ")
    ax.set_title("与NAS活动度相关", fontsize=12, fontweight="bold", color=C_MAIN)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    for i, v in enumerate(rho):
        if abs(v) > 0.1:
            ax.text(i, v + (0.02 if v > 0 else -0.04), f"{v:.3f}", ha="center",
                    fontsize=9, fontweight="bold", color=colors_rho[i])

    # 右: 治疗策略
    ax = axes[2]
    ax.axis("off")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.text(0.5, 0.95, "治疗策略验证", ha="center", fontsize=14, fontweight="bold", color=C_MAIN)

    strategies = [
        ("THRβ激动", "表达↓(ρ=-0.397)\nresmetirom已获批", C_MAIN),
        ("FASN抑制", "表达↑(meta +0.55)\nTVB-2640临床2b期", C_SEC),
        ("SCD1抑制", "表达↑(meta +0.95)\nDNL限速酶", C_SEC),
    ]
    for i, (name, desc, color) in enumerate(strategies):
        y_base = 0.75 - i * 0.28
        rect = FancyBboxPatch((0.05, y_base - 0.22), 0.9, 0.22,
                              boxstyle="round,pad=0.02", facecolor=color, alpha=0.08,
                              edgecolor=color, linewidth=1.5)
        ax.add_patch(rect)
        ax.text(0.12, y_base - 0.05, name, fontsize=12, fontweight="bold",
                color=color, va="center")
        ax.text(0.12, y_base - 0.15, desc, fontsize=9, color=C_GRAY, va="center",
                linespacing=1.3)

    plt.tight_layout()
    plt.savefig(f"{FIG}/result_target.png", dpi=180, bbox_inches="tight", facecolor=C_WHITE)
    plt.close()

# ==================== 图5: QSAR性能 ====================
def chart_qsar():
    with open(f"{D}/results/tables/s3_qsar_metrics.json") as f:
        m = json.load(f)

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5))
    fig.patch.set_facecolor(C_WHITE)

    targets = ["THRβ", "FASN", "SCD1"]
    x = np.arange(len(targets)); w = 0.32

    # 左: R² + Spearman
    ax = axes[0]
    r2_c = [m[t]["cluster_split"]["R2"] for t in ["THRB","FASN","SCD1"]]
    r2_r = [m[t]["random_split"]["R2"] for t in ["THRB","FASN","SCD1"]]
    sp_c = [m[t]["cluster_split"]["Spearman"] for t in ["THRB","FASN","SCD1"]]

    bars1 = ax.bar(x - w/2, r2_c, w, label="R² (聚类划分)", color=C_MAIN, alpha=0.85)
    bars2 = ax.bar(x + w/2, sp_c, w, label="Spearman ρ", color=C_SEC, alpha=0.85)
    ax.axhline(0, color=C_GRAY, lw=0.5)
    ax.set_xticks(x); ax.set_xticklabels(targets, fontsize=12, fontweight="bold")
    ax.set_ylabel("指标值")
    ax.set_title("模型预测能力", fontsize=14, fontweight="bold", color=C_MAIN, pad=10)
    ax.legend(fontsize=9, loc="upper right")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    for i, (r, s) in enumerate(zip(r2_c, sp_c)):
        ax.text(i - w/2, r + 0.02, f"{r:.2f}", ha="center", fontsize=9, fontweight="bold", color=C_MAIN)
        ax.text(i + w/2, s + 0.02, f"{s:.2f}", ha="center", fontsize=9, fontweight="bold", color=C_SEC)

    # 右: RMSE vs 基线
    ax = axes[1]
    rmse_c = [m[t]["cluster_split"]["RMSE"] for t in ["THRB","FASN","SCD1"]]
    rmse_b = [m[t]["cluster_split"]["mean_baseline_RMSE"] for t in ["THRB","FASN","SCD1"]]
    bars1 = ax.bar(x - w/2, rmse_c, w, label="集成模型RMSE", color=C_MAIN, alpha=0.85)
    bars2 = ax.bar(x + w/2, rmse_b, w, label="均值基线RMSE", color=C_GRAY, alpha=0.5)
    ax.set_xticks(x); ax.set_xticklabels(targets, fontsize=12, fontweight="bold")
    ax.set_ylabel("RMSE (pIC50)")
    ax.set_title("模型 vs 基线", fontsize=14, fontweight="bold", color=C_MAIN, pad=10)
    ax.legend(fontsize=9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    for i, (m_val, b_val) in enumerate(zip(rmse_c, rmse_b)):
        ax.text(i - w/2, m_val + 0.02, f"{m_val:.2f}", ha="center", fontsize=9, fontweight="bold", color=C_MAIN)
        ax.text(i + w/2, b_val + 0.02, f"{b_val:.2f}", ha="center", fontsize=9, color=C_GRAY)

    plt.tight_layout()
    plt.savefig(f"{FIG}/result_qsar.png", dpi=180, bbox_inches="tight", facecolor=C_WHITE)
    plt.close()

# ==================== 图6: 对接结果 ====================
def chart_docking():
    dock = pd.read_csv(f"{D}/results/tables/np_docking_raw_new.csv")
    ctrl = pd.read_csv(f"{D}/results/tables/positive_controls_docking_new.csv")

    fig, axes = plt.subplots(1, 2, figsize=(11, 5))
    fig.patch.set_facecolor(C_WHITE)

    # 左: 阳性对照
    ax = axes[0]
    ctrl_data = ctrl.dropna(subset=["affinity"])
    x = range(len(ctrl_data))
    colors_ctrl = [C_MAIN if t == "THRB" else C_ACC for t in ctrl_data.target]
    bars = ax.bar(x, ctrl_data.affinity.abs().values, color=colors_ctrl, edgecolor="white", width=0.55)
    ax.set_xticks(x)
    labels = [f"{r['control']}\n({r['target']})" for _, r in ctrl_data.iterrows()]
    ax.set_xticklabels(labels, fontsize=9, rotation=15, ha="right")
    ax.set_ylabel("|ΔG| (kcal/mol)")
    ax.set_title("阳性对照药理排序", fontsize=14, fontweight="bold", color=C_MAIN, pad=10)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    for i, v in enumerate(ctrl_data.affinity.values):
        ax.text(i, abs(v) + 0.2, f"{v:.1f}", ha="center", fontsize=10, fontweight="bold")

    # 右: NP对接分布散点(按药材着色)
    ax = axes[1]
    thr = dock[dock.target == "THRB"][["herb", "name", "affinity"]].rename(columns={"affinity": "dG_THRB"})
    fas = dock[dock.target == "FASN"][["herb", "name", "affinity"]].rename(columns={"affinity": "dG_FASN"})
    merged = thr.merge(fas, on=["herb", "name"])

    herb_colors = {}
    palette = [C_MAIN, C_SEC, C_ACC, C_RED, "#8B5CF6", "#EC4899", "#06B6D4",
               "#84CC16", "#F59E0B", "#6366F1"]
    for i, h in enumerate(merged.herb.unique()):
        herb_colors[h] = palette[i % len(palette)]

    for herb, g in merged.groupby("herb"):
        short = herb.split("(")[0][:4]
        ax.scatter(g.dG_THRB.abs(), g.dG_FASN.abs(), c=herb_colors[herb],
                  s=60, alpha=0.75, edgecolors="white", linewidth=0.5, label=short)

    ax.set_xlabel("|ΔG| THRβ (kcal/mol)", fontsize=10)
    ax.set_ylabel("|ΔG| FASN (kcal/mol)", fontsize=10)
    ax.set_title("54化合物双靶点对接", fontsize=14, fontweight="bold", color=C_MAIN, pad=10)
    ax.legend(fontsize=7.5, ncol=2, loc="lower right")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    plt.savefig(f"{FIG}/result_docking.png", dpi=180, bbox_inches="tight", facecolor=C_WHITE)
    plt.close()

# 生成全部图表
print("生成图表...")
chart_process()
chart_herb_rank()
chart_compound_top()
chart_target_evidence()
chart_qsar()
chart_docking()
print("全部图表已保存")

# ==================== ReportLab PDF ====================
print("生成PDF...")
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Image,
                                 PageBreak, KeepTogether)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

pdfmetrics.registerFont(TTFont("SimHei", r"C:\Windows\Fonts\simhei.ttf"))
pdfmetrics.registerFont(TTFont("SimSun", r"C:\Windows\Fonts\simsun.ttc", subfontIndex=0))

C1 = colors.HexColor("#2563EB")
C2 = colors.HexColor("#059669")
C3 = colors.HexColor("#D97706")
CR = colors.HexColor("#DC2626")
CG = colors.HexColor("#6B7280")

W, H = A4
doc = SimpleDocTemplate(f"{D}/mash_v2_结果可视化.pdf", pagesize=A4,
                        leftMargin=1.8*cm, rightMargin=1.8*cm,
                        topMargin=1.5*cm, bottomMargin=1.5*cm)
styles = getSampleStyleSheet()
styles.add(ParagraphStyle("TitleCN", fontName="SimHei", fontSize=24, leading=30,
                          alignment=TA_CENTER, textColor=C1, spaceAfter=3*mm))
styles.add(ParagraphStyle("Sub", fontName="SimSun", fontSize=11, leading=14,
                          alignment=TA_CENTER, textColor=CG, spaceAfter=8*mm))
styles.add(ParagraphStyle("H1", fontName="SimHei", fontSize=16, leading=20,
                          textColor=C1, spaceBefore=5*mm, spaceAfter=3*mm))
styles.add(ParagraphStyle("H2", fontName="SimHei", fontSize=13, leading=17,
                          textColor=colors.HexColor("#1F2937"), spaceBefore=3*mm, spaceAfter=2*mm))
styles.add(ParagraphStyle("Body", fontName="SimSun", fontSize=10.5, leading=16,
                          textColor=colors.HexColor("#374151"), spaceAfter=2*mm))
styles.add(ParagraphStyle("Highlight", fontName="SimHei", fontSize=11, leading=16,
                          textColor=CR, spaceAfter=3*mm))
styles.add(ParagraphStyle("Caption", fontName="SimSun", fontSize=9, leading=12,
                          textColor=CG, alignment=TA_CENTER, spaceAfter=4*mm))

def img(path, w=17*cm):
    return Image(path, width=w, height=w * 0.42)

story = []

# P1 封面
story.append(Spacer(1, 5*cm))
story.append(Paragraph("抗MASH天然药物筛选", styles["TitleCN"]))
story.append(Paragraph("结果可视化报告", ParagraphStyle("t2", parent=styles["TitleCN"],
                         fontSize=16, textColor=C2)))
story.append(Spacer(1, 1*cm))
story.append(Paragraph("THRβ(激动) + FASN(抑制) + SCD1(抑制) | 54化合物 × 9味药材", styles["Body"]))
story.append(Paragraph("数据: GSE48452 / ChEMBL / RCSB PDB / PubChem | 2026-08-23", styles["Body"]))
story.append(PageBreak())

# P2 研究流程
story.append(Paragraph("一、研究流程总览", styles["H1"]))
story.append(Paragraph("从文献调研到最终排名，共7个阶段，全部数据当日从公共数据库重新获取。", styles["Body"]))
story.append(Image(f"{FIG}/result_process.png", width=17*cm, height=8.5*cm))
story.append(PageBreak())

# P3 靶点证据
story.append(Paragraph("二、靶点病理学证据（新数据独立验证）", styles["H1"]))
story.append(Paragraph("使用GSE48452(n=73)+GSE63067(n=18)双队列Meta分析，DNL轴基因在MASH肝中方向一致上调，"
    "THRB表达随纤维化下降(ρ=−0.397, p=0.001)。", styles["Body"]))
story.append(Image(f"{FIG}/result_target.png", width=17*cm, height=6*cm))
story.append(Paragraph("图: 左-转录组变化方向(绿=上调,红=下调)；中-NAS活动度Spearman相关；右-治疗策略验证。", styles["Caption"]))

# P4 QSAR
story.append(Paragraph("三、QSAR模型性能", styles["H1"]))
story.append(Paragraph("XGBoost+RandomForest集成，Butina聚类划分评估(模拟发现新骨架的场景)。"
    "三靶点Spearman均>0.75，RMSE全部优于均值基线。", styles["Body"]))
story.append(Image(f"{FIG}/result_qsar.png", width=17*cm, height=6.5*cm))
story.append(PageBreak())

# P5 对接
story.append(Paragraph("四、分子对接结果", styles["H1"]))
story.append(Paragraph("THRβ使用2J4A(sobetirome共晶，门控RMSD 0.56Å)；FASN使用7MHD(ZEP共晶，门控RMSD 1.62Å)。"
    "阳性对照药理排序合理。", styles["Body"]))
story.append(Image(f"{FIG}/result_docking.png", width=17*cm, height=7*cm))
story.append(Paragraph("图: 左-阳性对照(蓝=THRβ,橙=FASN)；右-54化合物双靶点对接散点(按药材着色)。", styles["Caption"]))
story.append(PageBreak())

# P6 化合物排名
story.append(Paragraph("五、化合物TOP-10优先级", styles["H1"]))
story.append(Paragraph("TOPSIS 7准则加权排序。所有化合物处于T2边缘域(无域内化合物)——预测为假设生成级。", styles["Body"]))
story.append(Image(f"{FIG}/result_compound_top.png", width=17*cm, height=7*cm))
story.append(Paragraph("图: 左-TOP-10排名；右-前三详情卡片(蓝色T2边缘域)。", styles["Caption"]))
story.append(PageBreak())

# P7 药材排名
story.append(Paragraph("六、药材级优先级排序", styles["H1"]))
story.append(Paragraph("基于TOP-20占据数(60%权重)与临床证据等级(40%权重)。", styles["Body"]))
story.append(Image(f"{FIG}/result_herb_rank.png", width=16*cm, height=8*cm))
story.append(Paragraph("蓝色=A级证据(系统综述级RCT)；绿色=B级(临床前/小样本)；橙色=C+级(有限证据)。", styles["Caption"]))
story.append(Spacer(1, 8*mm))

# 结论
story.append(Paragraph("核心结论", styles["H1"]))
story.append(Paragraph("1. 靶点策略有据: DNL轴(FASN/SCD1/DGAT2)在MASH肝中跨两独立队列一致上调，"
    "THRB随纤维化下降——'抑制DNL+激动THRβ'策略有独立数据支撑。", styles["Body"]))
story.append(Paragraph("2. 天然产物全部处于药物化学空间之外: 54个化合物对训练集最大Tanimoto仅0.17-0.29，"
    "无一达到域内标准——这是本项目最有价值的独立发现。", styles["Highlight"]))
story.append(Paragraph("3. 探索性优先清单(假设生成级): "
    "化合物前三 葛根3'-甲氧基大豆黄素(TOPSIS 0.745)、虎杖儿茶素(0.717)、山楂表儿茶素(0.713)；"
    "药材级 葛根≈山楂并列第一(0.864)，茵陈凭唯一A级临床证据居第三。", styles["Body"]))

doc.build(story)
print("PDF已保存:", f"{D}/mash_v2_结果可视化.pdf")
