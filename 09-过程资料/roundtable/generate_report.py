# -*- coding: utf-8 -*-
"""圆桌评估报告 PDF 正文生成（ReportLab）——封面由 html2poster.js 单独渲染后合并。"""
import os
import sys
import hashlib

PDF_SKILL_DIR = r"C:\Users\user\.zcode\cli\plugins\cache\zcode-plugins-official\document-skills\0.1.0\skills\pdf"
sys.path.insert(0, os.path.join(PDF_SKILL_DIR, "scripts"))

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
    KeepTogether, CondPageBreak, HRFlowable,
)
from reportlab.platypus.tableofcontents import TableOfContents

# ---------------- fonts ----------------
pdfmetrics.registerFont(TTFont("Microsoft YaHei", "C:/Windows/Fonts/msyh.ttc", subfontIndex=0))
pdfmetrics.registerFont(TTFont("Microsoft YaHei-Bold", "C:/Windows/Fonts/msyhbd.ttc", subfontIndex=0))
pdfmetrics.registerFont(TTFont("SimHei", "C:/Windows/Fonts/simhei.ttf"))
pdfmetrics.registerFont(TTFont("Times New Roman", "C:/Windows/Fonts/times.ttf"))
pdfmetrics.registerFont(TTFont("Times New Roman-Bold", "C:/Windows/Fonts/timesbd.ttf"))
registerFontFamily("Microsoft YaHei", normal="Microsoft YaHei", bold="Microsoft YaHei-Bold",
                   italic="Microsoft YaHei", boldItalic="Microsoft YaHei-Bold")
registerFontFamily("SimHei", normal="SimHei", bold="SimHei",
                   italic="SimHei", boldItalic="SimHei")
registerFontFamily("Times New Roman", normal="Times New Roman", bold="Times New Roman-Bold",
                   italic="Times New Roman", boldItalic="Times New Roman-Bold")
try:
    from pdf import install_font_fallback
    install_font_fallback()
except Exception as e:
    print("font fallback skipped:", e)

# ---------------- palette (palette.cascade, seed 42) ----------------
PAGE_BG = colors.HexColor("#f5f5f4")
CARD_BG = colors.HexColor("#ebeae8")
TABLE_STRIPE = colors.HexColor("#ededeb")
HEADER_FILL = colors.HexColor("#4e4732")
BORDER = colors.HexColor("#c5bfac")
ACCENT = colors.HexColor("#1f7692")
TEXT_PRIMARY = colors.HexColor("#151513")
TEXT_MUTED = colors.HexColor("#7e7c74")
SEM_SUCCESS = colors.HexColor("#529067")
SEM_WARNING = colors.HexColor("#8c7443")
SEM_ERROR = colors.HexColor("#a25b54")

# ---------------- doc & styles ----------------
OUT = os.path.dirname(os.path.abspath(__file__))
BODY_PDF = os.path.join(OUT, "report_body.pdf")
MARGIN = 2.0 * cm
PAGE_W, PAGE_H = A4
AVAIL_W = PAGE_W - 2 * MARGIN

DOC_TITLE = "大创项目整体研发思路三方圆桌评估与修正报告"

st_h1 = ParagraphStyle("H1", fontName="Microsoft YaHei-Bold", fontSize=17, leading=24,
                       textColor=TEXT_PRIMARY, spaceBefore=18, spaceAfter=8, wordWrap="CJK")
st_h2 = ParagraphStyle("H2", fontName="Microsoft YaHei-Bold", fontSize=13, leading=19,
                       textColor=HEADER_FILL, spaceBefore=14, spaceAfter=6, wordWrap="CJK")
st_body = ParagraphStyle("Body", fontName="SimHei", fontSize=10.5, leading=17,
                         textColor=TEXT_PRIMARY, alignment=TA_LEFT, spaceAfter=8,
                         wordWrap="CJK", firstLineIndent=21)
