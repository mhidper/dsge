"""
Ecuaciones estructurales y simulador del modelo Semi-DSGE para la economía española.

FASE 1 (unificación del motor):
    La dinámica período-a-período vive ahora en funciones `*_step` que son la ÚNICA
    fuente de verdad. Tanto la simulación histórica (`simulate_model`, usada por la
    estimación bayesiana) como el motor de previsión (`forecasting.generate_forecast`)
    llaman a estas mismas funciones con el MISMO conjunto de parámetros `p`. Así se
    elimina el desacople anterior, en el que la previsión reimplementaba las ecuaciones
    con coeficientes incrustados y no respondía ni a la calibración ni al posterior.
"""

from typing import Dict, Tuple, Optional
import numpy as np
import pandas as pd
from .config import DEFAULT_PARAMS


def lag_array(arr: np.ndarray, lags: int = 1, fill_val: Optional[float] = None) -> np.ndarray:
    """Crea una serie rezagada en numpy de forma eficiente."""
    out = np.empty_like(arr)
    fill = arr[0] if fill_val is None else fill_val
    if lags >= len(arr):
        out[:] = fill
    else:
        out[:lags] = fill
        out[lags:] = arr[:-lags]
    return out


def pct_change_safe(cur: float, prev: float) -> float:
    """Variación porcentual robusta ante denominadores no positivos."""
    if prev is None or not np.isfinite(prev) or prev <= 0:
        return 0.0
    return ((cur - prev) / prev) * 100.0


# ==============================================================================
# NÚCLEO DINÁMICO: FUNCIONES DE TRANSICIÓN PERÍODO A PERÍODO (*_step)
# ------------------------------------------------------------------------------
# Reciben el estado rezagado (t-1) y las variables contemporáneas/exógenas (t)
# y devuelven el valor endógeno en t. Son deterministas y no dependen de arrays,
# por lo que sirven indistintamente para el histórico y la proyección futura.
# ==============================================================================

def is_step(gap_lag: float, real_rate_gap: float, gap_eu: float, gap_us: float,
            gap_cn: float, reer_gap: float, fiscal: float, tourism: float,
            p: Dict[str, float]) -> float:
    """
    Curva IS abierta (brecha de producto) en t:
    ỹ_t = a1 ỹ_{t-1} + a2 E[ỹ_{t+1}] - a_r (r_t - r*) + a_eu ỹ^EU + a_us ỹ^US
          + a_cn ỹ^CN - a_reer reer_gap + a_f f_t + a_tr tour_t
    La expectativa forward se aproxima como ỹ_{t-1}·0.85 (convención heredada;
    su sustitución por expectativas resueltas se aborda en una fase posterior).
    """
    a1 = p['is_persistence']
    a2 = p['is_forward']
    ar = p['is_interest_rate']
    a_eu = p['is_demand_eu']
    a_us = p['is_demand_usa']
    a_cn = p['is_demand_china']
    a_reer = p['is_reer']
    a_f = p['is_fiscal']
    a_tr = p['is_tourism']

    gap_fwd = gap_lag * 0.85
    return (
        a1 * gap_lag
        + a2 * gap_fwd
        - ar * real_rate_gap
        + a_eu * gap_eu
        + a_us * gap_us
        + a_cn * gap_cn
        - a_reer * reer_gap
        + a_f * fiscal
        + a_tr * tourism
    )


def _headline_core_wedge_lag(data: Dict[str, np.ndarray], n: int, target: float) -> np.ndarray:
    """Cuña general-núcleo rezagada un trimestre: (π^gen_{t-1} - π^core_{t-1}).

    Es el término que canaliza la energía hacia la subyacente de forma indirecta y
    acotada: la general recoge la energía por su peso en la cesta, y la subyacente
    solo persigue esa brecha. Se construye con inflación OBSERVADA (predeterminada),
    de modo que el bloque de precios sigue siendo recursivo. Si no hay datos de
    general/núcleo, la cuña es cero (el canal se desactiva sin romper nada).
    """
    if 'inflation_total' in data and 'inflation_core' in data:
        wedge = np.asarray(data['inflation_total'], float) - np.asarray(data['inflation_core'], float)
        wedge = np.nan_to_num(wedge, nan=0.0)
        return lag_array(wedge, 1, fill_val=0.0)
    return np.zeros(n)


