# Marco Teórico y Ecuaciones del Modelo MEcPol para España (EsadeEcPol)

## 1. Introducción y Filosofía del Modelo

El **Modelo MEcPol** (*Modelo Macroeconómico de EsadeEcPol*) pertenece a la familia de modelos **Semi-Estructurales / Semi-DSGE** (también conocidos como *Quarterly Projection Models* o QPM), metodología estándar empleada por los principales bancos centrales e instituciones multilaterales (Banco Central Europeo, Banco de España, Banco de Canadá, Fondo Monetario Internacional).

### Principios Fundamentales:
1. **Fundamentación Económica con Flexibilidad Empírica**: Combina la coherencia teórica de los modelos DSGE (expectativas forward-looking, restricciones presupuestarias y curvas de equilibrio) con la flexibilidad econométrica necesaria para capturar dinámicas reales de persistencia y ajuste en los datos.
2. **Economía Pequeña y Abierta en Unión Monetaria**: España carece de política monetaria independiente y de tipo de cambio nominal propio. Sus condiciones monetarias están determinadas por la política del Banco Central Europeo (BCE) más una prima de riesgo soberana/financiera, y su competitividad exterior se ajusta a través del Tipo de Cambio Real Efectivo (REER) y los diferenciales de inflación (*devaluación/inflación interna*).
3. **Desagregación Estructural**:
   - **Inflación**: Separación entre bienes transables (expuestos a competencia internacional y materias primas) y servicios no transables (traccionados por demanda interna y costes salariales), complementados por alimentos y energía.
   - **Mercado Laboral**: Ley de Okun aumentada con histéresis y vinculación a la población activa y ocupados.
   - **Actividad Económica**: Curva IS abierta con canal de tipos de interés reales, impulsos fiscales, demanda de socios comerciales (Eurozona, EE.UU., China) y turismo.

---

## 2. Ecuaciones del Sistema

El modelo opera a frecuencia trimestral. Las variables denotadas con tilde ($\tilde{x}_t$) representan **brechas** (desviaciones porcentuales respecto a su nivel potencial o de equilibrio). Las tasas de inflación y tipos de interés se expresan en porcentaje anualizado o interanual.

### Bloque I: Actividad Económica (Curva IS Abierta)

La brecha de producción ($\tilde{y}_t = \frac{Y_t - Y_t^*}{Y_t^*} \times 100$) representa las presiones de demanda sobre la capacidad instalada de la economía española:

$$\tilde{y}_t = \alpha_1 \tilde{y}_{t-1} + \alpha_2 \mathbb{E}_t [\tilde{y}_{t+1}] - \alpha_r (r_t - r^*) + \alpha_{eu} \tilde{y}^{EU}_t + \alpha_{us} \tilde{y}^{US}_t + \alpha_{cn} \tilde{y}^{CN}_t - \alpha_{reer} \widetilde{reer}_t + \alpha_f f_t + \alpha_{tr} \widetilde{tour}_t + \varepsilon^y_t$$

Donde:
* $\alpha_1$: Inercia y persistencia del consumo y la inversión por costes de ajuste y hábitos de consumo.
* $\alpha_2$: Componente de expectativas *forward-looking*. En el motor actual, $\mathbb{E}_t[\tilde{y}_{t+1}]$ se aproxima operativamente por $0{,}85\,\tilde{y}_{t-1}$ (proxy backward), a la espera de resolver las expectativas de forma explícita en una fase posterior.
* $r_t - r^*$: Brecha del tipo de interés real ($r_t = i_t - \mathbb{E}_t \pi_{t+1}$ menos el tipo real neutral $r^*$). Un tipo real por encima del neutral enfría la demanda.
* $\tilde{y}^{EU}_t, \tilde{y}^{US}_t, \tilde{y}^{CN}_t$: Brechas de demanda externa de la Eurozona (principal socio comercial), Estados Unidos y China.
* $\widetilde{reer}_t$: Brecha del Tipo de Cambio Real Efectivo. Un REER apreciado resta competitividad exterior neta.
* $f_t$: Impulso fiscal (gasto estructural e impacto de fondos europeos NGEU).
* $\widetilde{tour}_t$: Brecha de demanda del sector turístico internacional (peso del ~12-13% del PIB español).
* $\varepsilon^y_t \sim \mathcal{N}(0, \sigma_y^2)$: Shock estocástico de demanda agregada.

