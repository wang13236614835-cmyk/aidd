# -*- coding: utf-8 -*-
"""国创赛（中国国际大学生创新大赛）项目计划书生成脚本
由大创申报书 + 抗MASH研究成果改写为商业计划书格式
"""
import os
import sys
import hashlib

SKILL_SCRIPTS = r"C:\Users\user\.zcode\cli\plugins\cache\zcode-plugins-official\document-skills\0.1.0\skills\pdf\scripts"
if SKILL_SCRIPTS not in sys.path:
    sys.path.insert(0, SKILL_SCRIPTS)

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch, cm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether, CondPageBreak, Image, HRFlowable,
)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily

# ------------------------------------------------------------------
# 字体注册（Windows 系统字体，本机已验证）
# ------------------------------------------------------------------
pdfmetrics.registerFont(TTFont("Microsoft YaHei", r"C:\Windows\Fonts\msyh.ttc", subfontIndex=0))
pdfmetrics.registerFont(TTFont("Microsoft YaHei-Bold", r"C:\Windows\Fonts\msyhbd.ttc", subfontIndex=0))
pdfmetrics.registerFont(TTFont("SimHei", r"C:\Windows\Fonts\simhei.ttf"))
pdfmetrics.registerFont(TTFont("Times New Roman", r"C:\Windows\Fonts\times.ttf"))
pdfmetrics.registerFont(TTFont("Times New Roman-Bold", r"C:\Windows\Fonts\timesbd.ttf"))
registerFontFamily(
    "Microsoft YaHei", normal="Microsoft YaHei", bold="Microsoft YaHei-Bold",
    italic="Microsoft YaHei", boldItalic="Microsoft YaHei-Bold",
)
registerFontFamily("SimHei", normal="SimHei", bold="SimHei", italic="SimHei", boldItalic="SimHei")
registerFontFamily(
    "Times New Roman", normal="Times New Roman", bold="Times New Roman-Bold",
    italic="Times New Roman", boldItalic="Times New Roman-Bold",
)

from pdf import install_font_fallback  # noqa: E402
install_font_fallback()

# ------------------------------------------------------------------
# 配色（palette.cascade 自动生成，禁止手改）
# ------------------------------------------------------------------
PAGE_BG       = colors.HexColor('#eff0f1')
SECTION_BG    = colors.HexColor('#f0f1f2')
CARD_BG       = colors.HexColor('#e4e7e8')
TABLE_STRIPE  = colors.HexColor('#ebedee')
HEADER_FILL   = colors.HexColor('#334650')
COVER_BLOCK   = colors.HexColor('#5a7886')
BORDER        = colors.HexColor('#b8c8cf')
ICON          = colors.HexColor('#52798c')
ACCENT        = colors.HexColor('#a63648')
ACCENT_2      = colors.HexColor('#813ab4')
TEXT_PRIMARY  = colors.HexColor('#1a1b1c')
TEXT_MUTED    = colors.HexColor('#6f7578')
SEM_SUCCESS   = colors.HexColor('#46875c')
SEM_WARNING   = colors.HexColor('#a18347')
SEM_ERROR     = colors.HexColor('#92453e')
SEM_INFO      = colors.HexColor('#466a8e')

# ------------------------------------------------------------------
# 页面与样式
# ------------------------------------------------------------------
PAGE_W, PAGE_H = A4
LM = RM = 2.0 * cm
TM, BM = 2.2 * cm, 2.0 * cm
AVAIL_W = PAGE_W - LM - RM
MAX_KEEP_HEIGHT = PAGE_H * 0.4

S = {}
S['H1'] = ParagraphStyle('H1', fontName='Microsoft YaHei-Bold', fontSize=16.5, leading=24,
                         textColor=HEADER_FILL, spaceBefore=16, spaceAfter=8, wordWrap='CJK')
S['H2'] = ParagraphStyle('H2', fontName='Microsoft YaHei-Bold', fontSize=12.5, leading=18,
                         textColor=TEXT_PRIMARY, spaceBefore=13, spaceAfter=6, wordWrap='CJK')
S['H3'] = ParagraphStyle('H3', fontName='Microsoft YaHei-Bold', fontSize=11, leading=16,
                         textColor=ICON, spaceBefore=10, spaceAfter=5, wordWrap='CJK')
S['Body'] = ParagraphStyle('Body', fontName='SimHei', fontSize=10.3, leading=16.8,
                           textColor=TEXT_PRIMARY, alignment=TA_LEFT, wordWrap='CJK',
                           firstLineIndent=20.6, spaceBefore=0, spaceAfter=7)
S['BodyNoInd'] = ParagraphStyle('BodyNoInd', parent=S['Body'], firstLineIndent=0)
S['Bullet'] = ParagraphStyle('Bullet', fontName='SimHei', fontSize=10.2, leading=16.2,
                             textColor=TEXT_PRIMARY, leftIndent=16, firstLineIndent=0,
                             spaceBefore=1, spaceAfter=3, wordWrap='CJK')
S['Quote'] = ParagraphStyle('Quote', fontName='Microsoft YaHei', fontSize=10.6, leading=17.5,
                            textColor=HEADER_FILL, leftIndent=22, rightIndent=12,
                            borderPadding=0, spaceBefore=8, spaceAfter=8, wordWrap='CJK')
S['TH'] = ParagraphStyle('TH', fontName='Microsoft YaHei-Bold', fontSize=9.2, leading=13,
                         textColor=colors.white, alignment=TA_CENTER, wordWrap='CJK')
