# -*- coding: utf-8 -*-
"""论文图1-4：全部从已验证的原始/修正数据生成（可溯源）。"""
import json
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

D = "D:/zcode-workspace/mash_research"
P = "D:/zcode-workspace/paper"
os.makedirs(f"{P}/figs", exist_ok=True)

ACCENT = "#1f7692"
MUTED = "#7e7c74"
WARN = "#8c7443"
ERR = "#a25b54"
OK = "#529067"

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "DejaVu Sans"],
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.linewidth": 0.8,
    "font.size": 9,
})

j = json.load(open(f"{D}/results/tables/gnn_metrics_v2.json", encoding="utf-8"))
v6 = json.load(open(f"{D}/results/v6/conformal_calibration.json", encoding="utf-8"))

# ---------- Fig 1: dual-split parity ----------
fig, axes = plt.subplots(1, 2, figsize=(7.0, 3.4), sharey=True, sharex=True)
for ax, split, title in [
    (axes[0], "random", "Random split (proposal-style)"),
    (axes[1], "scaffold", "Scaffold split (strict)"),
]:
    tp = j[split]["test_preds"]
    y, mu, sig = np.array(tp["y"]), np.array(tp["mu"]), np.array(tp["sigma"])
    m = j[split]["BGNN"]
    ax.errorbar(mu, y, yerr=1.96 * sig, fmt="none", ecolor=MUTED, alpha=0.30,
                elinewidth=0.8, capsize=0, label="95% interval", zorder=1)
    ax.scatter(mu, y, s=16, color=ACCENT, zorder=2, label="compound")
    lims = [2.5, 10.5]
    ax.plot(lims, lims, ls="--", lw=0.8, color=MUTED, zorder=0)
    ax.set_xlim(lims); ax.set_ylim(lims)
    ax.set_xlabel("Predicted pIC$_{50}$ (mean $\\mu$)")
    ax.set_title(title, fontsize=9.5)
    ax.grid(True, ls="--", lw=0.4, alpha=0.25)
    ax.text(0.05, 0.95, "R$^2$ = %.2f\nRMSE = %.2f\nSpearman $\\rho$ = %.2f (n=%d)"
            % (m["R2"], m["RMSE"], m["Spearman"], len(y)),
            transform=ax.transAxes, va="top", fontsize=8,
            bbox=dict(fc="white", ec="none", alpha=0.8, pad=1.5))
axes[0].set_ylabel("Observed pIC$_{50}$")
axes[0].legend(loc="lower right", frameon=False, fontsize=7.5)
fig.suptitle("Same model, same data, different split: point accuracy collapses under scaffold extrapolation",
             fontsize=9.5, y=1.02)
fig.tight_layout()
fig.savefig(f"{P}/figs/fig1_dual_split.png", dpi=300, bbox_inches="tight")
plt.close(fig)

# ---------- Fig 2: recalibration coverage vs width ----------
meth = [("M0  raw $\\sigma$", "M0_raw_sigma"), ("M1  leverage-inflated $\\sigma$", "M1_leverage_inflated"),
        ("M2  flat split conformal", "M2_split_conformal_flat"),
        ("M5  scaffold-matched\n     conformal", "scaffold_val_calibration_M5/M5_scaffoldval_flat_conformal")]
labels, covs, cis, widths = [], [], [], []
for lab, key in meth:
    if "/" in key:
        v = v6["scaffold_val_calibration_M5"]["methods"][key.split("/")[1]]
    else:
        v = v6["methods"][key]
    labels.append(lab); covs.append(v["coverage95"])
    cis.append([v["coverage95"] - v["coverage95_wilson_CI"][0],
                v["coverage95_wilson_CI"][1] - v["coverage95"]])
    widths.append(v["mean_half_width"])

fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.0, 3.2))
x = np.arange(len(labels))
a1.axhline(0.95, ls="--", lw=0.9, color=ERR, label="nominal 95%")
a1.bar(x, covs, 0.55, color=ACCENT, alpha=0.85)
a1.errorbar(x, covs, yerr=np.array(cis).T, fmt="none", ecolor="#151513", capsize=3, lw=0.9)
a1.set_xticks(x); a1.set_xticklabels(labels, fontsize=7)
a1.set_ylabel("95% coverage on scaffold test\n(out-of-domain, n=34)")
a1.set_ylim(0, 1.08)
a1.grid(True, axis="y", ls="--", lw=0.4, alpha=0.25)
a1.legend(frameon=False, fontsize=7.5, loc="upper left")
for xi, c in zip(x, covs):
    a1.text(xi + 0.30, c + 0.02, "%.3f" % c, fontsize=7, ha="left")