---

### Bloque II: Condiciones Monetarias y Financieras en UEM

España no posee política monetaria autónoma. El tipo de interés nominal a corto plazo del mercado español ($i_t$) se define como el tipo oficial del BCE más una prima de riesgo:

$$i_t = i^{BCE}_t + spread_t$$

En el código, $i^{BCE}_t$ es la **facilidad de depósito del BCE** observada (serie `bce_tipo_deposito` del almacén) y $spread_t$ el **diferencial del bono a 10 años España–Alemania** (Eurostat, criterio Maastricht). La identidad combina, pues, un tipo de política a corto con un diferencial soberano a largo: es una aproximación deliberada del coste de financiación doméstico, no un tipo de mercado de un único plazo. El **EURIBOR a 3 meses** (`bce_euribor_3m`) está también disponible en el almacén como tipo corto observado, por si se desea anclar el histórico a él en lugar de a la identidad reconstruida.

donde $spread_t$ es la prima de riesgo soberana y crediticia española frente a Alemania:

$$spread_t = \rho_s spread_{t-1} + (1-\rho_s) \overline{spread} + \gamma_s (\tilde{y}_t - \tilde{y}^{EU}_t) + \varepsilon^s_t$$

**Regla de política monetaria del BCE (endógena en proyección).** En la muestra histórica $i^{BCE}_t$ es el tipo observado. En la **proyección**, en lugar de imponerse como una senda exógena fija —lo que dejaba la política "clavada" y generaba espirales deflacionarias en escenarios severos—, el tipo del BCE lo determina una **función de reacción tipo Taylor con suavizado**:

$$i^{BCE}_t = \rho_i\, i^{BCE}_{t-1} + (1-\rho_i)\left[\, i^{*} + \phi_\pi\,(\pi^{core}_{t-1} - \pi^{*}) + \phi_y\, \tilde{y}^{sig}_{t-1} \,\right] + \varepsilon^{m}_t, \qquad i^{BCE}_t \geq \underline{i}$$

Donde:
* $\rho_i$: suavizado / gradualismo del tipo ($\approx 0.80$).
* $i^{*}$: tipo nominal neutral del BCE ($\approx 2.25\%$: real neutral $\approx 0.25$ + objetivo $2\%$).
* $\phi_\pi$: respuesta a la brecha de inflación ($\approx 1.5$, cumpliendo el **principio de Taylor** $\phi_\pi > 1$).
* $\phi_y$: respuesta a la brecha de actividad ($\approx 0.5$).
* $\pi^{core}_{t-1}$: inflación **subyacente** rezagada. El BCE responde al núcleo, no a la general, es decir "mira a través" de la energía (política menos volátil, coherente con la práctica del BCE real).
* $\tilde{y}^{sig}_t = \omega\,\tilde{y}_t + (1-\omega)\,\tilde{y}^{EU}_t$: señal de actividad que mezcla la brecha española y la de la UEM ($\omega \approx 0.5$), reconociendo que el BCE fija política para el agregado, no solo para España.
* $\underline{i}$: suelo efectivo de tipos (ELB, $\approx 0\%$).
* $\varepsilon^{m}_t$: sesgo de política de escenario (`monetary_shock`), que permite superponer una postura hawkish/dovish sobre la regla.

Esta función de reacción cierra el modelo: cuando un shock abre la brecha y desinfla el núcleo, el BCE recorta y frena la retroalimentación tipo real → demanda → inflación; cuando la economía se recalienta, el tipo sube y la contiene.

---

### Bloque III: Inflación y Precios (Curvas de Phillips Desagregadas)

La inflación general se descompone en 4 bloques según la estructura del IPC del INE:

$$\pi_t = w_{nt} \pi^{nt}_t + w_t \pi^t_t + w_{alim} \pi^{alim}_t + w_{energ} \pi^{energ}_t$$

**Principio de diseño (la subyacente es estable y NO reacciona directamente a la energía).** Siguiendo la práctica estándar de los modelos semiestructurales —en particular el modelo del Banco Central de Chile (BCCh, DTBC-866), base de este proyecto: *"core inflation does not react directly to energy prices; energy is a separate CPI component"*, y el QPM del FMI para India—, la energía entra **directamente solo en la general** (por su peso $w_{energ}$ en la cesta) y en los **alimentos** (con retardo), pero **no** en las curvas de subyacente. La subyacente se mueve por su propia inercia (término dominante), expectativas ancladas al objetivo y la brecha de producción. El único traslado energía→subyacente es indirecto, pequeño y autolimitado (término de convergencia general-núcleo), coherente con la evidencia empírica de un *pass-through* a la subyacente de $\approx 0.03$ acumulado a tres años (FMI, WP/22/173).