S['TD'] = ParagraphStyle('TD', fontName='SimHei', fontSize=9.0, leading=13.2,
                         textColor=TEXT_PRIMARY, alignment=TA_LEFT, wordWrap='CJK')
S['TDC'] = ParagraphStyle('TDC', parent=S['TD'], alignment=TA_CENTER)
S['Caption'] = ParagraphStyle('Caption', fontName='Microsoft YaHei', fontSize=8.6, leading=12,
                              textColor=TEXT_MUTED, alignment=TA_CENTER, wordWrap='CJK',
                              spaceBefore=4, spaceAfter=4)
S['TOCH'] = ParagraphStyle('TOCH', fontName='Microsoft YaHei-Bold', fontSize=17, leading=24,
                           textColor=HEADER_FILL, spaceAfter=12)
S['TOC1'] = ParagraphStyle('TOC1', fontName='Microsoft YaHei-Bold', fontSize=11, leading=20,
                           textColor=TEXT_PRIMARY, leftIndent=6)
S['TOC2'] = ParagraphStyle('TOC2', fontName='SimHei', fontSize=9.8, leading=17,
                           textColor=TEXT_MUTED, leftIndent=26)
S['StatBig'] = ParagraphStyle('StatBig', fontName='Microsoft YaHei-Bold', fontSize=17, leading=21,
                              textColor=HEADER_FILL, alignment=TA_CENTER, wordWrap='CJK')
S['StatLabel'] = ParagraphStyle('StatLabel', fontName='SimHei', fontSize=8.4, leading=11.6,
                                textColor=TEXT_MUTED, alignment=TA_CENTER, wordWrap='CJK')
S['Small'] = ParagraphStyle('Small', fontName='SimHei', fontSize=8.6, leading=12.6,
                            textColor=TEXT_MUTED, wordWrap='CJK', spaceAfter=4)

# ------------------------------------------------------------------
# 辅助函数
# ------------------------------------------------------------------
class TocDocTemplate(SimpleDocTemplate):
    def afterFlowable(self, flowable):
        if hasattr(flowable, 'bookmark_name'):
            level = getattr(flowable, 'bookmark_level', 0)
            text = getattr(flowable, 'bookmark_text', '')
            key = getattr(flowable, 'bookmark_key', '')
            self.notify('TOCEntry', (level, text, self.page, key))


def add_heading(text, level=0):
    key = 'h_%s' % hashlib.md5(text.encode()).hexdigest()[:8]
    style = S['H1'] if level == 0 else S['H2']
    p = Paragraph('<a name="%s"/>%s' % (key, text), style)
    p.bookmark_name = text
    p.bookmark_level = level
    p.bookmark_text = text
    p.bookmark_key = key
    return p


H1_ORPHAN = (PAGE_H - TM - BM) * 0.18


def h1(story, text):
    story.append(CondPageBreak(H1_ORPHAN))
    story.append(add_heading(text, 0))
    story.append(HRFlowable(width='100%', thickness=1.1, color=ICON,
                            spaceBefore=0, spaceAfter=9))


def h2(story, text):
    story.append(CondPageBreak(H1_ORPHAN * 0.7))
    story.append(add_heading(text, 1))


def body(story, text):
    story.append(Paragraph(text, S['Body']))


def bullets(story, items):
    for it in items:
        story.append(Paragraph('• ' + it, S['Bullet']))
    story.append(Spacer(1, 4))


def stat_row(story, stats):
    """数据雕塑：[(大数字, 标签), ...] 一行展示"""
    n = len(stats)
    gap = 8
    w = (AVAIL_W - gap * (n - 1)) / n
    cells, widths = [], []
    for i, (num, label) in enumerate(stats):
        inner = Table(
            [[Paragraph('<b>%s</b>' % num, S['StatBig'])],
             [Paragraph(label, S['StatLabel'])]],
            colWidths=[w],
        )
        inner.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), SECTION_BG),
            ('LINEABOVE', (0, 0), (-1, 0), 2, ICON),
            ('TOPPADDING', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 2),
            ('TOPPADDING', (0, 1), (-1, 1), 1),
            ('BOTTOMPADDING', (0, 1), (-1, 1), 9),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        cells.append(inner)
        widths.append(w)
        if i < n - 1:
            cells.append('')
            widths.append(gap)
    outer = Table([cells], colWidths=widths, hAlign='CENTER')
    outer.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(Spacer(1, 6))
    story.append(outer)
    story.append(Spacer(1, 10))


def callout(story, text, color=ICON):
    tbl = Table([[Paragraph(text, S['Quote'])]], colWidths=[AVAIL_W])
    tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), SECTION_BG),
        ('LINEBEFORE', (0, 0), (0, -1), 3, color),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(Spacer(1, 4))
    story.append(tbl)
    story.append(Spacer(1, 6))