st_body_ni = ParagraphStyle("BodyNI", parent=st_body, firstLineIndent=0)
st_bullet = ParagraphStyle("Bullet", fontName="SimHei", fontSize=10.5, leading=16.5,
                           textColor=TEXT_PRIMARY, leftIndent=14, spaceAfter=5, wordWrap="CJK")
st_quote = ParagraphStyle("Quote", fontName="Microsoft YaHei", fontSize=11.5, leading=19,
                          textColor=HEADER_FILL, leftIndent=10, rightIndent=10, wordWrap="CJK")
st_th = ParagraphStyle("TH", fontName="Microsoft YaHei-Bold", fontSize=9.5, leading=13,
                       textColor=colors.white, alignment=TA_CENTER, wordWrap="CJK")
st_td = ParagraphStyle("TD", fontName="SimHei", fontSize=9, leading=13,
                       textColor=TEXT_PRIMARY, alignment=TA_LEFT, wordWrap="CJK")
st_td_c = ParagraphStyle("TDC", parent=st_td, alignment=TA_CENTER)
st_cap = ParagraphStyle("Cap", fontName="Microsoft YaHei", fontSize=8.5, leading=12,
                        textColor=TEXT_MUTED, alignment=TA_CENTER, spaceBefore=3, spaceAfter=6)

MAX_KEEP = PAGE_H * 0.4

def safe_keep(elements):
    total = 0
    for el in elements:
        w, h = el.wrap(AVAIL_W, PAGE_H)
        total += h
    if total <= MAX_KEEP:
        return [KeepTogether(elements)]
    if len(elements) >= 2:
        return [KeepTogether(elements[:2])] + list(elements[2:])
    return list(elements)

class TocDocTemplate(SimpleDocTemplate):
    def afterFlowable(self, flowable):
        if hasattr(flowable, "bookmark_name"):
            self.notify("TOCEntry", (getattr(flowable, "bookmark_level", 0),
                                     getattr(flowable, "bookmark_text", ""),
                                     self.page,
                                     getattr(flowable, "bookmark_key", "")))

def heading(text, level):
    key = "h_" + hashlib.md5(text.encode()).hexdigest()[:8]
    style = st_h1 if level == 0 else st_h2
    p = Paragraph('<a name="%s"/><b>%s</b>' % (key, text), style)
    p.bookmark_name = text
    p.bookmark_level = level
    p.bookmark_text = text
    p.bookmark_key = key
    return p

def h1(story, text):
    story.append(CondPageBreak((PAGE_H - 2 * MARGIN) * 0.18))
    story.append(heading(text, 0))
    story.append(HRFlowable(width="100%", thickness=1.2, color=ACCENT, spaceAfter=8))

def h2(story, text):
    story.append(CondPageBreak((PAGE_H - 2 * MARGIN) * 0.12))
    story.append(heading(text, 1))

def para(story, text, indent=True):
    story.append(Paragraph(text, st_body if indent else st_body_ni))

def bullets(story, items):
    for it in items:
        story.append(Paragraph("•  " + it, st_bullet))

def make_table(header, rows, ratios, caption=None, align_center_cols=None):
    align_center_cols = align_center_cols or []
    data = [[Paragraph("<b>%s</b>" % h, st_th) for h in header]]
    for r in rows:
        row = []
        for j, cell in enumerate(r):
            row.append(Paragraph(cell, st_td_c if j in align_center_cols else st_td))
        data.append(row)
    widths = [x * AVAIL_W for x in ratios]
    assert abs(sum(ratios) - 1.0) < 1e-6
    t = Table(data, colWidths=widths, hAlign="CENTER", repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_FILL),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    for i in range(1, len(data)):
        style.append(("BACKGROUND", (0, i), (-1, i), colors.white if i % 2 == 1 else TABLE_STRIPE))
    t.setStyle(TableStyle(style))
    out = [Spacer(1, 10), t]
    if caption:
        out.append(Paragraph(caption, st_cap))
    out.append(Spacer(1, 8))
    return out

