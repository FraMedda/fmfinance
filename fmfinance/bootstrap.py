import numpy as np
import pandas as pd


def bootstrap(factors, funds, n_boot, min_obs=36):
    """
    Cross-section bootstrap. Returns observed and simulated alphas/t-alphas.
    
    Input:  factors (DataFrame), funds (DataFrame), n_boot (int), min_obs (int)
    Output: alpha_obs, alpha_t_obs, alphas_boot, t_alphas_boot
    """
    
    X = np.column_stack([np.ones(len(factors)), factors.values])
    tickers = funds.columns.tolist()
    n = len(tickers)
    
    betas  = [None] * n
    resids = [None] * n
    masks  = [None] * n
    inv_xx = [None] * n
    alpha_obs   = [np.nan] * n
    alpha_t_obs = [np.nan] * n
    
    for i, f in enumerate(tickers):
        y = funds[f].values
        m = ~np.isnan(y)
        if m.sum() < min_obs:
            continue
        Xi = X[m]
        yi = y[m]
        ixx = np.linalg.inv(Xi.T @ Xi)
        b, _, _, _ = np.linalg.lstsq(Xi, yi, rcond=None)
        ei = yi - Xi @ b
        se = np.sqrt(np.sum(ei**2) / (m.sum() - Xi.shape[1]) * ixx[0, 0])
        
        betas[i]  = b
        resids[i] = ei
        masks[i]  = m
        inv_xx[i] = ixx
        alpha_obs[i]   = b[0]
        alpha_t_obs[i] = b[0] / se if se > 0 else np.nan
    
    valid = [i for i in range(n) if betas[i] is not None]
    tickers = [tickers[i] for i in valid]
    betas   = [betas[i] for i in valid]
    resids  = [resids[i] for i in valid]
    masks   = [masks[i] for i in valid]
    inv_xx  = [inv_xx[i] for i in valid]
    alpha_obs   = pd.Series([alpha_obs[i] for i in valid], index=tickers)
    alpha_t_obs = pd.Series([alpha_t_obs[i] for i in valid], index=tickers)
    n = len(tickers)
    
    alphas_boot   = np.full((n_boot, n), np.nan)
    t_alphas_boot = np.full((n_boot, n), np.nan)
    
    for b in range(n_boot):
        for i in range(n):
            ei = resids[i]
            Ti = len(ei)
            Xi = X[masks[i]]
            
            beta_H0 = betas[i].copy()
            beta_H0[0] = 0.0
            
            r_sim = Xi @ beta_H0 + ei[np.random.randint(0, Ti, Ti)]
            b_sim, _, _, _ = np.linalg.lstsq(Xi, r_sim, rcond=None)
            e_sim = r_sim - Xi @ b_sim
            se = np.sqrt(np.sum(e_sim**2) / (Ti - Xi.shape[1]) * inv_xx[i][0, 0])
            
            alphas_boot[b, i] = b_sim[0]
            t_alphas_boot[b, i] = b_sim[0] / se if se > 0 else np.nan
    
    return alpha_obs, alpha_t_obs, pd.DataFrame(alphas_boot, columns=tickers), pd.DataFrame(t_alphas_boot, columns=tickers)