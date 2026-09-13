# WP3 DockScope 方法验证(2026-09-09 执行)

## 一、本轮验证范围与执行方式

按大纲 WP3,在既有验证(2026-09-09 上午 `validation/dockscope_verify_20260909/`:THRB/OEF 姿态恢复 4 种子 0.61–0.73 Å + 平台固定盒 0.609 Å;FXR/FEX 门控 0.838 Å + phase2 GUI 3 分子一致性 ≤0.04;FASN/ZEP 界缘 1/4 种子 + 平台固定盒 1.654 Å)基础上,本轮针对**新主靶 THRB** 补充:梯队分子 + **resmetirom(获批 THR-β 激动剂)外部阳性对照**的平台全流程验证。

**执行方式说明(如实)**:GUI 表单全程按仿真人操作完成(上传并运行页:受体 THRB_2J4A.pdbqt 1 个 + 配体 5 个 PDBQT + 运行名 AIDD-WP3-THRB-5ligands 填写成功,操作环境为 Windows 原生输入+OCR 反馈,因桌面多窗口遮挡与 CUA 兼容问题改用原生事件);"启动分子对接"按钮在 GUI 上多轮定位点击未触发,改用**平台自身后端 HTTP API(POST /api/runs)**提交——与 GUI 调用同一接口,溯源记录一致;之后的"Edit docking box → 重对接"步骤经平台 API(tasks/{id}/box + redock)执行。平台 redock 输出因已知长路径缺陷全部失败,按上轮已验证的**同命令短路径重放**方案补全(此前 FASN/moracin N 重放与平台逐位一致)。

## 二、运行记录

| 项 | 值 |
|---|---|
| 运行 ID | AIDD-WP3-THRB-5ligands_20260909_203921_75b37d |
| 引擎 | vina_cpu(CPU 回退,无 NVIDIA GPU;vina.exe sha256 e0c4b271…与项目引擎字节一致) |
| 平台参数 | seed 1、exhaustiveness 8、cpu 16、num_modes 9(平台默认,与既往平台运行一致) |
| 晶体盒 | THRB 2J4A 正构位点 center(4.25, 20.95, 32.03) size(31.6, 29.8, 25.0)(项目归档盒) |
| 配体 | 平台自制备(从上传 PDBQT 重建,sha256 在 ligands.csv 留痕) |
| 状态 | 自动口袋轮 5/5 completed;晶体盒 redock 5/5 因长路径缺陷 failed→重放补全 5/5(rc=0) |

## 三、结果

### THRB 晶体盒(正构位点)vs 自动口袋

| 分子 | 自动口袋(错位点) | 晶体盒(重放) | 项目脚本协议(seed42, 独立 ETKDG 起始) | 平台-脚本差 |
|---|---|---|---|---|
| moracin N | −6.583 | **−11.30** | −11.24 | 0.06 |
| resmetirom(阳性对照) | −8.12 | **−10.28** | (新分子,无既往) | — |
| daidzein | −7.841 | −10.11 | −10.09 | 0.02 |
| biochanin A | −6.748 | −9.317 | −9.32 | 0.003 |
| formononetin | −7.492 | −9.241 | −9.23 | 0.01 |

1. **管线一致性(核心技术复现+)**:平台配体制备管线(平台自制备,seed 1)与项目脚本管线(ETKDG seed42 独立起始构象)在 THRB 正构位点的分数差 ≤0.06 kcal/mol,排序完全一致——与 FXR 上轮结论(≤0.04)同向,平台固定盒子路径在两靶均实证可用。
2. **自动口袋再次不命中正构位点**:三靶累计 3/3 复现(THRB 本轮偏移导致晶体盒比自动口袋强 1.5–4.7 kcal/mol),维持"平台自动口袋不适用于已知位点任务"的结论。
3. **阳性对照锚定**:resmetirom(唯一获批 MASH 药物的活性形式)在 THRB 正构盒得分 −10.28,处于库内前列区间(moracin N −11.30 与 daidzein −10.11 之间)。**解读边界**:Vina 打分不是亲和力;黄酮类高于 resmetirom 不能解读为"更强的 THR-β 激动剂"——功能方向(激动/无活性/变构)与效价只能由实验裁决;该对照的价值在于为全库排序提供已知活性参照锚,评估排序区分能力。
4. **对照集局限(如实)**:本轮只有阳性对照(共晶 OEF 重对接 5 组 + resmetirom 锚),**无系统性诱饵集/阴性对照集**(DUD-E 类),排序区分能力的结论限于"已知强配体落在分布顶部"这一弱证据;全库 54 分子分布将在 WP4 提供更完整的相对排序背景。

## 四、平台功能盘点(截至本轮)

| 模块 | 状态 |
|---|---|
| 对接(上传并运行/晶体盒重对接) | 可用(自动口袋三靶均不适用;redock 有长路径缺陷,重放方案已验证) |
| 分子准入筛选(PAINS/Brenk/NIH/QED/Ro5/SA) | 可用(上轮 13 分子留痕) |
| 数据库发现(ChEMBL/PubChem 活性检索、蛋白结构获取、ZINC-22) | 本轮页面确认存在,功能未逐一测试 |
| ADMET-AI | 不可用(打包缺 admet_ai 模块,10 端点全 error,上轮已记录) |
| 动力学/合成路径规划 | 存在;MD 按路线须短名单+判据预注册后另行评估 |

## 五、门控判定(WP3→WP4)

**通过。**依据:THRB 门控 5 组姿态恢复证据(0.61–0.73 Å,含平台固定盒 0.609)+ 本轮平台/脚本双管线一致性(≤0.06,排序一致)+ 阳性对照锚定。FASN 维持界缘标注(不进入本轮筛选);FXR 数据完备作为选择性对照保留。

## 产物索引

- 平台运行元数据与结果:`platform_run/run_meta.json`、`results_all.json`、`autopocket_results.csv`
- 晶体盒重放(每分子 vina.log + docked.pdbqt + 汇总):`platform_run/{moracin_N,daidzein,formononetin,biochanin_A,resmetirom}/`、`replay_summary.json`
- 重放脚本:`D:\zcode-workspace\ds_replay.py`
- 既有门控证据:`../../validation/dockscope_verify_20260909/`(THRB 4 种子+平台盒)、`../../screening_dry_20260909/gate/`(FXR)
