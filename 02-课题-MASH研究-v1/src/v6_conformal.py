# -*- coding: utf-8 -*-
"""
B2（judge_verdict.md）: sigma 域外校准 —— 杠杆膨胀 + conformal 重校准
全部真实数据：gnn_metrics_v2.json 的 test_preds × fxr_final_dataset.csv 的 leverage_h
协议：
  校准集 = 随机划分测试集 (n=36, 域内)   评估集 = 骨架划分测试集 (n=34, 域外/外推)
  M0 原始 sigma 区间        mu ± z_a * sigma
  M1 杠杆膨胀 sigma         sigma_inf = sigma * sqrt(1 + h/h_crit)
  M2 split conformal(非自适应) mu ± q_hat,  q_hat=|y-mu| 校准分位数
  M3 自适应 conformal(z残差)  mu ± q_z * sigma_inf,  z=|y-mu|/sigma_inf
  M4 杠杆加权 conformal       权重 w_i = h_i/mean(h_cal)，加权分位数(Tibshirani 2019 框架)
输出: results/v6/conformal_calibration.json
"""
import json
import math
import numpy as np
import pandas as pd
from scipy import stats

D = "D:/zcode-workspace/mash_research"
OUT = f"{D}/results/v6"
import os
os.makedirs(OUT, exist_ok=True)

j = json.load(open(f"{D}/results/tables/gnn_metrics_v2.json", encoding="utf-8"))
ds = pd.read_csv(f"{D}/data/chembl/fxr_final_dataset.csv")
ad = json.load(open(f"{D}/data/chembl/ad_reference.json", encoding="utf-8"))
H_CRIT = ad["h_crit"]
lev = dict(zip(ds["std_smiles"], ds["leverage_h"]))

def load(split):
    tp = j[split]["test_preds"]
    df = pd.DataFrame({"smiles": tp["smiles"], "y": tp["y"], "mu": tp["mu"], "sigma": tp["sigma"]})
    df["h"] = df["smiles"].map(lev)
    df["err"] = df["y"] - df["mu"]
    df["abs_err"] = df["err"].abs()
    return df

rand = load("random")     # calibration (in-domain)
scaf = load("scaffold")   # evaluation (out-of-domain)

def metrics(df):
    y, mu, sig = df["y"].values, df["mu"].values, df["sigma"].values
    ss_res = ((y - mu) ** 2).sum()
    ss_tot = ((y - y.mean()) ** 2).sum()
    r2 = 1 - ss_res / ss_tot
    rmse = math.sqrt(ss_res / len(y))
    mae = np.abs(y - mu).mean()
    sp_mu = stats.spearmanr(mu, y)
    sp_sig = stats.spearmanr(sig, np.abs(y - mu))
    return {
        "n": len(y), "R2": round(r2, 4), "RMSE": round(rmse, 4), "MAE": round(mae, 4),
        "Spearman_mu_y": [round(sp_mu.statistic, 4), float(f"{sp_mu.pvalue:.2e}")],
        "Spearman_sigma_abserr": [round(sp_sig.statistic, 4), round(sp_sig.pvalue, 5)],
        "coverage95_raw": round(float((np.abs(y - mu) <= 1.959964 * sig).mean()), 4),
        "coverage80_raw": round(float((np.abs(y - mu) <= 1.281552 * sig).mean()), 4),
    }

m_rand, m_scaf = metrics(rand), metrics(scaf)

def conformal_q(resid, alpha, weights=None):
    """split conformal 分位数；weights 归一化为均值1时用加权版。"""
    n = len(resid)
    if weights is None:
        q = np.quantile(resid, min(1.0, math.ceil((n + 1) * (1 - alpha)) / n), method="higher")
        return float(q)
    w = np.asarray(weights, dtype=float)
    w = w / w.mean()
    p = w / (w.sum() + 1.0)          # Tibshirani et al. 2019 一般加权 CP
    order = np.argsort(resid)
    cum = np.cumsum(p[order])
    target = 1 - alpha
    idx = np.searchsorted(cum, target)
    idx = min(idx, n - 1)
    return float(resid[order][idx])

