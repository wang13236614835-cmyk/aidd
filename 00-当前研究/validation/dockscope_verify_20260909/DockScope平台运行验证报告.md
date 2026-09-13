# DockScope 平台运行验证报告（2026-09-09）

**验证对象**：2026-09-05 归档的 CCD 修正独立起始重对接诊断（`validation/redock_corrected_20260905/`，开放门控 `pending_receptor_review_and_multiseed`）。
**执行方式**：DockScope 平台（`D:\dockscope\DockScopeLicensed`，Electron 前端 + Python 后端，内置 vina.exe / Vina-GPU-CUDA / smina / gromacs）。
**性质**：干实验方法学验证。不产生新候选榜，不放行药效/机制主张；受体审核（项目 27/28 开放项）仍未完成。

## 一、验证设计与输入

| 项 | 内容 |
|---|---|
| 靶点/配体 | THRB–2J4A–OEF（C18H18Br2O4）、FASN–7MHD–ZEP（C20H21FN2O2S2），CCD 修正化学 |
| 受体 | 项目归档 `03-课题-MASH研究-v2/docking/receptors/{THRB_2J4A,FASN_7MHD}.pdbqt`（sha256 与归档诊断一致：c9a69f39… / 0a926334…） |
| 配体起始 | 独立 ETKDG 构象（项目脚本在线重生成，非晶体几何记忆） |
| RMSD 协议 | Meeko 重建姿态 → RDKit `CalcRMS` 不叠合，对比 CCD 修正晶体参照；阈值 < 2.0 Å（与 validate_docking.py 完全一致） |
| RMSD 管线自检 | 对归档 THRB 姿态重算 = 0.7192，与归档值逐位一致 |

## 二、验证一：DockScope GUI 全自动管线（自动口袋检测）

在 DockScope「上传并运行」界面提交两个运行（引擎 AutoDock Vina CPU，exhaustiveness 8，seed 1，自动口袋 cb_dock2_inspired_grid，max_pockets=1）：

| 运行 | 状态 | 最佳 Vina 得分 | 最佳模式 RMSD（vs 晶体） | 2 Å 门控 |
|---|---|---|---|---|
| AIDD-verify-THRB-2J4A-OEF-redock | completed | −7.028 | 18.83 Å | **未通过** |
| AIDD-verify-FASN-7MHD-ZEP-redock | completed | −7.911 | 13.15 Å | **未通过** |

**原因（非化学/引擎问题）**：自动口袋检测 top-1 口袋中心偏离共结晶位点 —— THRB 偏 12.4 Å、FASN 偏 12.5 Å，搜索盒仅覆盖晶体配体约 62%/59% 原子，构造上即无法恢复晶体姿态。口袋候选全列表中：THRB 正构口袋最近候选排第 9/10（C9，7.7 Å）；FASN 最近候选即 12.5 Å，**无一命中**。

**结论**：DockScope 上传页默认自动口袋模式**不适用于**重对接验证或以已知位点为前提的正构筛选；此类任务必须固定盒子（见验证四）。

## 三、验证二：项目协议在 DockScope 引擎上的复现（seed 42）

以 `VINA_BIN=D:\dockscope\...\tools\vina.exe` 运行项目 `validate_docking.py`（固定晶体盒、exhaustiveness 16/32）。该 vina.exe 与 2026-09-05 归档诊断所用二进制 sha256 完全相同（e0c4b271…，AutoDock Vina 1.2.7 官方发布件）。

| 靶点 | 本次 | 归档(20260905) | 一致性 |
|---|---|---|---|
| THRB | 0.7192312541304148 | 0.7192312541304148 | 逐位一致 |
| FASN | 2.076567383188259 | 2.076567383188259 | 逐位一致；门控仍未通过（按协议报错终止） |

**结论**：归档重对接诊断**确定性复现通过**；FASN 单种子未过的记录获独立确认。

## 四、验证三：多种子敏感性（项目开放门控 multiseed 项的新证据）

