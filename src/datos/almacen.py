"""
Almacén único de datos del modelo Semi-DSGE para España.

Una base SQLite (macro.db) con dos tablas: `catalogo` (el contrato de cada
serie, sincronizado desde catalogo.yaml) y `observaciones` (el dato, en
formato largo, con vintage). Nadie más que este módulo escribe en la base:
los conectores de ingesta (fase 2) llaman a `escribir()`, el ensamblado
(fase 3) llama a `leer()`, y la operación (fase 6) llama a `frescura()`.

Uso típico de un conector:

    from src.datos import almacen
    almacen.sync_catalogo()                       # una vez, al arrancar
    serie = pd.Series(...)                        # índice = fechas, valores
    almacen.escribir(serie, "fred_brent", estado="oficial",
                      fuente_detalle="FRED:DCOILBRENTEU")

Uso típico del ensamblado:

    df = almacen.leer(["ine_ipc_general", "ine_ipc_subyacente"],
                       desde="1995-01-01")
    hist = almacen.leer("ine_pib_real_espana", vintage="2026-06-30")  # as of
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Union

import pandas as pd
import yaml

# ---------------------------------------------------------------------
# Rutas. Este fichero vive en sandbox/src/datos/almacen.py; la base y el
# catálogo YAML son vecinos suyos dentro del proyecto.
# ---------------------------------------------------------------------
_THIS_DIR = Path(__file__).resolve().parent          # .../src/datos
_PROJECT_ROOT = _THIS_DIR.parents[1]                 # .../DGSE

DB_PATH = _PROJECT_ROOT / "data" / "macro.db"
CATALOGO_YAML = _THIS_DIR / "catalogo.yaml"
ESQUEMA_SQL = _THIS_DIR / "esquema.sql"

_ESTADOS_VALIDOS = {"oficial", "provisional", "arrastrado"}


# ---------------------------------------------------------------------
# Conexión y creación del esquema
# ---------------------------------------------------------------------
@contextmanager
def _conectar(db_path: Optional[Path] = None):
    path = Path(db_path) if db_path is not None else DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(path))
    con.execute("PRAGMA foreign_keys = ON;")
    # TRUNCATE en vez del DELETE por defecto (o WAL): sobre carpetas montadas
    # en red o compartidas entre sistemas operativos (p.ej. el puente
    # Plan9/virtiofs que usa el entorno de Claude para leer carpetas de
    # Windows), tanto DELETE como WAL fallan con 'disk I/O error' al hacer
    # commit -DELETE necesita borrar el fichero de journal, WAL necesita
    # mmap de un fichero -wal/-shm, y ninguna de las dos operaciones es
    # fiable en esos montajes-. TRUNCATE solo trunca el journal a tamaño 0,
    # que sí funciona ahí, y es igual de seguro (ACID) en disco local normal.
    con.execute("PRAGMA journal_mode=TRUNCATE;")
    try:
        yield con
        con.commit()
    finally:
        con.close()


def inicializar_esquema(db_path: Optional[Path] = None) -> None:
    """Crea las tablas y vistas si no existen. Idempotente: no borra nada."""
    sql = ESQUEMA_SQL.read_text(encoding="utf-8")
    with _conectar(db_path) as con:
        con.executescript(sql)


# ---------------------------------------------------------------------
# Catálogo: fuente de verdad en YAML, sincronizada a la tabla SQL
# ---------------------------------------------------------------------
def _cargar_catalogo_yaml(path: Optional[Path] = None) -> List[dict]:
    p = Path(path) if path is not None else CATALOGO_YAML
    with open(p, encoding="utf-8") as f:
        doc = yaml.safe_load(f)
    series = doc.get("series", []) if doc else []
    ids = [s["serie_id"] for s in series]
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        raise ValueError(f"serie_id duplicado en catalogo.yaml: {sorted(dupes)}")
    return series


_CAMPOS_CATALOGO = [
    "serie_id", "descripcion", "proveedor", "id_origen", "unidad",
    "frecuencia_origen", "agregacion", "transformacion", "columna_modelo",
    "calendario_publicacion", "retraso_maximo_dias", "activo", "notas",
]


def sync_catalogo(db_path: Optional[Path] = None,
                   yaml_path: Optional[Path] = None) -> int:
    """
    Vuelca catalogo.yaml sobre la tabla `catalogo`. Es la única función que
    escribe en esa tabla: el YAML manda, la tabla es su copia consultable.
    Devuelve el número de series sincronizadas.
    """
    inicializar_esquema(db_path)
    series = _cargar_catalogo_yaml(yaml_path)

    filas = []
    for s in series:
        fila = {campo: s.get(campo) for campo in _CAMPOS_CATALOGO}
        fila["activo"] = 1 if fila.get("activo") in (None, True, 1) else 0
        filas.append(fila)

    placeholders = ", ".join(f":{c}" for c in _CAMPOS_CATALOGO)
    columnas = ", ".join(_CAMPOS_CATALOGO)
    sql = (f"INSERT OR REPLACE INTO catalogo ({columnas}, actualizado_en) "
           f"VALUES ({placeholders}, :actualizado_en)")

    ahora = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    ids_yaml = [f["serie_id"] for f in filas]
    with _conectar(db_path) as con:
        for fila in filas:
            fila["actualizado_en"] = ahora
            con.execute(sql, fila)
        # Podar del catálogo las series que ya no están en el YAML, para que
        # la tabla espeje el fichero (p.ej. al renombrar una serie). Solo se
        # borran las que no tienen observaciones: si tuviera datos, la clave
        # foránea lo impediría y además querríamos conservarlos, así que se
        # dejan y se avisa.
        marcadores = ",".join("?" * len(ids_yaml)) if ids_yaml else "''"
        huerfanas = [r[0] for r in con.execute(
            f"SELECT serie_id FROM catalogo WHERE serie_id NOT IN ({marcadores})",
            ids_yaml).fetchall()]
        for sid in huerfanas:
            con_obs = con.execute(
                "SELECT COUNT(*) FROM observaciones WHERE serie_id=?", (sid,)).fetchone()[0]
            if con_obs == 0:
                con.execute("DELETE FROM catalogo WHERE serie_id=?", (sid,))
            else:
                print(f"[almacen] Aviso: '{sid}' ya no está en el catálogo YAML pero "
                      f"conserva {con_obs} observaciones; se mantiene en la tabla.")
    return len(filas)


def catalogo(db_path: Optional[Path] = None, solo_activas: bool = True) -> pd.DataFrame:
    """Devuelve el catálogo tal como está en la base (sincronizado desde el YAML)."""
    inicializar_esquema(db_path)
    query = "SELECT * FROM catalogo"
    if solo_activas:
        query += " WHERE activo = 1"
    with _conectar(db_path) as con:
        df = pd.read_sql_query(query, con)
    return df


# ---------------------------------------------------------------------
# Escritura de observaciones
# ---------------------------------------------------------------------
def _a_serie_fecha_valor(datos: Union[pd.Series, pd.DataFrame]) -> pd.Series:
    """Normaliza la entrada a una pd.Series indexada por fecha (Timestamp)."""
    if isinstance(datos, pd.DataFrame):
        if datos.shape[1] != 1:
            raise ValueError("Si 'datos' es DataFrame debe tener una sola columna de valor.")
        s = datos.iloc[:, 0]
    else:
        s = datos
    s = s.copy()
    s.index = pd.to_datetime(s.index)
    return s.sort_index()


def escribir(datos: Union[pd.Series, pd.DataFrame],
             serie_id: str,
             estado: str = "oficial",
             vintage: Optional[str] = None,
             fuente_detalle: Optional[str] = None,
             db_path: Optional[Path] = None,
             validar_catalogo: bool = True) -> int:
    """
    Escribe observaciones de una serie. Idempotente: repetir la misma
    llamada dos veces dejará la base igual (INSERT OR REPLACE sobre la
    clave (serie_id, fecha, vintage)).

    Args:
        datos: Serie o DataFrame de una columna, índice = fecha.
        serie_id: debe existir en el catálogo (salvo validar_catalogo=False).
        estado: 'oficial' | 'provisional' | 'arrastrado'.
        vintage: fecha ISO de este vintage; por defecto, hoy (la fecha de
            descarga/estimación). Fijar un vintage pasado sirve para
            recargar histórico con su fecha real de publicación.
        fuente_detalle: texto libre trazable, p.ej. 'FRED:DCOILBRENTEU'.

    Returns:
        Número de filas escritas (tras eliminar NaN).
    """
    if estado not in _ESTADOS_VALIDOS:
        raise ValueError(f"estado debe ser uno de {_ESTADOS_VALIDOS}, recibido {estado!r}")

    inicializar_esquema(db_path)

    if validar_catalogo:
        ids_validos = set(catalogo(db_path, solo_activas=False)["serie_id"])
        if serie_id not in ids_validos:
            raise ValueError(
                f"serie_id {serie_id!r} no está en el catálogo. "
                f"Añádela a catalogo.yaml y corre sync_catalogo() primero, "
                f"o llama con validar_catalogo=False para casos de prueba."
            )

    s = _a_serie_fecha_valor(datos).dropna()
    if s.empty:
        return 0

    vintage_str = vintage or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    descargado_en = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    filas = [
        {
            "serie_id": serie_id,
            "fecha": fecha.strftime("%Y-%m-%d"),
            "vintage": vintage_str,
            "valor": float(valor),
            "estado": estado,
            "fuente_detalle": fuente_detalle,
            "descargado_en": descargado_en,
        }
        for fecha, valor in s.items()
    ]

    sql = """
        INSERT OR REPLACE INTO observaciones
            (serie_id, fecha, vintage, valor, estado, fuente_detalle, descargado_en)
        VALUES
            (:serie_id, :fecha, :vintage, :valor, :estado, :fuente_detalle, :descargado_en)
    """
    with _conectar(db_path) as con:
        con.executemany(sql, filas)
    return len(filas)


# ---------------------------------------------------------------------
# Lectura de observaciones
# ---------------------------------------------------------------------
def leer(series: Union[str, Sequence[str]],
         desde: Optional[str] = None,
         hasta: Optional[str] = None,
         vintage: Optional[str] = None,
         db_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Lee una o varias series como DataFrame ancho (índice=fecha, una
    columna por serie_id).

    Args:
        series: un serie_id o una lista de ellos.
        desde, hasta: filtro de fecha ISO, inclusive.
        vintage: si None, se usa el último vintage conocido de cada
            observación (el estado más actual). Si se da una fecha ISO,
            se reproduce "lo que se sabía" en ese momento: para cada
            (serie, fecha) se toma el vintage más reciente que no sea
            posterior al vintage pedido.

    Returns:
        DataFrame con DatetimeIndex y una columna por serie.
    """
    inicializar_esquema(db_path)
    ids = [series] if isinstance(series, str) else list(series)
    placeholders = ", ".join("?" for _ in ids)

    if vintage is None:
        sql = f"""
            SELECT serie_id, fecha, valor
            FROM observaciones_ultimo_vintage
            WHERE serie_id IN ({placeholders})
        """
        params: list = list(ids)
    else:
        # Última observación conocida A FECHA del vintage pedido, por (serie, fecha).
        sql = f"""
            SELECT o.serie_id, o.fecha, o.valor
            FROM observaciones o
            JOIN (
                SELECT serie_id, fecha, MAX(vintage) AS max_vintage
                FROM observaciones
                WHERE serie_id IN ({placeholders}) AND vintage <= ?
                GROUP BY serie_id, fecha
            ) m ON o.serie_id = m.serie_id AND o.fecha = m.fecha AND o.vintage = m.max_vintage
        """
        params = list(ids) + [vintage]

    # Filtro de fechas aplicado sobre una subconsulta, para que funcione
    # igual en las dos ramas (con o sin vintage) sin duplicar lógica.
    condiciones_extra = []
    if desde:
        condiciones_extra.append(("fecha >= ?", desde))
    if hasta:
        condiciones_extra.append(("fecha <= ?", hasta))

    if condiciones_extra:
        sql_base = f"SELECT * FROM ({sql})"
        clausulas = " AND ".join(c for c, _ in condiciones_extra)
        sql_final = f"{sql_base} WHERE {clausulas} ORDER BY fecha"
        params_final = params + [v for _, v in condiciones_extra]
    else:
        sql_final = f"SELECT * FROM ({sql}) ORDER BY fecha"
        params_final = params

    with _conectar(db_path) as con:
        df_largo = pd.read_sql_query(sql_final, con, params=params_final)

    if df_largo.empty:
        return pd.DataFrame(columns=ids, index=pd.DatetimeIndex([], name="fecha"))

    df_largo["fecha"] = pd.to_datetime(df_largo["fecha"])
    df_ancho = df_largo.pivot(index="fecha", columns="serie_id", values="valor")
    df_ancho = df_ancho.reindex(columns=ids)  # mismo orden que se pidió
    df_ancho.index.name = "fecha"
    return df_ancho.sort_index()