def make_table(story, header, rows, ratios, caption=None, align_center_cols=None):
    """标准表格：表头 HEADER_FILL 白字 + 隔行条纹 + 全 Paragraph 包裹"""
    widths = [r * AVAIL_W for r in ratios]
    data = [[Paragraph('<b>%s</b>' % h, S['TH']) for h in header]]
    align_center_cols = align_center_cols or []
    for r in rows:
        row = []
        for ci, c in enumerate(r):
            st = S['TDC'] if ci in align_center_cols else S['TD']
            row.append(Paragraph(c, st))
        data.append(row)
    tbl = Table(data, colWidths=widths, hAlign='CENTER', repeatRows=1)
    style = [
        ('BACKGROUND', (0, 0), (-1, 0), HEADER_FILL),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]
    for i in range(1, len(data)):
        style.append(('BACKGROUND', (0, i), (-1, i),
                      colors.white if i % 2 == 1 else TABLE_STRIPE))
    tbl.setStyle(TableStyle(style))
    story.append(Spacer(1, 10))
    if caption:
        story.append(tbl)
        story.append(Paragraph(caption, S['Caption']))
    else:
        story.append(tbl)
    story.append(Spacer(1, 10))


def embed_image(path, max_width=None, max_height=None):
    from PIL import Image as PILImage
    if max_width is None:
        max_width = AVAIL_W
    if max_height is None:
        max_height = PAGE_H * 0.35
    pil = PILImage.open(path)
    ow, oh = pil.size
    ratio = min(max_width / ow if ow > max_width else 1.0,
                max_height / oh if oh > max_height else 1.0)
    return Image(path, width=ow * ratio, height=oh * ratio)


# ------------------------------------------------------------------
# 页眉页脚
# ------------------------------------------------------------------
DOC_TITLE = '基于贝叶斯图神经网络的抗MASH天然药物智能筛选 · 项目计划书'


def on_page(canvas, doc):
    canvas.saveState()
    canvas.setFont('Microsoft YaHei', 7.3)
    canvas.setFillColor(TEXT_MUTED)
    canvas.drawString(LM, PAGE_H - TM + 16, DOC_TITLE)
    canvas.setStrokeColor(ICON)
    canvas.setLineWidth(1.1)
    canvas.line(LM, PAGE_H - TM + 10, PAGE_W - RM, PAGE_H - TM + 10)
    canvas.setFont('SimHei', 7.3)
    canvas.drawString(LM, BM - 22, '中国国际大学生创新大赛（2026）· 高教主赛道本科生创意组')
    canvas.drawRightString(PAGE_W - RM, BM - 22, '第 %d 页' % doc.page)
    canvas.setStrokeColor(BORDER)
    canvas.setLineWidth(0.5)
    canvas.line(LM, BM - 14, PAGE_W - RM, BM - 14)
    canvas.restoreState()


# ------------------------------------------------------------------
# 财务预测图（matplotlib，中文字体 SimHei）
# ------------------------------------------------------------------
def make_finance_chart(path):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
    plt.rcParams['axes.unicode_minus'] = False

    years = ['2027年', '2028年', '2029年']
    service = [15, 80, 200]
    pipeline = [0, 20, 150]
    cost = [20, 70, 220]
    net = [a + b - c for a, b, c in zip(service, pipeline, cost)]

    fig, ax = plt.subplots(figsize=(7.6, 3.5), dpi=200)
    x = range(len(years))
    bw = 0.26
    b1 = ax.bar([i - bw for i in x], service, bw, color='#52798c', label='筛选服务收入')
    b2 = ax.bar(list(x), pipeline, bw, color='#93ad9e', label='管线合作收入')
    b3 = ax.bar([i + bw for i in x], cost, bw, color='#c9cdd0', label='总成本')
    ax.plot(list(x), net, color='#a63648', marker='o', linewidth=1.8, markersize=5, label='净利润')

    for bars in (b1, b2, b3):
        for rect in bars:
            h = rect.get_height()
            ax.text(rect.get_x() + rect.get_width() / 2, h + 4, '%d' % h,
                    ha='center', va='bottom', fontsize=8, color='#4a5560')
    for i, v in enumerate(net):
        ax.text(i, v - 26 if v >= 0 else v - 30, '%d' % v, ha='center', fontsize=8.5,
                color='#a63648', fontweight='bold')

    ax.set_xticks(list(x))
    ax.set_xticklabels(years, fontsize=10)
    ax.set_ylabel('金额（万元）', fontsize=9.5)
    ax.set_ylim(-60, 260)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#b8c8cf')
    ax.spines['bottom'].set_color('#b8c8cf')
    ax.tick_params(colors='#4a5560', labelsize=9)
    ax.grid(axis='y', linestyle='--', linewidth=0.5, alpha=0.35, color='#8fa9b5')
    ax.set_axisbelow(True)
    ax.legend(fontsize=8.5, frameon=False, ncol=4, loc='upper left')
    fig.tight_layout()
    fig.savefig(path, facecolor='white')
    plt.close(fig)


TMP = r"D:\zcode-workspace\.zcode\tmp"
FIN_CHART = os.path.join(TMP, 'finance_chart.png')
TECH_PNG = os.path.join(TMP, 'tech_diagram.png')
make_finance_chart(FIN_CHART)

# ==================================================================
# 正文
# ==================================================================
story = []

# ---- 目录 ----
toc = TableOfContents()
toc.levelStyles = [S['TOC1'], S['TOC2']]
story.append(Paragraph('<b>目 录</b>', S['TOCH']))
story.append(HRFlowable(width='100%', thickness=1.1, color=ICON, spaceAfter=10))
story.append(toc)
story.append(PageBreak())

# ================= 一、执行摘要 =================
h1(story, '一、执行摘要')
body(story, '代谢相关脂肪性肝炎（MASH）已成为全球最主要的慢性肝病之一，我国疾病人群规模约1.5亿，'
            '而截至2024年3月FDA加速批准首款药物Resmetirom之前，这一领域长期处于"零获批药物"的治疗空白。'
            '新药研发周期长、成本高，AI虚拟筛选本应是降本增效的关键工具，却因一个被行业长期忽视的缺陷而'
            '折戟于天然产物场景：主流模型只输出单一预测值，不提供预测的可信度，导致"高置信真活性分子"与'
            '"模型外推假阳性"严重混杂，下游湿实验验证成本大量沉没。')
