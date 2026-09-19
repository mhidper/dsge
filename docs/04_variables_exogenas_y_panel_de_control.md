# Variables Exógenas y Panel de Control del Modelo

Este documento especifica **qué variables debe decidir el usuario antes de cada estimación** y cómo se traducirían a un futuro cuadro de mando (checks para activar/desactivar medidas, y campos de valor o de senda para las exógenas). No es un informe de resultados: es el contrato de entradas del modelo.

La lógica es la de un modelo semiestructural de economía abierta en unión monetaria: el sistema resuelve endógenamente actividad, precios, empleo y —desde la Fase 5— el tipo del BCE; pero necesita que se le fije el **entorno exterior, financiero, fiscal y regulatorio**. Esas son las palancas de escenario. Cambiarlas y reproyectar es el uso normal del modelo.

---

## 1. Cómo leer cada control

Cada variable se clasifica por el **tipo de control** que le corresponde en el panel:

- **Senda** — trayectoria trimestral a lo largo del horizonte (12 trimestres por defecto). En el panel sería una curva editable o una elección entre plantillas.
- **Valor terminal** — un único número al que la variable converge; el modelo interpola desde el último dato observado. Un campo numérico.
- **Check (on/off)** — un interruptor para activar o no una medida, con su ventana de fechas y magnitud.
- **Selector** — una elección entre opciones predefinidas.

La columna **Decisión requerida** indica qué tiene que fijar el usuario. La columna **Por defecto / fuente** indica de dónde sale el valor si no se toca.

---

## 2. Precios de la energía  *(senda)*

Son la palanca de primer orden sobre la inflación. El **histórico es real y se actualiza solo** desde FRED en cada reestimación (`refresh_energy_data.py`); lo que el usuario decide es la **senda futura**.

| Variable | Qué es | Rol | Decisión requerida | Por defecto / fuente |
| :-- | :-- | :-- | :-- | :-- |
| `oil_price_brent` | Brent, USD/barril | Motor del IPC energético (carburantes) y coste de bienes | Senda forward 12T | Baseline anclado a EIA STEO ajustado por riesgo (arranque ~110, converge ~80) |
| `gas_price_ttf` | Gas TTF, EUR/MWh | IPC energético (electricidad/gas), amortiguado | Senda forward 12T | Baseline ~55 → ~36 |

> **Pendiente (fase de supuestos):** automatizar la senda forward tirando de futuros (ICE Brent/TTF) y del STEO/Banco Mundial, igual que ya se automatizó el histórico. Hasta entonces, la senda del escenario es una decisión manual del usuario.

---

## 3. Demanda externa  *(valor terminal)*

Brechas de producto de los socios comerciales. Traccionan la curva IS española.

| Variable | Qué es | Decisión requerida | Por defecto (baseline / adverso / favorable) |
| :-- | :-- | :-- | :-- |
| `output_gap_eu` | Brecha de producto de la Eurozona (%) | Valor terminal | +0,1 / −1,8 / +0,7 |
| `output_gap_usa` | Brecha de producto de EE.UU. (%) | Valor terminal | +0,2 / −0,8 / +0,6 |
| `output_gap_china` | Brecha de producto de China (%) | Valor terminal | +0,1 / −1,0 / +0,5 |

---

## 4. Condiciones financieras

| Variable | Qué es | Tipo | Decisión requerida | Por defecto |
| :-- | :-- | :-- | :-- | :-- |
| `risk_premium_spain` | Prima de riesgo soberana (pp, 10A vs Bund) | Valor terminal | Valor terminal | 0,75 / 1,50 / 0,50 |
| `monetary_shock` | Sesgo hawkish/dovish **sobre** la regla de Taylor del BCE | Valor (pp) | Opcional; por defecto 0 | 0 |

> **Importante — el tipo del BCE ya NO es una variable exógena.** Desde la Fase 5 lo fija endógenamente la regla de Taylor (responde a subyacente y brecha). El usuario ya no elige la senda del tipo; solo puede introducir un sesgo puntual con `monetary_shock` si quiere una política más dura o más laxa que la que dicta la regla.

---

## 5. Política fiscal y turismo

