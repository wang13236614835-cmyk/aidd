# -*- coding: utf-8 -*-
"""
抗MASH天然药物筛选 —— 结果可视化PDF生成
"""

# Historical pipeline: its outputs are invalidated; corrected code lives in 00-当前研究.
raise RuntimeError("此历史入口已停用以保留原数据与结果；请使用仓库00-当前研究中的诊断/修订流程。")
import json, os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import rcParams

# CJK
rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
rcParams["axes.unicode_minus"] = False

D = "D:/zcode-workspace/mash_v2_new"
FIG = f"{D}/results/figures"
os.makedirs(FIG, exist_ok=True)

# ── 色板(与PDF一致) ──
ACCENT = "#4722b7"
ACCENT2 = "#2f97b9"
ACCENT3 = "#e07c3c"
C1, C2, C3 = ACCENT, ACCENT2, ACCENT3

# ===== Chart 1: 靶点证据热力图 =====
def chart_target_heatmap():
    tg = pd.read_csv(f"{D}/results/tables/target_validation_new.csv")
    genes = ["THRB", "FASN", "SCD", "DGAT2", "PPARA", "COL1A1", "TIMP1", "CYP7A1"]
    tg = tg[tg.gene.isin(genes)].set_index("gene").loc[genes]
    fig, axes = plt.subplots(1, 3, figsize=(10, 4), gridspec_kw={"width_ratios": [3, 3, 3]})
    for ax, col, title in zip(axes,
        ["LFC_meta", "spearman_NAS", "direction_consistent"],
        ["Meta log2FC", "Spearman NAS", "方向一致"]):
        if col == "direction_consistent":
            vals = [1 if v == "Y" else 0 for v in tg[col]]
            ax.barh(range(len(genes)), vals, color=[C1 if v else "#ccc" for v in vals])
            ax.set_yticks(range(len(genes))); ax.set_yticklabels(genes, fontsize=9)
            ax.set_xlim(0, 1.2); ax.set_xticks([0.5, 1]); ax.set_xticklabels(["N", "Y"])
        else:
            v = pd.to_numeric(tg[col], errors="coerce").fillna(0).values
            colors = [C1 if x > 0 else C3 for x in v]
            ax.barh(range(len(genes)), v, color=colors)
            ax.set_yticks(range(len(genes))); ax.set_yticklabels(genes, fontsize=9)
            ax.axvline(0, color="gray", lw=0.5)
        ax.set_title(title, fontsize=11, fontweight="bold")
        ax.invert_yaxis()
    plt.suptitle("S1: 靶点病理学验证 (双队列Meta分析)", fontsize=13, fontweight="bold", y=1.02)
    plt.tight_layout()
    plt.savefig(f"{FIG}/chart1_target_validation.png", dpi=200, bbox_inches="tight")
    plt.close()

# ===== Chart 2: QSAR模型性能 =====
def chart_qsar_metrics():
    with open(f"{D}/results/tables/s3_qsar_metrics.json") as f:
        m = json.load(f)
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5))
    targets = ["THRB", "FASN", "SCD1"]
    x = np.arange(len(targets)); w = 0.35
    # 左: R2
    c_r2 = [m[t]["cluster_split"]["R2"] for t in targets]
    r_r2 = [m[t]["random_split"]["R2"] for t in targets]
    axes[0].bar(x - w/2, c_r2, w, label="Butina聚类划分(主)", color=C1)
    axes[0].bar(x + w/2, r_r2, w, label="随机划分(辅)", color=C2)
    axes[0].axhline(0, color="gray", lw=0.5, ls="--")
    axes[0].set_xticks(x); axes[0].set_xticklabels(targets)
    axes[0].set_ylabel("R²"); axes[0].set_title("R² (测试集)", fontweight="bold")
    axes[0].legend(fontsize=8)
    # 右: conformal coverage
    c_cov = [m[t]["cluster_split"]["coverage95"] for t in targets]
    r_cov = [m[t]["random_split"]["coverage95"] for t in targets]
    axes[1].bar(x - w/2, c_cov, w, label="Butina聚类划分", color=C1)
    axes[1].bar(x + w/2, r_cov, w, label="随机划分", color=C2)
    axes[1].axhline(0.95, color="red", lw=0.8, ls="--", label="名义95%")
    axes[1].set_xticks(x); axes[1].set_xticklabels(targets)
    axes[1].set_ylabel("覆盖率"); axes[1].set_title("Conformal 95%覆盖率", fontweight="bold")
    axes[1].legend(fontsize=8, loc="lower right")
    plt.suptitle("S3: QSAR模型评估 (XGB+RF集成)", fontsize=13, fontweight="bold", y=1.02)
    plt.tight_layout()
    plt.savefig(f"{FIG}/chart2_qsar.png", dpi=200, bbox_inches="tight")
    plt.close()

