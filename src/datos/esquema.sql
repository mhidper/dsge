-- Esquema del almacén único de datos del modelo Semi-DSGE para España.
-- Dos tablas: el dato observado (observaciones) y su contrato (catalogo).
-- Nada más escribe en esta base: todo pasa por los conectores de ingesta
-- y se lee únicamente a través de src/datos/almacen.py.

PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------------
-- catalogo: el contrato de cada serie. Aquí se declara de dónde sale
-- cada variable y cómo se transforma; el pipeline no vuelve a adivinarlo
-- buscando subcadenas en cabeceras de Excel.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS catalogo (
    serie_id            TEXT PRIMARY KEY,   -- p.ej. 'gdp_real_spain'
    descripcion         TEXT NOT NULL,
    proveedor           TEXT NOT NULL,      -- 'INE' | 'EUROSTAT' | 'BCE' | 'FRED' | 'NOWCAST'
    id_origen           TEXT,               -- identificador de tabla/serie en el proveedor
    unidad              TEXT,
    frecuencia_origen   TEXT NOT NULL,      -- 'D' diaria | 'M' mensual | 'Q' trimestral
    agregacion          TEXT,               -- cómo pasar de frecuencia_origen a trimestral: 'media' | 'ultimo' | NULL si ya es trimestral
    transformacion      TEXT,               -- transformación aplicada por el ensamblado. Vocabulario:
                                             --   'nivel'      dato ya en la unidad final, solo se agrega
                                             --   'yoy_4'      variación interanual t/t-4 sobre el nivel trimestral
                                             --   'hp_gap_ln'  brecha en pp = ciclo de HP(1600) sobre log(nivel) * 100
                                             --   'derivada'   se calcula a partir de otras series (ver notas)
    columna_modelo      TEXT,               -- columna que alimenta en el DataFrame final del modelo (model.py)
    calendario_publicacion TEXT,            -- descripción legible de cuándo se espera dato nuevo, p.ej. 'día ~13 del mes siguiente'
    retraso_maximo_dias INTEGER,            -- umbral que usa la validación de frescura (fase 6)
    activo              INTEGER NOT NULL DEFAULT 1,
    notas               TEXT,
    actualizado_en       TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

-- ---------------------------------------------------------------------
-- observaciones: el dato en sí, en formato largo. Una fila por
-- (serie, fecha, vintage). El vintage permite reproducir cualquier
-- corrida anterior tal como se veía en su momento.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS observaciones (
    serie_id        TEXT NOT NULL REFERENCES catalogo(serie_id),
    fecha           TEXT NOT NULL,      -- ISO 'YYYY-MM-DD', inicio de periodo
    vintage         TEXT NOT NULL,      -- ISO 'YYYY-MM-DD': fecha de publicación/estimación de este valor
    valor           REAL,
    estado          TEXT NOT NULL DEFAULT 'oficial',  -- 'oficial' | 'provisional' | 'arrastrado'
    fuente_detalle  TEXT,               -- p.ej. 'FRED:DCOILBRENTEU' o 'INE:Tempus3:tabla 50902'
    descargado_en   TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    PRIMARY KEY (serie_id, fecha, vintage)
);

CREATE INDEX IF NOT EXISTS idx_obs_serie_fecha ON observaciones(serie_id, fecha);
CREATE INDEX IF NOT EXISTS idx_obs_vintage ON observaciones(vintage);
CREATE INDEX IF NOT EXISTS idx_obs_estado ON observaciones(estado);

-- Vista de conveniencia: último vintage disponible por (serie, fecha),
-- que es lo que casi siempre se quiere al leer "el dato más reciente".
CREATE VIEW IF NOT EXISTS observaciones_ultimo_vintage AS
SELECT o.*
FROM observaciones o
JOIN (
    SELECT serie_id, fecha, MAX(vintage) AS max_vintage
    FROM observaciones
    GROUP BY serie_id, fecha
) m ON o.serie_id = m.serie_id AND o.fecha = m.fecha AND o.vintage = m.max_vintage;

-- Vista de frescura: último dato por serie, comparado con "hoy",
-- para el panel de la fase 6. retraso_dias se calcula en Python
-- (SQLite no tiene julianday con zona horaria fiable para esto),
-- así que esta vista solo deja el último dato y su fecha de descarga.
CREATE VIEW IF NOT EXISTS ultimo_dato_por_serie AS
SELECT
    c.serie_id,
    c.descripcion,
    c.proveedor,
    c.retraso_maximo_dias,
    MAX(o.fecha) AS ultima_fecha,
    (SELECT descargado_en FROM observaciones_ultimo_vintage o2
       WHERE o2.serie_id = c.serie_id
       ORDER BY o2.fecha DESC LIMIT 1) AS ultima_descarga,
    (SELECT estado FROM observaciones_ultimo_vintage o3
       WHERE o3.serie_id = c.serie_id
       ORDER BY o3.fecha DESC LIMIT 1) AS ultimo_estado
FROM catalogo c
LEFT JOIN observaciones_ultimo_vintage o ON o.serie_id = c.serie_id
WHERE c.activo = 1
GROUP BY c.serie_id;
