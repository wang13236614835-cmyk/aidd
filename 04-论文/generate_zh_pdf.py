# -*- coding: utf-8 -*-
"""manuscript_zh.md -> 论文_中文通俗版.pdf（期刊稿件式样，中文正文 SimHei）。"""
import os
import re
import sys

PDF_SKILL_DIR = r"C:\Users\user\.zcode\cli\plugins\cache\zcode-plugins-official\document-skills\0.1.0\skills\pdf"
sys.path.insert(0, os.path.join(PDF_SKILL_DIR, "scripts"))

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image,
    CondPageBreak, HRFlowable,
)

pdfmetrics.registerFont(TTFont("Microsoft YaHei", "C:/Windows/Fonts/msyh.ttc", subfontIndex=0))
pdfmetrics.registerFont(TTFont("Microsoft YaHei-Bold", "C:/Windows/Fonts/msyhbd.ttc", subfontIndex=0))
pdfmetrics.registerFont(TTFont("SimHei", "C:/Windows/Fonts/simhei.ttf"))
pdfmetrics.registerFont(TTFont("Times New Roman", "C:/Windows/Fonts/times.ttf"))
pdfmetrics.registerFont(TTFont("Times New Roman-Bold", "C:/Windows/Fonts/timesbd.ttf"))
registerFontFamily("Microsoft YaHei", normal="Microsoft YaHei", bold="Microsoft YaHei-Bold",
                   italic="Microsoft YaHei", boldItalic="Microsoft YaHei-Bold")
registerFontFamily("SimHei", normal="SimHei", bold="SimHei", italic="SimHei", boldItalic="SimHei")
registerFontFamily("Times New Roman", normal="Times New Roman", bold="Times New Roman-Bold",
                   italic="Times New Roman", boldItalic="Times New Roman-Bold")
try:
    from pdf import install_font_fallback
    install_font_fallback()
except Exception as e:
    print("fallback skipped:", e)

ACCENT = colors.HexColor("#1f7692")
HEADER_FILL = colors.HexColor("#4e4732")
TABLE_STRIPE = colors.HexColor("#ededeb")
BORDER = colors.HexColor("#c5bfac")
TEXT_PRIMARY = colors.HexColor("#151513")
TEXT_MUTED = colors.HexColor("#7e7c74")

P = "D:/zcode-workspace/paper"
OUT = f"{P}/论文_中文通俗版.pdf"
MARGIN = 2.2 * cm
PAGE_W, PAGE_H = A4
AVAIL = PAGE_W - 2 * MARGIN

st_title = ParagraphStyle("T", fontName="Microsoft YaHei-Bold", fontSize=15, leading=22,
                          textColor=TEXT_PRIMARY, spaceAfter=10, wordWrap="CJK")
st_h1 = ParagraphStyle("H1", fontName="Microsoft YaHei-Bold", fontSize=12.5, leading=18,
                       textColor=HEADER_FILL, spaceBefore=14, spaceAfter=6, wordWrap="CJK")
st_h2 = ParagraphStyle("H2", fontName="Microsoft YaHei-Bold", fontSize=11, leading=16,
                       textColor=TEXT_PRIMARY, spaceBefore=10, spaceAfter=4, wordWrap="CJK")
st_body = ParagraphStyle("B", fontName="SimHei", fontSize=10.5, leading=17,
                         textColor=TEXT_PRIMARY, alignment=TA_JUSTIFY, spaceAfter=7, wordWrap="CJK")
st_th = ParagraphStyle("TH", fontName="Microsoft YaHei-Bold", fontSize=8.5, leading=12.5,
                       textColor=colors.white, alignment=TA_CENTER, wordWrap="CJK")
st_td = ParagraphStyle("TD", fontName="SimHei", fontSize=8.5, leading=12.5,
                       textColor=TEXT_PRIMARY, alignment=TA_LEFT, wordWrap="CJK")
st_cap = ParagraphStyle("CAP", fontName="SimHei", fontSize=9, leading=14,
                        textColor=TEXT_PRIMARY, spaceBefore=4, spaceAfter=12, wordWrap="CJK")
st_ref = ParagraphStyle("REF", fontName="SimHei", fontSize=9, leading=13.5,
                        textColor=TEXT_PRIMARY, spaceAfter=4, leftIndent=14,
                        firstLineIndent=-14, wordWrap="CJK")

def fmt(text):
    text = text.replace("&", "&").replace("<", "<").replace(">", ">")
    text = text.replace("pIC<sub>5</sub><sub>0</sub>", "pIC<sub>50</sub>").replace("IC<sub>5</sub><sub>0</sub>", "IC<sub>50</sub>")
    text = text.replace("R<super>2</super>", "R<super>2</super>").replace("σ<super>2</super>", "σ<super>2</super>")
    for k, v in [("10<super>-</super><super>4</super>", "10<super>-4</super>"), ("10<super>-</super><super>2</super>", "10<super>-2</super>"),
                 ("10<super>-</super><super>3</super>", "10<super>-3</super>"), ("10<super>-</super><super>5</super>", "10<super>-5</super>"),
                 ("5×10<super>-</super><super>4</super>", "5×10<super>-4</super>"), ("10<super>-</super><super>6</super>", "10<super>-6</super>")]:
        text = text.replace(k, v)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<i>\1</i>", text)
    return text

