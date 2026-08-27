// 新方向进展汇报 docx（R5学术封面+正文，无TOC）→ 之后Word转PDF
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Footer, PageNumber, NumberFormat, AlignmentType, HeadingLevel,
  WidthType, BorderStyle, ShadingType, TableLayoutType, VerticalAlign,
} = require("docx");
const fs = require("fs");
const NB = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
const noBorders = { top: NB, bottom: NB, left: NB, right: NB };
const allNoBorders = { top: NB, bottom: NB, left: NB, right: NB, insideHorizontal: NB, insideVertical: NB };
const Q = (s) => "\u201C" + s + "\u201D";
const PAL = { primary: "0B1220", body: "182030", muted: "506070" };

function h1(t){return new Paragraph({heading:HeadingLevel.HEADING_1,spacing:{before:340,after:150,line:312},children:[new TextRun({text:t,bold:true,color:PAL.primary,font:{ascii:"Times New Roman",eastAsia:"SimHei"}})]});}
function h2(t){return new Paragraph({heading:HeadingLevel.HEADING_2,spacing:{before:230,after:110,line:312},children:[new TextRun({text:t,bold:true,color:PAL.primary,font:{ascii:"Times New Roman",eastAsia:"SimHei"}})]});}
function body(t,o={}){return new Paragraph({alignment:AlignmentType.JUSTIFIED,indent:{firstLine:420},spacing:{line:312,after:60},children:[new TextRun({text:t,size:22,color:PAL.body,bold:!!o.bold})]});}
function runs2(rr){return new Paragraph({alignment:AlignmentType.JUSTIFIED,indent:{firstLine:420},spacing:{line:312,after:60},children:rr.map(r=>new TextRun({size:22,color:PAL.body,...r}))});}
function bullet(t){return new Paragraph({bullet:{level:0},spacing:{line:312,after:40},children:[new TextRun({text:t,size:22,color:PAL.body})]});}
function cap(t){return new Paragraph({alignment:AlignmentType.CENTER,keepNext:true,spacing:{before:110,after:70},children:[new TextRun({text:t,bold:true,size:20,color:PAL.muted})]});}
function mkTable(headers,rows,W){
  const w=W||headers.map(()=>Math.floor(100/headers.length));
  const cell=(t,i,h)=>new TableCell({width:{size:w[i],type:WidthType.PERCENTAGE},
    shading:h?{type:ShadingType.CLEAR,fill:"EDF2F7"}:undefined,
    margins:{top:50,bottom:50,left:90,right:90},
    children:[new Paragraph({spacing:{line:270},children:[new TextRun({text:String(t),bold:h,size:18,color:h?PAL.primary:PAL.body})]})]});
  return new Table({width:{size:100,type:WidthType.PERCENTAGE},
    borders:{top:{style:BorderStyle.SINGLE,size:2,color:"9AA6B2"},bottom:{style:BorderStyle.SINGLE,size:2,color:"9AA6B2"},left:NB,right:NB,
      insideHorizontal:{style:BorderStyle.SINGLE,size:1,color:"D0D0D0"},insideVertical:NB},
    rows:[new TableRow({tableHeader:true,cantSplit:true,children:headers.map((t,i)=>cell(t,i,true))}),
      ...rows.map(r=>new TableRow({cantSplit:true,children:r.map((t,i)=>cell(t,i,false))}))]});
}
// R5 cover
function cover(cfg){
  const simLR=1701,simT=1200;
  const meta=(cfg.metaLines||[]).map(l=>{const i=l.indexOf("\uFF1A");return i===-1?{label:l,value:""}:{label:l.slice(0,i).trim(),value:l.slice(i+1).trim()};});
  const children=[new Paragraph({spacing:{before:3100}}),
    new Paragraph({alignment:AlignmentType.CENTER,spacing:{after:400},children:[new TextRun({text:cfg.school,size:44,characterSpacing:40,font:{eastAsia:"SimSun",ascii:"Times New Roman"}})]})];
  cfg.titleLines.forEach((t,i)=>children.push(new Paragraph({alignment:AlignmentType.CENTER,spacing:{after:i<cfg.titleLines.length-1?120:300},children:[new TextRun({text:t,size:60,bold:true,font:{eastAsia:"SimHei",ascii:"Times New Roman"}})]})));
  children.push(new Paragraph({alignment:AlignmentType.CENTER,spacing:{after:200},children:[new TextRun({text:cfg.subtitle,size:30,font:{eastAsia:"SimSun",ascii:"Times New Roman"}})]}));
  children.push(new Paragraph({spacing:{before:1400}}));
  const bb={style:BorderStyle.SINGLE,size:4,color:"000000"};
  children.push(new Table({width:{size:62,type:WidthType.PERCENTAGE},alignment:AlignmentType.CENTER,layout:TableLayoutType.FIXED,borders:allNoBorders,
    rows:meta.map(e=>new TableRow({cantSplit:true,children:[
      new TableCell({width:{size:30,type:WidthType.PERCENTAGE},borders:noBorders,margins:{top:60,bottom:60,left:0,right:0},
        children:[new Paragraph({spacing:{line:400},children:[new TextRun({text:e.label+"\uFF1A",size:24,font:{eastAsia:"SimSun",ascii:"Times New Roman"}})]})]}),
      new TableCell({width:{size:70,type:WidthType.PERCENTAGE},borders:{top:NB,left:NB,right:NB,bottom:bb},margins:{top:60,bottom:60,left:80,right:0},
        children:[new Paragraph({spacing:{line:400},children:[new TextRun({text:e.value,size:24,font:{eastAsia:"SimSun",ascii:"Times New Roman"}})]})]})]}))}));
  children.push(new Paragraph({spacing:{before:3400}}),
    new Paragraph({alignment:AlignmentType.CENTER,children:[new TextRun({text:cfg.footer,size:24,color:"404040",font:{eastAsia:"SimSun",ascii:"Times New Roman"}})]}));
  return [new Table({width:{size:100,type:WidthType.PERCENTAGE},layout:TableLayoutType.FIXED,borders:allNoBorders,
    rows:[new TableRow({height:{value:16838,rule:"exact"},children:[new TableCell({shading:{type:ShadingType.CLEAR,fill:"FFFFFF"},borders:noBorders,verticalAlign:VerticalAlign.TOP,margins:{left:simLR,right:simLR},children})]})]})];
}

