"""
Pruebas de los conectores (Fase 2), sin red.

Este entorno de desarrollo no tiene salida a fred.stlouisfed.org ni a
data-api.ecb.europa.eu (confirmado: la conexión da 403 en el proxy),
así que estas pruebas no verifican que las claves de serie sean
correctas contra los servidores reales — eso solo se puede comprobar
la primera vez que esto corra con red real, en la máquina del usuario.
Lo que sí prueban, con texto de ejemplo en el formato real de cada
proveedor, es que el análisis (parseo) y la escritura en el almacén
son correctos y no rompen ante NaN o columnas con mayúsculas distintas.

Uso:
    python -m src.datos.conectores.test_conectores
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pandas as pd

from .. import almacen
from . import bce, eurostat, fred, ine, nowcast

CSV_FRED_EJEMPLO = """DATE,DCOILBRENTEU
2026-09-10,115.20
2026-09-11,118.06
2026-09-12,.
2026-09-15,130.80
"""

CSV_BCE_EJEMPLO = """KEY,FREQ,REF_AREA,CURRENCY,CURRENCY_DENOM,EXR_TYPE,EXR_SUFFIX,TIME_PERIOD,OBS_VALUE,OBS_STATUS
EXR.D.USD.EUR.SP00.A,D,USD,EUR,SP00,A,,2026-09-10,1.0812,A
EXR.D.USD.EUR.SP00.A,D,USD,EUR,SP00,A,,2026-09-11,1.0805,A
EXR.D.USD.EUR.SP00.A,D,USD,EUR,SP00,A,,2026-09-12,,A
EXR.D.USD.EUR.SP00.A,D,USD,EUR,SP00,A,,2026-09-15,1.0790,A
"""

# JSON-stat 2.0 (Eurostat). "value" como objeto disperso {posición: valor}:
# falta la clave "1" (2025-Q4) a propósito, simulando un hueco de la serie.
# category.index viene como objeto {id: posición} -- la forma más habitual
# quee entrega Eurostat cuando el orden de categorías no es trivial.
JSON_EUROSTAT_PIB_EJEMPLO = json.dumps({
    "version": "2.0",
    "class": "dataset",
    "id": ["freq", "unit", "s_adj", "na_item", "geo", "time"],
    "size": [1, 1, 1, 1, 1, 4],
    "dimension": {
        "freq": {"category": {"index": {"Q": 0}}},
        "unit": {"category": {"index": {"CLV10_MEUR": 0}}},
        "s_adj": {"category": {"index": {"SCA": 0}}},
        "na_item": {"category": {"index": {"B1GQ": 0}}},
        "geo": {"category": {"index": {"EA20": 0}}},
        "time": {"category": {"index": {
            "2025-Q3": 0, "2025-Q4": 1, "2026-Q1": 2, "2026-Q2": 3,
        }}},
    },
    "value": {"0": 2950000.0, "2": 2980000.0, "3": 3005000.0},
})

# JSON-stat 2.0 (Eurostat), variante: category.index como LISTA (la
# posición es el índice en la lista) y "value" como lista con null para
# el hueco -- la otra forma que permite el estándar.
JSON_EUROSTAT_TASA_EJEMPLO = json.dumps({
    "version": "2.0",
    "class": "dataset",
    "id": ["freq", "geo", "time"],
    "size": [1, 1, 3],
    "dimension": {
        "freq": {"category": {"index": {"M": 0}}},
        "geo": {"category": {"index": {"ES": 0}}},
        "time": {"category": {"index": ["2026-05", "2026-06", "2026-07"]}},
    },
    "value": [4.10, None, 4.25],
})


def _db_temporal() -> Path:
    return Path(tempfile.mkdtemp()) / "macro_test.db"


def test_parseo_fred_ignora_huecos():
    s = fred._parsear_csv_fred(CSV_FRED_EJEMPLO, "DCOILBRENTEU")
    assert s is not None
    assert len(s) == 3  # la fila con '.' se descarta
    assert round(s.iloc[-1], 2) == 130.80
    print("[OK] parseo FRED: descarta huecos ('.') y conserva el resto")


def test_parseo_bce_encuentra_columnas_por_nombre():
    s = bce._parsear_csv_bce(CSV_BCE_EJEMPLO, "EXR", "D.USD.EUR.SP00.A")
    assert s is not None
    assert len(s) == 3  # la fila con OBS_VALUE vacío se descarta
    assert round(s.iloc[-1], 4) == 1.0790
    print("[OK] parseo BCE: localiza TIME_PERIOD/OBS_VALUE y descarta vacíos")


def test_fred_escribe_en_almacen_de_forma_idempotente():
    db = _db_temporal()
    almacen.sync_catalogo(db_path=db)
    s = fred._parsear_csv_fred(CSV_FRED_EJEMPLO, "DCOILBRENTEU")
    n1 = almacen.escribir(s, "fred_brent", fuente_detalle="TEST", db_path=db)
    n2 = almacen.escribir(s, "fred_brent", fuente_detalle="TEST", db_path=db)
    assert n1 == n2 == 3
    leido = almacen.leer("fred_brent", db_path=db)
    assert len(leido) == 3
    print("[OK] escritura de una serie FRED parseada es idempotente")


def test_esta_desactualizada_antes_y_despues_de_escribir():
    from ._comun import esta_desactualizada
    db = _db_temporal()
    almacen.sync_catalogo(db_path=db)
    assert esta_desactualizada("fred_brent", max_age_days=7, db_path=db) is True
    s = fred._parsear_csv_fred(CSV_FRED_EJEMPLO, "DCOILBRENTEU")
    almacen.escribir(s, "fred_brent", db_path=db)
    assert esta_desactualizada("fred_brent", max_age_days=7, db_path=db) is False
    assert esta_desactualizada("fred_brent", max_age_days=-1, db_path=db) is True  # umbral absurdo, fuerza refresco
    print("[OK] esta_desactualizada() distingue serie sin datos, fresca y forzable")


def test_parseo_eurostat_categoria_dict_y_valor_disperso():
    s = eurostat._parsear_json_eurostat(JSON_EUROSTAT_PIB_EJEMPLO, "namq_10_gdp")
    assert s is not None
    assert len(s) == 3  # 2025-Q4 (hueco en el objeto disperso) se descarta
    assert s.index[0] == pd.Timestamp("2025-07-01")   # 2025-Q3
    assert s.index[-1] == pd.Timestamp("2026-04-01")  # 2026-Q2
    assert round(s.iloc[-1], 0) == 3005000
    print("[OK] parseo Eurostat: category.index como dict, value como objeto disperso")


def test_parseo_eurostat_categoria_lista_y_valor_lista_con_null():
    s = eurostat._parsear_json_eurostat(JSON_EUROSTAT_TASA_EJEMPLO, "irt_lt_mcby_m")
    assert s is not None
    assert len(s) == 2  # el hueco (null en la lista) se descarta
    assert s.index[0] == pd.Timestamp("2026-05-01")
    assert round(s.iloc[-1], 2) == 4.25
    print("[OK] parseo Eurostat: category.index como lista, value como lista con null")


def test_eurostat_escribe_en_almacen_de_forma_idempotente():
    db = _db_temporal()
    almacen.sync_catalogo(db_path=db)
    s = eurostat._parsear_json_eurostat(JSON_EUROSTAT_PIB_EJEMPLO, "namq_10_gdp")
    n1 = almacen.escribir(s, "eurostat_pib_eurozona", fuente_detalle="TEST", db_path=db)
    n2 = almacen.escribir(s, "eurostat_pib_eurozona", fuente_detalle="TEST", db_path=db)
    assert n1 == n2 == 3
    leido = almacen.leer("eurostat_pib_eurozona", db_path=db)
    assert len(leido) == 3
    print("[OK] escritura de una serie Eurostat parseada es idempotente")


def _punto_ine(fecha_str: str, valor: float) -> dict:
    return {"Fecha": int(pd.Timestamp(fecha_str).value // 10 ** 6), "Valor": valor}


def _tabla_ine_epa_ejemplo() -> str:
    # DATOS_TABLA devuelve una lista con TODAS las desagregaciones de la
    # tabla; solo "Ambos sexos. ... Total." es la que este conector debe
    # elegir (Hombres/Mujeres se descartan por no cumplir el criterio).
    return json.dumps([
        {
            "Id": 1, "Nombre": "Hombres. 16 y más años. Tasa de paro. España.",
            "Data": [_punto_ine("2026-01-15", 11.2), _punto_ine("2026-04-15", 10.9)],
        },
        {
            "Id": 2, "Nombre": "Mujeres. 16 y más años. Tasa de paro. España.",
            "Data": [_punto_ine("2026-01-15", 13.5), _punto_ine("2026-04-15", 13.1)],
        },
        {
            "Id": 3, "Nombre": "Ambos sexos. Total. Tasa de paro. España.",
            "Data": [_punto_ine("2026-01-15", 12.30), _punto_ine("2026-04-20", 11.95)],
        },
    ])


def _tabla_ine_pib_ejemplo() -> str:
    return json.dumps([
        {
            "Id": 10,
            "Nombre": "PIB pm. Oferta. Índices de volumen encadenado. "
                      "Dato no ajustado de estacionalidad y calendario.",
            "Data": [_punto_ine("2026-04-01", 118.4)],
        },
        {
            "Id": 11,
            "Nombre": "PIB pm. Oferta. Índices de volumen encadenado. "
                      "Dato ajustado de estacionalidad y calendario.",
            "Data": [_punto_ine("2026-01-01", 119.0), _punto_ine("2026-04-01", 119.6)],
        },
    ])


def test_ine_selecciona_la_serie_ambos_sexos_total_entre_varias():
    s = ine._parsear_datos_tabla(_tabla_ine_epa_ejemplo(), ["ambos sexos", "total"], [],
                                  "ine_epa_tasa_paro")
    assert s is not None
    assert len(s) == 2
    assert round(s.iloc[0], 2) == 12.30  # 2026-Q1 (15 y 20 de enero/abril caen en su trimestre)
    assert round(s.iloc[-1], 2) == 11.95
    assert list(s.index) == [pd.Timestamp("2026-01-01"), pd.Timestamp("2026-04-01")]
    print("[OK] INE: selecciona 'Ambos sexos'+'Total' entre varias series de la tabla")


def test_ine_excluye_no_ajustado_al_buscar_el_ajustado():
    s = ine._parsear_datos_tabla(_tabla_ine_pib_ejemplo(), ["encaden", "ajustado de estacionalidad"],
                                  ["no ajustado"], "ine_pib_real_espana")
    assert s is not None
    assert len(s) == 2  # solo la serie "ajustado", no la "no ajustado"
    assert round(s.iloc[-1], 1) == 119.6
    print("[OK] INE: 'excluye' descarta el 'no ajustado' al buscar el ajustado")


def test_ine_sin_coincidencia_unica_no_adivina():
    # Ningún "Nombre" contiene "trimestre natural": cero coincidencias -> None.
    assert ine._parsear_datos_tabla(_tabla_ine_epa_ejemplo(), ["trimestre natural"], [],
                                     "test") is None
    # "españa" está en las tres series de la tabla EPA de ejemplo: >1 coincidencia -> None.
    assert ine._parsear_datos_tabla(_tabla_ine_epa_ejemplo(), ["españa"], [], "test") is None
    print("[OK] INE: cero o varias coincidencias no se resuelven a ciegas (devuelve None)")


# Nombres COPIADOS de la corrida de diagnóstico real (2026-09-19), un
# objetivo + varios señuelos por tabla, para verificar que los criterios
# de producción (SERIES_INE) seleccionan exactamente la serie correcta.
# Estos son los nombres que en su día hicieron fallar a los criterios
# ingenuos ("total" casando con "Total Nacional", "ajustado" en singular).
NOMBRES_REALES_INE = {
    65219: [
        "Total Nacional. Tasa de paro de la poblacion. Ambos sexos. Total. ",           # <- objetivo
        "Total Nacional. Tasa de paro de la poblacion. Ambos sexos. De 16 a 19 anos. ",
        "Tasa de paro de la poblacion. Total Nacional. Ambos sexos. De 25 a 29 anos. ",
        "Total Nacional. Tasa de paro de la poblacion. Hombres. Total. ",
    ],
    65109: [
        "Total Nacional. Ambos sexos. Total. Ocupados. Valor absoluto. ",               # <- objetivo
        "Ocupados. Total Nacional. Ambos sexos. Total. Porcentaje. ",
        "Total Nacional. Ambos sexos. De 16 a 19 anos. Ocupados. Valor absoluto. ",
    ],
    65080: [
        "Total Nacional. Ambos sexos. Total. Activos. Valor absoluto. ",                # <- objetivo
        "Activos. Total Nacional. Ambos sexos. Total. Porcentaje. ",
        "Total Nacional. Ambos sexos. De 20 a 24 anos. Activos. Valor absoluto. ",
    ],
    65063: [
        "Total Nacional. Ambos sexos. Total. Total. Total. Valor absoluto. ",           # <- objetivo
        "Total Nacional. Ambos sexos. Total. Total. Solteros/Solteras. Valor absoluto. ",
        "Total Nacional. Ambos sexos. Total. Persona de referencia. Total. Valor absoluto. ",
    ],
    67822: [
        "Total Nacional. Datos ajustados de estacionalidad y calendario. Producto interior bruto a precios de mercado. Dato base. Indices de volumen encadenados. ",   # <- objetivo
        "Total Nacional. Datos no ajustados de estacionalidad y calendario. Producto interior bruto a precios de mercado. Dato base. Indices de volumen encadenados. ",
        "Total Nacional. Datos ajustados de estacionalidad y calendario. Producto interior bruto a precios de mercado. Variacion trimestral. Indices de volumen encadenados. ",
        "Total Nacional. Datos ajustados de estacionalidad y calendario. VABpb Industria (B-E, CNAE 2009). Dato base. Indices de volumen encadenados. ",
    ],
}


NOMBRES_REALES_IPC_76130 = [
    "Nacional. Índice general. Índice. ",                                                    # general (obj)
    "Nacional. Índice general. Variación anual. ",
    "Nacional. Subyacente: General sin alimentos no elaborados ni productos energéticos. Índice. ",  # subyacente (obj)
    "Nacional. Subyacente: General sin alimentos no elaborados ni productos energéticos. Variación anual. ",
    "Nacional. Servicios. Índice. ",                                                         # servicios (obj)
    "Nacional. Servicios sin alquiler de vivienda. Índice. ",
    "Nacional. General sin servicios (incluye alquiler de vivienda). Índice. ",
    "Nacional. Bienes industriales. Índice. ",                                               # bienes ind (obj)
    "Nacional. Bienes industriales duraderos. Índice. ",
    "Nacional. Bienes industriales sin productos energéticos. Índice. ",
    "Nacional. Productos energéticos. Índice. ",                                             # energía (obj)
    "Nacional. Alimentos no elaborados y productos energéticos. Índice. ",
    "Nacional. General sin productos energéticos. Índice. ",
    "Nacional. Alimentos sin elaboración. Índice. ",                                         # alimentos (obj)
    "Nacional. Alimentos elaborados. Índice. ",
    "Nacional. Alimentos, bebidas y tabaco. Índice. ",
]

IPC_OBJETIVOS = {
    "ine_ipc_general": "Nacional. Índice general. Índice. ",
    "ine_ipc_subyacente": "Nacional. Subyacente: General sin alimentos no elaborados ni productos energéticos. Índice. ",
    "ine_ipc_servicios": "Nacional. Servicios. Índice. ",
    "ine_ipc_bienes_industriales": "Nacional. Bienes industriales. Índice. ",
    "ine_ipc_energia": "Nacional. Productos energéticos. Índice. ",
    "ine_ipc_alimentos": "Nacional. Alimentos sin elaboración. Índice. ",
}


def test_ipc_criterios_seleccionan_una_sola_serie_de_76130():
    for serie_id, objetivo in IPC_OBJETIVOS.items():
        cfg = ine.SERIES_INE[serie_id]
        casan = [n for n in NOMBRES_REALES_IPC_76130
                 if ine._cumple_criterios(n, cfg["incluye"], cfg["excluye"])]
        assert casan == [objetivo], f"{serie_id}: esperaba [{objetivo!r}], casaron {casan}"
    print("[OK] IPC: cada criterio fija su única fila 'Índice' entre los grupos de 76130")


def test_ine_criterios_reales_seleccionan_una_sola_serie():
    # El primer nombre de cada lista es el objetivo (indice 0); ninguna otra
    # debe cumplir el criterio de produccion de SERIES_INE.
    tabla_a_serie = {cfg["tabla"]: sid for sid, cfg in ine.SERIES_INE.items()}
    for tabla, nombres in NOMBRES_REALES_INE.items():
        serie_id = tabla_a_serie[tabla]
        cfg = ine.SERIES_INE[serie_id]
        casan = [n for n in nombres
                 if ine._cumple_criterios(n, cfg["incluye"], cfg["excluye"])]
        assert casan == [nombres[0]], (
            f"tabla {tabla} ({serie_id}): esperaba solo el objetivo, "
            f"casaron {casan}")
    print("[OK] INE: los criterios reales de SERIES_INE fijan una unica serie por tabla")


def test_ine_fecha_en_frontera_de_zona_horaria_cae_en_el_trimestre_correcto():
    # Un dato de 2026-Q1 cuyo epoch, por la medianoche de Madrid, queda en UTC
    # a las 23:00 del 31-dic-2025 (último día de 2025-Q4). Sin el margen se
    # archivaría como 2025-Q4; con el margen debe caer en 2026-Q1.
    ms = int(pd.Timestamp("2025-12-31 23:00:00").value // 10 ** 6)
    tabla = json.dumps([{"Id": 1, "Nombre": "Ambos sexos. Total. Valor absoluto.",
                         "Data": [{"Fecha": ms, "Valor": 42.0}]}])
    s = ine._parsear_datos_tabla(tabla, ["ambos sexos. total"], [], "test")
    assert s is not None and len(s) == 1
    assert s.index[0] == pd.Timestamp("2026-01-01"), f"cayó en {s.index[0]}"
    print("[OK] INE: una fecha en la frontera de zona horaria se archiva en su trimestre real")


def test_ine_normaliza_objeto_unico_a_lista():
    # Cuando la tabla solo tiene una serie, la API devuelve un objeto, no una lista.
    unico = json.dumps({"Id": 1, "Nombre": "Ambos sexos. Total.",
                         "Data": [_punto_ine("2026-01-10", 5.0)]})
    s = ine._parsear_datos_tabla(unico, ["ambos sexos"], [], "test")
    assert s is not None and len(s) == 1
    print("[OK] INE: normaliza una respuesta de objeto único a lista de una serie")


def test_nowcast_encadena_qoq_sobre_el_ultimo_oficial():
    # t6: última fila -> trimestre en curso 2026Q3 con QoQ +0,5%.
    df_t6 = pd.DataFrame({"fecha": ["2026-08-01", "2026-09-01"],
                          "trim": ["2026Q3", "2026Q3"],
                          "pe": [0.4, 0.5]})
    # t3: fila "siguiente ... actual" -> QoQ del T+1 = +0,3%.
    df_t3 = pd.DataFrame({"desc": ["Trimestre siguiente - semana actual"], "val": [0.3]})
    s = nowcast._calcular_nowcast(df_t6, df_t3, pd.Timestamp("2026-04-01"), 126.0)
    assert s is not None
    assert list(s.index) == [pd.Timestamp("2026-07-01"), pd.Timestamp("2026-10-01")]
    assert round(s.iloc[0], 4) == round(126.0 * 1.005, 4)            # 2026Q3
    assert round(s.iloc[1], 4) == round(126.0 * 1.005 * 1.003, 4)    # 2026Q4
    print("[OK] nowcast: encadena el QoQ del tracker sobre el último índice oficial")


def test_nowcast_sin_trimestre_nuevo_no_escribe():
    # El 'trimestre en curso' ya es el último oficial y no hay t3 -> nada nuevo.
    df_t6 = pd.DataFrame({"fecha": ["2026-05-01"], "trim": ["2026Q2"], "pe": [0.6]})
    s = nowcast._calcular_nowcast(df_t6, None, pd.Timestamp("2026-04-01"), 126.0)
    assert s is None
    print("[OK] nowcast: no genera filas si no hay trimestre por delante del oficial")


if __name__ == "__main__":
    test_parseo_fred_ignora_huecos()
    test_parseo_bce_encuentra_columnas_por_nombre()
    test_fred_escribe_en_almacen_de_forma_idempotente()
    test_esta_desactualizada_antes_y_despues_de_escribir()
    test_parseo_eurostat_categoria_dict_y_valor_disperso()
    test_parseo_eurostat_categoria_lista_y_valor_lista_con_null()
    test_eurostat_escribe_en_almacen_de_forma_idempotente()
    test_ine_selecciona_la_serie_ambos_sexos_total_entre_varias()
    test_ine_excluye_no_ajustado_al_buscar_el_ajustado()
    test_ine_sin_coincidencia_unica_no_adivina()
    test_ine_criterios_reales_seleccionan_una_sola_serie()
    test_ipc_criterios_seleccionan_una_sola_serie_de_76130()
    test_ine_fecha_en_frontera_de_zona_horaria_cae_en_el_trimestre_correcto()
    test_ine_normaliza_objeto_unico_a_lista()
    test_nowcast_encadena_qoq_sobre_el_ultimo_oficial()
    test_nowcast_sin_trimestre_nuevo_no_escribe()
    print("\nTodas las pruebas de conectores (sin red) pasan.")
