# Informe Ejecutivo de Previsiones Macroeconómicas para España
**Modelo MEcPol v2.0 (EsadeEcPol)**  
**Escenario Evaluado:** `BASELINE`  
**Horizonte:** 2027-Q1 a 2029-Q4 (12 trimestres)

---

## 1. Resumen Ejecutivo y Diagnóstico

1. **Crecimiento**: en el escenario proyectado, el PIB real avanzaría a una media del **2.3%** interanual en el horizonte, con un perfil sin trimestres de contracción intertrimestral. El primer año se situaría en torno al **2.6%** (tasa anual de Contabilidad Nacional sobre medias del PIB en nivel proyectado) y el ritmo al cierre del horizonte rondaría el **2.3%**, en convergencia hacia el crecimiento potencial supuesto.
2. **Inflación**: la inflación general alcanzaría su máximo en **2027-Q1** (3.1%), por encima del objetivo del 2%, para cerrar el horizonte cerca del **1.4%**. La subyacente marcaría un máximo próximo al **3.2%**. Conviene recordar que el perfil de inflación depende de forma directa de la senda de energía supuesta en el escenario.
3. **Mercado laboral**: la tasa de paro pasaría del **10.10%** inicial al **9.22%** al final del horizonte (tendencia a la baja), en coherencia con la brecha de producto simulada y la NAIRU supuesta.

---

## 2. Proyecciones Resumidas por Año

*Nota: La tasa del PIB real refleja el crecimiento anual oficial (variación entre medias anuales consecutivas de la serie del PIB en nivel, metodología INE).*

| Año | PIB Real (% anual Cont. Nac.) | Tasa de Paro (% media) | Inflación General (% media) | Inflación Subyacente (% media) |
| :---: | :---: | :---: | :---: | :---: |
| **2027** | 2.6% | 9.50% | 2.2% | 2.7% |
| **2028** | 2.1% | 9.44% | 1.4% | 2.0% |
| **2029** | 2.2% | 9.37% | 1.4% | 1.8% |

---

## 3. Panel Gráfico de Previsiones (Fan Charts)

El siguiente panel presenta las sendas proyectadas junto a las bandas de probabilidad al 50% y 80%:

![Panel de Previsiones](figures/dashboard_prevision_baseline.png)

---

## 4. Detalle Trimestre a Trimestre

|         |   PIB (% i.a.) |   PIB (% t/t-1) |   Brecha PIB (%) |   Tasa Paro (%) |   Inflación Gen (%) |   Inflación Sub (%) |   Petróleo ($) |   Tipo BCE (%) |
|:--------|---------------:|----------------:|-----------------:|----------------:|--------------------:|--------------------:|---------------:|---------------:|
| 2027-Q1 |            2.8 |             0.6 |             -0.2 |           10.1  |                 3.1 |                 3.2 |            102 |           2.36 |
| 2027-Q2 |            2.7 |             0.6 |             -0.2 |            9.38 |                 2.2 |                 2.8 |             95 |           2.69 |
| 2027-Q3 |            2.6 |             0.5 |             -0.2 |            9.16 |                 1.8 |                 2.5 |             84 |           2.85 |
| 2027-Q4 |            2.3 |             0.5 |             -0.2 |            9.35 |                 1.6 |                 2.3 |             74 |           2.88 |
| 2028-Q1 |            2.2 |             0.5 |             -0.2 |            9.97 |                 1.4 |                 2.1 |             66 |           2.84 |
| 2028-Q2 |            2.1 |             0.5 |             -0.3 |            9.33 |                 1.4 |                 2   |             64 |           2.75 |
| 2028-Q3 |            2.1 |             0.5 |             -0.3 |            9.14 |                 1.4 |                 1.9 |             63 |           2.65 |
| 2028-Q4 |            2.1 |             0.5 |             -0.3 |            9.33 |                 1.4 |                 1.9 |             63 |           2.53 |
| 2029-Q1 |            2.2 |             0.6 |             -0.3 |            9.94 |                 1.4 |                 1.8 |             64 |           2.43 |
| 2029-Q2 |            2.2 |             0.6 |             -0.2 |            9.27 |                 1.4 |                 1.8 |             65 |           2.33 |
| 2029-Q3 |            2.3 |             0.6 |             -0.2 |            9.06 |                 1.4 |                 1.8 |             66 |           2.25 |
| 2029-Q4 |            2.3 |             0.6 |             -0.2 |            9.22 |                 1.4 |                 1.8 |             67 |           2.19 |


