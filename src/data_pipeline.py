"""
Pipeline de datos: Carga, homogenización trimestral, cálculo de brechas y consolidación.
"""

from pathlib import Path
from typing import Dict, Optional, Tuple
import numpy as np
import pandas as pd
from .config import DATA_PATHS, DATA_NUEVOS_DIR, DEFAULT_PARAMS


def build_policy_overlay(index, measures: Optional[list] = None) -> pd.Series:
    """Serie de superposición de las medidas energéticas conmutables sobre el IPC energético.

    Para cada medida con ventana [start, end), construye la dummy D_t (1 mientras rige)
    y devuelve Σ_m θ_m · ΔD_{m,t}: el efecto de nivel entra en el trimestre de activación
    (signo de θ) y el rebote opuesto en el de retirada. Los trimestres interiores no
    aportan (ΔD=0). Así una medida solo mueve la inflación al encenderse y al apagarse.

    Args:
        index: DatetimeIndex trimestral sobre el que evaluar el overlay.
        measures: lista de dicts como POLICY_MEASURES; si None, usa la de config.
    """
    from .config import POLICY_MEASURES
    ms = POLICY_MEASURES if measures is None else measures
    idx = pd.DatetimeIndex(index)
    overlay = pd.Series(0.0, index=idx)
    if len(idx) == 0:
        return overlay
    for m in ms:
        start = pd.Timestamp(m['start'])
        end = pd.Timestamp(m['end']) if m.get('end') else None
        active = (idx >= start) if end is None else ((idx >= start) & (idx < end))
        D = pd.Series(0.0, index=idx)
        D[active] = 1.0
        dD = D.diff().fillna(0.0)   # ningún caso arranca con la medida ya activa
        overlay = overlay + float(m['theta_pp']) * dD
    return overlay


def hp_filter(series: pd.Series, lamb: float = 1600.0) -> Tuple[pd.Series, pd.Series]:
    """
    Filtro Hodrick-Prescott para descomponer una serie temporal en tendencia y ciclo.
    
    Args:
        series: Serie temporal limpia (sin NaN).
        lamb: Parámetro de suavizado (1600 para frecuencia trimestral).
        
    Returns:
        (tendencia, ciclo)
    """
    clean_series = series.dropna()
    t_len = len(clean_series)
    if t_len < 4:
        return series.copy(), pd.Series(0.0, index=series.index)

    # Matriz de segundas diferencias K ((T-2) x T)
    k_mat = np.zeros((t_len - 2, t_len))
    for i in range(t_len - 2):
        k_mat[i, i] = 1.0
        k_mat[i, i + 1] = -2.0
        k_mat[i, i + 2] = 1.0

    # (I + lamb * K'K) * tau = y
    i_mat = np.eye(t_len)
    a_mat = i_mat + lamb * (k_mat.T @ k_mat)

    try:
        trend_vals = np.linalg.solve(a_mat, clean_series.values)
        trend = pd.Series(trend_vals, index=clean_series.index)
        cycle = clean_series - trend

        # Reindexar a la serie completa si tenía NaNs
        trend_full = pd.Series(np.nan, index=series.index)
        cycle_full = pd.Series(np.nan, index=series.index)
        trend_full.loc[trend.index] = trend
        cycle_full.loc[cycle.index] = cycle
        return trend_full, cycle_full
    except np.linalg.LinAlgError:
        trend_full = series.rolling(window=8, min_periods=1, center=True).mean()
        cycle_full = series - trend_full
        return trend_full, cycle_full


def parse_quarterly_index(idx_val) -> Optional[pd.Timestamp]:
    """Convierte representaciones como '20231', 20231, '2023-Q1' a Timestamp de inicio de trimestre."""
    s = str(idx_val).strip()
    if not s or s.lower() == 'nan':
        return None
    try:
        # Formato '20231' -> año 2023, trimestre 1
        if len(s) == 5 and s.isdigit():
            year = int(s[:4])
            quarter = int(s[4])
            month = (quarter - 1) * 3 + 1
            return pd.Timestamp(year=year, month=month, day=1)
        # Formato mensual '202301'
        if len(s) == 6 and s.isdigit():
            year = int(s[:4])
            month = int(s[4:6])
            return pd.Timestamp(year=year, month=month, day=1)
        # Formato fecha estándar
        return pd.to_datetime(s)
    except Exception:
        return None