# ===== Chart 3: NP库域适用度分布 + 对接打分分布 =====
def chart_ad_and_docking():
    pred = pd.read_csv(f"{D}/results/tables/np_predictions_new.csv")
    dock = pd.read_csv(f"{D}/results/tables/np_docking_raw_new.csv")
    fig, axes = plt.subplots(1, 3, figsize=(12, 4.5))
    # AD分布
    ad = pred[["THRB_maxTan_train", "FASN_maxTan_train", "SCD1_maxTan_train"]].mean(1)
    axes[0].hist(ad, bins=15, color=C1, edgecolor="white", alpha=0.85)
    axes[0].axvline(0.30, color="red", ls="--", lw=1, label="域内门槛(0.30)")
    axes[0].axvline(0.18, color=ACCENT3, ls="--", lw=1, label="边缘门槛(0.18)")
    axes[0].set_xlabel("平均最大Tanimoto"); axes[0].set_ylabel("化合物数")
    axes[0].set_title("域适用度分布\n(54化合物对训练集)", fontweight="bold", fontsize=10)
    axes[0].legend(fontsize=7)
    # THRβ对接
    thr = dock[dock.target == "THRB"].dropna(subset=["affinity"])
    axes[1].hist(thr.affinity, bins=12, color=C2, edgecolor="white", alpha=0.85)
    axes[1].axvline(-8, color="red", ls="--", lw=1, label="−8 kcal/mol")
    axes[1].set_xlabel("Vina ΔG (kcal/mol)"); axes[1].set_ylabel("次数")
    axes[1].set_title("THRβ对接打分分布\n(n=54)", fontweight="bold", fontsize=10)
    axes[1].legend(fontsize=7)
    # FASN对接
    fa = dock[dock.target == "FASN"].dropna(subset=["affinity"])
    axes[2].hist(fa.affinity, bins=12, color=C3, edgecolor="white", alpha=0.85)
    axes[2].axvline(-8, color="red", ls="--", lw=1, label="−8 kcal/mol")
    axes[2].set_xlabel("Vina ΔG (kcal/mol)"); axes[2].set_ylabel("次数")
    axes[2].set_title("FASN-TE对接打分分布\n(n=54)", fontweight="bold", fontsize=10)
    axes[2].legend(fontsize=7)
    plt.suptitle("S3-S5: 化学空间域适用度与对接打分", fontsize=13, fontweight="bold", y=1.02)
    plt.tight_layout()
    plt.savefig(f"{FIG}/chart3_ad_docking.png", dpi=200, bbox_inches="tight")
    plt.close()

