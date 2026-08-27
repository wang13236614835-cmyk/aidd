% make_report_figs.m —— 结果报告用高对比中文图（300dpi PNG -> paper/figs/report/）
D = 'D:/zcode-workspace/paper/figs/report';
if ~exist(D, 'dir'), mkdir(D); end
j = jsondecode(fileread('D:/zcode-workspace/mash_research/results/tables/gnn_metrics_v2.json'));
v6 = jsondecode(fileread('D:/zcode-workspace/mash_research/results/v6/conformal_calibration.json'));

set(groot, 'defaultAxesFontName', 'SimHei');
set(groot, 'defaultTextFontName', 'SimHei');
RED = [0.64 0.36 0.33]; TEAL = [0.12 0.46 0.57]; GRAY = [0.55 0.54 0.51];
GREEN = [0.32 0.56 0.40]; DARK = [0.08 0.08 0.07];

% ---------- 图A：随机 vs 骨架 R²（三模型） ----------
f = figure('Position', [50 50 900 480], 'Color', 'w');
models = {'贝叶斯GNN', '随机森林', 'XGBoost'};
r_rand = [j.random.BGNN.R2, j.random.baselines.RF.R2, j.random.baselines.XGB.R2];
r_scaf = [j.scaffold.BGNN.R2, j.scaffold.baselines.RF.R2, j.scaffold.baselines.XGB.R2];
b = bar([r_rand; r_scaf]', 'grouped');
b(1).FaceColor = TEAL; b(2).FaceColor = RED;
set(gca, 'XTickLabel', models, 'FontSize', 15, 'LineWidth', 0.8);
box off; grid on; set(gca,'GridLineStyle','--','GridAlpha',0.25);
yline(0, '-', 'R^2=0 基准', 'Color', DARK, 'LineWidth', 1.2, 'FontSize', 12, 'LabelHorizontalAlignment', 'left');
for k = 1:3
    text(k-0.16, r_rand(k)+0.04, sprintf('%.2f', r_rand(k)), 'HorizontalAlignment', 'center', 'FontSize', 12, 'Color', TEAL, 'FontWeight', 'bold');
    text(k+0.16, r_scaf(k)+0.04, sprintf('%.2f', r_scaf(k)), 'HorizontalAlignment', 'center', 'FontSize', 12, 'Color', RED, 'FontWeight', 'bold');
end
ylim([-0.9, 1.15]); ylabel('R^2（决定系数）', 'FontSize', 13);
title({'随机划分与骨架划分下的模型精度（同一数据）', '蓝：随机划分    红：骨架划分'}, 'FontSize', 14);
legend('随机划分', '骨架划分', 'Location', 'northeast', 'FontSize', 12, 'Box', 'off');
exportgraphics(f, fullfile(D, 'figA_collapse.png'), 'Resolution', 300);

% ---------- 图B：校准覆盖率 vs 名义95% ----------
f = figure('Position', [50 50 900 460], 'Color', 'w');
names = {'M0 原始σ', 'M1 杠杆膨胀', 'M2 平坦共形', 'M5 骨架匹配共形'};
cov = [v6.methods.M0_raw_sigma.coverage95, v6.methods.M1_leverage_inflated.coverage95, ...
       v6.methods.M2_split_conformal_flat.coverage95, ...
       v6.scaffold_val_calibration_M5.methods.M5_scaffoldval_flat_conformal.coverage95];
lo = [v6.methods.M0_raw_sigma.coverage95_wilson_CI(1), ...
      v6.methods.M1_leverage_inflated.coverage95_wilson_CI(1), ...
      v6.methods.M2_split_conformal_flat.coverage95_wilson_CI(1), ...
      v6.scaffold_val_calibration_M5.methods.M5_scaffoldval_flat_conformal.coverage95_wilson_CI(1)];
hi = [v6.methods.M0_raw_sigma.coverage95_wilson_CI(2), ...
      v6.methods.M1_leverage_inflated.coverage95_wilson_CI(2), ...
      v6.methods.M2_split_conformal_flat.coverage95_wilson_CI(2), ...
      v6.scaffold_val_calibration_M5.methods.M5_scaffoldval_flat_conformal.coverage95_wilson_CI(2)];
cols = [RED; RED; RED; GREEN];
bb = bar(cov, 0.55); bb.FaceColor = 'flat';
for k = 1:4, bb.CData(k,:) = cols(k,:); end
hold on;
eb_lo = cov - lo; eb_hi = hi - cov;
errorbar(1:4, cov, eb_lo, eb_hi, 'k', 'LineStyle', 'none', 'LineWidth', 1.1, 'CapSize', 6);
yline(0.95, '--', '名义水平 95%', 'Color', DARK, 'LineWidth', 1.4, 'FontSize', 12, 'LabelHorizontalAlignment', 'left');
for k = 1:4
    text(k, cov(k)+0.06, sprintf('%.1f%%', cov(k)*100), 'HorizontalAlignment', 'center', 'FontSize', 13, 'FontWeight', 'bold');
end
set(gca, 'XTickLabel', names, 'FontSize', 13, 'LineWidth', 0.8);
ylim([0, 1.15]); ylabel('骨架测试集上的95%覆盖率', 'FontSize', 13); box off; grid on;
set(gca,'GridLineStyle','--','GridAlpha',0.25);
title('四种校准方法的95%覆盖率（骨架测试集 n=34）', 'FontSize', 14);
exportgraphics(f, fullfile(D, 'figB_coverage.png'), 'Resolution', 300);

% ---------- 图C：区间半宽 vs 全数据范围 ----------
f = figure('Position', [50 50 900 440], 'Color', 'w');
w = [v6.methods.M0_raw_sigma.mean_half_width, v6.methods.M2_split_conformal_flat.mean_half_width, ...
     v6.scaffold_val_calibration_M5.methods.M5_scaffoldval_flat_conformal.mean_half_width];
labs = {'M0 原始σ', 'M2 平坦共形', 'M5 骨架匹配共形'};
bb = bar([w(1), w(2), w(3)], 0.5); bb.FaceColor = 'flat';
bb.CData(1,:) = GRAY; bb.CData(2,:) = GRAY; bb.CData(3,:) = RED;
hold on; yline(6.58/2, ':', '数据全域的一半（±3.29）', 'Color', DARK, 'LineWidth', 1.3, 'FontSize', 12);
for k = 1:3
    text(k, w(k)+0.12, sprintf('±%.2f', w(k)), 'HorizontalAlignment', 'center', 'FontSize', 13, 'FontWeight', 'bold');
end
set(gca, 'XTickLabel', labs, 'FontSize', 13, 'LineWidth', 0.8);
ylim([0, 4.2]); ylabel('区间平均半宽（pIC50 单位）', 'FontSize', 13); box off; grid on;
set(gca,'GridLineStyle','--','GridAlpha',0.25);
title('校准后预测区间的平均半宽', 'FontSize', 14);
exportgraphics(f, fullfile(D, 'figC_width.png'), 'Resolution', 300);

% ---------- 图D：收缩修正前后排名（雷公藤坠落） ----------
f = figure('Position', [50 50 900 500], 'Color', 'w');
herbs = {'黄连', '苦参', '甘草', '丹参', '青蒿', '水飞蓟', '五味子', '灵芝', '雷公藤', '柴胡'};
raw = [0.718 0.585 0.566 0.545 0.456 0.415 0.354 0.406 0.565 0.107];
shr = [0.529 0.458 0.443 0.427 0.375 0.285 0.277 0.221 0.162 0.037];
pos = 1:10;
bb = barh(pos, raw, 0.62); bb.FaceColor = [0.82 0.80 0.78]; bb.EdgeColor = 'none';
hold on;
sb = barh(pos, shr, 0.30); sb.FaceColor = 'flat';
for k = 1:10
    if strcmp(herbs{k}, '雷公藤'), sb.CData(k,:) = RED; else, sb.CData(k,:) = TEAL; end
end
set(gca, 'YDir', 'reverse');
set(gca, 'YTick', pos, 'YTickLabel', herbs, 'FontSize', 13, 'LineWidth', 0.8);
xlabel('CW-BCS 分数', 'FontSize', 13); box off; grid on;
set(gca,'GridLineStyle','--','GridAlpha',0.25);
text(0.55, 8.0, {'雷公藤 n=2', '修正前 0.565（第4位）', '修正后 0.162（第9位）'}, ...
    'FontSize', 12, 'Color', RED, 'FontWeight', 'bold');
title({'收缩修正前后中药CW-BCS排名（灰：修正前；彩色：修正后）', '红色为雷公藤（n=2，修正后降至第9）'}, 'FontSize', 14);
exportgraphics(f, fullfile(D, 'figD_shrinkage.png'), 'Resolution', 300);

% ---------- 图E：三级标注 ----------
f = figure('Position', [50 50 800 440], 'Color', 'w');
tier = [72, 32, 27]; tierlabs = {'域内高置信', '域内低置信', '域外预警'};
tcols = [GREEN; [0.85 0.72 0.42]; RED];
bb = bar(tier, 0.5); bb.FaceColor = 'flat';
for k = 1:3, bb.CData(k,:) = tcols(k,:); end
for k = 1:3
    text(k, tier(k)+2, sprintf('%d 个 (%.0f%%)', tier(k), tier(k)/1.31), 'HorizontalAlignment', 'center', 'FontSize', 14, 'FontWeight', 'bold');
end
set(gca, 'XTickLabel', tierlabs, 'FontSize', 13, 'LineWidth', 0.8);
ylim([0, 92]); ylabel('131 个中药成分', 'FontSize', 13); box off; grid on;
set(gca,'GridLineStyle','--','GridAlpha',0.25);
title('131个中药成分的三级适用域标注', 'FontSize', 14);
exportgraphics(f, fullfile(D, 'figE_tiers.png'), 'Resolution', 300);

% ---------- 图F：σ 的双重人格（域内 vs 域外） ----------
f = figure('Position', [50 50 800 440], 'Color', 'w');
vals = [0.5853, 0.2688];
bb = bar(vals, 0.45); bb.FaceColor = 'flat';
bb.CData(1,:) = GREEN; bb.CData(2,:) = [0.85 0.72 0.42];
hold on;
text(1, 0.60, '+0.585  (p=0.0002)', 'HorizontalAlignment', 'center', 'FontSize', 14, 'FontWeight', 'bold', 'Color', GREEN);
text(2, 0.29, '+0.269  (p=0.124)', 'HorizontalAlignment', 'center', 'FontSize', 14, 'FontWeight', 'bold');
set(gca, 'XTickLabel', {'域内（随机划分 n=36）', '域外（骨架划分 n=34）'}, 'FontSize', 13, 'LineWidth', 0.8);
ylim([0, 0.75]); ylabel('Spearman ρ（σ 与 |误差|）', 'FontSize', 13); box off; grid on;
set(gca,'GridLineStyle','--','GridAlpha',0.25);
title({'σ与预测误差的秩相关：域内与域外', '注：n=34 时可检出 |ρ|≥0.47'}, 'FontSize', 14);
exportgraphics(f, fullfile(D, 'figF_sigma.png'), 'Resolution', 300);

disp('report figures done.');
