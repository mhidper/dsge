"""
Utilidades compartidas por los conectores de ingesta (Fase 2).

Todo conector sigue el mismo patrón: comprobar si la serie está
desactualizada consultando el propio almacén (no un fichero de caché
aparte), descargar con reintentos, y escribir con almacen.escribir().
Si la descarga falla, el conector avisa y conserva lo que ya había en
la base: nunca lanza una excepción que rompa una corrida por falta de
red (mismo principio que refresh_energy_data.py, aplicado a todos los
proveedores).
"""

from __future__ import annotations

import ssl
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional

import pandas as pd

from .. import almacen

# Algunas instalaciones de Python en Windows (típicamente el instalador de
# python.org, no Anaconda) no encuentran localmente la cadena de certificados
# de ciertos sitios -p.ej. data-api.ecb.europa.eu- aunque sí la de otros
# -p.ej. fred.stlouisfed.org-, según qué CA use cada uno y qué tenga ya
# Windows en su almacén. El síntoma es CERTIFICATE_VERIFY_FAILED /
# "unable to get local issuer certificate". En vez de pedir que se toque
# el almacén de certificados de Windows, usamos aquí el paquete `certifi`
# (paquete de certificados raíz de Mozilla, empaquetado para Python), que
# es la solución estándar y portable: si está instalado, todas las
# descargas de los conectores lo usan; si no, se cae al comportamiento
# por defecto de Python (funciona en la mayoría de instalaciones).
try:
    import certifi
    _CONTEXTO_SSL = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    _CONTEXTO_SSL = None


def esta_desactualizada(serie_id: str, max_age_days: float,
                         db_path: Optional[Path] = None) -> bool:
    """
    True si la serie no tiene datos aún, o si su descarga más reciente
    supera max_age_days. Sustituye a la comprobación de antigüedad de
    fichero (_is_stale) que usaba el CSV de caché: aquí la "caché" es
    la propia base, así que no hay una segunda copia que se pueda
    desincronizar.
    """
    ultima = almacen.ultima_descarga(serie_id, db_path=db_path)
    if ultima is None:
        return True
    edad_dias = (pd.Timestamp.now(tz="UTC") - ultima).total_seconds() / 86400.0
    return edad_dias > max_age_days


def descargar_texto(url: str, timeout: int = 45, intentos: int = 3,
                     espera_base: float = 2.0) -> Optional[str]:
    """
    GET simple con reintentos y espera creciente (backoff). Devuelve el
    cuerpo como texto, o None si los `intentos` fallan todos (sin red,
    error del servidor, timeout). No lanza: el llamador decide qué
    hacer con un None (normalmente, conservar lo que ya había).
    """
    ultimo_error = None
    for intento in range(1, intentos + 1):
        try:
            with urllib.request.urlopen(url, timeout=timeout, context=_CONTEXTO_SSL) as resp:
                return resp.read().decode("utf-8")
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as e:
            ultimo_error = e
            # Un fallo de certificado no se arregla reintentando igual;
            # probar una vez más con certifi explícito si aún no se usaba.
            es_error_certificado = isinstance(e, urllib.error.URLError) and isinstance(
                getattr(e, "reason", None), ssl.SSLCertVerificationError
            )
            if es_error_certificado and _CONTEXTO_SSL is None:
                print("[conector] Fallo de certificado SSL; instala 'certifi' "
                      "(pip install certifi) para que los conectores usen su "
                      "propia cadena de confianza en vez de la del sistema.")
            if intento < intentos:
                time.sleep(espera_base * (2 ** (intento - 1)))
    print(f"[conector] Sin red o fallo tras {intentos} intentos en {url}: {ultimo_error}")
    return None


def registrar_resultado(nombre_conector: str, resultados: dict) -> int:
    """Imprime un resumen homogéneo al final de cada `actualizar_todo()`."""
    ok = sum(1 for v in resultados.values() if v)
    total = len(resultados)
    estado = "OK" if ok == total else ("PARCIAL" if ok else "SIN RED")
    print(f"[{nombre_conector}] {estado}: {ok}/{total} series actualizadas o ya al día.")
    for serie, exito in resultados.items():
        marca = "OK" if exito else "--"
        print(f"    [{marca}] {serie}")
    return ok