def _parse_pib_cvec(file_path) -> pd.DataFrame:
    """
    Parsea el CSV de INE con el índice CVEC (sep=';', notación '2025T1', coma decimal).
    Devuelve DataFrame con columna 'cvec_index' e índice DatetimeIndex trimestral.
    """
    df = pd.read_csv(file_path, sep=';', header=0, encoding='latin-1')
    period_col = df.columns[4]   # 5ª columna: código de periodo
    value_col = df.columns[5]    # 6ª columna: valor del índice
    df = df[[period_col, value_col]].copy()
    df.columns = ['period', 'raw_value']

    def _qstr_to_ts(s: str) -> Optional[pd.Timestamp]:
        s = str(s).strip()
        try:                        # formato '2025T1'
            year, q = int(s[:4]), int(s[5])
            return pd.Timestamp(year=year, month=(q - 1) * 3 + 1, day=1)
        except Exception:
            return None

    df['date'] = df['period'].apply(_qstr_to_ts)
    df['cvec_index'] = pd.to_numeric(
        df['raw_value'].astype(str).str.replace(',', '.', regex=False), errors='coerce'
    )
    df = df.dropna(subset=['date', 'cvec_index']).set_index('date').sort_index()
    return df[['cvec_index']]


def _scale_cvec_to_millions(df_cvec: pd.DataFrame, update_file: Path) -> pd.DataFrame:
    """
    Convierte el índice CVEC (base 2015 = 100) a millones de EUR.

    Estrategia: calcula el factor de escala como la media de
    gdp_real_spain / cvec_index en el período de solapamiento con
    actualizacion_oficial_2025_2026.csv.  Si el solapamiento no existe o
    el archivo no está disponible, usa el fallback de referencia
    (2015-avg quarterly GDP ≈ 259 110 M€ → 2591.1 M€/punto de índice).
    """
    FALLBACK_SCALE = 2591.1   # M€ por punto de índice CVEC, derivado de INE 2015
    scale = FALLBACK_SCALE
    try:
        if update_file.exists():
            df_up = pd.read_csv(update_file)
            df_up['date'] = pd.to_datetime(df_up['date'])
            df_up = df_up.set_index('date').sort_index()
            if 'gdp_real_spain' in df_up.columns:
                overlap = df_cvec.index.intersection(df_up.index)
                if len(overlap) >= 2:
                    ratios = (df_up.loc[overlap, 'gdp_real_spain']
                              / df_cvec.loc[overlap, 'cvec_index'])
                    scale = float(ratios.mean())
    except Exception:
        pass
    out = df_cvec.copy()
    out['gdp_real_spain'] = out['cvec_index'] * scale
    return out[['gdp_real_spain']]


def load_clean_sources(paths: Optional[Dict] = None) -> Dict[str, pd.DataFrame]:
    """
    Carga las fuentes CSV limpias de data/nuevos/:
      - 'epa'     : empleo_epa_2002_2026T2.csv  (pop_16plus, active, employed, unemployment_rate)
      - 'pib_cvec': pib_real_cvec_indice.csv     (gdp_real_spain en M€, 1995T1-2026T2)

    Son fuentes preferentes sobre los xlsx de data/raw/ porque tienen
    cabeceras estándar y no requieren detección heurística de columnas.
    El fallback a xlsx se mantiene en build_consolidated_dataset().
    """
    from .config import SANDBOX_DIR
    p = paths or DATA_PATHS
    result: Dict[str, pd.DataFrame] = {}

    # --- EPA ---
    epa_path = p.get('epa', DATA_NUEVOS_DIR / "empleo_epa_2002_2026T2.csv")
    if Path(epa_path).exists():
        df_epa = pd.read_csv(epa_path)
        df_epa['date'] = pd.to_datetime(df_epa['date'])
        df_epa = df_epa.set_index('date').sort_index()
        result['epa'] = df_epa

    # --- PIB CVEC ---
    cvec_path = p.get('pib_cvec', DATA_NUEVOS_DIR / "pib_real_cvec_indice.csv")
    if Path(cvec_path).exists():
        df_cvec = _parse_pib_cvec(cvec_path)
        update_file = SANDBOX_DIR / "data" / "actualizacion_oficial_2025_2026.csv"
        result['pib_cvec'] = _scale_cvec_to_millions(df_cvec, update_file)

    return result


