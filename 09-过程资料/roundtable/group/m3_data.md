# M3 数据完整性与验证备忘录（2026-08-23）

结论：除下文"问题清单"A–H外，进论文数字全部溯源复核通过。原始文件路径前缀 `D:/zcode-workspace/mash_research/`（下略）。

## 一、验证结果（存储值 / 复算值）

**1. 双划分指标**（`results/tables/gnn_metrics_v2.json`；复算=由同文件 test_preds 重算 test-only）
| 划分(n_test) | 指标 | BGNN | RF | XGB |
|---|---|---|---|---|
| random(36) | R²/RMSE/ρ | .790/.723/.768 复算完全一致✓ | .845/.620/.811(存储) | .811/.686/.820(存储) |
| scaffold(34) | R²/RMSE/ρ | -.610/1.290/.533 复算完全一致✓ | .047/.992/.641(存储) | -.127/1.079/.483(存储) |
split 283/35/36、284/36/34，均=354✓。

**2. UQ指标**：σ-|err| Spearman json存值为 pooled val+test 口径（代码 step3b 确认）：random .340(n=71)、scaffold -.027(n=70)；test-only 复算 random +.585(p=1.8e-4)✓、scaffold +.269(p=0.124不显著)✓，FINAL_REPORT 已双口径披露✓。95%覆率 pooled：random .944(67/71)、scaffold .80(56/70)；test-only 复算 random 1.00(36/36)、scaffold .735(25/34)✓。ECE=.029/.062 由存储coverage复算✓（pooled口径）。

**3. 规模链**：548✓(raw行数)→449✓('='且nM共450条，1条无SMILES剔除；368唯一分子同剔1→367✓)→367-9 PAINS=358✓(`fxr_clean_before_ad.csv`)→-4杠杆=354✓(`fxr_final_dataset.csv`)；pIC50 3.38–9.96✓，max h=.043<h*=.0503✓。131=72+32+27✓(tier计数，规则h*、σ0.70逐行核验131/131✓)。233✓(`tcm_library_raw.csv`行数)；**224✗（见问题A）**。

**4. 靶点验证**（`target_genes_validation.csv` vs `data/geo/deg_*.csv`，13/13行逐一吻合✓）：NR1H4 -0.285/1.03e-2；THRB -0.315/1.99e-2；ACACA +0.897/7.42e-5；ACACB +0.631/4.23e-3（advF列亦✓）。GSE135251：Control 10/NAFL 51/NASH 155=216✓（series matrix复核），advF=68✓，DEG 3909✓(padj<0.05且|log2FC|>0.5)。KEGG第一名 hsa04976(Bile secretion) p=8.58e-4、padj=0.280（BH m=326复算精确✓，但见问题C）。

**5. 修正榜单**：v5 fix 前3 FINAL=0.859/0.792/0.786✓（公式0.35Act+0.25Dock+0.20Ev+0.10Nov+0.10Obt 十行全算✓，15→10删5无名/CAS条✓）。herb fix 前5收缩分 .5288/.4577/.4426/.4265/.3747✓(=score·n/(n+5))；雷公藤 .5653(第4)→.1615(第9)✓。CW-BCS成分公式(含eps=1e-3兜底)131/131✓、w=1/(1+σ)✓、药材top3几何均值/冗余惩罚/代表成分10/10✓。

**6. 对接**：阳性对照与文件一致✓：FXR 丹参酮IIA -9.73≈GW4064 -9.70>CDCA -8.70>OCA -6.77；THRβ resmetirom -10.11>T3 -9.52；ACC ND-646 -10.52 最强✓。重对接RMSD：33Y/3FLI 1.22Å、T3/3GWS 0.42Å、6U3/5KKN 0.76Å、S1A/3GID 0.33Å✓(均<2Å)。Spearman(μ,ΔG_3FLI)=-0.394 复算-0.3939✓ 但 n=10、p=0.26（见问题D）。NP对接极值 ACC -11.61(8-Oxocoptisine)、THRβ -10.28(Deoxyartemisinin)✓，262=131×2✓。

**7. 小檗碱**：μ=8.208→8.21✓（CID2353、σ=.639、h=.0225、域内高置信）；GNNExplainer 首要原子 N6(1.00)✓。

**8. v2 QSAR**（`results/v2/qsar_qa.json`，原始`data/v2/chembl_*.csv`）：n=原始行数✓者 ACC2 892/DGAT2 261/FDFT1 192/FXR 1567/SCD 239/THRb 622；R²=.514/.600/.700/.580/.393/.776。**n≠行数者见问题F**。

