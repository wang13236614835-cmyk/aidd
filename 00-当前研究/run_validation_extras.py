"""验证补强分析(核心期刊审查20260905大修 项19/20/22/23)。

不改动已冻结的 run_diagnostics.py 证据链; 本脚本从同一冻结输入重算并校验哈希,
输出四类补充诊断:
- 项19 跨集最大相似度分布(test->train, val->train)与近邻占比, 附逐样本表
- 项20 按簇大小依次填充80/10/10%造成的划分选择性: 三集簇大小/标签分布/集内相似度对照
- 项22 误差按训练近邻分层(近邻>=0.8 / 中间 / 远邻)的RMSE与绝对误差分位数
- 项23 覆盖率的Wilson 95%CI与区间宽度、按域(近/远邻)分层覆盖

科学定位: 描述性诊断。不构成外部验证, 不放行候选。
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from rdkit import Chem, DataStructs
from rdkit.Chem import rdFingerprintGenerator
from scipy.stats import spearmanr
from sklearn.ensemble import RandomForestRegressor

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from methods import butina_labels, split_groups, conformal_radius  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT / "03-课题-MASH研究-v2"
HERE = Path(__file__).resolve().parent
FROZEN = HERE / "validation" / "20260905" / "diagnostic_summary.json"


def sha(p: Path) -> str:
    import hashlib
    return hashlib.sha256(p.read_bytes()).hexdigest()


def wilson_ci(k: int, n: int, z: float = 1.96):
    """Wilson score interval for binomial coverage (项23)."""
    if n == 0:
        return None
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return round(center - half, 4), round(center + half, 4)


def maxsim_distribution(fps, eval_idx, ref_idx):
    sims = [DataStructs.BulkTanimotoSimilarity(fps[i], [fps[j] for j in ref_idx])
            for i in eval_idx]
    mx = np.array([max(s) for s in sims])
    return {
        "n": len(mx),
        "quantiles_p05_p25_p50_p75_p95": [round(float(q), 4) for q in
                                          np.percentile(mx, [5, 25, 50, 75, 95])],
        "share_ge_0.8": round(float(np.mean(mx >= 0.8)), 4),
        "share_ge_0.6": round(float(np.mean(mx >= 0.6)), 4),
        "share_lt_0.4": round(float(np.mean(mx < 0.4)), 4),
    }, mx


def intra_set_mean_sim(fps, idx):
    if len(idx) < 2:
        return None
    sims = [DataStructs.TanimotoSimilarity(fps[i], fps[j])
            for a, i in enumerate(idx) for j in idx[a + 1:]]
    return round(float(np.mean(sims)), 4)


def main():
    frozen = json.loads(FROZEN.read_text(encoding="utf-8"))
    recorded = frozen.get("input_hashes", {})
    out = HERE / "validation" / "extras_20260905"
    out.mkdir(parents=True, exist_ok=True)
    fpg = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
    report = {"mode": "validation_extras_descriptive",
              "scientific_validation": "not_granted",
              "basis": "同 validation/20260905 冻结输入与同一划分/模型设定(seed=42)",
              "review_items": {"19": "跨集相似度分布", "20": "划分选择性测量",
                               "22": "误差按近邻分层", "23": "覆盖率Wilson CI"},
              "targets": {}}

    for target in ["THRB", "FASN", "SCD1"]:
        file = OLD / "data/chembl" / f"{target}_clean.csv"
        rel = str(file.relative_to(ROOT))
        if rel in recorded and sha(file) != recorded[rel]:
            raise SystemExit(f"{rel} 与冻结记录哈希不一致, 中止")
        df = pd.read_csv(file)
        mols = [Chem.MolFromSmiles(s) for s in df.std_smiles]
        fps = [fpg.GetFingerprint(m) for m in mols]
        labels, clusters = butina_labels(fps)
        tr, va, te = split_groups(labels)
        y = df.pIC50.to_numpy()

        # ---- 项19 跨集最大相似度 ----
        dist_test, mx_test = maxsim_distribution(fps, te, tr)
        dist_val, _ = maxsim_distribution(fps, va, tr)
        train_loo = []
        for i in tr:
            others = [j for j in tr if j != i]
            train_loo.append(max(DataStructs.BulkTanimotoSimilarity(
                fps[i], [fps[j] for j in others])))
        item19 = {"test_to_train": dist_test, "val_to_train": dist_val,
                  "train_leave_one_out": {
                      "n": len(tr),
                      "quantiles_p05_p50_p95": [round(float(q), 4) for q in
                                                np.percentile(train_loo, [5, 50, 95])]},
                  "note": "0.8为诊断阈值,不是通用泄漏界线;骨架/簇不交叉不排除指纹相似"}

        # ---- 项20 划分选择性 ----
        def split_stats(idx, name):
            sizes = [len(c) for c in clusters if c[0] in set(idx)]
            return {"split": name, "n": len(idx),
                    "n_clusters": len(sizes),
                    "cluster_size_median": round(float(np.median(sizes)), 2) if sizes else None,
                    "cluster_size_max": int(max(sizes)) if sizes else None,
                    "pIC50_min": round(float(y[idx].min()), 3),
                    "pIC50_max": round(float(y[idx].max()), 3),
                    "pIC50_mean": round(float(y[idx].mean()), 3),
                    "pIC50_std": round(float(y[idx].std()), 3),
                    "intra_set_mean_tanimoto": intra_set_mean_sim(fps, list(idx))}
        item20 = {"splits": [split_stats(tr, "train"), split_stats(va, "calibration"),
                             split_stats(te, "test")],
                  "mechanism": "split_groups按簇大小降序依次填80/10/10%,测试集系统性偏向小簇",
                  "label_range_overlap_traintest": [round(float(max(y[idx].min() for idx in [tr]), ), 3),
                                                    round(float(min(y[idx].max() for idx in [tr]), ), 3)]}

        # ---- 模型(与冻结诊断同设定) ----
        X = np.array([np.array(fp) for fp in fps])
        model = RandomForestRegressor(n_estimators=300, random_state=42,
                                      n_jobs=4).fit(X[tr], y[tr])
        pred = model.predict(X[te])
        cal = model.predict(X[va])
        radius = conformal_radius(np.abs(y[va] - cal))
        resid = y[te] - pred

        # ---- 项22 误差分层 ----
        strat = [("near_ge_0.8", mx_test >= 0.8),
                 ("mid_0.55_0.8", (mx_test >= 0.55) & (mx_test < 0.8)),
                 ("far_lt_0.55", mx_test < 0.55)]
        item22 = {"overall_abs_err_quantiles_p50_p90_max": [round(float(q), 3) for q in
                     np.percentile(np.abs(resid), [50, 90, 100])]}
        for name, m in strat:
            if m.sum() == 0:
                item22[name] = {"n": 0}
                continue
            item22[name] = {"n": int(m.sum()),
                            "RMSE": round(float(np.sqrt(np.mean(resid[m] ** 2))), 3),
                            "mean_abs_err": round(float(np.mean(np.abs(resid[m]))), 3)}
        item22["spearman_maxsim_abs_err"] = (round(float(
            spearmanr(mx_test, np.abs(resid)).statistic), 3)
            if len(np.unique(mx_test)) > 1 else None)
        item22["log_scale_note"] = "RMSE单位为pIC50;约1个log单位=活性约10倍尺度,非每样本固定10倍"

        # ---- 项23 覆盖率CI与宽度 ----
        k = int(np.sum(np.abs(resid) <= radius))
        n = len(te)
        item23 = {"radius_pIC50": round(float(radius), 4) if np.isfinite(radius) else "unbounded",
                  "empirical_coverage": f"{k}/{n}",
                  "coverage_wilson95": wilson_ci(k, n),
                  "nominal": 0.95,
                  "claim": "经验覆盖率仅对本次测试分布成立;簇偏移/外推不保证95%"}
        for name, m in strat:
            if m.sum():
                kk = int(np.sum(np.abs(resid[m]) <= radius))
                item23[f"coverage_{name}"] = {
                    "k_n": f"{kk}/{int(m.sum())}",
                    "wilson95": wilson_ci(kk, int(m.sum()))}

        pd.DataFrame({"row_id": te, "y": y[te], "pred": pred,
                      "abs_err": np.abs(resid),
                      "maxTan_train": mx_test,
                      "in_interval": (np.abs(resid) <= radius).astype(int)}
                     ).to_csv(out / f"{target}_test_stratified.csv", index=False)
        report["targets"][target] = {"item19_similarity": item19,
                                     "item20_split_selectivity": item20,
                                     "item22_error_stratified": item22,
                                     "item23_coverage": item23}

    (out / "validation_extras.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False),
        encoding="utf-8")
    print(json.dumps({t: {"coverage": v["item23_coverage"]["empirical_coverage"],
                          "wilson95": v["item23_coverage"]["coverage_wilson95"],
                          "near_ge0.8": v["item19_similarity"]["test_to_train"]["share_ge_0.8"]}
                      for t, v in report["targets"].items()}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