def load_nowcast_gdp(
    nowcast_dir: Path,
    last_official_date: pd.Timestamp,
    last_official_gdp: float,
) -> pd.DataFrame:
    """
    Lee las estimaciones de nowcasting del PIB desde el tracker hermano
    (crisistrackerv2) y devuelve un DataFrame con columna 'gdp_real_spain'
    para los trimestres aún sin dato INE.

    Fuentes (ambas en nowcast_dir):
      - t6.csv: historial de estimaciones del trimestre corriente;
                fila más reciente → Trimestre en curso, QoQ más actualizado.
      - t3.csv: fila "siguiente trimestre, semana en curso" → QoQ T+1.

    Solo devuelve filas con fecha > last_official_date.
    Cuando el INE publique el dato oficial, basta actualizar
    actualizacion_oficial_2025_2026.csv: la sección 6 lo sobrescribirá.

    Args:
        nowcast_dir        : ruta a crisistrackerv2/data/processed/tables/
        last_official_date : último trimestre con dato INE (p. ej. 2026-04-01)
        last_official_gdp  : PIB real en M€ de ese trimestre

    Returns:
        DataFrame (índice DatetimeIndex QS, columna gdp_real_spain),
        vacío si el directorio no existe o no hay trimestres nuevos.
    """
    if not nowcast_dir.exists():
        return pd.DataFrame()

    def _qstr_to_ts(s: str) -> Optional[pd.Timestamp]:
        """'2026Q3' → Timestamp(2026-07-01)"""
        try:
            s = str(s).strip()
            year, q = int(s[:4]), int(s[5])
            return pd.Timestamp(year=year, month=(q - 1) * 3 + 1, day=1)
        except Exception:
            return None

    try:
        # --- Trimestre corriente (t6.csv) ---
        t6_path = nowcast_dir / "t6.csv"
        current_qtr_date: Optional[pd.Timestamp] = None
        current_qoq: float = 0.0
        if t6_path.exists():
            df_t6 = pd.read_csv(t6_path)
            # Columnas: fecha_recogida, trimestre (ej. "2026Q3"), point_estimate
            last_row = df_t6.iloc[-1]
            current_qtr_date = _qstr_to_ts(str(last_row.iloc[1]))
            current_qoq = float(last_row.iloc[2])

        if current_qtr_date is None:
            return pd.DataFrame()

        # --- Trimestre siguiente (t3.csv) ---
        t3_path = nowcast_dir / "t3.csv"
        next_qoq: float = 0.0
        if t3_path.exists():
            df_t3 = pd.read_csv(t3_path)
            # Fila: "Evolución del PIB en el trimestre siguiente- semana en curso"
            # t3.csv usa "semana actual" para el siguiente trimestre (≠ "semana en curso")
            mask = (
                df_t3.iloc[:, 0].str.contains('siguiente', case=False, na=False)
                & df_t3.iloc[:, 0].str.contains('actual', case=False, na=False)
            )
            if mask.any():
                next_qoq = float(df_t3.loc[mask, df_t3.columns[1]].iloc[0])

        next_qtr_date = current_qtr_date + pd.DateOffset(months=3)

        # Construir niveles de PIB desde el último dato oficial disponible
        rows: dict = {}
        if current_qtr_date > last_official_date:
            gdp_current = last_official_gdp * (1.0 + current_qoq / 100.0)
            rows[current_qtr_date] = gdp_current
            if next_qtr_date > last_official_date:
                rows[next_qtr_date] = gdp_current * (1.0 + next_qoq / 100.0)
        elif current_qtr_date == last_official_date:
            # El trimestre corriente ya está cerrado en los datos oficiales/incorporados;
            # solo se añade el siguiente trimestre con su QoQ correspondiente.
            if next_qtr_date > last_official_date:
                rows[next_qtr_date] = last_official_gdp * (1.0 + next_qoq / 100.0)

        if not rows:
            return pd.DataFrame()

        idx = pd.DatetimeIndex(sorted(rows.keys()))
        return pd.DataFrame({'gdp_real_spain': [rows[d] for d in idx]}, index=idx)

    except Exception as e:
        print(f"Aviso nowcasting GDP: {e}")
        return pd.DataFrame()


