% verify_matlab.m —— 跨语言独立复核：MATLAB 重算论文关键统计量
% 数据源: mash_research/results/ 下的 JSON/CSV（与 Python 流水线完全独立）
root = 'D:/zcode-workspace/mash_research';
out = struct();

% ---------- 1) 双划分指标（从 test_preds 复算 vs json 存储） ----------
j = jsondecode(fileread(fullfile(root,'results/tables/gnn_metrics_v2.json')));
splits = {'random','scaffold'};
for i = 1:2
    s = splits{i};
    y  = j.(s).test_preds.y(:);   mu = j.(s).test_preds.mu(:);   sig = j.(s).test_preds.sigma(:);
    r2   = 1 - sum((y-mu).^2)/sum((y-mean(y)).^2);
    rmse = sqrt(mean((y-mu).^2));
    rho  = corr(mu, y, 'type','Spearman');
    cov95 = mean(abs(y-mu) <= 1.959964*sig);
    [rho_se, p_se] = corr(sig, abs(y-mu), 'type','Spearman');
    out.(s).R2_re      = round(r2, 4);
    out.(s).R2_stored  = round(j.(s).BGNN.R2, 4);
    out.(s).RMSE_re    = round(rmse, 4);
    out.(s).Spear_re   = round(rho, 4);
    out.(s).cov95_re   = round(cov95, 4);
    out.(s).sigmaerr_rho_re = round(rho_se, 4);
    out.(s).sigmaerr_p_re   = round(p_se, 5);
    out.(s).pass_R2 = abs(r2 - j.(s).BGNN.R2) < 5e-3;
end

% ---------- 2) M2 平坦 conformal 分位数（有限样本修正, "higher"） ----------
r = sort(abs(j.random.test_preds.y(:) - j.random.test_preds.mu(:)));
n1 = numel(r);
idx = min(ceil((n1+1)*0.95), n1);
q_m2 = r(idx);
v6 = jsondecode(fileread(fullfile(root,'results/v6/conformal_calibration.json')));
out.M2_q_matlab = round(q_m2, 4);
out.M2_q_python = v6.quantiles.q_abs;
out.M2_pass = abs(q_m2 - v6.quantiles.q_abs) < 5e-3;

% ---------- 3) Wilson 区间复算（覆率 0.735, n=34） ----------
n = 34; k = 25; z = 1.959964;
p = k/n; den = 1 + z^2/n;
c = (p + z^2/(2*n))/den;
h = z*sqrt(p*(1-p)/n + z^2/(4*n^2))/den;
out.wilson_scaffold_cov95 = [round(c-h,4), round(c+h,4)];
out.wilson_pass = abs((c-h) - 0.5688) < 2e-3 && abs((c+h) - 0.8540) < 2e-3;

% ---------- 4) 贝叶斯收缩复算（k=5） vs 修正榜 ----------
T = readtable(fullfile(root,'results/tables/herb_cwbcs_ranking.csv'), 'TextType','string');
F = readtable(fullfile(root,'results/tables/herb_cwbcs_ranking_fix.csv'), 'TextType','string');
shrunk = T.herb_score .* T.n_compounds ./ (T.n_compounds + 5);
[~, ia, ib] = intersect(string(T.herb), string(F.herb));
diffmax = max(abs(shrunk(ia) - F.herb_score_shrunk(ib)));
out.shrink_pass = diffmax < 1e-3;
out.shrink_diffmax = round(diffmax, 6);
out.shrink_tripterygium = round(shrunk(find(startsWith(string(T.herb),"Tripterygium"))), 4);

% ---------- 5) 杠杆连接复核：骨架测试集均值低于随机 ----------
D = readtable(fullfile(root,'data/chembl/fxr_final_dataset.csv'), 'TextType','string');
lev = containers.Map(cellstr(D.std_smiles), num2cell(D.leverage_h));
h_r = cellfun(@(s) lev(s), j.random.test_preds.smiles);
h_s = cellfun(@(s) lev(s), j.scaffold.test_preds.smiles);
out.lev_mean_random  = round(mean(h_r), 5);
out.lev_mean_scaffold = round(mean(h_s), 5);
out.lev_pass = mean(h_s) < mean(h_r);

% ---------- 汇总 ----------
fid = fopen('D:/zcode-workspace/paper/matlab_verify_report.json','w');
fprintf(fid, '%s', jsonencode(out, 'PrettyPrint', true)); fclose(fid);
disp('== MATLAB cross-language verification ==');
disp(out);
allpass = out.random.pass_R2 && out.scaffold.pass_R2 && out.M2_pass && out.wilson_pass && out.shrink_pass && out.lev_pass;
fprintf('ALL_CHECKS_PASS = %d\n', allpass);
