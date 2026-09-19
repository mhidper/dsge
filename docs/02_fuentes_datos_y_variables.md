# Fuentes de Datos, Tratamiento y Variables

Este documento describe las fuentes de datos utilizadas por el modelo Semi-DSGE para España, los procedimientos de limpieza, conversión de frecuencias y el cálculo de las variables endógenas y exógenas.

---

## 1. Inventario de Fuentes de Datos

Desde la reforma de la capa de datos, **todas** las series primarias se ingieren automáticamente vía API pública y se consolidan en un **almacén único** SQLite (`data/macro.db`). No hay ya jerarquía de ficheros congelados: los Excel y CSV previos quedan solo como respaldo/legado. El contrato de cada serie (fuente, identificador de origen, agregación, transformación y columna de destino en el modelo) vive en un catálogo versionable, `src/datos/catalogo.yaml`, que se sincroniza con la tabla `catalogo` de la base.

### 1.1 Arquitectura del almacén

* **`src/datos/almacen.py`** — única puerta de escritura/lectura. Tablas: `catalogo` (contrato de series) y `observaciones` (dato en formato largo con `vintage`, para reproducibilidad *as-of*, y `estado` ∈ {oficial, provisional, arrastrado}).
* **`src/datos/catalogo.yaml`** — fuente de verdad legible de las ~24 series.
* **`src/datos/ensamblado.py`** — arma el DataFrame trimestral del modelo leyendo del almacén y aplicando las transformaciones del catálogo. Regla dura: si falta una serie real, se detiene y avisa; no rellena con valores por defecto.

### 1.2 Conectores de ingesta (API) — `src/datos/conectores/`

| Conector | Proveedor (API) | Series | Frecuencia origen |
| :--- | :--- | :--- | :--- |
| `fred.py` | FRED (St. Louis Fed) | Brent (`DCOILBRENTEU`), gas EU (`PNGASEUUSDM`→EUR/MWh), PIB EE.UU. (`GDPC1`) | Diaria / Mensual / Trimestral |
| `bce.py` | BCE Data Portal (SDMX) | Facilidad de depósito, tipo de cambio USD/EUR, EURIBOR 3m | Diaria / Mensual |
| `eurostat.py` | Eurostat (JSON-stat) | IPCA EA20 (tasa e índice), PIB eurozona, rendimientos 10a ES y DE | Mensual / Trimestral |
| `ine.py` | INE Tempus3 | PIB CVEC (tabla 67822), EPA (65219/65109/65080/65063), IPC (tabla 76130, 6 grupos) | Trimestral / Mensual |
| `nowcast.py` | crisistrackerv2 (repo hermano local) | Nowcast provisional del PIB (t6/t3) | Trimestral |

El punto de entrada único es `python -m src.datos.conectores.actualizar_datos [--forzar] [--fuente <nombre>]`, que sincroniza el catálogo, ejecuta cada conector (best-effort: sin red conserva lo ya descargado) e imprime un panel de frescura. La selección de series del INE se hace por texto sobre el campo `Nombre` de cada tabla (p. ej. "Ambos sexos. Total" para la EPA; "Índice general" para el IPC), avisando si hay cero o varias coincidencias en vez de adivinar.

### 1.3 Nowcasting como INE provisional (`crisistrackerv2/`)

Para los trimestres aún sin dato oficial del INE, el pipeline toma las estimaciones del tracker de nowcasting hermano (`../crisistrackerv2/data/processed/tables/`):

* **`t6.csv`** (última fila) → tasa intertrimestral (QoQ) del **trimestre corriente**.
* **`t3.csv`** (fila "siguiente trimestre, semana actual") → QoQ del **trimestre siguiente**.

Estas tasas se convierten a nivel de PIB partiendo del último dato oficial y se insertan como filas provisionales **solo para fechas posteriores** al último dato INE. En cuanto el INE publica el trimestre, el conector del INE lo escribe como `oficial` en el almacén y el ensamblado deja de usar el provisional para esa fecha (se sustituye solo). La ruta es relativa (repos hermanos bajo `Github/`), por lo que si el tracker no está presente el pipeline lo ignora sin error.

---

## 2. Tratamiento y Transformación de Series

El ensamblado (`src/datos/ensamblado.py`) realiza de forma automática las siguientes transformaciones al leer del almacén (según declara `catalogo.yaml`):

### 2.1 Conversión de Frecuencias a Trimestral
* **Series Diarias (Petróleo, Tipo de Cambio)**: Se calcula la media aritmética de cada trimestre:
  $$P^{trimestral}_T = \frac{1}{N_T} \sum_{d \in T} P_d$$
