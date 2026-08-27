# M2备忘录｜应用章节写法：CW-BCS与候选证据（药学与中药学负责人，2026-08-23）

依据：judge_verdict（共识4/5/10、A3/A5/B4）、候选清单圆桌修订版、herb_cwbcs_ranking_fix.csv。

## 一、应用章节叙事（Results应用+讨论）
1. 定位句先行：应用是方法学的**演示**，不构成药效声称。首句"As a proof-of-concept application of the dual-split protocol and tiered UQ annotation…"。
2. CW-BCS语义边界（Results与讨论首段各一次）：CW-BCS度量**成分群对建模靶面板（FXR/THRβ/ACC等）的覆盖倾向**，仅此而已——覆盖≠协同：多靶覆盖不等于多轴协同，协同由正交轴组合设计单独评分、须Bliss/Loewe/ZIP实验裁决；面板条件性：换面板排名即失效。
3. 收缩排名呈现：正文只给收缩榜（score×n/(n+5)），原榜与k敏感性进SI。雷公藤0.565→0.162（第4→第9）作小样本收缩正面案例写一句，附肝毒注脚"not a recommendation"；前四黄连0.529＞苦参0.458＞甘草0.443＞丹参0.427注明"robust to shrinkage"。
4. 三级标注价值（应用与主线之桥）：把"σ域外欠膨胀（骨架覆率0.80）"翻译成**筛选纪律**——仅域内高置信成分可任药材代表、进优先队列，OOD成分（水飞蓟黄酮木脂素、青蒿素类）自动降权。黄连代表成分由Coptisine（低置信）改判Epiberberine（高置信）即该纪律产物，作方法自洽实例写入。131成分表由此是"UQ约束下的分层决策工具"而非清单。

## 二、中药解释边界
1. 黄连：可写"14成分中8个域内高置信、全部≥2靶覆盖，收缩分居首；与黄连及小檗碱既有代谢调节文献方向一致"。禁写"计算验证清热燥湿""预测最优保肝中药"。规范句："药材排名仅在靶面板语义内可解释；药典功效属另一语义体系，本文仅作事后一致性观察，不作功效验证。"
2. 五味子/灵芝低排名＝口袋性质：五味子木脂素对接THRβ/ACC普遍弱（多数成分0靶覆盖），灵芝三萜coverage_multi=1——低排名反映**结构—口袋匹配度**而非药材无效：五味子保肝主证据走Nrf2/抗氧化轴，不在面板内。写为方法自我设界的反向佐证：面板外机制不判死刑，只判"本研究不可判"。

## 三、候选证据表（正文最小集，7行）
| 条目 | 证据等级 | 锚点 |
| 樟芝 antcin K/antrodin B/Antrocinnamomin F | 物种级临床+计算交叉 | PMID 32657670 |
| 积雪草 asiatic acid | 直接文献（注明无计算分、不入计算排名） | PMID 35963324 |
| 黄连 Epiberberine | 纯计算（高置信代表成分） | 本文表 |
| 小檗碱 | 已知活性阳性对照锚 | 综述 |
| 甘草 Derrone、白花蛇舌草 Anthraxin | 纯计算+药材可购 | 本文表 |
| 07H239-A | 计算对照（不可购、细胞毒家族史） | PMID 15387660 |

证据等级列三级枚举：species-level clinical / direct literature / purely computational；另加"实证可购性"列（货号级证据进SI）。SI锚点：Alternaramide 26620692、Versicolamide B 37560942、各药材成分来源（黄连PMC10843322、甘草PMC10036654、苦参PMC3957258、五味子PMC10809469、灵芝PMID 31035236）。

## 四、安全hedge（逐条强制）
- 排名/优先语句一律附"computational prioritization for hypothesis generation; requires experimental validation"。
- 樟芝："clinical evidence at the species level（28例发酵菌丝体全粉、SteatoTest血清学终点），不可归因任何单体，无单体RCT"。
- asiatic acid："evidence-based entry independent of the computational pipeline"。
- CW-BCS："panel-conditional; coverage is not synergy"。
- ADMET/PAINS过滤："preliminary filters, not a safety assessment"；雷公藤、千里光（PA黑名单）随文注脚。

## 五、审稿人预期挑刺与预防
1. 成分库非穷尽、无体内暴露（小檗碱生物利用度）→明示library-level定位与排除规则，讨论承认缺位。
2. 药效过度声称→语义边界句前置。
3. QSAR×对接循环互证（共享活性库）→写"双异源交叉印证"并承认局限（保留分歧3）。
4. 成分归属可靠性→SI附逐药材来源表（C2归属过滤列为in progress）。
5. 中医语义误读→"语义体系不可通约"声明。
6. 樟芝证据拔高→全文grep无"单体RCT/三重命中"（B4验收）。

## 六、进SI不进正文
131成分四维全表；收缩前后榜对照+k敏感性；10药材成分来源清单；计算对照档细节（07H239-A/Alisiaquinol/Versicolamide B）；组合协同全表（含三联与resmetirom桥）；茵陈观察项；PA黑名单与Obtain实证明细；水飞蓟结构警示。
