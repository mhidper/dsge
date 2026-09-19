# Resumen: Ingestión de Datos y Actualización del Modelo

Este documento resume cómo el modelo Semi-DSGE se alimenta de datos reales y qué variables están actualizadas hasta el 2T de 2026, así como el manejo del trimestre en curso.

### 1. Jerarquía de Ingestión de Datos
El modelo (a través de `data_pipeline.py`) no coge los datos de un único sitio, sino que aplica una **jerarquía de tres niveles** para decidir qué dato manda:

1. **CSVs limpios (`data/nuevos/`) [Máxima prioridad]:** Si hay un archivo aquí (como los datos diarios del Brent o la EPA limpia `empleo_epa_2002_2026T2.csv`), el modelo lo usa por encima de cualquier otra cosa. Estos son los datos más actualizados y fáciles de procesar.
2. **Archivos Excel crudos (`data/raw/`) [Segunda opción]:** Si no hay CSV limpio para una variable, el modelo busca en los Excel originales (`series_trimestrales.xlsx`, `series_mensuales.xlsx`, etc.). Estos contienen el grueso de las variables (PIB de la UE, consumo, tipos de interés, etc.).
3. **Snapshot Oficial (`data/actualizacion_oficial_2025_2026.csv`) [Red de seguridad]:** Este archivo actúa como ancla. Siempre sobrescribe el tramo 2025T1-2026T2 con los datos oficiales ya cerrados por el INE o el Banco de España para asegurar que la estimación arranca desde el dato real y no desde un Excel desfasado.

### 2. Variables actualizadas hasta 2026T2
Gracias a los archivos limpios y al *snapshot* oficial, las principales variables macro ya están cerradas hasta el segundo trimestre de 2026. Entre ellas:
* **Mercado laboral:** Población activa, ocupados y tasa de paro (vienen de `empleo_epa_2002_2026T2.csv`).
* **PIB y Contabilidad Nacional:** El PIB real de España (viene de `pib_real_cvec_indice.csv`), consumo de hogares, FBCF y exportaciones.
* **Inflación trimestral:** El IPC general y sus subcomponentes (energía, alimentos, etc.).
* **Entorno internacional:** Tipos de interés del BCE, PIB de la Eurozona/EE.UU. y tipo de cambio.

### 3. ¿Cómo maneja el "Nowcasting" (Trimestre actual - 2026T3)?
Para los meses en los que el INE aún no ha publicado datos oficiales:

* **Para el PIB:** El pipeline se conecta a un módulo hermano (el `crisistrackerv2`). De ahí extrae la estimación de crecimiento intertrimestral del trimestre en curso (T3) y del siguiente (T4). Estas estimaciones provisionales se enganchan al último dato oficial (T2 de 2026). En cuanto el INE publica el T3 oficial, se actualiza el CSV de *snapshot* y el modelo automáticamente sustituye el *nowcast* por el dato real.
* **Para la Inflación y Energía:** Para proyectar el trimestre actual y desagregarlo mes a mes, el modelo utiliza datos de **alta frecuencia**. Toma el archivo de precios diarios del petróleo (`brent_daily.csv`), lo convierte a frecuencia mensual y aplica una elasticidad del 0,22. Esto permite que el modelo reaccione en tiempo real a shocks (como la subida del crudo) antes de que termine el trimestre.

En resumen: el modelo lee el histórico de fuentes oficiales hasta el último trimestre cerrado (2026T2), usa datos de alta frecuencia (diarios/semanales) para "adivinar" el trimestre actual, y proyecta a partir de ahí.