def phillips_services_step(pi_nt_lag: float, output_gap: float, clu_gap: float,
                           head_core_wedge_lag: float, p: Dict[str, float]) -> float:
    """π^nt_t = φ_b π^nt_{t-1} + φ_f E[π] + λ ỹ_t + γ CLU_gap_t + δ (π^gen_{t-1} - π^core_{t-1}).

    La subyacente de servicios NO reacciona directamente a la energía (cf. BCCh WP-866).
    Se mueve por su propia inercia (término dominante), expectativas ancladas al objetivo
    y la brecha de producción. El ÚNICO canal energético es el término de convergencia
    δ·(general-núcleo) rezagado: efecto de segunda ronda pequeño y AUTOLIMITADO, porque
    la brecha se cierra a medida que la subyacente se ajusta (estilo QPM India, FMI WP/17/33).
    """
    fb = p['phillips_nt_backward']
    ff = p['phillips_nt_forward']
    flambda = p['phillips_nt_gap']
    fclu = p['phillips_nt_clu']
    conv = p.get('phillips_headline_conv', 0.0)
    target = p['inflation_target']
    # Ancla híbrida NKPC: los pesos backward/forward se normalizan a suma 1 y la parte
    # forward apunta al objetivo. Garantiza que, sin shocks (brecha y cuña nulas), la
    # subyacente revierta EXACTAMENTE al 2%, en vez de a un nivel sesgado por debajo.
    w_sum = fb + ff
    w_b, w_f = (fb / w_sum, ff / w_sum) if w_sum > 0 else (1.0, 0.0)
    anchor = w_b * pi_nt_lag + w_f * target
    return (
        anchor
        + flambda * output_gap
        + fclu * clu_gap
        + conv * head_core_wedge_lag
    )


def phillips_goods_step(pi_t_lag: float, output_gap: float, reer_diff: float,
                        pi_eu: float, head_core_wedge_lag: float, p: Dict[str, float]) -> float:
    """π^t_t = β_b π^t_{t-1} + β_f E[π] + λ ỹ_t + β_reer Δreer + β_eu (π^EU-π*) + δ (π^gen-π^core)_{t-1}.

    La subyacente de bienes tampoco reacciona directamente a la energía: sus canales de
    coste exterior son el tipo de cambio real (Δreer) y la inflación importada de la UE,
    fieles al modelo chileno (b^t4 depreciación, b^t5 TCR). La energía solo entra por el
    mismo término de convergencia autolimitado que los servicios.
    """
    bb = p['phillips_t_backward']
    bf = p['phillips_t_forward']
    blambda = p['phillips_t_gap']
    breer = p['phillips_t_reer']
    beu = p['phillips_t_foreign']
    conv = p.get('phillips_headline_conv', 0.0)
    target = p['inflation_target']
    # Misma ancla híbrida normalizada que en servicios: reversión al objetivo sin shocks.
    w_sum = bb + bf
    w_b, w_f = (bb / w_sum, bf / w_sum) if w_sum > 0 else (1.0, 0.0)
    anchor = w_b * pi_t_lag + w_f * target
    return (
        anchor
        + blambda * output_gap
        + breer * reer_diff
        + beu * (pi_eu - target)
        + conv * head_core_wedge_lag
    )


def energy_step(pi_e_lag: float, oil_pct: float, gas_pct: float, p: Dict[str, float],
                policy_delta: float = 0.0) -> float:
    """π^energ_t = ρ_e π^energ_{t-1} + δ_oil Δoil + δ_gas Δgas + (medidas)_t.

    ``policy_delta`` es el escalón de las medidas regulatorias conmutables activas
    en t (Σ θ·ΔD): abarata al entrar una medida y rebota al salir. Es aditivo y
    separado de las elasticidades estructurales, de modo que activar o desactivar
    una medida no altera la estructura del pass-through.
    """
    rho = p['energy_persistence']
    d_oil = p['energy_oil_elasticity']
    d_gas = p['energy_gas_elasticity']
    return rho * pi_e_lag + d_oil * oil_pct + d_gas * gas_pct + policy_delta


