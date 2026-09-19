"""
Conector de nowcast (Fase 4): estimación provisional del PIB para el
trimestre en curso (y el siguiente) mientras el INE no publica el dato
oficial. Fuente: el repo hermano crisistrackerv2 (ficheros LOCALES, no una
API), en crisistrackerv2/data/processed/tables/.

  - t6.csv: historial de estimaciones del trimestre corriente; la última
            fila da el trimestre en curso y su crecimiento QoQ (%).
  - t3.csv: fila "siguiente trimestre - semana actual" -> QoQ del T+1.

El QoQ se encadena sobre el último dato OFICIAL del INE que ya está en el
almacén (ine_pib_real_espana, en unidades de índice CVEC), y el resultado
se escribe como nowcast_pib_espana con estado='provisional'. Cuando el INE
publique el trimestre, el conector del INE lo escribe como 'oficial' y el
ensamblado deja de usar el provisional para esa fecha.

Regla "todo real": el nowcast es una estimación real, no un valor por
defecto; por eso se marca 'provisional' y nunca sobrescribe un dato oficial.
Si el repo hermano no está, el conector se omite sin error (no inventa nada).

Uso:
    python -m src.datos.conectores.nowcast
    python -m src.datos.conectores.nowcast --forzar
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import pandas as pd

from .. import almacen
from ._comun import registrar_resultado

try:
    from ...config import NOWCAST_TABLES_DIR
except Exception:  # pragma: no cover - fallback si cambia el layout
    NOWCAST_TABLES_DIR = Path(__file__).resolve().parents[3].parent / "crisistrackerv2" / "data" / "processed" / "tables"


def _qstr_a_fecha(s: str) -> Optional[pd.Timestamp]:
    """'2026Q3' -> Timestamp(2026-07-01)."""
    try:
        s = str(s).strip()
        anio, q = int(s[:4]), int(s[5])
        return pd.Timestamp(year=anio, month=(q - 1) * 3 + 1, day=1)
    except Exception:
        return None


def _calcular_nowcast(df_t6: pd.DataFrame, df_t3: Optional[pd.DataFrame],
                       ultima_fecha_oficial: pd.Timestamp,
                       ultimo_indice_oficial: float) -> Optional[pd.Series]:
    """
    A partir de los QoQ del tracker y el último índice oficial, devuelve una
    pd.Series (índice=fecha QS) con el índice de PIB provisional para los
    trimestres posteriores al último oficial. Separado de la lectura de
    ficheros para poder probarlo sin el repo hermano. None si no hay nada nuevo.
    """
    if df_t6 is None or len(df_t6) == 0:
        return None
    ult = df_t6.iloc[-1]
    fecha_actual = _qstr_a_fecha(str(ult.iloc[1]))
    qoq_actual = float(ult.iloc[2])
    if fecha_actual is None:
        return None

    qoq_siguiente = 0.0
    tiene_siguiente = False
    if df_t3 is not None and len(df_t3) > 0:
        col0 = df_t3.iloc[:, 0].astype(str)
        mask = col0.str.contains("siguiente", case=False, na=False) & col0.str.contains("actual", case=False, na=False)
        if mask.any():
            qoq_siguiente = float(df_t3.loc[mask, df_t3.columns[1]].iloc[0])
            tiene_siguiente = True

    fecha_siguiente = fecha_actual + pd.DateOffset(months=3)
    filas: dict = {}
    if fecha_actual > ultima_fecha_oficial:
        idx_actual = ultimo_indice_oficial * (1.0 + qoq_actual / 100.0)
        filas[fecha_actual] = idx_actual
        if tiene_siguiente and fecha_siguiente > ultima_fecha_oficial:
            filas[fecha_siguiente] = idx_actual * (1.0 + qoq_siguiente / 100.0)
    elif fecha_actual == ultima_fecha_oficial and tiene_siguiente and fecha_siguiente > ultima_fecha_oficial:
        filas[fecha_siguiente] = ultimo_indice_oficial * (1.0 + qoq_siguiente / 100.0)

    if not filas:
        return None
    idx = pd.DatetimeIndex(sorted(filas))
    return pd.Series([filas[d] for d in idx], index=idx, dtype=float)


def actualizar_todo(forzar: bool = False, max_age_days: float = 7.0,
                     db_path: Optional[Path] = None,
                     nowcast_dir: Optional[Path] = None) -> int:
    """Lee el tracker hermano y escribe el nowcast provisional. Best-effort."""
    carpeta = Path(nowcast_dir) if nowcast_dir is not None else NOWCAST_TABLES_DIR
    resultados = {"nowcast_pib_espana": False}

    if not carpeta.exists():
        print(f"[nowcast] Repo hermano no encontrado en {carpeta}; se omite (sin datos, "
              f"sin inventar). El PIB queda hasta el último oficial del INE.")
        return registrar_resultado("nowcast", resultados)

    try:
        base = almacen.leer("ine_pib_real_espana", db_path=db_path)
        if base.empty:
            print("[nowcast] No hay PIB oficial del INE en el almacén todavía; "
                  "ejecútese antes el conector del INE.")
            return registrar_resultado("nowcast", resultados)
        serie_base = base["ine_pib_real_espana"].dropna()
        ultima_fecha = serie_base.index.max()
        ultimo_indice = float(serie_base.loc[ultima_fecha])

        t6 = carpeta / "t6.csv"
        t3 = carpeta / "t3.csv"
        df_t6 = pd.read_csv(t6) if t6.exists() else None
        df_t3 = pd.read_csv(t3) if t3.exists() else None

        nc = _calcular_nowcast(df_t6, df_t3, ultima_fecha, ultimo_indice)
        if nc is None or nc.empty:
            print("[nowcast] Sin trimestres nuevos por delante del último oficial "
                  f"({ultima_fecha.date()}); nada que escribir.")
            return registrar_resultado("nowcast", resultados)

        n = almacen.escribir(nc, "nowcast_pib_espana", estado="provisional",
                              fuente_detalle="crisistrackerv2:t6.csv,t3.csv", db_path=db_path)
        print(f"[nowcast] Provisional escrito: {nc.index.min().date()} -> "
              f"{nc.index.max().date()} ({n} obs, estado=provisional)")
        resultados["nowcast_pib_espana"] = True
    except Exception as e:
        print(f"[nowcast] Error inesperado: {e}")

    return registrar_resultado("nowcast", resultados)


if __name__ == "__main__":
    forzar = "--forzar" in sys.argv or "--force" in sys.argv
    ok = actualizar_todo(forzar=forzar)
    sys.exit(0 if ok == 1 else 1)
