"""
Conector Eurostat (API de difusión, formato JSON-stat 2.0): entorno
exterior (IPCA eurozona, PIB eurozona) y tipos a largo plazo (España,
Alemania) para la prima de riesgo.

Endpoint: https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/{dataset}
Documentación del formato: https://json-stat.org/format/

A diferencia de FRED/BCE (CSV plano), Eurostat devuelve JSON-stat: un
array de valores en orden "row-major" (la última dimensión declarada
en "id" varía más rápido) más metadatos de dimensiones ("dimension")
que dan, para cada una, el orden de sus categorías ("category.index")
y sus etiquetas ("category.label"). Como todas las consultas de este
conector filtran cada dimensión a una sola categoría salvo "time", la
fórmula general de posición se reduce a leer directamente el índice
de la categoría de tiempo — pero se implementa de forma general (con
"strides" por dimensión) para no romper si Eurostat cambia el orden
de las dimensiones en la respuesta.

El array "value" puede venir como lista (huecos = null) o, más
habitual en Eurostat, como objeto disperso {"posición": valor} que
omite las posiciones sin dato: ambas formas están soportadas.

Uso:
    python -m src.datos.conectores.eurostat
    python -m src.datos.conectores.eurostat --forzar
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Optional

import pandas as pd

from .. import almacen
from ._comun import descargar_texto, esta_desactualizada, registrar_resultado

BASE_URL = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data"

SERIES_EUROSTAT = {
    "eurostat_hicp_ea20": {
        "dataset": "prc_hicp_manr",
        "params": {"geo": "EA20", "unit": "RCH_A", "coicop": "CP00"},
    },
    # Índice IPCA eurozona en NIVEL (no la tasa): lo necesita el REER, que
    # compara el nivel de precios España/UE. La tasa (arriba) alimenta
    # inflation_eu; el índice (aquí) alimenta real_exchange_rate/reer_gap.
    "eurostat_hicp_indice_ea20": {
        "dataset": "prc_hicp_midx",
        "params": {"geo": "EA20", "unit": "I15", "coicop": "CP00"},
    },
    "eurostat_pib_eurozona": {
        "dataset": "namq_10_gdp",
        "params": {"geo": "EA20", "na_item": "B1GQ", "s_adj": "SCA", "unit": "CLV10_MEUR"},
    },
    "eurostat_rendimiento_10y_espana": {
        "dataset": "irt_lt_mcby_m",
        "params": {"geo": "ES"},
    },
    "eurostat_rendimiento_10y_alemania": {
        "dataset": "irt_lt_mcby_m",
        "params": {"geo": "DE"},
    },
}


def _url_json(dataset: str, params: dict) -> str:
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{BASE_URL}/{dataset}?format=JSON&lang=EN&{query}"


def _fecha_desde_periodo_eurostat(etiqueta: str) -> Optional[pd.Timestamp]:
    """
    Convierte un identificador de periodo de Eurostat ('2026-Q2',
    '2026-07' o '2026') en la fecha de inicio del periodo. Devuelve
    None si el formato no se reconoce (se descarta ese punto).
    """
    etiqueta = etiqueta.strip()
    m = re.match(r"^(\d{4})-Q([1-4])$", etiqueta)
    if m:
        anio, trimestre = int(m.group(1)), int(m.group(2))
        return pd.Timestamp(year=anio, month=(trimestre - 1) * 3 + 1, day=1)
    m = re.match(r"^(\d{4})-(\d{2})$", etiqueta)
    if m:
        return pd.Timestamp(year=int(m.group(1)), month=int(m.group(2)), day=1)
    m = re.match(r"^(\d{4})$", etiqueta)
    if m:
        return pd.Timestamp(year=int(m.group(1)), month=1, day=1)
    return None


def _categorias_ordenadas(dim_obj: dict) -> list:
    """
    Ids de categoría de una dimensión JSON-stat, en orden de posición.
    'category.index' puede venir como lista (la posición es el índice
    en la lista) o como objeto {id: posición} (más habitual cuando el
    orden no es trivial); se soportan ambas formas.
    """
    idx = dim_obj.get("category", {}).get("index")
    if idx is None:
        return list(dim_obj.get("category", {}).get("label", {}).keys())
    if isinstance(idx, list):
        return list(idx)
    return [k for k, _ in sorted(idx.items(), key=lambda kv: kv[1])]


def _parsear_json_eurostat(texto: str, dataset: str) -> Optional[pd.Series]:
    """
    Parsea una respuesta JSON-stat 2.0 de Eurostat a pd.Series (índice
    = fecha de inicio del periodo). Separado de la descarga para poder
    probarlo sin red, con un JSON de ejemplo.
    """
    try:
        data = json.loads(texto)
    except Exception as e:
        print(f"[eurostat] Respuesta no es JSON válido para {dataset}: {e}")
        return None

    try:
        ids = data.get("id")
        sizes = data.get("size")
        if not ids or not sizes or "time" not in ids:
            print(f"[eurostat] Respuesta sin estructura JSON-stat esperada para {dataset} "
                  f"(¿consulta vacía o parámetros incorrectos?)")
            return None

        dimensiones = data.get("dimension", {})
        n = len(ids)
        # stride[i] = producto de sizes[i+1:] (orden row-major: la última
        # dimensión declarada varía más rápido en el array "value").
        strides = [1] * n
        for i in range(n - 2, -1, -1):
            strides[i] = strides[i + 1] * sizes[i + 1]

        idx_tiempo = ids.index("time")
        categorias_tiempo = _categorias_ordenadas(dimensiones["time"])

        # El resto de dimensiones deben venir filtradas a una sola
        # categoría (así se construyen las URLs de este conector); si
        # alguna trae más de una no hay forma de saber cuál elegir.
        for i, dim_id in enumerate(ids):
            if i != idx_tiempo and sizes[i] != 1:
                print(f"[eurostat] La dimensión '{dim_id}' tiene {sizes[i]} categorías en la "
                      f"respuesta de {dataset}; la consulta debería filtrar a una sola.")
                return None

        valores_raw = data.get("value", {})
        es_lista = isinstance(valores_raw, list)

        fechas, valores = [], []
        for pos, cat_id in enumerate(categorias_tiempo):
            posiciones = [0] * n
            posiciones[idx_tiempo] = pos
            flat = sum(p * s for p, s in zip(posiciones, strides))
            if es_lista:
                v = valores_raw[flat] if flat < len(valores_raw) else None
            else:
                v = valores_raw.get(str(flat))
            if v is None:
                continue
            fecha = _fecha_desde_periodo_eurostat(cat_id)
            if fecha is None:
                continue
            fechas.append(fecha)
            valores.append(v)

        if not fechas:
            print(f"[eurostat] {dataset}: la respuesta no tiene puntos con dato utilizable.")
            return None

        s = pd.Series(valores, index=pd.DatetimeIndex(fechas), dtype=float).sort_index()
        return s[~s.index.duplicated(keep="last")]
    except Exception as e:
        print(f"[eurostat] Error al parsear la respuesta de {dataset}: {e}")
        return None


def actualizar_serie(serie_id: str, forzar: bool = False, max_age_days: float = 20.0,
                      db_path: Optional[Path] = None) -> bool:
    if serie_id not in SERIES_EUROSTAT:
        raise ValueError(f"{serie_id!r} no está entre las series Eurostat implementadas: "
                          f"{sorted(SERIES_EUROSTAT)}")

    if not forzar and not esta_desactualizada(serie_id, max_age_days, db_path):
        print(f"[eurostat] {serie_id} al día, no se descarga.")
        return True

    cfg = SERIES_EUROSTAT[serie_id]
    url = _url_json(cfg["dataset"], cfg["params"])
    texto = descargar_texto(url)
    if texto is None:
        print(f"[eurostat] {serie_id}: sin red, se conserva lo que ya hay en el almacén.")
        return False

    serie = _parsear_json_eurostat(texto, cfg["dataset"])
    if serie is None or serie.empty:
        print(f"[eurostat] {serie_id}: respuesta sin datos utilizables, "
              f"se conserva lo que ya hay en el almacén.")
        return False

    params_txt = "&".join(f"{k}={v}" for k, v in cfg["params"].items())
    n = almacen.escribir(serie, serie_id, estado="oficial",
                          fuente_detalle=f"EUROSTAT:{cfg['dataset']}?{params_txt}",
                          db_path=db_path)
    print(f"[eurostat] {serie_id} actualizado: {serie.index.min().date()} -> "
          f"{serie.index.max().date()} ({n} obs. escritas)")
    return True


def actualizar_todo(forzar: bool = False, max_age_days: float = 20.0,
                     db_path: Optional[Path] = None) -> int:
    """Refresca las cuatro series Eurostat. Best-effort: nunca lanza excepción."""
    resultados = {}
    for serie_id in SERIES_EUROSTAT:
        try:
            resultados[serie_id] = actualizar_serie(serie_id, forzar, max_age_days, db_path)
        except Exception as e:
            print(f"[eurostat] Error inesperado en {serie_id}: {e}")
            resultados[serie_id] = False
    return registrar_resultado("eurostat", resultados)


if __name__ == "__main__":
    forzar = "--forzar" in sys.argv or "--force" in sys.argv
    ok = actualizar_todo(forzar=forzar)
    sys.exit(0 if ok == len(SERIES_EUROSTAT) else 1)
