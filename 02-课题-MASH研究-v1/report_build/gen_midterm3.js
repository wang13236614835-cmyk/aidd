// 暑假中期报告 v3：排版修复 + 团队口吻（正文字符串不含任何引号）
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, Header, Footer,
 PageNumber, NumberFormat, AlignmentType, HeadingLevel, WidthType, BorderStyle,
 ShadingType, TableLayoutType, VerticalAlign } = require("docx");
const fs = require("fs");
const NB={style:BorderStyle.NONE,size:0,color:"FFFFFF"};
const noBorders={top:NB,bottom:NB,left:NB,right:NB};
const allNoBorders={top:NB,bottom:NB,left:NB,right:NB,insideHorizontal:NB,insideVertical:NB};
const PAL={primary:"0B1220",body:"182030",muted:"506070"};
const h1=t=>new Paragraph({heading:HeadingLevel.HEADING_1,spacing:{before:330,after:140,line:312},children:[new TextRun({text:t,bold:true,color:PAL.primary,font:{ascii:"Times New Roman",eastAsia:"SimHei"}})]});
const h2=t=>new Paragraph({heading:HeadingLevel.HEADING_2,spacing:{before:220,after:100,line:312},children:[new TextRun({text:t,bold:true,color:PAL.primary,font:{ascii:"Times New Roman",eastAsia:"SimHei"}})]});
const body=t=>new Paragraph({alignment:AlignmentType.JUSTIFIED,indent:{firstLine:440},spacing:{line:312,after:80},children:[new TextRun({text:t,size:24,color:PAL.body})]});
const bullet=t=>new Paragraph({bullet:{level:0},spacing:{line:312,after:50},children:[new TextRun({text:t,size:22,color:PAL.body})]});
const cap=t=>new Paragraph({alignment:AlignmentType.CENTER,keepNext:true,spacing:{before:110,after:70},children:[new TextRun({text:t,bold:true,size:20,color:PAL.muted})]});
function mkTable(h,r,W){const w=W||h.map(()=>Math.floor(100/h.length));
 const c=(t,i,H)=>new TableCell({width:{size:w[i],type:WidthType.PERCENTAGE},shading:H?{type:ShadingType.CLEAR,fill:"EDF2F7"}:undefined,margins:{top:70,bottom:70,left:100,right:100},children:[new Paragraph({spacing:{line:280},children:[new TextRun({text:String(t),bold:H,size:19,color:H?PAL.primary:PAL.body})]})]});
 return new Table({width:{size:100,type:WidthType.PERCENTAGE},borders:{top:{style:BorderStyle.SINGLE,size:2,color:"9AA6B2"},bottom:{style:BorderStyle.SINGLE,size:2,color:"9AA6B2"},left:NB,right:NB,insideHorizontal:{style:BorderStyle.SINGLE,size:1,color:"D0D0D0"},insideVertical:NB},
 rows:[new TableRow({tableHeader:true,cantSplit:true,children:h.map((t,i)=>c(t,i,true))}),...r.map(x=>new TableRow({cantSplit:true,children:x.map((t,i)=>c(t,i,false))}))]});}
