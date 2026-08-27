// -*- coding: utf-8 -*-
// 暑假中间报告 Word 生成（R5学术封面 + TOC + 7章正文）
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, ImageRun,
  PageBreak, Header, Footer, PageNumber, NumberFormat, AlignmentType,
  HeadingLevel, WidthType, BorderStyle, ShadingType, TableLayoutType,
  TableOfContents, VerticalAlign,
} = require("docx");
const fs = require("fs");

const NB = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
const noBorders = { top: NB, bottom: NB, left: NB, right: NB };
const allNoBorders = { top: NB, bottom: NB, left: NB, right: NB,
                       insideHorizontal: NB, insideVertical: NB };

// ---------- R5 helpers ----------
function calcTitleLayout(lines, pt) { return { titlePt: pt, titleLines: lines }; }

function calcR5MetaLayout(metaEntries, fontPt = 12) {
  const maxLabelLen = Math.max(...metaEntries.map(e => [...e.label].length));
  const labelNeedTw = (maxLabelLen + 2) * fontPt * 20;
  const totalNeedTw = labelNeedTw + 5000;
  const tablePct = Math.min(75, Math.max(55, Math.ceil(totalNeedTw / 11906 * 100)));
  const rawLabelPct = Math.ceil(labelNeedTw / (tablePct / 100 * 11906) * 100);
  return { tablePct, labelPct: Math.max(25, Math.min(45, rawLabelPct)) };
}
function buildR5MetaTable(metaEntries) {
  const { tablePct, labelPct } = calcR5MetaLayout(metaEntries);
  const valuePct = 100 - labelPct;
  const bottomBorder = { style: BorderStyle.SINGLE, size: 4, color: "000000" };
  const rows = metaEntries.map(entry => new TableRow({
    cantSplit: true,
    children: [
      new TableCell({
        width: { size: labelPct, type: WidthType.PERCENTAGE },
        borders: noBorders,
        margins: { top: 60, bottom: 60, left: 0, right: 0 },
        children: [new Paragraph({
          alignment: AlignmentType.LEFT,
          spacing: { before: 60, after: 60, line: 400 },
          children: [new TextRun({ text: entry.label + "\uFF1A", size: 24,
            font: { eastAsia: "SimSun", ascii: "Times New Roman" } })],
        })],
      }),
      new TableCell({
        width: { size: valuePct, type: WidthType.PERCENTAGE },
        borders: { top: NB, left: NB, right: NB, bottom: bottomBorder },
        margins: { top: 60, bottom: 60, left: 80, right: 0 },
        children: [new Paragraph({
          alignment: AlignmentType.LEFT,
          spacing: { before: 60, after: 60, line: 400 },
          children: [new TextRun({ text: entry.value, size: 24,
            font: { eastAsia: "SimSun", ascii: "Times New Roman" } })],
        })],
      }),
    ],
  }));
  return new Table({
    width: { size: tablePct, type: WidthType.PERCENTAGE },
    alignment: AlignmentType.CENTER,
    layout: TableLayoutType.FIXED,
    borders: allNoBorders,
    rows,
  });
}
function buildCoverR5(config) {
  const PAGE_H = 16838, simMarginLR = 1701, simMarginT = 1200;
  const { titlePt, titleLines } = calcTitleLayout(config.titleLines, config.titlePt || 32);
  const titleSize = titlePt * 2;
  const metaEntries = (config.metaLines || []).map(line => {
    const sep = line.indexOf("\uFF1A") !== -1 ? "\uFF1A" : ":";
    const idx = line.indexOf(sep);
    if (idx === -1) return { label: line, value: "" };
    return { label: line.slice(0, idx).trim(), value: line.slice(idx + sep.length).trim() };
  });
  const schoolNameH = config.schoolName ? (22 * 23 + 400) : 0;
  const titleTotalH = titleLines.length * (titlePt * 23 + 200);
  const subtitleH = config.subtitle ? (15 * 23 + 600) : 0;
  const metaTableH = metaEntries.length * 520;
  const footerH = config.footerRight ? (12 * 23 + 200) : 0;
  const fixedH = schoolNameH + titleTotalH + subtitleH + metaTableH + footerH + 3 * 350;
  const remaining = Math.max(15638 - fixedH, 600);
  const topSpacing = Math.min(Math.floor(remaining * 0.28) + simMarginT, 4200);
  const midSpacing = Math.min(Math.floor((remaining - simMarginT) * 0.18), 2000);
  const bottomSpacing = Math.min(remaining - topSpacing + simMarginT - midSpacing, 5500);
  const children = [];
  children.push(new Paragraph({ spacing: { before: topSpacing } }));
  if (config.schoolName) {
    children.push(new Paragraph({
      alignment: AlignmentType.CENTER, spacing: { after: 400 },
      children: [new TextRun({ text: config.schoolName, size: 44, characterSpacing: 40,
        font: { eastAsia: "SimSun", ascii: "Times New Roman" } })],
    }));
  }
  for (let i = 0; i < titleLines.length; i++) {
    children.push(new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: i < titleLines.length - 1 ? 120 : 300 },
      children: [new TextRun({ text: titleLines[i], size: titleSize, bold: true,
        font: { eastAsia: "SimHei", ascii: "Times New Roman" } })],
    }));
  }
  if (config.subtitle) {
    children.push(new Paragraph({
      alignment: AlignmentType.CENTER, spacing: { after: 200 },
      children: [new TextRun({ text: config.subtitle, size: 30,
        font: { eastAsia: "SimSun", ascii: "Times New Roman" } })],
    }));
  }
  children.push(new Paragraph({ spacing: { before: midSpacing } }));
  if (metaEntries.length) children.push(buildR5MetaTable(metaEntries));
  children.push(new Paragraph({ spacing: { before: bottomSpacing } }));
  if (config.footerRight) {
    children.push(new Paragraph({
      alignment: AlignmentType.CENTER,
      children: [new TextRun({ text: config.footerRight, size: 24, color: "404040",
        font: { eastAsia: "SimSun", ascii: "Times New Roman" } })],
    }));
  }
  return [new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    layout: TableLayoutType.FIXED,
    borders: allNoBorders,
    rows: [new TableRow({
      height: { value: PAGE_H, rule: "exact" },
      children: [new TableCell({
        shading: { type: ShadingType.CLEAR, fill: "FFFFFF" },
        borders: noBorders, verticalAlign: VerticalAlign.TOP,
        margins: { left: simMarginLR, right: simMarginLR },
        children,
      })],
    })],
  })];
}

