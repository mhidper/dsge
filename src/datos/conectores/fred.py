"""
Conector FRED: petróleo Brent y gas natural europeo.

Reescritura de refresh_energy_data.py sobre el almacén único. Dos
diferencias con la versión anterior:

  1. No hay fichero de caché CSV: la "caché" es la propia base
     (se mira `almacen.ultima_descarga()`), así que desaparece la
     copia huérfana que se generaba en sandbox/data/nuevos/ cuando
     este módulo se ejecutaba suelto en vez de como parte del paquete.
  2. La conversión del gas de USD/MMBtu a EUR/MWh usa el tipo de
     cambio del BCE ya cargado en el almacén (`bce_usd_eur`), no el
     Excel congelado en 2025-06-16. Si `bce_usd_eur` todavía no tiene
     datos (por ejemplo, si este conector se corre antes que el de
     BCE), cae al valor por defecto 1.08 igual que antes.

Uso:
    python -m src.datos.conectores.fred                 # refresco con caché (7 días)
    python -m src.datos.conectores.fred --forzar         # fuerza descarga
"""

from __future__ import annotations

import io
import sys
from pathlib import Path
from typing import Optional

import pandas as pd

from .. import almacen
from ._comun import descargar_texto, esta_desactualizada, registrar_resultado

FRED_BRENT_ID = "DCOILBRENTEU"     # Brent Europe, spot, diario, USD/barril
FRED_GAS_EU_ID = "PNGASEUUSDM"     # Gas natural EU (IMF PCPS), mensual, USD/MMBtu
FRED_PIB_USA_ID = "GDPC1"          # PIB real EE. UU., encadenado 2017, trimestral

MMBTU_PER_MWH = 0.293071
DEFAULT_USDEUR = 1.08              # respaldo si bce_usd_eur aún no tiene datos


def _fred_csv_url(series_id: str, start: str = "1987-01-01") -> str:
    return f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}&cosd={start}"


def _parsear_csv_fred(texto: str, series_id: str) -> Optional[pd.Series]:
    """
    Parsea el CSV de fredgraph.csv (dos columnas: fecha, valor; huecos
    marcados con '.'). Separado de la descarga para poder probarlo sin
    red, con un texto de ejemplo.
    """
    try:
        df = pd.read_csv(io.StringIO(texto))
        df.columns = ["date", "value"]
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df["value"] = pd.to_numeric(df["value"], errors="coerce")  # FRED marca huecos con '.'
        df = df.dropna(subset=["date", "value"]).set_index("date").sort_index()
        return df["value"]
    except Exception as e:
        print(f"[fred] Error al parsear la respuesta de {series_id}: {e}")
        return None


def _descargar_serie_fred(series_id: str, start: str = "1987-01-01") -> Optional[pd.Series]:
    """Descarga una serie de FRED como pd.Series (índice=fecha). None si falla."""
    texto = descargar_texto(_fred_csv_url(series_id, start))
    if texto is None:
        return None
    return _parsear_csv_fred(texto, series_id)


def actualizar_brent(forzar: bool = False, max_age_days: float = 7.0,
                      db_path: Optional[Path] = None) -> bool:
    """Descarga/actualiza el Brent diario y lo escribe en 'fred_brent'."""
    if not forzar and not esta_desactualizada("fred_brent", max_age_days, db_path):
        print("[fred] Brent al día, no se descarga (usar --forzar para saltarse la caché).")
        return True

    serie = _descargar_serie_fred(FRED_BRENT_ID, start="1987-01-01")
    if serie is None:
        print("[fred] Brent: sin red, se conserva lo que ya hay en el almacén.")
        return False

    n = almacen.escribir(serie, "fred_brent", estado="oficial",
                          fuente_detalle=f"FRED:{FRED_BRENT_ID}", db_path=db_path)
    print(f"[fred] Brent actualizado: {serie.index.min().date()} -> "
          f"{serie.index.max().date()} ({n} obs. escritas)")
    return True