## 二、不一致 / 不可验证清单（最重要）
- **A(严重，阻断性)**：`data/tcm/tcm_library_raw.csv` 233条全部status=PUBCHEM_NOT_FOUND、`tcm_library_filtered.csv`为空——2026-08-17 22:19被一次网络失败重跑覆盖，而131化合物的np_fxr_predictions.csv(21:09)在前。**"224解析"无任何中间文件可证**，ADMET过滤(224→131)亦无法由存量文件复跑。定稿前须网络正常时重跑step4重建中间文件（131条CID仍在np_fxr_predictions可反向核对）。
- **B(口径)**：json中σ-|err|与coverage均为pooled val+test（random n=71/scaffold n=70），文件内无标注；论文引用必须写明口径，test-only值以本备忘录复算为准。scaffold两口径方向相反且均不显著，措辞用"欠校准"而非"负相关"。
- **C(显著性)**：KEGG第一名padj=0.28>0.05，仅名义显著（p=8.6e-4）；且超几何p无法离线复算（KEGG基因集未缓存），建议存档kegg link快照+获取日期。
- **D(显著性)**：Spearman=-0.394为n=10、p=0.26；1OSH结构ρ=-0.04。只能表述"方向一致（探索性）"。
- **E(数据质量)**：4条THRβ亲和能为正值（Saikogenin A/D/F +3.63/+4.66/+1.14、Schisandrol A +0.052），物理不合理、无note；仅影响4个底部化合物（eps兜底），建议剔除或脚注。
- **F(口径)**：v2 QSAR n=RDKit指纹化成功数，非原始行数（PPARG 3511/3568、LXRa 433/441、FASN 1123/1126、HMGCR 259/261）；论文注明"成功指纹化化合物数"。
- **G(版本)**：`ad_reference.json` n_train=358，AD参考建于杠杆剔除前(358)而非终版354，需注明。
- **H(未复算)**：RF/XGB基线与v2 testR²为存储值（seed=42可复跑，建议投稿前重跑一次留档）；IL6在DEG矩阵中缺失（表中留空，脚注说明）。

## 三、数据可用性声明（草稿）
转录组：GEO GSE135251（216样本，10对照/51 NAFL/155 NASH）。FXR建模：ChEMBL CHEMBL2047（人IC50，assay B；清洗链548→449→367→354）。多靶点QSAR：ChEMBL CHEMBL4829/2439944/4158/3338/2047/402/2808/235/1275210/1947。结构：PDB 3FLI、1OSH、3GWS、5KKN、3GID（共晶配体33Y/FEX/T3/6U3/S1A）。天然产物：PubChem PUG-REST按名解析，逐成分CID见np_fxr_predictions.csv（如小檗碱CID2353、丹参酮I CID114917）。通路：KEGG REST（hsa04976等）。代码：src/step0–v5全流程脚本；全部汇总表：results/tables、results/v2、results/v5。作者声明所有论文数字可由上述文件+脚本复现。

## 四、数字-来源对照表骨架（论文附表）
| 论文位置 | 数字 | 来源文件 | 复核 |
|---|---|---|---|
| 结果2.1 表1 | R²/RMSE/ρ×6 | gnn_metrics_v2.json+test_preds复算 | ✓(BGNN)存储(RF/XGB) |
| 结果2.2 | σ-err ρ、95%覆率、ECE | 同上（pooled+test-only双口径） | ✓需标口径 |
| 方法3.1 | 548/449/367/354、3.38–9.96 | chembl 3个csv+dataset_summary.txt | ✓ |
| 方法3.4 | 233/224/131、72/32/27 | tcm_library_raw/np_fxr_predictions | 224✗待重建 |
| 结果3.1 | 4靶点log2FC/padj、10/51/155、3909 | target_genes_validation+deg_*.csv+geo_summary | ✓ |
| 结果3.2 | hsa04976 p/padj | kegg_ora_top25.csv | ✓padj>0.05需声明 |
| 结果4 | v5前3、herb前5、雷公藤 | final_unified_scores_fix/herb_cwbcs_ranking_fix | ✓ |
| 结果5 | 对照排序、4 RMSD、-0.394 | positive_controls/redock_validation/fxr_crossdocking | ✓(-0.394需标n,p) |
| 结果6 | 小檗碱8.21、N6 | np_fxr_predictions/gnnexplainer_top_atoms | ✓ |
| 补充 | v2各靶n/R² | qsar_qa.json+data/v2 | 口径F |