同一协议、同一引擎，仅换随机种子：

| seed | THRB RMSD (Å) | FASN RMSD (Å) |
|---|---|---|
| 42（归档） | 0.719 ✅ | 2.077 ❌ |
| 7 | 0.724 ✅ | 2.088 ❌ |
| 123 | 0.625 ✅ | 2.080 ❌ |
| 20260909 | 0.728 ✅ | **1.629 ✅** |

- **THRB/OEF：4/4 种子通过（0.63–0.73 Å）**——CCD 修正化学下姿态恢复稳健，多种子证据支持该门控项关闭（受体审核仍开放）。
- **FASN/ZEP：1/4 种子通过**，未过种子均贴在 2.08 Å 阈值缘——姿态恢复**种子敏感、界缘可恢复**。建议以多种子通过率/中位数报告该门控，不以单种子宣判；与结构审计中 FASN retry 1.657 的历史一致。

## 五、验证四：DockScope 平台内固定晶体盒子重对接（结果工作台 Edit docking box）

在 DockScope 结果工作台用 "Edit docking box → Save & re-dock" 将盒子改为项目晶体盒子，使用**平台自制备的受体/配体**与平台 vina 引擎（seed 1）：

| 靶点 | 盒子（center/size） | 最佳得分 | 最佳模式 RMSD | 2 Å 门控 |
|---|---|---|---|---|
| THRB | 4.25/20.95/32.03；31.6/29.8/25.0（ex16） | −10.73 | **0.609 Å** | **通过** |
| FASN | 1.43/61.22/170.07；23.0/26.8/26.9（ex8） | −10.33 | **1.654 Å** | **通过** |

- 位点正确时平台管线两靶点姿态恢复**均通过**；FASN 在晶体盒子下得分 −10.33 显著优于自动口袋错位点的 −7.91，进一步佐证正构位点判定。
- **平台缺陷记录**：任务目录名内嵌输入文件完整路径，深路径下超过 Windows 260 字符限制，导致 "Save & re-dock" 的 docked.pdbqt 写出失败（vina returncode=1；打分已正常算出）。FASN 姿态文件按平台日志中的原命令、短输出路径重放获得，模式 2–9 打分与平台日志逐位一致。后续在平台内跑长路径输入需注意此限制。

## 六、结论与边界

1. AIDD 项目当前对接诊断在 DockScope 平台引擎上**可复现**（seed42 逐位一致）；THRB 姿态恢复获 4 种子 + 平台固定盒子共 5 组证据稳健支持（0.61–0.73 Å）；FASN 界缘、种子敏感（1/4 种子过，平台固定盒子 1.654 Å 过）。
2. DockScope **上传页默认自动口袋模式**对 2J4A/7MHD 不能命中正构位点，不能替代固定盒子协议；**结果工作台 Edit docking box 可以**且两靶点均通过——平台适用于固定盒子验证/筛选，生产使用前必须逐受体核对口袋。
3. 平台长路径输出 bug（Windows MAX_PATH）见验证四；在平台内使用浅路径输入可规避。
4. 以上均为结构方法学验证，不构成靶点功能、MASH 疗效或候选化合物放行证据；受体质子化/链审核（项目开放项 27/28）未包含在本轮。

## 产物索引

- 汇总：`dockscope_redock_verification.json`（GUI 两运行 + 复现 + 多种子 + 平台固定盒子，含命令与哈希）
- GUI 运行留痕：`dockscope_THRB/`、`dockscope_FASN/`（自动口袋 docked.pdbqt、晶体盒子 docked.pdbqt、pockets.json、job.json、结果 CSV）
- 协议复现：`protocol_seed42/`、`protocol_seed7/`、`protocol_seed123/`、`protocol_seed20260909/`
- 本报告与脚本：`DockScope平台运行验证报告.md`、`verify_dockscope_poses.py`
- DockScope 原始任务目录：`C:\DockScopeData\workspace\dockscope\data\jobs\AIDD-verify-*`