# ===== Chart 4: TOPSIS排名 + 药材优先级 =====
def chart_topsis():
    top = pd.read_csv(f"{D}/results/tables/top20_priority.csv")
    herb = pd.read_csv(f"{D}/results/tables/herb_priority_new.csv")
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.5), gridspec_kw={"width_ratios": [3, 2]})
    # 左: TOP-20 横向条形图
    names = [f"{r['name']}\n({r['herb'].split('(')[0]})" for _, r in top.iloc[::-1].iterrows()]
    vals = top.iloc[::-1]["topsis"].values
    tier_colors = []
    for _, r in top.iloc[::-1].iterrows():
        t = r["confidence_tier"]
        tier_colors.append(C1 if "T1" in str(t) else (C2 if "T2" in str(t) else "#ccc"))
    axes[0].barh(range(len(names)), vals, color=tier_colors, edgecolor="white", height=0.7)
    axes[0].set_yticks(range(len(names))); axes[0].set_yticklabels(names, fontsize=7.5)
    axes[0].set_xlabel("TOPSIS贴近度"); axes[0].set_title("TOP-20化合物优先级", fontweight="bold", fontsize=11)
    axes[0].invert_yaxis()
    # 右: 药材优先级
    herb_sorted = herb.sort_values("priority_score", ascending=True)
    y = range(len(herb_sorted))
    axes[1].barh(y, herb_sorted.priority_score.values, color=C1, edgecolor="white", height=0.6)
    axes[1].set_yticks(y)
    axes[1].set_yticklabels([h.split("(")[0] for h in herb_sorted.herb.values], fontsize=9)
    axes[1].set_xlabel("优先级得分"); axes[1].set_title("药材级优先级排序", fontweight="bold", fontsize=11)
    # 标注证据等级
    for i, (_, r) in enumerate(herb_sorted.iterrows()):
        ev = "A" if r.evidence >= 0.9 else ("B" if r.evidence >= 0.5 else "C+")
        axes[1].text(r.priority_score + 0.01, i, f"证据:{ev}", va="center", fontsize=7, color="#666")
    plt.suptitle("S6: TOPSIS多准则优先级排序", fontsize=13, fontweight="bold", y=1.02)
    plt.tight_layout()
    plt.savefig(f"{FIG}/chart4_topsis.png", dpi=200, bbox_inches="tight")
    plt.close()

# ===== Chart 5: 置信分层饼图 + 置信-排名散点 =====
def chart_confidence():
    pred = pd.read_csv(f"{D}/results/tables/np_topsis_full.csv")
    fig, axes = plt.subplots(1, 2, figsize=(9, 4.5))
    # 饼图
    tier_counts = pred.confidence_tier.value_counts()
    labels = ["T2: 边缘(39)", "T3: 域外(15)"]
    axes[0].pie(tier_counts.values, labels=labels, colors=[C2, "#ccc"],
                autopct="%1.0f%%", startangle=90, textprops={"fontsize": 10})
    axes[0].set_title("置信分层分布\n(无域内化合物)", fontweight="bold", fontsize=11)
    # 散点: AD vs TOPSIS
    ad = pred[["THRB_maxTan_train", "FASN_maxTan_train", "SCD1_maxTan_train"]].mean(1)
    c = [C2 if "T2" in str(t) else "#999" for t in pred.confidence_tier]
    axes[1].scatter(ad, pred.topsis, c=c, s=50, alpha=0.7, edgecolors="white", linewidth=0.5)
    axes[1].axvline(0.30, color="red", ls="--", lw=0.8, alpha=0.6)
    axes[1].axvline(0.18, color=ACCENT3, ls="--", lw=0.8, alpha=0.6)
    axes[1].set_xlabel("平均最大Tanimoto (域适用度)")
    axes[1].set_ylabel("TOPSIS贴近度")
    axes[1].set_title("域适用度 vs 综合优先级", fontweight="bold", fontsize=11)
    # 标注top3
    for _, r in pred.head(3).iterrows():
        axes[1].annotate(r["name"][:12], (ad[r.name], r.topsis),
                        fontsize=7, xytext=(5, 5), textcoords="offset points")
    plt.suptitle("S6: 置信分层与优先级关系", fontsize=13, fontweight="bold", y=1.02)
    plt.tight_layout()
    plt.savefig(f"{FIG}/chart5_confidence.png", dpi=200, bbox_inches="tight")
    plt.close()

# ===== Chart 6: 阳性对照对比 =====
def chart_positive_controls():
    ctrl = pd.read_csv(f"{D}/results/tables/positive_controls_docking_new.csv")
    fig, ax = plt.subplots(figsize=(7, 3.5))
    x = range(len(ctrl))
    colors = [C1 if t == "THRB" else C3 for t in ctrl.target]
    ax.bar(x, ctrl.affinity.abs().values, color=colors, edgecolor="white", width=0.6)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{r['control']}\n({r['target']})" for _, r in ctrl.iterrows()],
                       fontsize=8, rotation=15, ha="right")
    ax.set_ylabel("|ΔG| (kcal/mol)")
    ax.set_title("阳性对照对接验证 (药理排序合理性)", fontweight="bold", fontsize=11)
    # 标注数值
    for i, v in enumerate(ctrl.affinity.values):
        ax.text(i, abs(v) + 0.15, f"{v:.1f}", ha="center", fontsize=8, fontweight="bold")
    plt.tight_layout()
    plt.savefig(f"{FIG}/chart6_controls.png", dpi=200, bbox_inches="tight")
    plt.close()

