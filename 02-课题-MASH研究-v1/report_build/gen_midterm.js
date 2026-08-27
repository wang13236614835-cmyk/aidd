// 暑假中期报告（自洽版）：演进逻辑链+按步骤方法结果+候选药双榜+不足与后续任务
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, Header, Footer,
 PageNumber, NumberFormat, AlignmentType, HeadingLevel, WidthType, BorderStyle,
 ShadingType, TableLayoutType, VerticalAlign } = require("docx");
const fs = require("fs");
const NB={style:BorderStyle.NONE,size:0,color:"FFFFFF"};
const noBorders={top:NB,bottom:NB,left:NB,right:NB};
const allNoBorders={top:NB,bottom:NB,left:NB,right:NB,insideHorizontal:NB,insideVertical:NB};
const Q=s=>"\u201C"+s+"\u201D";
const PAL={primary:"0B1220",body:"182030",muted:"506070"};
const h1=t=>new Paragraph({heading:HeadingLevel.HEADING_1,spacing:{before:330,after:140,line:312},children:[new TextRun({text:t,bold:true,color:PAL.primary,font:{ascii:"Times New Roman",eastAsia:"SimHei"}})]});
const h2=t=>new Paragraph({heading:HeadingLevel.HEADING_2,spacing:{before:220,after:100,line:312},children:[new TextRun({text:t,bold:true,color:PAL.primary,font:{ascii:"Times New Roman",eastAsia:"SimHei"}})]});
const body=(t,o={})=>new Paragraph({alignment:AlignmentType.JUSTIFIED,indent:{firstLine:420},spacing:{line:312,after:50},children:[new TextRun({text:t,size:21,color:PAL.body,bold:!!o.bold})]});
const runs2=rr=>new Paragraph({alignment:AlignmentType.JUSTIFIED,indent:{firstLine:420},spacing:{line:312,after:50},children:rr.map(r=>new TextRun({size:21,color:PAL.body,...r}))});
const bullet=t=>new Paragraph({bullet:{level:0},spacing:{line:312,after:35},children:[new TextRun({text:t,size:21,color:PAL.body})]});
const cap=t=>new Paragraph({alignment:AlignmentType.CENTER,keepNext:true,spacing:{before:100,after:60},children:[new TextRun({text:t,bold:true,size:19,color:PAL.muted})]});
function mkTable(h,r,W){const w=W||h.map(()=>Math.floor(100/h.length));
 const c=(t,i,H)=>new TableCell({width:{size:w[i],type:WidthType.PERCENTAGE},shading:H?{type:ShadingType.CLEAR,fill:"EDF2F7"}:undefined,margins:{top:45,bottom:45,left:75,right:75},children:[new Paragraph({spacing:{line:255},children:[new TextRun({text:String(t),bold:H,size:16,color:H?PAL.primary:PAL.body})]})]});
 return new Table({width:{size:100,type:WidthType.PERCENTAGE},borders:{top:{style:BorderStyle.SINGLE,size:2,color:"9AA6B2"},bottom:{style:BorderStyle.SINGLE,size:2,color:"9AA6B2"},left:NB,right:NB,insideHorizontal:{style:BorderStyle.SINGLE,size:1,color:"D0D0D0"},insideVertical:NB},
 rows:[new TableRow({tableHeader:true,cantSplit:true,children:h.map((t,i)=>c(t,i,true))}),...r.map(x=>new TableRow({cantSplit:true,children:x.map((t,i)=>c(t,i,false))}))]});}