const B=[];
B.push(h1("一、任务定位与方法学框架"));
B.push(body("本阶段任务：脱离原有申报书方法（单靶点FXR主锚+10味药限定），从课题本质出发——找到新颖的抗MASH药物。靶点本身也是创新对象，不做单一锁定，以"+Q("遗传机会靶点+新范式靶点+疾病模块可成药枢纽")+"组成并行靶点组合；化合物空间放开为全部天然产物（73.9万分子起步）。"));
B.push(body("方法学八步（顶刊逻辑，全部真实数据）：①遗传学锚靶（GWAS Catalog+Open Targets实测）→ ②疾病模块（216例肝活检共表达分析）→ ③超大天然库（COCONUT全库738,823分子）→ ④11肝靶点多靶点QSAR（ChEMBL 9,195化合物训练）→ ⑤冷门来源+ADMET+新颖性过滤 → ⑥综合分排名 → ⑦分子对接三角验证 → ⑧湿实验方案。"));

B.push(h1("二、已完成进展总览"));
B.push(cap("表1  新方向八步执行状态"));
B.push(mkTable(["步骤","内容","状态"],
 [["①遗传锚靶","GWAS Catalog Solr管道96研究797关联+OpenTargets v4全量拉取","完成"],
  ["②疾病模块","GSE135251(n=216)共表达：纤维化模块(r=0.58)/脂滴模块/胆固醇合成模块，45个hub基因","完成"],
  ["③超大库","COCONUT 2026-08(248MB)→去重去无效→738,823分子，27.4万带物种溯源","完成"],
  ["④多靶点QSAR","11靶点9,195化合物；检验Spearman：THR\u03B2 0.89/LXR\u03B1 0.85/PPAR\u03B3 0.83/SCD 0.69；全库打分完成","完成"],
  ["⑤⑥过滤排名","NP耐受ADMET+冷门物种计分(排除30名药属/已知药)+综合分","完成(TOP500)"],
  ["⑦对接三角","TOP12于FXR/THR\u03B2/ACC三受体交叉对接(重对接验证过的结构)","完成"],
  ["⑧湿实验方案","细胞\u2192酶学\u2192动物三级方案(见第五节)","已拟定"]],[10,62,28]));