// ---------- body helpers ----------
const PAL = { primary: "0B1220", body: "182030", accent: "1D4ED8", muted: "506070" };
function h1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 360, after: 160, line: 312 },
    children: [new TextRun({ text, bold: true, color: PAL.primary,
      font: { ascii: "Times New Roman", eastAsia: "SimHei" } })],
  });
}
function h2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 240, after: 120, line: 312 },
    children: [new TextRun({ text, bold: true, color: PAL.primary,
      font: { ascii: "Times New Roman", eastAsia: "SimHei" } })],
  });
}
function body(text, opts = {}) {
  return new Paragraph({
    alignment: AlignmentType.JUSTIFIED,
    indent: { firstLine: 420 },
    spacing: { line: 312, after: opts.after ?? 60 },
    children: [new TextRun({ text, size: 22, color: PAL.body, bold: !!opts.bold })],
  });
}
function bodyRuns(runs) {
  return new Paragraph({
    alignment: AlignmentType.JUSTIFIED,
    indent: { firstLine: 420 },
    spacing: { line: 312, after: 60 },
    children: runs.map(r => new TextRun({ size: 22, color: PAL.body, ...r })),
  });
}
function bullet(text) {
  return new Paragraph({
    bullet: { level: 0 },
    spacing: { line: 312, after: 40 },
    children: [new TextRun({ text, size: 22, color: PAL.body })],
  });
}
function caption(text) {
  return new Paragraph({
    alignment: AlignmentType.CENTER, keepNext: true,
    spacing: { before: 120, after: 80 },
    children: [new TextRun({ text, bold: true, size: 20, color: PAL.muted })],
  });
}
function mkTable(headers, rows, widths) {
  const W = widths || headers.map(() => Math.floor(100 / headers.length));
  const mkCell = (text, i, isHeader) => new TableCell({
    width: { size: W[i], type: WidthType.PERCENTAGE },
    shading: isHeader ? { type: ShadingType.CLEAR, fill: "EDF2F7" } : undefined,
    margins: { top: 50, bottom: 50, left: 90, right: 90 },
    children: [new Paragraph({
      spacing: { line: 276 },
      children: [new TextRun({ text: String(text), bold: isHeader, size: 18,
        color: isHeader ? PAL.primary : PAL.body })],
    })],
  });
  return new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    borders: {
      top: { style: BorderStyle.SINGLE, size: 2, color: "9AA6B2" },
      bottom: { style: BorderStyle.SINGLE, size: 2, color: "9AA6B2" },
      left: NB, right: NB,
      insideHorizontal: { style: BorderStyle.SINGLE, size: 1, color: "D0D0D0" },
      insideVertical: NB,
    },
    rows: [
      new TableRow({ tableHeader: true, cantSplit: true,
        children: headers.map((t, i) => mkCell(t, i, true)) }),
      ...rows.map(r => new TableRow({ cantSplit: true,
        children: r.map((t, i) => mkCell(t, i, false)) })),
    ],
  });
}
function img(path, w, h, cap) {
  const buf = fs.readFileSync(path);
  return [caption(cap),
    new Paragraph({
      alignment: AlignmentType.CENTER, spacing: { after: 160 },
      children: [new ImageRun({ data: buf, type: "png",
        transformation: { width: w, height: h } })],
    })];
}