function cover(cfg){const simLR=1701;
 const meta=(cfg.metaLines||[]).map(l=>{const i=l.indexOf("\uFF1A");return i===-1?{label:l,value:""}:{label:l.slice(0,i).trim(),value:l.slice(i+1).trim()};});
 const ch=[new Paragraph({spacing:{before:2900}}),
  new Paragraph({alignment:AlignmentType.CENTER,spacing:{after:400},children:[new TextRun({text:cfg.school,size:44,characterSpacing:40,font:{eastAsia:"SimSun",ascii:"Times New Roman"}})]})];
 cfg.titleLines.forEach((t,i)=>ch.push(new Paragraph({alignment:AlignmentType.CENTER,spacing:{after:i<cfg.titleLines.length-1?120:300},children:[new TextRun({text:t,size:56,bold:true,font:{eastAsia:"SimHei",ascii:"Times New Roman"}})]})));
 ch.push(new Paragraph({alignment:AlignmentType.CENTER,spacing:{after:200},children:[new TextRun({text:cfg.subtitle,size:28,font:{eastAsia:"SimSun",ascii:"Times New Roman"}})]}));
 ch.push(new Paragraph({spacing:{before:1200}}));
 const bb={style:BorderStyle.SINGLE,size:4,color:"000000"};
 ch.push(new Table({width:{size:62,type:WidthType.PERCENTAGE},alignment:AlignmentType.CENTER,layout:TableLayoutType.FIXED,borders:allNoBorders,rows:meta.map(e=>new TableRow({cantSplit:true,children:[
  new TableCell({width:{size:30,type:WidthType.PERCENTAGE},borders:noBorders,margins:{top:60,bottom:60,left:0,right:0},children:[new Paragraph({spacing:{line:400},children:[new TextRun({text:e.label+"\uFF1A",size:24,font:{eastAsia:"SimSun",ascii:"Times New Roman"}})]})]}),
  new TableCell({width:{size:70,type:WidthType.PERCENTAGE},borders:{top:NB,left:NB,right:NB,bottom:bb},margins:{top:60,bottom:60,left:80,right:0},children:[new Paragraph({spacing:{line:400},children:[new TextRun({text:e.value,size:24,font:{eastAsia:"SimSun",ascii:"Times New Roman"}})]})]})]}))}));
 ch.push(new Paragraph({spacing:{before:3000}}),new Paragraph({alignment:AlignmentType.CENTER,children:[new TextRun({text:cfg.footer,size:24,color:"404040",font:{eastAsia:"SimSun",ascii:"Times New Roman"}})]}));
 return [new Table({width:{size:100,type:WidthType.PERCENTAGE},layout:TableLayoutType.FIXED,borders:allNoBorders,rows:[new TableRow({height:{value:16838,rule:"exact"},children:[new TableCell({shading:{type:ShadingType.CLEAR,fill:"FFFFFF"},borders:noBorders,verticalAlign:VerticalAlign.TOP,margins:{left:simLR,right:simLR},children:ch})]})]})];}

