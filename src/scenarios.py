"""
Menú de variables exógenas y definición de escenarios macroeconómicos.

FASE 2 (redefinición de escenarios anclada al consenso vigente):
    A septiembre de 2026 la economía atraviesa un shock de oferta energético de
    primera magnitud (disrupciones en Oriente Medio; Brent en el entorno de
    100-105 USD). El consenso (EIA STEO, sep-2026) sitúa el Brent MEDIO de 2026 en
    ~91 USD, con descenso gradual en 2027 (85 -> 77 -> 70 -> 64). Por tanto:

      - BASELINE (central/consenso): incorpora el shock y su resolución gradual;
        un crudo elevado (~90) NO es un escenario adverso, es el central.
      - ADVERSO: escalada del conflicto (cierre de Ormuz), estanflación.
      - FAVORABLE: resolución rápida de la oferta (restauración de rutas saudíes),
        desinflación y recortes del BCE.

    Las sendas están ancladas a referencias verificables (EIA, mercados de futuros)
    y no a valores ilustrativos. Se ha eliminado además la duplicación de código del
    bloque adverso de la versión previa.
"""

from typing import Dict, List, Optional
import numpy as np
import yaml
from pathlib import Path


EXOGENOUS_VARIABLES = [
    'oil_price_brent',      # Petróleo Brent (USD/barril)
    'gas_price_ttf',        # Gas Natural TTF (EUR/MWh)
    'interest_rate_ecb',    # Tipo de política monetaria BCE (%)
    'risk_premium_spain',   # Prima de riesgo España vs Alemania (%)
    'output_gap_eu',        # Brecha de demanda Eurozona (%)
    'output_gap_usa',       # Brecha de demanda EE.UU. (%)
    'output_gap_china',     # Brecha de demanda China (%)
    'fiscal_impulse'        # Impulso fiscal neto / fondos NGEU (% PIB)
]


def _fit_horizon(steps: List[float], h: int) -> np.ndarray:
    """Ajusta una senda predefinida al horizonte h (trunca o prolonga con el último valor)."""
    arr = np.array(steps, dtype=float)
    if h <= len(arr):
        return arr[:h]
    return np.pad(arr, (0, h - len(arr)), mode='edge')


def _ramp_hold(start: float, end: float, h: int, ramp_frac: float = 0.67) -> np.ndarray:
    """
    Rampa lineal de `start` a `end` durante los primeros ~ramp_frac·h trimestres y
    después MESETA en `end`. Frente a una rampa que llega al valor terminal en el
    último trimestre, esto estabiliza el forcing exógeno antes del fin del horizonte
    y permite que las variables endógenas (brecha, paro) converjan a un estado
    coherente en vez de arrastrarse indefinidamente.
    """
    ramp_q = max(2, int(round(ramp_frac * h)))
    ramp_q = min(ramp_q, h)
    ramp = np.linspace(start, end, ramp_q)
    if ramp_q < h:
        hold = np.full(h - ramp_q, end)
        return np.concatenate([ramp, hold])
    return ramp


_ESCENARIOS_DIR = Path(__file__).resolve().parent / "escenarios"

# Valores de enganche por defecto cuando un 'desde: ultimo' no encuentra el
# último observado (mismos que usaba el código cableado anterior).
_ULTIMO_DEFECTO = {
    "interest_rate_ecb": 2.25,
    "risk_premium_spain": 0.75,
    "output_gap_eu": 0.0,
    "output_gap_usa": 0.0,
    "output_gap_china": 0.0,
}


def escenarios_disponibles() -> List[str]:
    """Nombres de escenario definidos (un .yaml por escenario)."""
    return sorted(p.stem for p in _ESCENARIOS_DIR.glob("*.yaml"))


def _cargar_escenario(scenario_type: str) -> Dict:
    """Lee escenarios/<scenario_type>.yaml. Error claro si no existe."""
    ruta = _ESCENARIOS_DIR / f"{scenario_type}.yaml"
    if not ruta.exists():
        disp = escenarios_disponibles()
        raise ValueError(f"Escenario desconocido: '{scenario_type}'. "
                         f"Definidos en {_ESCENARIOS_DIR.name}/: {disp}")
    with open(ruta, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    if "exogenas" not in cfg:
        raise ValueError(f"El escenario '{scenario_type}' no declara 'exogenas'.")
    return cfg


def _senda_desde_cfg(cfg: Dict, h: int, var: str,
                     last_values: Dict[str, float]) -> np.ndarray:
    """Construye la senda de una variable exógena desde su config YAML."""
    tipo = cfg.get("tipo")
    if tipo == "senda":
        return _fit_horizon([float(x) for x in cfg["valores"]], h)
    if tipo == "rampa":
        desde = cfg["desde"]
        if isinstance(desde, str) and desde.strip().lower() == "ultimo":
            desde = last_values.get(var, _ULTIMO_DEFECTO.get(var, 0.0))
        ramp_frac = float(cfg.get("ramp_frac", 0.67))
        return _ramp_hold(float(desde), float(cfg["hasta"]), h, ramp_frac)
    raise ValueError(f"Tipo de senda desconocido para '{var}': {tipo!r} "
                     f"(use 'senda' o 'rampa').")


def build_scenario_paths(last_values: Dict[str, float], horizon_quarters: int = 12,
                         scenario_type: str = 'baseline',
                         custom_overrides: Optional[Dict[str, List[float]]] = None) -> Dict[str, np.ndarray]:
    """
    Construye las sendas temporales de las variables exógenas para el horizonte.

    Args:
        last_values: últimos valores históricos observados (para enganche suave).
        horizon_quarters: nº de trimestres a proyectar.
        scenario_type: 'baseline', 'adverse_energy_rates' o 'favorable_disinflation'.
        custom_overrides: sobrescritura opcional de trayectorias concretas.
    """
    h = horizon_quarters

    escenario = _cargar_escenario(scenario_type)
    paths: Dict[str, np.ndarray] = {}
    for var, cfg in escenario["exogenas"].items():
        paths[var] = _senda_desde_cfg(cfg, h, var, last_values)

    # Sobrescrituras del usuario
    if custom_overrides:
        for var_name, user_path in custom_overrides.items():
            user_arr = np.array(user_path, dtype=float)
            if len(user_arr) < h:
                padding = np.full(h - len(user_arr), user_arr[-1])
                user_arr = np.concatenate([user_arr, padding])
            paths[var_name] = user_arr[:h]

    return paths