// ---------- content ----------
const Q = (s) => "\u201C" + s + "\u201D";  // curly quotes helper

const bodyChildren = [];

// 一、暑期工作总览
bodyChildren.push(h1("一、暑期工作总览"));
bodyChildren.push(body("对照申报书四项研究内容，暑期完成情况如下表。全部数据来自真实公共数据库（GEO、ChEMBL、PubChem、RCSB PDB、KEGG），全部代码与中间结果存档于项目目录，可复现。"));
bodyChildren.push(caption("表1  申报书研究内容完成情况对照"));
bodyChildren.push(mkTable(
  ["研究内容", "计划暑期完成部分", "实际完成"],
  [
    ["1 MASH核心靶点转录组学确证", "文献调研+GEO下载", "全部完成：GSE135251（n=216），DEG 3,909个，四靶点全部获显著性验证，KEGG富集第一名=胆汁分泌通路"],
    ["2 高质量活性数据集构建", "数据获取与清洗", "全部完成：ChEMBL FXR 548条\u2192清洗后354化合物+适用域基准"],
    ["3 贝叶斯GNN构建", "原计划9\u201411月", "提前超额完成：双划分评估+校准+GNNExplainer+基线对比"],
    ["4 中药筛选与CW-BCS评估", "原计划12月\u2014次年2月", "提前完成：131成分库+三级标注+排名+交叉对接"],
    ["对接验证（阶段安排第4段）", "原计划次年3\u20145月", "提前完成：5受体重对接验证全过+262次批量对接+8个阳性对照"],
  ], [24, 22, 54]));
bodyChildren.push(bodyRuns([
  { text: "量化指标达成：", bold: true },
  { text: "独立测试集 R\u00B2=0.790（目标\u22650.60）、RMSE=0.723（目标\u22640.80）、回归ECE=0.029（目标\u22640.15）、分类维度 AUPRC=0.955/F1=0.917。按申报书口径，主要量化目标已全部提前达成。" },
]));
bodyChildren.push(body("超出计划的自主工作：一是发现并定量实证" + Q("过度外推") + "痛点（见第三章）；二是开展冷门药材自主探索（见第五章）；三是完成MASH药物管线竞争格局调研（见第五章第三节）。"));