def md_table(lines):
    rows = []
    for ln in lines:
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if all(re.fullmatch(r":?-{2,}:?", c or "---") for c in cells):
            continue
        rows.append(cells)
    ncol = max(len(r) for r in rows)
    rows = [r + [""] * (ncol - len(r)) for r in rows]
    lens = [max(len(r[i]) for r in rows) for i in range(ncol)]
    caps = [min(l, 40) for l in lens]
    tot = sum(caps)
    ratios = [max(c / tot, 0.07) for c in caps]
    s = sum(ratios)
    ratios = [r / s for r in ratios]
    widths = [r * AVAIL for r in ratios]
    data = [[Paragraph(fmt(c), st_th) for c in rows[0]]]
    for r in rows[1:]:
        data.append([Paragraph(fmt(c), st_td) for c in r])
    t = Table(data, colWidths=widths, hAlign="CENTER", repeatRows=1)
    style = [("BACKGROUND", (0, 0), (-1, 0), HEADER_FILL),
             ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
             ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
             ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
             ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]
    for i in range(1, len(data)):
        style.append(("BACKGROUND", (0, i), (-1, i), colors.white if i % 2 == 1 else TABLE_STRIPE))
    t.setStyle(TableStyle(style))
    return t

def embed_fig(path, max_h=300):
    from PIL import Image as PILImage
    w, h = PILImage.open(path).size
    ratio = min(AVAIL / w, max_h / h, 1.0)
    return Image(path, width=w * ratio, height=h * ratio)

def on_page(canvas, doc):
    canvas.saveState()
    canvas.setFont("Microsoft YaHei", 7.5)
    canvas.setFillColor(TEXT_MUTED)
    canvas.drawString(MARGIN, PAGE_H - 1.05 * cm, "中文稿件 —— 面向投稿的通俗中文全稿（含圆桌二轮全部修正 F1-F13/S1-S11）")
    canvas.setStrokeColor(ACCENT); canvas.setLineWidth(1.0)
    canvas.line(MARGIN, PAGE_H - 1.2 * cm, PAGE_W - MARGIN, PAGE_H - 1.2 * cm)
    canvas.setStrokeColor(BORDER); canvas.setLineWidth(0.5)
    canvas.line(MARGIN, 1.2 * cm, PAGE_W - MARGIN, 1.2 * cm)
    canvas.drawString(MARGIN, 0.9 * cm, "王启龙 等 —— 天然产物虚拟筛选的双划分审计")
    canvas.drawRightString(PAGE_W - MARGIN, 0.9 * cm, "第 %d 页" % doc.page)
    canvas.restoreState()

md = open(f"{P}/manuscript_zh.md", encoding="utf-8").read()
lines = md.splitlines()
story = []
i = 0
title_done = False
fig_count = 0
FIGS = ["fig1_dual_split.png", "fig2_recalibration.png", "fig3_tiers.png", "fig4_cwbcs.png"]

while i < len(lines):
    s = lines[i].strip()
    if not s or s == "---":
        i += 1
        continue
    if s.startswith("# ") and not title_done:
        story.append(Paragraph(fmt(s[2:]), st_title))
        title_done = True
        i += 1
        continue
    if s.startswith("## "):
        head = s[3:]
        story.append(CondPageBreak((PAGE_H - 2 * MARGIN) * 0.12))
        story.append(Paragraph(fmt(head), st_h1))
        if head.startswith(("表格", "图注")):
            story.append(HRFlowable(width="100%", thickness=0.8, color=ACCENT, spaceAfter=6))
        i += 1
        continue
    if s.startswith("### "):
        story.append(CondPageBreak((PAGE_H - 2 * MARGIN) * 0.10))
        story.append(Paragraph(fmt(s[4:]), st_h2))
        i += 1
        continue
    if s.startswith("|"):
        block = []
        while i < len(lines) and lines[i].strip().startswith("|"):
            block.append(lines[i]); i += 1
        story.append(Spacer(1, 6))
        story.append(md_table(block))
        story.append(Spacer(1, 8))
        continue
    if s.startswith("**图"):
        fig_count += 1
        if fig_count <= len(FIGS):
            img = embed_fig(f"{P}/figs/{FIGS[fig_count - 1]}")
            story.extend([Spacer(1, 8), img, Paragraph(fmt(s), st_cap)])
        else:
            story.append(Paragraph(fmt(s), st_cap))
        i += 1
        continue
    if re.match(r"^\d+\.\s", s):
        story.append(Paragraph(fmt(s), st_ref))
        i += 1
        continue
    story.append(Paragraph(fmt(s), st_body))
    i += 1

doc = SimpleDocTemplate(OUT, pagesize=A4,
                        leftMargin=MARGIN, rightMargin=MARGIN,
                        topMargin=1.9 * cm, bottomMargin=1.8 * cm,
                        title="天然产物虚拟筛选的双划分审计（中文稿）",
                        author="Z.ai", creator="Z.ai",
                        subject="通俗中文SCI稿——圆桌二轮修正版")
doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
print("built:", OUT)
