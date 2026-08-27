# 审稿人C · 第三轮数据体检备忘录（2026-08-23）

本轮实测复算（Python 重算 + MATLAB 独立交叉验证），对照 Table S0 抽查 20+ 个数字。

## 一、复现状态总表

**问题 A–H 闭环情况：**

| 旧问题 | 状态 | 证据/缺口 |
|---|---|---|
| A 中药库覆盖事件 | 基本闭环 | step4 已重跑（log 233→224→131，herb 计数逐项吻合）；tcm_library_raw.csv 现 status OK=224/NOT_FOUND=9，filtered=131 行。**但 129/131 CID 反核对结果没存档**（哪 2 个变了无处可查） |
| B σ-err/覆率口径 | 已闭环 | 正文 §2.5/§3.3 双口径+附注；v6 json 带 test-only 段；本轮复算 random +0.585/scaffold +0.269 一致 |
| C KEGG 显著性 | 部分闭环 | 已降级为名义显著（padj=0.28 如实写入）；**KEGG 基因集快照+获取日期仍未存档**（data/ 下无任何 kegg 文件） |
| D 交叉对接 n=10 | 已闭环 | 全文标注"探索性，p=0.26"；复算 ρ=−0.3939✓ |
| E THRβ 正分 | 已闭环 | 脚注+标记不剔除（D10 执行） |
| F v2 n 口径 | 不适用 | 本稿未引用 v2 QSAR 数字 |
| G AD 参考 n=358 | 已闭环 | §2.2 明写"fitted on n=358"；h*=3×6/358 复算到小数点后 10 位一致 |
| H RF/XGB 存储值 | 已闭环 | baseline_recheck.json：4 组 R²/RMSE/MAE/ρ 逐位 match=true。**但 S0 未收录此文件与 v6c 脚本** |

**本轮抽查数字（全部实测）：** Wilson CI：25/34→[0.5688,0.854]、34/34→[0.8985,1.0]，与论文完全一致；覆率分子还原 M0=25、M1=26、M2=24、M3=22、M4=21（/34）✓。test-only 指标由 test_preds 重算：random R²=0.7898/RMSE=0.7228/ρ=0.7681、scaffold −0.6101/1.2900/0.5328 ✓；pooled σ-err 0.3404/−0.0268、pooled 覆率 0.9437/0.80 ✓。杠杆 0.0126/0.0096、0%>h* ✓。三级 72/32/27 ✓，tier 规则（h≤0.0503、σ≤0.70）逐行 0/131 错 ✓，中位 σ 0.583/0.769/0.805=图3 的 0.58/0.77/0.81 ✓。收缩算术 10/10 ✓（0.5288/0.4577/0.4426/0.4265/0.1615…）。小檗碱 μ=8.208/CID2353 ✓，表小檗碱碱 CW-BCS 0.7101→0.710 ✓。靶点 4 基因 log2FC/padj 逐格 ✓；FASN 2.473→2.47 等 4 对照 ✓；KEGG 8.58e-4/0.2799 ✓。阳性对照 7 个对接分 ✓；重对接 RMSD 1.22/0.42/0.76/0.33（docking/redock_validation.json）✓；np_docking 262=131×2 ✓。GEO 10/51/155、DEG 3909 ✓；354 行、pIC50 3.379–9.959 ✓；548/358/354 文件在（449/367 仅由脚本可推）。图1/3/4 数字与源文件一致。**MATLAB 独立复算（matlab -batch，脚本存 roundtable3/wilson_check_matlab.m）：6 组 Wilson CI + h* 全部一致，OVERALL=true。**

## 二、遗留问题清单