| Variable | Qué es | Tipo | Decisión requerida | Por defecto |
| :-- | :-- | :-- | :-- | :-- |
| `fiscal_impulse` | Impulso fiscal neto, incl. ejecución NGEU (% PIB) | Senda | Valor terminal | 0,1 / −0,3 / 0,2 |
| `tourism_demand` | Brecha de demanda turística internacional | Senda (opcional) | Fijar o dejar el proxy | Proxy de la brecha UE ×0,4 si no se fija |

---

## 6. Oferta potencial  *(palanca de largo plazo)*

| Variable | Qué es | Tipo | Decisión requerida | Por defecto |
| :-- | :-- | :-- | :-- | :-- |
| `migration_wap_growth` | Ritmo de crecimiento de la población en edad de trabajar por inmigración | Valor | Fijar o dejar la desaceleración gradual | Desaceleración migratoria trimestral (config) |

Esta palanca mueve el PIB potencial (y, por tanto, la brecha): una inmigración más fuerte eleva el potencial y reduce la brecha. Es la palanca de escenario de oferta.

---

## 7. Medidas regulatorias/fiscales sobre la energía  *(checks on/off)*

Intervenciones temporales que abaratan el IPC energético mientras rigen. Se modelan como **superposiciones de nivel conmutables** (`POLICY_MEASURES`), separadas de las elasticidades estructurales. En el histórico ya están fechadas y activas; en **proyección** el usuario decide si alguna vuelve a estar vigente (`POLICY_MEASURES_FORECAST`).

| Medida | Check | Ventana | Magnitud (pp sobre IPC energético) | Estado de la cifra |
| :-- | :-- | :-- | :-- | :-- |
| Bonificación 20 cts combustibles | on/off | fechas | −5,7 | Estimada (sólida) |
| IVA eléctrico 21→10% | on/off | fechas | −2,9 | Mecánica |
| IVA eléctrico 10→5% | on/off | fechas | −1,5 | Mecánica |
| Excepción ibérica (tope al gas) | on/off | fechas | −3,0 | **Indicativa — refinar con cifra oficial** |

Para simular "¿y si vuelve el tope al gas en 2027?": marcar el check, fijar su ventana futura y su magnitud, y reproyectar. No requiere reestimar. Cada check del panel corresponde a una entrada en `POLICY_MEASURES_FORECAST`.

---

## 8. Selectores globales

| Selector | Qué controla | Opciones / por defecto |
| :-- | :-- | :-- |
| `scenario_type` | Plantilla de escenario | baseline / adverse_energy_rates / favorable_disinflation / (custom) |
| `horizonte` | Nº de trimestres a proyectar | 12 por defecto (8–12) |
| `auto_refresh` | Refresco automático de datos de energía | On por defecto; Off para reproducibilidad estricta |

---

## 9. Lo que NO es decisión de escenario

Para evitar confusión en el panel, conviene separar lo exógeno (arriba) de lo que es **estructura del modelo** y no se toca en cada corrida:

- **Endógeno** (lo resuelve el modelo): PIB y brecha, inflación general/subyacente/servicios/bienes/alimentos/energía, paro y empleo, tipo de interés español y **tipo del BCE** (regla de Taylor), tipo de cambio real.
- **Parámetros estructurales** (calibrados/estimados, no son palancas de escenario): elasticidades del IPC energético (crudo 0,24, gas 0,05, persistencia 0,13), curvas de Phillips, curva IS, regla de Taylor, función de producción del potencial. Se revisan al recalibrar el modelo, no al cambiar de escenario.

---

## 10. Síntesis: el mínimo que exige tu decisión antes de estimar

En una corrida típica, las decisiones imprescindibles son:

1. **Escenario** (o senda de crudo y gas si es a medida).
2. **Brechas externas** (UE sobre todo).
3. **Impulso fiscal**.
4. **Prima de riesgo**.
5. **Qué medidas energéticas siguen o vuelven a estar vigentes** en el horizonte (checks).
6. Opcional: sesgo monetario, palanca migratoria, turismo.

Todo lo demás lo resuelve el modelo o viene de datos que ya se actualizan solos.