B.push(h1("三、靶点创新组合（不锁定单靶点，三线并行）"));
B.push(body("按"+Q("一切皆可重来，只要求新颖有效")+"的原则，靶点层组合如下——三者互补，任何一条线出hit即成立：",{bold:true}));
B.push(cap("表2  靶点组合与新颖性评估"));
B.push(mkTable(["线","靶点","证据与新颖性","拥挤度"],
 [["A 遗传机会","MARC1(p=1e-43,OT遗传0.818,有配体结构)；TM6SF2(3e-83)；SLC39A8(1e-133)；SERPINA1(CIR遗传0.902)；GCKR/MBOAT7/SUGP1/FARSB/SAMM50/CMIP","GWAS多性状验证+零在研药物（PNPLA3已被AZ的ASO占位、HSD17B13被GSK/Alnylam三家挤满，均降权）","空白"],
  ["B 新范式","CerS6(神经酰胺合酶6)","Science 2025(PMID 40310917)：肠道真菌Fusarium foetens代谢物FF-C1直接抑制CerS6逆转小鼠MASH——天然真菌代谢物+全新靶点的完整先例；抑制剂几乎空白","极低"],
  ["C 疾病模块","胆固醇合成模块hub(SQLE/FDFT1，r_NAS=0.24)；纤维化模块hub(MMP2/THY1/MFAP4)","源自本项目216例共表达分析；SQLE/FDFT1无上市降肝脂药(statins占据HMGCR)；纤维化hub为MASH关键终点","低-中"]],[14,30,42,14]));
B.push(body("说明：A线由人类遗传学背书（最不易翻车），B线由顶刊动物药效背书（机制最新），C线由本队自有数据背书（可独立叙事）。三线共用同一化合物库与筛选管线。"));

B.push(h1("四、冷门候选筛选结果"));
B.push(body("73.9万分子\u2192QSAR+ADMET+冷门过滤\u2192TOP500\u2192TOP12对接三角验证。首批三首选（全部冷门来源、多证据一致）："));
B.push(cap("表3  首选湿实验候选（对接单位kcal/mol）"));
B.push(mkTable(["候选","来源","QSAR-top3","FXR","ACC","THR\u03B2"],
 [["07H239-A","炭角菌内生真菌(Xylariaceae)","7.39","-8.06","-9.00","-8.04"],
  ["Alisiaquinol","未鉴定海绵","7.39","-7.10","-9.85","-5.80"],
  ["Aspergicin","海洋红树林内生曲霉","6.83","-8.09","-9.42","-3.24"],
  ["樟芝antrodin群(对照)","牛樟芝(台湾真菌)","7.2-7.6","-8.5~-10.6(文献交叉)","强","失效(甾体)"]],[22,26,12,13,13,14]));
B.push(bullet("阳性对照锚点：GW4064在FXR=-9.70、ND-646在ACC=-10.52、resmetirom在THR\u03B2=-10.11——候选分数与已知活性药同量级。"));
B.push(bullet("交叉验证发现：樟芝antrodin群在本轮73.9万库筛选中独立重现（与上一轮文献锚定路线收敛），升格为稳健对照组。"));
B.push(bullet("其余TOP冷门来源：内生真菌(Merulin/Xylarenone/Pleosporone)、海洋放线菌氯化色烯、大型藻、海绵生物碱(共40个，见shortlist_top500.csv)。"));
B.push(body("局限如实声明：QSAR在天然产物空间的外推可靠性有限（前期已自检），故排名主证据为冷门文献+多模型一致性，QSAR仅作排序器；对接对大环/甾体骨架存在系统偏差已标注。"));