// 二、关键结果摘要
bodyChildren.push(h1("二、关键结果摘要"));
bodyChildren.push(bullet("病理学验证（GSE135251，n=216，Normal 10/NAFL 51/NASH 155）：FXR(NR1H4)下调-0.285(padj=1.0e-02)、THR-\u03B2(THRB)下调-0.315(2.0e-02)、ACC1(ACACA)上调+0.897(7.4e-05)、ACC2(ACACB)上调+0.631(4.2e-03)；阳性对照基因FASN/CYP7A1/COL1A1/TNF全部符合预期方向。"));
bodyChildren.push(bullet("模型：贝叶斯GIN（异方差NLL+MC Dropout T=50+五种子集成），随机划分测试集R\u00B2=0.790；骨架划分下R\u00B2=-0.610（关键发现，见第三章）。"));
bodyChildren.push(bullet("初版中药排名（CW-BCS）：黄连(0.718)>苦参(0.585)>甘草(0.566)>雷公藤(0.565)>丹参(0.545)。经中期自查，该排名的创新性定位不成立，已降级处理（见第五章）。"));
bodyChildren.push(bullet("对接质控：4个受体共晶配体重对接RMSD 0.33\u20141.22\u00C5（全<2\u00C5门槛）；阳性对照药理学排序合理（GW4064\u2248丹参酮IIA>CDCA>OCA；resmetirom>T3；ND-646最强）。"));
bodyChildren.push(bullet("可解释性：GNNExplainer显示小檗碱族关键原子为季铵氮与异喹啉芳香核。"));
bodyChildren.push(...img("../results/figures/gnn_calibration_pack.png", 560, 168,
  "图1  模型校准证据包：测试集预测散带、z分数可靠性图、\u03C3-误差相关"));
bodyChildren.push(...img("../results/figures/target_genes_boxplots.png", 560, 245,
  "图2  四靶点基因在各病理分组中的表达（GSE135251，n=216）"));

// 三、可信度自评与缺点直陈
bodyChildren.push(h1("三、可信度自评与缺点直陈"));
bodyChildren.push(body("本章为本报告核心：对全部已完成结论做证据强度分级，并逐一列出缺陷。", { bold: true }));
bodyChildren.push(h2("3.1 结论可信度分层"));
bodyChildren.push(caption("表2  主要结论的证据强度评级"));
bodyChildren.push(mkTable(
  ["结论", "证据强度依据", "评级"],
  [
    ["三靶点在MASH肝组织差异表达", "216例真实数据+阳性对照基因全部符合预期+通路富集支持", "高"],
    ["对接流程可靠", "4受体重对接RMSD<2\u00C5+8个阳性药排序合理", "高"],
    ["模型在合成骨架空间的预测能力", "随机划分R\u00B2=0.79，但测试集仅36个分子", "中"],
    [Q("过度外推") + "痛点存在", "双划分对照实验，所有模型同崩塌，设计干净", "中高"],
    ["冷门/知名药材FXR预测绝对数值", "召回测试失败（见D2）", "低"],
    ["初版CW-BCS排名位次", "启发式加权+依赖低可信输入", "低"],
  ], [30, 52, 18]));
bodyChildren.push(h2("3.2 五个具体缺陷（含证据）"));
bodyChildren.push(bodyRuns([{ text: "D1 模型在化学空间外推时失效。", bold: true },
  { text: "骨架划分（测试分子来自训练集未见过的母核）下，GNN的R\u00B2从0.79崩塌至-0.61，RF从0.85跌至0.05，XGBoost为负。这不是实现错误而是方法本性的暴露——它反过来证明了本项目" + Q("不确定性量化") + "立论的正确性，但也意味着：任何对训练分布之外分子（多数天然产物正是如此）的预测值都不能按面值采信。" }]));