const B=[];
B.push(h1("一、项目背景与暑期工作概述"));
B.push(body("代谢相关脂肪性肝炎（MASH）是全球慢性肝病的主要类型，与肝硬化及肝细胞癌进展密切相关。2024年3月甲状腺激素受体β激动剂resmetirom获美国食品药品监督管理局批准成为首个MASH治疗药物，2025年8月司美格鲁肽亦获加速批准，但现有疗法在纤维化逆转、安全性与可及性方面仍远不能满足临床需求，新候选分子的发掘依然是领域核心问题。"));
B.push(body("本项目立项时的技术路线为：以FXR为建模主锚点，构建带不确定性量化的贝叶斯图神经网络，对十种保肝中药的活性成分进行虚拟筛选。项目组在暑期按申报书计划完成了病理学验证与模型构建的全部内容；在执行过程中，项目组通过对模型适用边界的严格检验认识到，单一靶点的点预测难以支撑天然产物这类高多样性化学空间的筛选决策，据此将研究逐步深化为多靶点评估、组合协同与中药专项相结合的完整框架，并最终形成两份候选药物榜单（全域来源与中药来源各前五名）。全部研究基于真实公共数据库（GEO、ChEMBL、PubChem、COCONUT、RCSB PDB、STRING），全部代码与中间结果在项目目录中存档，可复核、可复现。"));
B.push(h1("二、总体研究思路与阶段衔接"));
B.push(body("整个暑期工作由浅入深分为五个相互衔接的环节。第一步，在人体病理层面确认候选靶点与疾病的关联，为后续所有计算提供生物学依据；第二步，按申报书原方案构建FXR单靶点预测模型，并对模型开展超出常规做法的严格性检验；第三步，检验所暴露的问题直接推动了方法升级——项目组将单一靶点扩展为覆盖脂代谢与核受体两大类共十一个肝相关靶点的多靶点评估体系，化合物空间由十味中药扩展到七十余万天然产物；第四步，对计算筛选得到的候选分子逐一进行文献新颖性核查，确认其研究空白并评估风险；第五步，针对MASH多机制并存的疾病特征设计组合协同方案，并以四种独立方法交叉验证设计逻辑，最终结合项目组自身的中医药学背景完成中药专项筛选，形成候选药物终版榜单。"));
B.push(body("需要说明的是，第二环节中发现的模型局限并非工作失误，而是本项目的重要方法学收获：它以定量证据说明了在天然产物筛选中引入不确定性量化与多靶点交叉验证的必要性，这一认识贯穿并塑造了后续全部工作。"));
B.push(h1("三、各环节方法与结果"));
B.push(h2("3.1 MASH核心靶点的病理学验证"));
B.push(body("本环节目的在于为项目组确认FXR、THRβ与ACC三个靶点在MASH患者肝组织中存在可检测的病理改变，使后续建模有据可依。数据采用GEO数据库的GSE135251数据集（转录组测序，216例人肝活检，其中健康对照10例、单纯脂肪变性51例、MASH 155例，均附纤维化分期与NAS评分）。经基因符号映射、标准化与统计学检验（Welch t检验加Benjamini-Hochberg校正），共鉴定出3909个差异表达基因。四个核心靶点均达到统计学显著：FXR编码基因NR1H4下调0.285（对数尺度，校正后p=0.010），THRβ编码基因THRB下调0.315（p=0.020），ACC1编码基因ACACA上调0.897（p=7.4\u00D710\u2075），ACC2编码基因ACACB上调0.631（p=0.004）。受体下调与合成酶上调的组合模式，为受体激动联合合成抑制的干预思路提供了病理学注脚。"));
B.push(body("在同批数据上开展的共表达分析进一步识别出三个与疾病严重度相关的基因模块：以THY1、COL1A2为代表的纤维化模块（与纤维化分期相关系数0.58），以PLIN1/2、FGF21为代表的脂滴代谢模块，以及以HMGCR、SQLE、FDFT1为代表的胆固醇合成模块。通路富集分析中排名首位的正是胆汁分泌通路（p=8.6\u00D710\u2074），与FXR的胆汁酸感受器身份吻合。这些模块与靶点共同构成了后续多靶点评估的疾病背景。"));
B.push(h2("3.2 FXR单靶点贝叶斯GNN模型及其严格性检验"));
B.push(body("按申报书方案，项目组从ChEMBL数据库获取人源FXR（CHEMBL2047）的结合实验活性数据548条，经精确关系过滤、盐剥离、规范化去重、PAINS过滤与适用域剔除后得到354个化合物的训练集。模型采用图同构网络（GIN）架构，引入异方差负对数似然损失与蒙特卡洛Dropout（T=50）实现偶然与认知不确定性的双层量化，并以五个随机种子的深度集成稳定方差估计。"));
B.push(body("在申报书口径的随机划分独立测试集上，模型决定系数R\u00B2为0.790、均方根误差0.723、回归期望校准误差0.029，三项均达到或优于申报书指标；分类维度的精确率-召回率曲线下面积达0.955。分子对接环节对四个受体晶体结构完成重对接验证（构象均方根偏差全部小于2埃），阳性对照药物的对接强弱排序与已知活性强度一致，说明结构层面的计算流程可信。"));
B.push(body("然而，三项超常规的严格性检验揭示了模型的适用边界。其一，将测试集改为训练集未见过的分子骨架时，所有模型的决定系数均大幅下降（本模型由0.79降至-0.61，随机森林与XGBoost基线同样崩塌），说明性能高度依赖化学空间相似性。其二，以六种已知天然FXR配体（胆汁酸家族）做召回测试，预测值与文献活性值的秩相关仅为-0.086，即模型对天然产物骨架基本不具备排序能力，尽管其输出的大方差在一定程度上提示了自身的不确定性。其三，初版筛选中黄连生物碱族获得的高预测活性经溯源核查，与训练集的最大分子指纹相似度仅0.20，属于模型外推产生的可疑结果。这三项发现共同界定了单靶点点预测的可靠性边界，也直接构成了下一环节方法升级的动因。"));
B.push(h2("3.3 从单靶点到多靶点：天然产物库的规模化筛选"));
B.push(body("鉴于上述局限，项目组将评估框架升级为多靶点体系：从ChEMBL获取十一个肝相关靶点（FXR、THRβ、ACC2、FASN、DGAT2、SCD、HMGCR、FDFT1、SQLE、PPARγ、LXRα）共9195个化合物的真实活性数据，为每个靶点训练随机森林定量模型（检验集Spearman相关0.69至0.89），同时对化合物空间做量级扩充——下载COCONUT天然产物全库，去重与结构验证后得到738823个分子，其中27.4万个标注了来源物种。"));
B.push(body("以至少三个靶点同时预测活性达微摩尔级为标准，共识别出80698个多靶点配体；剔除泛警报结构、理化性质不合格者以及渗入数据库的合成库化合物与已知药物后，天然来源的多靶点领先者浮出水面：牛樟芝的Antrocinnamomin F同时作用于五个靶点且在FXR、ACC、THRβ三个受体的对接中全部达到强结合区间（-8.0至-8.9千卡/摩尔），土曲霉的丁内酯族、海绵与内生真菌来源的多个分子紧随其后。多靶点预测值至此仍属计算假设，其研究价值取决于候选是否真正处于研究空白，这正是下一环节的任务。"));
B.push(h2("3.4 候选化合物的新颖性核查"));
B.push(body("项目组对位居前列的候选逐一在PubMed检索其肝病与代谢相关文献。核查结果支持三个主打车位：海洋来源Alternaria真菌的环肽Alternaramide此前从未被报道于任何肝病模型，但已有一项抑制TLR4-MyD88/NF-κB通路的抗炎机制研究（PMID 26620692），而该通路恰是MASH炎症阶段的核心环节，机制衔接顺理成章；曲霉属的Versicolamide B本体在代谢性肝病领域同样零报道，其同家族分子notoamide Q则在小鼠肝缺血再灌注模型中显示保护作用（PMID 37560942），且已有不对称全合成路线，样品可获取性在稀有真菌代谢物中最佳；牛樟芝来源的antcin与antrodin类成分则有小型随机双盲临床研究与充分的动物文献托底。与此同时，核查也暴露出若干高风险候选——强细胞毒记录、深水海绵来源难以再获取、结构修订论文曾被撤稿——均被项目组如实降级为列表成员而非主打车位。"));
B.push(h2("3.5 组合协同设计与多方法交叉验证"));
B.push(body("MASH是脂代谢紊乱、炎症与纤维化多机制并存的疾病，单一分子即便多靶点，也难以同时覆盖全部病理环节。为此项目组将上述成分按四条作用轴（核受体轴、脂合成轴、炎症间接轴、纤维化轴）设计正交组合，并采用四种彼此独立的方法验证设计逻辑。网络医学邻近度分析（基于STRING真实互作数据）显示含Alternaramide的组合在网络距离上最优；临床先例检索证实MASH组合疗法已被领域接受，FXR+THRβ、FXR+ACC、FGF21+GLP-1等组合均已进入二期临床；人肝单细胞图谱（Nature 2019）证实胶原合成限于间质细胞、白细胞介素1β等炎症标志限于巨噬细胞区室，为多轴作用于不同细胞类型提供了直接证据；组合数据库层面则因现有库以肿瘤为主而无肝病数据，属中性结果。四法合议后项目组对组合优先级做了修正：证据最强的代谢加代谢与代谢加纤维化组合升为一等，含Alternaramide的组合因机制身份尚待复核而列为二线。"));
B.push(h2("3.6 中药专项筛选"));
B.push(body("考虑到项目组自身的中医药学背景与药材可及性优势，最后一个环节面向中药开展专项筛选。在已打分的全库中，按七十九味中药材（涵盖药典常用药、民族药与冷门肝病专科药）的物种信息过滤，得到40106个中药来源化合物的多靶点命中表；项目组对每味药的最佳成分补做了FXR与ACC双受体对接。结果显示中药池的对接构象分整体反超全域池：甘草来源的Derrone在FXR受体取得全场最强的-10.17千卡/摩尔，白花蛇舌草的Anthraxin双受体均低于-9.3，苣荬菜、田基黄、黄芪的代表性成分紧随其后。中药线的相对短板在于证据分——多数命中依赖药材传统效用加计算推断，而非成分自身的直接文献，这一差距恰好应由后续湿实验弥补。"));
B.push(h1("四、候选药物推荐"));
B.push(body("综合五个环节的证据，项目组采用统一且系数公开的终评公式对全部候选排序：终评得分等于0.35乘多靶点活性分、加0.25乘对接构象分、加0.20乘证据分、加0.10乘新颖性分、加0.10乘可获得性分，其中证据分按临床研究、成分直接文献、药材传统效用加计算推断、纯计算四档赋值。两份榜单如下。"));
B.push(cap("表1  候选药物榜单（全域来源前五名，对接单位为千卡/摩尔）"));
B.push(mkTable(["序","候选分子","来源","MTS","FXR","ACC","终评"],
 [["1","Antrocinnamomin F","牛樟芝","34.4","-8.01","-8.93","0.859"],
  ["2","Aspernolide D族丁内酯","土曲霉","35.6","-8.63","-8.97","0.737"],
  ["3","07H239-A","内生真菌","22.2","-8.06","-9.00","0.626"],
  ["4","Alisiaquinol","深水海绵","22.2","-7.10","-9.85","0.625"],
  ["5","Alternaramide","海洋真菌","20.0","-6.51","-8.25","0.620"]],[5,24,15,10,11,11,10]));
