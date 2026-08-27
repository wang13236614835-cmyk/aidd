import os
from fpdf import FPDF
import textwrap

md_text = """大创项目全流程综合结题分析报告 (Comprehensive Analysis Report)

生成日期: 2026-08-24
分析对象: 本大创项目全生命周期内的所有工作区文件(包含V1、V2、V3、圆桌审计等全阶段)

---

〇、执行摘要 (Executive Summary)

本大创项目完整经历了从“初次探索 (V1)”到“代码与数据独立审计 (V3)”，再到“方法学推倒重构 (V2)”的真实、高质量的科研闭环。项目最杰出的科研价值不仅在于“筛出了几个候选药物”，而在于真实地发现了AI在预测天然产物时存在的“适用域外推失效”现象，并以此为契机完成了计算管线的全面进化。

---

一、项目演进全景与三套具体流程 (Full Timeline & Specific Workflows)

整个工作区的数据和报告，实际上映射了项目在不同认知阶段建立的三条独立管线：

【管线一：初始履约管线（V1 方案，文件夹：mash_research）】
* 研发目的：完成立项申报书中承诺的基于图神经网络的筛选任务。
* 具体流程：
  - 疾病模块与靶点：基于GEO(GSE135251)数据，锁定单一核受体FXR(NR1H4)为主靶点。
  - 化合物库：10味经典保肝中药，解析出131个化学成分。
  - 算法模型：贝叶斯图神经网络(BGNN)，结合异方差NLL与MC Dropout进行不确定性量化。
  - 筛选机制：首创CW-BCS体系，进行绝对分数排名。
* 独立结论：计算得出黄连（及其成分小檗碱/表小檗碱）综合排名第一。
* 局限性暴露：在圆桌审议中发现，深度学习模型对天然产物出现了严重的“过拟合”与“骨架崩塌”(外推R2降至-0.61)，且黄连等候选物的购买可行性存在隐患。

【管线二：第三方审计与湿实验落地管线（V1+ 方案，文件夹：verify_repro, roundtable）】
* 研发目的：为确保学术诚信，对V1进行代码重写复算；同时为了指导真实的1500元湿实验采购，对候选物进行落地清洗。
* 具体流程：
  - 100%独立复现：通过全新的Python与MATLAB脚本，重做了V1的T检验、ChEMBL过滤等，证明了V1所有计算结果与底层数据100%真实吻合，无任何数据造假。
  - 严苛的人工修正：剔除了无商品化供应的分子、含肝毒性(PA)的千里光，引入“临床/机制文献直证”双链逻辑。
* 独立结论：排除了黄连等纯计算产物，最终锁定 樟芝群（Antcin K等）与 积雪草（asiatic acid）为可以直接投入HepG2脂变湿实验的首选安全对象。

【管线三：完全独立重构的新方法管线（V2 方案，文件夹：mash_v2_new）】
* 研发目的：吸收前期所有教训，做一次真正符合顶级学术逻辑的推倒重来(即最终的PDF可视化报告)。
* 具体流程：
  - 靶点组合升级：转向国际最新前沿，采用 THRβ(激动) + FASN(抑制) + SCD1(抑制)协同调控轴。
  - 算法回归鲁棒性：改用 XGBoost/Random Forest(随机森林)集成模型 + Morgan指纹，防止过拟合。
  - 化合物库换血：全新引入另外10味文献驱动的药材，提取出54个完全不同的化合物。
  - 评估与排序体系：引入Butina聚类强行考察骨架发现能力；采用TOPSIS多准则决策系统全面排序。
* 独立结论：
  - 筛选出葛根（3'-甲氧基大豆黄素）、山楂、茵陈为最高优候选。
  - 最核心科学贡献：以极为诚实的态度证明，54个分子全部在已知训练集适用域之外，所有预测结果主动降级为"假设生成级(Hypothesis-generating)"。

*(注：期间曾短暂探索过生物药如FGF21和海洋真菌分子，但因"缺乏冷门生态位"和"本科生无法获取"被务实否决。)*

---

二、三套方法结果为何不同？(核心区别对照)

为什么得出药物不同？因为AI输入不同的生物学假设和搜索空间，必然得出不同的结果。

* 生物学靶点(锁)：V1/V1+是FXR单靶点；V2是THRβ+FASN+SCD1协同轴。
* 中药筛选库(钥匙)：V1/V1+是第一批131分子；V2是全新的54个不同分子。
* 算法与评估：V1是GNN预测；V1+是人工可购买性过滤；V2是XGB/RF集成与TOPSIS排序。
* 最终结果：V1是黄连(计算第一)；V1+是樟芝(最可落地)；V2是葛根/山楂(新轴潜力)。

结论：这三个结果互相不矛盾。黄连是FXR路线的最佳计算结果；樟芝是该路线下最稳妥的可购买实验对象；而葛根/山楂则是全新的多靶点路线下的最优解。

---

三、结题报告的终极撰写建议 (How to Close the Project)

基于上述全景分析，建议您按以下结构组织结题材料，将使该项目的科研深度超越普通大创：

1. 【主要工作交付】第一章：计算与模型构建 (V1)
   汇报如何搭建BGNN模型并筛选131个中药成分。提交黄连/苦参排名的原表（证明代码跑通）。
2. 【实验落地设计】第二章：模型审计与湿实验规划 (V1+)
   汇报自我审计过程与采购排查。提交以樟芝/积雪草为主的HepG2实验计划（展示干实验落地能力）。
3. 【亮点与升华】第三章：方法学的反思与重构 (V2)
   展示PDF可视化报告(葛根/山楂)，作为项目的"超预期延伸成果(Bonus)"。
   升华话术：“通过探索，我们深刻认识到AI预测天然产物的痛点(适用域外推失效)。我们在结题前自发重构了靶点更新、风险披露更严苛的V2管线，为后续研究建立了标杆。”
"""

class PDF(FPDF):
    def header(self):
        self.set_font("helvetica", "B", 15)
        self.cell(0, 10, "Comprehensive Final Analysis Report", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")

pdf = PDF()
pdf.add_page()

# FPDF requires a unicode font for Chinese. 
# We'll try to find a default windows font.
font_path = "C:/Windows/Fonts/msyh.ttc"
if not os.path.exists(font_path):
    font_path = "C:/Windows/Fonts/simhei.ttf"

if os.path.exists(font_path):
    pdf.add_font("msyh", "", font_path, uni=True)
    pdf.set_font("msyh", "", 11)
else:
    print("Chinese font not found. Please ensure a valid font exists.")
    pdf.set_font("helvetica", "", 11)

for line in md_text.split('\n'):
    if line.startswith("# ") or line.startswith("---") or line.startswith("〇、") or line.startswith("一、") or line.startswith("二、") or line.startswith("三、"):
        pdf.set_font("msyh", "", 13)
        pdf.multi_cell(0, 8, txt=line)
        pdf.set_font("msyh", "", 11)
    else:
        pdf.multi_cell(0, 6, txt=line)

pdf_file = "D:/zcode-workspace/大创结题综合指导报告.pdf"
pdf.output(pdf_file)
print(f"PDF generated successfully at {pdf_file}")
