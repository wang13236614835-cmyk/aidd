// 终版TOP5汇报：系数+运转逻辑+双榜单
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, Header, Footer,
 PageNumber, NumberFormat, AlignmentType, HeadingLevel, WidthType, BorderStyle,
 ShadingType, TableLayoutType, VerticalAlign } = require("docx");
const fs = require("fs");
const NB={style:BorderStyle.NONE,size:0,color:"FFFFFF"};
const noBorders={top:NB,bottom:NB,left:NB,right:NB};
const allNoBorders={top:NB,bottom:NB,left:NB,right:NB,insideHorizontal:NB,insideVertical:NB};
const Q=s=>"\u201C"+s+"\u201D";
const PAL={primary:"0B1220",body:"182030",muted:"506070"};
const h1=t=>new Paragraph({heading:HeadingLevel.HEADING_1,spacing:{before:340,after:150,line:312},children:[new TextRun({text:t,bold:true,color:PAL.primary,font:{ascii:"Times New Roman",eastAsia:"SimHei"}})]});
const body=(t,o={})=>new Paragraph({alignment:AlignmentType.JUSTIFIED,indent:{firstLine:420},spacing:{line:312,after:60},children:[new TextRun({text:t,size:22,color:PAL.body,bold:!!o.bold})]});
const bullet=t=>new Paragraph({bullet:{level:0},spacing:{line:312,after:40},children:[new TextRun({text:t,size:22,color:PAL.body})]});
const cap=t=>new Paragraph({alignment:AlignmentType.CENTER,keepNext:true,spacing:{before:110,after:70},children:[new TextRun({text:t,bold:true,size:20,color:PAL.muted})]});
function mkTable(h,r,W){const w=W||h.map(()=>Math.floor(100/h.length));
 const c=(t,i,H)=>new TableCell({width:{size:w[i],type:WidthType.PERCENTAGE},shading:H?{type:ShadingType.CLEAR,fill:"EDF2F7"}:undefined,margins:{top:50,bottom:50,left:80,right:80},children:[new Paragraph({spacing:{line:260},children:[new TextRun({text:String(t),bold:H,size:17,color:H?PAL.primary:PAL.body})]})]});
 return new Table({width:{size:100,type:WidthType.PERCENTAGE},borders:{top:{style:BorderStyle.SINGLE,size:2,color:"9AA6B2"},bottom:{style:BorderStyle.SINGLE,size:2,color:"9AA6B2"},left:NB,right:NB,insideHorizontal:{style:BorderStyle.SINGLE,size:1,color:"D0D0D0"},insideVertical:NB},
 rows:[new TableRow({tableHeader:true,cantSplit:true,children:h.map((t,i)=>c(t,i,true))}),...r.map(x=>new TableRow({cantSplit:true,children:x.map((t,i)=>c(t,i,false))}))]});}
