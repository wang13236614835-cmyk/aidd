# ChEMBL靶点ID与阳性对照药物核实报告
（全部经curl实际访问ChEMBL REST API验证，2026-08-17）

## 1. 靶点核实
| 靶点 | ChEMBL ID | pref_name | UniProt | 人源数据量(assay_type=B) |
|---|---|---|---|---|
| FXR/NR1H4 | CHEMBL2047 | Bile acid receptor | Q96RI1 | 总11,536；IC50 548；EC50 4,081 |
| THR-β/THRB | CHEMBL1947 | Thyroid hormone receptor beta | P10828 | 总1,287；IC50 644；EC50 200 |
| ACACA(ACC1) | CHEMBL3351 | Acetyl-CoA carboxylase 1 | Q13085 | 1,137 |
| ACACB(ACC2) | CHEMBL4829 | Acetyl-CoA carboxylase 2 | O00763 | 6,083 |

## 2. 阳性对照核实
| 药物 | molecule_chembl_id | 活性数据(实测) |
|---|---|---|
| OCA | CHEMBL566315 | vs FXR 92条；人源FXR EC50≈90-99nM (pChEMBL≈7.0)；max_phase 4.0 |
| GW4064 | CHEMBL318457 | vs FXR 128条；EC50 15-37nM |
| Resmetirom | CHEMBL3261331 | vs THRB 11条(EC50 73-2370nM)；2024年获批Rezdiffra |
| ND-646 | CHEMBL6012286 | vs ACACA IC50 0.37-1.0nM；vs ACACB 4.36-10nM |
| Soraphen A | CHEMBL1235782 | 仅3条(酵母/UNCHECKED)；无人源ACC数据 |
| TOFA | CHEMBL1562779 | 59条但vs人源ACACA/ACACB=0条 |
| 丹参酮IIA | CHEMBL187266 | vs FXR=0条！其FXR激动作用仅有文献支持 |

## 3. 实测踩坑记录
1. /activity/count.json不存在(404)；计数用activity.json?...&limit=0读page_meta.total_count
2. OCA搜索陷阱：q="obeticholic acid"首条CHEMBL266340是错误记录；正确ID经别名6-ECDCA/ocaliva命中
3. ND-646搜索陷阱：q="ND-646"命中错误分子；q="ND646"才正确
4. 丹参酮IIA在ChEMBL无FXR数据——天然产物FXR阳性对照需改用CDCA或注明文献来源
5. 人源ACC最可靠阳性对照=ND-646

## 4. 决策影响(本项目)
- FXR建模数据：IC50 548条(实测下载确认，与本项目step1一致)
- THR-β虽有644条IC50，但申报书选择对接代理评分——考虑到IC50混杂物种/测定体系且本项目
  时间约束，沿用对接代理策略，但报告需注明THR-β/ACC的ChEMBL数据量以备扩展
- 对接阳性对照：FXR用WAY-362450(33Y共晶配体)+OCA；THRβ用T3+resmetirom；ACC用ND-646+soraphen A