def actualizar_gas(forzar: bool = False, max_age_days: float = 7.0,
                    db_path: Optional[Path] = None) -> bool:
    """Descarga/actualiza el gas europeo mensual, convertido a EUR/MWh, en 'fred_gas_eu'."""
    if not forzar and not esta_desactualizada("fred_gas_eu", max_age_days, db_path):
        print("[fred] Gas al día, no se descarga (usar --forzar para saltarse la caché).")
        return True

    serie_usd_mmbtu = _descargar_serie_fred(FRED_GAS_EU_ID, start="1990-01-01")
    if serie_usd_mmbtu is None:
        print("[fred] Gas: sin red, se conserva lo que ya hay en el almacén.")
        return False

    usd_por_mwh = serie_usd_mmbtu / MMBTU_PER_MWH

    usdeur = almacen.leer("bce_usd_eur", db_path=db_path)
    if not usdeur.empty:
        usdeur_m = (usdeur["bce_usd_eur"]
                    .resample("MS").mean()
                    .reindex(usd_por_mwh.index, method="nearest")
                    .fillna(DEFAULT_USDEUR))
        fuente_fx = "BCE:EXR.D.USD.EUR.SP00.A"
    else:
        usdeur_m = pd.Series(DEFAULT_USDEUR, index=usd_por_mwh.index)
        fuente_fx = f"respaldo fijo {DEFAULT_USDEUR} (bce_usd_eur aún sin datos)"

    ttf_eur_mwh = usd_por_mwh / usdeur_m

    n = almacen.escribir(ttf_eur_mwh, "fred_gas_eu", estado="oficial",
                          fuente_detalle=f"FRED:{FRED_GAS_EU_ID}, FX={fuente_fx}",
                          db_path=db_path)
    print(f"[fred] Gas actualizado: {ttf_eur_mwh.index.min().date()} -> "
          f"{ttf_eur_mwh.index.max().date()} ({n} obs. escritas); conversión FX: {fuente_fx}")
    return True


def actualizar_pib_usa(forzar: bool = False, max_age_days: float = 30.0,
                       db_path: Optional[Path] = None) -> bool:
    """Descarga/actualiza el PIB real trimestral de EE. UU. en 'fred_pib_usa'.

    Guarda el nivel (miles de millones USD encadenados 2017); la brecha de
    producto (output_gap_usa) la calcula el ensamblado por filtro HP, igual
    que para la eurozona. Reemplaza al 0 fijo que hoy pone data_pipeline.py.
    """
    if not forzar and not esta_desactualizada("fred_pib_usa", max_age_days, db_path):
        print("[fred] PIB EE. UU. al día, no se descarga.")
        return True

    serie = _descargar_serie_fred(FRED_PIB_USA_ID, start="1970-01-01")
    if serie is None:
        print("[fred] PIB EE. UU.: sin red, se conserva lo que ya hay en el almacén.")
        return False

    # FRED fecha el trimestre en su primer día (2026-04-01 = 2026T2); ya es
    # inicio de trimestre, no necesita el ajuste horario del INE.
    n = almacen.escribir(serie, "fred_pib_usa", estado="oficial",
                          fuente_detalle=f"FRED:{FRED_PIB_USA_ID}", db_path=db_path)
    print(f"[fred] PIB EE. UU. actualizado: {serie.index.min().date()} -> "
          f"{serie.index.max().date()} ({n} obs. escritas)")
    return True


def actualizar_todo(forzar: bool = False, max_age_days: float = 7.0,
                     db_path: Optional[Path] = None) -> int:
    """Refresca Brent, gas, PIB EE. UU. y letras España. Best-effort: nunca lanza."""
    resultados = {}
    try:
        resultados["fred_brent"] = actualizar_brent(forzar, max_age_days, db_path)
    except Exception as e:
        print(f"[fred] Error inesperado en Brent: {e}")
        resultados["fred_brent"] = False
    try:
        resultados["fred_gas_eu"] = actualizar_gas(forzar, max_age_days, db_path)
    except Exception as e:
        print(f"[fred] Error inesperado en gas: {e}")
        resultados["fred_gas_eu"] = False
    try:
        # El PIB trimestral cambia poco; su propia caché (30 días) evita
        # descargas inútiles aunque el resto del bloque se refresque semanal.
        resultados["fred_pib_usa"] = actualizar_pib_usa(forzar, 30.0, db_path)
    except Exception as e:
        print(f"[fred] Error inesperado en PIB EE. UU.: {e}")
        resultados["fred_pib_usa"] = False
    return registrar_resultado("fred", resultados)


if __name__ == "__main__":
    forzar = "--forzar" in sys.argv or "--force" in sys.argv
    ok = actualizar_todo(forzar=forzar)
    sys.exit(0 if ok == 3 else 1)