def callout(story, big, label):
    inner = Table(
        [[Paragraph("<b>%s</b>" % big, ParagraphStyle("cb", fontName="Microsoft YaHei-Bold",
                                                      fontSize=15, leading=22, textColor=ACCENT,
                                                      alignment=TA_CENTER, wordWrap="CJK"))],
         [Paragraph(label, ParagraphStyle("cl", fontName="SimHei", fontSize=9.5, leading=15,
                                          textColor=TEXT_PRIMARY, alignment=TA_CENTER,
                                          wordWrap="CJK"))]],
        colWidths=[AVAIL_W * 0.92], hAlign="CENTER")
    inner.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), CARD_BG),
        ("BOX", (0, 0), (-1, -1), 1, ACCENT),
        ("LINEBEFORE", (0, 0), (0, -1), 4, ACCENT),
        ("TOPPADDING", (0, 0), (-1, 0), 10),
        ("BOTTOMPADDING", (0, -1), (-1, -1), 10),
        ("TOPPADDING", (0, 1), (-1, 1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
    ]))
    story.extend([Spacer(1, 8)] + safe_keep([inner]) + [Spacer(1, 8)])

# ---------------- header / footer ----------------
def on_page(canvas, doc):
    canvas.saveState()
    canvas.setFont("Microsoft YaHei", 7.5)
    canvas.setFillColor(TEXT_MUTED)
    canvas.drawString(MARGIN, PAGE_H - 1.1 * cm, DOC_TITLE)
    canvas.setStrokeColor(ACCENT)
    canvas.setLineWidth(1.2)
    canvas.line(MARGIN, PAGE_H - 1.25 * cm, PAGE_W - MARGIN, PAGE_H - 1.25 * cm)
    canvas.setStrokeColor(BORDER)
    canvas.setLineWidth(0.5)
    canvas.line(MARGIN, 1.25 * cm, PAGE_W - MARGIN, 1.25 * cm)
    canvas.setFont("Microsoft YaHei", 7.5)
    canvas.drawString(MARGIN, 0.95 * cm, "三方圆桌 · 评估与修正")
    canvas.drawRightString(PAGE_W - MARGIN, 0.95 * cm, "第 %d 页" % doc.page)
    canvas.restoreState()

# ---------------- story ----------------
story = []

toc = TableOfContents()
toc.levelStyles = [
    ParagraphStyle("TOC1", fontName="Microsoft YaHei-Bold", fontSize=11.5, leading=20,
                   leftIndent=6, textColor=TEXT_PRIMARY, wordWrap="CJK"),
    ParagraphStyle("TOC2", fontName="SimHei", fontSize=10, leading=17,
                   leftIndent=26, textColor=TEXT_MUTED, wordWrap="CJK"),
]
story.append(Paragraph("<b>目 录</b>", ParagraphStyle(
    "TocTitle", fontName="Microsoft YaHei-Bold", fontSize=16, leading=24,
    textColor=TEXT_PRIMARY, spaceAfter=12)))
story.append(toc)
story.append(PageBreak())

# ============ 一、评估设置 ============
h1(story, "一、评估设置")
para(story, "本报告以多智能体三方圆桌方式，对沈阳药科大学大创项目《基于贝叶斯图神经网络的抗MASH天然药物筛选》"
            "的整体研发思路进行终局评估。评估对象为项目自申报书（v0）起，经全流程计算执行（v1）、遗传锚定重开课题（v2）、"
            "组合协同调控（v3）、交叉验证（v4）至统一评分（v5）的完整演进链。圆桌遵循既定模板：R1盲写立论（双方互不可见）、"
            "R2亮牌交锋（写作期间互盲）、裁判终局裁决；观点多样性由人格具体化、阅读清单不对称与盲写纪律三重机制保证，"
            "而非依赖模型差异。", indent=False)
story.extend(make_table(
    ["角色", "人格", "立场"],
    [["正方", "申报书作者方辩护人", "延续修正：思路整体成立，演进是证据驱动的科学深化，应收敛交付"],
     ["反方", "独立审计师（药物研发背景）", "推倒重做：系统性缺陷，给出可得性优先的全线替代方案"],
     ["裁判", "中立主持人", "程序性主持；对全部争议数字独立复算后裁决"]],
    [0.12, 0.30, 0.58], caption="表 1　圆桌阵容与立场", align_center_cols=[0]))
