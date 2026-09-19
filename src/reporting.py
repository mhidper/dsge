"""
Generación de informes ejecutivos en Markdown y exportación de gráficos macroeconómicos (Fan Charts).
"""

from pathlib import Path
from typing import Dict, Optional
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from .config import REPORTS_DIR


def ensure_reports_dir() -> Path:
    """Asegura la existencia del directorio de informes y figuras."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    figs_dir = REPORTS_DIR / "figures"
    figs_dir.mkdir(parents=True, exist_ok=True)
    return figs_dir


def plot_forecast_dashboard(df_history: pd.DataFrame,
                            forecast_bands: Dict[str, Dict[str, np.ndarray]],
                            scenario_name: str = "baseline",
                            output_path: Optional[Path] = None) -> Path:
    """
    Genera un panel gráfico macroeconómico con las previsiones y sus bandas de incertidumbre (Fan Charts).
    """
    figs_dir = ensure_reports_dir()
    save_path = output_path or (figs_dir / f"dashboard_prevision_{scenario_name}.png")

    # Estilo visual limpio y profesional
    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
    fig, axes = plt.subplots(2, 2, figsize=(15, 10), dpi=150)
    fig.suptitle(f"Proyecciones Macroeconómicas para España - Escenario: {scenario_name.upper()}",
                 fontsize=16, fontweight='bold', y=0.98)

    # Ventana histórica a mostrar (últimos 16 trimestres / 4 años)
    hist_tail = df_history.tail(16).copy()
    last_date = hist_tail.index[-1]
    future_dates = forecast_bands['gdp_growth_annual']['dates']
    # Eje temporal continuo para la previsión (incluye el último punto histórico para empalme perfecto)
    proj_dates = [last_date] + list(future_dates)

    def attach_anchor(last_val: float, band_dict: Dict[str, np.ndarray]):
        """Antepone el último punto histórico a la previsión y a las bandas para continuidad visual."""
        return {
            'central': np.insert(band_dict['central'], 0, last_val),
            'p10': np.insert(band_dict['p10'], 0, last_val),
            'p25': np.insert(band_dict['p25'], 0, last_val),
            'p75': np.insert(band_dict['p75'], 0, last_val),
            'p90': np.insert(band_dict['p90'], 0, last_val),
        }

    # 1. Crecimiento del PIB Interanual
    ax1 = axes[0, 0]
    hist_gdp_yoy = hist_tail['gdp_real_spain'].pct_change(4) * 100.0
    last_gdp_val = hist_gdp_yoy.iloc[-1]
    b_gdp = attach_anchor(last_gdp_val, forecast_bands['gdp_growth_annual'])

    ax1.plot(hist_tail.index, hist_gdp_yoy, label='Histórico', color='#1f77b4', lw=2.2)
    ax1.plot(proj_dates, b_gdp['central'], label='Previsión Central', color='#2ca02c', lw=2.5)
    ax1.fill_between(proj_dates, b_gdp['p10'], b_gdp['p90'], color='#2ca02c', alpha=0.15, label='IC 80%')
    ax1.fill_between(proj_dates, b_gdp['p25'], b_gdp['p75'], color='#2ca02c', alpha=0.25, label='IC 50%')
    ax1.axvline(last_date, color='gray', linestyle=':', lw=1.2, alpha=0.8)
    ax1.axhline(0, color='gray', linestyle='--', lw=0.8)
    ax1.set_title("Crecimiento del PIB Real (% Interanual)", fontweight='bold', fontsize=12)
    ax1.set_ylabel("%")
    ax1.legend(loc='best', frameon=True)

    # 2. Inflación General y Subyacente
    ax2 = axes[0, 1]
    last_inf_val = hist_tail['inflation_total'].iloc[-1]
    b_inf = attach_anchor(last_inf_val, forecast_bands['inflation_total'])

    ax2.plot(hist_tail.index, hist_tail['inflation_total'], label='General (Histórico)', color='#d62728', lw=2.0)
    if 'inflation_core' in hist_tail.columns:
        ax2.plot(hist_tail.index, hist_tail['inflation_core'], label='Subyacente (Histórico)',
                 color='#ff7f0e', lw=1.8, linestyle='--')

    ax2.plot(proj_dates, b_inf['central'], label='General (Previsión)', color='#d62728', lw=2.5)
    ax2.fill_between(proj_dates, b_inf['p10'], b_inf['p90'], color='#d62728', alpha=0.15, label='IC 80% (General)')
    ax2.fill_between(proj_dates, b_inf['p25'], b_inf['p75'], color='#d62728', alpha=0.25, label='IC 50% (General)')

    if 'inflation_core' in forecast_bands and 'inflation_core' in hist_tail.columns:
        last_core_val = hist_tail['inflation_core'].iloc[-1]
        b_core = attach_anchor(last_core_val, forecast_bands['inflation_core'])
        ax2.plot(proj_dates, b_core['central'], label='Subyacente (Previsión)',
                 color='#ff7f0e', lw=2.2, linestyle=':')

    ax2.axvline(last_date, color='gray', linestyle=':', lw=1.2, alpha=0.8)
    ax2.axhline(2.0, color='black', linestyle=':', lw=1.2, label='Objetivo BCE (2%)')
    ax2.set_title("Inflación IPC (% Interanual)", fontweight='bold', fontsize=12)
    ax2.set_ylabel("%")
    ax2.legend(loc='best', frameon=True)

    # 3. Tasa de Paro
    ax3 = axes[1, 0]
    last_u_val = hist_tail['unemployment_rate'].iloc[-1]
    b_u = attach_anchor(last_u_val, forecast_bands['unemployment_rate'])

    ax3.plot(hist_tail.index, hist_tail['unemployment_rate'], label='EPA Observada', color='#9467bd', lw=2.2)
    ax3.plot(proj_dates, b_u['central'], label='Previsión (con estacionalidad)', color='#8c564b', lw=2.5)
    ax3.fill_between(proj_dates, b_u['p10'], b_u['p90'], color='#8c564b', alpha=0.15, label='IC 80%')
    ax3.fill_between(proj_dates, b_u['p25'], b_u['p75'], color='#8c564b', alpha=0.25, label='IC 50%')

    # Tendencia desestacionalizada / NAIRU
    if 'unemployment_rate_sa' in forecast_bands and 'unemployment_rate_sa' in hist_tail.columns:
        last_usa_val = hist_tail['unemployment_rate_sa'].iloc[-1]
        b_usa = attach_anchor(last_usa_val, forecast_bands['unemployment_rate_sa'])
        ax3.plot(hist_tail.index, hist_tail['unemployment_rate_sa'], color='#7f7f7f', lw=1.5, linestyle='--', label='Tendencia (SA)')
        ax3.plot(proj_dates, b_usa['central'], color='#7f7f7f', lw=1.8, linestyle='--', label='Tendencia Proyectada')
    elif 'nairu' in forecast_bands and 'nairu' in hist_tail.columns:
        last_n_val = hist_tail['nairu'].iloc[-1]
        b_n = attach_anchor(last_n_val, forecast_bands['nairu'])
        ax3.plot(hist_tail.index, hist_tail['nairu'], color='#7f7f7f', lw=1.5, linestyle=':', label='NAIRU')
        ax3.plot(proj_dates, b_n['central'], color='#7f7f7f', lw=1.8, linestyle=':', label='NAIRU Estructural')

    ax3.axvline(last_date, color='gray', linestyle=':', lw=1.2, alpha=0.8)
    ax3.set_title("Tasa de Desempleo (% Población Activa)", fontweight='bold', fontsize=12)
    ax3.set_ylabel("%")
    ax3.legend(loc='best', frameon=True, fontsize=8)

    # 4. Brecha de Producción (Output Gap)
    ax4 = axes[1, 1]
    last_gap_val = hist_tail['output_gap_spain'].iloc[-1]
    b_gap = attach_anchor(last_gap_val, forecast_bands['output_gap_spain'])

    ax4.plot(hist_tail.index, hist_tail['output_gap_spain'], label='Brecha Histórica', color='#17becf', lw=2.0)
    ax4.plot(proj_dates, b_gap['central'], label='Previsión Central', color='#1f77b4', lw=2.5)
    ax4.fill_between(proj_dates, b_gap['p10'], b_gap['p90'], color='#1f77b4', alpha=0.15, label='IC 80%')
    ax4.fill_between(proj_dates, b_gap['p25'], b_gap['p75'], color='#1f77b4', alpha=0.25, label='IC 50%')
    ax4.axvline(last_date, color='gray', linestyle=':', lw=1.2, alpha=0.8)
    ax4.axhline(0, color='gray', linestyle='--', lw=0.8)
    ax4.set_title("Brecha de Producción / Output Gap (% PIB Potencial)", fontweight='bold', fontsize=12)
    ax4.set_ylabel("%")
    ax4.legend(loc='best', frameon=True)

    for ax in axes.flat:
        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        ax.tick_params(axis='x', rotation=30)

    plt.tight_layout()
    fig.savefig(save_path, bbox_inches='tight')
    plt.close(fig)
    return save_path


def plot_scenario_comparison(comparison_dfs: Dict[str, pd.DataFrame],
                             df_history: Optional[pd.DataFrame] = None,
                             output_path: Optional[Path] = None) -> Path:
    """Genera gráfico comparativo entre los diferentes escenarios macroeconómicos."""
    figs_dir = ensure_reports_dir()
    save_path = output_path or (figs_dir / "comparativa_escenarios.png")

    fig, axes = plt.subplots(1, 3, figsize=(16, 4.5), dpi=150)
    fig.suptitle("Comparativa de Escenarios a Medio Plazo (2026 - 2029)", fontsize=14, fontweight='bold')

    colors = {'baseline': '#2ca02c', 'adverse_energy_rates': '#d62728', 'favorable_disinflation': '#1f77b4'}
    labels = {'baseline': 'Base (Consenso)', 'adverse_energy_rates': 'Adverso (Energía/Tipos)', 'favorable_disinflation': 'Favorable'}

    # Si se proporciona df_history, extraer anclaje
    has_hist = df_history is not None and len(df_history) > 0
    if has_hist:
        hist_tail = df_history.tail(8).copy()
        last_d = hist_tail.index[-1]
        hist_gdp_yoy = hist_tail['gdp_real_spain'].pct_change(4) * 100.0
        last_gdp = hist_gdp_yoy.iloc[-1]
        last_inf = hist_tail['inflation_total'].iloc[-1]
        last_u = hist_tail['unemployment_rate'].iloc[-1]

    # 1. Crecimiento PIB
    ax1 = axes[0]
    if has_hist:
        ax1.plot(hist_tail.index, hist_gdp_yoy, color='#555555', lw=1.8, label='Histórico', linestyle='--')
        ax1.axvline(last_d, color='gray', linestyle=':', lw=1.0, alpha=0.7)

    for sc_name, df in comparison_dfs.items():
        c = colors.get(sc_name, '#333333')
        l = labels.get(sc_name, sc_name)
        if has_hist:
            plot_x = [last_d] + list(df.index)
            plot_y = [last_gdp] + list(df['gdp_growth_annual'].values)
        else:
            plot_x = df.index
            plot_y = df['gdp_growth_annual'].values
        ax1.plot(plot_x, plot_y, label=l, color=c, lw=2.2)
    ax1.set_title("Crecimiento PIB Real (% i.a.)", fontweight='bold')
    ax1.set_ylabel("%")
    ax1.legend(loc='best', fontsize=9)

    # 2. Inflación General
    ax2 = axes[1]
    if has_hist:
        ax2.plot(hist_tail.index, hist_tail['inflation_total'], color='#555555', lw=1.8, label='Histórico', linestyle='--')
        ax2.axvline(last_d, color='gray', linestyle=':', lw=1.0, alpha=0.7)

    for sc_name, df in comparison_dfs.items():
        c = colors.get(sc_name, '#333333')
        l = labels.get(sc_name, sc_name)
        if has_hist:
            plot_x = [last_d] + list(df.index)
            plot_y = [last_inf] + list(df['inflation_total'].values)
        else:
            plot_x = df.index
            plot_y = df['inflation_total'].values
        ax2.plot(plot_x, plot_y, label=l, color=c, lw=2.2)
    ax2.axhline(2.0, color='gray', linestyle=':', lw=1.0)
    ax2.set_title("Inflación General (% i.a.)", fontweight='bold')
    ax2.set_ylabel("%")
    ax2.legend(loc='best', fontsize=9)

    # 3. Tasa de Paro
    ax3 = axes[2]
    if has_hist:
        ax3.plot(hist_tail.index, hist_tail['unemployment_rate'], color='#555555', lw=1.8, label='Histórico', linestyle='--')
        ax3.axvline(last_d, color='gray', linestyle=':', lw=1.0, alpha=0.7)

    for sc_name, df in comparison_dfs.items():
        c = colors.get(sc_name, '#333333')
        l = labels.get(sc_name, sc_name)
        if has_hist:
            plot_x = [last_d] + list(df.index)
            plot_y = [last_u] + list(df['unemployment_rate'].values)
        else:
            plot_x = df.index
            plot_y = df['unemployment_rate'].values
        ax3.plot(plot_x, plot_y, label=l, color=c, lw=2.2)
    ax3.set_title("Tasa de Paro (%)", fontweight='bold')
    ax3.set_ylabel("%")
    ax3.legend(loc='best', fontsize=9)

    for ax in axes:
        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        ax.tick_params(axis='x', rotation=30)

    plt.tight_layout()
    fig.savefig(save_path, bbox_inches='tight')
    plt.close(fig)
    return save_path


def compute_annual_gdp_growth(df_history: Optional[pd.DataFrame], df_forecast: pd.DataFrame) -> pd.Series:
    """
    Calcula la tasa de crecimiento anual del PIB según la metodología de Contabilidad Nacional (INE):
    tasa de variación entre los valores medios de dos años consecutivos de la serie del PIB real en nivel.
    Si no se dispone de la serie en nivel proyectada, se encadena a partir de las tasas intertrimestrales
    empezando desde el último nivel histórico.
    """
    if df_history is not None and 'gdp_real_spain' in df_history.columns:
        s_hist = df_history['gdp_real_spain'].dropna()
    else:
        s_hist = pd.Series(dtype=float)

    base_level = float(s_hist.iloc[-1]) if len(s_hist) > 0 else 100.0

    if 'gdp_real_spain' in df_forecast.columns and not df_forecast['gdp_real_spain'].isna().all():
        s_fore = df_forecast['gdp_real_spain']
    else:
        levels = []
        curr = base_level
        for qoq in df_forecast['gdp_growth_quarterly']:
            curr = curr * (1.0 + qoq / 100.0)
            levels.append(curr)
        s_fore = pd.Series(levels, index=df_forecast.index)

    if len(s_hist) > 0:
        gdp_full = pd.concat([s_hist, s_fore])
    else:
        gdp_full = s_fore

    # Media anual del PIB en nivel para cada año
    annual_means = gdp_full.groupby(gdp_full.index.year).mean()
    annual_growth = (annual_means.pct_change() * 100.0).dropna()
    return annual_growth


def generate_markdown_report(df_forecast: pd.DataFrame,
                             dashboard_img_path: Path,
                             comparison_img_path: Optional[Path] = None,
                             scenario_name: str = "baseline",
                             output_file: Optional[Path] = None,
                             monthly_section_md: Optional[str] = None,
                             df_history: Optional[pd.DataFrame] = None) -> Path:
    """
    Genera el informe ejecutivo en Markdown con tablas, gráficos y diagnóstico analítico.
    """
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = output_file or (REPORTS_DIR / f"informe_prevision_{scenario_name}.md")

    # Tabla de resultados trimestrales formateada (como strings para preservar ceros decimales)
    quarter_labels = [f"{d.year}-Q{d.quarter}" for d in df_forecast.index]
    table_df = pd.DataFrame(index=quarter_labels)
    table_df['PIB (% i.a.)'] = df_forecast['gdp_growth_annual'].apply(lambda x: f"{x:.1f}")
    table_df['PIB (% t/t-1)'] = df_forecast['gdp_growth_quarterly'].apply(lambda x: f"{x:.1f}")
    table_df['Brecha PIB (%)'] = df_forecast['output_gap_spain'].apply(lambda x: f"{x:.1f}")
    table_df['Tasa Paro (%)'] = df_forecast['unemployment_rate'].apply(lambda x: f"{x:.2f}")
    table_df['Inflación Gen (%)'] = df_forecast['inflation_total'].apply(lambda x: f"{x:.1f}")
    table_df['Inflación Sub (%)'] = df_forecast['inflation_core'].apply(lambda x: f"{x:.1f}")
    if 'oil_price_brent' in df_forecast.columns:
        table_df['Petróleo ($)'] = df_forecast['oil_price_brent'].apply(lambda x: f"{x:.1f}")
    if 'interest_rate_ecb' in df_forecast.columns:
        table_df['Tipo BCE (%)'] = df_forecast['interest_rate_ecb'].apply(lambda x: f"{x:.2f}")

    # Calcular tasas anuales: PIB según Contabilidad Nacional (medias anuales en nivel)
    # y regla de 1 decimal para crecimiento/inflación, 2 para paro
    ann_gdp_growth = compute_annual_gdp_growth(df_history, df_forecast)
    grouped = df_forecast.groupby(df_forecast.index.year)
    annual_summary = pd.DataFrame(index=sorted(df_forecast.index.year.unique()))
    
    gdp_col = []
    for y in annual_summary.index:
        if y in ann_gdp_growth.index:
            gdp_col.append(f"{ann_gdp_growth.loc[y]:.1f}%")
        else:
            gdp_col.append(f"{grouped['gdp_growth_annual'].mean().loc[y]:.1f}%")
    annual_summary['PIB Real (% anual Cont. Nac.)'] = gdp_col
    annual_summary['Tasa de Paro (% media)'] = grouped['unemployment_rate'].mean().apply(lambda x: f"{x:.2f}%")
    annual_summary['Inflación General (% media)'] = grouped['inflation_total'].mean().apply(lambda x: f"{x:.1f}%")
    annual_summary['Inflación Subyacente (% media)'] = grouped['inflation_core'].mean().apply(lambda x: f"{x:.1f}%")

    dash_rel = f"figures/{dashboard_img_path.name}"
    comp_rel = f"figures/{comparison_img_path.name}" if comparison_img_path else None

    # -------------------------------------------------------------
    # Diagnóstico cualitativo generado a partir de los resultados
    # (sin texto incrustado: el resumen se deriva de las cifras)
    # -------------------------------------------------------------
    avg_growth = df_forecast['gdp_growth_annual'].mean()
    peak_infl = df_forecast['inflation_total'].max()
    peak_infl_q = df_forecast['inflation_total'].idxmax()
    peak_infl_label = f"{peak_infl_q.year}-Q{peak_infl_q.quarter}"
    end_infl = df_forecast['inflation_total'].iloc[-1]
    core_peak = df_forecast['inflation_core'].max()
    final_u = df_forecast['unemployment_rate'].iloc[-1]
    start_u = df_forecast['unemployment_rate'].iloc[0]
    end_growth = df_forecast['gdp_growth_annual'].iloc[-1]
    min_q_growth = df_forecast['gdp_growth_quarterly'].min()
    first_year = int(df_forecast.index[0].year)
    last_year = int(df_forecast.index[-1].year)
    first_year_growth = ann_gdp_growth.loc[first_year] if first_year in ann_gdp_growth.index else df_forecast[df_forecast.index.year == first_year]['gdp_growth_annual'].mean()

    # Cualificadores condicionales según el signo/tamaño de los resultados
    contraccion = "con algún trimestre de contracción intertrimestral" if min_q_growth < 0 else "sin trimestres de contracción intertrimestral"
    dir_paro = "al alza" if final_u > start_u + 0.1 else ("a la baja" if final_u < start_u - 0.1 else "estable")
    dir_infl = "por encima" if peak_infl > 2.0 else "en el entorno"

    bullet_growth = (
        f"**Crecimiento**: en el escenario proyectado, el PIB real avanzaría a una media del "
        f"**{avg_growth:.1f}%** interanual en el horizonte, con un perfil {contraccion}. "
        f"El primer año se situaría en torno al **{first_year_growth:.1f}%** (tasa anual de Contabilidad Nacional "
        f"sobre medias del PIB en nivel proyectado) y el ritmo al cierre del horizonte "
        f"rondaría el **{end_growth:.1f}%**, en convergencia hacia el crecimiento potencial supuesto."
    )
    bullet_infl = (
        f"**Inflación**: la inflación general alcanzaría su máximo en **{peak_infl_label}** ({peak_infl:.1f}%), "
        f"{dir_infl} del objetivo del 2%, para cerrar el horizonte cerca del **{end_infl:.1f}%**. "
        f"La subyacente marcaría un máximo próximo al **{core_peak:.1f}%**. Conviene recordar que el "
        f"perfil de inflación depende de forma directa de la senda de energía supuesta en el escenario."
    )
    bullet_labor = (
        f"**Mercado laboral**: la tasa de paro pasaría del **{start_u:.2f}%** inicial al **{final_u:.2f}%** "
        f"al final del horizonte (tendencia {dir_paro}), en coherencia con la brecha de producto simulada y "
        f"la NAIRU supuesta."
    )

    h_start = f"{df_forecast.index[0].year}-Q{df_forecast.index[0].quarter}"
    h_end = f"{df_forecast.index[-1].year}-Q{df_forecast.index[-1].quarter}"

    md_content = f"""# Informe Ejecutivo de Previsiones Macroeconómicas para España
