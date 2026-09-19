# Auditoría Integral del Repositorio y Plan de Migración: MEcPol

**Fecha de la Auditoría:** Septiembre 2026  
**Proyecto:** MEcPol — Modelo Macroeconómico de EsadeEcPol (Center for Economic Policy)  
**Ubicación:** `c:\Users\Usuario\Documents\Github\DGSE`  
**Estado:** Inventario y metodología re-auditados y corregidos (sep-2026). Motor verificado 100% ejecutable de la ingesta API al informe en `reports/`. Reorganización de ficheros pendiente de ejecución.  

---

## 1. Diagnóstico Ejecutivo

El repositorio ha experimentado una evolución metodológica y técnica muy profunda en los últimos meses:
1. **Origen:** Nació como una exploración académica combinando modelos DSGE puros en Dynare (`Modelo/`, `calculate_estimate.mod`) y notebooks secuenciales de exploración en Jupyter (`notebooks/01_...` a `06_semi_dsge_v6.ipynb`).
2. **Evolución:** La necesidad de contar con un motor de previsión macroeconómica ágil, empíricamente ajustado a España, con función de producción Cobb-Douglas (canal migratorio), bridge model de alta frecuencia para inflación (Brent/TTF), regla de Taylor endógena, estacionalidad de la EPA y maquetación ejecutiva oficial para EsadeEcPol dio lugar al desarrollo dentro de la carpeta `sandbox/`.
3. **Situación Actual:** `sandbox/` es **la fuente de la verdad ("la biblia")**: contiene el código de producción, el **almacén único** SQLite (`macro.db`) alimentado por **conectores de ingesta vía API** (INE, BCE, Eurostat, FRED, nowcast) y gobernado por un catálogo versionable, el ensamblado que aplica sus transformaciones, las ecuaciones calibradas, la documentación metodológica y el generador de informes PDF (ReportLab). El motor corre de punta a punta —de la ingesta API al informe en `reports/`— sin fricciones (verificado, septiembre 2026).
4. **Problema Identificado:** Fuera de `sandbox/`, la raíz del repositorio contiene múltiples carpetas vacías, scripts de 0 bytes, archivos temporales de experimentos previos, salidas intermedias y un `README.md` totalmente desfasado.

---

## 2. Inventario Detallado de Ficheros y Dictamen

A continuación se detalla el análisis de cada directorio y archivo del repositorio actual, con su dictamen clasificado en:
* 🟢 **MANTENER / PROMOVER:** Código y datos esenciales del modelo MEcPol en producción.
* 📦 **ARCHIVAR:** Código histórico y referencias académicas que tienen valor de consulta pero no forman parte del motor activo.
* 🔴 **ELIMINAR:** Ficheros vacíos, temporales, duplicados o inservibles.