bodyChildren.push(bodyRuns([{ text: "D2 模型在天然产物空间的排序能力未获证明。", bold: true },
  { text: "用已知天然FXR配体（胆汁酸家族：CDCA/DCA/LCA/CA/甘氨酸CDCA/OCA）做召回测试：预测值与文献活性估计的Spearman相关仅-0.086（即无排序能力），平均绝对误差0.88 log单位，OCA被低估1.4个单位。唯一可辩护之处是模型对这类分子输出了大\u03C3（0.92\u20131.50），" + Q("知道自己不知道") + "。原因：ChEMBL FXR的IC50数据以现代合成非甾体骨架为主，甾体/生物碱骨架欠表示。" }]));
bodyChildren.push(bodyRuns([{ text: "D3 初版" + Q("黄连第一") + "疑似外推伪影。", bold: true },
  { text: "复核发现：小檗碱与全部354个训练化合物的最大Morgan指纹Tanimoto相似度仅0.200（最相近的3个邻居活性只有pIC50 5.4\u20145.9），模型却给出\u03BC=8.21的强预测；黄连碱、巴马汀同理（maxTan 0.17\u20140.19）。而描述符层适用域（leverage=0.022，仅基于MW/LogP/TPSA等11个整体性质）判定其" + Q("域内") + "——描述符AD层看不见结构母核缺失，识别不了这种伪域内。结论：初版排名中黄连族的高分不可信，AD双层机制需要增加指纹相似度维度（已列入修正计划）。注：FXR晶体交叉对接对黄连碱族给出-8.5\u2014-10.6 kcal/mol，方向上支持结合，但Vina对带电骨架打分偏乐观，不能单独作为证据。" }]));
bodyChildren.push(bodyRuns([{ text: "D4 CW-BCS是未经回顾性验证的启发式。", bold: true },
  { text: "w=1/(1+\u03C3)权重、几何均值、Tanimoto冗余惩罚的参数均为合理假设而非拟合结果；位次对min-max归一化敏感；且其FXR输入端依赖D2/D3所述不可靠的天然产物预测。" + Q("衡量结合覆盖而非药理协同") + "的边界已声明，但作为创新点的成色目前只有方法设计，没有独立验证。" }]));
bodyChildren.push(bodyRuns([{ text: "D5 对接与过滤规则的结构性偏差。", bold: true },
  { text: "其一，Vina对甾体/大环打分系统性偏低：OCA实测nM级活性却只得-6.77 kcal/mol，soraphen A（Ki=2.1nM）仅-6.71。其二，THR-\u03B2的T3口袋太小，冷门探索中9个甾醇类分子全部得到正分（无有效构象）——THR-\u03B2对接代理对甾体骨架不可用。其三，申报书ADMET规则（LogP<5.5）结构性排除全部羊毛甾烷三萜（LogP 7.0\u20148.5），而这类骨架恰含保肝证据充分的成分（桦褐孔菌、樟芝），已补做明确标注的" + Q("放宽ADMET敏感性分析") + "（MW<600/LogP<8）作为补救，但主筛选规则需要正式修订。" }]));
bodyChildren.push(h2("3.3 其他如实申报的偏差"));
bodyChildren.push(bullet("用Python（Welch t + BH）替代申报书的R语言DESeq2/limma：方法等价，阳性对照基因验证通过，结题时需说明。"));
bodyChildren.push(bullet("TCMSP数据库无法程序化访问，成分清单改为文献锚定+PubChem CID溯源（每成分有CID可查证），OB/DL筛选标准未执行。"));
bodyChildren.push(bullet("未做PyMOL氢键/残基互作图（pose文件已存，仅差可视化）。"));
bodyChildren.push(bullet("全部计算在单机CPU完成，无GPU资源消耗（影响经费执行说明）。"));

// 四、进度可信度
bodyChildren.push(h1("四、实际推进进度可信度"));
bodyChildren.push(bodyRuns([{ text: "进度判定：真实、可审计、大幅提前。", bold: true },
  { text: "判断依据：全部中间数据文件带时间戳存档；数据来源全部可溯源（CID/PMID/PDB ID/GSE编号）；结果可由代码一键复现；过程中保留了完整的失败与纠错记录（如KEGG接口行为变化、PubChem限流、多个被误用的PDB ID纠错）。" }]));