def load_raw_datasets(paths: Optional[Dict] = None) -> Dict[str, pd.DataFrame]:
    """Carga los archivos primarios desde data/raw."""
    p = paths or DATA_PATHS
    datasets = {}

    # 1. Crudo Brent
    #    Preferencia: brent_daily.csv (FRED, actualizado por refresh_energy_data,
    #    extendido hasta hoy). Fallback: crudo.csv de data/raw (congelado en 2025Q2).
    from .refresh_energy_data import BRENT_CSV
    crudo_src = BRENT_CSV if BRENT_CSV.exists() else p['crudo']
    if crudo_src.exists():
        df_crudo = pd.read_csv(crudo_src)
        date_col = 'date' if 'date' in df_crudo.columns else (
            'Fecha' if 'Fecha' in df_crudo.columns else df_crudo.columns[0])
        # columna de valor: 'brent_usd' si viene del refresco, si no la primera no-fecha
        val_col = 'brent_usd' if 'brent_usd' in df_crudo.columns else \
            [c for c in df_crudo.columns if c not in (date_col, 'source', 'fetched_utc')][0]
        df_crudo[date_col] = pd.to_datetime(df_crudo[date_col], errors='coerce')
        df_crudo[val_col] = pd.to_numeric(df_crudo[val_col], errors='coerce')
        df_crudo = df_crudo.dropna(subset=[date_col]).set_index(date_col).sort_index()
        df_crudo_q = df_crudo[[val_col]].resample('QS').mean()
        df_crudo_q.columns = ['oil_price_brent']
        datasets['crudo'] = df_crudo_q

    # 2. Series Trimestrales
    if p['trimestrales'].exists():
        df_trim = pd.read_excel(p['trimestrales'])
        if len(df_trim) > 1 and str(df_trim.iloc[0, 0]).lower() in ['unidades', 'series', 'nan']:
            df_trim = df_trim.iloc[1:].reset_index(drop=True)
        # Parsear fecha en primera columna
        date_col = df_trim.columns[0]
        dates = [parse_quarterly_index(x) for x in df_trim[date_col]]
        df_trim['date'] = dates
        df_trim = df_trim.dropna(subset=['date']).set_index('date').sort_index()
        # Convertir a numérico
        for col in df_trim.columns:
            df_trim[col] = pd.to_numeric(df_trim[col], errors='coerce')
        datasets['trimestrales'] = df_trim

    # 3. Series Mensuales
    if p['mensuales'].exists():
        df_mens = pd.read_excel(p['mensuales'])
        if len(df_mens) > 1 and str(df_mens.iloc[0, 0]).lower() in ['unidades', 'series', 'nan']:
            df_mens = df_mens.iloc[1:].reset_index(drop=True)
        date_col = df_mens.columns[0]
        dates = [parse_quarterly_index(x) for x in df_mens[date_col]]
        df_mens['date'] = dates
        df_mens = df_mens.dropna(subset=['date']).set_index('date').sort_index()
        for col in df_mens.columns:
            df_mens[col] = pd.to_numeric(df_mens[col], errors='coerce')
        # Resample trimestral promediando meses
        df_mens_q = df_mens.resample('QS').mean()
        datasets['mensuales'] = df_mens_q

    # 4. Estimación PIB Potencial y NAIRU
    if p['potencial'].exists():
        try:
            df_pot = pd.read_csv(p['potencial'], sep=';')
            if 'date' not in df_pot.columns:
                df_pot = pd.read_csv(p['potencial'])
            df_pot['date'] = pd.to_datetime(df_pot['date'])
            df_pot = df_pot.set_index('date').sort_index()
            for col in df_pot.columns:
                df_pot[col] = pd.to_numeric(df_pot[col], errors='coerce')
            datasets['potencial'] = df_pot
        except Exception as e:
            print(f"Aviso al cargar pib_potencial_espana.csv: {e}")

    # 5. Tipo de cambio diario
    if p['diarias'].exists():
        try:
            df_diarias = pd.read_excel(p['diarias'])
            if len(df_diarias) > 1:
                df_diarias = df_diarias.iloc[1:].reset_index(drop=True)
            d_col = df_diarias.columns[0]
            v_col = df_diarias.columns[1]
            df_diarias[d_col] = pd.to_datetime(df_diarias[d_col], errors='coerce')
            df_diarias[v_col] = pd.to_numeric(df_diarias[v_col], errors='coerce')
            df_diarias = df_diarias.dropna(subset=[d_col]).set_index(d_col).sort_index()
            df_fx_q = df_diarias[[v_col]].resample('QS').mean()
            df_fx_q.columns = ['usd_eur_rate']
            datasets['diarias'] = df_fx_q
        except Exception as e:
            print(f"Aviso al cargar series_diarias.xlsx: {e}")

    return datasets


