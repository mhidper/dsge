---
name: lieflat-charts
description: >-
  Sistema de diseño de visualización editorial e interactiva basado en 'lieflat-charts'
  con la paleta corporativa y tipografía oficial de EsadeEcPol. Especializado en
  gráficos macroeconómicos (Fan Charts, descomposición aditiva de inflación, curvas
  de Phillips, matrices de escenarios y cuadros de mando en tiempo real para GitHub Pages).
---

# Lieflat Charts — Edición EsadeEcPol (MEcPol)

Esta skill proporciona los estándares, plantillas y tokens de diseño para generar visualizaciones macroeconómicas interactivas y editoriales en HTML/SVG autónomo, siguiendo la filosofía de *lieflat-charts* y la identidad visual corporativa de **EsadeEcPol** (definida en `esade-ecpol-report-design`).

---

## 1. Filosofía Visual y Estilos

1. **Lupi Editorial (Narrativa y Detalle)**:
   * Líneas capilares finas (`0.5–0.8px`).
   * Unidades honestas y reales (fechas trimestrales `YYYY-QX`, porcentajes con decimales exactos).
   * Anotaciones contextuales en puntos de inflexión históricos (p. ej. shock energético de 2022, pico inflacionario de agosto 2026).
   * Uso de micro-ticks y rejillas de fondo ultra-sutiles (`#e2e8f0` con `opacity: 0.6`).

2. **Glance (Decisión Rápida & KPIs)**:
   * Tarjetas ejecutivas con cifras destacadas en gran formato (`Georgia-Bold`).
   * Píldoras de estado (`badge`) con indicación de tendencia (positivo/verde `#16a34a`, alerta/coral `#ff5a5f`, neutral `#505b8c`).
   * Comparación visual de escenarios en paralelo con conmutadores instantáneos.

3. **Basics (Formas Estándar con Alta Calidad)**:
   * Fan Charts con áreas de densidad estocástica (percentiles 50% y 80%).
   * Gráficos de barras apiladas y áreas continuas para la descomposición del IPC por componentes.
   * Gráficos de dispersión (*scatter*) con trayectoria temporal enlazada para la Curva de Phillips.

---

## 2. Paleta Cromática Institucional de EsadeEcPol

Toda visualización producida bajo esta skill debe ceñirse estrictamente a la paleta corporativa:

```javascript
export const ESADE_THEME = {
  primary: '#000b3d',       // Deep Navy: Títulos principales, ejes base, serie histórica
  secondary: '#0e1e63',     // Midnight Navy: Fondos de tarjetas oscuras o bordes
  royalBlue: '#1e4192',     // Royal Blue: Serie de previsión central, enlaces, acentos
  coral: '#ff5a5f',         // Coral: Inflación, shock energético, alertas
  slateBlue: '#505b8c',     // Slate: Series secundarias, NAIRU, etiquetas auxiliares
  iceBlue: '#eef2ff',       // Ice Blue: Bandas de confianza, rellenos de resalte
  borderSlate: '#e2e8f0',   // Líneas divisorias y rejilla
  bgCard: '#f8fafc',        // Fondo suave de tarjetas y contenedores
  positive: '#16a34a',      // Crecimiento favorable, empleo
  warning: '#f59e0b',       // Previsiones con alta dispersión
  textDark: '#161616',      // Texto principal
  textMuted: '#767d8a'      // Metadatos, fuentes, notas técnicas
};
```

---

## 3. Reglas Innegociables de Formato Numérico
* **Tasas de Crecimiento del PIB (% anual / trimestral):** Exactamente **1 decimal** (ej. `2,7%`, `2,2%`, `0,5%`). Nunca dos decimales.
* **Inflación y Desempleo (%):** **1 o 2 decimales** según el contexto (generalmente 2 decimales en IPC mensual del INE y tasa de paro de la EPA).
* **Tipos de Interés (%):** **2 decimales** (ej. `3,25%`, `2,75%`).
* **Separador de decimales:** Coma (`,`) en textos en español; punto (`.`) en inglés o código JavaScript interno.

---

## 4. Despliegue en GitHub Pages (`docs/`)
Los gráficos se exportan directamente como componentes web autónomos en `docs/index.html` que leen de `docs/data/latest_forecast.json`, garantizando que cualquier actualización en el motor `run_forecast.py` se refleje inmediatamente en el portal web sin necesidad de compilación adicional.