* **Series Mensuales (IPC por componentes, Tipos de Interés)**: Se calcula la media del trimestre para índices de precios y tipos de mercado.

### 2.2 Desestacionalización y Ajuste de Calendario
* Las series de Contabilidad Nacional Trimestral (CNTR) y de la Encuesta de Población Activa (EPA) se utilizan en sus versiones corregidas de efectos estacionales y de calendario (CVEC / SA).

### 2.3 Cálculo de Brechas (Gaps) y Tendencias
* **Brecha de PIB España ($\tilde{y}_t$)**: Se obtiene a partir de la estimación estructural de la función de producción ([01_gdp_potential_analysis.ipynb](file:///c:/Users/Usuario/Documents/Github/DGSE/notebooks/01_gdp_potential_analysis.ipynb)), asegurando coherencia con la capacidad productiva del país:
  $$\tilde{y}_t = \left(\frac{Y_t - Y_t^*}{Y_t^*}\right) \times 100$$
* **Brechas Externas ($\tilde{y}^{EU}_t, \tilde{y}^{US}_t, \tilde{y}^{CN}_t$)**: Se aplica el filtro Hodrick-Prescott sobre el logaritmo del PIB real de cada bloque geográfico con parámetro de suavizado estándar trimestral ($\lambda = 1600$):
  $$\ln(Y^{ext}_t) = \tau_t + c_t \implies \tilde{y}^{ext}_t = c_t \times 100$$
* **NAIRU y Brecha de Desempleo**:
  $$\tilde{u}_t = u_t - u^*_t$$

### 2.4 Homogeneización de Escalas
* Todas las variables de brechas ($\tilde{y}_t, \tilde{u}_t, \widetilde{reer}_t$) se estandarizan en **puntos porcentuales** (e.g., $+1.5\%$).
* Las tasas de inflación se expresan en variación interanual porcentual:
  $$\pi_t = \left(\frac{IPC_t}{IPC_{t-4}} - 1\right) \times 100$$
* Los tipos de interés y primas de riesgo se expresan en tanto por ciento anual ($3.50\%$).

---

## 3. Diccionario de Variables del Dataset Trimestral Unificado

El dataset final generado para la estimación y previsión contiene:

| Código de Variable | Descripción | Tipo | Unidad |
| :--- | :--- | :--- | :--- |
| `date` | Trimestre (Formato YYYY-QQ) | Índice temporal | Fecha |
| `gdp_real_spain` | PIB real de España en volumen encadenado | Endógena | Índice base / Millones € |
| `gdp_potential_spain` | PIB potencial estimado | Endógena | Índice base / Millones € |
| `output_gap_spain` | Brecha de producto ($\tilde{y}_t$) | Endógena | % |
| `inflation_total` | Inflación IPC general interanual | Endógena | % |
| `inflation_core` | Inflación IPC subyacente interanual | Endógena | % |
| `inflation_services` | Inflación IPC servicios (no transables) | Endógena | % |
| `inflation_goods` | Inflación IPC bienes industriales (transables) | Endógena | % |
| `inflation_food` | Inflación IPC alimentos elaborados y frescos | Endógena | % |
| `inflation_energy` | Inflación IPC componentes energéticos | Endógena | % |
| `unemployment_rate` | Tasa de paro EPA | Endógena | % población activa |
| `nairu` | Tasa de paro estructural NAIRU | Endógena | % población activa |
| `employment_persons` | Número de personas ocupadas (EPA) | Endógena | Miles de personas |
| `interest_rate_spain` | Tipo doméstico; el motor lo reconstruye como `interest_rate_ecb` + `risk_premium_spain` (EURIBOR 3m observado disponible en el almacén) | Endógena | % anual |
| `interest_rate_ecb` | Tipo de política monetaria BCE (Depo/Refi) | Endógena en proyección (regla de Taylor); observada en histórico | % anual |
| `risk_premium_spain` | Diferencial de rendimiento 10Y España - Alemania | Exógena | Puntos básicos / % |
| `oil_price_brent` | Precio del barril de petróleo Brent | Exógena | USD/barril |
| `gas_price_ttf` | Precio del gas natural europeo TTF | Exógena | EUR/MWh |
| `output_gap_eu` | Brecha de producto Eurozona | Exógena | % |
| `output_gap_usa` | Brecha de producto Estados Unidos | Exógena | % |
| `output_gap_china` | Brecha de producto China | Exógena | % |
| `real_exchange_rate` | Tipo de cambio real efectivo (REER), nivel de precios relativo ES/UE | Endógena | Índice (100 = inicio) |
| `gdp_provisional` | Marca 1/0: trimestre de nowcast provisional (1) vs dato oficial INE (0) | Metadato | {0,1} |