body(story, '本项目源于一项已深度实施的沈阳药科大学大学生创新创业训练计划项目，将预测不确定性量化（UQ）'
            '系统性引入天然产物虚拟筛选全流程：以贝叶斯图神经网络（MC Dropout，T=50）在输出活性预测'
            '均值的同时输出方差，以可靠性图与预期校准误差（ECE）校准，以首创的置信度加权多靶点结合覆盖'
            '评分（CW-BCS）量化中药成分群的多靶点覆盖潜力。项目以不足6000元研发投入，完成了三套独立计算'
            '管线、两轮独立审计复现，并形成分层候选分子池，现正启动HepG2脂变模型湿实验验证。')
stat_row(story, [
    ('3 套', '独立计算管线已交付'),
    ('185 个', '天然产物成分完成打分'),
    ('73.9 万', 'COCONUT库记录覆盖'),
    ('100%', '关键结果独立复现审计'),
])
body(story, '商业模式采用"双轮驱动"：<b>AI筛选服务</b>面向药企、科研院所与中药企业提供附带置信度分层的'
            '虚拟筛选与报告服务，解决行业"点估计不可信"的信任赤字；<b>候选分子管线</b>以经审计的樟芝组'
            '（Antcin K、Antrodin B）、积雪草酸等候选为早期资产，按预设决策门推进湿实验验证，成熟后以'
            '授权合作方式转化。项目兼具学术诚信与方法学稀缺性——我们不仅筛选分子，更率先量化"哪些预测'
            '值得相信"，这正是AI制药走向产业可用必须补上的一课。')

# ================= 二、项目背景与市场分析 =================
h1(story, '二、项目背景与市场分析')
h2(story, '2.1 疾病负担：庞大的患者群体与治疗空白')
body(story, 'MASH（前称NASH）由脂质代谢紊乱、慢性炎症及肝纤维化共同驱动，可进展为肝硬化与肝细胞癌。'
            '公开流行病学研究（Rinella et al., 2023）显示，我国相关疾病人群规模约1.5亿，全球成人脂肪肝'
            '患病率约三成，疾病负担沉重。治疗端长期依赖生活方式干预，2024年3月FDA才加速批准首款MASH'
            '治疗药物——甲状腺激素受体β（THR-β）激动剂Resmetirom，且伴有肝毒性风险信号；FXR激动剂'
            '奥贝胆酸（OCA）处于临床III期，存在瘙痒与脂代谢异常等副作用；GLP-1类药物亦在临床探索中。'
            '单靶点强激动策略的局限日益显现，而天然小分子多靶点弱协同调控特性，为MASH治疗提供了极具'
            '潜力的互补方向。')
make_table(story,
    ['在研/已上市方案', '靶点/机制', '状态', '主要局限'],
    [
        ['Resmetirom（Rezdiffra）', 'THR-β激动剂', '2024年3月FDA获批', '肝毒性风险信号，单靶点'],
        ['奥贝胆酸（OCA）', 'FXR激动剂', '临床III期', '瘙痒、脂代谢异常'],
        ['GLP-1类药物', '胰高血糖素样肽受体', '临床探索期', '以注射为主，减重伴随'],
        ['天然产物多靶点方案', '多靶点弱协同', '无获批药物，机制分散', '缺量化筛选工具——本项目切入点'],
    ],
    [0.26, 0.20, 0.24, 0.30],
    caption='表2-1 MASH治疗格局与空白（据公开资料及项目汇报材料整理）',
    align_center_cols=[1, 2])
h2(story, '2.2 行业痛点：AI筛选的"信任赤字"')
body(story, '计算机辅助药物设计（CADD）在天然产物筛选中存在一个亟待解决的方法学瓶颈：主流QSAR/GNN模型'
            '仅输出点估计值，不提供统计置信度。其后果有三：其一，公开数据库训练集以合成小分子为主，天然'
            '产物结构多样性极高，模型陷入过度外推而点估计无法预警；其二，缺乏置信度评估导致真实活性分子与'
            '外推假阳性严重混杂，下游实验验证的沉没成本剧增；其三，传统中药信息学对成分等权评估，忽视预测'
            '置信度的客观差异，整体结论可靠性难以保证。本项目在自建管线上的实测数据直接印证了这一痛点：'
            '贝叶斯GNN在随机切分下R<super>2</super>达0.790，而在骨架隔离切分下骤降至-0.610——'
            '不诚实的评估方式会让产业界为"看似漂亮"的预测付出真金白银的实验代价。')
callout(story, '<b>我们把这一发现变成产品：</b>所有筛选结果均附三级置信标注（域内高置信 / 域内低置信 / '
               '域外预警），客户拿到的不是一份分数榜单，而是一份"哪些分子值得优先买、哪些分子只是模型'
               '想象"的实验决策依据。', ACCENT)
