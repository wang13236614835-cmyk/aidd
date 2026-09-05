# -*- coding: utf-8 -*-
"""
S1: 病理学靶点确证（全新数据）。
主队列 GSE48452 (n=73, 肝活检, 对照→单纯脂肪变→NASH) + 复验队列 GSE63067 (n=18)。
方法：芯片series matrix → 探针注释 → limma风格(Welch t + BH) DE →
     THRB/FASN/SCD1 靶点方向验证 + 经典对照基因 + KEGG ORA。
不使用旧项目任何代码或数据。
"""

# Historical pipeline: its outputs are invalidated; corrected code lives in 00-当前研究.
raise RuntimeError("此历史入口已停用以保留原数据与结果；请使用仓库00-当前研究中的诊断/修订流程。")
import gzip, io, json, os, re, urllib.request
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

D = "D:/zcode-workspace/mash_v2_new"
GEO = f"{D}/data/geo"
os.makedirs(GEO, exist_ok=True)

def fetch(url, path):
    if not os.path.exists(path):
        req = urllib.request.Request(url, headers={"User-Agent": "academic-research/2.0"})
        with urllib.request.urlopen(req, timeout=300) as r, open(path, "wb") as f:
            f.write(r.read())
    return path

# ---------- 下载 ----------
SERIES = {
    "GSE48452": "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE48nnn/GSE48452/matrix/GSE48452_series_matrix.txt.gz",
    "GSE63067": "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE63nnn/GSE63067/matrix/GSE63067_series_matrix.txt.gz",
}
for gse, url in SERIES.items():
    p = fetch(url, f"{GEO}/{gse}_series_matrix.txt.gz")
    print("downloaded:", gse, os.path.getsize(p) // 1024, "KB")

def parse_matrix(path):
    txt = gzip.open(path, "rt", encoding="utf-8", errors="ignore").read()
    samples, chars, plat = [], {}, None
    expr_start = None
    lines = txt.splitlines()
    table_rows, in_table = [], False
    for i, line in enumerate(lines):
        if line.startswith("!Series_platform_id"):
            plat = line.split("\t")[1].strip('"')
        elif line.startswith("!Sample_geo_accession"):
            samples = [x.strip('"') for x in line.split("\t")[1:]]
        elif line.startswith("!Sample_characteristics_ch1"):
            vals = [x.strip('"') for x in line.split("\t")[1:]]
            key = re.sub(r":.*$", "", vals[0]).strip()
            chars.setdefault(key, [])
            chars[key] += [re.sub(r"^[^:]*:\s*", "", v).strip() for v in vals]
        elif line.startswith("!series_matrix_table_begin"):
            in_table = True
        elif line.startswith("!series_matrix_table_end"):
            in_table = False
        elif in_table and not line.startswith('"ID_REF"'):
            table_rows.append(line)
    expr = pd.DataFrame(
        [r.split("\t") for r in table_rows])
    expr = expr.set_index(0)
    expr.index = expr.index.str.strip('"').str.replace('"', '', regex=False)
    expr.columns = samples[: expr.shape[1]]
    expr = expr.apply(pd.to_numeric, errors="coerce")
    meta = pd.DataFrame(chars, index=samples)
    return expr, meta, plat

def bh(p):
    return multipletests(p, method="fdr_bh")[1]

def analyze(gse):
    expr, meta, plat = parse_matrix(f"{GEO}/{gse}_series_matrix.txt.gz")
    print(f"\n===== {gse} | platform {plat} | expr {expr.shape} =====")
    print("metadata fields:", list(meta.columns))
    # 找分组列
    gcol = None
    for c in meta.columns:
        vals = set(str(v).lower() for v in meta[c])
        if any(k in vals for k in ["nash", "steatosis"]) or \
           any(("nash" in v or "steat" in v or "normal" in v or "control" in v or "healthy" in v)
               for v in vals):
            gcol = c
            break
    print("group col:", gcol)
    print(meta[gcol].value_counts().to_string() if gcol else "!! no group col")
    return expr, meta, plat, gcol

expr1, meta1, plat1, gcol1 = analyze("GSE48452")
expr2, meta2, plat2, gcol2 = analyze("GSE63067")
expr1.to_csv(f"{GEO}/GSE48452_expr_raw.csv.gz", compression="gzip")
expr2.to_csv(f"{GEO}/GSE63067_expr_raw.csv.gz", compression="gzip")
meta1.to_csv(f"{GEO}/GSE48452_meta.csv")
meta2.to_csv(f"{GEO}/GSE63067_meta.csv")
json.dump(dict(GSE48452=dict(platform=plat1, group_col=gcol1),
               GSE63067=dict(platform=plat2, group_col=gcol2)),
          open(f"{GEO}/parse_info.json", "w"), indent=1)
print("\nnext: annotation + DE in s1b")
