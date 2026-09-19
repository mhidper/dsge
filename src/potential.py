"""
Bloque de PIB potencial por función de producción (Cobb-Douglas) con input laboral
explícito, para la economía española.

FASE 3 (potencial endógeno con canal migratorio):
    El potencial se construye a partir de una descomposición de crecimiento
        g(Y*) = (1-α)·g(L*) + contribución_capital + contribución_PTF
    donde el input laboral potencial
        L* = Población en edad de trabajar × Tasa de actividad tendencial × (1 - NAIRU)
    se calcula con los datos reales de mercado laboral (EPA), de modo que la fuerte
    expansión de la población en edad de trabajar por INMIGRACIÓN entra directamente
    en el potencial. Capital (~0.6 pp) y PTF (~0.5 pp) se toman como contribuciones
    tendenciales calibradas al consenso del Banco de España (Documento Ocasional sobre
    la revisión del crecimiento potencial, 2026: potencial 2025-2028 ~2.2%).

    Esto sustituye al potencial estático previo (que crecía ~1.6-1.8% e inflaba la
    brecha hasta +3%). Con esta especificación el potencial ronda 2.2-2.6% y la brecha
    de producto actual resulta pequeña (~+1%), coherente con la posición cíclica.

    La población en edad de trabajar es, además, PROYECTABLE con un supuesto migratorio,
    lo que convierte a la inmigración en una palanca de escenario.

Nota (limitación conocida): el nivel del potencial no incorpora un escalón explícito por
el COVID, por lo que el nivel de la brecha ANTERIOR a 2020 debe leerse con cautela; el
anclaje se fija en la posición cíclica reciente (paro≈NAIRU ⇒ brecha≈0 en 2024-2025),
que es lo relevante para la previsión a medio plazo.
"""

from typing import Dict, Optional, Tuple
import numpy as np
import pandas as pd

from .config import DATA_PATHS, DEFAULT_PARAMS
from .data_pipeline import hp_filter


def _parse_epa_quarter(s) -> Optional[pd.Timestamp]:
    """Convierte '2025T1' en Timestamp de inicio de trimestre."""
    try:
        y, q = str(s).split('T')
        return pd.Timestamp(int(y), (int(q) - 1) * 3 + 1, 1)
    except Exception:
        return None


def load_labour_data(paths: Optional[Dict] = None) -> pd.DataFrame:
    """Carga indicadores de mercado laboral (EPA): paro, población 15+, ocupados, activos."""
    p = paths or DATA_PATHS
    path = p['labor']
    df = pd.read_excel(path)
    date_col = df.columns[0]
    df['date'] = df[date_col].map(_parse_epa_quarter)
    df = df.dropna(subset=['date']).drop(columns=[date_col]).set_index('date').sort_index()
    # Normalizar nombres de columnas por orden esperado: paro, WAP, ocupados, activos
    rename = {}
    for c in df.columns:
        cu = str(c).lower()
        if 'paro' in cu:
            rename[c] = 'u'
        elif 'edad de trabajar' in cu or 'poblac' in cu:
            rename[c] = 'wap'
        elif 'ocupad' in cu:
            rename[c] = 'emp'
        elif 'activ' in cu:
            rename[c] = 'active'
    df = df.rename(columns=rename)
    for c in ['u', 'wap', 'emp', 'active']:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')
    return df[['u', 'wap', 'emp', 'active']]


def _project_wap(wap: pd.Series, target_index: pd.DatetimeIndex,
                 decel: float) -> pd.Series:
    """
    Prolonga la población en edad de trabajar más allá del último dato observado con
    desaceleración gradual del ritmo migratorio: cada trimestre el crecimiento se
    multiplica por `decel` (<1), acercándolo a la media histórica.
    """
    wap = wap.reindex(target_index)
    last = wap.last_valid_index()
    if last is None:
        return wap.ffill().bfill()
    prev_year = last - pd.DateOffset(years=1)
    if prev_year in wap.index and pd.notna(wap.loc[prev_year]) and wap.loc[prev_year] > 0:
        g_ann = wap.loc[last] / wap.loc[prev_year] - 1.0
    else:
        g_ann = 0.008
    gq = (1.0 + g_ann) ** 0.25 - 1.0
    w = wap.loc[last]
    for d in [x for x in target_index if x > last]:
        gq *= decel
        w *= (1.0 + gq)
        wap.loc[d] = w
    return wap