B.push(cap("表2  候选药物榜单（中药专项前五名，对接单位为千卡/摩尔）"));
B.push(mkTable(["序","药材","代表成分","MTS","FXR","ACC","终评"],
 [["1","白花蛇舌草","Anthraxin","35.0","-9.34","-9.87","0.792"],
  ["2","苣荬菜","未名香豆素苷","35.4","-9.37","-9.35","0.789"],
  ["3","甘草","Derrone","34.7","-10.17","-8.72","0.786"],
  ["4","地耳草（田基黄）","田基黄苷类","35.4","-8.88","-8.45","0.772"],
  ["5","黄芪","未名异黄酮苷","35.3","-7.27","-10.05","0.771"]],[5,15,24,10,11,11,10]));
B.push(body("在组合层面项目组推荐两个全中药组方：组方甲为白花蛇舌草Anthraxin（代谢轴）联合积雪草苷元asiatic acid（纤维化轴，有转化生长因子β/Smad通路的直接文献支持）；组方乙为田基黄苷联合甘草Derrone（代谢双轴）。牛樟芝antcin K与小檗碱建议作为实验阳性对照。"));
B.push(h1("五、存在的不足"));
B.push(body("项目组如实列示当前工作的八项不足及对应改进方案。"));
B.push(mkTable(["序","不足之处","改进方案"],
 [["1","定量模型外推边界：天然产物骨架上的预测排序能力未获证明（胆汁酸召回检验失败）","适用域加入分子指纹相似度维度；预测靶谱以报告基因逐一验证"],
  ["2","未名成分待定名：中药榜单中苣荬菜与黄芪的最佳成分尚无名称","按库内结构溯源并结合核磁复核后命名，方可写入论文"],
  ["3","候选身份待复核：Alternaramide的炎症机制文献存在检索矛盾；Derrone已有抗癌方向文献","以NF-κB报告基因实验前置裁决；补充肝病新颖性专项检索"],
  ["4","对接打分系统偏差：甾体与大环骨架在部分受体口袋失效或偏低","对关键候选补充MM-GBSA重打分与分子动力学模拟"],
  ["5","缺乏湿实验数据：全部结论基于计算与文献","按第六节三阶段方案执行实验验证"],
  ["6","网络验证为子网版：邻近度计算基于查询蛋白互作子网而非全互作组","下载完整STRING连接组文件重算z分数"],
  ["7","组合协同为假设：组合评分属假设生成器，未经实验裁决","以Bliss、Loewe、ZIP三法一致性矩阵实验裁定"],
  ["8","中药清单覆盖有限：专项覆盖79味药材，未及全药典","扩充地方标准与民族药药材后重筛"]],[8,46,46]));