# 生成所有图表
print("generating charts...")
chart_target_heatmap()
chart_qsar_metrics()
chart_ad_and_docking()
chart_topsis()
chart_confidence()
chart_positive_controls()
print("all charts saved to", FIG)

# ===== ReportLab PDF =====
print("building PDF...")
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Image,
                                 Table, TableStyle, PageBreak, KeepTogether)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.cidfonts import UnicodeCIDFont

# 注册CJK字体
pdfmetrics.registerFont(TTFont("SimHei", r"C:\Windows\Fonts\simhei.ttf"))
pdfmetrics.registerFont(TTFont("SimSun", r"C:\Windows\Fonts\simsun.ttc", subfontIndex=0))

# 色板
ACCENT_C = colors.HexColor("#4722b7")
ACCENT2_C = colors.HexColor("#2f97b9")
ACCENT3_C = colors.HexColor("#e07c3c")
TEXT_C = colors.HexColor("#1d1f20")
MUTED_C = colors.HexColor("#80878c")
BG_C = colors.HexColor("#d8dce0")

W, H = A4
OUT_PDF = f"{D}/mash_v2_results.pdf"

doc = SimpleDocTemplate(OUT_PDF, pagesize=A4,
                        leftMargin=2*cm, rightMargin=2*cm,
                        topMargin=2*cm, bottomMargin=2*cm)
styles = getSampleStyleSheet()
styles.add(ParagraphStyle("TitleCN", fontName="SimHei", fontSize=22, leading=28,
                          alignment=TA_CENTER, textColor=ACCENT_C, spaceAfter=6*mm))
styles.add(ParagraphStyle("SubTitleCN", fontName="SimSun", fontSize=11, leading=15,
                          alignment=TA_CENTER, textColor=MUTED_C, spaceAfter=10*mm))
styles.add(ParagraphStyle("H1", fontName="SimHei", fontSize=16, leading=22,
                          textColor=ACCENT_C, spaceBefore=8*mm, spaceAfter=4*mm))
styles.add(ParagraphStyle("H2", fontName="SimHei", fontSize=13, leading=18,
                          textColor=TEXT_C, spaceBefore=5*mm, spaceAfter=3*mm))
styles.add(ParagraphStyle("Body", fontName="SimSun", fontSize=10, leading=16,
                          textColor=TEXT_C, alignment=TA_JUSTIFY, spaceAfter=3*mm))
styles.add(ParagraphStyle("BodyBold", fontName="SimHei", fontSize=10, leading=16,
                          textColor=TEXT_C, spaceAfter=3*mm))
styles.add(ParagraphStyle("Caption", fontName="SimSun", fontSize=8.5, leading=12,
                          textColor=MUTED_C, alignment=TA_CENTER, spaceAfter=5*mm))
styles.add(ParagraphStyle("Small", fontName="SimSun", fontSize=8, leading=11,
                          textColor=MUTED_C))

def img(path, w=16*cm):
    return Image(path, width=w, height=w * 0.45)

def tbl(data, col_widths=None):
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT_C),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "SimHei"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("FONTNAME", (0, 1), (-1, -1), "SimSun"),
        ("FONTSIZE", (0, 1), (-1, -1), 8.5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BG_C]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#ccc")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return t

story = []
# === 封面 ===
story.append(Spacer(1, 6*cm))
story.append(Paragraph("抗MASH天然药物筛选", styles["TitleCN"]))
story.append(Paragraph("全新独立研究报告", ParagraphStyle("Sub2", parent=styles["SubTitleCN"],
                         fontSize=14, leading=18, textColor=ACCENT2_C)))
