"""
Configuración, parámetros estructurales y priors del modelo Semi-DSGE para España.
"""

from pathlib import Path

# Directorios del proyecto (MEcPol)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SANDBOX_DIR = PROJECT_ROOT  # Alias de compatibilidad hacia atrás
DATA_DIR = PROJECT_ROOT / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_NUEVOS_DIR = DATA_DIR / "nuevos"
DATA_PROCESSED_DIR = DATA_DIR / "processed"
REPORTS_DIR = PROJECT_ROOT / "reports"
DOCS_DIR = PROJECT_ROOT / "docs"

# Rutas a datos brutos
DATA_PATHS = {
    'crudo': DATA_RAW_DIR / "crudo.csv",
    'diarias': DATA_RAW_DIR / "series_diarias.xlsx",
    'mensuales': DATA_RAW_DIR / "series_mensuales.xlsx",
    'trimestrales': DATA_RAW_DIR / "series_trimestrales.xlsx",
    'potencial': DATA_RAW_DIR / "pib_potencial_espana.csv",
    'labor': DATA_RAW_DIR / "indicadores mercado laboral.xlsx",
    # Fuentes limpias (preferentes sobre los xlsx cuando están disponibles)
    'epa': DATA_NUEVOS_DIR / "empleo_epa_2002_2026T2.csv",
    'pib_cvec': DATA_NUEVOS_DIR / "pib_real_cvec_indice.csv",
}

# Nowcasting tracker (repo hermano en el mismo directorio Github/)
# Si no existe (p. ej. en otro equipo), el pipeline lo ignora sin errores.
NOWCAST_TABLES_DIR = PROJECT_ROOT.parent / "crisistrackerv2" / "data" / "processed" / "tables"