def energy_pressure_step(z_lag: float, pi_energy: float, p: Dict[str, float]) -> float:
    """Acumulador de presión energética (retardo geométrico tipo Koyck).

    Z^e_t = μ Z^e_{t-1} + (1-μ) π^e_t.

    Z^e es una media móvil exponencial de la inflación energética: con μ alto su pico
    llega VARIOS trimestres después del de π^e, reproduciendo el desfase con que el
    shock energético de 2021-22 se transmitió a alimentos y subyacente en 2022-23.
    Un único estado captura de forma parsimoniosa toda la estructura de retardos.
    """
    mu = p['energy_pressure_persistence']
    return mu * z_lag + (1.0 - mu) * pi_energy


def food_step(pi_food_lag: float, energy_pressure_lag: float, core_lag: float,
              p: Dict[str, float]) -> float:
    """π^alim_t = ρ_a π^alim_{t-1} + δ_fe (Z^e_{t-1} - π*) + δ_fc π^core_{t-1}.

    La ENERGÍA es el motor con retardo (fertilizantes, piensos, transporte, procesado):
    entra por el acumulador Z^e rezagado. La subyacente entra también REZAGADA como
    coste laboral/márgenes, no contemporánea: en 2022-24 la energía lideró los alimentos,
    y estos a la subyacente, no al revés.
    """
    rho = p['food_persistence']
    d_fe = p.get('food_energy_transmission', 0.0)
    d_fc = p['food_core_transmission']
    target = p['inflation_target']
    return rho * pi_food_lag + d_fe * (energy_pressure_lag - target) + d_fc * core_lag


def taylor_rule_step(ecb_lag: float, core_infl_lag: float, gap_spain_lag: float,
                     gap_eu: float, p: Dict[str, float], mon_shock: float = 0.0) -> float:
    """Regla de Taylor del BCE con suavizado (endogeniza el tipo en la proyección).

    i_bce_t = ρ·i_bce_{t-1} + (1-ρ)·[i* + φ_π·(π^core_{t-1} - π*) + φ_y·brecha] + shock

    Responde a la inflación SUBYACENTE rezagada (medio plazo, "mira a través" de la
    energía) y a una mezcla de la brecha española y de la UEM. Al abrirse la brecha y
    desinflarse el núcleo, el tipo baja y corta la espiral deflacionaria fisheriana.
    `mon_shock` permite a un escenario añadir un sesgo hawkish/dovish sobre la regla.
    Respeta un suelo efectivo (ELB).
    """
    rho = p['ecb_smoothing']
    i_star = p['ecb_neutral_nominal']
    phi_pi = p['taylor_inflation']
    phi_y = p['taylor_gap']
    target = p['inflation_target']
    w_es = p.get('taylor_gap_weight_spain', 0.5)
    floor = p.get('ecb_floor', 0.0)

    gap_signal = w_es * gap_spain_lag + (1.0 - w_es) * gap_eu
    i_target = i_star + phi_pi * (core_infl_lag - target) + phi_y * gap_signal
    i = rho * ecb_lag + (1.0 - rho) * i_target + mon_shock
    return float(max(i, floor))


def okun_step(u_lag: float, nairu_t: float, nairu_lag: float, gap_diff: float,
              p: Dict[str, float], gap_level: float = 0.0) -> float:
    """u_t = u*_t + δ_u (u_{t-1} - u*_{t-1}) - θ_gap ỹ_t - θ_diff Δỹ_t, acotada a [4, 30]."""
    delta_u = p['okun_persistence']
    theta_diff = p.get('okun_sensitivity', 0.22)
    theta_gap = p.get('okun_gap_sensitivity', 0.28)
    val = nairu_t + delta_u * (u_lag - nairu_lag) - theta_gap * gap_level - theta_diff * gap_diff
    return float(np.clip(val, 4.0, 30.0))


