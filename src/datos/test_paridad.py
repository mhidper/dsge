"""
Prueba de paridad (Fase 3): compara, columna a columna, el panel nuevo
(ensamblado.py, todo desde el almacén y todo real) con el que produce el
pipeline actual (data_pipeline.build_consolidated_dataset, el 'collage' de
xlsx congelados + CSV de override + constantes inventadas).

NO es un test de igualdad: se ESPERAN divergencias, y son la parte
interesante — donde el pipeline viejo usaba datos congelados o valores
inventados (China=0, IPC×0,85, tipo=respaldo fijo), el nuevo pone dato real.
El objetivo es que cada divergencia quede a la vista y explicada, no oculta.

Uso:
    python -m src.datos.test_paridad
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .ensamblado import construir_dataset


def _cargar_viejo() -> pd.DataFrame:
    from ..data_pipeline import build_consolidated_dataset
    # auto_refresh=False: sin red, reproducible; usa lo que haya en disco.
    return build_consolidated_dataset(auto_refresh=False)


def comparar() -> pd.DataFrame:
    nuevo = construir_dataset()
    viejo = _cargar_viejo()

    idx = nuevo.index.intersection(viejo.index)
    comunes = [c for c in nuevo.columns if c in viejo.columns]
    solo_nuevo = [c for c in nuevo.columns if c not in viejo.columns]
    solo_viejo = [c for c in viejo.columns if c not in nuevo.columns]

    filas = []
    for c in comunes:
        a = pd.to_numeric(viejo.loc[idx, c], errors="coerce")
        b = pd.to_numeric(nuevo.loc[idx, c], errors="coerce")
        m = a.notna() & b.notna()
        n = int(m.sum())
        if n == 0:
            filas.append((c, 0, np.nan, np.nan, np.nan, np.nan, np.nan))
            continue
        diff = (b[m] - a[m]).abs()
        corr = a[m].corr(b[m]) if n > 2 else np.nan
        filas.append((c, n, float(diff.mean()), float(diff.max()), corr,
                      float(a[m].iloc[-1]), float(b[m].iloc[-1])))

    rep = pd.DataFrame(filas, columns=[
        "columna", "n", "dif_media_abs", "dif_max_abs", "corr", "ult_viejo", "ult_nuevo"])
    rep = rep.sort_values("dif_media_abs", ascending=False, na_position="last")

    print("=" * 92)
    print(f"PARIDAD  ensamblado.py (nuevo, real)  vs  data_pipeline.py (viejo, collage)")
    print(f"  solapamiento temporal: {idx.min().date()} -> {idx.max().date()} ({len(idx)} trimestres)")
    print(f"  columnas comunes: {len(comunes)} | solo nuevo: {solo_nuevo} | solo viejo: {solo_viejo}")
    print("=" * 92)
    with pd.option_context("display.width", 120, "display.max_rows", 100):
        print(rep.to_string(index=False,
              formatters={"corr": lambda x: f"{x: .3f}" if pd.notna(x) else "  n/a",
                          "dif_media_abs": lambda x: f"{x: .3f}" if pd.notna(x) else " n/a",
                          "dif_max_abs": lambda x: f"{x: .3f}" if pd.notna(x) else " n/a",
                          "ult_viejo": lambda x: f"{x: .2f}" if pd.notna(x) else " n/a",
                          "ult_nuevo": lambda x: f"{x: .2f}" if pd.notna(x) else " n/a"}))
    print("=" * 92)
    print("Lectura: corr alta + dif pequeña = misma serie (bien). Divergencias grandes")
    print("esperables donde el viejo inventaba: output_gap_china, interest_rate_ecb,")
    print("risk_premium_spain, y el desglose de IPC (antes fabricado con ×0,85).")
    return rep


if __name__ == "__main__":
    comparar()
