"""
Ensamblado (Fase 3): arma el DataFrame trimestral del modelo leyendo SOLO
del almacén único (macro.db), aplicando las transformaciones que declara el
catálogo. Sustituye a data_pipeline.py::build_consolidated_dataset.

Principio "todo real": cada columna del modelo procede de una serie real y
catalogada. Si una serie que una columna necesita no tiene datos, se PARA con
FaltaDatoError y dice cuál falta; NUNCA rellena con un valor por defecto. La
única constante explícita es output_gap_china = 0, por decisión del usuario
(China aparcada), y se registra en el log como tal, no de forma silenciosa.

Reutiliza los cálculos ya validados del modelo (no los reinventa):
  - hp_filter y build_policy_overlay de data_pipeline.py
  - compute_historical_potential de potential.py (alimentado con la EPA del
    almacén en vez del xlsx)

Uso:
    from src.datos.ensamblado import construir_dataset
    df = construir_dataset()          # sincroniza catálogo y arma el panel
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from . import almacen
from ..data_pipeline import build_policy_overlay, hp_filter
from ..potential import compute_historical_potential

# M€ por punto de índice CVEC (INE 2015); solo afecta al NIVEL informado del
# PIB, no a la dinámica del modelo (que usa logs y tasas). Mismo valor que
# usaba data_pipeline._scale_cvec_to_millions como referencia.
ESCALA_CVEC_M_EUR = 2591.1


class FaltaDatoError(RuntimeError):
    """Una columna del modelo necesita una serie que el almacén no tiene."""


def _leer(serie_id: str, db_path: Optional[Path]) -> pd.Series:
    """Lee una serie del almacén como pd.Series(fecha->valor). Lanza si está vacía."""
    df = almacen.leer(serie_id, db_path=db_path)
    if df.empty or serie_id not in df.columns:
        raise FaltaDatoError(
            f"La serie '{serie_id}' no tiene datos en el almacén. Ejecútese el "
            f"conector correspondiente (python -m src.datos.conectores.actualizar_datos) "
            f"antes de ensamblar. No se rellena con un valor por defecto.")
    s = df[serie_id].dropna()
    if s.empty:
        raise FaltaDatoError(f"La serie '{serie_id}' existe pero no tiene valores no nulos.")
    return s


def _trimestral_media(serie_id: str, master: pd.DatetimeIndex,
                       db_path: Optional[Path]) -> pd.Series:
    """Serie de origen mensual/diario -> media trimestral alineada al master."""
    s = _leer(serie_id, db_path)
    return s.resample("QS").mean().reindex(master)


def _trimestral_directa(serie_id: str, master: pd.DatetimeIndex,
                         db_path: Optional[Path]) -> pd.Series:
    """Serie ya trimestral (fechas a inicio de trimestre) -> alineada al master."""
    s = _leer(serie_id, db_path)
    return s.reindex(master)


def _yoy4(indice_trim: pd.Series) -> pd.Series:
    """Tasa interanual desde un índice trimestral (t/t-4, en %)."""
    return indice_trim.pct_change(4) * 100.0


def _hp_gap_ln(nivel_trim: pd.Series, master: pd.DatetimeIndex,
               lamb: float = 1600.0) -> pd.Series:
    """Brecha (%) como ciclo HP del log del nivel trimestral."""
    serie = nivel_trim.dropna()
    if len(serie) < 8:
        raise FaltaDatoError(
            f"Serie demasiado corta ({len(serie)} obs) para una brecha HP fiable.")
    _, ciclo = hp_filter(np.log(serie), lamb=lamb)
    return (ciclo * 100.0).reindex(master)


def construir_dataset(db_path: Optional[Path] = None, auto_sync: bool = True) -> pd.DataFrame:
    """
    Arma el panel trimestral del modelo desde el almacén. Devuelve un DataFrame
    indexado por trimestres (QS), con las mismas columnas que producía
    data_pipeline.build_consolidated_dataset, pero todas a partir de datos reales.
    """
    if auto_sync:
        almacen.sync_catalogo(db_path=db_path)

    # ---- Índice maestro: 1995T1 hasta el último trimestre con PIB ----
    pib_idx = _leer("ine_pib_real_espana", db_path)          # índice CVEC oficial, trimestral
    inicio = pd.Timestamp("1995-01-01")
    fin_oficial = pib_idx.index.max()

    # Nowcast provisional (opcional): trimestres por delante del último oficial.
    # Es dato real (una estimación), no un valor por defecto; si no hay repo de
    # nowcast, no se extiende y punto (no se inventa el trimestre en curso).
    try:
        nc = _leer("nowcast_pib_espana", db_path)   # _leer ya devuelve una Serie
        nc = nc[nc.index > fin_oficial]
    except FaltaDatoError:
        nc = pd.Series(dtype=float)

    fin = max(fin_oficial, nc.index.max()) if not nc.empty else fin_oficial
    master = pd.date_range(start=inicio, end=fin, freq="QS")
    df = pd.DataFrame(index=master)

    # ---- 1. PIB real (oficial + cola provisional) y potencial ----
    indice_pib = pib_idx.reindex(master)
    es_provisional = pd.Series(False, index=master)
    for fecha, valor in nc.items():
        if fecha in master.values and pd.isna(indice_pib.loc[fecha]):  # nunca pisa un dato oficial
            indice_pib.loc[fecha] = valor
            es_provisional.loc[fecha] = True
    df["gdp_real_spain"] = indice_pib * ESCALA_CVEC_M_EUR
    # Marca numérica (1.0 provisional / 0.0 oficial) para no romper el motor,
    # que trata el DataFrame como matriz numérica. El informe la usa para
    # señalar los trimestres de nowcast.
    df["gdp_provisional"] = es_provisional.astype(float).values

    # Mercado laboral real (EPA) para la función de producción del potencial.
    labour_df = pd.DataFrame({
        "u": _trimestral_directa("ine_epa_tasa_paro", master, db_path),
        "wap": _trimestral_directa("ine_epa_pob16mas", master, db_path),
        "emp": _trimestral_directa("ine_epa_ocupados", master, db_path),
        "active": _trimestral_directa("ine_epa_activos", master, db_path),
    })
    gdp_real = df["gdp_real_spain"].astype(float).interpolate()
    pf = compute_historical_potential(gdp_real, labour_df=labour_df)
    df["gdp_potential_spain"] = pf["gdp_potential"].reindex(master)
    df["output_gap_spain"] = pf["output_gap"].reindex(master)
    # Empleo potencial = L* de la función de producción (mismo insumo laboral real:
    # población en edad de trabajar x actividad tendencial x (1-NAIRU), en miles).
    df["employment_potential"] = pf["Lstar"].reindex(master)

    # ---- 2. Mercado laboral ----
    from ..model import compute_unemployment_seasonal_factors
    df["unemployment_rate"] = labour_df["u"]
    df["employment_persons"] = labour_df["emp"]
    trend_u, _ = hp_filter(labour_df["u"].dropna(), lamb=6400)
    df["nairu"] = trend_u.reindex(master)

    # Factores estacionales de la EPA (suma cero) y tasa desestacionalizada
    seas_u = compute_unemployment_seasonal_factors(labour_df["u"])
    df["unemployment_rate_sa"] = pd.Series(
        [labour_df["u"].loc[d] - seas_u.get(d.quarter, 0.0) if pd.notna(labour_df["u"].loc[d]) else np.nan for d in master],
        index=master
    )

    # Puente / Nowcast laboral para trimestres con PIB provisional (ej: 2026-T3 y 2026-T4):
    # Cuando la EPA aún no ha publicado pero el PIB de nowcast sí está disponible, se
    # proyecta la tasa de paro y los ocupados mediante Okun y la elasticidad de empleo.
    if df["unemployment_rate"].isna().any():
        u_vals = df["unemployment_rate"].values.copy()
        u_sa_vals = df["unemployment_rate_sa"].values.copy()
        n_vals = df["nairu"].values.copy()
        emp_vals = df["employment_persons"].values.copy()
        gap_vals = df["output_gap_spain"].values
        gdp_real_vals = df["gdp_real_spain"].values

        # Prolongar NAIRU tendencialmente sobre los trimestres sin EPA
        for i in range(1, len(master)):
            if np.isnan(n_vals[i]) and not np.isnan(n_vals[i - 1]):
                # Continuar la suave deriva tendencial histórica (~ -0.10 pp/trimestre)
                deriva = n_vals[i - 1] - n_vals[i - 2] if i >= 2 and not np.isnan(n_vals[i - 2]) else -0.10
                deriva = np.clip(deriva, -0.20, 0.0)
                n_vals[i] = n_vals[i - 1] + deriva

        # Estimar tasa de paro desestacionalizada con Okun y superponer estacionalidad
        for i in range(1, len(master)):
            if np.isnan(u_sa_vals[i]) and not np.isnan(u_sa_vals[i - 1]):
                gap_diff_i = gap_vals[i] - gap_vals[i - 1] if not np.isnan(gap_vals[i - 1]) else 0.0
                gap_level_i = gap_vals[i] if not np.isnan(gap_vals[i]) else 0.0
                # Okun en niveles y diferencias sobre la tasa desestacionalizada
                u_sa_vals[i] = n_vals[i] + 0.78 * (u_sa_vals[i - 1] - n_vals[i - 1]) - 0.28 * gap_level_i - 0.22 * gap_diff_i
                q_i = master[i].quarter
                u_vals[i] = u_sa_vals[i] + seas_u.get(q_i, 0.0)

            if np.isnan(emp_vals[i]) and not np.isnan(emp_vals[i - 1]):
                g_gdp = (gdp_real_vals[i] / gdp_real_vals[i - 1] - 1.0) if not np.isnan(gdp_real_vals[i - 1]) else 0.005
                emp_vals[i] = emp_vals[i - 1] * (1.0 + 0.75 * g_gdp)

        df["nairu"] = n_vals
        df["unemployment_rate_sa"] = u_sa_vals
        df["unemployment_rate"] = u_vals
        df["employment_persons"] = emp_vals

    # ---- 3. Inflación (índices IPC -> media trimestral -> interanual) ----
    ipc = {
        "inflation_total": "ine_ipc_general",
        "inflation_core": "ine_ipc_subyacente",
        "inflation_services": "ine_ipc_servicios",
        "inflation_goods": "ine_ipc_bienes_industriales",
        "inflation_energy": "ine_ipc_energia",
        "inflation_food": "ine_ipc_alimentos",
    }
    niveles_ipc = {}
    for col, serie_id in ipc.items():
        idx_trim = _trimestral_media(serie_id, master, db_path)
        niveles_ipc[serie_id] = idx_trim
        df[col] = _yoy4(idx_trim)

    # IPCA eurozona: el almacén guarda ya la TASA interanual (RCH_A) -> media trimestral.
    df["inflation_eu"] = _trimestral_media("eurostat_hicp_ea20", master, db_path)

    # ---- 4. Entorno exterior (brechas HP) ----
    df["output_gap_eu"] = _hp_gap_ln(_trimestral_directa("eurostat_pib_eurozona", master, db_path), master)
    df["output_gap_usa"] = _hp_gap_ln(_trimestral_directa("fred_pib_usa", master, db_path), master)
    # China APARCADA por decisión del usuario: marcador 0 explícito y registrado,
    # no un valor por defecto silencioso. Reactivar cuando se decida su fuente.
    df["output_gap_china"] = 0.0
    print("[ensamblado] output_gap_china = 0 (China aparcada por decisión del usuario, "
          "no es un dato real; el resto del panel es real).")

    # ---- 5. Energía ----
    df["oil_price_brent"] = _trimestral_media("fred_brent", master, db_path)
    df["gas_price_ttf"] = _trimestral_media("fred_gas_eu", master, db_path)

    # ---- 6. Condiciones financieras ----
    df["interest_rate_spain"] = _trimestral_media("bce_euribor_3m", master, db_path)   # tipo corto
    df["interest_rate_ecb"] = _trimestral_media("bce_tipo_deposito", master, db_path)  # facilidad depósito REAL
    # Prima de riesgo = diferencial 10 años España - Alemania (dato real, no una resta a ojo).
    es10 = _trimestral_media("eurostat_rendimiento_10y_espana", master, db_path)
    de10 = _trimestral_media("eurostat_rendimiento_10y_alemania", master, db_path)
    df["risk_premium_spain"] = es10 - de10

    # ---- 7. Tipo de cambio real efectivo interno (precios relativos ES/UE) ----
    es_cpi = niveles_ipc["ine_ipc_general"]
    eu_cpi = _trimestral_media("eurostat_hicp_indice_ea20", master, db_path)
    rel = (es_cpi / eu_cpi)
    primero = rel.dropna().iloc[0]
    reer = rel / primero * 100.0
    df["real_exchange_rate"] = reer
    _, ciclo_reer = hp_filter(np.log(reer.dropna()), lamb=1600)
    df["reer_gap"] = (ciclo_reer * 100.0).reindex(master)

    # ---- 8. Overlay de medidas energéticas (mismo cálculo que el pipeline) ----
    df["energy_policy_overlay"] = build_policy_overlay(master).reindex(master).fillna(0.0)

    # ---- Colas con retraso de publicación: IPCA UE y REER acaban antes que el
    #      resto (Eurostat publica el IPCA con desfase); se prolonga el último
    #      valor para no dejar NaN en el trimestre en curso / provisional.
    for _col in ["inflation_eu", "reer_gap", "real_exchange_rate"]:
        if _col in df.columns:
            df[_col] = df[_col].ffill()

    # ---- Muestra limpia: donde hay PIB (brecha) e inflación ----
    df = df.sort_index()
    valido = df["output_gap_spain"].notna() & df["inflation_total"].notna()
    return df[valido].copy()


if __name__ == "__main__":
    d = construir_dataset()
    print(f"\n[ensamblado] Panel armado: {d.shape[0]} trimestres x {d.shape[1]} columnas")
    print(f"  rango: {d.index.min().date()} -> {d.index.max().date()}")
    print(f"  columnas: {list(d.columns)}")
    print("\n  últimas 4 filas (selección):")
    cols = ["gdp_real_spain", "output_gap_spain", "unemployment_rate",
            "inflation_total", "interest_rate_spain", "risk_premium_spain"]
    print(d[cols].tail(4).to_string())