h2(story, '2.3 政策与产业机遇')
bullets(story, [
    '<b>健康中国战略：</b>慢性肝病防治列入国民健康行动，肝病用药自主创新属于鼓励方向；',
    '<b>中医药现代化政策：</b>国家支持用大数据、人工智能阐释中药药效物质基础，经典保肝中药的数字化筛选证据链具有稀缺性；',
    '<b>AI制药产业风口：</b>多家机构预测2030年全球MASH药物市场将达百亿美元级，上下游的早期筛选与评估服务同步扩容；',
    '<b>算力成本下探：</b>轻量化模型千元级算力即可完成训练与推理，为低成本、高周转的筛选服务模式提供了可行性基础。',
])
h2(story, '2.4 目标市场与客户画像')
make_table(story,
    ['客户 segment', '核心需求', '付费场景', '获客路径'],
    [
        ['高校/医院科研团队', '中药药效物质基础研究、论文级证据链', '定制筛选+方法学报告，单项目0.5-3万元', '学术合作、会议、导师网络'],
        ['中药/健康品企业', '经典名方二次开发、功效成分升级', '成分群多靶点评估，单项目3-15万元', '行业协会、校友渠道'],
        ['创新药企Biotech', 'MASH领域早期候选分子与评估工具', '管线授权/联合开发，里程碑付款', '竞赛曝光、产业对接会'],
    ],
    [0.22, 0.30, 0.28, 0.20],
    caption='表2-2 目标客户分层（初期以科研市场验证，中期向企业市场延展）')

# ================= 三、产品与核心技术 =================
h1(story, '三、产品与核心技术')
h2(story, '3.1 产品定位：一个平台，双轮驱动')
body(story, '项目对外交付<b>BayesScreen天然产物智能筛选服务</b>，对内沉淀<b>抗MASH候选分子管线</b>。'
            '平台以"不确定性量化"为技术内核，向上服务外部客户的筛选需求，向下持续为自研管线供给候选。'
            '当前版本以计算管线+报告交付的形式运行，SaaS化产品开发列入融资后的首要投入方向。')
img = embed_image(TECH_PNG, max_width=AVAIL_W, max_height=PAGE_H * 0.33)
story.append(Spacer(1, 6))
story.append(img)
story.append(Paragraph('图3-1 BayesScreen平台技术架构（三层九模块）', S['Caption']))
story.append(Spacer(1, 4))
h2(story, '3.2 已完成的研究进展（三套管线，全部可审计）')
make_table(story,
    ['管线', '靶点策略', '方法核心', '代表产出'],
    [
        ['V1 初始履约管线', 'FXR主靶点+THR-β/ACC对接验证', '贝叶斯GNN（MC Dropout, T=50）+CW-BCS评分', '10味保肝中药131个成分完成打分；黄连（小檗碱）计算排名第一'],
        ['V1+ 审计与落地管线', '同V1，聚焦可购买、低风险候选', '100%独立代码复现+圆桌交叉审计+V5统一评分', '剔除不可得/含肝毒风险条目，锁定樟芝组与积雪草酸为湿实验首选'],
        ['V2 独立重构管线', 'THR-β+FASN+SCD1协同轴（双队列验证）', 'XGBoost/RF集成+Butina簇划分+conformal+TOPSIS', '新10味药材54个候选完成分层排序，全部标注适用域状态'],
    ],
    [0.16, 0.24, 0.28, 0.32],
    caption='表3-1 三套计算管线研究进展（均保留代码、数据与审计链）')
h2(story, '3.3 核心技术指标')
stat_row(story, [
    ('0.790 / -0.610', '随机/骨架切分R<super>2</super>（方法学警示）'),
    ('0.843', 'V2 THR-β簇切分R<super>2</super>'),
    ('RMSD<2 Å', '共晶配体对接姿势恢复'),
    ('T=50', 'MC Dropout前向传播次数'),
])
make_table(story,
    ['模型', '随机切分R<super>2</super>', '骨架切分R<super>2</super>', '项目解读'],
    [
        ['贝叶斯GNN（BGNN）', '0.790', '-0.610', '随机集表现不等于新骨架外推能力，UQ成为必需品'],
        ['随机森林（RF）', '0.845', '0.047', '点预测基线中较稳健者'],
        ['XGBoost', '0.811', '-0.127', '同样发生明显骨架退化'],
    ],
    [0.22, 0.16, 0.16, 0.46],
    caption='表3-2 V1双划分模型表现（FXR池化活性端点）',
    align_center_cols=[1, 2])
body(story, 'V2独立重构管线采用更严格的簇切分评估，THR-β模型簇切分R<super>2</super>达0.843'
            '（RMSE 0.442，Spearman 0.895），FASN与SCD1分别为0.651与0.651；54个天然产物候选经'
            'Tanimoto域评分判定后，39个为边缘层、15个为域外，团队据此将全部候选诚实标注为'
            '"假设生成级"——这一定级策略本身即构成对外服务的差异化卖点：我们拒绝用不确定的预测'
            '透支客户信任。')
h2(story, '3.4 核心创新点')
bullets(story, [
    '<b>不确定性量化（UQ）全流程植入：</b>MC Dropout输出μ±σ，可靠性图与ECE校准，筛选结果具备统计学置信度分层，显著降低无意义实验验证成本；',
    '<b>首创CW-BCS置信度加权多靶点结合覆盖评分：</b>以w=1/(1+σ)对成分贡献赋权，融合GNN预测与Vina对接代理评分，量化中药成分群多靶点覆盖潜力，衔接CADD与中医药计算体系；',
    '<b>双层适用域预警机制：</b>2D描述符PCA/Leverage线性过滤与深度模型非线性方差分级相结合，"域外剔除+域内分级"阶梯式预警；',
    '<b>骨架外推诚实评估范式：</b>以Butina簇划分替代随机切分考察化学骨架外推能力，并以split conformal给出预测区间，把"模型何时可信"变成可交付指标；',
    '<b>GNNExplainer可解释性：</b>提取关键原子子图解析药效团，使计算预测能与中药传统功效相互印证。',
])
h2(story, '3.5 湿实验验证进展与候选分子管线')
body(story, '平台输出的候选已进入湿实验落地通道。依据"计算高分+独立文献/临床双链印证+市场可购高纯度'
            '标准品"三重门控，首批进入HepG2 PA/OA脂变模型验证的候选如下：')