bodyChildren.push(bodyRuns([{ text: "需注意的进度水分点（如实扣减）：", bold: true },
  { text: "完成阶段4中的TCMSP环节为替代实现而非原方案；对接验证未包含原方案的PyMOL互作分析；GNN指标在随机划分下达标，但该口径严格性弱于骨架划分（申报书未指定划分协议，按其字面口径达标）。" }]));

// 五、方向修正
bodyChildren.push(h1("五、中期审查触发的方向修正"));
bodyChildren.push(h2("5.1 初版TOP5的创新性不成立（按排除标准执行）"));
bodyChildren.push(body("对初版CW-BCS排名前5逐一到注册库与文献核实，结论如下表。初版排名在" + Q("发现新药") + "意义上没有产出——名药之所以为名药，与既有证据自洽；其价值仅在于验证了筛选流程没有方向性错误。"));
bodyChildren.push(caption("表3  初版排名的创新性核查与处理"));
bodyChildren.push(mkTable(
  ["初版排名", "药材", "核实结论", "处理"],
  [
    ["1", "黄连（小檗碱族）", "小檗碱NAFLD RCT\u22653项+meta；HTD1801（小檗碱-UDCA盐）已进MASH III期（NCT06353347）", "降级为方法学验证对照"],
    ["2", "苦参（苦参碱类）", "苦参素注射液上市（HBV适应症）", "同上"],
    ["3", "甘草（甘草酸类）", "甘草酸二铵/异甘草酸镁上市肝药", "同上"],
    ["4", "雷公藤", "毒性药材，仅2个无毒成分入库", "保留毒性标注，不作创新主张"],
    ["5", "丹参（丹参酮类）", "丹参酮IIA保肝研究广泛", "同上"],
    ["库内", "水飞蓟、五味子", "利加隆上市；五酯/联苯双酯/双环醇上市", "初版库本身即已知保肝药集合"],
  ], [10, 16, 50, 24]));
bodyChildren.push(h2("5.2 冷门药材自主探索（新方向）"));
bodyChildren.push(body("方法：遴选7味冷门但有MASH相关线索的药材（樟芝、桦褐孔菌、獐牙菜属、藤茶、叶下珠、积雪草、苦丁茶），文献锚定57个特征成分\u2192PubChem解析（CID可溯源）\u2192ADMET过滤\u2192生产模型推理+三级标注\u2192top29对接THR-\u03B2/ACC\u2192文献证据分级（A临床/B动物/C体外/D传统）。"));
bodyChildren.push(bodyRuns([{ text: "计算结果（诚实呈现，含负面）：", bold: true },
  { text: "FXR轴冷门药材整体弱于知名药味（\u03BC 4.2\u20146.6 vs 6.5\u20148.4），无一达活性阈值，且依D2结论该轴绝对值本就不可信，仅作参考；ACC轴对接广泛强势（-7.0\u2014-9.9），樟芝zhankuic acid A(-9.92)、antcin A(-9.57)、桦褐孔菌inotodiol(-9.79)最突出（阳性药ND-646=-10.52）；THR-\u03B2轴甾体骨架全部对接失败（正分，见D5），该轴对三萜类成分不可用。" }]));