| Ruta / Componente | Contenido | Diagnóstico | Dictamen | Acción Propuesta |
| :--- | :--- | :--- | :---: | :--- |
| **`sandbox/`** | Motor completo MEcPol (src, data, docs, reports, run_forecast.py) | Es el núcleo de producción actual. Todo funciona y está validado. | 🟢 **PROMOVER** | **Sacar de `sandbox/` y convertir en la raíz del proyecto.** |
| `sandbox/src/` | 12 módulos Python + subpaquete de datos `datos/` (almacén, catálogo, ensamblado y conectores API) y `escenarios/` (YAML) | Motor de estimación, proyección, ingesta API, bridge mensual y PDF ReportLab. | 🟢 **PROMOVER** | Mover a `/src/` en raíz (reemplazando el `src/` vacío). |
| `sandbox/data/` | `macro.db` (SQLite, almacén único) + `nuevos/` y `actualizacion_oficial_2025_2026.csv` (CSV ya **superados** por el almacén) | `macro.db` es la fuente viva; los CSV son solo respaldo/legado tras la migración a ingesta API. | 🟢 **PROMOVER** (`macro.db`) / 📦 **ARCHIVAR** (CSV) | Mover `macro.db` a `/data/`; los CSV superados, a `archive/data_legacy/`. |
| `sandbox/docs/` | 4 documentos metodológicos (01 marco teórico a 04 variables exógenas) | Documentación analítica exhaustiva y rigurosa. | 🟢 **PROMOVER** | Mover a `/docs/` en raíz. |
| `sandbox/reports/` | PDF oficial MEcPol, Markdown baseline y figuras | Informes ejecutivos listos para difusión. | 🟢 **PROMOVER** | Mover a `/reports/` en raíz. |
| `sandbox/run_forecast.py` | CLI principal para simulación y previsión | Punto de entrada del usuario para ejecutar el modelo. | 🟢 **PROMOVER** | Mover a `/run_forecast.py` en raíz. |
| `.agents/skills/esade-ecpol-report-design/` | Skill de Antigravity con tokens de diseño EsadeEcPol | Reglas cromáticas, tipográficas y de cálculo (precisión y CN). | 🟢 **MANTENER** | Conservar en `.agents/` para garantizar reproducibilidad. |
| `src/data_processing.py` y `src/modeling.py` | 2 archivos de Python en la raíz | **Vacíos (0 bytes)**. Restos de un scaffold inicial. | 🔴 **ELIMINAR** | Eliminar de forma segura. |
| `Claude outputs/` | 1 documento markdown y 2 gráficos png antiguos | Salidas intermedias de chat. Su contenido ya está integrado en `sandbox/`. | 🔴 **ELIMINAR** | Eliminar de forma segura. |
| `Modelo dos países/` | Subcarpeta `monetary/toolkit/` | **Completamente vacía (0 bytes)**. | 🔴 **ELIMINAR** | Eliminar de forma segura. |
| `pendiente/` | `files.zip` (25 KB) y 4 archivos de auditoría previa | Documentos de trabajo de una fase superada (problemas identificados). | 🔴 **ELIMINAR** | Eliminar (o archivar si Manuel desea conservar el zip). |
| `reports/figures/` | Carpeta en raíz | **Completamente vacía**. | 🔴 **ELIMINAR** | Eliminar (se usará `sandbox/reports/figures`). |
| `reports/html/` | 3 archivos HTML exportados de notebooks antiguos | Pesa más de 6 MB y no se usan en el pipeline actual. | 🔴 **ELIMINAR** | Eliminar (los notebooks originales ya los contienen). |
| `data/raw/`, `data/processed/`, `data/nuevos/` (raíz) | Excel antiguos (`series_trimestrales.xlsx`, etc.) | Duplicados o versiones anteriores. Todo fue migrado a `macro.db`. | 📦 **ARCHIVAR** | Mover a `archive/data_legacy/` o eliminar los redundantes. |
| `Modelo/` | `calculate_estimate.mod`, subcarpetas Dynare, `.mat` | Modelo DSGE puro previo en Dynare / MATLAB. | 📦 **ARCHIVAR** | Mover a `archive/dynare_dsge/` como historial académico. |
| `notebooks/` | `01_gdp_potential_analysis.ipynb` a `06_semi_dsge_v6.ipynb` | Bitácora de trabajo y pruebas econométricas de Manuel. | 📦 **PRESERVAR** | Mantener intactos en `notebooks/` (no tocar según regla de usuario). |
| `Documentos/` | `Summer_Course_2020_Foundations_Course_update.pdf` | Material docente y metodológico de consulta. | 📦 **PRESERVAR** | Mover a `docs/references/`. |
| `docs/references/` | Paper Arroyo et al. (2020) y códigos de replicación MSEP | Modelo chileno de referencia técnica. | 🟢 **MANTENER** | Conservar en `docs/references/`. |
| `ejemplos/` | `Celso/` y `SW2007/` | Códigos de replicación de Smets-Wouters. | 📦 **PRESERVAR** | Mover a `docs/references/ejemplos/`. |
| `README.md` (raíz) | Markdown descriptivo desfasado | Describe estructura obsoleta con archivos inexistentes. | 🟢 **REESCRIBIR** | Actualizar por completo con la arquitectura oficial de MEcPol. |

---

## 3. Arquitectura Objetivo del Proyecto (`/DGSE`)

Una vez completada la migración y la limpieza, el repositorio presentará una estructura limpia, profesional y estándar para un proyecto de modelización de think tank:

