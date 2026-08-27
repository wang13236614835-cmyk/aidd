# 审稿人B（药学与数据完整性）二审意见（2026-08-23）

抽验：compound_cwbcs_full、herb_cwbcs_ranking_fix、final_unified_scores_fix、fxr_crossdocking_top10（均自行复算）。

1. 摘要/§2.2｜"354 FXR agonists"与筛选矛盾：IC50('=', type B)为结合抑制测度，不区分激动/拮抗；Discussion又自称"agnostic to agonism vs antagonism"。【必须修】改"354条FXR生物活性(IC50型)记录"；§2.2注明"IC50测度与pIC50输出均不含作用方向"；不可知句前移§2.7；中文稿统一"预测结合强度，不预测激活方向"。

2. §3.6｜ρ=−0.394仅对3FLI成立（实测：3FLI −0.394/p=0.26；1OSH −0.042/p=0.91），正文未注明受体，涉选择性报告。【必须修】正文与S0注明3FLI并同报1OSH无效，或删"directionally consistent"。

3. §2.6｜"十味传统保肝药材"含雷公藤——药典毒性药材、无保肝主治；青蒿/黄连/苦参主治亦非保肝，中文稿尤敏感。【必须修】改"十味与肝保护研究相关的中药（雷公藤为毒性药材仅作计算对照）"，Table 4该行加安全注。

4. §2.6｜PA药材黑名单（千里光/款冬/菊三七前置过滤，圆桌据以删v5千里光条目）未入论文与SI；扩展板恰含十味以外药材。【必须修】排除标准补PA整药材排除；SI记v5_fix删5无名+1千里光操作。

5. §3.7/Table 5｜樟芝群"双源计算"数据链不全：fix表仅antrocinnamomin F一行（无THR-β列），antcin K/antrodin B计算分无存档；圆桌"5靶点QSAR"与论文三靶面板矛盾且无源文件。【必须修】SI补数值，或降格"物种级证据+antrocinnamomin F双源计算"；中文稿统一三靶口径，5靶无来源即删。

6. Table 5｜"computable"混用两义：面板条目给AD分层，扩展板条目是否经域审计不明。【建议修】脚注定义"computable=有计算分但非131面板、未经三级AD标注"。

7. §3.7｜asiatic acid在fix表FINAL=0.32，论文未提，易被误比0.859。【建议修】S0/S3补"0.32仅为文献证据分，不参与计算排名"。

8. §3.5｜小檗碱μ=8.21(≈6nM)有被读作"强FXR直接配体"风险（其保肝文献多为非FXR直接机制）。【建议修】锚点列加"非该强度直接配体的实验证据，仅作已知活性参照"。

9. §2.8｜OCA −6.77已注甾体低分倾向，但未点明"临床FXR激动剂对接低分"的反向警示。【建议修】加"对接分仅支持库内相对排序，不得跨靶点/类型比活性"。

10. S0缺口｜a)交叉验证未注明用哪列ΔG；b)np_docking_raw.csv未列入S0/S5；c)圆桌引用的Versicolamide B、Alternaramide不在现行数据文件，fix表Alternaramide注仍"待复核"，与圆桌"已复核、维持降级"不符。【建议修】补S0两行；中文稿同步更新措辞。

11. 清单差异｜圆桌B档含土曲霉群(0.737)、茵陈螺甾烷苷元(0.716)，论文九候选未含。【建议修】中文稿说明两套清单从属关系。

12. Table 5｜07H239-A"computational control only"置于"prioritized candidates"表内，正文自洽但表格结构矛盾。【建议修】中文稿将对照档单独成块。

13. §2.7｜"binding-coverage propensity, not synergy, panel-conditional"已前置（合格）；建议同处补"不区分激动/拮抗、非药效预测、非用药推荐"。【建议修】

14. 中文表述｜樟芝首现写"牛樟芝(Antrodia cinnamomea)"；十味拉丁/中文名核对无误；五味子/灵芝"轴外而非无效"解释已在Discussion，中文稿应在Table 4附近保留。【建议修】

15. 验证确认（无需修改）｜tier 72/32/27、Table 4十行数值、epiberberine 0.710、水飞蓟11/11全OOD、4个正分THR-β（saikogenin A/D/F、schisandrol A）与csv一致；樟芝"species-level"三处统一；07H239-A降级三处自洽。

问题计数：15（必须修5、建议修9、确认1）。
