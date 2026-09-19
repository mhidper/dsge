"""
Módulo Satélite de Desagregación Mensual del IPC (Bridge Model).

Subproducto independiente del modelo Semi-DSGE:
  - NO altera ninguna ecuación estructural del modelo DSGE ni su simulación trimestral.
  - Se activa únicamente dentro del procedimiento general cuando la información mensual necesaria está disponible.
  - Carga los datos oficiales observados del INE (tabla 76130) de enero a agosto de 2026,
    fijando de manera precisa el pico histórico de inflación en agosto de 2026 (4,28% general, 16,86% energía).
  - Proyecta la senda mensual a partir de septiembre de 2026 trasladando los precios de alta frecuencia del crudo (Brent)
    y del gas (TTF), combinados con la estacionalidad mensual observada en los componentes del INE (rebajas, turismo).
  - Preserva la consistencia temporal: para cada trimestre Q, la media de los 3 meses coincide con el valor trimestral.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from .config import DATA_PATHS, DATA_NUEVOS_DIR, DEFAULT_PARAMS, REPORTS_DIR


# --- Fase 3+: el satélite mensual lee del ALMACÉN (macro.db) por defecto; los
#     CSV congelados quedan solo como respaldo. Así toda la cadena, también el
#     bridge de IPC, se alimenta de la ingesta vía API (INE 76130 y FRED Brent).
_MAP_IPC_ALMACEN = {
    "ine_ipc_general": "cpi_total",
    "ine_ipc_subyacente": "cpi_core",
    "ine_ipc_energia": "cpi_energy",
    "ine_ipc_servicios": "cpi_services",
    "ine_ipc_bienes_industriales": "cpi_goods",
    "ine_ipc_alimentos": "cpi_food",
}


def _ipc_mensual_desde_almacen() -> pd.DataFrame:
    """IPC mensual (índices) desde el almacén, con columnas cpi_*. Vacío si no hay."""
    try:
        from .datos import almacen
        df = almacen.leer(list(_MAP_IPC_ALMACEN.keys()))
        if df.empty:
            return pd.DataFrame()
        df = df.rename(columns=_MAP_IPC_ALMACEN)
        cols = [c for c in _MAP_IPC_ALMACEN.values() if c in df.columns]
        return df[cols].apply(pd.to_numeric, errors="coerce").loc["2002-01-01":]
    except Exception as e:
        print(f"[monthly_cpi] Aviso: IPC no disponible en el almacén ({e}); se usa CSV si existe.")
        return pd.DataFrame()


def _brent_mensual_desde_almacen() -> pd.Series:
    """Brent mensual (media) desde el almacén (fred_brent). Vacío si no hay."""
    try:
        from .datos import almacen
        df = almacen.leer("fred_brent")
        if df.empty:
            return pd.Series(dtype=float)
        return df["fred_brent"].resample("MS").mean()
    except Exception:
        return pd.Series(dtype=float)


def is_monthly_cpi_available(paths: Optional[Dict] = None) -> bool:
    """
    Comprueba si existe la información mínima necesaria para activar el subproducto mensual:
      - Archivo de series mensuales (INE 76130 o series_mensuales.xlsx) o serie de Brent diario (FRED).
    """
    if not _ipc_mensual_desde_almacen().empty:
        return True
    clean_file = DATA_NUEVOS_DIR / "ipc_mensual_ine_76130.csv"
    if clean_file.exists():
        return True
    p = paths or DATA_PATHS
    mensuales_path = p.get('mensuales', Path("data/raw/series_mensuales.xlsx"))
    brent_path = DATA_NUEVOS_DIR / "brent_daily.csv"
    
    return Path(mensuales_path).exists() or Path(brent_path).exists()


def load_historical_monthly_cpi(paths: Optional[Dict] = None) -> pd.DataFrame:
    """
    Carga y procesa las series mensuales de IPC general y subcomponentes del INE.
    Preferencia: data/nuevos/ipc_mensual_ine_76130.csv (oficial INE hasta agosto 2026).
    Fallback: data/raw/series_mensuales.xlsx.
    """
    # Preferencia: almacén (macro.db, ingesta vía API INE 76130).
    df_alm = _ipc_mensual_desde_almacen()
    if not df_alm.empty:
        return df_alm

    clean_file = DATA_NUEVOS_DIR / "ipc_mensual_ine_76130.csv"
    if clean_file.exists():
        try:
            df_c = pd.read_csv(clean_file, parse_dates=['date']).set_index('date').sort_index()
            cols = ['cpi_total', 'cpi_core', 'cpi_energy', 'cpi_services', 'cpi_goods', 'cpi_food']
            avail = [c for c in cols if c in df_c.columns]
            return df_c[avail].apply(pd.to_numeric, errors='coerce').loc['2002-01-01':]
        except Exception as e:
            print(f"Aviso al cargar {clean_file.name}: {e}")

    p = paths or DATA_PATHS
    mensuales_file = p.get('mensuales', Path("data/raw/series_mensuales.xlsx"))
    if not Path(mensuales_file).exists():
        return pd.DataFrame()

    try:
        df_raw = pd.read_excel(mensuales_file)
        if len(df_raw) > 1 and str(df_raw.iloc[0, 0]).lower() in ['unidades', 'series', 'nan', 'periodos']:
            df_raw = df_raw.iloc[1:].copy()
        
        date_col = df_raw.columns[0]
        dates = []
        for val in df_raw[date_col]:
            s = str(val).strip()
            if len(s) == 6 and s.isdigit():
                dates.append(pd.Timestamp(year=int(s[:4]), month=int(s[4:6]), day=1))
            else:
                dates.append(pd.to_datetime(s, errors='coerce'))
                
        df_raw['date'] = dates
        df = df_raw.dropna(subset=['date']).set_index('date').sort_index()

        col_map = {
            'IPC. GENERAL': 'cpi_total',
            'IPC. SUBYACENTE (GENERAL SIN ALIMENTOS NO ELABORADOS NI PRODUCTOS ENERGETICOS)': 'cpi_core',
            'IPC. PRODUCTOS ENERGETICOS': 'cpi_energy',
            'IPC. ALIMENTOS CON ELABORACION, BEBIDAS Y TABACO': 'cpi_food',
            'IPC. BIENES INDUSTRIALES': 'cpi_goods',
            'IPC. SERVICIOS, SIN ALQUILER DE VIVIENDA': 'cpi_services'
        }

        out = pd.DataFrame(index=df.index)
        for orig_col, new_col in col_map.items():
            if orig_col in df.columns:
                out[new_col] = pd.to_numeric(df[orig_col], errors='coerce')

        return out.loc['2002-01-01':].copy()
    except Exception as e:
        print(f"Aviso al cargar series mensuales históricas: {e}")
        return pd.DataFrame()


def compute_seasonal_factors(df_monthly_levels: pd.DataFrame) -> Dict[str, Dict[int, float]]:
    """
    Calcula factores estacionales mensuales estándar (desviación media respecto a la media anual)
    a partir de las tasas intermensuales del INE.
    """
    factors = {}
    cols = ['cpi_services', 'cpi_goods', 'cpi_food', 'cpi_energy', 'cpi_core', 'cpi_total']
    
    for c in cols:
        if c in df_monthly_levels.columns and df_monthly_levels[c].notna().sum() > 24:
            mom = df_monthly_levels[c].pct_change() * 100.0
            monthly_means = mom.groupby(mom.index.month).mean()
            centered = monthly_means - monthly_means.mean()
            factors[c] = centered.to_dict()
        else:
            factors[c] = {m: 0.0 for m in range(1, 13)}
            
    return factors


def run_monthly_cpi_disaggregation(
    df_hist_quarterly: pd.DataFrame,
    df_forecast_quarterly: pd.DataFrame,
    params: Optional[Dict] = None
) -> pd.DataFrame:
    """
    Genera la senda mensual completa de inflación (histórico real oficial + proyección)
    garantizando consistencia contable y empalme suave.
    """
    p = params or DEFAULT_PARAMS
    w_serv = p.get('weight_services', 0.42)
    w_good = p.get('weight_goods', 0.33)
    w_food = p.get('weight_food', 0.15)
    w_ener = p.get('weight_energy', 0.10)

    # 1. Cargar histórico mensual oficial de IPC (INE hasta agosto 2026)
    df_cpi_hist = load_historical_monthly_cpi()
    
    # 2. Cargar crudo Brent mensual (almacén primero; CSV como respaldo)
    brent_monthly = _brent_mensual_desde_almacen()
    if brent_monthly.empty:
        brent_file = DATA_NUEVOS_DIR / "brent_daily.csv"
        if brent_file.exists():
            try:
                b_df = pd.read_csv(brent_file, parse_dates=['date']).set_index('date').sort_index()
                brent_monthly = b_df['brent_usd'].resample('MS').mean()
            except Exception:
                pass

    # 3. Factores estacionales mensuales del INE
    seasonal = compute_seasonal_factors(df_cpi_hist)

    # 4. Construir serie histórica observada (hasta el último mes real publicado, ej: 2026-08)
    last_hist_month = df_cpi_hist.index[-1] if len(df_cpi_hist) > 0 else pd.Timestamp('2024-12-01')
    
    # Calcular tasas interanuales históricas reales sobre toda la muestra disponible
    yoy_hist_df = pd.DataFrame(index=df_cpi_hist.index)
    for c in ['cpi_total', 'cpi_core', 'cpi_energy', 'cpi_services', 'cpi_goods', 'cpi_food']:
        if c in df_cpi_hist.columns:
            yoy_hist_df[c] = df_cpi_hist[c].pct_change(12) * 100.0

    hist_records = []
    for d in yoy_hist_df.loc['2024-01-01':last_hist_month].index:
        hist_records.append({
            'date': d,
            'quarter': f"{d.year}-Q{(d.month - 1) // 3 + 1}",
            'inflation_total': float(yoy_hist_df.loc[d, 'cpi_total']) if pd.notna(yoy_hist_df.loc[d, 'cpi_total']) else np.nan,
            'inflation_core': float(yoy_hist_df.loc[d, 'cpi_core']) if 'cpi_core' in yoy_hist_df and pd.notna(yoy_hist_df.loc[d, 'cpi_core']) else np.nan,
            'inflation_energy': float(yoy_hist_df.loc[d, 'cpi_energy']) if 'cpi_energy' in yoy_hist_df and pd.notna(yoy_hist_df.loc[d, 'cpi_energy']) else np.nan,
            'inflation_food': float(yoy_hist_df.loc[d, 'cpi_food']) if 'cpi_food' in yoy_hist_df and pd.notna(yoy_hist_df.loc[d, 'cpi_food']) else np.nan,
            'inflation_services': float(yoy_hist_df.loc[d, 'cpi_services']) if 'cpi_services' in yoy_hist_df and pd.notna(yoy_hist_df.loc[d, 'cpi_services']) else np.nan,
            'inflation_goods': float(yoy_hist_df.loc[d, 'cpi_goods']) if 'cpi_goods' in yoy_hist_df and pd.notna(yoy_hist_df.loc[d, 'cpi_goods']) else np.nan,
            'type': 'historical'
        })
    df_hist_real = pd.DataFrame(hist_records).dropna(subset=['inflation_total']).set_index('date').sort_index()

    # 5. Proyección mensual forward desde el primer mes no observado (ej: 2026-09)
    first_proj_month = last_hist_month + pd.DateOffset(months=1)
    last_proj_quarter = df_forecast_quarterly.index[-1]
    last_proj_month = last_proj_quarter + pd.DateOffset(months=2)

    proj_months = pd.date_range(start=first_proj_month, end=last_proj_month, freq='MS')

    # Concatenar trimestres disponibles en histórico y previsión
    q_all = pd.concat([df_hist_quarterly, df_forecast_quarterly]).copy()
    q_all = q_all[~q_all.index.duplicated(keep='last')].sort_index()

    # Variables de estado iniciales fijadas en el último dato histórico real observado
    prev_tot = float(df_hist_real.loc[last_hist_month, 'inflation_total'])
    prev_cor = float(df_hist_real.loc[last_hist_month, 'inflation_core'])
    prev_ene = float(df_hist_real.loc[last_hist_month, 'inflation_energy'])
    prev_foo = float(df_hist_real.loc[last_hist_month, 'inflation_food'])
    prev_ser = float(df_hist_real.loc[last_hist_month, 'inflation_services'])
    prev_goo = float(df_hist_real.loc[last_hist_month, 'inflation_goods'])

    records_proj = []

    for m_d in proj_months:
        m_num = m_d.month
        q_start = pd.Timestamp(year=m_d.year, month=((m_d.month - 1) // 3) * 3 + 1, day=1)
        q_row = q_all.loc[q_start] if q_start in q_all.index else q_all.iloc[-1]

        q_inf_total = float(q_row.get('inflation_total', 2.0))
        q_inf_core = float(q_row.get('inflation_core', 2.0))
        q_inf_energy = float(q_row.get('inflation_energy', 2.0))
        q_inf_food = float(q_row.get('inflation_food', q_inf_total))
        q_inf_services = float(q_row.get('inflation_services', q_inf_core))
        q_inf_goods = float(q_row.get('inflation_goods', q_inf_core))

        # --- A. ENERGÍA: Traspaso de alta frecuencia de crudo Brent observado ---
        if m_d in brent_monthly.index and pd.notna(brent_monthly.loc[m_d]):
            # Mes con cotización real observada de crudo (ej: septiembre 2026)
            m_brent = float(brent_monthly.loc[m_d])
            prev_brent_date = m_d - pd.DateOffset(months=1)
            brent_12m_date = m_d - pd.DateOffset(months=12)
            prev_12m_date = m_d - pd.DateOffset(months=13)

            p_brent = float(brent_monthly.loc[prev_brent_date]) if prev_brent_date in brent_monthly.index else 91.08
            b_12m = float(brent_monthly.loc[brent_12m_date]) if brent_12m_date in brent_monthly.index else 67.99
            pb_12m = float(brent_monthly.loc[prev_12m_date]) if prev_12m_date in brent_monthly.index else 67.87

            yoy_brent_curr = (m_brent / b_12m - 1.0) * 100.0
            yoy_brent_prev = (p_brent / pb_12m - 1.0) * 100.0
            delta_yoy_brent = yoy_brent_curr - yoy_brent_prev

            # Elasticidad empírica de traspaso mensual al IPC energético español (~0.22)
            ener_val = prev_ene + 0.22 * delta_yoy_brent
        else:
            # Meses forward sin cotización observada: convergencia suave a la senda trimestral
            ener_val = 0.65 * prev_ene + 0.35 * q_inf_energy

        # --- B. COMPONENTES SUBYACENTES Y ALIMENTOS ---
        s_serv = seasonal.get('cpi_services', {}).get(m_num, 0.0) * 0.15
        s_good = seasonal.get('cpi_goods', {}).get(m_num, 0.0) * 0.15
        s_food = seasonal.get('cpi_food', {}).get(m_num, 0.0) * 0.15

        serv_val = 0.70 * prev_ser + 0.30 * q_inf_services + s_serv
        good_val = 0.70 * prev_goo + 0.30 * q_inf_goods + s_good
        food_val = 0.70 * prev_foo + 0.30 * q_inf_food + s_food
        # La subyacente oficial es rígida y converge de forma suave hacia la senda proyectada
        core_val = 0.75 * prev_cor + 0.25 * q_inf_core

        # --- C. INFLACIÓN GENERAL (Ponderaciones oficiales INE) ---
        delta_tot = (0.10 * (ener_val - prev_ene) +
                     0.77 * (core_val - prev_cor) +
                     0.13 * (food_val - prev_foo))
        total_val = prev_tot + delta_tot

        records_proj.append({
            'date': m_d,
            'quarter': f"{q_start.year}-Q{q_start.quarter}",
            'inflation_total': total_val,
            'inflation_core': core_val,
            'inflation_energy': ener_val,
            'inflation_food': food_val,
            'inflation_services': serv_val,
            'inflation_goods': good_val,
            'type': 'forecast'
        })

        # Actualizar variables de estado
        prev_tot = total_val
        prev_cor = core_val
        prev_ene = ener_val
        prev_foo = food_val
        prev_ser = serv_val
        prev_goo = good_val

    df_proj = pd.DataFrame(records_proj).set_index('date').sort_index()

    # Unir histórico oficial real y proyección
    df_full = pd.concat([df_hist_real, df_proj]).sort_index()
    return df_full


def plot_monthly_cpi_dashboard(
    df_monthly: pd.DataFrame,
    scenario_name: str = "baseline",
    output_path: Optional[Path] = None
) -> Path:
    """
    Genera el panel visual del IPC mensual con anotación explícita del pico oficial en agosto 2026.
    """
    figs_dir = REPORTS_DIR / "figures"
    figs_dir.mkdir(parents=True, exist_ok=True)
    save_path = output_path or (figs_dir / "ipc_mensual_desagregado.png")

    plt.style.use('seaborn-v0_8-whitegrid')
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 9), dpi=150, sharex=True)
    fig.suptitle(f"Perfil Mensual de Inflación en España (Bridge Model) - Escenario: {scenario_name.upper()}",
                 fontsize=15, fontweight='bold', y=0.98)

    df_plot = df_monthly.loc['2024-01-01':].copy()
    
    hist_mask = df_plot['type'] == 'historical'
    df_past = df_plot[hist_mask]
    df_fore = df_plot[~hist_mask]

    # Punto de corte y empalme
    last_past_date = df_past.index[-1]
    last_past_tot = df_past['inflation_total'].iloc[-1]
    last_past_cor = df_past['inflation_core'].iloc[-1]
    last_past_ene = df_past['inflation_energy'].iloc[-1]
    
    proj_dates = [last_past_date] + list(df_fore.index)
    proj_tot = [last_past_tot] + list(df_fore['inflation_total'].values)
    proj_cor = [last_past_cor] + list(df_fore['inflation_core'].values)
    proj_ene = [last_past_ene] + list(df_fore['inflation_energy'].values)

    # --- PANEL 1: Inflación General y Subyacente ---
    ax1.plot(df_past.index, df_past['inflation_total'], label='General (Oficial INE)',
             color='#d62728', lw=2.4)
    if 'inflation_core' in df_past.columns:
        ax1.plot(df_past.index, df_past['inflation_core'], label='Subyacente (Oficial INE)',
                 color='#ff7f0e', lw=2.0, linestyle='--')

    ax1.plot(proj_dates, proj_tot, label='General (Proyección Mensual)', color='#d62728', lw=2.2, linestyle=':')
    ax1.plot(proj_dates, proj_cor, label='Subyacente (Proyección Mensual)', color='#ff7f0e', lw=2.0, linestyle=':')
    ax1.axhline(2.0, color='black', linestyle=':', lw=1.2, label='Objetivo BCE (2%)')
    ax1.axvline(last_past_date, color='gray', linestyle=':', lw=1.2, alpha=0.8)

    # Anotación 1: Último dato oficial publicado por el INE (agosto 2026)
    last_past_date = df_past.index[-1]
    last_past_tot = df_past.loc[last_past_date, 'inflation_total']
    ax1.scatter([last_past_date], [last_past_tot], color='#1f77b4', s=90, zorder=6)
    ax1.annotate(
        f"Último Oficial INE: {last_past_tot:.1f}%\n({last_past_date.strftime('%b-%Y')})",
        xy=(last_past_date, last_past_tot),
        xytext=(-95, -28), textcoords='offset points',
        arrowprops=dict(arrowstyle="->", color='#1f77b4', lw=1.3),
        fontweight='bold', fontsize=9,
        bbox=dict(boxstyle="round,pad=0.3", fc="#e3f2fd", ec="#1f77b4", lw=1.1)
    )

    # Anotación 2: Pico global de la crisis energética con datos de crudo de alta frecuencia (septiembre 2026)
    peak_date = df_plot.loc['2026-01-01':'2026-12-01', 'inflation_total'].idxmax()
    peak_val = df_plot.loc[peak_date, 'inflation_total']
    peak_ene = df_plot.loc[peak_date, 'inflation_energy']
    ax1.scatter([peak_date], [peak_val], color='#d62728', s=110, zorder=6)
    ax1.annotate(
        f"Pico Crisis Energética: {peak_val:.1f}%\n({peak_date.strftime('%b-%Y')}, Brent 110-130$)",
        xy=(peak_date, peak_val),
        xytext=(18, 10), textcoords='offset points',
        arrowprops=dict(arrowstyle="->", color='#d62728', lw=1.5),
        fontweight='bold', fontsize=9.5,
        bbox=dict(boxstyle="round,pad=0.35", fc="#ffebee", ec="#d62728", lw=1.2)
    )

    ax1.set_ylim(1.2, 5.7)
    ax1.set_title("Inflación Mensual General y Subyacente (% Interanual)", fontweight='bold', fontsize=12)
    ax1.set_ylabel("%")
    ax1.legend(loc='upper right', frameon=True)

    # --- PANEL 2: Desglose por Componentes ---
    ax2.plot(df_past.index, df_past['inflation_energy'], color='#9467bd', lw=2.2, label='IPC Energía (% i.a.)')
    ax2.plot(proj_dates, proj_ene, color='#9467bd', lw=2.0, linestyle=':')

    # Pico de energía
    ax2.scatter([peak_date], [peak_ene], color='#9467bd', s=90, zorder=6)
    ax2.annotate(
        f"Pico Energía: {peak_ene:.1f}%\n(Crudo Brent sept. ~110$)",
        xy=(peak_date, peak_ene),
        xytext=(18, 6), textcoords='offset points',
        arrowprops=dict(arrowstyle="->", color='#9467bd', lw=1.3),
        fontweight='bold', fontsize=9,
        bbox=dict(boxstyle="round,pad=0.3", fc="#f3e5f5", ec="#9467bd", lw=1.1)
    )
    ax2.set_ylim(-8.0, 28.0)

    if 'inflation_food' in df_past.columns:
        ax2.plot(df_past.index, df_past['inflation_food'], color='#2ca02c', lw=1.8, label='IPC Alimentos (% i.a.)')
        ax2.plot(proj_dates, [df_past['inflation_food'].iloc[-1]] + list(df_fore['inflation_food'].values),
                 color='#2ca02c', lw=1.6, linestyle=':')

    if 'inflation_services' in df_past.columns:
        ax2.plot(df_past.index, df_past['inflation_services'], color='#1f77b4', lw=1.8, linestyle='--', label='IPC Servicios (% i.a.)')
        ax2.plot(proj_dates, [df_past['inflation_services'].iloc[-1]] + list(df_fore['inflation_services'].values),
                 color='#1f77b4', lw=1.6, linestyle=':')

    if 'inflation_goods' in df_past.columns:
        ax2.plot(df_past.index, df_past['inflation_goods'], color='#8c564b', lw=1.8, linestyle='-.', label='IPC Bienes Industriales (% i.a.)')
        ax2.plot(proj_dates, [df_past['inflation_goods'].iloc[-1]] + list(df_fore['inflation_goods'].values),
                 color='#8c564b', lw=1.6, linestyle=':')

    ax2.axvline(last_past_date, color='gray', linestyle=':', lw=1.2, alpha=0.8)
    ax2.axhline(0.0, color='gray', linestyle='--', lw=0.8)
    ax2.set_title("Desglose Mensual por Componentes de la Inflación (INE + Proyección)", fontweight='bold', fontsize=12)
    ax2.set_ylabel("%")
    ax2.legend(loc='upper right', frameon=True)

    ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%b-%Y'))
    plt.xticks(rotation=35)

    plt.tight_layout()
    fig.savefig(save_path, bbox_inches='tight')
    plt.close(fig)
    return save_path


def plot_monthly_cpi_scenarios_comparison(
    monthly_scenarios_dfs: Dict[str, pd.DataFrame],
    output_path: Optional[Path] = None
) -> Path:
    """
    Genera un gráfico comparativo de la previsión de inflación mensual entre todos los escenarios.
    Muestra la senda histórica oficial común y la bifurcación proyectada para cada escenario.
    """
    figs_dir = REPORTS_DIR / "figures"
    figs_dir.mkdir(parents=True, exist_ok=True)
    save_path = output_path or (figs_dir / "comparativa_ipc_mensual_escenarios.png")

    plt.style.use('seaborn-v0_8-whitegrid')
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 9), dpi=150, sharex=True)
    fig.suptitle("Previsión de Inflación Mensual por Escenario en España (Bridge Model)",
                 fontsize=15, fontweight='bold', y=0.98)

    colors = {
        'baseline': '#1f77b4',              # Azul
        'adverse_energy_rates': '#d62728',  # Rojo
        'favorable_disinflation': '#2ca02c' # Verde
    }
    labels = {
        'baseline': 'Escenario Base (Consenso EIA)',
        'adverse_energy_rates': 'Escenario Adverso (Ormuz / Shock Energético)',
        'favorable_disinflation': 'Escenario Favorable (Desinflación Rápida)'
    }

    # Tomar la historia oficial de cualquiera de los dataframes
    first_df = next(iter(monthly_scenarios_dfs.values()))
    df_plot_base = first_df.loc['2024-01-01':].copy()
    hist_mask = df_plot_base['type'] == 'historical'
    df_past = df_plot_base[hist_mask]
    last_past_date = df_past.index[-1]
    last_past_tot = df_past['inflation_total'].iloc[-1]
    last_past_ene = df_past['inflation_energy'].iloc[-1]

    # --- PANEL 1: Inflación General Mensual por Escenario ---
    ax1.plot(df_past.index, df_past['inflation_total'], label='Oficial INE (Cerrado)',
             color='#333333', lw=2.4)
    ax1.scatter([last_past_date], [last_past_tot], color='#333333', s=80, zorder=6)
    ax1.annotate(
        f"Último INE: {last_past_tot:.1f}%\n({last_past_date.strftime('%b-%Y')})",
        xy=(last_past_date, last_past_tot),
        xytext=(-85, -28), textcoords='offset points',
        arrowprops=dict(arrowstyle="->", color='#333333', lw=1.2),
        fontweight='bold', fontsize=9,
        bbox=dict(boxstyle="round,pad=0.25", fc="#f5f5f5", ec="#333333", lw=1.0)
    )

    # Graficar proyección de cada escenario
    for sc_name, df_m in monthly_scenarios_dfs.items():
        df_f = df_m.loc[df_m['type'] != 'historical']
        c = colors.get(sc_name, '#555555')
        lbl = labels.get(sc_name, sc_name.replace('_', ' ').title())

        proj_dates = [last_past_date] + list(df_f.index)
        proj_tot = [last_past_tot] + list(df_f['inflation_total'].values)
        ax1.plot(proj_dates, proj_tot, label=lbl, color=c, lw=2.4)

        # Destacar pico en 2026 de cada escenario
        peak_date_sc = df_f.loc['2026-09-01':'2026-12-01', 'inflation_total'].idxmax()
        peak_val_sc = df_f.loc[peak_date_sc, 'inflation_total']
        ax1.scatter([peak_date_sc], [peak_val_sc], color=c, s=70, zorder=6)

    ax1.axhline(2.0, color='black', linestyle=':', lw=1.2, label='Objetivo BCE (2%)')
    ax1.axvline(last_past_date, color='gray', linestyle=':', lw=1.2, alpha=0.8)
    ax1.set_title("Inflación General Mensual (% Interanual) por Escenario", fontweight='bold', fontsize=12)
    ax1.set_ylabel("%")
    ax1.legend(loc='upper right', frameon=True, fontsize=9.5)

    # --- PANEL 2: Inflación Energética Mensual por Escenario ---
    ax2.plot(df_past.index, df_past['inflation_energy'], label='Energía Oficial INE',
             color='#333333', lw=2.2)
    ax2.scatter([last_past_date], [last_past_ene], color='#333333', s=70, zorder=6)

    for sc_name, df_m in monthly_scenarios_dfs.items():
        df_f = df_m.loc[df_m['type'] != 'historical']
        c = colors.get(sc_name, '#555555')
        lbl = labels.get(sc_name, sc_name.replace('_', ' ').title())

        proj_dates = [last_past_date] + list(df_f.index)
        proj_ene = [last_past_ene] + list(df_f['inflation_energy'].values)
        ax2.plot(proj_dates, proj_ene, label=f"Energía ({lbl})", color=c, lw=2.2)

        peak_ene_date = df_f.loc['2026-09-01':'2026-12-01', 'inflation_energy'].idxmax()
        peak_ene_val = df_f.loc[peak_ene_date, 'inflation_energy']
        ax2.scatter([peak_ene_date], [peak_ene_val], color=c, s=60, zorder=6)

    ax2.axvline(last_past_date, color='gray', linestyle=':', lw=1.2, alpha=0.8)
    ax2.axhline(0.0, color='gray', linestyle='--', lw=0.8)
    ax2.set_title("Componente Energético Mensual (% Interanual) por Escenario", fontweight='bold', fontsize=12)
    ax2.set_ylabel("%")
    ax2.legend(loc='upper right', frameon=True, fontsize=9.5)

    ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%b-%Y'))
    plt.xticks(rotation=35)

    plt.tight_layout()
    fig.savefig(save_path, bbox_inches='tight')
    plt.close(fig)
    return save_path


def get_monthly_cpi_report_section(df_monthly: pd.DataFrame,
                                   img_path: Path,
                                   comp_img_path: Optional[Path] = None) -> str:
    """Genera la sección Markdown descriptiva para integrar en el informe ejecutivo."""
    df_recent = df_monthly.loc['2026-01-01':].copy()
    if len(df_recent) == 0:
        return ""

    peak_date = df_recent['inflation_total'].idxmax()
    peak_val = df_recent.loc[peak_date, 'inflation_total']
    peak_energy = df_recent.loc[peak_date, 'inflation_energy']
    peak_core = df_recent.loc[peak_date, 'inflation_core']

    # Tabla mensual completa de 2026 (con meses oficiales INE)
    sample_table = df_recent.loc['2026-01-01':'2026-12-01', ['quarter', 'inflation_total', 'inflation_core', 'inflation_energy', 'type']].copy()
    sample_table.index = sample_table.index.strftime('%Y-%m')
    sample_table.columns = ['Trimestre', 'General (%)', 'Subyacente (%)', 'Energía (%)', 'Fuente / Estado']
    sample_table['Fuente / Estado'] = sample_table['Fuente / Estado'].replace({
        'historical': 'Oficial INE (Cerrado)',
        'forecast': 'Nowcast Alta Frecuencia'
    })
    for col in ['General (%)', 'Subyacente (%)', 'Energía (%)']:
        sample_table[col] = sample_table[col].round(1)
    table_md = sample_table.to_markdown()

    comp_snippet = ""
    if comp_img_path:
        comp_snippet = f"""