para(story, "评分标准事先公开于共享白板：方法/技术适配度30%、严谨性25%、领域可解释性20%、鲁棒性15%、论证质量10%，"
            "每维10分制加权。裁判纪律：只引文书与原始数据、先亮标准后打分、应询与让步对称执行、不引入第三方方案。", indent=False)

# ============ 二、交锋要点 ============
h1(story, "二、交锋要点")
h2(story, "2.1 反方审计命中（裁判复算全部属实）")
bullets(story, [
    "<b>终榜污染</b>：v5统一终榜前10名中5个为无名/CAS指代条目（最高0.789），无名条目压过具名候选；积雪草asiatic acid无计算分仍列一等。",
    "<b>安全性漏滤</b>：千里光（吡咯里西啶生物碱肝毒药材）无毒性过滤入榜；COCONUT organism字段存在数据血缘污染。",
    "<b>可得性失实</b>：07H239-A（原文标题即Cytotoxic，JNP 2004）与Alisiaquinol（未鉴定海绵）不可购，Obtain字段却置1.0，且07H239-A曾被列为湿实验首选。",
    "<b>CW-BCS缺陷</b>：榜首黄连、次席苦参的代表成分均为模型自标的域内低置信级；雷公藤仅2个成分却排第4，压过18个成分的丹参。",
    "<b>表述失实</b>：MARC1在研管线空白已被证伪（OliX OLX75016进入Ph1，Lilly以最高6.3亿美元许可）；樟芝临床RCT实为28例菌丝体全粉、血清学终点；FINAL_REPORT的1847系申报书引用错误（原文约569条）。",
    "<b>披露缺口</b>：骨架划分95%覆盖率0.80未在报告披露；v2十靶点QSAR只有随机划分，无骨架验证，解决外推的主张不成立。",
])
h2(story, "2.2 正方复算翻盘（裁判验证吻合）")
bullets(story, [
    "<b>口径澄清</b>：反方王牌数字sigma-误差Spearman=-0.027系json存储的pooled口径（val+test合并，n=71）；test-only复算随机划分为+0.585（p约2e-4，显著）、骨架划分为+0.269（方向为正）——sigma在外推完全失效的论断不成立。",
    "<b>归属纠正</b>：掐头去尾R<super>2</super>=-10.04实为骨架划分算术（裁判复算-11.11）；随机划分实测+0.41——反方将骨架划分的算术安到了随机划分头上。",
    "<b>外部反查</b>：OLX75016 Ph1属实但Novo同类管线同月被砍，证明反方单轴一锤定音的替代逻辑同样脆弱。",
    "<b>诚实让步</b>：正方让步11项（sigma域外欠膨胀、n=2直排、无名条目、千里光漏滤、07H239-A不可购、证据措辞拔高等）并全部给出量化修补；反方让步5项（双划分协议过硬、崩塌属领域难题、HepG2设计规范、GSE数据为真、Alternaramide文献真实）。",
])
h2(story, "2.3 争议数字的裁判复算")
story.extend(make_table(
    ["争议点", "反方主张", "裁判实测", "裁定"],
    [["sigma-err Spearman（骨架）", "-0.027，sigma失效", "json存储值-0.027为pooled口径；test-only=+0.269（p=0.12）", "数字来源正方胜；完全失效论不成立"],
     ["掐头去尾R<super>2</super>", "-10.04，归于随机划分", "随机划分+0.41；骨架划分-11.11", "反方归属错误，正方胜"],
     ["骨架95%覆盖率", "0.80未披露", "0.80属实；test-only复算0.735更差", "反方实质正确，正方已让步"],
     ["v5终榜五项污染", "无名条目/Obtain失实等", "逐行核对全部属实", "反方指控成立，修补方案可行"],
     ["CW-BCS榜", "低置信代表/n=2直排", "属实；收缩算术复验正确（雷公藤0.565至0.162）", "反方指控成立，正方修补成立"]],
    [0.20, 0.22, 0.33, 0.25], caption="表 2　五项争议数字的独立复算裁决"))

