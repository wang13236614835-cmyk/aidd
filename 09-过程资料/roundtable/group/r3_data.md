# R3 数据侧最终回应（2026-08-23）

## 1. 问题A定案：选(c)两步走
np_fxr_predictions.csv（21:09，131条CID锚定、逐行复算通过）为不依赖网络的证据基线；同时择网络稳定时重跑step4（约6分钟）重建233→224→131中间文件，以131条CID反核对：新链产出与原131集CID完全一致→224可用，方法注明"intermediates rebuilt 2026-08-XX, CID-verified 131/131"；不一致→弃用224，仅写233→(ADMET)→131。SI无论如何如实记录2026-08-17 22:19网络失败重跑覆盖事件。理由：224无中间证据是客观缺口，(b)单独补不齐，(a)单独无兜底。

## 2. B2/v6数字：可复算（今日实跑验证）
v6_conformal.py复跑与conformal_calibration.json逐键bit级一致（纯确定性、全离线存量输入）；v6b复跑sanity μ-Pearson 0.9997、y/smiles全匹配、M5 flat q̂=2.9835、cov=1.0(34/34) Wilson[0.8985,1.0]，与存值一致（torch 2.2.0 CPU，seed(0)下MC dropout可确定复现）；抽查M0覆率0.7353=25/34、Wilson[0.5688,0.854]手算吻合。两脚本满足"可复现"标准，进开源包。引用注意：M5宽度2.983是n_cal=36下95%分位取最大值（必然保守），按M1双档呈现；alpha_020节键名"coverage95"实为80%覆率，须改名或SI注明后方可引用。

## 3. 数据可用性声明（定稿）
GEO GSE135251（216：10/51/155）；ChEMBL CHEMBL2047及4829/2439944/4158/3338/402/2808/235/1275210/1947；PDB 3FLI/1OSH/3GWS/5KKN/3GID（配体33Y/FEX/T3/6U3/S1A）；PubChem PUG-REST逐成分CID见np_fxr_predictions.csv（小檗碱CID2353）；KEGG REST hsa04976（快照+获取日期）；代码src/step0–v6b与results全部汇总表开源（仓库/Zenodo DOI）。句式："All numbers are regenerable from the archived raw files and scripts (src/step0–v6b); source data are available from GEO/ChEMBL/PDB/PubChem/KEGG under the accessions above."

## 4. 对照表：进SI（Table S0）
四列（论文位置/数字/来源文件/复核状态）沿用备忘录骨架，增补v6行（M0–M5覆率与宽度←conformal_calibration.json，复算✓）。先手透明、审稿可自查，优于rebuttal被动应对；rebuttal仅引用SI表。

## 5. C–H最终措辞各一句
- C：写"ranked first by nominal p=8.6e-4 (BH padj=0.28, not significant after correction)"，并存档KEGG快照及获取日期。
- D：只写"directionally consistent but exploratory (ρ=−0.39, n=10, p=0.26)"，不进任何结论句。
- E：剔除4条正亲和能（Saikogenin A/D/F、Schisandrol A），SI列清单并注"剔除不改排名"。
- F：表注"n = RDKit成功指纹化化合物数（原始：PPARG 3568→3511、LXRa 441→433、FASN 1126→1123、HMGCR 261→259）"。
- G：方法注明"AD reference built on the pre-leverage-filter set (n=358)"。
- H：投稿前seed=42重跑RF/XGB与v2 testR²留档；IL6脚注"not quantified on the GSE135251 platform"。

## 6. 不可让步项
① 224只能"重跑且CID 131/131反核对通过"或"弃用"二选一，无第三种写法；② 一切覆率/ρ必须带口径标签（pooled/test-only）+n+Wilson CI，v6 alpha_020键名更正后方可引用。