# ==============================================================================
# PARÁMETROS ESTRUCTURALES CALIBRADOS PARA ESPAÑA (UEM)
# ==============================================================================
DEFAULT_PARAMS = {
    # --------------------------------------------------
    # 1. Curva IS (Demanda Agregada Doméstica)
    # --------------------------------------------------
    'is_persistence': 0.65,        # Fase 2: persistencia de la brecha coherente con la media del
                                   # prior (0.65) y estacionaria con todos los canales activos y el
                                   # anclaje parcial de expectativas en el tipo real. (El 0.82 previo
                                   # hacía la IS explosiva, multiplicador de largo plazo ~16x.)
    'is_forward': 0.14,            # Componente de expectativas forward-looking
    'is_interest_rate': 0.18,      # Sensibilidad a tipos de interés reales
    'is_demand_eu': 0.40,          # Tracción de la demanda de la Eurozona
    'is_demand_usa': 0.08,         # Tracción de la demanda de EE.UU.
    'is_demand_china': 0.05,       # Tracción de la demanda de China
    'is_reer': 0.12,               # Sensibilidad a competitividad exterior
    'is_fiscal': 0.30,             # Multiplicador fiscal / impacto fondos NGEU
    'is_credit': 0.15,             # Condiciones financieras y crédito
    'is_tourism': 0.15,            # Fuerte tracción del turismo receptor
    'r_neutral_spain': 1.00,       # Tipo de interés real neutral de largo plazo (%)

    # --------------------------------------------------
    # 2. Curva de Phillips: No Transables / Servicios (Doméstico)
    # --------------------------------------------------
    'phillips_nt_backward': 0.65,  # Inercia salarial y de servicios (término DOMINANTE)
    'phillips_nt_forward': 0.25,   # Expectativas de inflación (ancladas al objetivo)
    'phillips_nt_gap': 0.18,       # Sensibilidad a la brecha de producción
    'phillips_nt_clu': 0.22,       # Transmisión de Costes Laborales Unitarios

    # --------------------------------------------------
    # 3. Curva de Phillips: Transables / Bienes Industriales (Comercio)
    # --------------------------------------------------
    'phillips_t_backward': 0.50,   # Persistencia en bienes industriales
    'phillips_t_forward': 0.25,    # Peso de expectativas
    'phillips_t_gap': 0.15,        # Sensibilidad a brecha de producción
    'phillips_t_reer': 0.20,       # Pass-through tipo de cambio (canal de coste exterior)
    'phillips_t_foreign': 0.35,    # Sensibilidad a inflación importada
    'phillips_t_oil': 0.18,        # (Retirado tras Fase 5) La subyacente NO reacciona
                                   # directamente a la energía (cf. BCCh WP-866: "core inflation
                                   # does not react directly to energy prices"). La energía llega
                                   # a la subyacente solo por el canal de convergencia general→núcleo
                                   # (phillips_headline_conv) y por la brecha de producción. Clave
                                   # conservada por compatibilidad; sin uso en las ecuaciones.

    # --- Canal ÚNICO de segunda ronda energía→subyacente (estilo QPM India) ---
    # Término autolimitado δ·(π_general_{t-1} - π_subyacente_{t-1}): la subyacente
    # "persigue" suavemente la brecha entre la general (que sí recoge la energía por
    # su peso en la cesta) y ella misma. Acotado y reversivo: al normalizarse la
    # energía la brecha se cierra sola y la subyacente vuelve al objetivo. Coeficiente
    # pequeño, coherente con el pass-through a subyacente de ~0.03 acumulado a 3 años
    # (FMI WP/22/173) y el 10% del QPM de India (FMI WP/17/33).
    'phillips_headline_conv': 0.040,

    # --------------------------------------------------
    # 4. Inflación Energética y de Alimentos (Shock Energético Reforzado)
    # --------------------------------------------------
    # Elasticidades del IPC energético a Brent(€) y gas TTF(€), RECALIBRADAS con la
    # estimación 1999-2025 (crudo y gas separados, con dummy de la bonificación de
    # combustibles). Valores estructurales, no del pico de la crisis:
    #   crudo β≈0.24 (estable en el tiempo); gas β≈0.02-0.05 (bajo: en la cesta
    #   energética del INE pesan más los carburantes, y la electricidad está regulada);
    #   persistencia ρ≈0.12 (los datos NO muestran el 0.60 previo: el efecto se agota
    #   en el trimestre). El efecto de las medidas regulatorias temporales (tope al gas,
    #   IVA eléctrico, 20 cts) NO va aquí: se modela aparte como overlays conmutables
    #   (POLICY_MEASURES), para poder activarlas/desactivarlas en proyección.
    'energy_oil_elasticity': 0.24, # (antes 0.45) traslado del crudo, valor estructural
    'energy_gas_elasticity': 0.05, # (antes 0.30) traslado del gas, amortiguado por la cesta
    'energy_persistence': 0.13,    # (antes 0.60) persistencia real del shock energético
    # --- Acumulador de presión energética (retardo geométrico tipo Koyck) ---
    # Z^e_t = μ·Z^e_{t-1} + (1-μ)·π^e_t.  Con μ alto, Z es una media móvil ponderada
    # de la inflación energética reciente cuyo pico llega VARIOS trimestres después del
    # de π^e, reproduciendo el retardo con que la energía se trasladó a los ALIMENTOS
    # en 2022-23. Z^e rezagado alimenta SOLO los alimentos (food_energy_transmission);
    # NO entra en la subyacente (cf. BCCh WP-866). Preserva la recursividad del bloque.
    'energy_pressure_persistence': 0.70,  # μ: memoria del acumulador (pico rezagado ~3-4T)
    'food_persistence': 0.55,      # Persistencia en alimentos
    'food_energy_transmission': 0.090,  # δ_fe: energía→alimentos con retardo (fertilizantes,
                                        # piensos, transporte, procesado). MOTOR del episodio 2022-23.
    'food_core_transmission': 0.15,# δ_fc: coste laboral/márgenes vía subyacente REZAGADA
                                   # (antes 0.35 sobre subyacente contemporánea, causalidad invertida)

    # --------------------------------------------------
    # 5. Ponderaciones del IPC (INE - Cesta Española)
    # --------------------------------------------------
    'weight_services': 0.42,       # Ponderación de servicios (no transables)
    'weight_goods': 0.33,          # Ponderación de bienes industriales (transables)
    'weight_food': 0.15,           # Ponderación de alimentos elaborados y frescos
    'weight_energy': 0.10,         # Ponderación de electricidad, carburantes y gas

    # --------------------------------------------------
    # 5b. Regla de política monetaria del BCE (Fase 5)
    #     Función de reacción tipo Taylor con suavizado, que ENDOGENIZA el tipo del
    #     BCE en la proyección (antes era exógeno del escenario, lo que dejaba la
    #     política monetaria "clavada" y provocaba espirales deflacionarias en los
    #     escenarios severos). El BCE reacciona a la inflación SUBYACENTE (señal de
    #     medio plazo, "mirando a través" de la energía, como el BCE real) y a una
    #     mezcla de la brecha española y de la UEM. Suaviza tipos y respeta un suelo.
    #       i_bce_t = ρ·i_bce_{t-1} + (1-ρ)·[i* + φ_π·(π^core-π*) + φ_y·brecha]
    # --------------------------------------------------
    'ecb_smoothing': 0.80,          # ρ: inercia/suavizado del tipo (política gradual)
    'ecb_neutral_nominal': 2.25,    # i*: tipo nominal neutral del BCE (r* ~0.25 + objetivo 2)
    'taylor_inflation': 1.50,       # φ_π: respuesta a la brecha de inflación (>1, principio de Taylor)
    'taylor_gap': 0.50,             # φ_y: respuesta a la brecha de producción
    'taylor_gap_weight_spain': 0.50,# peso de la brecha ESP vs UEM en la señal de actividad
    'ecb_floor': 0.00,              # suelo efectivo de tipos (ELB)

    # --------------------------------------------------
    # 6. Mercado Laboral (Ley de Okun y NAIRU Estructural)
    # --------------------------------------------------
    'okun_persistence': 0.78,       # δ_u: persistencia e inercia laboral
    'okun_gap_sensitivity': 0.28,   # θ_gap: reacción al nivel de la brecha de producción
    'okun_sensitivity': 0.22,       # θ_diff: reacción a la aceleración/cambio del PIB
    'employment_output_elast': 0.75,# Fuerte elasticidad del empleo al PIB en España
    'employment_persistence': 0.35,
    'nairu_default': 9.66,          # Tasa NAIRU estructural del último trimestre observado (EPA 2026T2)
    'nairu_ss': 8.85,               # Nivel estructural de largo plazo hacia el que converge la NAIRU
    'nairu_persistence': 0.94,      # Inercia de ajuste estructural de la NAIRU

    # --------------------------------------------------
    # 7. Shocks y Persistencias AR(1)
    # --------------------------------------------------
    'rho_demand': 0.60,
    'rho_supply_nt': 0.45,
    'rho_supply_t': 0.45,
    'rho_unemployment': 0.50,
    'inflation_target': 2.0,

    # --------------------------------------------------
    # 8. Entorno exterior
    # --------------------------------------------------
    'inflation_eu_default': 2.0,     # Inflación de la Eurozona por defecto si falta el dato

    # --------------------------------------------------
    # 9. PIB potencial por función de producción (Fase 3)
    #    Descomposición: g(Y*) = (1-α)·g(L*) + capital + PTF, con L* del bloque laboral.
    #    Capital y PTF calibrados al consenso del Banco de España (potencial 2025-28 ~2.2%).
    # --------------------------------------------------
    'pf_alpha': 0.35,                    # Elasticidad del capital (participación del capital)
    'capital_contrib_annual': 0.6,       # Contribución tendencial del capital (pp anuales, BdE)
    'tfp_contrib_annual': 0.5,           # Contribución tendencial de la PTF (pp anuales, BdE)
    'migration_decel': 0.92,             # Desaceleración trimestral del ritmo migratorio (WAP)
    'participation_hp_lambda': 1600.0,   # Suavizado HP de la tasa de actividad tendencial
    'nairu_hp_lambda': 25600.0,          # Suavizado HP de la NAIRU (tendencia de la tasa de paro)
    'gap_anchor_window': ('2024-01-01', '2025-01-01'),  # Ventana de anclaje cíclico (paro≈NAIRU ⇒ brecha≈0)
}

