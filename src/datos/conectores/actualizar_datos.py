"""
Punto de entrada único de la Fase 2: actualiza todas las fuentes que ya
tienen conector escrito.

Uso:
    python -m src.datos.conectores.actualizar_datos                     # todas, con caché
    python -m src.datos.conectores.actualizar_datos --forzar            # ignora la caché
    python -m src.datos.conectores.actualizar_datos --fuente eurostat   # solo una fuente

El conector de INE (siguiente tramo de la fase 2) se añade aquí en el
mismo patrón: expone su propio `actualizar_todo(forzar, max_age_days,
db_path)` y este script solo orquesta. El pipeline actual
(data_pipeline.py) no depende de este script todavía: eso llega con
la Fase 3 (ensamblado).
"""

from __future__ import annotations

import argparse
import sys

from .. import almacen
from . import bce, eurostat, fred, ine, nowcast

FUENTES = {
    "fred": fred,
    "bce": bce,
    "eurostat": eurostat,
    "ine": ine,
    "nowcast": nowcast,  # después del INE: encadena sobre el último PIB oficial
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Actualiza el almacén de datos del modelo")
    parser.add_argument("--forzar", action="store_true",
                         help="Ignora la caché por antigüedad y vuelve a descargar todo")
    parser.add_argument("--fuente", choices=sorted(FUENTES) + ["todo"], default="todo",
                         help="Actualizar solo una fuente (por defecto, todas las disponibles)")
    args = parser.parse_args()

    n = almacen.sync_catalogo()
    print(f"[actualizar_datos] Catálogo sincronizado: {n} series declaradas.\n")

    fuentes_a_correr = FUENTES if args.fuente == "todo" else {args.fuente: FUENTES[args.fuente]}

    for nombre, modulo in fuentes_a_correr.items():
        modulo.actualizar_todo(forzar=args.forzar)
        print()

    print("[actualizar_datos] Panel de frescura tras la actualización:")
    fr = almacen.frescura()
    cols = [c for c in ["serie_id", "proveedor", "ultima_fecha", "dias_desde_descarga", "retrasada"]
            if c in fr.columns]
    if not fr.empty:
        print(fr[cols].to_string(index=False))
    else:
        print("(sin datos todavía)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
