"""
Pruebas del almacén (Fase 1). Corren contra una base temporal, nunca
contra sandbox/data/macro.db, así que no hace falta limpiar nada después.

Uso:
    python -m src.datos.test_almacen
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pandas as pd

from . import almacen


def _db_temporal():
    tmp = Path(tempfile.mkdtemp()) / "macro_test.db"
    return tmp


def test_sync_catalogo():
    db = _db_temporal()
    n = almacen.sync_catalogo(db_path=db)
    assert n > 0, "el catálogo no debería estar vacío"
    cat = almacen.catalogo(db_path=db)
    assert "serie_id" in cat.columns
    assert cat["serie_id"].is_unique
    print(f"[OK] sync_catalogo: {n} series")


def test_escritura_rechaza_serie_no_catalogada():
    db = _db_temporal()
    almacen.sync_catalogo(db_path=db)
    serie = pd.Series([1.0], index=[pd.Timestamp("2026-01-01")])
    try:
        almacen.escribir(serie, "serie_que_no_existe", db_path=db)
        raise AssertionError("debería haber lanzado ValueError")
    except ValueError:
        pass
    print("[OK] escribir() rechaza series no catalogadas")


def test_idempotencia():
    db = _db_temporal()
    almacen.sync_catalogo(db_path=db)
    serie = pd.Series(
        [80.0, 81.5, 79.2],
        index=pd.date_range("2026-01-01", periods=3, freq="QS"),
    )
    n1 = almacen.escribir(serie, "fred_brent", vintage="2026-09-18", db_path=db)
    n2 = almacen.escribir(serie, "fred_brent", vintage="2026-09-18", db_path=db)
    assert n1 == n2 == 3
    leido = almacen.leer("fred_brent", db_path=db)
    assert len(leido) == 3
    assert leido["fred_brent"].tolist() == [80.0, 81.5, 79.2]
    print("[OK] escribir() es idempotente")


def test_lectura_multiserie_y_fechas():
    db = _db_temporal()
    almacen.sync_catalogo(db_path=db)
    fechas = pd.date_range("2020-01-01", periods=8, freq="QS")
    almacen.escribir(pd.Series(range(8), index=fechas, dtype=float),
                      "ine_ipc_general", vintage="2026-09-18", db_path=db)
    almacen.escribir(pd.Series(range(10, 18), index=fechas, dtype=float),
                      "ine_ipc_subyacente", vintage="2026-09-18", db_path=db)

    df = almacen.leer(["ine_ipc_general", "ine_ipc_subyacente"],
                       desde="2021-01-01", hasta="2021-12-31", db_path=db)
    assert list(df.columns) == ["ine_ipc_general", "ine_ipc_subyacente"]
    assert len(df) == 4  # 4 trimestres de 2021
    print("[OK] leer() multi-serie con filtro de fechas")


def test_vintages_reproducen_una_corrida_anterior():
    db = _db_temporal()
    almacen.sync_catalogo(db_path=db)
    fecha = pd.Timestamp("2026-07-01")

    almacen.escribir(pd.Series([100.0], index=[fecha]), "ine_epa_tasa_paro",
                      estado="provisional", vintage="2026-08-01", db_path=db)
    almacen.escribir(pd.Series([99.5], index=[fecha]), "ine_epa_tasa_paro",
                      estado="oficial", vintage="2026-10-15", db_path=db)

    como_estaba_en_agosto = almacen.leer("ine_epa_tasa_paro", vintage="2026-08-15", db_path=db)
    estado_actual = almacen.leer("ine_epa_tasa_paro", db_path=db)

    assert como_estaba_en_agosto.loc[fecha, "ine_epa_tasa_paro"] == 100.0
    assert estado_actual.loc[fecha, "ine_epa_tasa_paro"] == 99.5
    print("[OK] leer(vintage=...) reproduce una corrida anterior")


def test_frescura():
    db = _db_temporal()
    almacen.sync_catalogo(db_path=db)
    almacen.escribir(pd.Series([1.0], index=[pd.Timestamp.now().normalize()]),
                      "fred_brent", db_path=db)
    fr = almacen.frescura(db_path=db)
    assert "retrasada" in fr.columns
    fila = fr[fr["serie_id"] == "fred_brent"].iloc[0]
    assert fila["retrasada"] == False  # se acaba de cargar, no puede estar retrasada
    print("[OK] frescura() calcula retraso y marca correctamente")


if __name__ == "__main__":
    test_sync_catalogo()
    test_escritura_rechaza_serie_no_catalogada()
    test_idempotencia()
    test_lectura_multiserie_y_fechas()
    test_vintages_reproducen_una_corrida_anterior()
    test_frescura()
    print("\nTodas las pruebas de la Fase 1 pasan.")