# ---------------------------------------------------------------------
# Frescura (panel de operación, fase 6 lo consume)
# ---------------------------------------------------------------------
def frescura(db_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Última fecha y descarga de cada serie activa, con el retraso en días
    respecto a hoy y si supera el umbral declarado en el catálogo.
    """
    inicializar_esquema(db_path)
    with _conectar(db_path) as con:
        df = pd.read_sql_query("SELECT * FROM ultimo_dato_por_serie", con)

    if df.empty:
        return df

    ahora = pd.Timestamp.now(tz="UTC")
    df["ultima_descarga"] = pd.to_datetime(df["ultima_descarga"], utc=True, errors="coerce")
    df["dias_desde_descarga"] = (ahora - df["ultima_descarga"]).dt.days
    df["retrasada"] = (
        df["retraso_maximo_dias"].notna()
        & df["dias_desde_descarga"].notna()
        & (df["dias_desde_descarga"] > df["retraso_maximo_dias"])
    )
    return df.sort_values("dias_desde_descarga", ascending=False, na_position="first")


def ultima_descarga(serie_id: str, db_path: Optional[Path] = None) -> Optional[pd.Timestamp]:
    """Fecha/hora (UTC) de la escritura más reciente de esta serie, o None si no tiene datos.

    Es lo que usan los conectores para decidir si una serie está desactualizada,
    en vez de mirar la edad de un fichero de caché aparte.
    """
    inicializar_esquema(db_path)
    with _conectar(db_path) as con:
        fila = con.execute(
            "SELECT MAX(descargado_en) FROM observaciones WHERE serie_id = ?",
            (serie_id,),
        ).fetchone()
    if not fila or not fila[0]:
        return None
    return pd.Timestamp(fila[0], tz="UTC")


if __name__ == "__main__":
    n = sync_catalogo()
    print(f"Catálogo sincronizado: {n} series.")
    print(catalogo().to_string(index=False, max_colwidth=40))