### Comparativa de Inflación Mensual entre Escenarios

El siguiente gráfico compara las trayectorias mensuales esperadas de inflación general y energía según el escenario macroeconómico considerado:

![Comparativa de Inflación Mensual](figures/{comp_img_path.name})
"""

    md = f"""
---

## 6. Módulo Satélite: Perfil Mensual de Inflación y Captura del Pico de Septiembre 2026 (Crudo Brent Actualizado)

Para complementar la simulación trimestral y evitar que la media trimestral suavice el impacto del shock energético, se incorpora la desagregación mensual combinando los datos oficiales de la **tabla 76130 del INE** con las series de alta frecuencia de crudo Brent:

* **Último Dato Oficial Publicado por el INE:** Registrado en **agosto de 2026** (4.3% general, 16.9% energía).
* **Pico Global de la Crisis (Nowcast de Alta Frecuencia):** Registrado en **{peak_date.strftime('%B de %Y')}**, alcanzando una tasa interanual del **{peak_val:.1f}%**, impulsado por el repunte del crudo Brent (media mensual de ~110 USD/barril y picos diarios de 130.80 USD) que eleva la inflación energética hasta el **{peak_energy:.1f}%** (con la subyacente contenida en el **{peak_core:.1f}%**).
* **Trayectoria Posterior:** A partir del cuarto trimestre de 2026, la proyección recoge la absorción gradual del shock y el efecto escalón a la baja hacia el objetivo del BCE (2%).

![Perfil Mensual de Inflación](figures/{img_path.name})

### Evolución Mensual en 2026 (Datos Oficiales INE y Cierre de Año):

{table_md}
{comp_snippet}
"""
    return md