function cover(cfg){const simLR=1701;
 const meta=(cfg.metaLines||[]).map(l=>{const i=l.indexOf("\uFF1A");return i===-1?{label:l,value:""}:{label:l.slice(0,i).trim(),value:l.slice(i+1).trim()};});
 const ch=[new Paragraph({spacing:{before:3000}}),
  new Paragraph({alignment:AlignmentType.CENTER,spacing:{after:400},children:[new TextRun({text:cfg.school,size:44,characterSpacing:40,font:{eastAsia:"SimSun",ascii:"Times New Roman"}})]})];
 cfg.titleLines.forEach((t,i)=>ch.push(new Paragraph({alignment:AlignmentType.CENTER,spacing:{after:i<cfg.titleLines.length-1?120:300},children:[new TextRun({text:t,size:58,bold:true,font:{eastAsia:"SimHei",ascii:"Times New Roman"}})]})));
 ch.push(new Paragraph({alignment:AlignmentType.CENTER,spacing:{after:200},children:[new TextRun({text:cfg.subtitle,size:28,font:{eastAsia:"SimSun",ascii:"Times New Roman"}})]}));
 ch.push(new Paragraph({spacing:{before:1300}}));
 const bb={style:BorderStyle.SINGLE,size:4,color:"000000"};
 ch.push(new Table({width:{size:62,type:WidthType.PERCENTAGE},alignment:AlignmentType.CENTER,layout:TableLayoutType.FIXED,borders:allNoBorders,rows:meta.map(e=>new TableRow({cantSplit:true,children:[
  new TableCell({width:{size:30,type:WidthType.PERCENTAGE},borders:noBorders,margins:{top:60,bottom:60,left:0,right:0},children:[new Paragraph({spacing:{line:400},children:[new TextRun({text:e.label+"\uFF1A",size:24,font:{eastAsia:"SimSun",ascii:"Times New Roman"}})]})]}),
  new TableCell({width:{size:70,type:WidthType.PERCENTAGE},borders:{top:NB,left:NB,right:NB,bottom:bb},margins:{top:60,bottom:60,left:80,right:0},children:[new Paragraph({spacing:{line:400},children:[new TextRun({text:e.value,size:24,font:{eastAsia:"SimSun",ascii:"Times New Roman"}})]})]})]}))}));
 ch.push(new Paragraph({spacing:{before:3200}}),new Paragraph({alignment:AlignmentType.CENTER,children:[new TextRun({text:cfg.footer,size:24,color:"404040",font:{eastAsia:"SimSun",ascii:"Times New Roman"}})]}));
 return [new Table({width:{size:100,type:WidthType.PERCENTAGE},layout:TableLayoutType.FIXED,borders:allNoBorders,rows:[new TableRow({height:{value:16838,rule:"exact"},children:[new TableCell({shading:{type:ShadingType.CLEAR,fill:"FFFFFF"},borders:noBorders,verticalAlign:VerticalAlign.TOP,margins:{left:simLR,right:simLR},children:ch})]})]})];}

const B=[];
B.push(h1("一、项目背景与中期自查结论"));
B.push(body("项目《基于贝叶斯图神经网络的抗MASH天然药物筛选》立项于2026年6月。本中期报告覆盖暑期全部工作。中期自查结论：申报书原技术路线（单靶点FXR建模+10味药筛选）的量化指标已全部提前达成，但经三轮自我审查发现其候选产出创新性不足；据此完成方法学重构，最终交付"+Q("全域TOP5+中药TOP5")+ "候选药双榜及协同组合方案。全部数据来自真实公共数据库（GEO/ChEMBL/PubChem/COCONUT/STRING/PDB），全部代码与中间结果存档可复现。"));
B.push(h1("二、研究历程：四阶段演进逻辑（自洽主线）"));
B.push(body("本报告的自洽性建立在以下因果链上——每一阶段的结果直接触发下一阶段的决策："));
B.push(cap("表1  阶段演进逻辑链"));
B.push(mkTable(["阶段","动机","关键发现","决策"],
 [["\u2460按申报书执行","完成原定单靶点路线","随机划分指标达标(R\u00B2=0.790)；但骨架划分R\u00B2=-0.61、胆汁酸召回Spearman=-0.086、小檗碱与训练集maxTan仅0.20却预测8.21","确认模型外推缺陷；初版TOP5全为知名上市药味(小檗碱/甘草酸等)"],
  ["\u2461方法重构","脱离原框架，按顶刊逻辑重来","GWAS+OpenTargets锁定机会靶点(MARC1等零竞争)；73.9万库+11靶点QSAR筛出天然多靶点领袖","候选空间从10味药扩展到全部天然产物"],
  ["\u2461+\u2462深度+核证","多靶点视角+SCI强度要求","新颖性逐条核查：Alternaramide零肝病报道+TLR4/NF-\u03BAB机制文献；Versicolamide B有全合成路线","确立主打候选组合"],
  ["\u2463协同+验证","用户质询\u201C确定生效吗\u201D","四法独立验证(网络邻近度/临床先例/单细胞/数据库)：代谢+代谢证据最强；修正组合排序","含Alternaramide组合降二线待身份复核"],
  ["\u2464中药专项","用户要求向中药靠","79味中药40,106成分再筛；甘草Derrone FXR对接-10.17全场最强","双TOP5+全中药组方定型"]],[12,22,42,24]));