story.append(Spacer(1, 8*mm))
story.append(Paragraph("课题: 基于多靶点QSAR与分子对接的天然产物优先级排序", styles["Body"]))
story.append(Paragraph("靶点: THRβ(激动) + FASN(抑制) + SCD1(抑制)", styles["Body"]))
story.append(Paragraph("数据: GSE48452/GSE63067 + ChEMBL + RCSB PDB + PubChem", styles["Body"]))
story.append(Spacer(1, 15*mm))
story.append(Paragraph("2026-08-23 | 独立重做版（不使用旧申报书/旧数据/旧管线）", styles["Caption"]))
story.append(PageBreak())

# === S1: 靶点验证 ===
story.append(Paragraph("S1 病理学靶点确证（新数据集）", styles["H1"]))
story.append(Paragraph("使用GSE48452(n=73,主队列)+GSE63067(n=18,复验)双队列Stouffer加权meta分析，"
    "DNL轴基因FASN/SCD1/DGAT2在MASH肝中跨队列方向一致上调，THRB表达随纤维化分期下降(ρ=−0.397)。", styles["Body"]))
story.append(img(f"{FIG}/chart1_target_validation.png"))
story.append(Paragraph("图1: 双队列meta分析靶点验证。左:meta log2FC(正值=上调)；中:NAS评分Spearman相关；右:跨队列方向一致性。", styles["Caption"]))

# 靶点表
story.append(Paragraph("核心靶点证据表", styles["H2"]))
tg = pd.read_csv(f"{D}/results/tables/target_validation_new.csv")
tdata = [["基因","角色","meta LFC","meta padj","Spearman NAS","方向一致"]]
for _, r in tg[tg.gene.isin(["THRB","FASN","SCD","DGAT2","COL1A1","CYP7A1"])].iterrows():
    tdata.append([str(r.gene), str(r.role).split("(")[0], str(r.LFC_meta),
                  str(r.padj_meta), str(r.spearman_NAS), str(r.direction_consistent)])
story.append(tbl(tdata, col_widths=[55, 80, 55, 55, 70, 55]))
story.append(PageBreak())

# === S3: QSAR ===
story.append(Paragraph("S3 QSAR模型评估", styles["H1"]))
story.append(Paragraph("Morgan指纹(2048bit) + XGBoost/RF等权集成，Butina聚类划分(Tanimoto 0.4)为主评估，"
    "split-conformal 95%区间校准。三靶点聚类划分Spearman均>0.3且RMSE优于均值基线——全部达标。", styles["Body"]))
story.append(img(f"{FIG}/chart2_qsar.png"))
story.append(Paragraph("图2: 左:三靶点R²(聚类vs随机划分)；右:Conformal 95%覆盖率(红色虚线=名义95%)。", styles["Caption"]))

# QSAR指标表
with open(f"{D}/results/tables/s3_qsar_metrics.json") as f:
    qm = json.load(f)
qdata = [["靶点","划分","n(train/val/test)","RMSE","均值基线RMSE","R²","Spearman","Conformal覆盖"]]
for t in ["THRB","FASN","SCD1"]:
    for sp in ["cluster_split","random_split"]:
        d = qm[t][sp]
        qdata.append([t if sp=="cluster_split" else "", sp.replace("_split",""),
                      "/".join(map(str, d["n"])), str(d["RMSE"]),
                      str(d.get("mean_baseline_RMSE","-")), str(d["R2"]),
                      str(d["Spearman"]), str(d["coverage95"])])
story.append(tbl(qdata, col_widths=[40, 55, 65, 42, 52, 40, 52, 60]))
story.append(PageBreak())

# === S4+S5: NP库与对接 ===
story.append(Paragraph("S4-S5 天然产物库与分子对接", styles["H1"]))
story.append(Paragraph("10味全新药材(茵陈/葛根/山楂/泽泻/决明子/桑叶/垂盆草/叶下珠/虎杖/绞股蓝)→"
    "54化合物通过ADMET筛选。THRβ=2J4A(OEF共晶,门控RMSD 0.56Å)、FASN=7MHD(ZEP共晶,门控RMSD 1.62Å)。"
    "阳性对照药理排序合理(sobetirom -11.1 > resmetirom -10.3；orlistat -8.5 > cerulenin -7.8)。", styles["Body"]))
