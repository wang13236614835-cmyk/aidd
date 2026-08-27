% wilson_check_matlab.m —— MATLAB 独立交叉验证
% 输入: results/v6/conformal_calibration.json (论文 Table 3 / Table S1 的源数据)
% 输出格式: 项目 | 论文值 | MATLAB值 | 一致true/false, 末行 OVERALL
% 运行: matlab -batch "run('D:\zcode-workspace\roundtable3\wilson_check_matlab.m')"

txt = fileread('D:/zcode-workspace/mash_research/results/v6/conformal_calibration.json');
J = jsondecode(txt);
n = 34; z = 1.959963985;
ok = true;

fprintf('%s\n', repmat('=',1,78));
fprintf('%s\n', 'MATLAB 独立交叉验证: 覆率 Wilson 95% CI (n=34) + h* 公式');
fprintf('运行时间: %s | MATLAB %s\n', datestr(now,'yyyy-mm-dd HH:MM:SS'), version);
fprintf('%s\n', repmat('=',1,78));

% --- M0-M4: 覆率 + Wilson CI ---
methods = {'M0_raw_sigma','M1_leverage_inflated','M2_split_conformal_flat', ...
           'M3_conformalized_z_sigma_inf','M4_weighted_conformal_z_sigma_inf'};
short   = {'M0 raw sigma','M1 leverage-inflated','M2 flat conformal', ...
           'M3 z-conformal','M4 weighted z-conformal'};
for i = 1:5
    m = J.methods.(methods{i});
    k = round(m.coverage95*n);                 % 由覆率还原命中数
    p = k/n; d = 1 + z^2/n;
    c = (p + z^2/(2*n))/d; hw = z*sqrt(p*(1-p)/n + z^2/(4*n^2))/d;
    lo = c-hw; hi = min(c+hw,1);
    pass = (abs(k/n - m.coverage95)<1e-3) && (abs(lo-m.coverage95_wilson_CI(1))<1e-3) ...
        && (abs(hi-m.coverage95_wilson_CI(2))<1e-3);
    ok = ok && pass;
    fprintf('%s | %.4f [%.4f, %.4f] | %.4f [%.4f, %.4f] (k=%d/%d) | %s\n', ...
        short{i}, m.coverage95, m.coverage95_wilson_CI(1), m.coverage95_wilson_CI(2), ...
        k/n, lo, hi, k, n, string(pass));
end

% --- M5 scaffold-matched flat conformal ---
m5 = J.scaffold_val_calibration_M5.methods.M5_scaffoldval_flat_conformal;
k5 = round(m5.coverage95*n);                   % = 34/34
p = 1; d = 1 + z^2/n;
c = (p + z^2/(2*n))/d; hw = z*sqrt(p*(1-p)/n + z^2/(4*n^2))/d;
lo5 = c-hw; hi5 = min(c+hw,1);
pass = (k5==n) && (abs(lo5-m5.coverage95_wilson_CI(1))<1e-3) && (abs(hi5-m5.coverage95_wilson_CI(2))<1e-3);
ok = ok && pass;
fprintf('%s | %.4f [%.4f, %.4f] | %.4f [%.4f, %.4f] (k=%d/%d) | %s\n', ...
    'M5 scaffold-matched', m5.coverage95, m5.coverage95_wilson_CI(1), m5.coverage95_wilson_CI(2), ...
    k5/n, lo5, hi5, k5, n, string(pass));

% --- h* 公式: 3(k+1)/n, k=5 PCs, n_train=358 ---
hstar = 3*(5+1)/358;
pass = abs(hstar - J.H_crit) < 1e-12;
ok = ok && pass;
fprintf('%s | %.10f | %.10f | %s\n', 'h* = 3(5+1)/358', J.H_crit, hstar, string(pass));

% --- M5 平均半宽 (论文 Table 3: 2.98) ---
pass = abs(m5.mean_half_width - 2.98) < 0.005;
ok = ok && pass;
fprintf('%s | %.2f | %.4f | %s\n', 'M5 mean half-width', 2.98, m5.mean_half_width, string(pass));

% --- z 变体半宽 (论文 Table S1: 5.18-5.22) ---
m5z1 = J.scaffold_val_calibration_M5.methods.M5_scaffoldval_z_conformal_sigma_inf;
m5z2 = J.scaffold_val_calibration_M5.methods.M5_scaffoldval_z_conformal_rawsigma;
pass = (abs(m5z1.mean_half_width-5.18)<0.005) && (abs(m5z2.mean_half_width-5.22)<0.005);
ok = ok && pass;
fprintf('%s | %.2f / %.2f | %.4f / %.4f | %s\n', 'M5 z-variant half-widths', ...
    5.18, 5.22, m5z1.mean_half_width, m5z2.mean_half_width, string(pass));

fprintf('%s\n', repmat('-',1,78));
fprintf('OVERALL: %s\n', string(ok));
fprintf('%s\n', repmat('=',1,78));
