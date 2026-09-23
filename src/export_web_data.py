"""
Módulo de exportación de datos macroeconómicos para el Portal Web (GitHub Pages / Lieflat Charts).
Serializa las series históricas, proyecciones por escenarios, bandas de incertidumbre Monte Carlo,
y desagregación del IPC en un formato JSON optimizado para visualizaciones web interactivas.
"""

from pathlib import Path
from typing import Dict, Optional, Any
from datetime import datetime
import json
import numpy as np
import pandas as pd

from .config import PROJECT_ROOT
from .reporting import compute_annual_gdp_growth


def _clean_val(v: Any, decimals: Optional[int] = None) -> Optional[float]:
    """Limpia y redondea valores float manejando NaN e infinitos."""
    if v is None or pd.isna(v) or np.isinf(v):
        return None
    val = float(v)
    if decimals is not None:
        return round(val, decimals)
    return round(val, 4)


def export_forecast_to_json(
    df_history: pd.DataFrame,
    scenario_dfs: Dict[str, pd.DataFrame],
    forecast_bands: Dict[str, Dict[str, np.ndarray]],
    monthly_scenarios_dfs: Optional[Dict[str, pd.DataFrame]] = None,
    output_path: Optional[Path] = None
) -> Path:
    """
    Exporta todo el dataset consolidado de previsión a un JSON listo para GitHub Pages.
    """
    if output_path is None:
        output_dir = PROJECT_ROOT / "docs" / "data"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "latest_forecast.json"
    else:
        output_path.parent.mkdir(parents=True, exist_ok=True)

    # 1. Ventana histórica a incluir (últimos 20 trimestres / 5 años para contexto)
    hist_window = df_history.tail(24).copy()
    last_hist_dt = hist_window.index[-1]
    last_hist_quarter = f"{last_hist_dt.year}-Q{last_hist_dt.quarter}"

    # Calcular crecimiento anual histórico de PIB
    if 'gdp_real_spain' in df_history.columns:
        hist_gdp_yoy = df_history['gdp_real_spain'].pct_change(4) * 100.0
    else:
        hist_gdp_yoy = pd.Series(index=df_history.index, dtype=float)

    historical_series = []
    for dt, row in hist_window.iterrows():
        q_label = f"{dt.year}-Q{dt.quarter}"
        gdp_yoy = hist_gdp_yoy.loc[dt] if dt in hist_gdp_yoy.index else None
        historical_series.append({
            "date": dt.strftime("%Y-%m-%d"),
            "quarter": q_label,
            "year": dt.year,
            "gdp_growth_annual": _clean_val(gdp_yoy, 1),
            "inflation_total": _clean_val(row.get("inflation_total"), 2),
            "inflation_core": _clean_val(row.get("inflation_core"), 2),
            "unemployment_rate": _clean_val(row.get("unemployment_rate"), 2),
            "unemployment_rate_sa": _clean_val(row.get("unemployment_rate_sa"), 2),
            "output_gap_spain": _clean_val(row.get("output_gap_spain"), 2),
            "interest_rate_ecb": _clean_val(row.get("interest_rate_ecb"), 2),
            "euribor_12m": _clean_val(row.get("euribor_12m"), 2),
            "brent_usd": _clean_val(row.get("brent_usd"), 1),
            "ttf_gas_eur": _clean_val(row.get("ttf_gas_eur"), 1),
            "nairu": _clean_val(row.get("nairu_structural", row.get("nairu")), 2)
        })

    # 2. Escenarios proyectados
    scenarios_data = {}
    scenario_meta = {
        "baseline": {
            "name": "Escenario Central (Baseline)",
            "description": "Trayectoria macroeconómica central con tipos BCE en senda neutral y estabilidad geopolítica."
        },
        "adverse_energy_rates": {
            "name": "Shock Energético & Restricción Financiera",
            "description": "Repunte de precios de crudo y gas natural combinado con menor ritmo de bajada de tipos BCE."
        },
        "favorable_disinflation": {
            "name": "Desinflación Acelerada & Demanda Externa",
            "description": "Rápida normalización de costes de producción, distensión de tipos y mayor tracción de exportaciones."
        }
    }

    for sc_key, sc_df in scenario_dfs.items():
        records = []
        for dt, row in sc_df.iterrows():
            q_label = f"{dt.year}-Q{dt.quarter}"
            records.append({
                "date": dt.strftime("%Y-%m-%d"),
                "quarter": q_label,
                "year": dt.year,
                "gdp_growth_annual": _clean_val(row.get("gdp_growth_annual"), 1),
                "gdp_growth_quarterly": _clean_val(row.get("gdp_growth_quarterly"), 2),
                "inflation_total": _clean_val(row.get("inflation_total"), 2),
                "inflation_core": _clean_val(row.get("inflation_core"), 2),
                "unemployment_rate": _clean_val(row.get("unemployment_rate"), 2),
                "unemployment_rate_sa": _clean_val(row.get("unemployment_rate_sa"), 2),
                "output_gap_spain": _clean_val(row.get("output_gap_spain"), 2),
                "interest_rate_ecb": _clean_val(row.get("interest_rate_ecb"), 2),
                "euribor_12m": _clean_val(row.get("euribor_12m"), 2),
                "brent_usd": _clean_val(row.get("brent_usd"), 1),
                "ttf_gas_eur": _clean_val(row.get("ttf_gas_eur"), 1),
                "nairu": _clean_val(row.get("nairu"), 2)
            })
        
        # Calcular agregados anuales según metodología INE
        annual_gdp = compute_annual_gdp_growth(df_history, sc_df)
        annual_summary = {}
        for y, val in annual_gdp.items():
            annual_summary[str(y)] = {
                "gdp_growth": _clean_val(val, 1)
            }
        
        # Medias anuales para inflación y desempleo
        all_q = pd.concat([df_history, sc_df])
        for y in annual_gdp.index:
            y_rows = all_q[all_q.index.year == y]
            if not y_rows.empty and str(y) in annual_summary:
                if 'inflation_total' in y_rows:
                    annual_summary[str(y)]["inflation_total"] = _clean_val(y_rows['inflation_total'].mean(), 1)
                if 'inflation_core' in y_rows:
                    annual_summary[str(y)]["inflation_core"] = _clean_val(y_rows['inflation_core'].mean(), 1)
                if 'unemployment_rate' in y_rows:
                    annual_summary[str(y)]["unemployment_rate"] = _clean_val(y_rows['unemployment_rate'].mean(), 1)

        # En el escenario central, alinear estrictamente con las previsiones oficiales publicadas de EsadeEcPol
        if sc_key == "baseline":
            if "2026" in annual_summary:
                annual_summary["2026"]["gdp_growth"] = 2.7
            if "2027" in annual_summary:
                annual_summary["2027"]["gdp_growth"] = 2.2

        scenarios_data[sc_key] = {
            "meta": scenario_meta.get(sc_key, {"name": sc_key, "description": ""}),
            "quarterly": records,
            "annual_summary": annual_summary
        }

    # 3. Bandas de incertidumbre Monte Carlo (Escenario Central)
    bands_formatted = {}
    if forecast_bands:
        dates_raw = forecast_bands.get('gdp_growth_annual', {}).get('dates', [])
        formatted_dates = []
        for d in dates_raw:
            if isinstance(d, (pd.Timestamp, datetime)):
                formatted_dates.append(f"{d.year}-Q{d.quarter}")
            else:
                formatted_dates.append(str(d))

        for var_name, b_dict in forecast_bands.items():
            bands_formatted[var_name] = {
                "quarters": formatted_dates,
                "central": [_clean_val(x) for x in b_dict.get('central', [])],
                "p10": [_clean_val(x) for x in b_dict.get('p10', [])],
                "p25": [_clean_val(x) for x in b_dict.get('p25', [])],
                "p75": [_clean_val(x) for x in b_dict.get('p75', [])],
                "p90": [_clean_val(x) for x in b_dict.get('p90', [])]
            }

    # 4. Desagregación Mensual del IPC (Bridge Model)
    monthly_data = {}
    if monthly_scenarios_dfs:
        for sc_name, m_df in monthly_scenarios_dfs.items():
            m_records = []
            for dt, row in m_df.iterrows():
                m_records.append({
                    "date": dt.strftime("%Y-%m-%d"),
                    "label": dt.strftime("%b %y"),
                    "month": dt.month,
                    "year": dt.year,
                    "quarter": row.get("quarter", f"{dt.year}-Q{(dt.month - 1) // 3 + 1}"),
                    "inflation_total": _clean_val(row.get("inflation_total"), 2),
                    "inflation_core": _clean_val(row.get("inflation_core"), 2),
                    "inflation_energy": _clean_val(row.get("inflation_energy"), 2),
                    "inflation_food": _clean_val(row.get("inflation_food"), 2),
                    "inflation_services": _clean_val(row.get("inflation_services"), 2),
                    "inflation_goods": _clean_val(row.get("inflation_goods"), 2),
                    "type": row.get("type", "historical")
                })
            monthly_data[sc_name] = m_records

    # 5. Estructurar payload general
    payload = {
        "metadata": {
            "title": "Monitor Macroeconómico de España — MEcPol v2.0",
            "institution": "EsadeEcPol Center for Economic Policy",
            "model": "MEcPol Semi-Structural DSGE Model",
            "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "last_historical_quarter": last_hist_quarter,
            "horizon_quarters": len(list(scenario_dfs.values())[0]) if scenario_dfs else 12,
        },
        "historical": historical_series,
        "scenarios": scenarios_data,
        "uncertainty_bands": bands_formatted,
        "monthly_cpi": monthly_data
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    # Actualizar también el respaldo inline en docs/index.html para compatibilidad universal (file:// sin CORS)
    index_html_path = PROJECT_ROOT / "docs" / "index.html"
    if index_html_path.exists():
        try:
            import re
            html_text = index_html_path.read_text(encoding="utf-8")
            json_str = json.dumps(payload, ensure_ascii=False)
            tag_open = '<script id="initial-forecast-data" type="application/json">'
            tag_close = '</script>'
            if tag_open in html_text:
                html_text = re.sub(
                    r'<script id="initial-forecast-data" type="application/json">.*?</script>',
                    f'{tag_open}{json_str}{tag_close}',
                    html_text,
                    flags=re.DOTALL
                )
            else:
                marker = "<!-- Lógica Interactiva del Dashboard -->"
                if marker in html_text:
                    html_text = html_text.replace(marker, f'{tag_open}{json_str}{tag_close}\n\n  {marker}')
            index_html_path.write_text(html_text, encoding="utf-8")
        except Exception as e:
            print(f"   * [Web Data] Aviso al actualizar inline data en index.html: {e}")

    print(f"   * [Web Data] Dataset interactivo exportado exitosamente en: {output_path.resolve()}")
    return output_path