El orden de resolución respeta esta jerarquía y mantiene el bloque **recursivo**: energía → acumulador de presión → alimentos y subyacente (que leen términos rezagados).

#### 1. Curva de Phillips para Servicios / Bienes No Transables ($\pi^{nt}_t$)
Inflación doméstica, ligada a costes laborales y presiones internas. Ancla híbrida NKPC con pesos normalizados a suma 1 (garantiza reversión al objetivo sin shocks) y un único canal energético indirecto:

$$\pi^{nt}_t = \omega^{nt}_b\, \pi^{nt}_{t-1} + \omega^{nt}_f\, \pi^{*} + \lambda_{nt} \tilde{y}_t + \gamma_{nt} \widetilde{CLU}_t + \delta_{conv} (\pi_{t-1} - \pi^{core}_{t-1}) + \varepsilon^{nt}_t$$

Donde:
* $\omega^{nt}_b = \phi^b_{nt}/(\phi^b_{nt}+\phi^f_{nt})$ y $\omega^{nt}_f = \phi^f_{nt}/(\phi^b_{nt}+\phi^f_{nt})$: pesos backward/forward **normalizados a suma 1**, con la parte forward anclada al objetivo $\pi^{*}$. En estado estacionario (brecha y cuña nulas) $\pi^{nt}=\pi^{*}$.
* $\widetilde{CLU}_t$: Brecha de Costes Laborales Unitarios (salarios menos productividad).
* $\delta_{conv}(\pi_{t-1} - \pi^{core}_{t-1})$: **canal de segunda ronda energía→subyacente**, autolimitado. La subyacente "persigue" suavemente la brecha entre la general (que sí recoge la energía) y el núcleo; al normalizarse la energía la brecha se cierra sola y la subyacente revierte. Coeficiente pequeño ($\delta_{conv}\approx 0.04$), estilo QPM India.

#### 2. Curva de Phillips para Bienes Transables ($\pi^t_t$)
Bienes industriales expuestos al comercio mundial. Sus canales de coste exterior son el tipo de cambio real y la inflación importada de la UE (fieles al modelo chileno); la energía entra solo por el mismo término de convergencia:

$$\pi^t_t = \omega^{t}_b\, \pi^t_{t-1} + \omega^{t}_f\, \pi^{*} + \lambda_t \tilde{y}_t + \beta_{reer} \Delta reer_t + \beta_{eu} (\pi^{EU}_t - \pi^*) + \delta_{conv} (\pi_{t-1} - \pi^{core}_{t-1}) + \varepsilon^t_t$$

con pesos $\omega^{t}_b, \omega^{t}_f$ normalizados a suma 1 análogos a los de servicios.

#### 3. Inflación Energética ($\pi^{energ}_t$) y Acumulador de Presión
Transmisión directa de los precios internacionales del crudo y del gas:

$$\pi^{energ}_t = \rho_e \pi^{energ}_{t-1} + \delta_{oil} \Delta \ln(P^{oil}_t) + \delta_{gas} \Delta \ln(P^{gas}_t) + \varepsilon^e_t$$

Sobre esta serie se construye un **acumulador de presión energética** (retardo geométrico tipo Koyck) que propaga el shock con inercia hacia los alimentos:

$$Z^{e}_t = \mu\, Z^{e}_{t-1} + (1-\mu)\, \pi^{energ}_t$$

Con $\mu$ alto ($\approx 0.70$), el pico de $Z^e$ llega varios trimestres **después** del de $\pi^{energ}$, reproduciendo el retardo con que la energía se trasladó a los alimentos en 2022-23.

#### 4. Inflación de Alimentos ($\pi^{alim}_t$)
La energía es el **motor con retardo** (fertilizantes, piensos, transporte, procesado), vía el acumulador rezagado; la subyacente entra también rezagada como coste laboral/márgenes. La causalidad es energía → alimentos → subyacente (la observada en 2022-24), no a la inversa:

