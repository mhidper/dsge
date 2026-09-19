"""
Estimación Bayesiana del modelo Semi-DSGE mediante Metropolis-Hastings Adaptativo (MCMC).
"""

from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from scipy.stats import beta as beta_dist, norm, invgamma
from .config import DEFAULT_PARAMS, PRIORS
from .model import simulate_model


def log_prior_density(param_values: np.ndarray, param_names: List[str],
                      priors_dict: Optional[Dict] = None) -> float:
    """Calcula la log-densidad a priori conjunta."""
    priors = priors_dict or PRIORS
    total_lp = 0.0

    for val, name in zip(param_values, param_names):
        if name not in priors:
            continue
        pinfo = priors[name]
        dist_type = pinfo['dist']
        mu, sigma = pinfo['mean'], pinfo['std']

        if dist_type == 'beta':
            if val <= 0.001 or val >= 0.999:
                return -np.inf
            var = sigma ** 2
            alpha = mu * (mu * (1.0 - mu) / var - 1.0)
            b_param = (1.0 - mu) * (mu * (1.0 - mu) / var - 1.0)
            if alpha <= 0 or b_param <= 0:
                return -np.inf
            total_lp += beta_dist.logpdf(val, alpha, b_param)

        elif dist_type == 'norm':
            total_lp += norm.logpdf(val, mu, sigma)

        elif dist_type == 'invgamma':
            if val <= 0.0:
                return -np.inf
            alpha = (mu / sigma) ** 2 + 2.0
            scale = mu * ((mu / sigma) ** 2 + 1.0)
            total_lp += invgamma.logpdf(val, alpha, scale=scale)

    return total_lp


def log_likelihood(data_dict: Dict[str, np.ndarray], param_values: np.ndarray,
                   param_names: List[str]) -> float:
    """
    Función de verosimilitud conjunta evaluada sobre el sistema estructural.
    Compara las series simuladas de Brecha de PIB, Inflación y Paro con los datos observados.
    """
    try:
        p = DEFAULT_PARAMS.copy()
        for name, val in zip(param_names, param_values):
            p[name] = float(val)

        # Simular modelo estructural forzando la evaluación de las ecuaciones
        res = simulate_model(data_dict, params=p, force_structural_is=True)

        target_vars = [
            ('output_gap_spain', 'output_gap_spain', 1.0),
            ('inflation_total', 'inflation_total', 1.0),
            ('unemployment_rate', 'unemployment_rate', 1.0)
        ]

        ll = 0.0
        for obs_col, sim_col, weight in target_vars:
            if obs_col in data_dict and sim_col in res:
                obs = data_dict[obs_col]
                sim = res[sim_col]
                mask = ~np.isnan(obs) & ~np.isnan(sim)
                if np.sum(mask) > 15:
                    resid = obs[mask] - sim[mask]
                    # Sigma concentrada estimada
                    sigma = np.std(resid) + 1e-4
                    ll += weight * np.sum(norm.logpdf(resid, loc=0.0, scale=sigma))
                else:
                    return -np.inf
        return ll
    except Exception:
        return -np.inf


def log_posterior(param_values: np.ndarray, param_names: List[str],
                  data_dict: Dict[str, np.ndarray]) -> float:
    """Log-Posterior = Log-Prior + Log-Likelihood"""
    lp = log_prior_density(param_values, param_names)
    if not np.isfinite(lp):
        return -np.inf
    ll = log_likelihood(data_dict, param_values, param_names)
    if not np.isfinite(ll):
        return -np.inf
    return lp + ll


def estimate_bayesian_mcmc(data_dict: Dict[str, np.ndarray],
                           params_to_estimate: Optional[List[str]] = None,
                           n_samples: int = 2000,
                           n_burn: int = 500,
                           initial_step: float = 0.01) -> Dict:
    """
    Estimación mediante Metropolis-Hastings adaptativo con ajuste de paso dinámico.
    """
    param_names = params_to_estimate or list(PRIORS.keys())
    # Filtrar sólo los definidos en priors
    param_names = [p for p in param_names if p in PRIORS]
    n_params = len(param_names)

    # Punto de partida: medias de los priors
    current_params = np.array([PRIORS[p]['mean'] for p in param_names])
    current_logp = log_posterior(current_params, param_names, data_dict)

    if not np.isfinite(current_logp):
        print("Aviso: Punto de prior inicial no válido, ajustando parámetros...")
        current_params = np.array([DEFAULT_PARAMS[p] for p in param_names])
        current_logp = log_posterior(current_params, param_names, data_dict)

    step_size = initial_step
    cov_matrix = np.eye(n_params) * (step_size ** 2)

    total_iters = n_samples + n_burn
    chain = np.zeros((total_iters, n_params))
    accepted = 0
    batch_accepted = 0

    for i in range(total_iters):
        # Propuesta aleatoria gaussiana
        proposal = np.random.multivariate_normal(current_params, cov_matrix)
        prop_logp = log_posterior(proposal, param_names, data_dict)

        ratio = prop_logp - current_logp
        if np.log(np.random.rand()) < ratio:
            current_params = proposal
            current_logp = prop_logp
            accepted += 1
            batch_accepted += 1

        chain[i] = current_params

        # Adaptación de paso durante burn-in para tasa de aceptación óptima (~25-35%)
        if i < n_burn and (i + 1) % 50 == 0:
            rate = batch_accepted / 50.0
            if rate < 0.20:
                step_size *= 0.8
            elif rate > 0.40:
                step_size *= 1.2
            cov_matrix = np.eye(n_params) * (step_size ** 2)
            batch_accepted = 0

    valid_samples = chain[n_burn:]
    acc_rate = accepted / total_iters

    # Resumen de resultados
    results_summary = {}
    posterior_means = {}
    for idx, name in enumerate(param_names):
        vals = valid_samples[:, idx]
        mean_val = float(np.mean(vals))
        std_val = float(np.std(vals))
        p5 = float(np.percentile(vals, 5))
        p95 = float(np.percentile(vals, 95))
        posterior_means[name] = mean_val
        results_summary[name] = {
            'prior_mean': PRIORS[name]['mean'],
            'post_mean': mean_val,
            'post_std': std_val,
            'ci_90': (p5, p95)
        }

    return {
        'posterior_means': posterior_means,
        'summary': results_summary,
        'samples': valid_samples,
        'param_names': param_names,
        'acceptance_rate': acc_rate
    }