def build_consolidated_dataset(paths: Optional[Dict] = None,
                               auto_refresh: bool = True) -> pd.DataFrame:
    """
    Construye el dataset macroeconómico trimestral consolidado para España
    con todas las variables endógenas y exógenas normalizadas.

    Jerarquía de fuentes:
      1. CSVs limpios de data/nuevos/ (EPA y PIB CVEC) — fuentes preferentes.
      2. xlsx de data/raw/ (trimestrales, mensuales, potencial) — fallback.
      3. actualizacion_oficial_2025_2026.csv — siempre sobreescribe el
         período 2025T1-2026T2 con los valores oficiales más recientes.

    Args:
        auto_refresh: si True (por defecto), refresca best-effort las series de
            energía (Brent y gas) desde FRED antes de construir el dataset. Con
            caché por antigüedad, solo descarga si el CSV local está obsoleto; sin
            red (p. ej. sandbox) conserva lo cacheado sin fallar. Poner False para
            reproducibilidad estricta o entornos offline.
    """
    if auto_refresh:
        try:
            from .refresh_energy_data import refresh_energy_data
            refresh_energy_data(force=False)
        except Exception as e:
            print(f"Aviso: refresco de energía omitido ({e}).")

    raw = load_raw_datasets(paths)
    clean = load_clean_sources(paths)          # ← fuentes preferentes

    df_trim = raw.get('trimestrales', pd.DataFrame())
    df_mens = raw.get('mensuales', pd.DataFrame())
    df_pot = raw.get('potencial', pd.DataFrame())
    df_crudo = raw.get('crudo', pd.DataFrame())
    df_fx = raw.get('diarias', pd.DataFrame())
    df_epa = clean.get('epa', pd.DataFrame())          # EPA 2002-presente
    df_pib_cvec = clean.get('pib_cvec', pd.DataFrame())  # PIB CVEC 1995-presente

    # Índice maestro trimestral (acotado a 1995 en adelante para consistencia UEM)
    start_date = pd.Timestamp('1995-01-01')
    candidate_ends = [df.index.max() for df in [df_trim, df_mens, df_pot, df_pib_cvec, df_epa]
                      if len(df) > 0]
    end_date = max(candidate_ends)
    master_index = pd.date_range(start=start_date, end=end_date, freq='QS')
    df = pd.DataFrame(index=master_index)

    # -------------------------------------------------------------
    # 1. PIB Real y Potencial de España
    #    Preferencia: CSV CVEC (cabeceras estándar, escala M€ calibrada).
    #    Fallback: xlsx trimestrales → potencial.csv.
    # -------------------------------------------------------------
    if len(df_pib_cvec) > 0 and 'gdp_real_spain' in df_pib_cvec.columns:
        # Fuente primaria: CVEC INE escalado a millones EUR
        df['gdp_real_spain'] = df_pib_cvec['gdp_real_spain'].reindex(master_index)
    else:
        # Fallback: xlsx trimestrales
        pib_spain_col = None
        for col in df_trim.columns:
            if 'PIB. VOLUMEN' in col.upper() or ('PIB' in col.upper() and 'ESP' in col.upper()):
                pib_spain_col = col
                break
        if pib_spain_col:
            df['gdp_real_spain'] = df_trim[pib_spain_col].reindex(master_index)

    # Potencial y brecha desde archivo especializado si está disponible
    if len(df_pot) > 0:
        if 'gdp_potential' in df_pot.columns:
            df['gdp_potential_spain'] = df_pot['gdp_potential'].reindex(master_index)
        if 'output_gap' in df_pot.columns:
            gap_raw = df_pot['output_gap'].reindex(master_index)
            # Escala porcentaje (ej: 1.5 en lugar de 0.015)
            if gap_raw.dropna().abs().mean() < 0.20:
                gap_raw = gap_raw * 100.0
            df['output_gap_spain'] = gap_raw
        if 'gdp_real' in df_pot.columns and df_pot['gdp_real'].count() > 10:
            df['gdp_real_spain'] = df_pot['gdp_real'].reindex(master_index)
            # Si el último trimestre no tenía gdp_real pero sí potencial y brecha, reconstruir
            mask_fill = df['gdp_real_spain'].isna() & df['gdp_potential_spain'].notna() & df['output_gap_spain'].notna()
            df.loc[mask_fill, 'gdp_real_spain'] = df.loc[mask_fill, 'gdp_potential_spain'] * (1.0 + df.loc[mask_fill, 'output_gap_spain'] / 100.0)
        if 'nairu' in df_pot.columns:
            df['nairu'] = df_pot['nairu'].reindex(master_index)
        if 'employment_potential' in df_pot.columns:
            df['employment_potential'] = df_pot['employment_potential'].reindex(master_index)

    # Si falta brecha o potencial, calcular mediante filtro HP sobre PIB real
    if 'output_gap_spain' not in df.columns or df['output_gap_spain'].count() < 10:
        if 'gdp_real_spain' in df.columns and df['gdp_real_spain'].count() > 10:
            log_pib = np.log(df['gdp_real_spain'].dropna())
            trend_log, cycle_log = hp_filter(log_pib, lamb=1600)
            df['output_gap_spain'] = cycle_log * 100.0
            df['gdp_potential_spain'] = np.exp(trend_log)

    # -------------------------------------------------------------
    # 2. Mercado Laboral (Tasa de Paro y Empleo)
    #    Preferencia: CSV EPA (columnas estándar, 2002T1-presente).
    #    Fallback: xlsx trimestrales.
    # -------------------------------------------------------------
    if len(df_epa) > 0 and 'unemployment_rate' in df_epa.columns:
        # Fuente primaria: EPA limpia
        df['unemployment_rate'] = df_epa['unemployment_rate'].reindex(master_index)
        if 'employed' in df_epa.columns:
            df['employment_persons'] = df_epa['employed'].reindex(master_index)
    else:
        # Fallback: xlsx trimestrales
        paro_col = None
        for col in df_trim.columns:
            if 'TASA DE PARO' in col.upper() or 'DESEMPLEO' in col.upper():
                paro_col = col
                break
        if paro_col:
            df['unemployment_rate'] = df_trim[paro_col].reindex(master_index)
        else:
            df['unemployment_rate'] = DEFAULT_PARAMS['nairu_default']

    if 'nairu' not in df.columns or df['nairu'].isna().all():
        # NAIRU suavizado como tendencia HP de la tasa de paro
        trend_u, _ = hp_filter(df['unemployment_rate'].dropna(), lamb=6400)
        df['nairu'] = trend_u.reindex(master_index).fillna(DEFAULT_PARAMS['nairu_default'])

    # Ocupados / Empleo
    if 'employment_potential' in df.columns and df['employment_potential'].count() > 10:
        # Reconstruir ocupados a partir del potencial y la tasa de paro
        df['employment_persons'] = df['employment_potential'] * (1 - df['unemployment_rate'] / 100.0) / (1 - df['nairu'] / 100.0)
    else:
        # Proxy normalizado a base 100 en 2015
        df['employment_persons'] = 100.0 * (1 - (df['unemployment_rate'] - df['nairu']) / 100.0)

    # -------------------------------------------------------------
    # 3. Inflación y Precios (Cálculo Interanual t/t-4)
    # -------------------------------------------------------------
    ipc_mappings = {
        'IPC. GENERAL': 'cpi_total_index',
        'IPC. SUBYACENTE': 'cpi_core_index',
        'IPC. SERVICIOS': 'cpi_services_index',
        'IPC. BIENES INDUSTRIALES': 'cpi_goods_index',
        'IPC. PRODUCTOS ENERGETICOS': 'cpi_energy_index',
        'IPC. ALIMENTOS': 'cpi_food_index',
        'IPCA. UE': 'cpi_eu_index'
    }

    found_ipc_cols = {}
    for target_key, std_name in ipc_mappings.items():
        for col in df_mens.columns:
            if target_key in col.upper():
                found_ipc_cols[std_name] = col
                break

    # Calcular tasas de inflación interanual (y guardar niveles de índice para el REER)
    cpi_levels = {}
    for std_name, raw_col in found_ipc_cols.items():
        idx_series = df_mens[raw_col].reindex(master_index)
        cpi_levels[std_name] = idx_series
        infl_series = idx_series.pct_change(4) * 100.0
        out_var = std_name.replace('cpi_', 'inflation_').replace('_index', '')
        df[out_var] = infl_series

    # Si falta desglose, aproximar usando general y subyacente
    if 'inflation_total' in df.columns:
        if 'inflation_core' not in df.columns:
            df['inflation_core'] = df['inflation_total'] * 0.85
        if 'inflation_services' not in df.columns:
            df['inflation_services'] = df['inflation_core'] * 1.05
        if 'inflation_goods' not in df.columns:
            df['inflation_goods'] = df['inflation_core'] * 0.95
        if 'inflation_energy' not in df.columns:
            df['inflation_energy'] = (df['inflation_total'] - df['inflation_core'] * 0.75) / 0.25
        if 'inflation_food' not in df.columns:
            df['inflation_food'] = df['inflation_core']

    # -------------------------------------------------------------
    # 4. Variables Exógenas Internacionales
    # -------------------------------------------------------------
    # Brecha de demanda de socios externos (UE, Alemania, USA)
    external_cols = {
        'gdp_germany': ['ALEMANIA', 'GERMANY'],
        'gdp_eu': ['UE. CVEC', 'EUROPA', 'EUROZONE'],
        'gdp_usa': ['EEUU', 'USA', 'ESTADOS UNIDOS']
    }
    for var_name, keywords in external_cols.items():
        matched_col = None
        for col in df_trim.columns:
            if any(k in col.upper() for k in keywords) and 'PIB' in col.upper():
                matched_col = col
                break
        if matched_col:
            series = df_trim[matched_col].reindex(master_index).dropna()
            if len(series) > 10:
                _, cycle = hp_filter(np.log(series), lamb=1600)
                gap_name = var_name.replace('gdp_', 'output_gap_')
                df[gap_name] = cycle * 100.0

    if 'output_gap_eu' not in df.columns:
        df['output_gap_eu'] = df.get('output_gap_germany', pd.Series(0.0, index=master_index))
    if 'output_gap_usa' not in df.columns:
        df['output_gap_usa'] = pd.Series(0.0, index=master_index)
    df['output_gap_china'] = pd.Series(0.0, index=master_index)

    # Petróleo Brent
    if len(df_crudo) > 0:
        df['oil_price_brent'] = df_crudo['oil_price_brent'].reindex(master_index).ffill()
    else:
        df['oil_price_brent'] = 75.0

    # -------------------------------------------------------------
    # Gas Natural (EUR/MWh).
    #   Preferencia: serie REAL de gas europeo (FRED PNGASEUUSDM convertida a EUR/MWh
    #   por refresh_energy_data), mensual → trimestral. Recoge la variación intra-anual
    #   real, incluido el pico de 2021-2022.
    #   Fallback: medias anuales interpoladas (ttf_annual), si no hay serie descargada.
    #   Los trimestres 2025-2026 quedan sobrescritos por la actualización oficial.
    # -------------------------------------------------------------
    from .refresh_energy_data import GAS_CSV
    gas_loaded = False
    if GAS_CSV.exists():
        try:
            dg = pd.read_csv(GAS_CSV, parse_dates=['date'])
            gq = (dg.set_index('date')['ttf_eur_mwh']
                    .resample('QS').mean().reindex(master_index))
            df['gas_price_ttf'] = gq.interpolate(method='time').ffill().bfill()
            gas_loaded = df['gas_price_ttf'].notna().sum() > 20
        except Exception as e:
            print(f"Aviso al cargar gas real ({GAS_CSV.name}): {e}")
    if not gas_loaded:
        # Respaldo: medias anuales de referencia del Dutch TTF interpoladas.
        ttf_annual = {
            2005: 16, 2008: 25, 2009: 13, 2010: 17, 2011: 22, 2012: 24, 2013: 27,
            2014: 21, 2015: 20, 2016: 14, 2017: 17, 2018: 23, 2019: 13.6, 2020: 9.4,
            2021: 46.8, 2022: 123.0, 2023: 40.6, 2024: 34.5, 2025: 36.0, 2026: 55.0,
        }
        gas_anchor = pd.Series(
            {pd.Timestamp(y, 7, 1): v for y, v in ttf_annual.items()}
        ).reindex(master_index)
        df['gas_price_ttf'] = gas_anchor.interpolate(method='time').ffill().bfill()

    # -------------------------------------------------------------
    # 5. Condiciones Financieras (Tipos e Intereses)
    # -------------------------------------------------------------
    tipo_col = None
    for col in df_mens.columns:
        if 'TIPO INTERES' in col.upper() or 'LETRAS' in col.upper() or 'EURIBOR' in col.upper():
            tipo_col = col
            break
    if tipo_col:
        df['interest_rate_spain'] = df_mens[tipo_col].reindex(master_index)
    else:
        df['interest_rate_spain'] = 2.50

    # Tipo BCE y prima de riesgo
    df['interest_rate_ecb'] = (df['interest_rate_spain'] - 0.70).clip(lower=0.0)
    df['risk_premium_spain'] = (df['interest_rate_spain'] - df['interest_rate_ecb']).clip(lower=0.20)

    # -------------------------------------------------------------
    # Tipo de Cambio Real Efectivo INTERNO (competitividad vía precios relativos)
    # Para un miembro de la UEM no hay tipo de cambio nominal propio: la competitividad
    # se ajusta por el diferencial de precios frente a los socios (devaluación interna).
    # Construimos el REER como el nivel de precios relativo España/UE (base 100 al inicio);
    # una apreciación (precios españoles subiendo más rápido) resta competitividad.
    # -------------------------------------------------------------
    es_cpi = cpi_levels.get('cpi_total_index')
    eu_cpi = cpi_levels.get('cpi_eu_index')
    if (es_cpi is not None and eu_cpi is not None
            and es_cpi.notna().sum() > 20 and eu_cpi.notna().sum() > 20):
        rel = (es_cpi / eu_cpi).reindex(master_index)
        first = rel.dropna().iloc[0]
        reer = rel / first * 100.0
        df['real_exchange_rate'] = reer
        log_reer = np.log(reer.dropna())
        _, cycle = hp_filter(log_reer, lamb=1600)
        df['reer_gap'] = cycle.reindex(master_index) * 100.0
    else:
        df['real_exchange_rate'] = 100.0
        df['reer_gap'] = 0.0

    # Limpiar extremos y rellenar valores faltantes razonables
    df = df.sort_index()
    # Descartar periodos sin datos de PIB o inflación
    valid_mask = df['output_gap_spain'].notna() & df['inflation_total'].notna()
    df_clean = df[valid_mask].copy()

    # -------------------------------------------------------------
    # 6. Incorporar Actualización Oficial Más Reciente (2025 - 2026)
    # -------------------------------------------------------------
    from .config import SANDBOX_DIR
    update_file = SANDBOX_DIR / "data" / "actualizacion_oficial_2025_2026.csv"
    if update_file.exists():
        try:
            df_up = pd.read_csv(update_file)
            df_up['date'] = pd.to_datetime(df_up['date'])
            df_up = df_up.set_index('date').sort_index()
            # Combinar asegurando que los nuevos trimestres se incorporen
            overlap_mask = ~df_clean.index.isin(df_up.index)
            df_clean = pd.concat([df_clean[overlap_mask], df_up]).sort_index()
        except Exception as e:
            print(f"Aviso al cargar actualización oficial 2025-2026: {e}")

    # Completar colas recientes de series cuyo índice mensual acaba antes del final
    # de la muestra (los índices de IPC terminan en 2024): se prolonga el último valor
    # válido para no dejar huecos en la Phillips de bienes ni en la competitividad.
    for _col in ['inflation_eu', 'reer_gap', 'real_exchange_rate']:
        if _col in df_clean.columns:
            df_clean[_col] = df_clean[_col].ffill()

    # -------------------------------------------------------------
    # 6b. Nowcasting provisional: trimestres sin dato INE todavía
    #     Fuente: crisistrackerv2 (repo hermano en Github/).
    #       · t6.csv → QoQ del trimestre corriente (actualización semanal)
    #       · t3.csv → QoQ del trimestre siguiente
    #     Las filas nowcast se añaden DESPUÉS de actualizacion_oficial, de modo
    #     que solo cubren fechas posteriores al último dato INE disponible.
    #     En cuanto se publique el dato oficial y se actualice
    #     actualizacion_oficial_2025_2026.csv, estas filas se sustituyen solas.
    # -------------------------------------------------------------
    from .config import NOWCAST_TABLES_DIR
    if NOWCAST_TABLES_DIR.exists() and len(df_clean) > 0:
        try:
            last_off_date = df_clean.index.max()
            last_off_gdp  = float(df_clean.loc[last_off_date, 'gdp_real_spain'])
            if not pd.isna(last_off_gdp):
                df_now = load_nowcast_gdp(NOWCAST_TABLES_DIR, last_off_date, last_off_gdp)
                if len(df_now) > 0:
                    new_dates = [d for d in df_now.index if d not in df_clean.index]
                    if new_dates:
                        # Añadir filas vacías y rellenar con el último dato conocido
                        df_ext = pd.DataFrame(
                            index=pd.DatetimeIndex(new_dates),
                            columns=df_clean.columns,
                            dtype=float,
                        )
                        df_clean = pd.concat([df_clean, df_ext]).sort_index()
                        cols_to_ffill = [c for c in df_clean.columns if c != 'gdp_real_spain']
                        df_clean[cols_to_ffill] = df_clean[cols_to_ffill].ffill()
                    # Asignar GDP nowcast (también actualiza si ya existe la fila)
                    df_clean.loc[df_now.index, 'gdp_real_spain'] = df_now['gdp_real_spain']
        except Exception as e:
            print(f"Aviso al incorporar nowcast en pipeline: {e}")

    # -------------------------------------------------------------
    # 7. PIB potencial por FUNCIÓN DE PRODUCCIÓN (Fase 3)
    #    Sustituye el potencial estático (que infravaloraba el crecimiento y
    #    sobreestimaba la brecha) por uno con input laboral explícito, de modo que
    #    la expansión de la población en edad de trabajar por inmigración eleva el
    #    potencial y reduce la brecha a niveles coherentes con la posición cíclica.
    # -------------------------------------------------------------
    try:
        from .potential import compute_historical_potential
        gdp_real = df_clean['gdp_real_spain'].astype(float).interpolate()
        if gdp_real.notna().sum() > 20:
            pf = compute_historical_potential(gdp_real)
            df_clean['gdp_potential_spain'] = pf['gdp_potential'].reindex(df_clean.index)
            df_clean['output_gap_spain'] = pf['output_gap'].reindex(df_clean.index)
    except Exception as e:
        print(f"Aviso: potencial por función de producción no disponible, se mantiene el previo: {e}")

    # -------------------------------------------------------------
    # 8. Overlay de medidas energéticas conmutables (histórico)
    #    Efecto de nivel de las intervenciones (20 cts, IVA eléctrico, tope al gas)
    #    sobre el IPC energético, en el trimestre de entrada y de salida. La ecuación
    #    energética lo suma; así el modelo reproduce el escalón que dejaron las medidas.
    # -------------------------------------------------------------
    try:
        df_clean['energy_policy_overlay'] = build_policy_overlay(df_clean.index).reindex(df_clean.index).fillna(0.0)
    except Exception as e:
        print(f"Aviso: overlay de medidas energéticas no disponible: {e}")
        df_clean['energy_policy_overlay'] = 0.0

    return df_clean