B.push(h1("五、湿实验方案（摘要）"));
B.push(bullet("阶段1 细胞初筛：HepG2/Hepa1-6棕榈酸脂变模型，TOP40四点浓度(0.1-30\u03BCM)；BODIPY/TG定量+CellTiter-Glo活力；Hit标准=TG降\u226530%且活力\u226580%@\u226410\u03BCM；阳性对照AICAR/小檗碱/lovastatin。"));
B.push(bullet("阶段2 机制归属：MARC1重组酶活(NADH 340nm)；CerS6酶活/神经酰胺组学(B线)；FXR/THR\u03B2报告基因；SPR测KD。"));
B.push(bullet("阶段3 体内：AMLN饮食C57BL/6J小鼠12周+给药4周(20mg/kg/day)，NAS评分+油红O+纤维化qPCR，n=8/组。"));
B.push(bullet("样品获取：07H239-A需菌种发酵(炭角菌可培养)；Aspergicin海洋曲霉可培养；Alisiaquinol海绵来源难\u2192先做合成类似物；樟芝菌丝体粉+antrodin标样可购。"));

B.push(h1("六、下一步计划"));
B.push(bullet("靶点三线并行推进：A线MARC1抑制剂筛选（库内对接+酶活验证）；B线CerS6——按Science 2025范式寻找第二个真菌CerS6抑制剂（本库真菌来源聚酮/生物碱优先）；C线SQLE/FDFT1天然抑制剂筛选。"));
B.push(bullet("化合物线：07H239-A/Aspergicin发酵获取+类似物虚拟扩充（ECFP邻域检索ChEMBL）；TOP40采购清单与溶剂对照整理。"));
B.push(bullet("论文线：73.9万分子四维三角筛选框架+机会靶点组合论证，目标普通期刊/学术会议。"));

B.push(h1("七、结论"));
B.push(body("新方向已按用户要求完成重开：靶点不锁定（遗传机会+Science2025新范式+自建疾病模块三线并行），化合物不限来源（73.9万全天然产物空间），筛出内生真菌/海绵/海洋曲霉来源的三首选冷门候选并给出可执行湿实验方案。全部数据真实可溯源（GWAS/OT/ChEMBL/COCONUT/PubChem/PDB），全部代码可复现。"));

const doc=new Document({
  styles:{default:{document:{run:{font:{ascii:"Times New Roman",eastAsia:"Microsoft YaHei"},size:22,color:PAL.body},paragraph:{spacing:{line:312}}}}},
  sections:[
    {properties:{page:{margin:{top:0,bottom:0,left:0,right:0}}},children:cover({
      school:"沈阳药科大学",
      titleLines:["抗MASH冷门药物筛选","新方向进展汇报"],
      subtitle:"靶点创新组合 \u00B7 73.9万分子库 \u00B7 冷门候选到湿实验方案",
      metaLines:["项目：基于贝叶斯图神经网络的抗MASH天然药物筛选（大创）","汇报期间：2026年8月（新方向阶段）","文档性质：进展汇报"],
      footer:"2026年8月"})},
    {properties:{page:{margin:{top:1440,bottom:1440,left:1701,right:1417},pageNumbers:{start:1,formatType:NumberFormat.DECIMAL}}},
      headers:{default:new Header2()},
      footers:{default:new Footer({children:[new Paragraph({alignment:AlignmentType.CENTER,children:[new TextRun({children:[PageNumber.CURRENT],size:18})]})]})},
      children:B},
  ],
});
function Header2(){const {Header}=require("docx");return new Header({children:[new Paragraph({alignment:AlignmentType.CENTER,children:[new TextRun({text:"抗MASH冷门药物筛选\u00B7新方向进展汇报",size:18,color:"888888"})]})]});}
Packer.toBuffer(doc).then(buf=>{fs.writeFileSync("新方向进展汇报.docx",buf);console.log("saved",buf.length);});