---

## 5. Comparativa entre Escenarios Alternativos

![Comparativa de Escenarios](figures/comparativa_escenarios.png)

* **Escenario Base (consenso)**: Incorpora el shock energético en curso y su resolución gradual. Brent anclado a la senda de consenso (EIA STEO, sep-2026): ~91 USD de media en 2026 y descenso hacia 64-67 USD a lo largo de 2027-2028. BCE en torno al 2.0%-2.25%.
* **Escenario Adverso**: Escalada geopolítica (cierre del estrecho de Ormuz) con Brent hacia 120-128 USD, gas al alza, BCE subiendo al 3.25% y recesión en la Eurozona. Estanflación seguida de recesión desinflacionaria.
* **Escenario Favorable**: Resolución rápida de la oferta (restauración de rutas de suministro), Brent de vuelta a 60-65 USD, desinflación y recortes del BCE hacia el 1.75%.

---

## 6. Módulo Satélite: Perfil Mensual de Inflación y Captura del Pico de Septiembre 2026 (Crudo Brent Actualizado)

Para complementar la simulación trimestral y evitar que la media trimestral suavice el impacto del shock energético, se incorpora la desagregación mensual combinando los datos oficiales de la **tabla 76130 del INE** con las series de alta frecuencia de crudo Brent:

* **Último Dato Oficial Publicado por el INE:** Registrado en **agosto de 2026** (4.3% general, 16.9% energía).
* **Pico Global de la Crisis (Nowcast de Alta Frecuencia):** Registrado en **September de 2026**, alcanzando una tasa interanual del **4.9%**, impulsado por el repunte del crudo Brent (media mensual de ~110 USD/barril y picos diarios de 130.80 USD) que eleva la inflación energética hasta el **22.9%** (con la subyacente contenida en el **3.0%**).
* **Trayectoria Posterior:** A partir del cuarto trimestre de 2026, la proyección recoge la absorción gradual del shock y el efecto escalón a la baja hacia el objetivo del BCE (2%).

![Perfil Mensual de Inflación](figures/ipc_mensual_desagregado.png)

### Evolución Mensual en 2026 (Datos Oficiales INE y Cierre de Año):

| date    | Trimestre   |   General (%) |   Subyacente (%) |   Energía (%) | Fuente / Estado         |
|:--------|:------------|--------------:|-----------------:|--------------:|:------------------------|
| 2026-01 | 2026-Q1     |           2.3 |              2.6 |          -2.5 | Oficial INE (Cerrado)   |
| 2026-02 | 2026-Q1     |           2.3 |              2.7 |          -3.1 | Oficial INE (Cerrado)   |
| 2026-03 | 2026-Q1     |           3.4 |              2.9 |           7.3 | Oficial INE (Cerrado)   |
| 2026-04 | 2026-Q2     |           3.2 |              2.8 |           6.6 | Oficial INE (Cerrado)   |
| 2026-05 | 2026-Q2     |           3.2 |              3   |           5.9 | Oficial INE (Cerrado)   |
| 2026-06 | 2026-Q2     |           3.2 |              2.9 |           6.7 | Oficial INE (Cerrado)   |
| 2026-07 | 2026-Q3     |           3.6 |              3   |          10.1 | Oficial INE (Cerrado)   |
| 2026-08 | 2026-Q3     |           4.3 |              2.9 |          16.9 | Oficial INE (Cerrado)   |
| 2026-09 | 2026-Q3     |           4.9 |              3   |          22.9 | Nowcast Alta Frecuencia |
| 2026-10 | 2026-Q4     |           4.3 |              2.8 |          19.3 | Nowcast Alta Frecuencia |
| 2026-11 | 2026-Q4     |           3.9 |              2.7 |          17   | Nowcast Alta Frecuencia |
| 2026-12 | 2026-Q4     |           3.6 |              2.6 |          15.5 | Nowcast Alta Frecuencia |

### Comparativa de Inflación Mensual entre Escenarios

El siguiente gráfico compara las trayectorias mensuales esperadas de inflación general y energía según el escenario macroeconómico considerado:

![Comparativa de Inflación Mensual](figures/comparativa_ipc_mensual_escenarios.png)