def build_labour_potential(gdp_real: pd.Series, params: Optional[Dict] = None,
                           labour_df: Optional[pd.DataFrame] = None,
                           horizon_index: Optional[pd.DatetimeIndex] = None) -> Dict:
    """
    Construye el input laboral potencial L* y el crecimiento potencial anual sobre el
    índice de `gdp_real` (ampliable con `horizon_index` para proyección).

    Returns dict con Series: 'Lstar', 'partic_trend', 'nairu_trend', 'wap',
    'potential_growth_ann', y el estado terminal para proyección.
    """
    p = DEFAULT_PARAMS.copy()
    if params:
        p.update(params)
    alpha = p['pf_alpha']
    cap = p['capital_contrib_annual']
    tfp = p['tfp_contrib_annual']
    decel = p['migration_decel']

    if labour_df is None:
        labour_df = load_labour_data()

    # Índice de trabajo: histórico de gdp_real más, si procede, el horizonte futuro
    base_index = gdp_real.index
    full_index = base_index if horizon_index is None else base_index.union(horizon_index)

    wap = _project_wap(labour_df['wap'], full_index, decel)
    active = labour_df['active'].reindex(full_index).interpolate().ffill().bfill()
    u = labour_df['u'].reindex(full_index).interpolate().ffill().bfill()

    partic = (active / wap)
    partic_tr, _ = hp_filter(partic.dropna(), p['participation_hp_lambda'])
    partic_tr = partic_tr.reindex(full_index).ffill().bfill()
    nairu_tr, _ = hp_filter(u.dropna(), p['nairu_hp_lambda'])
    nairu_tr = nairu_tr.reindex(full_index).ffill().bfill()

    Lstar = wap * partic_tr * (1.0 - nairu_tr / 100.0)
    g_lstar_ann = (Lstar / Lstar.shift(4) - 1.0) * 100.0
    potential_growth_ann = (1.0 - alpha) * g_lstar_ann + cap + tfp

    return {
        'Lstar': Lstar,
        'partic_trend': partic_tr,
        'nairu_trend': nairu_tr,
        'wap': wap,
        'potential_growth_ann': potential_growth_ann,
        'full_index': full_index,
    }


def compute_historical_potential(gdp_real: pd.Series, params: Optional[Dict] = None,
                                 labour_df: Optional[pd.DataFrame] = None) -> Dict:
    """
    Calcula el nivel de PIB potencial y la brecha de producto históricos por función
    de producción, anclando el nivel a la posición cíclica reciente (paro≈NAIRU ⇒
    brecha≈0 en la ventana de anclaje).

    Returns dict con Series 'gdp_potential', 'output_gap', 'potential_growth_ann' y
    el estado terminal ('last_potential', 'last_wap', 'last_partic', 'last_nairu',
    'last_wap_growth_ann') para proyectar el potencial en la previsión.
    """
    p = DEFAULT_PARAMS.copy()
    if params:
        p.update(params)

    lab = build_labour_potential(gdp_real, p, labour_df)
    idx = gdp_real.index
    gy = np.log(gdp_real.astype(float))

    pg_ann = lab['potential_growth_ann'].reindex(idx)
    pg_q = ((1.0 + pg_ann / 100.0) ** 0.25 - 1.0).fillna(0.006)

    # Nivel potencial acumulando el crecimiento potencial desde el primer dato
    log_pot = np.zeros(len(idx))
    log_pot[0] = float(gy.iloc[0]) if np.isfinite(gy.iloc[0]) else 0.0
    pg_vals = pg_q.values
    for i in range(1, len(idx)):
        log_pot[i] = log_pot[i - 1] + pg_vals[i]
    log_pot = pd.Series(log_pot, index=idx)

    # Anclaje cíclico: brecha media ≈ 0 en la ventana donde paro≈NAIRU
    aw0, aw1 = p['gap_anchor_window']
    raw_gap = gy - log_pot
    anchor = raw_gap.loc[aw0:aw1].mean()
    if not np.isfinite(anchor):
        anchor = raw_gap.mean()
    log_pot_anchored = log_pot + anchor

    gdp_potential = np.exp(log_pot_anchored)
    output_gap = (gy - log_pot_anchored) * 100.0

    # Estado terminal para la proyección
    last = idx[-1]
    wap = lab['wap']
    prev_year = last - pd.DateOffset(years=1)
    last_wap_g = (wap.loc[last] / wap.loc[prev_year] - 1.0) if prev_year in wap.index and wap.loc[prev_year] > 0 else 0.008

    return {
        'gdp_potential': gdp_potential,
        'output_gap': output_gap,
        'potential_growth_ann': pg_ann,
        'Lstar': lab['Lstar'],  # insumo laboral potencial (empleo potencial, miles)
        'last_potential': float(gdp_potential.iloc[-1]),
        'last_wap': float(wap.loc[last]),
        'last_partic': float(lab['partic_trend'].loc[last]),
        'last_nairu': float(lab['nairu_trend'].loc[last]),
        'last_wap_growth_ann': float(last_wap_g),
        'last_Lstar': float(lab['Lstar'].loc[last]),
    }


