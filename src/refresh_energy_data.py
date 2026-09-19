"""
Refresco automático de las series de precios de energía (Brent y gas europeo).

Descarga datos observados desde FRED (Federal Reserve Economic Data, público y
gratuito, sin clave) y los deja versionados en ``data/nuevos/`` para que el
pipeline los consuma. Sustituye:
  - el crudo.csv congelado en 2025Q2  → Brent diario extendido hasta hoy.
  - el ``ttf_annual`` inventado         → serie real de gas europeo (mensual).

Series FRED utilizadas:
  - DCOILBRENTEU : Brent Europe, spot, diario, USD/barril.
  - PNGASEUUSDM  : Global price of Natural gas, EU (IMF PCPS), mensual, USD/MMBtu.
                   Se convierte a EUR/MWh para alinear con el TTF del modelo.

Diseño (importante):
  * La descarga corre donde HAY red sin restricciones: la máquina del usuario.
    En un entorno sin salida (p. ej. el sandbox de Claude) la función NO falla:
    conserva el CSV cacheado y avisa. El modelo es así determinista y offline-safe.
  * Caché por antigüedad: solo vuelve a descargar si el fichero local supera
    ``max_age_days`` (por defecto 7). Reestimar el modelo dispara el refresco
    sin martillear FRED en cada ejecución.
  * Cada fila queda con su fecha de descarga y fuente → trazable y auditable.

Uso directo:
    python sandbox/src/refresh_energy_data.py            # refresco con caché
    python sandbox/src/refresh_energy_data.py --force    # fuerza descarga
"""

from __future__ import annotations

import io
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

try:
    from .config import DATA_NUEVOS_DIR
except Exception:  # ejecución como script suelto
    DATA_NUEVOS_DIR = Path(__file__).resolve().parent.parent / "data" / "nuevos"

# --- Identificadores de series FRED (parametrizables) ---
FRED_BRENT_ID = "DCOILBRENTEU"   # Brent diario, USD/barril
FRED_GAS_EU_ID = "PNGASEUUSDM"   # Gas natural EU (IMF), mensual, USD/MMBtu

# --- Ficheros de salida ---
BRENT_CSV = DATA_NUEVOS_DIR / "brent_daily.csv"        # date, brent_usd
GAS_CSV = DATA_NUEVOS_DIR / "gas_ttf_monthly.csv"      # date, ttf_eur_mwh, gas_eu_usd_mmbtu

# --- Constantes de conversión gas ---
MMBTU_PER_MWH = 0.293071        # 1 MMBtu = 0.293071 MWh
DEFAULT_USDEUR = 1.08           # respaldo si no hay serie de tipo de cambio


def _fred_csv_url(series_id: str, start: str = "1987-01-01") -> str:
    return (f"https://fred.stlouisfed.org/graph/fredgraph.csv"
            f"?id={series_id}&cosd={start}")


def _download_fred(series_id: str, start: str = "1987-01-01",
                   timeout: int = 45) -> Optional[pd.DataFrame]:
    """Descarga una serie de FRED como DataFrame [date, value]. None si no hay red.

    Intenta primero pandas_datareader (si está instalado) y, en su defecto, el
    endpoint CSV público vía urllib. No lanza excepción: devuelve None ante
    cualquier fallo de red para que el pipeline continúe con el CSV cacheado.
    """
    # 1) pandas_datareader, si está disponible
    try:
        from pandas_datareader import data as pdr  # type: ignore
        s = pdr.DataReader(series_id, "fred", start)
        df = s.reset_index()
        df.columns = ["date", "value"]
        return df
    except Exception:
        pass

    # 2) endpoint CSV público de FRED vía urllib (sin dependencias extra)
    try:
        import urllib.request
        url = _fred_csv_url(series_id, start)
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
        df = pd.read_csv(io.StringIO(raw))
        df.columns = ["date", "value"]
        # FRED marca los huecos con '.'
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        return df
    except Exception as e:
        print(f"[refresh_energy_data] Sin red o fallo al descargar {series_id}: {e}")
        return None


def _is_stale(path: Path, max_age_days: float) -> bool:
    """True si el fichero no existe o supera la antigüedad máxima."""
    if not path.exists():
        return True
    age_days = (time.time() - path.stat().st_mtime) / 86400.0
    return age_days > max_age_days


def _load_usdeur_quarterly() -> Optional[pd.Series]:
    """Serie trimestral USD/EUR desde series_diarias.xlsx, para convertir el gas."""
    try:
        from .config import DATA_PATHS
        dd = pd.read_excel(DATA_PATHS["diarias"])
        dd = dd.iloc[1:].reset_index(drop=True)
        d0 = dd.columns[0]
        dd[d0] = pd.to_datetime(dd[d0].astype(str).str.strip("'"), errors="coerce", format="%Y%m%d")
        dd = dd.dropna(subset=[d0]).set_index(d0).sort_index()
        s = pd.to_numeric(dd.iloc[:, 0], errors="coerce")
        return s.resample("MS").mean()
    except Exception:
        return None