def compute_unemployment_seasonal_factors(u_series: pd.Series) -> Dict[int, float]:
    """Calcula los factores estacionales trimestrales aditivos de la EPA (suma cero).
    
    s_q = Media(u_t - MA4(u_t) | trimestre=q), centrados para que sum(s_q) = 0.
    Permite proyectar la tasa de paro con su patrón estacional intra-anual (dientes de sierra)
    de forma coherente con la dinámica estructural desestacionalizada (Okun).
    """
    u_clean = u_series.dropna()
    if len(u_clean) < 16:
        return {1: 0.52, 2: -0.12, 3: -0.30, 4: -0.10}
    ma4 = u_clean.rolling(4, center=True).mean()
    diff = u_clean - ma4
    diff_by_q = diff.groupby(diff.index.quarter).mean()
    centered = diff_by_q - diff_by_q.mean()
    return centered.to_dict()


def aggregate_inflation_point(pi_s: float, pi_g: float, pi_f: float, pi_e: float,
                              p: Dict[str, float]) -> Tuple[float, float]:
    """Agrega inflación general y subyacente en un punto con las ponderaciones normalizadas."""
    w_s = p['weight_services']
    w_g = p['weight_goods']
    w_f = p['weight_food']
    w_e = p['weight_energy']
    tot = w_s + w_g + w_f + w_e
    w_s, w_g, w_f, w_e = w_s / tot, w_g / tot, w_f / tot, w_e / tot
    core = (w_s / (w_s + w_g)) * pi_s + (w_g / (w_s + w_g)) * pi_g
    total = w_s * pi_s + w_g * pi_g + w_f * pi_f + w_e * pi_e
    return total, core


# ==============================================================================
# ECUACIONES SOBRE ARRAYS (histórico) — construidas sobre las *_step
# ==============================================================================

def interest_rate_equation(data: Dict[str, np.ndarray], params: Dict[str, float]) -> np.ndarray:
    """Tipo nominal en España (UEM): i_esp = i_ecb + spread."""
    n = len(data.get('output_gap_spain', []))
    i_ecb = data.get('interest_rate_ecb', np.full(n, 2.5))
    spread = data.get('risk_premium_spain', np.full(n, 0.8))
    return i_ecb + spread


def is_curve_spain(data: Dict[str, np.ndarray], params: Dict[str, float],
                   gap_initial: Optional[np.ndarray] = None) -> np.ndarray:
    """Curva IS abierta evaluada recursivamente sobre el histórico usando `is_step`."""
    n = len(data.get('output_gap_spain', []))
    if n == 0:
        return np.array([])
    p = DEFAULT_PARAMS.copy()
    p.update(params)

    nominal_rate = data.get('interest_rate_spain', np.full(n, 3.0))
    infl_exp = data.get('inflation_core', np.full(n, 2.0))
    real_rate = nominal_rate - infl_exp
    real_rate_gap = real_rate - p['r_neutral_spain']

    gap_eu = data.get('output_gap_eu', np.zeros(n))
    gap_us = data.get('output_gap_usa', np.zeros(n))
    gap_cn = data.get('output_gap_china', np.zeros(n))
    reer_gap = data.get('reer_gap', np.zeros(n))
    fiscal = data.get('fiscal_impulse', np.zeros(n))
    tourism = data.get('tourism_demand', gap_eu * 0.4)

    fitted_gap = np.zeros(n)
    if gap_initial is not None and len(gap_initial) > 0:
        fitted_gap[0] = gap_initial[0]
    elif 'output_gap_spain' in data and len(data['output_gap_spain']) > 0:
        fitted_gap[0] = data['output_gap_spain'][0]

    for t in range(1, n):
        fitted_gap[t] = is_step(
            fitted_gap[t - 1], real_rate_gap[t], gap_eu[t], gap_us[t], gap_cn[t],
            reer_gap[t], fiscal[t], tourism[t], p
        )
    return fitted_gap