# ============ 三、裁决结果 ============
h1(story, "三、裁决结果")
callout(story, "有条件成立 —— 以延续修正为主体",
        "辩题答案：项目研发思路有条件成立，必须吸收反方三项结构性条件（输出层重建、UQ域外校准与披露纪律、契约对齐与可得性优先）；"
        "条件不执行则推倒重做自动成立。核心依据：正方核心资产真实可复现，失败集中于输出层与披露纪律，而全部修补方案已在双方之间形成共识——"
        "修正的成本远低于重做。")
story.extend(make_table(
    ["维度", "权重", "正方（延续修正）", "反方（推倒重做）"],
    [["方法/技术适配度", "30%", "6.5", "6.0"],
     ["严谨性", "25%", "7.0", "6.5"],
     ["领域可解释性", "20%", "7.0", "6.5"],
     ["鲁棒性", "15%", "6.0", "7.0"],
     ["论证质量", "10%", "8.0", "6.5"],
     ["加权总分", "100%", "<b>6.80</b>", "<b>6.43</b>"]],
    [0.34, 0.16, 0.25, 0.25], caption="表 3　五维加权总分（每维10分制）", align_center_cols=[1, 2, 3]))
para(story, "胜负手：正方复算数字6/6经裁判验证吻合且应询让步充分；反方审计命中率极高并赢下化合物库与交付诊断两个子问题，"
            "但其两张王牌统计数字经复算归属有误且未撤回。", indent=False)
h2(story, "3.1 逐子问题裁定")
story.extend(make_table(
    ["子问题", "胜方", "裁定要点"],
    [["1 靶点策略", "正方微胜（附条件）", "GSE135251四靶实证+三阶演进各有触发依据；须按证据层级重述并删除管线空白等失实表述"],
     ["2 模型与数据", "数字归正方，实质归反方", "0.79掐后+0.41、sigma域内+0.585成立；覆率0.80未披露与v2无骨架验证确凿"],
     ["3 化合物库与候选", "反方胜", "五项指控全部属实；方向（可得性优先）采纳反方，榜单重建按正方修补执行"],
     ["4 交付与定位", "诊断归反方，解法归正方", "契约/结题/清单三者互斥属实；v1口径冻结+v2-v5作附录的呈报纪律可执行"],
     ["5 下一步", "实质共识", "双方收敛于可购标准品+HepG2脂变+小鼠外置的同一方案"]],
    [0.17, 0.22, 0.61], caption="表 4　五个子问题的裁定"))
h2(story, "3.2 共识与保留分歧")
para(story, "双方形成16条可直接执行的共识，要点包括：双划分评估协议是全项目最过硬的方法学产出必须保留；骨架95%覆率0.80须补披露；"
            "v5终榜污染条目除名重跑且一等梯队位次不变；雷公藤收缩后落至丹参之后；千里光建PA黑名单；07H239-A降为计算对照、"
            "Versicolamide B降为机制参照；MARC1管线空白表述删除；樟芝证据降为物种级表述；1847更正为569；20个可购标准品外部校准实验采纳执行；"
            "结题以v1契约口径呈报、v2-v5作延伸附录。", indent=False)
para(story, "另有7项保留分歧记录在案、不强行裁决，其中两项需后续数据定谳：骨架sigma-err真值（pooled口径-0.027与test-only口径+0.269并存，"
            "需更大域外验证集）；宽量程拉高R<super>2</super>的定性（0.79至0.41方向成立、纯靠不成立）。", indent=False)

