import markdown
import os

try:
    from weasyprint import HTML
except ImportError:
    HTML = None
    print("weasyprint not found, trying fpdf2")

md_text = """
# 大创项目全流程综合结题分析报告 (Comprehensive Analysis Report)

**生成日期**: 2026-08-24
**分析对象**: 本大创项目全生命周期内的所有工作区文件(包含V1、V2、V3、圆桌审计等全阶段)

---

## 〇、执行摘要 (Executive Summary)

本大创项目完整经历了从“**初次探索 (V1)**”到“**代码与数据独立审计 (V3)**”，再到“**方法学推倒重构 (V2)**”的真实、高质量的科研闭环。
项目最杰出的科研价值不仅在于“筛出了几个候选药物”，而在于**真实地发现了AI在预测天然产物时存在的“适用域外推失效”现象，并以此为契机完成了计算管线的全面进化**。

---

## 一、项目演进全景与三套具体流程 (Full Timeline & Specific Workflows)

整个工作区的数据和报告，实际上映射了项目在不同认知阶段建立的三条独立管线：

### 管线一：初始履约管线（V1 方案，文件夹：`mash_research`）
*   **研发目的**：完成立项申报书中承诺的基于图神经网络的筛选任务。
*   **具体流程**：
    *   **疾病模块与靶点**：基于GEO (GSE135251) 数据，锁定单一核受体 **FXR (NR1H4)** 为主靶点。
    *   **化合物库**：10味经典保肝中药，解析出 **131** 个化学成分。
    *   **算法模型**：**贝叶斯图神经网络 (BGNN)**，结合异方差NLL与MC Dropout进行不确定性量化。
    *   **筛选机制**：首创 CW-BCS (置信度加权结合覆盖评分) 体系，进行绝对分数排名。
*   **独立结论**：计算得出**黄连（及其成分小檗碱/表小檗碱）**综合排名第一。
*   **局限性暴露**：在圆桌审议中发现，深度学习模型对天然产物出现了严重的“过拟合”与“骨架崩塌” (外推R²降至-0.61)，且黄连等候选物的购买可行性/药代动力学存在隐患。

### 管线二：第三方审计与湿实验落地管线（V1+ 方案，文件夹：`verify_repro`, `roundtable`）
*   **研发目的**：为确保学术诚信，对V1进行代码重写复算；同时为了指导真实的1500元湿实验采购，对候选物进行落地清洗。
*   **具体流程**：
    *   **100% 独立复现**：通过全新的Python与MATLAB脚本，重做了V1的T检验、ChEMBL过滤、杠杆值计算等，**证明了V1所有计算结果与底层数据100%真实吻合，无任何数据造假**。
    *   **严苛的人工修正**：剔除了无商品化供应的分子、剔除了含肝毒性(PA)的千里光，引入“临床/机制文献直证”双链逻辑，最终形成“V5 Unified Score”。
*   **独立结论**：排除了黄连等纯计算产物，最终锁定 **樟芝群（Antcin K等）** 与 **积雪草（asiatic acid）** 为可以直接投入HepG2脂变湿实验的首选安全对象。

### 管线三：完全独立重构的新方法管线（V2 方案，文件夹：`mash_v2_new`）
*   **研发目的**：吸收前期所有教训，摒弃容易过拟合的模型与单一靶点，做一次真正符合顶级学术逻辑的推倒重来 (即您最后看到的PDF可视化报告)。
*   **具体流程**：
    *   **靶点组合升级**：转向国际最新前沿，采用 **THRβ(激动) + FASN(抑制) + SCD1(抑制)** 协同调控轴（由双队列GSE48452+GSE63067独立验证）。
    *   **算法回归鲁棒性**：弃用深度神经网络，改用 **XGBoost/Random Forest (随机森林)** 集成模型 + Morgan指纹，防止过拟合。
    *   **化合物库换血**：全新引入另外10味文献驱动的药材（葛根、山楂等），提取出 **54** 个完全不同的化合物。
    *   **评估与排序体系**：引入 Butina 聚类，强行考察化学骨架发现能力；采用运筹学成熟的 **TOPSIS 多准则决策系统** 进行全面排序。
*   **独立结论**：
    *   筛选出 **葛根（3'-甲氧基大豆黄素）、山楂、茵陈** 为最高优候选。
    *   **最核心的科学贡献**：报告以极为诚实的态度证明，54个分子全部在已知训练集的空间之外(最大相似度仅0.29)，因此所有预测结果被主动降级为 **"假设生成级 (Hypothesis-generating)"**，拒绝夸大宣传。

*(注：期间曾短暂探索过生物药如FGF21和海洋真菌冷门分子，但均因“缺乏冷门生态位”和“本科生无法购买/合成”而被务实地否决。)*

---

## 二、三套方法结果为何不同？(核心区别对照)

为什么折腾了三遍，得出的药物都不一样？这正是AI筛选的特征——**输入不同的生物学假设和搜索空间，必然得出不同的结果**。

| 维度 | V1（初始计算路线） | V1+（圆桌审计落地路线） | V2（全新重做路线 / PDF） |
| :--- | :--- | :--- | :--- |
| **生物学靶点 (锁)** | FXR 单一核受体 | FXR 单一核受体 | THRβ + FASN + SCD1 协同轴 |
| **中药筛选库 (钥匙)**| 第一批10味经典药(131分子)| 第一批中排查出的可购买分子| 第二批全新10味药(54分子) |
| **筛选与评估算法** | 贝叶斯 GNN 预测 | 算法同上 + 人工现实过滤 | XGB/RF集成 + TOPSIS排序 |
| **最终候选 (Result)**| **黄连（小檗碱）** | **樟芝、积雪草** | **葛根、山楂、茵陈** |

**结论**：这三个结果**互相不矛盾**。黄连是FXR路线的最佳计算结果；樟芝是该路线下最稳妥的可购买实验对象；而葛根/山楂则是全新的多靶点路线下的最优解。

---

## 三、结题报告的终极撰写建议 (How to Close the Project)

基于上述全景分析，建议您按以下结构组织结题材料，将使该项目的科研深度超越普通的大创水准：

1.  **【主要工作交付】第一章：计算与模型构建 (V1)**
    *   汇报你们如何搭建了复杂的BGNN模型，筛选了131个中药成分。
    *   **提交交付物**：黄连/苦参排名的原表（证明代码跑通了，任务完成了）。
2.  **【实验落地设计】第二章：模型审计与湿实验规划 (V1+)**
    *   汇报你们为了严谨起见，不仅自己对代码做了100%复现，还对结果进行了采购排查。
    *   **提交交付物**：以樟芝/积雪草为主的、预算在1500元以内的HepG2脂变模型实验计划（展示你们能将干实验落地为湿实验的能力）。
3.  **【亮点与升华】第三章：方法学的反思与重构 (V2)**
    *   在最后把那份 **PDF可视化报告 (葛根/山楂/茵陈)** 亮出来，作为项目的**“超预期延伸成果 (Bonus)”**。
    *   **升华话术**：“通过一年的探索，我们深刻认识到了AI预测天然产物的痛点（适用域外推失效）。因此在结题前，我们自发推倒重来，构建了一套靶点更新、不确定性披露更严苛的V2管线。尽管时间有限，但这套体系为该领域的后续研究建立了标杆。”

"""