```
DGSE/
│
├── .agents/                                # Sistema de personalizaciones y skills de Antigravity
│   └── skills/
│       └── esade-ecpol-report-design/      # Estándar editorial y diseño corporativo MEcPol
│
├── run_forecast.py                         # [PROMOVIDO] Motor principal CLI (simulación y generación)
├── requirements.txt                        # Dependencias de Python actualizadas
├── README.md                               # [RENOVADO] Documento principal de bienvenida y uso
├── AUDITORIA_Y_PLAN_MIGRACION_MECPOL.md   # Este informe de auditoría
│
├── src/                                    # [PROMOVIDO de sandbox/src] Código fuente MEcPol
│   ├── __init__.py
│   ├── config.py                           # Parámetros estructurales, calibración y rutas
│   ├── model.py                            # Ecuaciones semi-estructurales y estado estacionario
│   ├── forecasting.py                      # Motor de proyecciones trimestrales y Monte Carlo
│   ├── potential.py                        # PIB potencial Cobb-Douglas y canal migratorio
│   ├── monthly_cpi.py                      # Bridge model satélite de IPC mensual (INE 76130)
│   ├── pdf_generator.py                    # Generador de informes PDF de calidad editorial (ReportLab)
│   ├── reporting.py                        # Informes Markdown, gráficos y cálculo de medias de nivel
│   ├── estimation.py                       # Calibración Bayesiana MCMC (Metropolis-Hastings)
│   ├── scenarios.py                        # Orquestación de escenarios alternativos
│   ├── refresh_energy_data.py              # Actualización de series de alta frecuencia (Brent, TTF)
│   ├── data_pipeline.py                    # Legado: helpers (hp_filter, build_policy_overlay) que aún importan ensamblado/potential; su build_consolidated_dataset está superado por ensamblado.py
│   ├── datos/                              # Capa de datos (almacén único + ingesta API)
│   │   ├── almacen.py                      # Única puerta a macro.db (catálogo + observaciones con vintage/estado)
│   │   ├── catalogo.yaml                   # Contrato versionable de las ~24 series
│   │   ├── esquema.sql                     # Esquema SQLite (catalogo, observaciones)
│   │   ├── ensamblado.py                   # Arma el DataFrame del modelo desde el almacén (todo real)
│   │   ├── test_almacen.py / test_paridad.py  # Pruebas de la capa de datos y paridad vs pipeline viejo
│   │   └── conectores/                     # Ingesta vía API: fred, bce, eurostat, ine, nowcast (+ _comun, actualizar_datos, tests)
│   └── escenarios/                         # Escenarios en YAML: baseline / adverse_energy_rates / favorable_disinflation
│
├── data/                                   # [PROMOVIDO de sandbox/data]
│   └── macro.db                            # Almacén único SQLite (INE, BCE, Eurostat, FRED, nowcast); ÚNICA fuente viva
│                                           #   (los CSV nuevos/ y actualizacion_oficial_*.csv → archive/data_legacy/, superados)
│
├── docs/                                   # [PROMOVIDO de sandbox/docs] Documentación metodológica
│   ├── 01_marco_teorico_y_ecuaciones.md    # Teoría macroeconómica, NAIRU, Okun, Phillips y Taylor
│   ├── 02_fuentes_datos_y_variables.md     # Ficha de variables oficiales y códigos de tablas
│   ├── 03_guia_escenarios_y_prevision.md   # Manual de escenarios (Base, Ormuz, Desinflación)
│   ├── 04_variables_exogenas_y_control.md  # Panel de variables internacionales
│   └── references/                         # Papers académicos y modelos de referencia (MSEP, etc.)
│       ├── Summer_Course_2020.pdf
│       └── replication_codes_MSEP/
│
├── reports/                                # [PROMOVIDO de sandbox/reports] Informes generados
│   ├── informe_ejecutivo_baseline.pdf      # Informe Policy Brief MEcPol (5 páginas, diseño EsadeEcPol)
│   ├── informe_prevision_baseline.md       # Informe ejecutivo en Markdown
│   └── figures/                            # Gráficos de alta resolución sin distorsión (Fan charts, IPC)
│
├── notebooks/                              # [PRESERVADO] Bitácora de notebooks de investigación
│   ├── 01_gdp_potential_analysis.ipynb
│   └── 06_semi_dsge_v6.ipynb
│
└── archive/                                # [NUEVO] Histórico y versiones legadas
    ├── dynare_dsge/                        # Códigos del modelo previo en Dynare/MATLAB
    └── data_legacy/                        # Hojas Excel antiguas reemplazadas por macro.db
```

---

## 4. Estado de la Metodología y Documentación

La documentación de `sandbox/docs/` ha sido **auditada y alineada al 100% con el código** (septiembre 2026). Los bloques del motor y su correspondencia con la implementación:

