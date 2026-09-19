---
name: esade-ecpol-report-design
description: >-
  Sistema de diseño, especificación técnica y repositorio de versiones de
  maquetación para informes ejecutivos en PDF y Markdown con la identidad visual
  oficial de EsadeEcPol (Center for Economic Policy). Permite reproducir al 100%
  cualquier versión de diseño, garantizando coherencia cromática, tipográfica y
  geométrica.
---

# EsadeEcPol Report Design & Layout Versioning System (Modelo MEcPol)

Esta skill define el estándar editorial, la arquitectura de diseño y el protocolo de versionado para la generación de informes macroeconómicos ejecutivos en PDF (mediante `ReportLab`) y Markdown para el **Modelo MEcPol** (*Modelo Macroeconómico de EsadeEcPol*).

---

## 1. Identidad Visual Oficial de EsadeEcPol (Tokens de Diseño)

Los valores cromáticos y tipográficos proceden directamente de las variables CSS `:root` de [esade.edu/ecpol](https://www.esade.edu/ecpol/es/):

### 1.1. Paleta de Colores Corporativa

| Token | Código Hex | Nombre Esade | Uso Editorial |
| :--- | :---: | :--- | :--- |
| `--primary-color` | `#000b3d` | **Deep Navy** | Wordmark de cabecera, títulos H1/H2, cabecera de tablas principales, cifras KPI mayores. |
| `--secondary-color` | `#0e1e63` | **Midnight Navy** | Fondos oscuros alternativos, bordes de contraste fuerte. |
| `--header-color` | `#1e4192` | **Esade Royal Blue** | Líneas divisorias de cabecera, subtítulos de sección, franja lateral en callouts de actividad, enlaces. |
| `--danger-color` | `#ff5a5f` | **Esade Coral** | Franja lateral y badges para choques de oferta, energía e inflación volátil. |
| `--multiply-color` | `#505b8c` | **Slate Blue** | Micro-etiquetas secundarias, notas técnicas y leyendas de apoyo. |
| `--tag-color` | `#767d8a` | **Metadata Grey** | Subtítulos institucionales, fechas, fuentes y notas a pie de página. |
| `--tag-hover-color` | `#161616` | **Neutral Dark** | Texto corrido del cuerpo (body text) de alta legibilidad sobre fondo blanco. |
| `--bg-card` | `#f8fafc` | **Off-white Soft** | Fondo de tarjetas KPI, filas alternas de tablas y recuadros de análisis. |
| `--highlight-bg` | `#eef2ff` | **Ice Blue** | Fondo de resaltado para la fila del propio modelo en tablas comparativas. |
| `--border-color` | `#e2e8f0` | **Border Slate** | Líneas de división de tablas y bordes de tarjetas. |
| `--positive-color` | `#16a34a` | **Green Alert** | Micro-indicadores positivos (crecimiento, empleo). |

### 1.2. Sistema Tipográfico Dual (Serif Display + Sans Técnico)

EsadeEcPol utiliza una combinación deliberada de una tipografía con serifa rotunda y elegante para los titulares institucionales, y una sans-serif geométrica para los bloques de datos y análisis:

* **Títulos y Display (*Esade Serif*):** 
  * Sistema: `Georgia-Bold` (`C:\Windows\Fonts\georgiab.ttf`).
  * Propósito: Título principal de portada (19 pt / leading 23), títulos de sección (12.5 pt / leading 16.5) y cifras de las tarjetas KPI (13.5 pt).
* **Cuerpo, Tablas y Metadatos (*Esade Sans*):**
  * Sistema: `Calibri / Mabry Pro` (`C:\Windows\Fonts\calibri.ttf`, `calibrib.ttf`, `calibrii.ttf`).
  * Propósito: Texto de análisis (8.5 pt / leading 11.5), cabeceras de tabla (7.5 pt bold), celdas de datos (7.5 pt) y metadatos de cabecera (8-9 pt).

---

## 2. Geometría y Reglas de Maquetación de Página (A4)

```
+-------------------------------------------------------------+
| Margin Top: 42 pt                                           |
| Running Header (EsadeEcPol | Macro y Fiscal)     h - 28 pt  |
| Header Divider Line (#1e4192, 1.2 pt)            h - 33 pt  |
+-------------------------------------------------------------+
|                                                             |
|   Usable Width:  523.27 pt  (595.27 - 2 x 36 pt margins)    |
|   Usable Height: 746.89 pt  (841.89 - 42 - 46 pt margins)   |
|                                                             |
+-------------------------------------------------------------+
| Footer Divider Line (#e2e8f0, 0.6 pt)                 36 pt |
| Running Footer ("Página X de Y" + filiación)          24 pt |
| Margin Bottom: 46 pt                                        |
+-------------------------------------------------------------+
```

### 2.1. Regla de Oro: Proporción 1:1 de Gráficos (Sin Distorsión)
Para evitar que los gráficos se vean achatados o estirados, **NUNCA** se deben forzar el ancho y el alto de forma independiente sin calcular la relación de aspecto nativa:

$$\text{Alto Deseado} = \frac{\text{Ancho Utilizable (515 pt)}}{\text{Aspect Ratio Nativo } (W / H)}$$

* **Dashboard Trimestral (Fan Charts):** Nativo `2232 x 1477` (Ratio 1.51) $\rightarrow$ Ancho: `515 pt`, Alto: `315 pt`.
* **Comparativas Mensuales IPC:** Nativo `2082 x 1330` (Ratio 1.565) $\rightarrow$ Ancho: `515 pt`, Alto: `329 pt`.
* **Comparativa de Escenarios Trimestral:** Nativo `2385 x 669` (Ratio 3.565) $\rightarrow$ Ancho: `515 pt`, Alto: `144 pt`.

### 2.2. Regla Innegociable de Precisión Numérica (Decimales)
En todos los informes ejecutivos, tablas institucionales, tarjetas KPI, resúmenes analíticos y anotaciones gráficas:
* **Tasas de Crecimiento (PIB real interanual, intertrimestral, potencial):** **1 solo decimal** (ej. `2,7%`, `2,2%`, `0,5%`). **NUNCA** dos decimales.
* **Tasas de Inflación (General, subyacente, energía, alimentos, servicios, bienes):** **1 solo decimal** (ej. `3,3%`, `2,2%`, `2,8%`).
* **Brecha de Producción (Output Gap):** **1 solo decimal** (ej. `-0,2%`, `-0,3%`).
* **EXCEPCIONES con DOS decimales:**
  * **Tasa de Paro EPA / NAIRU:** **2 decimales** obligatorios (ej. `10,10%`, `9,38%`, `9,16%`, `8,85%`, `9,22%`).
  * **Tipos de Interés / Euríbor (3M, 12M, BCE):** **2 decimales** obligatorios (ej. `3,11%`, `3,44%`, `3,60%`, `2,94%`).

### 2.3. Metodología de Contabilidad Nacional para el Crecimiento Anual del PIB
En macroeconomía aplicada y Contabilidad Nacional Trimestral (INE / Eurostat), la tasa de crecimiento anual del PIB real para un año $T$ **NUNCA** se calcula como la media aritmética simple de las cuatro tasas interanuales trimestrales:

$$\text{INCORRECTO: } g_T \neq \frac{1}{4}\sum_{q=1}^4 yoy_{T, q}$$

**Metodología Oficial Obligatoria (Medias Anuales en Nivel):**
Se proyecta la serie del PIB real en nivel $Y_t$ (o índice de volumen encadenado a partir de las tasas intertrimestrales $q/q-1$). El crecimiento anual es la variación porcentual entre las medias anuales (o sumas anuales) de dos años consecutivos:

$$\bar{Y}_T = \frac{1}{4}\sum_{q=1}^4 Y_{T, q} \qquad \bar{Y}_{T-1} = \frac{1}{4}\sum_{q=1}^4 Y_{T-1, q}$$
$$g_T = \left( \frac{\bar{Y}_T}{\bar{Y}_{T-1}} - 1 \right) \times 100$$

Esta fórmula respeta el efecto arrastre (*carryover effect*), la composición intra-anual y coincide exactamente con las cifras reportadas por el INE y organismos internacionales.

---

## 3. Histórico de Versiones de Maquetación

### Versión 1.0 — Diseño Base DGSE (Histórico)
* **Archivo de referencia:** Versión preliminar inicial.
* **Paleta:** Azul marino genérico (`#1f77b4`), escala de grises básica.
* **Tipografía:** Helvetica estándar en todo el documento.
* **Limitación identificada:** Gráficos mensuales comprimidos verticalmente en una sola página.

### Versión 2.0 — Estándar Editorial EsadeEcPol Policy Brief (Vigente)
* **Archivo generador:** [`sandbox/src/pdf_generator.py`](file:///C:/Users/Usuario/Documents/Github/DGSE/sandbox/src/pdf_generator.py)
* **Características:**
  1. **Página 1:** Portada ejecutiva tipo Policy Brief con tag temático, 5 tarjetas KPI, Cuadro Comparativo Institucional (9 organismos) y bloque de diagnóstico con filete lateral en `#1e4192`.
  2. **Página 2:** Dashboard trimestral con fan charts al 50% y 80%, incorporando tasa de paro EPA con estacionalidad y NAIRU de fondo.
  3. **Página 3:** Gráfico mensual de comparativa de escenarios de inflación a tamaño completo (relación nativa exacta 1.565, sin distorsión) y diagnóstico macroeconómico.
  4. **Página 4:** Gráfico mensual de desglose por componentes (energía, alimentos, servicios, bienes) a tamaño completo (relación nativa exacta 1.565) con filete coral (`#ff5a5f`).
  5. **Página 5:** Comparativa de escenarios a medio plazo (ratio 3.565), tabla detallada trimestre a trimestre (12 trimestres) y balance de riesgos final.
  6. **Canvas dinámico en dos pasadas:** Numeración automática `Página X de 5` y encabezado institucional persistente.

---

## 4. Protocolo para Crear una Nueva Versión (v2.1, v3.0, etc.)

Cuando se solicite o se decida evolucionar la maquetación:

1. **Crear la especificación de la nueva versión:** Registrar en la carpeta `versions/` un archivo markdown con los cambios (ej. `v3_corporate_redesign.md`).
2. **Actualizar los tokens en `pdf_generator.py`:** Mantener las constantes `COLOR_*` y `FONT_*` documentadas.
3. **Validar las proporciones nativas de las figuras:** Comprobar con PIL el aspect ratio de cada imagen generada por matplotlib antes de fijar las dimensiones en ReportLab.
4. **Inspección visual:** Compilar el PDF y renderizar cada página a PNG con `fitz` (PyMuPDF) a 150 DPI para verificar alineación, legibilidad y ausencia de solapamientos.
