"""
Conector BCE (Data Portal / SDMX): tipo de depósito y USD/EUR.

Endpoint: https://data-api.ecb.europa.eu/service/data/{dataflow}/{clave}
Documentación: https://data.ecb.europa.eu/help/api/data

Solo se implementan aquí las dos series cuya clave SDMX es estable y
está documentada en los ejemplos públicos del propio BCE:

  - bce_tipo_deposito : FM.D.U2.EUR.4F.KR.DFR.LEV  (facilidad de depósito, diaria)
  - bce_usd_eur       : EXR.D.USD.EUR.SP00.A       (tipo de cambio de referencia, diario)

`interest_rate_spain` (tipo español representativo, hoy "letras del
tesoro" en series_mensuales.xlsx) se deja fuera a propósito: la clave
exacta en el dataflow de tipos de interés (IRS) no está confirmada, y
container un identificador adivinado sería peor que dejarlo pendiente.
Ver catalogo.yaml -> bce_tipo_letras_espana.

Nota: este entorno de desarrollo no pudo probar el endpoint en vivo
(bloqueo de robots.txt en la herramienta de scraping). Las claves están
tomadas de la documentación pública del BCE y son las que se usan en
los paquetes de referencia (p.ej. el paquete `ecb` de R), pero conviene
que la primera ejecución en tu máquina, con red real, se revise contra
https://data.ecb.europa.eu/data/datasets antes de dar la fase por cerrada.

Uso:
    python -m src.datos.conectores.bce
    python -m src.datos.conectores.bce --forzar
"""

from __future__ import annotations

import io
import sys
from pathlib import Path
from typing import Optional

import pandas as pd

from .. import almacen
from ._comun import descargar_texto, esta_desactualizada, registrar_resultado

BASE_URL = "https://data-api.ecb.europa.eu/service/data"

SERIES_BCE = {
    "bce_tipo_deposito": {
        "dataflow": "FM",
        "clave": "D.U2.EUR.4F.KR.DFR.LEV",
        "start": "1999-01-01",
    },
    "bce_usd_eur": {
        "dataflow": "EXR",
        "clave": "D.USD.EUR.SP00.A",
        "start": "1999-01-01",
    },
    # Tipo corto doméstico (interest_rate_spain): EURIBOR 3m, el tipo del
    # mercado monetario del euro que siguen las Letras del Tesoro. Elegido
    # por el usuario 2026-09-19 tras caerse la serie OCDE de letras (404).
    "bce_euribor_3m": {
        "dataflow": "FM",
        "clave": "M.U2.EUR.RT.MM.EURIBOR3MD_.HSTA",
        "start": "1999-01-01",
    },
}


def _url_csv(dataflow: str, clave: str, start: str) -> str:
    return f"{BASE_URL}/{dataflow}/{clave}?format=csvdata&startPeriod={start}"


def _parsear_csv_bce(texto: str, dataflow: str, clave: str) -> Optional[pd.Series]:
    """
    Parsea el SDMX-CSV del BCE. Trae muchas columnas de metadatos; solo
    interesan TIME_PERIOD y OBS_VALUE, buscadas por nombre (insensible a
    mayúsculas) para no depender del orden exacto, que cambia entre
    dataflows. Separado de la descarga para poder probarlo sin red.
    """
    try:
        df = pd.read_csv(io.StringIO(texto))
        cols = {c.upper(): c for c in df.columns}
        col_fecha = cols.get("TIME_PERIOD")
        col_valor = cols.get("OBS_VALUE")
        if col_fecha is None or col_valor is None:
            print(f"[bce] Respuesta sin columnas TIME_PERIOD/OBS_VALUE reconocibles "
                  f"para {dataflow}/{clave}; columnas recibidas: {list(df.columns)}")
            return None
        s = df[[col_fecha, col_valor]].copy()
        s.columns = ["fecha", "valor"]
        s["fecha"] = pd.to_datetime(s["fecha"], errors="coerce")
        s["valor"] = pd.to_numeric(s["valor"], errors="coerce")
        s = s.dropna(subset=["fecha", "valor"]).set_index("fecha").sort_index()
        return s["valor"]
    except Exception as e:
        print(f"[bce] Error al parsear la respuesta de {dataflow}/{clave}: {e}")
        return None


def _descargar_serie_bce(dataflow: str, clave: str, start: str) -> Optional[pd.Series]:
    """Descarga y parsea una serie del formato csvdata del BCE. None si falla."""
    texto = descargar_texto(_url_csv(dataflow, clave, start))
    if texto is None:
        return None
    return _parsear_csv_bce(texto, dataflow, clave)


def actualizar_serie(serie_id: str, forzar: bool = False, max_age_days: float = 10.0,
                      db_path: Optional[Path] = None) -> bool:
    if serie_id not in SERIES_BCE:
        raise ValueError(f"{serie_id!r} no está entre las series BCE implementadas: "
                          f"{sorted(SERIES_BCE)}")

    if not forzar and not esta_desactualizada(serie_id, max_age_days, db_path):
        print(f"[bce] {serie_id} al día, no se descarga.")
        return True

    cfg = SERIES_BCE[serie_id]
    serie = _descargar_serie_bce(cfg["dataflow"], cfg["clave"], cfg["start"])
    if serie is None:
        print(f"[bce] {serie_id}: sin red o respuesta no reconocida, "
              f"se conserva lo que ya hay en el almacén.")
        return False

    n = almacen.escribir(serie, serie_id, estado="oficial",
                          fuente_detalle=f"BCE:{cfg['dataflow']}.{cfg['clave']}",
                          db_path=db_path)
    print(f"[bce] {serie_id} actualizado: {serie.index.min().date()} -> "
          f"{serie.index.max().date()} ({n} obs. escritas)")
    return True


def actualizar_todo(forzar: bool = False, max_age_days: float = 10.0,
                     db_path: Optional[Path] = None) -> int:
    """Refresca las series BCE implementadas. Best-effort: nunca lanza excepción."""
    resultados = {}
    for serie_id in SERIES_BCE:
        try:
            resultados[serie_id] = actualizar_serie(serie_id, forzar, max_age_days, db_path)
        except Exception as e:
            print(f"[bce] Error inesperado en {serie_id}: {e}")
            resultados[serie_id] = False
    return registrar_resultado("bce", resultados)


if __name__ == "__main__":
    forzar = "--forzar" in sys.argv or "--force" in sys.argv
    ok = actualizar_todo(forzar=forzar)
    sys.exit(0 if ok == len(SERIES_BCE) else 1)