def phillips_curve_services(data: Dict[str, np.ndarray], params: Dict[str, float]) -> np.ndarray:
    """Curva de Phillips de servicios/no transables evaluada con `phillips_services_step`."""
    n = len(data.get('output_gap_spain', []))
    p = DEFAULT_PARAMS.copy()
    p.update(params)
    output_gap = data.get('output_gap_spain', np.zeros(n))
    pi_target = p['inflation_target']

    pi_nt = data.get('inflation_services', data.get('inflation_core', np.full(n, pi_target)))
    clu_gap = data.get('clu_gap', output_gap * 0.7)
    # Cuña general-núcleo rezagada: único canal energético (autolimitado). Se toma de la
    # inflación observada (predeterminada), lo que mantiene el bloque recursivo.
    wedge_lag = _headline_core_wedge_lag(data, n, pi_target)

    fitted_nt = np.zeros(n)
    fitted_nt[0] = pi_nt[0] if len(pi_nt) > 0 and not np.isnan(pi_nt[0]) else pi_target
    for t in range(1, n):
        fitted_nt[t] = phillips_services_step(
            fitted_nt[t - 1], output_gap[t], clu_gap[t], wedge_lag[t], p
        )
    return fitted_nt


def phillips_curve_goods(data: Dict[str, np.ndarray], params: Dict[str, float]) -> np.ndarray:
    """Curva de Phillips de bienes transables evaluada con `phillips_goods_step`."""
    n = len(data.get('output_gap_spain', []))
    p = DEFAULT_PARAMS.copy()
    p.update(params)
    output_gap = data.get('output_gap_spain', np.zeros(n))
    pi_target = p['inflation_target']

    pi_t_arr = data.get('inflation_goods', data.get('inflation_core', np.full(n, pi_target)))
    reer = data.get('real_exchange_rate', np.full(n, 100.0))
    reer_diff = np.diff(reer, prepend=reer[0])
    pi_eu = data.get('inflation_eu', np.full(n, pi_target))
    wedge_lag = _headline_core_wedge_lag(data, n, pi_target)

    fitted_t = np.zeros(n)
    fitted_t[0] = pi_t_arr[0] if len(pi_t_arr) > 0 and not np.isnan(pi_t_arr[0]) else pi_target
    for t in range(1, n):
        fitted_t[t] = phillips_goods_step(
            fitted_t[t - 1], output_gap[t], reer_diff[t], pi_eu[t], wedge_lag[t], p
        )
    return fitted_t


def energy_inflation_equation(data: Dict[str, np.ndarray], params: Dict[str, float]) -> np.ndarray:
    """Inflación de energía evaluada con `energy_step`."""
    n = len(data.get('output_gap_spain', []))
    p = DEFAULT_PARAMS.copy()
    p.update(params)
    oil = data.get('oil_price_brent', np.full(n, 75.0))
    oil_lag = lag_array(oil, 1)
    oil_pct = np.where(oil_lag > 0, ((oil - oil_lag) / oil_lag) * 100.0, 0.0)
    gas = data.get('gas_price_ttf', np.full(n, 35.0))
    gas_lag = lag_array(gas, 1)
    gas_pct = np.where(gas_lag > 0, ((gas - gas_lag) / gas_lag) * 100.0, 0.0)

    overlay = data.get('energy_policy_overlay', np.zeros(n))
    pi_energy = np.zeros(n)
    if 'inflation_energy' in data and len(data['inflation_energy']) > 0:
        pi_energy[0] = data['inflation_energy'][0]
    for t in range(1, n):
        pi_energy[t] = energy_step(pi_energy[t - 1], oil_pct[t], gas_pct[t], p,
                                   policy_delta=float(overlay[t]) if t < len(overlay) else 0.0)
    return pi_energy


def energy_pressure_equation(pi_energy: np.ndarray, params: Dict[str, float]) -> np.ndarray:
    """Serie del acumulador de presión energética Z^e (retardo geométrico Koyck).

    Construido sobre `energy_step`'s output con `energy_pressure_step`. Este estado es
    el que propaga el shock energético hacia alimentos y subyacente con inercia y retardo.
    """
    n = len(pi_energy)
    p = DEFAULT_PARAMS.copy()
    p.update(params)
    z = np.zeros(n)
    z[0] = pi_energy[0] if n > 0 else p['inflation_target']
    for t in range(1, n):
        z[t] = energy_pressure_step(z[t - 1], pi_energy[t], p)
    return z