def wilson(k, n, z=1.959964):
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return [round(center - half, 4), round(center + half, 4)]

alpha = 0.05
res = {"H_crit": H_CRIT, "calibration_set": "random test (n=%d)" % len(rand),
       "evaluation_set": "scaffold test (n=%d)" % len(scaf),
       "random_test_only": m_rand, "scaffold_test_only": m_scaf,
       "leverage_mean_cal": round(float(rand["h"].mean()), 5),
       "leverage_mean_eval": round(float(scaf["h"].mean()), 5),
       "leverage_frac_over_crit_cal": round(float((rand["h"] > H_CRIT).mean()), 4),
       "leverage_frac_over_crit_eval": round(float((scaf["h"] > H_CRIT).mean()), 4),
       "methods": {}}

# M1 杠杆膨胀
def sigma_inf(df):
    return df["sigma"].values * np.sqrt(1 + df["h"].values / H_CRIT)

# M2 非自适应 split conformal
q_abs = conformal_q(rand["abs_err"].values, alpha)
# M3 自适应（z 残差 = |err|/sigma_inf）
z_cal = rand["abs_err"].values / sigma_inf(rand)
q_z = conformal_q(z_cal, alpha)
# M4 杠杆加权（对 z 残差加权）
q_zw = conformal_q(z_cal, alpha, weights=rand["h"].values)

def eval_interval(half_width, df=scaf):
    cov = float((df["abs_err"].values <= half_width).mean())
    return {"coverage95": round(cov, 4),
            "coverage95_wilson_CI": wilson(int(cov * len(df)), len(df)),
            "mean_half_width": round(float(np.mean(half_width)), 4),
            "median_half_width": round(float(np.median(half_width)), 4)}

res["methods"] = {
    "M0_raw_sigma": eval_interval(1.959964 * scaf["sigma"].values),
    "M1_leverage_inflated": eval_interval(1.959964 * sigma_inf(scaf)),
    "M2_split_conformal_flat": eval_interval(np.full(len(scaf), q_abs)),
    "M3_conformalized_z_sigma_inf": eval_interval(q_z * sigma_inf(scaf)),
    "M4_weighted_conformal_z_sigma_inf": eval_interval(q_zw * sigma_inf(scaf)),
}
res["quantiles"] = {"q_abs": round(q_abs, 4), "q_z": round(q_z, 4), "q_z_weighted": round(q_zw, 4)}

# 80% 区间（M0 vs 最优方法）
q_abs80 = conformal_q(rand["abs_err"].values, 0.20)
z_cal80 = z_cal
q_z80 = conformal_q(z_cal80, 0.20)
res["alpha_020"] = {
    "M0_raw_sigma": {k.replace("95", "80"): v for k, v in eval_interval(1.281552 * scaf["sigma"].values).items() if k.startswith("coverage")},
    "M3_conformalized_z_sigma_inf": {k.replace("95", "80"): v for k, v in eval_interval(q_z80 * sigma_inf(scaf)).items() if k.startswith("coverage")},
}

json.dump(res, open(f"{OUT}/conformal_calibration.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)

print("== test-only metrics ==")
print("random :", m_rand)
print("scaffold:", m_scaf)
print("\n== leverage: mean cal %.4f vs eval %.4f | frac>h_crit cal %.2f eval %.2f" % (
    res["leverage_mean_cal"], res["leverage_mean_eval"],
    res["leverage_frac_over_crit_cal"], res["leverage_frac_over_crit_eval"]))
print("\n== 95% interval coverage on scaffold (out-of-domain) ==")
for k, v in res["methods"].items():
    print("%-34s cov=%.3f CI%s width_mean=%.3f" % (
        k, v["coverage95"], v["coverage95_wilson_CI"], v["mean_half_width"]))
print("\nquantiles:", res["quantiles"])
print("\n80% coverage:", res["alpha_020"])
print("\nsaved ->", f"{OUT}/conformal_calibration.json")