def refresh_brent(force: bool = False, max_age_days: float = 7.0) -> Optional[pd.DataFrame]:
    """Descarga/actualiza el Brent diario a data/nuevos/brent_daily.csv."""
    DATA_NUEVOS_DIR.mkdir(parents=True, exist_ok=True)
    if not force and not _is_stale(BRENT_CSV, max_age_days):
        return pd.read_csv(BRENT_CSV, parse_dates=["date"])

    df = _download_fred(FRED_BRENT_ID, start="1987-01-01")
    if df is None:
        if BRENT_CSV.exists():
            print("[refresh_energy_data] Brent: uso el CSV cacheado.")
            return pd.read_csv(BRENT_CSV, parse_dates=["date"])
        return None

    df = df.dropna().rename(columns={"value": "brent_usd"})
    df["date"] = pd.to_datetime(df["date"])
    df = df[["date", "brent_usd"]].sort_values("date")
    df["source"] = f"FRED:{FRED_BRENT_ID}"
    df["fetched_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    df.to_csv(BRENT_CSV, index=False)
    print(f"[refresh_energy_data] Brent actualizado: {df['date'].min().date()} -> "
          f"{df['date'].max().date()} ({len(df)} obs)")
    return df


def refresh_gas(force: bool = False, max_age_days: float = 7.0) -> Optional[pd.DataFrame]:
    """Descarga/actualiza el gas europeo mensual y lo convierte a EUR/MWh."""
    DATA_NUEVOS_DIR.mkdir(parents=True, exist_ok=True)
    if not force and not _is_stale(GAS_CSV, max_age_days):
        return pd.read_csv(GAS_CSV, parse_dates=["date"])

    df = _download_fred(FRED_GAS_EU_ID, start="1990-01-01")
    if df is None:
        if GAS_CSV.exists():
            print("[refresh_energy_data] Gas: uso el CSV cacheado.")
            return pd.read_csv(GAS_CSV, parse_dates=["date"])
        return None

    df = df.dropna().rename(columns={"value": "gas_eu_usd_mmbtu"})
    df["date"] = pd.to_datetime(df["date"])
    df = df[["date", "gas_eu_usd_mmbtu"]].sort_values("date").set_index("date")

    # USD/MMBtu → USD/MWh → EUR/MWh (con USD/EUR trimestral reindexado a mensual)
    usdeur = _load_usdeur_quarterly()
    if usdeur is not None:
        usdeur_m = usdeur.reindex(df.index, method="nearest").fillna(DEFAULT_USDEUR)
    else:
        usdeur_m = pd.Series(DEFAULT_USDEUR, index=df.index)
    usd_per_mwh = df["gas_eu_usd_mmbtu"] / MMBTU_PER_MWH
    df["ttf_eur_mwh"] = usd_per_mwh / usdeur_m

    out = df.reset_index()[["date", "ttf_eur_mwh", "gas_eu_usd_mmbtu"]]
    out["source"] = f"FRED:{FRED_GAS_EU_ID}"
    out["fetched_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out.to_csv(GAS_CSV, index=False)
    print(f"[refresh_energy_data] Gas actualizado: {out['date'].min().date()} -> "
          f"{out['date'].max().date()} ({len(out)} obs)")
    return out


def refresh_energy_data(force: bool = False, max_age_days: float = 7.0) -> dict:
    """Refresca Brent y gas. Best-effort: nunca lanza excepción.

    Returns:
        dict con las claves 'brent' y 'gas' (DataFrame o None).
    """
    result = {}
    try:
        result["brent"] = refresh_brent(force=force, max_age_days=max_age_days)
    except Exception as e:
        print(f"[refresh_energy_data] Error inesperado en Brent: {e}")
        result["brent"] = None
    try:
        result["gas"] = refresh_gas(force=force, max_age_days=max_age_days)
    except Exception as e:
        print(f"[refresh_energy_data] Error inesperado en gas: {e}")
        result["gas"] = None
    return result


if __name__ == "__main__":
    force = "--force" in sys.argv
    print(f"Refrescando series de energia (force={force})...")
    r = refresh_energy_data(force=force)
    ok = sum(1 for v in r.values() if v is not None)
    print(f"Hecho. Series actualizadas/cargadas: {ok}/2")
    if ok < 2:
        print("Aviso: alguna serie no se pudo actualizar (sin red o fuente no accesible).")
        sys.exit(1)