def food_inflation_equation(data: Dict[str, np.ndarray], params: Dict[str, float],
                            core_infl: np.ndarray) -> np.ndarray:
    """Inflación de alimentos evaluada con `food_step`.

    Motor: presión energética acumulada REZAGADA (Z^e_{t-1}); coste laboral/márgenes
    vía subyacente REZAGADA (π^core_{t-1}). Ambos con un trimestre de retardo, de modo
    que el bloque de precios sigue siendo recursivo (no simultáneo).
    """
    n = len(core_infl)
    p = DEFAULT_PARAMS.copy()
    p.update(params)
    pi_target = p['inflation_target']
    zpress = data.get('energy_pressure', np.full(n, pi_target))
    zpress_lag = lag_array(zpress, 1, fill_val=pi_target)
    core_lag = lag_array(core_infl, 1, fill_val=core_infl[0] if n > 0 else pi_target)

    pi_food = np.zeros(n)
    if 'inflation_food' in data and len(data['inflation_food']) > 0:
        pi_food[0] = data['inflation_food'][0]
    elif n > 0:
        pi_food[0] = core_infl[0]
    for t in range(1, n):
        pi_food[t] = food_step(pi_food[t - 1], zpress_lag[t], core_lag[t], p)
    return pi_food


def aggregate_inflation(pi_services: np.ndarray, pi_goods: np.ndarray,
                        pi_food: np.ndarray, pi_energy: np.ndarray,
                        params: Dict[str, float]) -> Tuple[np.ndarray, np.ndarray]:
    """Agregación vectorizada de la inflación general y subyacente."""
    p = DEFAULT_PARAMS.copy()
    p.update(params)
    w_s = p['weight_services']
    w_g = p['weight_goods']
    w_f = p['weight_food']
    w_e = p['weight_energy']
    total_w = w_s + w_g + w_f + w_e
    w_s, w_g, w_f, w_e = w_s / total_w, w_g / total_w, w_f / total_w, w_e / total_w
    pi_core = (w_s / (w_s + w_g)) * pi_services + (w_g / (w_s + w_g)) * pi_goods
    pi_total = w_s * pi_services + w_g * pi_goods + w_f * pi_food + w_e * pi_energy
    return pi_total, pi_core


def okun_law_equation(data: Dict[str, np.ndarray], params: Dict[str, float],
                      output_gap: np.ndarray) -> np.ndarray:
    """Tasa de paro con histéresis evaluada con `okun_step`."""
    n = len(output_gap)
    p = DEFAULT_PARAMS.copy()
    p.update(params)
    nairu_series = data.get('nairu', np.full(n, p['nairu_default']))
    u_obs = data.get('unemployment_rate', np.zeros(n))

    fitted_u = np.zeros(n)
    fitted_u[0] = u_obs[0] if len(u_obs) > 0 and not np.isnan(u_obs[0]) else nairu_series[0]
    gap_diff = np.diff(output_gap, prepend=output_gap[0])
    for t in range(1, n):
        fitted_u[t] = okun_step(fitted_u[t - 1], nairu_series[t], nairu_series[t - 1], gap_diff[t], p,
                                gap_level=output_gap[t])
    return fitted_u