story.append(img(f"{FIG}/chart3_ad_docking.png"))
story.append(Paragraph("图3: 左:54化合物域适用度分布(红线=域内门槛0.30)；中/右:THRβ与FASN对接打分分布。", styles["Caption"]))
story.append(img(f"{FIG}/chart6_controls.png"))
story.append(Paragraph("图4: 阳性对照对接验证。蓝色=THRβ(获批药resmetirom、配体sobetirome)，橙色=FASN(orlistat、cerulenin)。", styles["Caption"]))
story.append(PageBreak())

# === S6: TOPSIS ===
story.append(Paragraph("S6 TOPSIS多准则优先级排序", styles["H1"]))
story.append(Paragraph("7准则加权(THRβ pIC50 0.25 / FASN pIC50 0.15 / SCD1 pIC50 0.10 / "
    "−dG_THRB 0.20 / −dG_FASN 0.10 / 域适用度 0.15 / 药材证据 0.05)。"
    "关键发现: 54个化合物无一达到域内标准(最大Tanimoto 0.17–0.29)——"
    "天然产物在药物化学空间之外是全局事实，所有预测属假设生成级。", styles["Body"]))
story.append(img(f"{FIG}/chart4_topsis.png"))
story.append(Paragraph("图5: 左:TOP-20化合物(蓝=T2边缘, 灰=T3域外)；右:药材级优先级(证据等级标注)。", styles["Caption"]))
story.append(img(f"{FIG}/chart5_confidence.png"))
story.append(Paragraph("图6: 左:置信分层饼图(全部T2/T3，无T1域内)；右:域适用度vs TOPSIS散点。", styles["Caption"]))

# TOP-10表
top = pd.read_csv(f"{D}/results/tables/top20_priority.csv").head(10)
tdata = [["#","化合物","药材","TOPSIS","分层","THRβ pIC50","dG_THRB","dG_FASN"]]
for i, (_, r) in enumerate(top.iterrows(), 1):
    tier = "T2" if "T2" in str(r.confidence_tier) else "T3"
    tdata.append([str(i), str(r["name"])[:16], str(r.herb).split("(")[0][:6],
                  f"{r.topsis:.3f}", tier, f"{r.THRB_pIC50:.2f}",
                  f"{r.dG_THRB:.1f}", f"{r.dG_FASN:.1f}"])
story.append(tbl(tdata, col_widths=[20, 90, 50, 45, 28, 52, 48, 48]))
story.append(PageBreak())

# === 结论 ===
story.append(Paragraph("核心结论", styles["H1"]))
story.append(Paragraph("<b>1. 靶点病理学再确证</b>: DNL轴(FASN/SCD1/DGAT2)在MASH肝中跨两独立队列方向一致上调；"
    "THRB表达随纤维化下降(ρ=−0.397, p=0.001)——抑制DNL+激动THRβ策略有据。", styles["Body"]))
story.append(Paragraph("<b>2. 域外性是全局事实</b>: 54个天然产物对三靶点训练集最大Tanimoto仅0.17–0.29，"
    "无一达到域内标准。换了靶点/数据/算法，天然产物在药物化学空间之外的结论独立成立——"
    "这是本项目最有价值的发现。", styles["Body"]))
story.append(Paragraph("<b>3. 探索性优先清单</b>: 化合物前三 葛根3'-甲氧基大豆黄素(TOPSIS 0.745)、"
    "虎杖儿茶素(0.717)、山楂表儿茶素(0.713)；药材级 葛根≈山楂并列第一(0.864)，"
    "茵陈凭唯一A级临床证据居第三(0.640)。所有候选属假设生成级，需实验验证。", styles["Body"]))
story.append(Spacer(1, 10*mm))
story.append(Paragraph("⚠️ 局限: THRβ IC50混合结合/功能测定；儿茶素类频繁命中倾向；"
    "单构象受体无MD重打分；SCD1降级为仅QSAR(无人源抑制剂共晶)。", styles["Small"]))

# build
doc.build(story)
print("PDF saved:", OUT_PDF)