# ============ 四、修正执行记录 ============
h1(story, "四、修正执行记录（本报告已落地项）")
h2(story, "4.1 A1　v5终榜重跑（已完成）")
para(story, "删除5个无名/CAS条目；千里光全药材除名并建立PA药材黑名单；07H239-A与Alisiaquinol的Obtain实证置0"
            "（FINAL分别由0.626降至0.526、0.625降至0.524）；樟芝证据措辞更正为物种级临床证据。修正后榜首樟芝Antrocinnamomin F（0.859）不变；"
            "敏感性检验（证据分从严1.0至0.7）下FINAL=0.799仍居首，但与第2名（0.792）仅差0.007，属边缘领先，如实呈报。"
            "输出results/v5/final_unified_scores_fix.csv，原始文件保留溯源。", indent=False)
story.extend(make_table(
    ["排名", "候选", "FINAL", "备注"],
    [["1", "樟芝 Antrocinnamomin F", "0.859", "一等A档；敏感性0.799仍居首"],
     ["2", "白花蛇舌草 | Anthraxin", "0.792", "一等B档（计算+可购）"],
     ["3", "甘草 | Derrone", "0.786", "一等B档"],
     ["4", "土曲霉 Aspernolide D族丁内酯", "0.737", "一等B档（发酵可得）"],
     ["5", "茵陈 | 螺甾烷苷元", "0.716", "观察项：化学类别名，待具名鉴定"],
     ["6", "海洋 Alternaramide", "0.620", "存疑档：待NF-kB报告基因裁决"],
     ["7", "内生曲霉 Aspergicin", "0.614", "证据单链（纯计算）"],
     ["8", "内生真菌 07H239-A", "0.526", "计算对照档：Obtain实证置0"],
     ["9", "海绵 Alisiaquinol", "0.524", "计算对照档：来源不可得"],
     ["10", "积雪草 | asiatic acid", "0.320", "一等A档：无计算分，以直接文献入列"]],
    [0.09, 0.34, 0.11, 0.46], caption="表 5　修正后v5统一终榜（final_unified_scores_fix.csv）", align_center_cols=[0, 2]))
h2(story, "4.2 A3　CW-BCS榜双修（已完成）")
para(story, "经验贝叶斯收缩（score*n/(n+5)）后，雷公藤由第4（0.565）落至第9（0.162），前四名不变；代表成分置信硬约束执行："
            "域内低置信成分不得单独作为药材代表。输出results/tables/herb_cwbcs_ranking_fix.csv。", indent=False)
story.extend(make_table(
    ["排名", "中药", "收缩分", "代表成分（置信硬约束后）"],
    [["1", "黄连", "0.529", "Epiberberine（高置信）；Coptisine降为次代表"],
     ["2", "苦参", "0.458", "Kushenol E（高置信）；Maackiain降为次代表"],
     ["3", "甘草", "0.443", "Licoflavanone（高置信）"],
     ["4", "丹参", "0.427", "Salvilenone（高置信）"],
     ["5", "青蒿", "0.375", "Chrysosplenol D（高置信）+Deoxyartemisinin（域外参考）"],
     ["6", "水飞蓟", "0.285", "全成分域外预警，整药材标注警示"],
     ["7", "五味子", "0.277", "Schisandrin C（高置信）；Pregomisin降为次代表"],
     ["8", "灵芝", "0.221", "Lucidenic acid C（高置信）"],
     ["9", "雷公藤", "0.162", "Triptophenolide（收缩后由第4落至第9）"],
     ["10", "柴胡", "0.037", "Saikogenin F（高置信）"]],
    [0.09, 0.11, 0.11, 0.69], caption="表 6　收缩+置信约束后的中药CW-BCS榜（herb_cwbcs_ranking_fix.csv）", align_center_cols=[0, 2]))
h2(story, "4.3 A2/A5　报告更正与候选清单四档重排（已完成）")
para(story, "FINAL_REPORT完成三处更正：1847更正为申报书原文的约569条；补录外推场景披露段（骨架sigma-err双口径与95%覆率0.80、"
            "sigma加权产品降级声明）；CW-BCS收缩榜注记。最终候选清单按四档重排（详见mash_research/最终候选清单_圆桌修订版.md）："
            "一等（证据双链/可购）=樟芝群+积雪草asiatic acid，B档=白花蛇舌草/甘草/土曲霉群；存疑档=Alternaramide（文献已复核真实，维持降级待裁决）；"
            "计算对照档=07H239-A与Alisiaquinol；机制参照档=Versicolamide B。组合方案首选Antrocinnamomin F+asiatic acid（代谢+纤维化轴）。", indent=False)