make_table(story,
    ['候选成分', '来源药材', '入选依据（证据链）', '管线定位'],
    [
        ['Antcin K / Antrodin B', '樟芝', '物种/制剂级临床RCT信息+双异源计算交叉印证', '优先实验假设A'],
        ['Asiatic acid（积雪草酸）', '积雪草', '外部抗纤维化文献线索，商业化充分', '优先实验假设A'],
        ['Berberine（小檗碱）', '黄连', 'V1计算第一，已知活性锚点', '阳性对照'],
        ['Lovastatin（洛伐他汀）', '标准药', '工业界经典降脂阳性对照', '阳性对照'],
    ],
    [0.24, 0.12, 0.40, 0.24],
    caption='表3-3 首批湿实验候选（浓度梯度0.1-30 μM，主读出细胞内TG）',
    align_center_cols=[1, 3])
body(story, '预设hit标准：相对模型组TG下降不低于30%、最低有效浓度不高于10 μM时细胞活力不低于80%，'
            '双红线同步满足方判定为hit；任何伴随明显细胞损失的"脂质改善"一律不予推进。阶段2将对命中物'
            '开展独立批次复现与qPCR机制模块检测，阶段3进入TGF-β激活的LX-2肝星状细胞纤维化模型，'
            '阶段4的AMLN小鼠体内验证规划为外部合作项目。')
h2(story, '3.6 知识产权与成果规划')
make_table(story,
    ['类型', '现状', '规划（12个月内）'],
    [
        ['软件著作权', 'BayesScreen筛选管线代码库（V1/V1+/V2，含审计链）已固化', '提交2-3项软著申请（筛选管线/CW-BCS评分引擎/置信度报告生成器）'],
        ['学术论文', '方法学结论与管线审计报告已成稿', '投稿1篇（AI药学/中药信息学方向期刊或会议）'],
        ['发明专利', '暂无', '结合湿实验hit数据，布局"置信度加权多靶点筛选方法"专利申请'],
        ['数据资产', '20味药材185成分结构化数据库+评分结果集', '持续扩充并形成中药多靶点覆盖数据库产品'],
    ],
    [0.16, 0.42, 0.42],
    caption='表3-4 知识产权布局（真实披露：暂无已授权专利，全部为进行中规划）')

# ================= 四、商业模式 =================
h1(story, '四、商业模式')
h2(story, '4.1 业务模式：服务现金流 + 管线增值')
body(story, '<b>引擎一（AI筛选服务）：</b>以项目制定制筛选切入，交付"候选分子+三级置信标注+实验优先级'
            '建议+可解释性报告"的组合物。相较传统CRO只给分数榜单，我们的交付物直接回答"下一步买哪几个'
            '分子、先做哪个实验"，客单价虽低但决策价值密度高，适合科研市场快速起量并沉淀口碑。')
body(story, '<b>引擎二（候选分子管线）：</b>自研抗MASH天然候选管线按决策门分层推进，每通过一个验证'
            '阶段（脂变hit→机制方向→纤维化模型），资产价值显著抬升。中期以授权、联合开发或里程碑付款'
            '方式与药企/健康品企业合作，不追求自建重资产临床团队。')
h2(story, '4.2 盈利模式与定价')
make_table(story,
    ['收入线', '定价（元/项目）', '交付物', '边际成本结构'],
    [
        ['高校科研定制筛选', '5,000-30,000', '候选清单+置信分层+报告', '算力与人力，毛利约70%'],
        ['企业成分群评估（CW-BCS）', '30,000-150,000', '多靶点覆盖评分+药效团解析', '算力+专家复核，毛利约65%'],
        ['管线授权/联合开发', '里程碑付款制', '候选分子资产+数据包', '湿实验投入前置'],
        ['数据库订阅（远期）', '按年订阅', '中药多靶点覆盖数据库', '近零边际成本'],
    ],
    [0.26, 0.18, 0.30, 0.26],
    caption='表4-1 收入结构与定价（创意组阶段以验证为主，价格为规划口径）',
    align_center_cols=[1])
h2(story, '4.3 客户获取与合作伙伴')
bullets(story, [
    '<b>学术背书路径：</b>以论文、学术会议报告与开源方法学工具建立"置信度筛选"标签，吸引高校科研团队合作；',
    '<b>指导教师与院校网络：</b>依托沈阳药科大学在药学领域的产业联系，对接中药企业二次开发需求；',
    '<b>赛事与孵化资源：</b>以中国国际大学生创新大赛为起点，衔接校创新创业学院孵化资源与产业导师；',
    '<b>标杆案例策略：</b>首批3-5个高校项目以成本价换取可公开案例与推荐信，形成销售素材库。',
])