B.push(h1("三、方法与结果（按步骤）"));
B.push(h2("步骤1 病理学靶点验证（真实数据：GEO GSE135251，n=216）"));
B.push(body("RNA-seq计数矩阵（Normal 10/NAFL 51/NASH 155，含F0-F4分期）\u2192标准化\u2192Welch t+BH。结果：FXR(NR1H4)\u2193-0.285(padj=1.0e-2)、THR\u03B2(THRB)\u2193-0.315、ACC1(ACACA)\u2191+0.897(7.4e-5)、ACC2\u2191+0.631；阳性对照基因全部符合预期；KEGG富集第一名=胆汁分泌通路(p=8.6e-4)。共表达分析得三个疾病模块：纤维化(THY1/COL1A2, r_fib=0.58)、脂滴(PLIN/FGF21)、胆固醇合成(HMGCR/SQLE/FDFT1)。"));
B.push(h2("步骤2 贝叶斯GNN单靶点建模（含自我证伪）"));
B.push(body("GIN+异方差NLL+MC Dropout五种子集成，随机划分独立测试集R\u00B2=0.790/RMSE=0.723/ECE=0.029（超申报书指标）；重对接验证4受体RMSD全<2\u00C5；阳性对照排序合理。自我证伪三项：骨架划分崩塌、天然配体召回失败、外推伪影（详见不足D1-D3）——该发现本身成为方法学贡献。"));
B.push(h2("步骤3 重构：超大库多靶点筛选"));
B.push(body("COCONUT全库738,823分子（27.4万带物种溯源）\u219211肝靶点QSAR（ChEMBL 9,195化合物训练，检验Spearman 0.69-0.89）\u219280,698个\u22653靶多靶点配体\u2192PAINS/ADMET/已知药剔除\u2192天然多靶点领袖（樟芝Antrocinnamomin F、土曲霉丁内酯族等）。"));
B.push(h2("步骤4 新颖性核证（PubMed逐条实测）"));
B.push(body("Alternaramide（海洋Alternaria环五肽）：零肝病报道+TLR4/NF-\u03BAB抗炎机制文献；Versicolamide B：本体零报道+家族肝保护先例+全合成可得；高风险候选（强细胞毒/来源难/结构争议）如实降级。"));
B.push(h2("步骤5 协同组合设计与四法验证"));
B.push(body("正交四轴（核受体/脂合成/炎症间接/纤维化）组合设计\u2192网络邻近度(STRING)、临床先例(DUET/ATLAS/TANDEM/SYNERGY)、单细胞细胞类型(Nature 2019人肝图谱)、组合数据库四法独立裁决\u2192证据分层修正组合排序（代谢+代谢最强；代谢+纤维化为SYNERGY范式）。"));
B.push(h2("步骤6 中药专项"));
B.push(body("79味中药（药典+民族药+冷门肝病专科药）40,106成分专项过滤\u2192每味药最佳多靶点成分\u2192FXR/ACC双受体对接\u2192中药TOP5。"));
B.push(h1("四、候选药终版双榜（最终交付）"));
B.push(runs2([{text:"终评公式（系数显性）：",bold:true},{text:"FinalScore = 0.35\u00D7Act(多靶点活性MTS/45) + 0.25\u00D7Dock(双受体|dG|均值/10) + 0.20\u00D7Evidence(临床1.0/直接文献0.7/传统效用+计算0.5/纯计算0.3) + 0.10\u00D7Novelty + 0.10\u00D7Obtain。"}]));
B.push(cap("表2  TOP5 全域"));
B.push(mkTable(["#","候选","MTS","dG_FXR","dG_ACC","Final"],
 [["1","樟芝 Antrocinnamomin F（唯一临床RCT来源）","34.4","-8.01","-8.93","0.859"],
  ["2","土曲霉 Aspernolide D族丁内酯","35.6","-8.63","-8.97","0.737"],
  ["3","内生真菌 07H239-A","22.2","-8.06","-9.00","0.626"],
  ["4","海绵 Alisiaquinol","22.2","-7.10","-9.85","0.625"],
  ["5","海洋环肽 Alternaramide（身份待复核）","20.0","-6.51","-8.25","0.620"]],[5,37,9,12,12,10]));
B.push(cap("表3  TOP5 中药"));
B.push(mkTable(["#","药材 | 成分","MTS","dG_FXR","dG_ACC","Final"],
 [["1","白花蛇舌草 | Anthraxin","35.0","-9.34","-9.87","0.792"],
  ["2","苣荬菜 | 未名香豆素苷","35.4","-9.37","-9.35","0.789"],
  ["3","甘草 | Derrone（全场最强FXR对接-10.17）","34.7","-10.17","-8.72","0.786"],
  ["4","地耳草/田基黄 | 田基黄苷类","35.4","-8.88","-8.45","0.772"],
  ["5","黄芪 | 未名异黄酮苷","35.3","-7.27","-10.05","0.771"]],[5,37,9,12,12,10]));