**Modelo MEcPol v2.0 (EsadeEcPol)**  
**Escenario Evaluado:** `{scenario_name.upper()}`  
**Horizonte:** {h_start} a {h_end} ({len(df_forecast)} trimestres)

---

## 1. Resumen Ejecutivo y Diagnóstico

1. {bullet_growth}
2. {bullet_infl}
3. {bullet_labor}

---

## 2. Proyecciones Resumidas por Año

*Nota: La tasa del PIB real refleja el crecimiento anual oficial (variación entre medias anuales consecutivas de la serie del PIB en nivel, metodología INE).*

| Año | PIB Real (% anual Cont. Nac.) | Tasa de Paro (% media) | Inflación General (% media) | Inflación Subyacente (% media) |
| :---: | :---: | :---: | :---: | :---: |
"""
    for year, row in annual_summary.iterrows():
        md_content += f"| **{year}** | {row['PIB Real (% anual Cont. Nac.)']} | {row['Tasa de Paro (% media)']} | {row['Inflación General (% media)']} | {row['Inflación Subyacente (% media)']} |\n"

    md_content += f"""
---

## 3. Panel Gráfico de Previsiones (Fan Charts)

El siguiente panel presenta las sendas proyectadas junto a las bandas de probabilidad al 50% y 80%:

![Panel de Previsiones]({dash_rel})

---

## 4. Detalle Trimestre a Trimestre

{table_df.to_markdown()}

"""

    if comp_rel:
        md_content += f"""
---

## 5. Comparativa entre Escenarios Alternativos

![Comparativa de Escenarios]({comp_rel})

* **Escenario Base (consenso)**: Incorpora el shock energético en curso y su resolución gradual. Brent anclado a la senda de consenso (EIA STEO, sep-2026): ~91 USD de media en 2026 y descenso hacia 64-67 USD a lo largo de 2027-2028. BCE en torno al 2.0%-2.25%.
* **Escenario Adverso**: Escalada geopolítica (cierre del estrecho de Ormuz) con Brent hacia 120-128 USD, gas al alza, BCE subiendo al 3.25% y recesión en la Eurozona. Estanflación seguida de recesión desinflacionaria.
* **Escenario Favorable**: Resolución rápida de la oferta (restauración de rutas de suministro), Brent de vuelta a 60-65 USD, desinflación y recortes del BCE hacia el 1.75%.
"""

    if monthly_section_md:
        md_content += monthly_section_md

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(md_content)

    return report_path
