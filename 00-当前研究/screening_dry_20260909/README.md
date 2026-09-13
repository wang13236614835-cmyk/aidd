# 重启对接筛选：54 条保肝中药 NP 库 × 三靶固定盒子（2026-09-09）

**性质：计算排序假设（dry screening hypothesis）。不构成候选放行、药效或机制主张**；承接 `candidate_release: false` 的既定边界，本轮只重做"实验对接筛选"这一层，不重建加权候选榜（审计 A11 教训）。

## 协议（全部要素当日验证）

| 要素 | 值 | 验证依据 |
|---|---|---|
| 引擎 | DockScope 内置 vina.exe（sha256 e0c4b271…，Vina 1.2.7） | 20260909 与项目归档 seed42 逐位复现 |
| 靶点/盒子 | THRB 2J4A（4.25/20.95/32.03；31.6/29.8/25.0）、FASN 7MHD（1.43/61.22/170.07；23/26.8/26.9）、FXR 1OSH（5.23/29.0/53.67；19.4/22.5/24.8），全部晶体配体盒子，固定 | THRB 5/5 组姿态恢复 0.61–0.73 Å；FASN 平台固定盒 1.654 Å（界缘，种子敏感 1/4，排名按界缘解读）；FXR/FEX 本轮门控 0.838 Å |
| 配体库 | `np_library_filtered.csv` 54 条（茵陈/虎杖/山楂/葛根/桑叶/决明子/泽泻等） | 结构可解析、规范异构不重复（项目已核）；**身份/CID/药材来源人工审核 0/54 pending** |
| 配体制备 | SMILES→ETKDGv3(seed42)→MMFF→Meeko PDBQT；独立起始、无晶体几何记忆 | 与 validate_docking.py 同管线；rdkit 2026.03.3 / meeko 0.7.1 |
| 对接参数 | exhaustiveness 8，num_modes 9，seed 42，cpu 8 | 单种子单 exhaustiveness，未做多种子中位数 |
| 排序 | 每靶按 Vina 最佳得分透明排序；另给等权平均排名列（**仅浏览参考，非加权候选分**） | 不做 TOPSIS/硬编码权重 |

运行：162/162 全部完成、零失败，耗时 1604 s。元数据（受体/库/引擎哈希、命令）见 `screening_results.json`。

## 结果

### 分靶 Top-10（Vina kcal/mol，越负越强）

**FXR（门控 0.838 Å）**：moracin N −9.32｜genistin −9.28｜catechin −9.04｜piceid −9.00｜formononetin −8.95｜3'-methoxydaidzein −8.91｜daidzein −8.79｜moracin M −8.75｜biochanin A −8.62｜oxyresveratrol −8.61

**THRB（门控 0.61–0.73 Å 稳健）**：moracin N −11.24｜daidzein −10.09｜catechin −9.77｜capillarisin −9.73｜moracin M −9.66｜3'-methoxydaidzein −9.64｜oxyresveratrol −9.60｜epicatechin −9.46｜biochanin A −9.32｜formononetin −9.23

**FASN（门控 1.654 Å 界缘）**：moracin N −10.20｜daidzin −9.76｜mulberrofuran G −9.75｜formononetin −9.71｜ononin −9.70｜puerarin −9.67｜daidzein −9.62｜maslinic acid −9.48｜piceid −9.43｜alisol B −9.41

### 三靶同时进 Top-20 的一致名单（13 条）

moracin N（桑叶，三靶均第 1）｜daidzein（葛根）｜formononetin（葛根）｜3'-methoxydaidzein（葛根）｜daidzin（葛根）｜moracin M（桑叶）｜piceid（虎杖）｜biochanin A（葛根）｜genistin（葛根）｜epicatechin（山楂）｜capillarisin（茵陈）｜isorhamnetin（茵陈）｜toralactone（决明子）

完整表：`results_per_target_long.csv`（每靶全排名）、`results_summary_wide.csv`（宽表+一致标注）。

## 与历史失效榜（MASH v2 TOPSIS）的差异

历史榜首 3'-methoxydaidzein 在本轮一致名单第 4；历史第 2 catechin 本轮 FASN 跌出 Top-10；历史榜 10 名开外的 **moracin N 本轮三靶全部第 1**。差异来源：历史榜由 QSAR 预测 pIC50 主导的 TOPSIS 加权 + 部分旧盒子/旧化学；本轮为纯 Vina 得分 + 验证过的晶体盒子。**这正说明排名强烈依赖方法与权重——任何单榜都不应解读为药效序**，两组排名的分歧本身是需向组内和导师呈现的事实。

## 边界与后续

1. 库身份审核 0/54 pending：名称/CID/药材来源未经人工全量核验，排名以"库内相对位置"为准；
2. FASN 门控界缘（种子敏感）：FASN 列单独解读需谨慎；
3. 单种子 ex8：稳健名次需多种子复跑（THRB/FXRB 门控已稳健，可先跑）；
4. 受体质子化/链审核（项目开放项 27/28）未包含；
5. 前续验证见 `../validation/dockscope_verify_20260909/`。

## 产物索引

- `run_screening.py`、`summarize.py`（可复现：`python run_screening.py --screen`）
- `gate/`（FXR 门控）、`ligands_pdbqt/`（54 个制备配体）、`docking/{FXR,THRB,FASN}/`（162 个姿态与日志）
- `screening_results.json`（元数据+全记录）、`results_per_target_long.csv`、`results_summary_wide.csv`、`screen_run.log`