$$\pi^{alim}_t = \rho_a \pi^{alim}_{t-1} + \delta_{fe} (Z^{e}_{t-1} - \pi^{*}) + \delta_{fc} \pi^{core}_{t-1} + \varepsilon^a_t$$

---

### Bloque IV: Mercado Laboral (Desempleo, Ocupación y Estimación Estructural de la NAIRU)

Para realizar proyecciones rigurosas y dinámicas a medio plazo, el mercado de trabajo modela de forma integrada el desempleo cíclico, el desempleo estructural (NAIRU) y la identidad del factor trabajo:

#### 1. Estimación de la NAIRU ($u^*_t$) por tendencia de la tasa de paro
En la muestra histórica, la NAIRU se obtiene como la **tendencia de la tasa de paro observada** mediante un filtro Hodrick-Prescott fuertemente suavizado (λ = 6400 en el ensamblado para la serie que alimenta la ley de Okun; λ = 25600 en el bloque de potencial para el insumo laboral $L^*$), en línea con la práctica operativa de organismos como el Banco de España y la Comisión Europea. El último valor tendencial (EPA 2026-T2, $\approx 9{,}66\%$) fija el punto de partida de la proyección (`nairu_default`).

> **Nota metodológica (honestidad doc↔código).** El motor **no** despeja la NAIRU de una curva de Phillips estructural; usa la tendencia HP descrita. Una estimación plenamente estructural —resolviendo $u^*_t$ como el estado no observable que equilibra la curva de servicios/salarios, $\pi^{serv}_t - \pi^* = \omega_b (\pi^{serv}_{t-1} - \pi^*) - \gamma_u (u_t - u^*_t) + \gamma_{CLU} \widetilde{CLU}_t + \varepsilon^{pc}_t$— queda contemplada como **extensión futura**, no como el método vigente.

