# Guía de Escenarios, Previsión a Medio Plazo y Generación de Informes

Este documento detalla cómo se configuran los escenarios macroeconómicos mediante el **menú de variables exógenas**, cómo resuelve el modelo las trayectorias futuras de inflación, empleo y crecimiento, y cómo se generan automáticamente los informes ejecutivos en Markdown.

---

## 1. El Menú de Variables Exógenas

Dado que España es una economía pequeña y abierta dentro de una unión monetaria, su evolución a medio plazo está fuertemente condicionada por el entorno internacional y financiero. El modelo aísla un conjunto explícito de **variables exógenas clave**:

1. **Energía y Materias Primas**:
   - `oil_price_brent`: Precio del crudo Brent (USD por barril).
   - `gas_price_ttf`: Precio del gas natural europeo TTF (EUR/MWh).
2. **Entorno Global y Demanda Externa**:
   - `output_gap_eu`: Brecha de producto de la Eurozona (%).
   - `output_gap_usa`: Brecha de producto de Estados Unidos (%).
   - `output_gap_china`: Brecha de producto de China (%).
3. **Condiciones Financieras**:
   - `risk_premium_spain`: Prima de riesgo de la deuda soberana española (puntos básicos / %).
   - `monetary_shock` *(opcional)*: sesgo hawkish/dovish que se **superpone** a la regla de Taylor del BCE.
4. **Política Fiscal**:
   - `fiscal_impulse`: Impulso fiscal neto (incluyendo ejecución de transferencias NGEU como % del PIB).

> **El tipo del BCE ya no es una palanca de escenario.** Desde la Fase 5 lo fija endógenamente la **regla de Taylor** (ver doc 01, Bloque II): responde a la subyacente y a la brecha. Un escenario solo puede sesgarlo con `monetary_shock`. *(Nota técnica: `scenarios.py` aún escribe una senda `interest_rate_ecb` heredada que la proyección ignora; conviene retirarla o convertirla en `monetary_shock` — pendiente de limpieza.)*

---

## 2. Escenarios Predefinidos

El sistema incluye tres escenarios estándar para un horizonte de previsión de 8 a 12 trimestres (2 a 3 años vista):

> **Nota de coyuntura (sep-2026)**: la economía atraviesa un shock de oferta energético de primera magnitud (disrupciones en Oriente Medio). El Brent del 3T-2026 se estima en ~102 USD al contado con tendencia alcista. En consecuencia, el escenario **base** NO asume un crudo bajo: incorpora el shock y su resolución gradual (coherente con EIA STEO sep-2026 revisado al alza). Un crudo elevado es el central, no el adverso. Las sendas se prolongan con meseta en su valor terminal para permitir la convergencia del sistema. En los tres escenarios el **tipo del BCE es una respuesta endógena** (regla de Taylor), no un supuesto.

### Escenario 1: Base (Consenso con shock energético en resolución)
* **Petróleo**: parte de ~102 USD (3T-2026) y desciende a lo largo de 2027 (95 → 84 → 74 → 66), estabilizándose en 63-67 USD en 2028-2029.
* **Gas TTF**: ~58 EUR/MWh en el 3T-2026, normalización gradual hacia 32 EUR/MWh.
* **BCE (endógeno)**: la regla lo asienta en el entorno neutral (~2.3%) conforme la subyacente revierte al 2%.
* **Demanda Externa**: Eurozona en torno a su potencial; brechas externas próximas a cero.
* **Prima de riesgo**: estable en ~75 puntos básicos.

### Escenario 2: Escalada Geopolítica y Shock de Oferta (Adverso)
* **Petróleo**: cierre del estrecho de Ormuz; Brent de 112 hacia el pico de **155-158 USD** (2027Q1-Q2) y resolución lenta hasta 112.
* **Gas TTF**: alza hasta **120-125 EUR/MWh** en el pico, con normalización posterior.
* **BCE (endógeno)**: sube modestamente ante el repunte y luego **recorta hasta el suelo (0%)** al abrirse la recesión, arrestando la espiral deflacionaria.
* **Demanda Externa**: recesión en la Eurozona (brecha hacia −1.8%).
* **Prima de riesgo**: ampliación hasta ~150 puntos básicos.
* **Dinámica**: estanflación (pico de inflación de dos dígitos en energía) seguida de recesión desinflacionaria; brecha de producto que se estabiliza en torno a −4% (contenida por la respuesta monetaria).

### Escenario 3: Resolución Rápida de la Oferta y Desinflación (Favorable)
* **Petróleo**: restauración rápida del suministro; caída a 60-63 USD/barril.
* **Gas TTF**: descenso a 25-28 EUR/MWh.
* **BCE (endógeno)**: la regla lo mantiene algo por encima del neutral para contener el auge cíclico (brecha positiva).
* **Demanda Externa**: dinamismo industrial en Europa y tracción de EE.UU. y Asia.
* **Prima de riesgo**: reducción a 50 puntos básicos.

---

## 3. Mecanismo de Simulación y Resolución del Modelo

**Punto de arranque (jump-off).** La proyección parte del último dato disponible: dato oficial del INE cuando existe, y en su defecto la estimación de **nowcasting** (ver doc 02, §1.3) como INE provisional para el trimestre corriente y el siguiente.

El bloque es **recursivo** (no simultáneo): dentro de cada trimestre $t = T+1, \dots, T+H$ las ecuaciones se resuelven en cascada, y todos los cruces entre ecuaciones usan valores rezagados (predeterminados), lo que preserva la recursividad. El orden es:

1. **Inyección de exógenas**: se asignan los valores del escenario (energía, brechas externas, prima de riesgo, impulso fiscal).
2. **Política monetaria (regla de Taylor)**: se fija el tipo del BCE en respuesta a la subyacente y la brecha rezagadas, y de ahí el tipo español ($i_t = i^{BCE}_t + spread_t$).
3. **Demanda agregada (IS)**: se obtiene la brecha de producto con el tipo real, las brechas externas, el REER, el impulso fiscal y el turismo.
4. **Cascada de precios**: energía → acumulador de presión $Z^e$ → alimentos y subyacente (servicios y bienes, que leen la cuña general-núcleo rezagada) → agregación de la general y la subyacente.
5. **Mercado de trabajo**: tasa de paro con histéresis (Okun) y empleo en personas vía la elasticidad al PIB y la población activa.
6. **Recomposición de niveles y tasas**: PIB real en niveles y sus variaciones trimestral ($t/t-1$) e interanual ($t/t-4$).
7. **Abanicos de probabilidad (fan charts)**: 1.000 simulaciones de Monte Carlo con los errores estándar de la estimación histórica ($\sigma_\varepsilon$) y la variabilidad paramétrica, para bandas al 50%, 70% y 90%.

---

## 4. Generación Automática de Informes

La ejecución del modelo genera un informe completo en Markdown en la carpeta `sandbox/reports/`:

```bash
python sandbox/run_forecast.py --scenario baseline --horizon 12
```

El informe incluye:
- **Resumen Ejecutivo**: Principales conclusiones macroeconómicas del horizonte proyectado.
- **Tabla Resumen**: Proyecciones anuales y trimestrales de PIB, Empleo, Paro, Inflación General e Inflación Subyacente.
- **Gráficos de Previsión**: Curvas históricas empalmadas con las proyecciones y sus respectivos abanicos de incertidumbre.
- **Análisis de Sensibilidad**: Comparativa directa de los resultados entre los escenarios Base, Adverso y Favorable.