a2.bar(x, widths, 0.55, color=MUTED, alpha=0.9)
rng = v6["random_test_only"]
a2.axhline(3.29, ls=":", lw=0.9, color=ERR)
a2.text(1.55, 3.33, "half of full pIC$_{50}$ range (6.58/2)", fontsize=7, color=ERR)
a2.set_xticks(x); a2.set_xticklabels(labels, fontsize=7)
a2.set_ylabel("Mean interval half-width\n(pIC$_{50}$ units)")
a2.grid(True, axis="y", ls="--", lw=0.4, alpha=0.25)
for xi, w in zip(x, widths):
    a2.text(xi + 0.30, w + 0.05, "%.2f" % w, fontsize=7, ha="left")
fig.suptitle("Post-hoc recalibration from in-domain data cannot restore coverage;"
             " matched-domain conformal does, at the cost of resolution",
             fontsize=9, y=1.03)
fig.tight_layout()
fig.savefig(f"{P}/figs/fig2_recalibration.png", dpi=300, bbox_inches="tight")
plt.close(fig)

# ---------- Fig 3: three-tier annotation ----------
c = pd.read_csv(f"{D}/results/tables/compound_cwbcs_full.csv")
tier_counts = c["tier"].value_counts()
order = ["in_domain_high_conf(域内高置信)", "in_domain_low_conf(域内低置信)", "OOD_warning(域外预警)"]
names = ["In-domain\nhigh confidence", "In-domain\nlow confidence", "Out-of-domain\nwarning"]
vals = [int(tier_counts.get(k, 0)) for k in order]
cols = [OK, WARN, ERR]
fig, ax = plt.subplots(figsize=(4.6, 3.0))
bars = ax.bar(np.arange(3), vals, 0.55, color=cols, alpha=0.85)
for xi, v in zip(np.arange(3), vals):
    ax.text(xi, v + 1.5, str(v), ha="center", fontsize=9)
ax.set_xticks(np.arange(3)); ax.set_xticklabels(names, fontsize=8)
ax.set_ylabel("Natural products (n=131)")
ax.set_ylim(0, 85)
ax.grid(True, axis="y", ls="--", lw=0.4, alpha=0.25)
sig_by = [c.loc[c["tier"] == k, "fxr_sigma"].dropna().median() for k in order]
ax2 = ax.twinx()
ax2.plot(np.arange(3), sig_by, "o--", color="#151513", ms=5, lw=1)
ax2.set_ylabel("Median predictive $\\sigma$ (pIC$_{50}$)", fontsize=8)
ax2.spines["right"].set_visible(True)
for xi, s in zip(np.arange(3), sig_by):
    ax2.text(xi + 0.10, s + 0.015, "%.2f" % s, fontsize=7.5)
fig.suptitle("Three-tier applicability annotation of 131 herbal natural products", fontsize=9.5, y=1.0)
fig.tight_layout()
fig.savefig(f"{P}/figs/fig3_tiers.png", dpi=300, bbox_inches="tight")
plt.close(fig)

# ---------- Fig 4: shrunk CW-BCS ranking ----------
h = pd.read_csv(f"{D}/results/tables/herb_cwbcs_ranking_fix.csv")
h = h.sort_values("herb_score_shrunk", ascending=True).tail(10)
def color_of(rep):
    if "域外" in rep:
        return ERR
    if "high_conf" in rep or "高置信" in rep:
        return ACCENT
    return MUTED
cols = [color_of(r) for r in h["rep_fix"]]
fig, ax = plt.subplots(figsize=(6.4, 3.6))
ypos = np.arange(len(h))
ax.barh(ypos, h["herb_score_shrunk"], 0.62, color=cols, alpha=0.88)
old = h["herb_score"]
ax.scatter(old, ypos, marker="|", s=220, color="#151513", lw=1.2, label="pre-shrinkage score")
for yi, (v, o, rep) in enumerate(zip(h["herb_score_shrunk"], old, h["rep_fix"])):
    name = rep.split("(")[0].split("[")[0].strip()
    ax.text(v + 0.008, yi, "%.3f  (rep. %s)" % (v, name), va="center", fontsize=7)
ax.set_yticks(ypos)
ax.set_yticklabels([x.split("(")[0].strip() for x in h["herb"]], fontsize=8.5, style="italic")
ax.set_xlabel("Shrunk herb CW-BCS score, $s\\times n/(n+5)$")
ax.set_xlim(0, 0.72)
ax.grid(True, axis="x", ls="--", lw=0.4, alpha=0.25)
from matplotlib.patches import Patch
ax.legend(handles=[Patch(fc=ACCENT, label="high-confidence representative"),
                   Patch(fc=ERR, label="out-of-domain flag"),
                   plt.Line2D([0], [0], color="#151513", marker="|", ls="", ms=8,
                              label="pre-shrinkage score")],
          frameon=False, fontsize=7, loc="lower right")
ax.set_title("Confidence-weighted multi-target coverage (CW-BCS): shrinkage-corrected herb ranking", fontsize=9)
fig.tight_layout()
fig.savefig(f"{P}/figs/fig4_cwbcs.png", dpi=300, bbox_inches="tight")
plt.close(fig)

print("figures saved:", os.listdir(f"{P}/figs"))
