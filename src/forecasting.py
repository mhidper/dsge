"""
Motor de previsión a medio plazo, simulación de escenarios y cálculo de abanicos de incertidumbre.

FASE 1 (unificación del motor):
    El bucle de proyección futura usa AHORA las mismas funciones de transición
    (`*_step` de `model.py`) y el mismo diccionario de parámetros `p` que la
    simulación histórica y la estimación bayesiana. Se eliminan los coeficientes
    incrustados (0.86, 0.12, 0.15, 0.45, ...) y el recargo energético aditivo de
    +3.5 pp sin base estructural. Quedan reactivados los canales que antes se
    perdían en la previsión: impulso fiscal/NGEU, turismo, REER, China y EE.UU.,
    de modo que la calibración y el posterior sí determinan la senda proyectada.
"""

from typing import Dict, List, Optional
import numpy as np
import pandas as pd
from .config import DEFAULT_PARAMS
from .model import (
    simulate_model, is_step, phillips_services_step, phillips_goods_step,
    energy_step, energy_pressure_step, food_step, okun_step, taylor_rule_step,
    aggregate_inflation_point, pct_change_safe, compute_unemployment_seasonal_factors
)
from .scenarios import build_scenario_paths
from .potential import compute_historical_potential, project_potential_path


def generate_forecast(df_history: pd.DataFrame,
                      horizon_quarters: int = 12,
                      scenario_type: str = 'baseline',
                      custom_exogenous: Optional[Dict[str, List[float]]] = None,
                      params: Optional[Dict[str, float]] = None) -> pd.DataFrame:
    """
    Genera la proyección central determinista para un escenario dado, usando el
    núcleo estructural unificado (`*_step`) con los parámetros `params`.
    """
    p = DEFAULT_PARAMS.copy()
    if params:
        p.update(params)

    last_date = df_history.index[-1]
    future_dates = pd.date_range(start=last_date + pd.DateOffset(months=3),
                                 periods=horizon_quarters, freq='QS')

    last_vals = {col: float(df_history[col].iloc[-1]) for col in df_history.columns
                 if not pd.isna(df_history[col].iloc[-1])}

    exog_paths = build_scenario_paths(last_vals, horizon_quarters, scenario_type, custom_exogenous)

    df_combined = df_history.copy()
    future_rows = pd.DataFrame(index=future_dates, columns=df_combined.columns)
    df_combined = pd.concat([df_combined, future_rows])

    for var, path in exog_paths.items():
        if var not in df_combined.columns:
            df_combined[var] = np.nan
        df_combined.loc[future_dates, var] = path

    # Forward-fill de base para exógenas de apoyo no fijadas por el escenario
    df_combined = df_combined.ffill()

    t_start = len(df_history)
    t_end = len(df_combined)

    sim = {col: df_combined[col].values.astype(float) for col in df_combined.columns}

    # Asegurar presencia de todas las series necesarias
    n_tot = len(df_combined)
    for key, default in [
        ('output_gap_spain', 0.0), ('inflation_services', 2.0), ('inflation_goods', 1.5),
        ('inflation_energy', 0.0), ('energy_pressure', p['inflation_target']),
        ('energy_policy_overlay', 0.0),
        ('inflation_food', 2.0), ('inflation_core', 2.0),
        ('inflation_total', 2.0), ('unemployment_rate', p['nairu_default']),
        ('unemployment_rate_sa', p['nairu_default']),
        ('nairu', p['nairu_default']), ('interest_rate_ecb', 2.5),
        ('risk_premium_spain', 0.8), ('interest_rate_spain', 3.0),
        ('oil_price_brent', 75.0), ('gas_price_ttf', 35.0),
        ('output_gap_eu', 0.0), ('output_gap_usa', 0.0), ('output_gap_china', 0.0),
        ('real_exchange_rate', 100.0), ('reer_gap', 0.0), ('fiscal_impulse', 0.0),
        ('gdp_real_spain', 100.0), ('gdp_potential_spain', 100.0),
    ]:
        if key not in sim:
            sim[key] = np.full(n_tot, default, dtype=float)
        sim[key] = np.nan_to_num(sim[key], nan=default)

    # Factores estacionales de la tasa de paro EPA y serie desestacionalizada histórica
    seas_u = compute_unemployment_seasonal_factors(df_history['unemployment_rate']) if 'unemployment_rate' in df_history.columns else {1: 0.52, 2: -0.12, 3: -0.30, 4: -0.10}
    if 'unemployment_rate_sa' not in df_history.columns or np.isnan(sim['unemployment_rate_sa'][:t_start]).any():
        for i in range(t_start):
            q_i = df_combined.index[i].quarter
            sim['unemployment_rate_sa'][i] = sim['unemployment_rate'][i] - seas_u.get(q_i, 0.0)

    sim['gdp_growth_quarterly'] = np.zeros(n_tot)
    sim['gdp_growth_annual'] = np.zeros(n_tot)
    sim['employment_yoy'] = np.zeros(n_tot)

    # Histórico de crecimiento del PIB (para empalmar tasas interanuales)
    for i in range(1, t_start):
        sim['gdp_growth_quarterly'][i] = pct_change_safe(sim['gdp_real_spain'][i], sim['gdp_real_spain'][i - 1])
    for i in range(4, t_start):
        sim['gdp_growth_annual'][i] = pct_change_safe(sim['gdp_real_spain'][i], sim['gdp_real_spain'][i - 4])

    # Sembrar el acumulador de presión energética sobre el histórico, para que el
    # valor de arranque (t_start-1) refleje el estado energético real del jump-off
    # y no un default plano. A partir de ahí el bucle lo prolonga.
    if t_start > 0:
        sim['energy_pressure'][0] = sim['inflation_energy'][0]
        for i in range(1, t_start):
            sim['energy_pressure'][i] = energy_pressure_step(
                sim['energy_pressure'][i - 1], sim['inflation_energy'][i], p)

    # Ponderaciones normalizadas del IPC (para subyacente contemporánea)
    w_s = p['weight_services']; w_g = p['weight_goods']
    core_ws = w_s / (w_s + w_g)

    # Proyección del PIB potencial por función de producción (Fase 3):
    # prolonga la población en edad de trabajar con desaceleración migratoria gradual.
    # `migration_wap_growth` (en params o escenario) es la palanca migratoria de escenario.
    try:
        pf_state = compute_historical_potential(df_history['gdp_real_spain'].astype(float).interpolate())
        pf_proj = project_potential_path(pf_state, horizon_quarters, p,
                                         migration_wap_growth=p.get('migration_wap_growth'))
        future_potential = pf_proj['gdp_potential']
    except Exception:
        # Repliegue robusto: crecimiento potencial constante ~2.2% anual
        g_q = (1.0 + 0.022) ** 0.25 - 1.0
        base = float(df_history['gdp_potential_spain'].iloc[-1])
        future_potential = np.array([base * (1.0 + g_q) ** (k + 1) for k in range(horizon_quarters)])

    # Turismo futuro: proxy coherente con el histórico (tracción UE) salvo escenario explícito
    tourism_future = exog_paths.get('tourism_demand', None)

    # Inflación de la Eurozona para la Phillips de bienes: último dato válido o defecto de config
    pi_eu_default = p.get('inflation_eu_default', p['inflation_target'])
    if 'inflation_eu' in df_history.columns:
        _eu = df_history['inflation_eu'].values.astype(float)
        _eu = _eu[np.isfinite(_eu)]
        pi_eu_t = float(_eu[-1]) if len(_eu) > 0 else pi_eu_default
    else:
        pi_eu_t = pi_eu_default

    beta_e = p['employment_output_elast']

    # Overlay de medidas energéticas conmutables en la PROYECCIÓN. Por defecto vacío
    # (POLICY_MEASURES_FORECAST = []). Para simular "¿y si vuelve el tope al gas / los
    # 20 cts?", basta poblar esa lista en config con la ventana futura: aquí se inyecta
    # su escalón en el tramo proyectado, sin tocar el histórico.
    try:
        from .data_pipeline import build_policy_overlay
        from .config import POLICY_MEASURES_FORECAST
        if POLICY_MEASURES_FORECAST:
            ov_fc = build_policy_overlay(df_combined.index, POLICY_MEASURES_FORECAST)
            sim['energy_policy_overlay'][t_start:] = ov_fc.values[t_start:]
    except Exception as e:
        print(f"Aviso: overlay de medidas en proyección no disponible: {e}")

    # ------------------------------------------------------------------
    # BUCLE RECURSIVO DE PROYECCIÓN (núcleo estructural unificado)
    # ------------------------------------------------------------------
    for t in range(t_start, t_end):
        # A. Política monetaria ENDÓGENA (Fase 5): el tipo del BCE lo fija una regla de
        # Taylor con suavizado, en función de la subyacente rezagada y de la brecha
        # (española + UEM). Sustituye al tipo exógeno del escenario, que dejaba la
        # política "clavada" y disparaba espirales deflacionarias. Un escenario puede
        # inyectar un sesgo hawkish/dovish vía 'monetary_shock'.
        mon_shock = sim['monetary_shock'][t] if 'monetary_shock' in sim else 0.0
        sim['interest_rate_ecb'][t] = taylor_rule_step(
            sim['interest_rate_ecb'][t - 1], sim['inflation_core'][t - 1],
            sim['output_gap_spain'][t - 1], sim['output_gap_eu'][t], p, mon_shock)
        sim['interest_rate_spain'][t] = sim['interest_rate_ecb'][t] + sim['risk_premium_spain'][t]
        # Expectativa de inflación anclada parcialmente al objetivo (Fase 2): mismo operador
        # de expectativas que las curvas de Phillips (0.5·objetivo + 0.5·subyacente rezagada).
        # Reduce la retroalimentación desestabilizadora inflación->tipo real->brecha.
        exp_infl = 0.5 * p['inflation_target'] + 0.5 * sim['inflation_core'][t - 1]
        real_rate_gap = (sim['interest_rate_spain'][t] - exp_infl) - p['r_neutral_spain']

        # B. Curva IS (con TODOS los canales activos y parámetros reales)
        tour_t = tourism_future[t - t_start] if tourism_future is not None else sim['output_gap_eu'][t] * 0.4
        sim['output_gap_spain'][t] = is_step(
            sim['output_gap_spain'][t - 1], real_rate_gap,
            sim['output_gap_eu'][t], sim['output_gap_usa'][t], sim['output_gap_china'][t],
            sim['reer_gap'][t], sim['fiscal_impulse'][t], tour_t, p
        )
        gap_t = sim['output_gap_spain'][t]

        # C. Precios de energía (Δoil, Δgas) y cascada de precios (Fase 4)
        oil_pct = pct_change_safe(sim['oil_price_brent'][t], sim['oil_price_brent'][t - 1])
        gas_pct = pct_change_safe(sim['gas_price_ttf'][t], sim['gas_price_ttf'][t - 1])
        sim['inflation_energy'][t] = energy_step(
            sim['inflation_energy'][t - 1], oil_pct, gas_pct, p,
            policy_delta=float(sim['energy_policy_overlay'][t]))

        # Acumulador de presión energética; SOLO alimenta a los alimentos (no a la subyacente)
        sim['energy_pressure'][t] = energy_pressure_step(
            sim['energy_pressure'][t - 1], sim['inflation_energy'][t], p)
        z_lag = sim['energy_pressure'][t - 1]

        # La subyacente NO reacciona directamente a la energía: solo persigue la cuña
        # general-núcleo rezagada (canal de segunda ronda pequeño y autolimitado).
        wedge_lag = sim['inflation_total'][t - 1] - sim['inflation_core'][t - 1]

        clu_gap = gap_t * 0.7
        sim['inflation_services'][t] = phillips_services_step(
            sim['inflation_services'][t - 1], gap_t, clu_gap, wedge_lag, p)

        reer_diff = sim['real_exchange_rate'][t] - sim['real_exchange_rate'][t - 1]
        sim['inflation_goods'][t] = phillips_goods_step(
            sim['inflation_goods'][t - 1], gap_t, reer_diff, pi_eu_t, wedge_lag, p)

        # Alimentos: la energía SÍ es el motor (Z rezagado) + subyacente rezagada (coste laboral)
        core_lag = sim['inflation_core'][t - 1]
        sim['inflation_food'][t] = food_step(sim['inflation_food'][t - 1], z_lag, core_lag, p)

        pi_total, pi_core = aggregate_inflation_point(
            sim['inflation_services'][t], sim['inflation_goods'][t],
            sim['inflation_food'][t], sim['inflation_energy'][t], p)
        sim['inflation_total'][t] = pi_total
        sim['inflation_core'][t] = pi_core

        # D. Mercado laboral (Okun sobre tasa desestacionalizada, NAIRU híbrida y estacionalidad EPA)
        rho_n = p.get('nairu_persistence', 0.94)
        n_ss = p.get('nairu_ss', 8.85)
        sim['nairu'][t] = rho_n * sim['nairu'][t - 1] + (1.0 - rho_n) * n_ss

        gap_diff = gap_t - sim['output_gap_spain'][t - 1]
        sim['unemployment_rate_sa'][t] = okun_step(
            sim['unemployment_rate_sa'][t - 1], sim['nairu'][t], sim['nairu'][t - 1], gap_diff, p,
            gap_level=gap_t)
        
        # Módulo satélite aditivo: superposición de estacionalidad observada EPA
        q_t = df_combined.index[t].quarter
        sim['unemployment_rate'][t] = sim['unemployment_rate_sa'][t] + seas_u.get(q_t, 0.0)

        # E. PIB potencial (proyección por función de producción) y PIB real
        sim['gdp_potential_spain'][t] = future_potential[t - t_start]
        sim['gdp_real_spain'][t] = sim['gdp_potential_spain'][t] * (1.0 + gap_t / 100.0)
        sim['gdp_growth_quarterly'][t] = pct_change_safe(sim['gdp_real_spain'][t], sim['gdp_real_spain'][t - 1])
        sim['gdp_growth_annual'][t] = pct_change_safe(sim['gdp_real_spain'][t], sim['gdp_real_spain'][t - 4])

        # F. Empleo: variación interanual coherente con la elasticidad empleo-PIB
        # (acumulación de 4 crecimientos trimestrales; sustituye al atajo 0.75·PIB)
        if t - t_start >= 3:
            sim['employment_yoy'][t] = sum(
                beta_e * (sim['gdp_growth_quarterly'][k] / 100.0) for k in range(t - 3, t + 1)
            ) * 100.0
        else:
            sim['employment_yoy'][t] = sim['gdp_growth_annual'][t] * beta_e

    forecast_df = pd.DataFrame(index=future_dates)
    for col in ['gdp_growth_annual', 'gdp_growth_quarterly', 'gdp_real_spain', 'gdp_potential_spain', 'output_gap_spain',
                'inflation_total', 'inflation_core', 'inflation_services', 'inflation_goods',
                'inflation_energy', 'inflation_food', 'unemployment_rate', 'unemployment_rate_sa',
                'nairu', 'employment_yoy', 'interest_rate_spain', 'interest_rate_ecb', 'oil_price_brent']:
        if col in sim:
            forecast_df[col] = sim[col][t_start:]
    return forecast_df