1. **Table 4 柴胡行"Raw s=0.107"用错列**（中危）：herb_cwbcs_ranking_fix.csv 里柴胡 herb_score=0.0990（冗余惩罚后、收缩前，即图4 竖刻度线位置），0.107 是惩罚前的 topK 几何均值；同表水飞蓟 0.415 用的却是惩罚后口径，同列自相矛盾。修法：改为 0.099，或在表注定义"raw=冗余惩罚后"。
2. **丹参舍入不一致**（低危）：真值 0.4265，Table 4 写 0.427、图4 显示 0.426（Python %.3f）。统一为 0.426。
3. **图2 参考线标签误导**（中危）：虚线画在 3.29（=半程 6.58/2，作半宽对比是对的），但标签写"full pIC50 range (3.38–9.96)"。摘要"半宽 2.98 approaching full dynamic range"同样把半宽与全距比。修法：标签改"half of full range (3.29)"；摘要建议改"区间宽度 5.96≈全距 6.58 的 91%"。
4. **无 requirements.txt/environment.yml**（投稿前必须）：全仓搜不到任何依赖清单，"脚本可复现"承诺缺支撑。列出 python/numpy/pandas/scipy/rdkit/torch/PyG/xgboost/sklearn/vina 版本。
5. **S0 落后于现状**（低危）：缺 baseline_recheck.json+v6c 行（这是加分项，应写进"独立验证"列）；也没有"图1–4←make_figures.py←各源文件"行——make_figures.py 目前只在 SI 末尾脚本清单出现，建议同时进 S0。
6. **129/131 CID 反核对无存档**（中危）：两个变化的化合物是谁、新旧 CID 各是什么，没有任何文件记录，SI 声明不可追溯。跑一次 5 分钟的对比并存 CSV，SI S3 点名这 2 个。
7. **数据库版本/访问日期缺失**（中危）：ChEMBL release 号未记录（step1 未抓 /status.json），GEO/ChEMBL/PubChem/KEGG 访问日期只能靠文件时间戳推断（2026-08-17）。中文版数据可用性段规范写法："GEO 登录号 GSE135251（访问日期 2026-08-17）；ChEMBL（release X，CHEMBL2047，IC50，assay B，访问日期…）；PubChem PUG-REST（逐成分 CID 见附表）；PDB 3FLI/1OSH/3GWS/5KKN/3GID；KEGG REST（hsa）"。现在补抓一次 chembl status 记当前版本并注明"获取时未记录版本"。
8. **中文版图的数字一致性**：图重制中文标签时禁止手工改数字——把 make_figures.py 的标签抽成中英字典参数化重跑，数据仍从同一批 CSV/JSON 读入，重制后逐图 diff 数字标注。
9. **MATLAB 交叉验证**：已做（见上），最省事方式即 `matlab -batch "run('wilson_check_matlab.m')"`，一次约 1 分钟；建议把输出留档作为内部审计记录，期刊不需要。
10. 小项：IL6 在靶点表中为空（正文未用，SI 可加一句脚注）；449/367 中间清洗文件未存 CSV（可由 raw+脚本重推，建议顺手存档）。

## 三、投稿前检查单（按时间顺序）

**必做：**
1. 改 Table 4 柴胡 raw 0.107→0.099、丹参统一 0.426，重出图4 无需（图是对的）。
2. 改图2 参考线标签并重跑 make_figures.py 重出图2；同步微调摘要措辞。
3. 更新 S0：加 baseline_recheck.json、v6c、图-源数据行。
4. 存档 CID 对比 CSV（2 个差异化合物点名）并补进 SI S3。
5. 写 requirements.txt + README（脚本运行顺序、随机种子、软件版本）。
6. 整理"图源数据"附表（每图一张 CSV：图1/2 的点值与条值、图3 计数与中位σ、图4 排名值），进 SI 或 Zenodo 预打包。
7. 数据可用性段补齐版本与访问日期；存 KEGG 快照。
8. 人工：补全作者名单/ORCID/邮箱/经费号/审稿人建议（决策纪要遗留 2）。
9. 加一句伦理说明："本研究为纯计算与公共数据再分析（GEO/ChEMBL/PubChem/PDB/KEGG），未涉及人体或动物实验，无需伦理审批"——中文期刊通常仍要求此声明，ACS Omega 加上无害。
10. Zenodo 先建私有 draft 把 results+scripts 传好，"接收后公开"只差一键。

**建议做：** 11. 全流程在干净环境空跑一遍（至少 step1→step4 + v6）；12. MATLAB 复算日志归档；13. 中文导读同步本轮三处数字修正。
