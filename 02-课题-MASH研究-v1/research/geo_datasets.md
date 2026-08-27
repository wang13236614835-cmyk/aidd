# GEO MASH/NASH肝组织转录组数据集调研报告
（GEO官方FTP实测验证 + EBI BioStudies/Europe PMC/HGNC REST交叉验证，2026-08-17）

## 数据集对比（5个全部实测）
| 项目 | GSE135251 ⭐首选 | GSE164760 | GSE89632 | GSE48452 | GSE63067 |
|---|---|---|---|---|---|
| 数据类型 | RNA-seq | Microarray | Microarray | Microarray | Microarray |
| 平台 | GPL18573 NextSeq 500 | GPL13667 HG-U219 | GPL14951 HumanHT-12 | GPL11532 HuGene-1_1 | GPL570 U133 Plus2 |
| 总样本 | 216 | 170 | 63 | 73 | 18 |
| 分组 | Normal 10; NAFL/SS 51; NASH 141 | Healthy 6; Cirrhotic 8; NASH 74; NASH-HCC 82 | HC 24; SS 20; NASH 19 | Control 14; HealthyObese 27; SS 14; NASH 18 | Normal 7; SS 2; NASH 9 |
| 纤维化分期 | 逐样本F0-F4+NAS评分 | 无(有cirrhotic组) | 无 | 有 | 无 |
| PMID | 33268509 (Sci Transl Med 2020) | 33992698 | 25581263/35166723 | 23931760 | 25993042 |

## 决策
- 主分析：GSE135251（唯一RNA-seq、样本量最大、Normal+SS+MASH齐全、逐样本F分期+NAS）
- 备选验证：GSE89632（三组平衡经典队列）
- GSE63067样本量过小不用

## 实测注记
- FTP路径规则：数字部分去末3位+"nnn"（GSE135251→GSE135nnn）
- HTTPS对nih.gov在部分沙箱被SSL阻断，改走ftp://协议或Python requests
- GSE135251 series matrix含字段：nas score / fibrosis stage / group in paper(NASH_F2等) / disease / Stage
- RAW.tar 45.9MB含216个逐样本计数文件

## 基因符号确认（HGNC实测）
FXR=NR1H4 (HGNC:7967, Entrez:9971)（"NLR1H4"不存在——项目书如有此写法需更正）
THR-β=THRB (Entrez:7068); ACC1=ACACA (Entrez:31); ACC2=ACACB (Entrez:32)