B.push(body("推荐组方：全中药组方A=白花蛇舌草Anthraxin(代谢轴)+积雪草asiatic acid(纤维化轴，直接文献)；组方B=田基黄苷+甘草Derrone(代谢双轴)；阳性对照=樟芝antcin K/小檗碱。",{}));
B.push(h1("五、不足与改进方案"));
B.push(mkTable(["编号","不足（如实）","改进方案"],
 [["D1","QSAR在天然产物空间外推可靠性未证明（胆汁酸召回Spearman=-0.086）","AD层加入Morgan指纹相似度维度(maxTan\u22650.3才判域内)；报告基因逐一验证预测靶谱"],
  ["D2","中药TOP5含2个未名成分（苣荬菜/黄芪）","按库内SMILES结构溯源+NMR复核定名后方可入论文"],
  ["D3","Alternaramide的TLR4身份两轮核查矛盾；Derrone有抗癌方向文献","NF-\u03BAB报告基因身份裁决实验前置；Derrone补肝病新颖性专项检索"],
  ["D4","对接对甾体/大环系统失效或偏差","MM-GBSA重打分+关键候选补分子动力学"],
  ["D5","全部结论为计算+文献，无湿实验","按第六节三阶段执行（细胞\u2192机制\u2192小鼠）"],
  ["D6","网络邻近度为查询子网版非全互作组","下载完整STRING links文件重跑z-score"],
  ["D7","组合协同分为假设生成器","ZIP/Bliss/Loewe三法矩阵实验裁决"],
  ["D8","中药清单覆盖79味（非全药典）","扩充至全药典+地方标准药材重筛"]],[7,48,45]));
B.push(h1("六、后续任务（时间线）"));
B.push(bullet("9-10月：采购/发酵获取双榜TOP10成分；未名成分定名；Alternaramide身份裁决(NF-\u03BAB报告基因)；Derrone新颖性复核。"));
B.push(bullet("10-12月：HepG2/Hepa1-6脂变模型单药四点初筛(hit=TG\u226530%\u2193且活力\u226580%@\u226410\u03BCM)+安全窗；组方A/B做6\u00D76矩阵ZIP分析。"));
B.push(bullet("12-1月：机制归属（FXR/ACC报告基因+TGF\u03B2/Smad纤维化轴验证）；湿实验数据回填终评Evidence项，双榜重排。"));
B.push(bullet("春季：AMLN小鼠12周+4周给药(n=8)；论文撰写（叙事：73.9万库\u2192多靶点\u2192中药专项\u2192协同验证）；结题材料。"));
B.push(h1("七、结论"));
B.push(body("暑期完成了从申报书路线到顶刊逻辑重构的完整演进：单靶点量化指标达标并自我证伪其外推边界，随后以73.9万分子库+11靶点多靶点框架+中药专项重筛，交付证据链完整的候选药双榜（全域TOP5+中药TOP5）与全中药协同组方，并给出八项不足的对应改进方案与逐月任务线。全部结论可复现、可审计，为秋季湿实验验证做好了优先级与材料准备。"));
B.push(body("（报告完）",{}));
const doc=new Document({styles:{default:{document:{run:{font:{ascii:"Times New Roman",eastAsia:"Microsoft YaHei"},size:21,color:PAL.body},paragraph:{spacing:{line:312}}}}},
 sections:[{properties:{page:{margin:{top:0,bottom:0,left:0,right:0}}},children:cover({school:"沈阳药科大学",titleLines:["基于贝叶斯图神经网络的","抗MASH天然药物筛选项目"],subtitle:"暑假中期报告（自洽版）",metaLines:["项目类别：创新训练项目","项目负责人：王启龙","指导教师：姜希伟","报告期间：2026年6月\u20148月"],footer:"二〇二六年八月"})},
 {properties:{page:{margin:{top:1400,bottom:1400,left:1701,right:1417},pageNumbers:{start:1,formatType:NumberFormat.DECIMAL}}},
  headers:{default:new Header({children:[new Paragraph({alignment:AlignmentType.CENTER,children:[new TextRun({text:"抗MASH天然药物筛选\u00B7暑假中期报告",size:18,color:"888888"})]})]})},
  footers:{default:new Footer({children:[new Paragraph({alignment:AlignmentType.CENTER,children:[new TextRun({children:[PageNumber.CURRENT],size:18})]})]})},children:B}]});
Packer.toBuffer(doc).then(b=>{fs.writeFileSync("暑假中期报告_自洽版.docx",b);console.log("saved");});
