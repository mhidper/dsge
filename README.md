# MEcPol — Modelo Macroeconómico de EsadeEcPol

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![EsadeEcPol](https://img.shields.io/badge/EsadeEcPol-Center%20for%20Economic%20Policy-000b3d.svg)](https://www.esade.edu/ecpol/es/)
[![Status: Production](https://img.shields.io/badge/Status-Production%20v2.0-16a34a.svg)]()

**MEcPol** (*Modelo Macroeconómico de EsadeEcPol*) es una plataforma analítica semi-estructural desarrollada para la simulación, análisis de política económica y previsión macroeconómica de la economía española en su contexto europeo e internacional.

El modelo combina el rigor teórico del marco nuevo-keynesiano (expectativas forward-looking, curva IS abierta, curvas de Phillips desagregadas y regla de Taylor endógena) con la flexibilidad empírica necesaria para la proyección operativa y el diseño de políticas públicas.

---

## 🏛️ Características Principales

1. **Economía Abierta en Unión Monetaria:**
   * Modelización de España sin política monetaria autónoma, sujeta al ciclo del BCE y al diferencial de deuda soberana.
   * Regla de Taylor del BCE endógena en proyección (suavizado $\rho=0.80$, anclaje en inflación subyacente y señal de actividad mixta España-Eurozona).
2. **Función de Producción Cobb-Douglas y Canal Migratorio:**
   * Estimación del PIB potencial con elasticidad de capital $\alpha=0.35$ y contribución del capital y PTF calibradas según el consenso del Banco de España.
   * Insumo laboral potencial dependiente de la población en edad de trabajar ($WAP$), internalizando de forma directa el impacto de los flujos migratorios sobre la capacidad productiva.
3. **Curvas de Phillips Desagregadas en 4 Componentes:**
   * **Servicios / No Transables:** Sensible a la brecha de costes laborales unitarios ($\widetilde{CLU}$) y demanda interna.
   * **Bienes Transables:** Sensible a la competitividad exterior (REER) y la inflación importada de la UE.
   * **Alimentos:** Impulsada con retardo por un acumulador de presión energética (modelo Koyck).
   * **Energía:** Traspaso directo de cotizaciones internacionales de crudo Brent y gas natural TTF.
   * **Subyacente Estable:** La energía no entra directamente en el núcleo, garantizando realismo empírico y ausencia de espirales artificiales.
4. **Mercado Laboral con NAIRU Híbrida y Estacionalidad EPA:**
   * Dinámica de Okun completa (sensibilidad a la brecha en niveles y aceleraciones).
   * Módulo satélite aditivo de factores estacionales centrados de la EPA (T1 $+0.52$, T2 $-0.12$, T3 $-0.30$, T4 $-0.10$ pp).
5. **Bridge Model Satélite de IPC Mensual de Alta Frecuencia:**
   * Desagregación mensual que concilia los datos oficiales de la tabla 76130 del INE con cotizaciones spot de crudo para anticipar picos de inflación antes de su dilución en la media trimestral.
6. **Metodología de Contabilidad Nacional (INE / Eurostat):**
   * Cálculo de tasas de crecimiento anuales del PIB mediante la variación de las **medias de nivel de años consecutivos** ($\bar{Y}_T / \bar{Y}_{T-1} - 1$), respetando el efecto arrastre (*carryover*).
7. **Informes Ejecutivos Oficiales de EsadeEcPol:**
   * Generación automatizada de Policy Briefs en PDF (ReportLab) y Markdown con la identidad visual corporativa de EsadeEcPol (paleta cromática `#000b3d`, `#0e1e63`, `#1e4192`, `#ff5a5f` y sistema tipográfico dual).

---

## 📂 Estructura del Repositorio

```
DGSE/
│
├── run_forecast.py                         # Motor principal CLI de ejecución y previsión
├── requirements.txt                        # Dependencias de Python del proyecto
├── README.md                               # Documentación principal de MEcPol
├── AUDITORIA_Y_PLAN_MIGRACION_MECPOL.md   # Auditoría técnica del repositorio
│
├── src/                                    # Código fuente modular de MEcPol
│   ├── config.py                           # Calibración estructural, priors y rutas del proyecto
│   ├── model.py                            # Ecuaciones semi-estructurales y estado estacionario
│   ├── forecasting.py                      # Motor de proyecciones trimestrales y Monte Carlo
│   ├── potential.py                        # Función de producción Cobb-Douglas y canal migratorio
│   ├── monthly_cpi.py                      # Bridge model mensual de IPC y componentes (INE 76130)
│   ├── pdf_generator.py                    # Generador de informes PDF oficiales (ReportLab)
│   ├── reporting.py                        # Generador de Markdown, tablas y cálculo de tasas anuales
│   ├── estimation.py                       # Calibración Bayesiana MCMC (Metropolis-Hastings)
│   ├── scenarios.py                        # Orquestación de escenarios macroeconómicos
│   ├── refresh_energy_data.py              # Ingesta y actualización de crudo Brent y gas TTF
│   ├── data_pipeline.py                    # Utilidades de datos y filtros HP
│   ├── datos/                              # Almacén de datos (macro.db) y ensamblado
│   │   ├── almacen.py                      # Interfaz única a macro.db (SQLite)
│   │   ├── ensamblado.py                   # Construcción del dataset consolidado
│   │   ├── catalogo.yaml                   # Contrato de series catalogadas
│   │   └── conectores/                     # Conectores de ingesta oficial (INE, BCE, Eurostat, FRED)
│   └── escenarios/                         # Definiciones de shocks exógenos
│
├── data/                                   # Almacén de datos en producción
│   ├── macro.db                            # Base de datos SQLite oficial consolidada
│   ├── actualizacion_oficial_2025_2026.csv # Cierre histórico reciente oficial
│   └── nuevos/                             # Series de alta frecuencia (Brent, TTF, EPA, CVEC)
│
├── docs/                                   # Documentación metodológica oficial
│   ├── 01_marco_teorico_y_ecuaciones.md    # Especificación teórica de todas las ecuaciones
│   ├── 02_fuentes_datos_y_variables.md     # Ficha técnica de variables y fuentes estadísticas
│   ├── 03_guia_escenarios_y_prevision.md   # Manual de escenarios (Base, Ormuz, Desinflación)
│   ├── 04_variables_exogenas_y_control.md  # Panel de variables internacionales
│   └── references/                         # Literatura de referencia y modelos académicos (MSEP)
│
├── reports/                                # Informes y visualizaciones ejecutivas
│   ├── informe_ejecutivo_baseline.pdf      # Policy Brief oficial en PDF (5 páginas)
│   ├── informe_prevision_baseline.md       # Informe ejecutivo en Markdown
│   └── figures/                            # Paneles gráficos de alta resolución (Fan charts, IPC)
│
├── notebooks/                              # Cuadernos Jupyter de análisis e investigación
│
├── .agents/skills/                         # Skills de Antigravity (estándar de maquetación MEcPol)
└── archive/                                # Repositorio de versiones históricas (Dynare y Excel)
```

---

## 🚀 Instalación y Uso Rápido

### 1. Instalación de Requisitos
Se requiere Python 3.9 o superior.
```bash
pip install -r requirements.txt
```

### 2. Ejecución del Escenario Central (Baseline)
Para correr la simulación central a 12 trimestres y compilar automáticamente los informes en Markdown y PDF:
```bash
python run_forecast.py --scenario baseline --horizon 12
```

### 3. Comparativa Completa de Escenarios
Para simular simultáneamente el escenario central, el escenario adverso (escalada geopolítica y shock de crudo) y el escenario favorable (desinflación rápida):
```bash
python run_forecast.py --scenario all --horizon 12
```

### 4. Calibración Bayesiana MCMC (Opcional)
Para re-estimar los parámetros estructurales sobre la muestra histórica mediante Metropolis-Hastings antes de proyectar:
```bash
python run_forecast.py --scenario baseline --estimate --samples 2000
```

---

## 📊 Salidas del Modelo

Tras cada ejecución, los resultados quedan disponibles en:
* **Informe Ejecutivo en PDF:** [`reports/informe_ejecutivo_baseline.pdf`](reports/informe_ejecutivo_baseline.pdf)
  * Portada con tarjetas KPI y cuadro comparativo institucional (BdE, Funcas, Min. Economía, OCDE, FMI, CE, etc.).
  * Fan charts estocásticos (intervalos 50% y 80%) para PIB, inflación, paro EPA y brecha.
  * Desglose mensual de inflación por componentes y sensibilidad energética.
  * Cuadro macroeconómico trimestral detallado a medio plazo.
* **Informe en Markdown:** [`reports/informe_prevision_baseline.md`](reports/informe_prevision_baseline.md)
* **Gráficos en Alta Resolución:** [`reports/figures/`](reports/figures/)

---

## 📝 Reglas Editoriales y de Precisión Numérica

* **Crecimiento del PIB e Inflación:** 1 solo decimal (`2.7%`, `2.2%`, `3.3%`).
* **Tasa de Paro y Tipos de Interés:** 2 decimales (`10.10%`, `9.22%`, `3.11%`).
* **Identidad Visual:** Especificada en [`.agents/skills/esade-ecpol-report-design/SKILL.md`](.agents/skills/esade-ecpol-report-design/SKILL.md).

---

## 🏛️ Créditos y Filiación

**Esade Center for Economic Policy (EsadeEcPol)**  
Área Macro y Fiscal  
Web: [esade.edu/ecpol](https://www.esade.edu/ecpol/es/)