def generate_monte_carlo_bands(df_history: pd.DataFrame,
                               horizon_quarters: int = 12,
                               scenario_type: str = 'baseline',
                               params: Optional[Dict[str, float]] = None,
                               n_sims: int = 500,
                               sigma_shocks: Optional[Dict[str, float]] = None) -> Dict[str, Dict[str, np.ndarray]]:
    """
    Genera bandas de incertidumbre (fan charts) para las principales variables.
    NOTA (pendiente de fase posterior): actualmente perturba la senda central con
    ruido gaussiano; la propagación de shocks a través de la dinámica del modelo
    se abordará al reescribir el bloque estocástico.
    """
    p = DEFAULT_PARAMS.copy()
    if params:
        p.update(params)

    sigmas = {'is_demand': 0.40, 'supply_nt': 0.35, 'supply_t': 0.45, 'okun_labor': 0.25, 'oil_shock': 5.0}
    if sigma_shocks:
        sigmas.update(sigma_shocks)

    target_vars = ['output_gap_spain', 'gdp_growth_annual', 'gdp_growth_quarterly',
                   'inflation_total', 'inflation_core', 'unemployment_rate', 'unemployment_rate_sa',
                   'nairu', 'employment_yoy']
    sim_trajectories = {var: np.zeros((n_sims, horizon_quarters)) for var in target_vars}

    central_df = generate_forecast(df_history, horizon_quarters, scenario_type, params=p)

    np.random.seed(42)
    for s in range(n_sims):
        shock_demand = np.random.normal(0, sigmas['is_demand'], horizon_quarters)
        shock_inflation = np.random.normal(0, sigmas['supply_nt'], horizon_quarters)
        shock_unemp = np.random.normal(0, sigmas['okun_labor'], horizon_quarters)
        sim_trajectories['output_gap_spain'][s, :] = central_df['output_gap_spain'].values + shock_demand
        sim_trajectories['gdp_growth_annual'][s, :] = central_df['gdp_growth_annual'].values + shock_demand * 0.8
        sim_trajectories['gdp_growth_quarterly'][s, :] = central_df['gdp_growth_quarterly'].values + shock_demand * 0.4
        sim_trajectories['inflation_total'][s, :] = central_df['inflation_total'].values + shock_inflation + shock_demand * 0.15
        sim_trajectories['inflation_core'][s, :] = central_df['inflation_core'].values + shock_inflation * 0.7
        sim_trajectories['unemployment_rate'][s, :] = np.clip(central_df['unemployment_rate'].values + shock_unemp - shock_demand * 0.3, 4.0, 30.0)
        sim_trajectories['unemployment_rate_sa'][s, :] = np.clip(central_df['unemployment_rate_sa'].values + shock_unemp - shock_demand * 0.3, 4.0, 30.0)
        sim_trajectories['nairu'][s, :] = central_df['nairu'].values
        sim_trajectories['employment_yoy'][s, :] = central_df['employment_yoy'].values + shock_demand * 0.5 - shock_unemp * 0.6

    bands = {}
    for var in target_vars:
        bands[var] = {
            'central': central_df[var].values,
            'p10': np.percentile(sim_trajectories[var], 10, axis=0),
            'p25': np.percentile(sim_trajectories[var], 25, axis=0),
            'p50': np.percentile(sim_trajectories[var], 50, axis=0),
            'p75': np.percentile(sim_trajectories[var], 75, axis=0),
            'p90': np.percentile(sim_trajectories[var], 90, axis=0),
            'dates': central_df.index
        }
    return bands