# ================= 五、市场营销与竞争策略 =================
h1(story, '五、市场营销与竞争策略')
h2(story, '5.1 竞争分析')
make_table(story,
    ['竞争者类型', '代表', '优势', '短板（我们的机会）'],
    [
        ['国际CADD软件巨头', 'Schrödinger等', '物理引擎深、品牌强', 'license昂贵，天然产物/中药场景与置信度分层非其重心'],
        ['国内CRO虚拟筛选服务', '各类外包服务商', '流程成熟、交付快', '输出以点估计分数为主，无法回答"预测可信度"'],
        ['自建AI团队的大药企', '内部AI部门', '数据与资金雄厚', '聚焦自研管线，中小机构难以复用其能力'],
    ],
    [0.20, 0.16, 0.22, 0.42],
    caption='表5-1 竞争格局：以"置信度+中药场景+极低成本"错位竞争')
h2(story, '5.2 差异化定位与营销节奏')
body(story, '我们不与巨头拼算力与物理引擎深度，而是占据"天然产物场景+置信度交付+轻量化成本"的错位'
            '生态位。营销节奏三步走：第一年以学术圈层渗透（论文+开源+会议工作坊）建立方法学声誉；第二年'
            '以标杆案例切入企业市场，形成3-5个可引用的商业案例；第三年沉淀数据库订阅与SaaS入口，'
            '将一次性项目收入转化为持续性收入。')

# ================= 六、团队介绍 =================
h1(story, '六、团队介绍')
h2(story, '6.1 核心团队')
make_table(story,
    ['成员', '角色', '分工'],
    [
        ['王启龙', '项目负责人', '研究总体规划、贝叶斯GNN建模与CW-BCS评分体系实现、对外答辩'],
        ['衣思淼', '数据与靶点组', 'GEO转录组分析、靶点确证、活性数据清洗与适用域过滤'],
        ['代维斯丹', '计算平台组', '分子对接（AutoDock Vina/PyMOL）、管线工程化与代码审计'],
        ['宁显泷', '候选治理组', '候选可得性与安全性排查、证据分层与文档管理'],
        ['王散曼', '实验转化组', 'HepG2脂变模型湿实验执行、数据统计与可视化'],
    ],
    [0.14, 0.20, 0.66],
    caption='表6-1 核心团队分工（5人均为项目实际核心成员）',
    align_center_cols=[0, 1])
body(story, '团队专业覆盖药学、生物医学工程与中药学，形成"药理机制把控—不确定性量化算法—中医药解读"'
            '的完整闭环。项目最难得的资产是团队已经历了真实科研的全部残酷环节：建模、崩溃、审计、重构，'
            '并在每一轮留下了可追溯的代码与报告。')
h2(story, '6.2 指导教师')
body(story, '指导教师姜希伟（医疗器械学院），具备数理统计与生物信息学背景，自大创立项起全程指导技术路线'
            '与学术规范，将继续为公司的科学顾问委员会提供方法学把关，并协助对接院校产业资源。')

# ================= 七、财务分析与融资计划 =================
h1(story, '七、财务分析与融资计划')
h2(story, '7.1 已投入成本（极致人效比的证明）')
body(story, '项目至今的干实验研发依托大创专项经费4000元预算完成（GPU算力约1000元、数据资料与'
            '耗材约3000元），湿实验启动预算1500元。以不足6000元现金投入，产出三套管线、185个成分'
            '打分、两轮独立审计与一套方法学发现——单位经费的科研产出密度，正是轻量化AI筛选模式商业'
            '可行性的最好证明。')
stat_row(story, [
    ('<0.6 万元', '累计现金研发投入'),
    ('3 套', '交付管线'),
    ('100%', '关键结果独立复现通过'),
])
h2(story, '7.2 三年财务预测（规划口径）')
img2 = embed_image(FIN_CHART, max_width=AVAIL_W, max_height=PAGE_H * 0.30)
story.append(Spacer(1, 6))
story.append(img2)
story.append(Paragraph('图7-1 三年财务预测（万元，创意组阶段预测，用于说明商业逻辑而非承诺）', S['Caption']))
make_table(story,
    ['项目', '2027年', '2028年', '2029年'],
    [
        ['筛选服务收入', '15', '80', '200'],
        ['管线合作收入', '0', '20', '150'],
        ['收入合计', '15', '100', '350'],
        ['总成本（人力/算力/实验）', '20', '70', '220'],
        ['净利润', '-5', '30', '130'],
    ],
    [0.40, 0.20, 0.20, 0.20],
    caption='表7-1 利润预测简表（万元）',
    align_center_cols=[1, 2, 3])
body(story, '预测假设：2027年以5-8个高校科研项目验证交付（平均客单价约2万元）；2028年进入企业市场'
            '并完成首个管线小额授权；2029年数据库订阅上线、管线授权规模化。人力成本按学生团队向专职'
            '团队过渡的混合结构估算。')
h2(story, '7.3 融资计划与资金用途')
body(story, '项目当前处于本科生创意组阶段，未注册公司。计划在湿实验hit数据落地后（预计2027年上半年）'
            '注册公司，并引入种子轮融资<b>50万元</b>，资金用途规划如下：')
make_table(story,
    ['用途', '金额（万元）', '占比', '说明'],
    [
        ['平台产品化与软著/专利', '20', '40%', '筛选管线SaaS化、报告引擎开发、IP布局'],
        ['湿实验验证', '18', '36%', '命中复验、机制方向验证、纤维化模型'],
        ['市场与运营', '12', '24%', '标杆案例打造、会议推广、注册及法务'],
    ],
    [0.28, 0.16, 0.12, 0.44],
    caption='表7-2 种子轮资金用途（规划）',
    align_center_cols=[1, 2])