2. **Consistencia con la Función de Producción y Factores Demográficos:**
   En el bloque de crecimiento potencial ([`src/potential.py`](file:///C:/Users/Usuario/Documents/Github/DGSE/sandbox/src/potential.py)), el insumo laboral potencial depende de:
   $$L^*_t = WAP_t \times pr^*_t \times (1 - u^*_t)$$
   Donde $WAP_t$ es la población en edad de trabajar (alimentada por el canal migratorio) y $pr^*_t$ es la tasa de actividad tendencial.

3. **Evolución Tendencial en Proyección:**
   En el horizonte proyectado, la NAIRU no se congela artificialmente, sino que converge de forma suave hacia su nivel estructural de equilibrio de medio plazo ($u^*_{SS} \approx 8.8\% - 9.0\%$):
   $$u^*_t = \rho_{nairu} u^*_{t-1} + (1 - \rho_{nairu}) u^*_{SS}$$

#### 2. Dinámica del Desempleo Cíclico (Ley de Okun Completa en Niveles y Diferencias):
La tasa de desempleo desestacionalizada ($u^{SA}_t$) responde tanto al nivel de holgura económica (brecha de producción) como a la aceleración cíclica:
$$u^{SA}_t = u^*_t + \delta_u (u^{SA}_{t-1} - u^*_{t-1}) - \theta_{gap} \tilde{y}_t - \theta_{diff} (\tilde{y}_t - \tilde{y}_{t-1}) + \varepsilon^u_t$$
Donde:
* $\theta_{gap} > 0$: garantiza que si la economía opera por debajo de su potencial ($\tilde{y}_t < 0$), el paro se mantiene por encima de la NAIRU, evitando proyecciones planas o desconectadas del nivel de actividad.
* $\theta_{diff} > 0$: captura los costes de ajuste y la velocidad de creación/destrucción de empleo ante aceleraciones del PIB.
* $\delta_u \in (0, 1)$: parámetro de persistencia e inercia laboral (histéresis).

#### 3. Módulo Puente Aditivo de Estacionalidad de la EPA:
La serie observada de la Encuesta de Población Activa (EPA) no está corregida de estacionalidad y presenta un marcado patrón intra-anual recurrente. Para preservar la consistencia con las cifras oficiales sin alterar las relaciones estructurales de fondo, el modelo emplea una descomposición satélite aditiva centrada ($\sum_{q=1}^4 \gamma^{seas}_q = 0$):
$$u_t = u^{SA}_t + \gamma^{seas}_{quarter(t)}$$
Los factores estacionales históricos calculados sobre las desviaciones respecto a la media móvil ($MA(4)$) son:
* **T1:** $+0.52$ pp (repunte de invierno y fin de contratos de la campaña navideña).
* **T2:** $-0.12$ pp (campaña de primavera / Semana Santa / inicio estival).
* **T3:** $-0.30$ pp (punto álgido del empleo turístico estival).
* **T4:** $-0.10$ pp (otoño y transición invernal).

#### 4. Puente de Nowcasting Laboral (2026-T3 y 2026-T4):
Para evitar discontinuidades entre el último dato cerrado de la EPA (2026-T2) y el inicio del horizonte formal de previsión macroeconómica (2027-T1), los trimestres con PIB provisional de nowcast proyectan de forma endógena la tasa de paro desestacionalizada con Okun, recomponen la estacionalidad correspondiente al trimestre y estiman los ocupados mediante la elasticidad empleo-PIB:
$$E_t = E_{t-1} \times \left(1 + \beta_e \frac{\Delta Y_t}{Y_{t-1}}\right)$$

#### 5. Número de Ocupados y Productividad Aparente:
A partir de la población activa tendencial ($L_t$) y la tasa de paro:
$$E_t = L_t \times \left(1 - \frac{u_t}{100}\right)$$
$$\Delta \ln(Prod_t) = \Delta \ln(Y_t) - \Delta \ln(E_t)$$

---

### Bloque V: Crecimiento del PIB Real en Niveles y Metodología Oficial de Contabilidad Nacional

El producto interior bruto real se recompone a partir del PIB potencial proyectado ($Y_t^*$) y la brecha de producto simulada:

$$Y_t = Y_t^* \times \left(1 + \frac{\tilde{y}_t}{100}\right)$$

#### 1. Tasas Trimestrales e Interanuales:
$$\text{Crecimiento Intertrimestral } (t/t-1) = \left(\frac{Y_t}{Y_{t-1}} - 1\right) \times 100$$
$$\text{Crecimiento Interanual Trimestral } (t/t-4) = \left(\frac{Y_t}{Y_{t-4}} - 1\right) \times 100$$

#### 2. Tasa de Crecimiento Anual Oficial (Metodología Contabilidad Nacional INE / Eurostat):
En macroeconomía aplicada, la tasa de crecimiento de un año completo $T$ **nunca** se calcula como la media simple de las cuatro tasas interanuales trimestrales ($\frac{1}{4}\sum_{q=1}^4 yoy_{T,q}$), ya que este atajo ignora la dinámica intra-anual y el efecto arrastre (*carryover*).

En el modelo MEcPol, la tasa de crecimiento anual oficial se calcula como la variación porcentual entre las **medias anuales del PIB real en nivel** (o índice de volumen encadenado) de dos años consecutivos:

$$\bar{Y}_T = \frac{1}{4}\sum_{q=1}^4 Y_{T, q} \qquad \bar{Y}_{T-1} = \frac{1}{4}\sum_{q=1}^4 Y_{T-1, q}$$
$$g^{anual}_T = \left( \frac{\bar{Y}_T}{\bar{Y}_{T-1}} - 1 \right) \times 100$$

Esta formulación garantiza que las proyecciones anuales del modelo coincidan exactamente con la definición de Contabilidad Nacional de los cuadros macroeconómicos del INE, el Banco de España y los organismos internacionales.

---

### Bloque VI: PIB Potencial por Función de Producción (canal migratorio)

El PIB potencial ($Y_t^*$) no se toma como una tendencia estática, sino que se construye mediante una descomposición de crecimiento de tipo Cobb-Douglas:

$$g(Y_t^*) = (1-\alpha)\, g(L_t^*) + c^{K} + c^{PTF}$$

donde el **input laboral potencial** se calcula con los datos observados de la EPA:

$$L_t^* = \text{Población en edad de trabajar}_t \times \text{Tasa de actividad tendencial}_t \times \left(1 - \frac{\text{NAIRU}_t}{100}\right)$$

La tasa de actividad tendencial y la NAIRU se obtienen por filtro HP de las series observadas. La elasticidad del capital se fija en $\alpha = 0.35$. Las contribuciones tendenciales del capital ($c^{K} \approx 0.6$ pp) y de la PTF ($c^{PTF} \approx 0.5$ pp) se calibran al consenso del Banco de España (Documento Ocasional sobre la revisión del crecimiento potencial, 2026: potencial 2025-2028 $\approx 2.2\%$).

La consecuencia relevante es que la fuerte expansión de la población en edad de trabajar por **inmigración** entra directamente en el potencial: eleva $g(L_t^*)$ y, por tanto, $g(Y_t^*)$, reduciendo la brecha de producto a niveles coherentes con la posición cíclica (paro $\approx$ NAIRU $\Rightarrow$ brecha $\approx 0$). En proyección, la población en edad de trabajar se prolonga con una **desaceleración migratoria gradual**, lo que convierte al supuesto migratorio en una palanca de escenario. El nivel del potencial se ancla a la posición cíclica reciente; su lectura previa a 2020 debe tomarse con cautela al no incorporar un escalón explícito por el COVID.

---

### Bloque VII: Módulo Satélite de IPC Mensual (Bridge Model de Alta Frecuencia)

Para salvar la brecha temporal entre la frecuencia trimestral del núcleo macroeconómico y la necesidad de anticipar picos inflacionarios de alta frecuencia (como el shock de crudo del verano de 2026), MEcPol incorpora un **modelo puente satélite mensual** ([`src/monthly_cpi.py`](file:///C:/Users/Usuario/Documents/Github/DGSE/sandbox/src/monthly_cpi.py)):

1. **Datos de Entrada:**
   * Serie oficial del IPC mensual del INE (tabla `76130`, con desglose en General, Subyacente, Alimentos, Energía, Bienes y Servicios), leída del **almacén único** (`macro.db`, ingesta vía la API del INE); respaldo a CSV solo si el almacén está vacío.
   * Cotizaciones de crudo Brent (`fred_brent` del almacén, ingesta vía FRED) y gas Dutch TTF.
2. **Ecuación de Traspaso Mensual de Energía:**
   $$\pi^{energ}_m = \pi^{energ}_{m-1} + \eta_{brent} \left[ \Delta yoy(P^{brent}_m) - \Delta yoy(P^{brent}_{m-1}) \right]$$
   Donde $\eta_{brent} \approx 0.22$ es la elasticidad empírica de transmisión mensual de carburantes y electricidad.
3. **Agregación por Ponderaciones Oficiales del INE:**
   $$\pi_m = 0.10\, \pi^{energ}_m + 0.75\, \pi^{core}_m + 0.15\, \pi^{alim}_m$$
   (ponderaciones idénticas a las del núcleo trimestral: servicios 0,42 + bienes 0,33 = subyacente 0,75; alimentos 0,15; energía 0,10).
4. **Reconciliación con la Senda Trimestral:**
   Las medias trimestrales del módulo mensual convergen armónicamente con la senda del modelo estructural macroeconómico mediante un proceso autorregresivo de suavizado forward.

---

## 3. Menú de Variables Exógenas (Generador de Escenarios)

Las siguientes variables son exógenas al sistema doméstico español y constituyen las palancas sobre las cuales se diseñan los escenarios de previsión:

| Variable | Notación | Fuente Habitual | Unidad |
| :--- | :--- | :--- | :--- |
| **Petróleo Brent** | $P^{oil}_t$ | ICE / FRED | USD / barril |
| **Gas Natural (TTF)** | $P^{gas}_t$ | Dutch TTF | EUR / MWh |
| **PIB Eurozona** | $g^{EU}_t$ | Eurostat / BCE | Tasa de variación interanual (%) |
| **PIB Estados Unidos** | $g^{US}_t$ | BEA / Federal Reserve | Tasa de variación interanual (%) |
| **PIB China** | $g^{CN}_t$ | NBS / FMI | Tasa de variación interanual (%) |
| **Prima de Riesgo España** | $spread_t$ | Tesoro / BdE | Puntos básicos (10Y vs Bund) |
| **Sesgo de política (opcional)** | $\varepsilon^{m}_t$ | Supuesto de escenario | pp sobre la regla de Taylor |

> **Nota**: el **tipo de interés del BCE** ($i^{BCE}_t$) dejó de ser exógeno: en la proyección lo fija la **regla de Taylor** del Bloque II. Un escenario solo puede desviarlo de la regla mediante el sesgo `monetary_shock` ($\varepsilon^m_t$). En la muestra histórica se usa el tipo observado.
