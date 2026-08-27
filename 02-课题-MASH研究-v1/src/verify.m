% verify.m —— MATLAB 独立复算（v2：修复 Spearman 与输出）
D = 'D:/zcode-workspace/mash_research';
j = jsondecode(fileread(fullfile(D, 'results/tables/gnn_metrics_v2.json')));

fid = fopen(fullfile(D, 'results/v6/matlab_verify.csv'), 'w');
fprintf(fid, 'split,n,R2,RMSE,Spearman_mu_y,Spearman_sigma_abserr,cov95_raw\n');
for k = 1:2
    if k == 1, sp = 'random'; else, sp = 'scaffold'; end
    tp = j.(sp).test_preds;
    y = double(tp.y(:)); mu = double(tp.mu(:)); sg = double(tp.sigma(:));
    n = length(y);
    r2 = 1 - sum((y - mu).^2) / sum((y - mean(y)).^2);
    rmse = sqrt(mean((y - mu).^2));
    ry = myrank(y); rm_ = myrank(mu); rs = myrank(sg); ra = myrank(abs(y - mu));
    sp_mu = pearson(ry(:), rm_(:));
    sp_sig = pearson(rs(:), ra(:));
    cov95 = mean(abs(y - mu) <= 1.959964 * sg);
    fprintf(fid, '%s,%d,%.4f,%.4f,%.4f,%.4f,%.4f\n', sp, n, r2, rmse, sp_mu, sp_sig, cov95);
    fprintf('%s: n=%d R2=%.4f RMSE=%.4f rho(mu,y)=%.4f rho(sig,|err|)=%.4f cov95=%.4f\n', ...
        sp, n, r2, rmse, sp_mu, sp_sig, cov95);
end
yc = double(j.random.test_preds.y(:)); muc = double(j.random.test_preds.mu(:));
ye = double(j.scaffold.test_preds.y(:)); mue = double(j.scaffold.test_preds.mu(:));
rc = sort(abs(yc - muc)); nc = length(rc);
kk = ceil((nc + 1) * 0.95); q = rc(min(kk, nc));
cov_conf = mean(abs(ye - mue) <= q);
fprintf('M2 flat conformal: q=%.4f cov(scaffold)=%.4f\n', q, cov_conf);
fprintf(fid, 'M2_flat_conformal,q=%.4f,cov_eval=%.4f,,,\n', q, cov_conf);
fclose(fid);
disp('MATLAB verify v2 done.');

function r = myrank(x)
    [s, idx] = sort(x);
    n = length(x);
    r = zeros(n, 1);
    i = 1;
    while i <= n
        j2 = i;
        while j2 < n && s(j2+1) == s(i)
            j2 = j2 + 1;
        end
        r(idx(i:j2)) = (i + j2) / 2;
        i = j2 + 1;
    end
end

function c = pearson(a, b)
    a = a - mean(a); b = b - mean(b);
    c = sum(a .* b) / sqrt(sum(a.^2) * sum(b.^2));
end
