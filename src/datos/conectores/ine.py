"""
Conector INE (API Tempus3): PIB trimestral (CNTR) y EPA (mercado laboral).

Endpoint: https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/{idTabla}
Documentación: https://www.ine.es/dyngs/DataLab/manual.html?cid=1259945243874

A diferencia de FRED/BCE/Eurostat, aquí NO se filtra por un código de
variable ("tv") conocido de antemano. DATOS_TABLA devuelve TODAS las
series desagregadas de una tabla del INE en una sola respuesta (p.ej.
la EPA por sexo y grupo de edad trae una serie por cada combinación),
y cada una incluye un campo "Nombre" en texto libre que describe la
combinación exacta (p.ej. "Ambos sexos. 16 y más años. Tasa de paro.
España."). Este conector pide la tabla completa y selecciona la única
serie cuyo "Nombre" contiene todos los fragmentos de texto requeridos
(ver SERIES_INE) sin contener ninguno de los fragmentos excluidos.

Si no hay exactamente una coincidencia, no se adivina: se avisa y se
listan los "Nombre" recibidos, para poder ajustar el criterio con el
texto real que devuelve la tabla. Esto sustituye a resolver de
antemano el código "tv" exacto (que no se pudo confirmar sin acceso
en vivo a servicios.ine.es desde este entorno) y es, además, más
robusto ante cambios de codificación interna del INE entre tablas.

La fecha de cada punto se toma del campo "Fecha" (epoch en
milisegundos, documentado y estable en Tempus3) y se redondea al
primer día del trimestre correspondiente, en vez de interpretar el
código de periodo ("FK_Periodo"), cuya numeración exacta no está
confirmada para estas tablas.

El IPC (tabla 76130) no está aquí: sigue sirviéndose del script ya
validado (ver docs/02_fuentes_datos_y_variables.md); su migración a
este mismo patrón de conector es trabajo pendiente de menor prioridad
porque esa parte del pipeline ya funciona.

Uso:
    python -m src.datos.conectores.ine
    python -m src.datos.conectores.ine --forzar
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import pandas as pd

from .. import almacen
from ._comun import descargar_texto, esta_desactualizada, registrar_resultado

BASE_URL = "https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA"

# incluye: fragmentos (insensibles a mayúsculas) que TODOS deben aparecer
# en "Nombre" para identificar la serie. excluye: si aparece cualquiera,
# se descarta (para evitar, p.ej., coger el "no ajustado" al buscar el
# ajustado de estacionalidad y calendario).
SERIES_INE = {
    # Criterios afinados 2026-09-19 contra los "Nombre" reales que devuelve
    # cada tabla (ver la corrida de diagnóstico). Dos aprendizajes clave:
    #  - "total" a secas casa con "Total Nacional" en TODAS las series, así
    #    que para fijar la categoría "Total" (edad, etc.) hay que anclarla a
    #    lo que la precede, p.ej. "ambos sexos. total".
    #  - El INE escribe "ajustadOS de estacionalidad" (plural, concordando
    #    con "Datos"), no "ajustado"; y "no ajustados" contiene a "ajustados",
    #    de ahí el exclue explícito.
    "ine_pib_real_espana": {
        "tabla": 67822,
        "incluye": ["producto interior bruto a precios de mercado", "dato base",
                    "encadenad", "ajustados de estacionalidad"],
        "excluye": ["no ajustados"],
        "frecuencia": "Q",
        "nult": 200,
    },
    "ine_epa_tasa_paro": {
        "tabla": 65219,
        "incluye": ["ambos sexos. total"],  # edad = Total, no un grupo de edad
        "excluye": [],
        "frecuencia": "Q",
        "nult": 150,
    },
    "ine_epa_ocupados": {
        "tabla": 65109,
        "incluye": ["ambos sexos. total", "valor absoluto"],  # niveles, no %
        "excluye": [],
        "frecuencia": "Q",
        "nult": 150,
    },
    "ine_epa_activos": {
        "tabla": 65080,
        "incluye": ["ambos sexos. total", "valor absoluto"],
        "excluye": [],
        "frecuencia": "Q",
        "nult": 150,
    },
    "ine_epa_pob16mas": {
        "tabla": 65063,
        # Gran total: edad=Total, relación=Total, estado civil=Total.
        "incluye": ["ambos sexos. total. total. total", "valor absoluto"],
        "excluye": [],
        "frecuencia": "Q",
        "nult": 150,
    },

    # --- IPC, tabla 76130 (grupos especiales), mensual, se guarda el ÍNDICE;
    #     la media trimestral y la tasa interanual las hace el ensamblado.
    #     Nombres confirmados por --listar 76130 el 2026-09-19. En cada grupo
    #     conviven 4 filas (Índice / Variación mensual / anual / en lo que va
    #     de año); los criterios anclan la fila "Índice".
    "ine_ipc_general": {
        "tabla": 76130,
        "incluye": ["índice general"],
        "excluye": ["variación"],
        "frecuencia": "M",
        "nult": 400,
    },
    "ine_ipc_subyacente": {
        "tabla": 76130,
        "incluye": ["subyacente"],
        "excluye": ["variación"],
        "frecuencia": "M",
        "nult": 400,
    },
    "ine_ipc_servicios": {
        "tabla": 76130,
        "incluye": ["servicios. índice"],
        "excluye": ["sin"],  # descarta "Servicios sin alquiler..." y "General sin servicios..."
        "frecuencia": "M",
        "nult": 400,
    },
    "ine_ipc_bienes_industriales": {
        "tabla": 76130,
        "incluye": ["bienes industriales. índice"],  # el agregado, no duraderos/semiduraderos/etc.
        "excluye": [],
        "frecuencia": "M",
        "nult": 400,
    },
    "ine_ipc_energia": {
        "tabla": 76130,
        "incluye": ["productos energéticos. índice"],
        "excluye": ["sin", "alimentos"],  # descarta "...sin productos energéticos" y "Alimentos ... y productos energéticos"
        "frecuencia": "M",
        "nult": 400,
    },
    "ine_ipc_alimentos": {
        "tabla": 76130,
        # Alimentos NO elaborados: los elaborados ya van dentro de la subyacente,
        # así que este es el complemento correcto del núcleo (ver nota al usuario).
        "incluye": ["alimentos sin elaboración. índice"],
        "excluye": [],
        "frecuencia": "M",
        "nult": 400,
    },
}


def _url_json(tabla: int, nult: int) -> str:
    return f"{BASE_URL}/{tabla}?nult={nult}"


def _cumple_criterios(nombre: str, incluye: list, excluye: list) -> bool:
    nombre_low = (nombre or "").lower()
    if not all(frag.lower() in nombre_low for frag in incluye):
        return False
    return not any(frag.lower() in nombre_low for frag in excluye)


def _seleccionar_serie(series_tabla: list, incluye: list, excluye: list,
                        serie_id: str) -> Optional[dict]:
    candidatas = [s for s in series_tabla if _cumple_criterios(s.get("Nombre", ""), incluye, excluye)]
    if len(candidatas) == 1:
        return candidatas[0]

    if not candidatas:
        print(f"[ine] {serie_id}: ninguna serie de la tabla cumple incluye={incluye} "
              f"excluye={excluye}. 'Nombre' recibidos en la tabla (hasta 80):")
        listado = series_tabla
    else:
        print(f"[ine] {serie_id}: {len(candidatas)} series cumplen incluye={incluye} a la vez "
              f"(debería ser una sola); afina el criterio. Coincidencias:")
        listado = candidatas

    for s in listado[:80]:
        print(f"    - {s.get('Nombre')!r} (Id={s.get('Id')})")
    return None


def _parsear_datos_tabla(texto: str, incluye: list, excluye: list,
                          serie_id: str, frecuencia: str = "Q") -> Optional[pd.Series]:
    """
    Parsea una respuesta DATOS_TABLA del INE y devuelve la serie que
    cumple los criterios como pd.Series (índice = inicio de trimestre).
    Separado de la descarga para poder probarlo sin red.
    """
    try:
        data = json.loads(texto)
    except Exception as e:
        print(f"[ine] Respuesta no es JSON válido para {serie_id}: {e}")
        return None

    if isinstance(data, dict):
        # La API devuelve un único objeto (no una lista) cuando la tabla
        # solo contiene una serie; se normaliza a lista de un elemento.
        data = [data]
    if not isinstance(data, list):
        print(f"[ine] Respuesta con forma inesperada para {serie_id}: {type(data)}")
        return None

    serie_obj = _seleccionar_serie(data, incluye, excluye, serie_id)
    if serie_obj is None:
        return None

    fechas, valores = [], []
    for punto in serie_obj.get("Data", []):
        valor = punto.get("Valor")
        fecha_ms = punto.get("Fecha")
        if valor is None or fecha_ms is None:
            continue
        # El INE codifica la fecha del periodo como epoch en ms tomando la
        # medianoche de Madrid (UTC+1/+2); en UTC eso cae 1-2 h ANTES, en el
        # último día del trimestre anterior, y un floor directo desplazaba
        # toda la serie un trimestre hacia atrás (detectado 2026-09-19: la
        # tasa de paro y el PIB salían corridos un trimestre respecto a la
        # realidad). Sumar 5 días antes de redondear al inicio de trimestre
        # neutraliza el desfase horario sin cruzar de trimestre: el INE fecha
        # estos datos al INICIO del periodo, nunca al final. Asume frecuencia
        # trimestral (todas las series de SERIES_INE lo son).
        d = pd.to_datetime(fecha_ms, unit="ms") + pd.Timedelta(days=5)
        if frecuencia.upper() == "M":
            d = pd.Timestamp(year=d.year, month=d.month, day=1)
        else:  # trimestral: inicio del trimestre
            d = pd.Timestamp(year=d.year, month=((d.month - 1) // 3) * 3 + 1, day=1)
        fechas.append(d)
        valores.append(valor)

    if not fechas:
        print(f"[ine] {serie_id}: la serie identificada no tiene puntos con dato.")
        return None

    s = pd.Series(valores, index=pd.DatetimeIndex(fechas), dtype=float).sort_index()
    return s[~s.index.duplicated(keep="last")]


def actualizar_serie(serie_id: str, forzar: bool = False, max_age_days: float = 60.0,
                      db_path: Optional[Path] = None) -> bool:
    if serie_id not in SERIES_INE:
        raise ValueError(f"{serie_id!r} no está entre las series INE implementadas: "
                          f"{sorted(SERIES_INE)}")

    if not forzar and not esta_desactualizada(serie_id, max_age_days, db_path):
        print(f"[ine] {serie_id} al día, no se descarga.")
        return True

    cfg = SERIES_INE[serie_id]
    texto = descargar_texto(_url_json(cfg["tabla"], cfg["nult"]))
    if texto is None:
        print(f"[ine] {serie_id}: sin red, se conserva lo que ya hay en el almacén.")
        return False

    serie = _parsear_datos_tabla(texto, cfg["incluye"], cfg["excluye"], serie_id,
                                  frecuencia=cfg.get("frecuencia", "Q"))
    if serie is None or serie.empty:
        print(f"[ine] {serie_id}: no se pudo identificar la serie en la tabla {cfg['tabla']}, "
              f"se conserva lo que ya hay en el almacén.")
        return False

    n = almacen.escribir(serie, serie_id, estado="oficial",
                          fuente_detalle=f"INE:Tempus3 tabla {cfg['tabla']}",
                          db_path=db_path)
    print(f"[ine] {serie_id} actualizado: {serie.index.min().date()} -> "
          f"{serie.index.max().date()} ({n} obs. escritas)")
    return True


def actualizar_todo(forzar: bool = False, max_age_days: float = 60.0,
                     db_path: Optional[Path] = None) -> int:
    """Refresca PIB + EPA. Best-effort: nunca lanza excepción."""
    resultados = {}
    for serie_id in SERIES_INE:
        try:
            resultados[serie_id] = actualizar_serie(serie_id, forzar, max_age_days, db_path)
        except Exception as e:
            print(f"[ine] Error inesperado en {serie_id}: {e}")
            resultados[serie_id] = False
    return registrar_resultado("ine", resultados)


def listar_tabla(tabla: int, nult: int = 1) -> None:
    """Vuelca todos los 'Nombre' de una tabla del INE, para escribir los
    criterios de selección con la redacción real. Uso:
        python -m src.datos.conectores.ine --listar 76130
    """
    texto = descargar_texto(_url_json(tabla, nult))
    if texto is None:
        print(f"[ine] No se pudo descargar la tabla {tabla} (sin red).")
        return
    try:
        data = json.loads(texto)
    except Exception as e:
        print(f"[ine] Respuesta no válida para la tabla {tabla}: {e}")
        return
    if isinstance(data, dict):
        data = [data]
    print(f"[ine] Tabla {tabla}: {len(data)} series")
    for s in data:
        print(f"  - {s.get('Nombre')!r}")


if __name__ == "__main__":
    if "--listar" in sys.argv:
        i = sys.argv.index("--listar")
        tabla = int(sys.argv[i + 1])
        listar_tabla(tabla)
        sys.exit(0)
    forzar = "--forzar" in sys.argv or "--force" in sys.argv
    ok = actualizar_todo(forzar=forzar)
    sys.exit(0 if ok == len(SERIES_INE) else 1)