1. **Curva IS abierta:** tipos reales, demanda externa (UE/EE.UU./China), REER, impulso fiscal y turismo, anclada a la función de producción. La expectativa *forward* $\mathbb{E}_t[\tilde{y}_{t+1}]$ se aproxima operativamente por $0{,}85\,\tilde{y}_{t-1}$ (documentado; resolución explícita pendiente).
2. **Curva de Phillips desagregada en 4 bloques:** no transables (servicios/CLU), transables (REER + inflación importada UE), alimentos (presión energética rezagada tipo Koyck) y energía (Brent/TTF directo). La subyacente **no** reacciona directamente a la energía; único canal indirecto autolimitado (convergencia general-núcleo).
3. **Mercado laboral y NAIRU:** Okun en niveles y aceleraciones; estacionalidad EPA aditiva de suma cero (T1 +0,52 / T2 −0,12 / T3 −0,30 / T4 −0,10). **Corrección de la auditoría:** la NAIRU **no** se estima estructuralmente en el motor vigente —se obtiene como **tendencia HP** de la tasa de paro (λ=6400 para Okun; λ=25600 para el potencial)— y en proyección converge a su nivel de largo plazo (≈8,85%, ρ=0,94). La estimación estructural queda como extensión futura, ya documentada como tal en `docs/01`.
4. **Condiciones monetarias:** regla de Taylor endógena del BCE en proyección (ρ=0,80, i\*=2,25, φπ=1,5, φy=0,5; responde al núcleo rezagado y a una señal de brecha ES/UEM). El tipo doméstico se reconstruye como `interest_rate_ecb` (facilidad de depósito observada) + `risk_premium_spain` (diferencial 10a ES−DE): mezcla deliberada de un tipo corto de política con un diferencial soberano largo. El EURIBOR 3m observado está en el almacén por si se prefiere anclar el histórico a él.
5. **Bridge mensual de IPC:** desagregación de alta frecuencia (tabla INE 76130 + Brent), ahora **leída del almacén** (`macro.db`, ingesta API), con respaldo a CSV. Pesos alineados con el núcleo trimestral (energía 0,10 / subyacente 0,75 / alimentos 0,15).
6. **Crecimiento anual del PIB (Contabilidad Nacional):** variación de las medias anuales del nivel del PIB en volumen encadenado (no media de tasas interanuales). Implementado en `reporting.compute_annual_gdp_growth`.
7. **Función de producción (potencial):** Cobb-Douglas con α=0,35 y contribuciones tendenciales de capital (0,6 pp) y PTF (0,5 pp), canal migratorio vía población en edad de trabajar. Coincide con la calibración de `config.py` y con el consenso del Banco de España.
8. **Precisión numérica:** crecimiento e inflación a 1 decimal; paro y tipos a 2.

## 5. Plan de Ejecución para la Migración

Para ejecutar esta reorganización sin riesgo alguno:

### Fase 1: Copia de Seguridad y Verificación (Inmediata)
* Comprobar que `sandbox/` contiene el 100% de los elementos operativos.
* Crear la carpeta `archive/` para salvaguardar `Modelo/` (Dynare) y hojas Excel previas.

> **Verificado (sep-2026):** cadena completa ejecutada sin fricciones — `actualizar_datos` (ingesta API a `macro.db`) → `ensamblado` → `run_forecast.py` (3 escenarios + bandas Monte Carlo + satélite mensual de IPC) → informe Markdown y PDF en `reports/`. El satélite mensual y el resto del motor leen del almacén (todo real). `requirements.txt` actualizado con `reportlab` y `openpyxl` (faltaban).

### Fase 2: Promoción de `sandbox/` a la Raíz
1. Mover los contenidos de `sandbox/src/` a `/src/`.
2. Mover los contenidos de `sandbox/data/` a `/data/`.
3. Mover los contenidos de `sandbox/docs/` a `/docs/`.
4. Mover los contenidos de `sandbox/reports/` a `/reports/`.
5. Mover `sandbox/run_forecast.py` a `/run_forecast.py`.
6. Actualizar las rutas de importación en los scripts (eliminar cualquier prefijo residual `sandbox.` para que operen directamente como módulos estándar).

### Fase 3: Limpieza de Reliquias (Previa Confirmación)
* Solicitar confirmación expresa a Manuel antes de borrar definitivamente:
  * `Modelo dos países/` (carpeta vacía).
  * `src/data_processing.py` y `src/modeling.py` (archivos vacíos en raíz).
  * `Claude outputs/` (archivos redundantes).
  * `pendiente/` (archivos obsoletos).
  * `reports/html/` (exports HTML innecesarios).
  * La carpeta `sandbox/` una vez que todos sus contenidos hayan sido promovidos a la raíz.

### Fase 4: Reescritura del `README.md` Principal
* Redactar un nuevo `README.md` institucional que documente el **Modelo MEcPol**, sus bloques teóricos, instrucciones de ejecución rápida (`python run_forecast.py`) y estructura del proyecto.