# ==============================================================================
# MEDIDAS REGULATORIAS/FISCALES TEMPORALES SOBRE LA ENERGÍA (conmutables)
# ==============================================================================
# Intervenciones que alteran el precio energético al consumo durante una ventana,
# modeladas como SUPERPOSICIONES DE NIVEL sobre el IPC energético (no como cambios
# en las elasticidades estructurales). Cada medida inyecta su efecto en el trimestre
# de ENTRADA (signo de theta_pp) y el rebote opuesto en el de SALIDA. Así se pueden
# activar/desactivar por fechas sin reestimar el modelo: si una medida vuelve, basta
# añadir su ventana futura en POLICY_MEASURES_FORECAST y reproyectar.
#
# theta_pp = efecto (en puntos porcentuales) sobre el IPC energético mientras rige
#            la medida. Negativo = abarata. 'end': None = sigue vigente / sin retirada.
POLICY_MEASURES = [
    {
        'name': 'bonif_combustibles_20cts',
        'component': 'carburantes',
        'theta_pp': -5.7,                     # ESTIMADO de nuestros datos (escalón limpio, R²=0.81)
        'start': '2022-04-01', 'end': '2022-12-31',
        'source': 'RDL 6/2022. Bonificación general 0,20 €/l (abr-dic 2022; desde 2023 solo transporte profesional).',
    },
    {
        'name': 'iva_electricidad_10',
        'component': 'electricidad',
        'theta_pp': -2.9,                     # MECÁNICO: 21%→10% = -9.1% elec × ~0.32 peso en cesta energética
        'start': '2021-07-01', 'end': '2024-01-01',
        'source': 'IVA eléctrico 21%→10% (jun-2021). Restituido gradualmente en 2024 (fechas 2024 pendientes de afinar).',
    },
    {
        'name': 'iva_electricidad_5',
        'component': 'electricidad',
        'theta_pp': -1.5,                     # MECÁNICO: 10%→5% = -4.5% elec × ~0.32 peso
        'start': '2022-07-01', 'end': '2024-01-01',
        'source': 'IVA eléctrico 10%→5% (jul-2022). Restituido gradualmente en 2024.',
    },
    {
        'name': 'excepcion_iberica',
        'component': 'electricidad',
        'theta_pp': -3.0,                     # INDICATIVO — refinar. El efecto NETO en IPC está contestado
                                              # por el 'ajuste' que se devuelve en la factura. No identificable
                                              # con nuestra serie; cifra oficial pendiente (BdE/CNMC).
        'start': '2022-07-01', 'end': '2023-12-31',
        'source': 'Tope al gas (15-jun-2022 a 31-dic-2023). Coste transferencias jun-dic 2022: 7.255 M€; ahorro ~209 €/hogar 2022.',
    },
]