def project_potential_path(state: Dict, horizon: int, params: Optional[Dict] = None,
                           migration_wap_growth: Optional[float] = None) -> Dict[str, np.ndarray]:
    """
    Proyecta el PIB potencial y su crecimiento sobre el horizonte, prolongando la
    población en edad de trabajar con desaceleración migratoria gradual. Mantiene la
    tasa de actividad tendencial y la NAIRU en su último valor.

    Args:
        state: estado terminal de `compute_historical_potential`.
        migration_wap_growth: crecimiento anual de la WAP al que converge la senda
            (palanca migratoria de escenario). Si None, decae desde el ritmo reciente.

    Returns dict con arrays 'gdp_potential' y 'potential_growth_ann' de longitud `horizon`.
    """
    p = DEFAULT_PARAMS.copy()
    if params:
        p.update(params)
    alpha = p['pf_alpha']
    cap = p['capital_contrib_annual']
    tfp = p['tfp_contrib_annual']
    decel = p['migration_decel']

    partic = state['last_partic']
    nairu = state['last_nairu']
    wap = state['last_wap']
    # Serie de L* con 4 rezagos para el interanual: reconstruimos hacia atrás con el ritmo reciente
    gq = (1.0 + state['last_wap_growth_ann']) ** 0.25 - 1.0
    target_gq = None if migration_wap_growth is None else (1.0 + migration_wap_growth) ** 0.25 - 1.0

    # Historia corta de L* (últimos 4 trimestres aproximados con el ritmo reciente)
    Lstar_hist = [state['last_Lstar'] / (1.0 + gq) ** (4 - k) for k in range(4)]  # t-3..t
    Lstar_hist.append(state['last_Lstar'])  # asegurar t
    Lstar = list(Lstar_hist)

    pot = state['last_potential']
    out_pot = np.zeros(horizon)
    out_g = np.zeros(horizon)
    w = wap
    for h in range(horizon):
        gq *= decel
        if target_gq is not None:
            gq = 0.5 * gq + 0.5 * target_gq  # converge hacia el supuesto de escenario
        w *= (1.0 + gq)
        L_new = w * partic * (1.0 - nairu / 100.0)
        Lstar.append(L_new)
        g_lstar_ann = (Lstar[-1] / Lstar[-5] - 1.0) * 100.0
        pg_ann = (1.0 - alpha) * g_lstar_ann + cap + tfp
        pg_q = (1.0 + pg_ann / 100.0) ** 0.25 - 1.0
        pot *= (1.0 + pg_q)
        out_pot[h] = pot
        out_g[h] = pg_ann
    return {'gdp_potential': out_pot, 'potential_growth_ann': out_g}