# ============ 五、修正后研发思路（终稿） ============
h1(story, "五、修正后研发思路（终稿）")
h2(story, "5.1 定位与契约")
para(story, "本科大创的计算方法学项目。主线交付=申报书契约（带不确定性量化的GNN筛选框架+CW-BCS四维表+前5味中药+结题与论文）；"
            "v2至v5全部定位为延伸探索附录，答辩主线即申报书技术路线，消除契约漂移风险。", indent=False)
h2(story, "5.2 靶点叙事（按证据层级重述）")
para(story, "FXR/THR-beta/ACC三靶的GSE135251患者数据实证（padj均显著、四个阳性对照基因方向正确）为表达关联层；遗传学锚定"
            "（MARC1等GWAS级证据）为更高层级参照，MARC1以重组酶活试验为实验出口、不作建模主锚；删除管线空白类失实表述；"
            "每季度外部证据核对（OLX75016与denifanstat III期读出）维护叙事。", indent=False)
h2(story, "5.3 模型与不确定性量化")
para(story, "双划分评估协议为全项目最硬方法学产出，保留并作为论文主线（天然产物外推崩塌的定量实证+UQ域外校准）；"
            "sigma的有效性声明限定域内（test-only +0.585显著），域外欠膨胀（覆率0.80）如实披露；在sigma乘杠杆膨胀+conformal重校准完成前，"
            "三级标注与w=1/(1+sigma)加权产品一律附域内有效/域外校准中声明；v2十靶点QSAR补骨架划分验证，无骨架验证的靶点不得输出域外排序，"
            "弱模型靶点（SCD 0.393、ACC2 0.514）排序权重下调。", indent=False)
h2(story, "5.4 化合物库与候选管理")
para(story, "可得性优先原则入规：Obtain为实证字段（每个1.0条目附可购证明）；PA肝毒药材黑名单前置；成分归属硬过滤"
            "（药材接受名匹配+文献共现，修复COCONUT organism血缘错误）；无名/CAS条目不得入榜；候选按四档清单管理，"
            "湿实验只上一等可购标样。", indent=False)
h2(story, "5.5 验证与交付")
para(story, "湿实验（一学期/1500元档）：首批4个可购标样（antcin K、antrodin B、asiatic acid、小檗碱），HepG2脂变模型"
            "（棕榈酸/油酸2:1诱导24-48小时）四点浓度，Hit标准=TG较模型组下降30%以上且活力80%以上@浓度不高于10微摩尔，"
            "小檗碱/lovastatin双阳性对照；AMLN小鼠维持外置（需外部合作与追加经费，不进大创承诺）。该实验同时是圆桌采纳的外部校准回路，"
            "终结纯计算自证。交付：结题按v1契约口径冻结（R<super>2</super>=0.790超契约32%、131成分四维表、开源框架）；"
            "论文重定位为双划分实证+UQ域外校准的方法学主线，候选清单作应用示例；答辩问答预案三题备齐。", indent=False)