# Activaciones HIPOTÉTICAS en el horizonte de proyección (por defecto, ninguna).
# Mismo formato que POLICY_MEASURES. Para simular "¿y si vuelve el tope al gas en
# 2027?", añadir aquí una entrada con su ventana futura y reproyectar.
POLICY_MEASURES_FORECAST = []


# ==============================================================================
# ESPECIFICACIÓN DE DISTRIBUCIONES A PRIORI PARA ESTIMACIÓN BAYESIANA
# ==============================================================================
# Todas las claves coinciden EXACTAMENTE con DEFAULT_PARAMS
PRIORS = {
    # Curva IS
    'is_persistence': {'dist': 'beta', 'mean': 0.65, 'std': 0.10},
    'is_forward': {'dist': 'beta', 'mean': 0.20, 'std': 0.06},
    'is_interest_rate': {'dist': 'beta', 'mean': 0.25, 'std': 0.08},
    'is_demand_eu': {'dist': 'beta', 'mean': 0.35, 'std': 0.08},
    'is_reer': {'dist': 'beta', 'mean': 0.12, 'std': 0.05},

    # Phillips NT (Servicios)
    'phillips_nt_backward': {'dist': 'beta', 'mean': 0.60, 'std': 0.10},
    'phillips_nt_forward': {'dist': 'beta', 'mean': 0.25, 'std': 0.08},
    'phillips_nt_gap': {'dist': 'beta', 'mean': 0.22, 'std': 0.08},
    'phillips_nt_clu': {'dist': 'beta', 'mean': 0.20, 'std': 0.07},

    # Phillips T (Bienes)
    'phillips_t_backward': {'dist': 'beta', 'mean': 0.45, 'std': 0.10},
    'phillips_t_forward': {'dist': 'beta', 'mean': 0.30, 'std': 0.08},
    'phillips_t_gap': {'dist': 'beta', 'mean': 0.18, 'std': 0.06},
    'phillips_t_reer': {'dist': 'beta', 'mean': 0.22, 'std': 0.07},
    'phillips_t_foreign': {'dist': 'beta', 'mean': 0.30, 'std': 0.08},

    # Canal de segunda ronda energía→subyacente (autolimitado, pequeño)
    'phillips_headline_conv': {'dist': 'beta', 'mean': 0.040, 'std': 0.02},

    # Bloque energía → alimentos (cascada con retardo; la energía SÍ mueve alimentos)
    'energy_pressure_persistence': {'dist': 'beta', 'mean': 0.70, 'std': 0.10},
    'food_persistence': {'dist': 'beta', 'mean': 0.55, 'std': 0.10},
    'food_energy_transmission': {'dist': 'beta', 'mean': 0.090, 'std': 0.04},
    'food_core_transmission': {'dist': 'beta', 'mean': 0.15, 'std': 0.06},

    # Mercado Laboral
    'okun_persistence': {'dist': 'beta', 'mean': 0.82, 'std': 0.06},
    'okun_sensitivity': {'dist': 'beta', 'mean': 0.42, 'std': 0.08},
    'employment_output_elast': {'dist': 'beta', 'mean': 0.70, 'std': 0.10}
}