html_template = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    body {{ font-family: "SimSun", "Microsoft YaHei", sans-serif; line-height: 1.6; color: #333; margin: 40px; }}
    h1 {{ color: #2c3e50; text-align: center; border-bottom: 2px solid #3498db; padding-bottom: 10px; font-size: 24px;}}
    h2 {{ color: #2980b9; margin-top: 30px; border-bottom: 1px solid #eee; padding-bottom: 5px; font-size: 18px;}}
    h3 {{ color: #16a085; font-size: 16px;}}
    table {{ border-collapse: collapse; width: 100%; margin: 20px 0; font-size: 12px; }}
    th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
    th {{ background-color: #f8f9fa; color: #2c3e50; }}
    ul, ol {{ margin-left: 20px; font-size: 14px;}}
    p {{ font-size: 14px;}}
    strong {{ color: #e74c3c; }}
    em {{ color: #7f8c8d; font-style: normal; }}
</style>
</head>
<body>
{markdown.markdown(md_text, extensions=['tables'])}
</body>
</html>
"""

with open("D:/zcode-workspace/temp.html", "w", encoding="utf-8") as f:
    f.write(html_template)

if HTML is not None:
    try:
        HTML("D:/zcode-workspace/temp.html").write_pdf("D:/zcode-workspace/大创全流程综合结题分析报告.pdf")
        print("PDF successfully generated at D:/zcode-workspace/大创全流程综合结题分析报告.pdf using WeasyPrint")
    except Exception as e:
        print(f"Weasyprint error: {e}")
else:
    print("Could not generate PDF, weasyprint module not working.")