# ============ 六、行动清单状态 ============
h1(story, "六、行动清单状态")
story.extend(make_table(
    ["档", "项", "内容", "状态"],
    [["结题必须", "A1", "v5终榜重跑（除名/黑名单/Obtain实证）", "已完成"],
     ["结题必须", "A2", "FINAL_REPORT三处更正（1847/披露/收缩注记）", "已完成"],
     ["结题必须", "A3", "CW-BCS收缩+代表成分置信硬约束", "已完成"],
     ["结题必须", "A5", "最终候选清单四档重排", "已完成"],
     ["结题必须", "A4", "结题呈报口径冻结（v1主线+v2-v5附录）", "结题文书撰写时执行"],
     ["答辩论文", "B1", "答辩问答预案三题（演进链/骨架崩塌/新榜）", "待办"],
     ["答辩论文", "B2", "sigma域外conformal重校准（覆率目标0.90以上）", "待办"],
     ["答辩论文", "B3", "论文主线重定位（双划分+UQ域外校准）", "待办"],
     ["答辩论文", "B4", "樟芝证据表述统一（物种级临床证据）", "已随A1/A5落地"],
     ["继续研究", "C1", "4标样HepG2脂变外部校准实验", "待办"],
     ["继续研究", "C2", "成分归属硬过滤+COCONUT血缘修复重扫", "待办"],
     ["继续研究", "C3", "v2十靶点QSAR补骨架划分验证", "待办"],
     ["继续研究", "C4", "MARC1重组酶活出口+外部管线季度跟踪", "待办"],
     ["继续研究", "C5", "AMLN小鼠维持外置（不进承诺）", "已写入修订版清单"]],
    [0.13, 0.07, 0.60, 0.20], caption="表 7　14项行动清单执行状态", align_center_cols=[0, 1, 3]))

# ============ 七、结论 ============
h1(story, "七、结论")
para(story, "圆桌三方经两轮盲写交锋与裁判独立复算，得出一致可执行的结论：该项目研发思路有条件成立——学术内核"
            "（双划分协议、真实数据全流程、UQ框架）经复算为真且为最硬产出，不需要推倒重做；但输出层（榜单、证据标注、可得性、披露纪律）"
            "按审计意见完成重建后方可交付。", indent=False)
para(story, "本报告已执行全部可计算修正项：终榜除名污染条目后一等梯队位次稳定（樟芝0.859居首，敏感性检验下仍居首）；"
            "CW-BCS收缩修正后前四名不变而雷公藤回落至第9；候选清单按一等/存疑/计算对照/机制参照四档重排；"
            "湿实验入口收敛为4个可购标样+HepG2脂变模型。剩余B/C档行动项按表7推进，全部完成前不提交结题材料。", indent=False)
para(story, "全部文书可溯源：roundtable/目录含四份辩论文书、裁决书与本报告；mash_research/results/含原始与修正数据表；"
            "修正脚本为mash_research/src/fix_v5_cwbcs_roundtable.py。", indent=False)

# ---------------- build ----------------
doc = TocDocTemplate(
    BODY_PDF, pagesize=A4,
    leftMargin=MARGIN, rightMargin=MARGIN, topMargin=2.1 * cm, bottomMargin=1.9 * cm,
    title=DOC_TITLE, author="Z.ai", creator="Z.ai",
    subject="大创项目整体研发思路三方圆桌评估与修正报告")
doc.multiBuild(story, onFirstPage=on_page, onLaterPages=on_page)
print("body built:", BODY_PDF)

# ---------------- merge cover ----------------
from pypdf import PdfReader, PdfWriter, Transformation

A4_W, A4_H = 595.28, 841.89

def normalize(page):
    w, h = float(page.mediabox.width), float(page.mediabox.height)
    if abs(w - A4_W) > 0.3 or abs(h - A4_H) > 0.3:
        page.add_transformation(Transformation().scale(sx=A4_W / w, sy=A4_H / h))
        page.mediabox.lower_left = (0, 0)
        page.mediabox.upper_right = (A4_W, A4_H)
    return page

writer = PdfWriter()
writer.add_page(normalize(PdfReader(os.path.join(OUT, "cover.pdf")).pages[0]))
for p in PdfReader(BODY_PDF).pages:
    writer.add_page(normalize(p))
writer.add_metadata({"/Title": DOC_TITLE, "/Author": "Z.ai", "/Creator": "Z.ai",
                     "/Subject": "三方圆桌评估与修正报告"})
FINAL = os.path.join(OUT, "大创研发思路圆桌评估与修正报告.pdf")
with open(FINAL, "wb") as f:
    writer.write(f)
print("final:", FINAL)
