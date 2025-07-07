# Modelos DSGE y Semi-DSGE para la Economía Española

Este repositorio contiene el desarrollo e implementación de modelos de Equilibrio General Dinámico y Estocástico (DSGE) y modelos Semi-DSGE para el análisis de la economía española.

## 📋 Contenido del Repositorio

### 📁 `src/` - Código Fuente y Análisis
- **`dgse.ipynb`** - Notebook principal con el modelo DSGE completo
- **`gdp_potential.ipynb`** - Análisis y estimación del PIB potencial de España
- **`semi-dsge.ipynb`** - Modelo Semi-DSGE básico
- **`semi-dsge II.ipynb`** - Extensión del modelo Semi-DSGE
- **`semi-dsge III.ipynb`** - Desarrollo avanzado del modelo Semi-DSGE
- **`semi-dsge IV.ipynb`** - Versión final y refinada del modelo Semi-DSGE
- **Archivos HTML** - Versiones exportadas de los notebooks para visualización web
- **Datos CSV** - Datasets procesados utilizados en los análisis

### 📁 `datos/` - Fuentes de Datos
- **`OPCE_Rastreador_T1_2025_BD.xlsx`** - Datos de seguimiento económico T1 2025
- **`series_trimestrales.xlsx`** - Series temporales trimestrales
- **`series_mensuales.xlsx`** - Series temporales mensuales  
- **`series_diarias.xlsx`** - Series temporales diarias
- **`indicadores mercado laboral.xlsx`** - Indicadores del mercado laboral español
- **`crudo.csv`** - Datos de precios del petróleo crudo

### 📁 `sec3_3_1_structural_domestic_MSEP/` - Literatura de Referencia
- **`3_3_1_Arroyo_Bullano_Fornero_Zuniga_2020.pdf`** - Paper de referencia sobre modelos estructurales domésticos
- **`replication_codes_MSEP/`** - Códigos de replicación del paper MSEP

## 🎯 Objetivos del Proyecto

1. **Modelado Macroeconómico**: Desarrollo de modelos DSGE para España
2. **Análisis Estructural**: Implementación de modelos Semi-DSGE para mayor flexibilidad
3. **PIB Potencial**: Estimación y análisis del producto potencial español
4. **Pronósticos**: Generación de proyecciones económicas a corto y medio plazo
5. **Validación Empírica**: Calibración y estimación con datos españoles

## 🔧 Tecnologías Utilizadas

- **Python** - Lenguaje principal de desarrollo
- **Jupyter Notebooks** - Ambiente de desarrollo y análisis
- **Pandas** - Manipulación y análisis de datos
- **NumPy** - Computación numérica
- **Matplotlib/Plotly** - Visualización de datos
- **Scipy** - Métodos de optimización y estadística

## 📊 Principales Variables Analizadas

- PIB y componentes del gasto
- Inflación y precios
- Mercado laboral (empleo, desempleo, salarios)
- Tipos de interés y variables financieras
- Comercio exterior
- Precios de materias primas (petróleo)

## 🚀 Cómo Usar

1. **Clonar el repositorio**:
   ```bash
   git clone https://github.com/mhidper/dsge.git
   cd dsge
   ```

2. **Instalar dependencias** (requiere Python 3.7+):
   ```bash
   pip install jupyter pandas numpy matplotlib scipy plotly
   ```

3. **Ejecutar los notebooks**:
   ```bash
   jupyter notebook
   ```

4. **Comenzar por**:
   - `src/dgse.ipynb` para el modelo DSGE completo
   - `src/gdp_potential.ipynb` para análisis del PIB potencial
   - `src/semi-dsge.ipynb` para modelos Semi-DSGE

## 📈 Estado del Proyecto

- ✅ Modelo DSGE base implementado
- ✅ Estimación PIB potencial completada
- ✅ Modelos Semi-DSGE desarrollados (versiones I-IV)
- ✅ Calibración con datos españoles
- 🔄 En desarrollo: Validación y mejoras del modelo

## 📄 Referencias

- Arroyo, Bullano, Fornero & Zuniga (2020) - "Structural domestic model for MSEP"
- Literatura adicional sobre modelos DSGE para economías pequeñas abiertas

## 👥 Contribuciones

Las contribuciones son bienvenidas. Por favor, abre un issue para discutir cambios importantes antes de implementarlos.

## 📄 Licencia

Este proyecto es de uso académico y de investigación.

---

*Proyecto desarrollado para el análisis macroeconómico de España mediante modelos DSGE y Semi-DSGE*