B.push(h1("六、下一阶段工作计划"));
B.push(bullet("2026年9至10月：采购或发酵获取两份榜单前十名成分；完成未名成分结构定名；完成Alternaramide机制身份与Derrone新颖性复核。"));
B.push(bullet("2026年10至12月：HepG2与Hepa1-6棕榈酸脂变模型单药四点初筛（命中标准：甘油三酯下降不低于30%且细胞活力不低于80%，有效浓度不高于10微摩尔）；组方甲、乙开展六乘六浓度矩阵并以三种协同度量法联合判定。"));
B.push(bullet("2026年12月至2027年1月：机制归属实验（FXR与ACC通路报告基因、转化生长因子β/Smad纤维化轴验证）；以实验数据回填终评公式的证据项并重排榜单。"));
B.push(bullet("2027年春季：AMLN饮食小鼠十二周造模加四周给药（每组八只）；论文撰写与结题材料准备。"));
B.push(h1("七、结语"));
B.push(body("项目组在暑期按验证、建模、检验、升级、交付的次序完成了从申报书原方案到多靶点组合框架的完整深化：病理层面确认了靶点的疾病相关性，建模层面以严格检验界定了单靶点预测的适用边界，筛选层面在七十余万天然产物中建立了多靶点评估体系，核证层面确认了候选的研究空白，最终交付全域与中药两份候选榜单及全中药组方。下一阶段项目组的核心任务是将计算假设交付实验裁决，使榜单中至少一个候选或一组组合获得细胞与动物层面的正面证据。"));
const doc=new Document({styles:{default:{document:{run:{font:{ascii:"Times New Roman",eastAsia:"Microsoft YaHei"},size:24,color:PAL.body},paragraph:{spacing:{line:312}}}}},
 sections:[{properties:{page:{margin:{top:0,bottom:0,left:0,right:0}}},children:cover({school:"沈阳药科大学",titleLines:["基于贝叶斯图神经网络的","抗MASH天然药物筛选项目"],subtitle:"暑假中期报告",metaLines:["项目类别：创新训练项目","项目负责人：王启龙","指导教师：姜希伟","报告期间：2026年6月至8月"],footer:"二〇二六年八月"})},
 {properties:{page:{margin:{top:1400,bottom:1400,left:1701,right:1417},pageNumbers:{start:1,formatType:NumberFormat.DECIMAL}}},
  headers:{default:new Header({children:[new Paragraph({alignment:AlignmentType.CENTER,children:[new TextRun({text:"抗MASH天然药物筛选项目·暑假中期报告",size:18,color:"888888"})]})]})},
  footers:{default:new Footer({children:[new Paragraph({alignment:AlignmentType.CENTER,children:[new TextRun({children:[PageNumber.CURRENT],size:18})]})]})},children:B}]});
Packer.toBuffer(doc).then(b=>{fs.writeFileSync("暑假中期报告.docx",b);console.log("saved");});