bodyChildren.push(caption("表4  冷门药材文献证据分级与最终推荐"));
bodyChildren.push(mkTable(
  ["推荐位", "药材", "证据等级", "核心依据", "风险/边界"],
  [
    ["1", "樟芝 Antrodia cinnamomea", "A-", "唯一有NASH小样本RCT的冷门药材（28例双盲6个月，SteatoTest/ActiTest/TNF-\u03B1显著改善，PMID 32657670）；antcin/antrodin/zhankuic acid麦角甾烷骨架新颖；无任何国家批准药品、无NASH注册试验；计算ACC轴-9.6支持", "RCT仅28例且单一中心；大陆无合法原料渠道（监管风险）"],
    ["2", "桦褐孔菌 Inonotus obliquus", "B", "提取物及inotodiol/trametenolic acid经FXR/SHP/SREBP-1c轴改善HFD-NAFLD（PMID 35278405，与本项目三靶点策略直接吻合）；无药品；计算ACC-9.8", "国内保健品营销泛滥拉低冷门成色"],
    ["3", "苦丁茶 Ilex kudingcha", "B", "LXR\u03B2拮抗机制（PMID 23226556）+RCT meta血脂阳性；kudinoside皂苷骨架新颖；无药品", "特征皂苷MW>500被ADMET过滤，苷元数据不足"],
    ["4", "积雪草 Centella", "B-", "asiatic acid抗肝纤维化多通路证据（PMID 35963324），差异化定位抗纤维化终点；肝方向无上市药", "LiverTox有罕见肝损报告"],
    ["5", "藤茶/DHM", "A-（附警示）", "60例RCT阳性（PMID 26032587）", "该RCT与同组白藜芦醇试验数据高度相似已遭质疑，临床可信度存疑"],
    ["排除", "叶下珠 Phyllanthus", "B+/人体-", "动物阳性但1年RCT阴性（PMID 37313177）+已有HBV适应症上市药", "按排除标准剔除"],
  ], [8, 17, 12, 42, 21]));
bodyChildren.push(body("獐牙菜属（swertiamarin等）条件保留：NAFLD动物证据扎实（PMID 31005808/33794740），但已有青叶胆片等传统黄疸适应症上市药，不满足" + Q("无上市肝药") + "的严格口径，仅保留单体新适应症方向。"));
bodyChildren.push(bodyRuns([{ text: "回答核心问题——能否找到冷门中药对MASH有显著效果的创新点：能，但有严格边界。", bold: true },
  { text: "最强候选是樟芝（唯一同时满足：有NASH临床证据+无药品+骨架新颖+可计算对接），其次是桦褐孔菌（机制证据与本项目FXR/脂合成轴直接吻合）。但" + Q("显著效果") + "目前只在28例小样本RCT（樟芝）与动物水平（其余），距确证还远——这正是留给本项目后续体内外验证的空间。相反，初版知名药味全部被排除出创新主张。" }]));
bodyChildren.push(h2("5.3 生物药方向可行性评估"));
bodyChildren.push(bodyRuns([{ text: "结论：生物药方向对本科大创不适宜，且" + Q("显著效果") + "的生物药已无冷门空间。", bold: true },
  { text: "依据：已获批2个（resmetirom 2024、semaglutide 2025-08）；效果显著的生物药管线已被瓜分完毕——FGF21三强2025年被Novo/Roche/GSK合计约100亿美元收购，GLP-1类III期扎堆，凡显示显著疗效的生物药几乎都已进入大厂临床。真实生物药冷门（口服HSD17B13仅1家PoC、miRNA疗法刚进I期、F4/失代偿人群无药）均超出本科团队资源、周期与合规能力。" }]));
bodyChildren.push(body("一代FXR全线临床失败（OCA两次被拒、终止NASH开发）对项目的重要提示：天然产物FXR调节的叙事应定位" + Q("温和多靶点协同") + "而非" + Q("强激动") + "。HTD1801（小檗碱成盐改造，MASH III期）的范式表明：天然产物单体+成药性改造+现代终点（MRI-PDFF）的IIa设计是注册库里可量化的空白生态位，也是本团队可执行的方向。"));
bodyChildren.push(...img("../results/figures/tier_annotation.png", 560, 342,
  "图3  131个初版成分的三级置信标注分布（各药材）"));