function cover(cfg){const simLR=1701;
 const meta=(cfg.metaLines||[]).map(l=>{const i=l.indexOf("\uFF1A");return i===-1?{label:l,value:""}:{label:l.slice(0,i).trim(),value:l.slice(i+1).trim()};});
 const ch=[new Paragraph({spacing:{before:3100}}),
  new Paragraph({alignment:AlignmentType.CENTER,spacing:{after:400},children:[new TextRun({text:cfg.school,size:44,characterSpacing:40,font:{eastAsia:"SimSun",ascii:"Times New Roman"}})]})];
 cfg.titleLines.forEach((t,i)=>ch.push(new Paragraph({alignment:AlignmentType.CENTER,spacing:{after:i<cfg.titleLines.length-1?120:300},children:[new TextRun({text:t,size:60,bold:true,font:{eastAsia:"SimHei",ascii:"Times New Roman"}})]})));
 ch.push(new Paragraph({alignment:AlignmentType.CENTER,spacing:{after:200},children:[new TextRun({text:cfg.subtitle,size:30,font:{eastAsia:"SimSun",ascii:"Times New Roman"}})]}));
 ch.push(new Paragraph({spacing:{before:1400}}));
 const bb={style:BorderStyle.SINGLE,size:4,color:"000000"};
 ch.push(new Table({width:{size:62,type:WidthType.PERCENTAGE},alignment:AlignmentType.CENTER,layout:TableLayoutType.FIXED,borders:allNoBorders,rows:meta.map(e=>new TableRow({cantSplit:true,children:[
  new TableCell({width:{size:30,type:WidthType.PERCENTAGE},borders:noBorders,margins:{top:60,bottom:60,left:0,right:0},children:[new Paragraph({spacing:{line:400},children:[new TextRun({text:e.label+"\uFF1A",size:24,font:{eastAsia:"SimSun",ascii:"Times New Roman"}})]})]}),
  new TableCell({width:{size:70,type:WidthType.PERCENTAGE},borders:{top:NB,left:NB,right:NB,bottom:bb},margins:{top:60,bottom:60,left:80,right:0},children:[new Paragraph({spacing:{line:400},children:[new TextRun({text:e.value,size:24,font:{eastAsia:"SimSun",ascii:"Times New Roman"}})]})]})]}))}));
 ch.push(new Paragraph({spacing:{before:3400}}),new Paragraph({alignment:AlignmentType.CENTER,children:[new TextRun({text:cfg.footer,size:24,color:"404040",font:{eastAsia:"SimSun",ascii:"Times New Roman"}})]}));
 return [new Table({width:{size:100,type:WidthType.PERCENTAGE},layout:TableLayoutType.FIXED,borders:allNoBorders,rows:[new TableRow({height:{value:16838,rule:"exact"},children:[new TableCell({shading:{type:ShadingType.CLEAR,fill:"FFFFFF"},borders:noBorders,verticalAlign:VerticalAlign.TOP,margins:{left:simLR,right:simLR},children:ch})]})]})];}

const B=[];
B.push(h1("一、运转逻辑（全链条）"));
B.push(body("73.9万天然分子库(COCONUT全库,物种可溯源) \u2192 11靶点多靶点QSAR打分(ChEMBL 9,195化合物训练,检验Spearman 0.69-0.89) \u2192 \u22652靶活性配体识别+PAINS/ADMET/已知药剔除 \u2192 中药专项池(79味药材,40,106成分)与全域池并行 \u2192 FXR/ACC双受体对接三角(重对接验证RMSD<2\u00C5结构) \u2192 统一终评公式(系数见下) \u2192 双TOP5。全程真实数据可复现。"));
B.push(h1("二、终评公式与系数（显性）"));
B.push(body("FinalScore = 0.35\u00D7Act + 0.25\u00D7Dock + 0.20\u00D7Evidence + 0.10\u00D7Novelty + 0.10\u00D7Obtain",{bold:true}));
B.push(bullet("Act = min(MTS/45, 1)：多靶点活性分，MTS=\u03A3(11靶中pAct\u22656.5的预测活性值)"));
B.push(bullet("Dock = min(mean(|dG_FXR|,|dG_ACC|)/10, 1)：结合构象分（阳性锚：GW4064=-9.7/ND-646=-10.5）"));
B.push(bullet("Evidence：1.0=来源有临床RCT；0.7=成分直接机制文献；0.5=药材传统肝效用+计算命中；0.3=纯计算"));
B.push(bullet("Novelty：1.0=零肝病报道；0.8=候选药材成分无肝病报道"));
B.push(bullet("Obtain：1.0=商品/药材可购；0.7=发酵可产；0.1=来源难再获取"));
B.push(h1("三、TOP5 全域（不论来源）"));
B.push(cap("表1  全域TOP5"));
B.push(mkTable(["#","候选","MTS","dG_FXR","dG_ACC","Act","Dock","Evid","Final"],
 [["1","樟芝 Antrocinnamomin F","34.4","-8.01","-8.93","0.76","0.85","1.0","0.859"],
  ["2","土曲霉 Aspernolide D族丁内酯","35.6","-8.63","-8.97","0.79","0.88","0.3","0.737"],
  ["3","内生真菌 07H239-A","22.2","-8.06","-9.00","0.49","0.85","0.3","0.626"],
  ["4","海绵 Alisiaquinol","22.2","-7.10","-9.85","0.49","0.85","0.3","0.625"],
  ["5","海洋 Alternaramide","20.0","-6.51","-8.25","0.44","0.74","0.5","0.620"]],[4,26,7,10,10,7,7,7,9]));