def employment_dynamics(data: Dict[str, np.ndarray], params: Dict[str, float],
                        output_gap: np.ndarray, fitted_u: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Evolución del empleo en personas y su variación interanual."""
    n = len(output_gap)
    p = DEFAULT_PARAMS.copy()
    p.update(params)
    nairu = data.get('nairu', np.full(n, 12.0))
    emp_pot = data.get('employment_potential', None)

    if emp_pot is not None and not np.isnan(emp_pot).all():
        u_ratio = (1.0 - fitted_u / 100.0) / (1.0 - nairu / 100.0)
        employment_persons = emp_pot * u_ratio
    else:
        beta_e = p['employment_output_elast']
        rho_e = p['employment_persistence']
        gdp_growth = np.diff(output_gap, prepend=output_gap[0]) + 0.5
        emp_growth = np.zeros(n)
        employment_persons = np.zeros(n)
        initial_emp = data.get('employment_persons', np.full(n, 21000.0))[0]
        employment_persons[0] = initial_emp
        for t in range(1, n):
            emp_growth[t] = beta_e * (gdp_growth[t] / 100.0) + rho_e * emp_growth[t - 1]
            employment_persons[t] = employment_persons[t - 1] * (1.0 + emp_growth[t])

    emp_annual_growth = np.zeros(n)
    for t in range(4, n):
        if employment_persons[t - 4] > 0:
            emp_annual_growth[t] = ((employment_persons[t] - employment_persons[t - 4]) / employment_persons[t - 4]) * 100.0
    return employment_persons, emp_annual_growth


def reconstruct_gdp_growth(data: Dict[str, np.ndarray], output_gap: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Reconstruye PIB real en niveles y tasas trimestral/interanual."""
    n = len(output_gap)
    if 'gdp_potential_spain' in data and not np.isnan(data['gdp_potential_spain']).all():
        pot = data['gdp_potential_spain']
    else:
        pot = 100.0 * (1.004 ** np.arange(n))
    gdp_real = pot * (1.0 + output_gap / 100.0)
    gdp_growth_q = np.zeros(n)
    for t in range(1, n):
        if gdp_real[t - 1] > 0:
            gdp_growth_q[t] = ((gdp_real[t] - gdp_real[t - 1]) / gdp_real[t - 1]) * 100.0
    gdp_growth_yoy = np.zeros(n)
    for t in range(4, n):
        if gdp_real[t - 4] > 0:
            gdp_growth_yoy[t] = ((gdp_real[t] - gdp_real[t - 4]) / gdp_real[t - 4]) * 100.0
    return gdp_real, gdp_growth_q, gdp_growth_yoy


def simulate_model(data: Dict[str, np.ndarray], params: Optional[Dict[str, float]] = None,
                   force_structural_is: bool = True) -> Dict[str, np.ndarray]:
    """
    Simulador integral del modelo Semi-DSGE para España (histórico / verosimilitud).
    """
    p = DEFAULT_PARAMS.copy()
    if params:
        p.update(params)

    data_sim = {k: np.array(v, dtype=float) for k, v in data.items()}
    results = {}

    results['interest_rate_spain'] = interest_rate_equation(data_sim, p)
    data_sim['interest_rate_spain'] = results['interest_rate_spain']

    if force_structural_is or 'output_gap_spain' not in data_sim:
        results['output_gap_spain'] = is_curve_spain(data_sim, p)
    else:
        results['output_gap_spain'] = data_sim['output_gap_spain']
    data_sim['output_gap_spain'] = results['output_gap_spain']

    # Cascada de precios (Fase 4): energía → acumulador de presión Z^e → subyacente
    # (servicios y bienes reciben Z^e rezagado) → alimentos (Z^e y subyacente rezagados).
    # El orden importa: Z^e debe existir antes que las Phillips, que lo leen de data_sim.
    results['inflation_energy'] = energy_inflation_equation(data_sim, p)
    results['energy_pressure'] = energy_pressure_equation(results['inflation_energy'], p)
    data_sim['energy_pressure'] = results['energy_pressure']

    results['inflation_services'] = phillips_curve_services(data_sim, p)
    results['inflation_goods'] = phillips_curve_goods(data_sim, p)

    w_s = p['weight_services'] / (p['weight_services'] + p['weight_goods'])
    core_prov = w_s * results['inflation_services'] + (1 - w_s) * results['inflation_goods']
    results['inflation_food'] = food_inflation_equation(data_sim, p, core_prov)

    pi_total, pi_core = aggregate_inflation(
        results['inflation_services'], results['inflation_goods'],
        results['inflation_food'], results['inflation_energy'], p
    )
    results['inflation_total'] = pi_total
    results['inflation_core'] = pi_core

    results['unemployment_rate'] = okun_law_equation(data_sim, p, results['output_gap_spain'])
    emp_persons, emp_yoy = employment_dynamics(data_sim, p, results['output_gap_spain'], results['unemployment_rate'])
    results['employment_persons'] = emp_persons
    results['employment_yoy'] = emp_yoy

    gdp_real, g_q, g_yoy = reconstruct_gdp_growth(data_sim, results['output_gap_spain'])
    results['gdp_real'] = gdp_real
    results['gdp_growth_quarterly'] = g_q
    results['gdp_growth_annual'] = g_yoy

    return results