// 六、秋季计划
bodyChildren.push(h1("六、修正后的秋季计划"));
bodyChildren.push(bullet("方法修正（对应D1\u2014D5）：AD层加入Morgan指纹相似度维度（建议maxTan\u22650.3才可判域内）；CW-BCS做回顾性验证（以已知多靶点天然配体做召回）；正式修订ADMET规则对三萜类的处理；补PyMOL互作图。"));
bodyChildren.push(bullet("主线聚焦：以樟芝（首选）与桦褐孔菌为对象，完成antcin/antrodin/inotodiol类骨架的FXR-THR\u03B2-ACC三轴完整刻画+骨架衍生物虚拟扩充，形成" + Q("冷门真菌源麦角甾烷三萜抗MASH") + "特色方向。"));
bodyChildren.push(bullet("论文定位：以双划分实证外推崩塌+双层置信度标注+冷门真菌药材筛选为主线的方法学论文（普通期刊/会议，符合申报书定位）。"));
bodyChildren.push(bullet("结题文书准备（结题报告书按学校模板改写）。"));

// 七、附录
bodyChildren.push(h1("七、附录：证据与文件索引"));
bodyChildren.push(bullet("主报告：FINAL_REPORT.md；评估：结题评估报告.md；调研：research/目录6份（GEO数据集/PDB结构/ChEMBL靶点/中药成分/冷门药材证据/管线格局）"));
bodyChildren.push(bullet("数据表：results/tables/ 共19个CSV（含known_fxr_ligand_recall.csv、obscure_herbs_predictions.csv、obscure_sensitivity_triterpenes.csv、obscure_docking.csv等）"));
bodyChildren.push(bullet("图：results/figures/ 6张；代码：src/step0\u201410共15个脚本；模型：models/bgnn_production.pt"));
bodyChildren.push(body("（报告完）", { after: 0 }));

// ---------- document ----------
const doc = new Document({
  styles: { default: { document: {
    run: { font: { ascii: "Times New Roman", eastAsia: "Microsoft YaHei" },
           size: 22, color: PAL.body },
    paragraph: { spacing: { line: 312 } },
  }}},
  features: { updateFields: true },
  sections: [
    { properties: { page: { margin: { top: 0, bottom: 0, left: 0, right: 0 } } },
      children: buildCoverR5({
        schoolName: "沈阳药科大学",
        titleLines: ["基于贝叶斯图神经网络的", "抗MASH天然药物筛选项目"],
        titlePt: 32,
        subtitle: "暑假中间报告",
        metaLines: [
          "项目类别：创新训练项目",
          "项目负责人：王启龙",
          "指导教师：姜希伟",
          "报告期间：2026年6月\u20142026年8月",
        ],
        footerRight: "二〇二六年八月",
      }) },
    { properties: { page: { margin: { top: 1440, bottom: 1440, left: 1701, right: 1417 },
        pageNumbers: { start: 1, formatType: NumberFormat.LOWER_ROMAN } } },
      footers: { default: new Footer({ children: [new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [new TextRun({ children: [PageNumber.CURRENT], size: 18 })] })] }) },
      children: [
        new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 240, after: 240 },
          children: [new TextRun({ text: "目  录", bold: true, size: 32,
            font: { eastAsia: "SimHei", ascii: "Times New Roman" } })] }),
        new TableOfContents("目录", { hyperlink: true, headingStyleRange: "1-2" }),
        new Paragraph({ spacing: { before: 120 },
          children: [new TextRun({ text: "（提示：在Word中右键目录\u2192更新域以刷新页码）",
            italics: true, size: 18, color: "888888" })] }),
        new Paragraph({ children: [new PageBreak()] }),
      ] },
    { properties: { page: { margin: { top: 1440, bottom: 1440, left: 1701, right: 1417 },
        pageNumbers: { start: 1, formatType: NumberFormat.DECIMAL } } },
      headers: { default: new Header({ children: [new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: "抗MASH天然药物筛选项目·暑假中间报告", size: 18,
          color: "888888" })] })] }) },
      footers: { default: new Footer({ children: [new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [new TextRun({ children: [PageNumber.CURRENT], size: 18 })] })] }) },
      children: bodyChildren },
  ],
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync("暑假中间报告.docx", buf);
  console.log("saved 暑假中间报告.docx", buf.length, "bytes");
});