B.push(body("樟芝以临床RCT证据(唯一Evidence=1.0)登顶；2-5名为纯计算/待复核证据的冷门新分子，分差主要来自证据项。"));
B.push(h1("四、TOP5 中药（专项）"));
B.push(cap("表2  中药TOP5"));
B.push(mkTable(["#","药材 | 成分","MTS","dG_FXR","dG_ACC","Act","Dock","Final"],
 [["1","白花蛇舌草 | Anthraxin","35.0","-9.34","-9.87","0.78","0.96","0.792"],
  ["2","苣荬菜 | 未名香豆素苷","35.4","-9.37","-9.35","0.79","0.94","0.789"],
  ["3","甘草 | Derrone","34.7","-10.17","-8.72","0.77","0.94","0.786"],
  ["4","地耳草/田基黄 | 田基黄苷类","35.4","-8.88","-8.45","0.79","0.87","0.772"],
  ["5","黄芪 | 未名异黄酮苷","35.3","-7.27","-10.05","0.78","0.87","0.771"]],[4,28,7,10,10,7,7,9]));
B.push(body("中药TOP5整体分值(0.77-0.79)紧逼全域第二名：中药池在对接构象分上反超(Dock 0.87-0.96)。白花蛇舌草Anthraxin与甘草Derrone(FXR -10.17为全场最强对接)为中药线主打；田基黄为"+Q("冷门肝病专科药+计算命中")+ "最佳交集。未名成分结构已存于库，下一步按SMILES溯源定名。"));
B.push(h1("五、推荐组合与验证"));
B.push(bullet("全中药组方A：白花蛇舌草Anthraxin(代谢轴) + 积雪草asiatic acid(纤维化轴, Evidence 0.7直接文献)。"));
B.push(bullet("组方B：田基黄苷 + 甘草Derrone(代谢双轴)。转化桥：任一组分+樟芝antcin K作阳性对照。"));
B.push(bullet("湿实验：HepG2脂变模型6\u00D76矩阵，Bliss/Loewe/ZIP三法，hit=ZIP>10且单药无效；报告基因(FXR/ACC通路)+TGF\u03B2/Smad验证纤维化轴；AMLN小鼠12周。"));
B.push(h1("六、边界"));
B.push(bullet("QSAR为外推排序器(非确定性预测)；未名成分需结构溯源定名+文献核查后入论文；Derrone已有抗癌方向文献需肝病新颖性复核；对接对甾体/大环失效项已剔除。"));
B.push(body("数据表：results/v5/final_unified_scores.csv；中药池全表：results/v4/tcm_multitarget_top300.csv。"));
const doc=new Document({styles:{default:{document:{run:{font:{ascii:"Times New Roman",eastAsia:"Microsoft YaHei"},size:22,color:PAL.body},paragraph:{spacing:{line:312}}}}},
 sections:[{properties:{page:{margin:{top:0,bottom:0,left:0,right:0}}},children:cover({school:"沈阳药科大学",titleLines:["抗MASH候选药终版双榜","全域TOP5 \u00B7 中药TOP5"],subtitle:"统一终评系数 \u00B7 运转逻辑 \u00B7 73.9万库实证",metaLines:["项目：基于贝叶斯图神经网络的抗MASH天然药物筛选（大创）","性质：最终候选汇报","日期：2026年8月"],footer:"2026年8月"})},
 {properties:{page:{margin:{top:1440,bottom:1440,left:1701,right:1417},pageNumbers:{start:1,formatType:NumberFormat.DECIMAL}}},
  headers:{default:new Header({children:[new Paragraph({alignment:AlignmentType.CENTER,children:[new TextRun({text:"抗MASH候选药终版双榜",size:18,color:"888888"})]})]})},
  footers:{default:new Footer({children:[new Paragraph({alignment:AlignmentType.CENTER,children:[new TextRun({children:[PageNumber.CURRENT],size:18})]})]})},children:B}]});
Packer.toBuffer(doc).then(b=>{fs.writeFileSync("抗MASH终版双榜.docx",b);console.log("saved");});