# ================= 八、风险分析与应对 =================
h1(story, '八、风险分析与应对')
make_table(story,
    ['风险类别', '风险描述', '应对策略'],
    [
        ['技术风险', '天然产物处于训练集化学空间之外，预测可靠性受限', '这正是本项目的核心认知：全部交付附置信分层与域外预警；以骨架切分+conformal诚实评估，拒绝过度承诺'],
        ['实验风险', '候选未达预设hit标准（TG降幅或活力红线）', '分层候选池+预设go/no-go决策门；小檗碱/洛伐他汀双阳性对照锚定体系有效性；未命中即止损转向'],
        ['市场风险', '药企对AI筛选外包接受度与付费意愿不确定', '先以付费意愿明确的高校科研市场验证现金流；以学术声誉降低企业市场教育成本'],
        ['政策/合规风险', '天然药物转化路径长、监管要求高', '服务收入为主对冲管线周期；数据全部来自公开数据库（GEO/ChEMBL/COCONUT/TCMSP）并遵守相应许可'],
        ['团队风险', '本科生毕业导致人员更替', '代码与数据全量文档化、审计链可交接；指导教师保证学术延续；以股权/署名机制绑定核心成员'],
    ],
    [0.13, 0.30, 0.57],
    caption='表8-1 风险矩阵与应对')

# ================= 九、社会价值与发展规划 =================
h1(story, '九、社会价值与发展规划')
h2(story, '9.1 社会价值')
bullets(story, [
    '<b>服务健康中国：</b>面向1.5亿量级的脂肪肝疾病人群，为更安全、可及的MASH干预方案提供早期候选与方法学工具；',
    '<b>推动中医药现代化：</b>为经典保肝中药建立"成分-靶点-置信度"的可解释计算证据链，让传统功效获得数字化表达；',
    '<b>降低创新门槛：</b>千元级算力即可运行的轻量化管线，让中小机构与青年研究者也能参与高水平的药物发现；',
    '<b>树立科研诚信范式：</b>全流程可审计、负面结果如实披露（骨架外推失效的发现与公开），为AI制药建立"可信AI"的实践样本；',
    '<b>带动就业与人才培养：</b>规划3年内提供8-12个研发与运营岗位，并以项目制持续训练交叉学科本科生。',
])
h2(story, '9.2 发展里程碑')
make_table(story,
    ['时间', '里程碑', '关键交付/判定标准'],
    [
        ['2026年9月', '国创赛报名与校赛', '项目计划书、汇报材料提交'],
        ['2026年10-12月', 'HepG2脂变初筛（阶段1）', '首批4个标准品完成门控+梯度给药，输出hit/非hit判定'],
        ['2027年3-5月', '命中复验与机制验证（阶段2）', '独立批次复现+qPCR机制线索；大创结题'],
        ['2027年上半年', '注册公司、软著落地、论文投稿', '2-3项软著受理、1篇论文投出'],
        ['2027年下半年', '种子轮融资、平台SaaS化开发', '完成50万元融资，MVP上线'],
        ['2028年', '企业市场突破与首个管线授权', '3-5个商业案例、首笔管线里程碑收款'],
        ['2029年', '数据库订阅与规模化', '订阅制收入上线，现金流为正'],
    ],
    [0.18, 0.34, 0.48],
    caption='表9-1 发展里程碑（含预设决策门，未达标即按止损规则调整）',
    align_center_cols=[0])

# ================= 附录 =================
h1(story, '附录：证据边界与合规声明')
body(story, '本项目秉持学术诚信原则，对研究结论的证据边界作如下声明：')
bullets(story, [
    '截至本计划书撰写日，项目所有候选分子均处于"计算优先级假设"层级，尚无直接、已完成的抗MASH湿实验疗效证据；',
    '樟芝相关信息属于物种/制剂级临床证据，不构成单体分子（Antcin K、Antrodin B等）的疗效证明；',
    'V2管线54个候选经适用域评定为边缘层或域外，其排序结论为"假设生成级"，均已如实标注；',
    '随机切分与骨架切分的表现差异、不同校准口径下的覆盖率差异等负面结果，均在内部审计报告中如实保留；',
    '全部数据来自公开数据库（GEO、ChEMBL、COCONUT、TCMSP），遵守相应数据许可条款；未重跑或篡改任何原始研究文件；',
    '财务预测为创意组阶段的规划口径，用于说明商业逻辑，不构成业绩承诺。',
])
story.append(Spacer(1, 10))
story.append(Paragraph('—— 全文完 ——', ParagraphStyle(
    'End', fontName='Microsoft YaHei', fontSize=10, leading=15,
    textColor=TEXT_MUTED, alignment=TA_CENTER)))

# ------------------------------------------------------------------
# 构建
# ------------------------------------------------------------------
OUT_BODY = os.path.join(TMP, 'gc_bp_body.pdf')
doc = TocDocTemplate(
    OUT_BODY, pagesize=A4,
    leftMargin=LM, rightMargin=RM, topMargin=TM, bottomMargin=BM,
    title=DOC_TITLE, author='Z.ai', creator='Z.ai',
    subject='中国国际大学生创新大赛项目计划书',
)
doc.multiBuild(story, onFirstPage=on_page, onLaterPages=on_page)
print('body pages ->', doc.page)
print('saved:', OUT_BODY)
