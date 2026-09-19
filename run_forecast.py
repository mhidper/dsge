"""
Script principal para ejecutar simulaciones, calibración y generar informes ejecutivos en Markdown.

Uso:
    python sandbox/run_forecast.py --scenario baseline --horizon 12
    python sandbox/run_forecast.py --scenario all
    python sandbox/run_forecast.py --scenario adverse_energy_rates --estimate
"""

import argparse
import sys
from pathlib import Path

# Asegurar codificación UTF-8 en consola Windows
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Añadir la raíz del proyecto al sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.datos.ensamblado import construir_dataset
from src.forecasting import generate_forecast, generate_monte_carlo_bands
from src.estimation import estimate_bayesian_mcmc
from src.reporting import plot_forecast_dashboard, plot_scenario_comparison, generate_markdown_report
from src.config import DEFAULT_PARAMS, REPORTS_DIR


def main():
    parser = argparse.ArgumentParser(description="Motor de Previsión Macroeconómica Semi-DSGE para España")
    parser.add_argument("--scenario", type=str, default="baseline",
                        choices=["baseline", "adverse_energy_rates", "favorable_disinflation", "all"],
                        help="Escenario a simular (o 'all' para simular y comparar todos)")
    parser.add_argument("--horizon", type=int, default=12,
                        help="Horizonte de previsión en trimestres (default: 12)")
    parser.add_argument("--estimate", action="store_true",
                        help="Ejecutar calibración bayesiana MCMC sobre datos históricos antes de proyectar")
    parser.add_argument("--samples", type=int, default=1500,
                        help="Número de muestras MCMC si se ejecuta estimación (default: 1500)")
    args = parser.parse_args()

    print("\n" + "=" * 65)
    print("[*] MODELO MECPOL (ESADEECPOL) - MOTOR DE PREVISIONES")
    print("=" * 65)

    # 1. Cargar y preparar datos históricos consolidados
    print("\n[*] [Paso 1/4] Cargando y consolidando datos historicos oficiales...")
    df_hist = construir_dataset()   # Fase 3: almacén único, todo real
    start_q = f"{df_hist.index[0].year}-Q{df_hist.index[0].quarter}"
    end_q = f"{df_hist.index[-1].year}-Q{df_hist.index[-1].quarter}"
    print(f"   * Muestra historica: {len(df_hist)} trimestres ({start_q} a {end_q})")
    print(f"   * Ultimo dato Brecha PIB: {df_hist['output_gap_spain'].iloc[-1]:.1f}%")
    print(f"   * Ultima Tasa de Paro:    {df_hist['unemployment_rate'].iloc[-1]:.2f}%")
    print(f"   * Ultima Inflacion Gen:   {df_hist['inflation_total'].iloc[-1]:.1f}%")

    # 2. Estimación bayesiana opcional
    model_params = DEFAULT_PARAMS.copy()
    if args.estimate:
        print("\n[*] [Paso 2/4] Ejecutando estimacion Bayesiana Metropolis-Hastings...")
        data_dict = {c: df_hist[c].values for c in df_hist.columns}
        mcmc_res = estimate_bayesian_mcmc(data_dict, n_samples=args.samples, n_burn=500)
        model_params.update(mcmc_res['posterior_means'])
        print(f"   * Estimacion completada (Tasa de aceptacion: {mcmc_res['acceptance_rate']:.1%})")
        for p_name, val in mcmc_res['posterior_means'].items():
            print(f"     - {p_name:<24}: {val:.4f}")
    else:
        print("\n[*] [Paso 2/4] Utilizando parametros estructurales calibrados de referencia.")

    # 3. Simulación de escenarios
    print(f"\n[*] [Paso 3/4] Generando proyecciones a {args.horizon} trimestres...")
    scenarios_to_run = ["baseline", "adverse_energy_rates", "favorable_disinflation"] if args.scenario == "all" else [args.scenario]

    scenario_dfs = {}
    for sc in ["baseline", "adverse_energy_rates", "favorable_disinflation"]:
        scenario_dfs[sc] = generate_forecast(df_hist, horizon_quarters=args.horizon,
                                             scenario_type=sc, params=model_params)

    # Gráfico de comparativa de escenarios
    comp_img_path = plot_scenario_comparison(scenario_dfs, df_history=df_hist)
    print(f"   * Grafico comparativo generado en: {comp_img_path.name}")

    # 4. Generar bandas de incertidumbre e informe para el escenario seleccionado
    print("\n[*] [Paso 4/4] Generando informes ejecutivos en Markdown y graficos...")
    reports_generated = []

    target_scenario = "baseline" if args.scenario == "all" else args.scenario
    bands = generate_monte_carlo_bands(df_hist, horizon_quarters=args.horizon,
                                       scenario_type=target_scenario, params=model_params)
    dash_img_path = plot_forecast_dashboard(df_hist, bands, scenario_name=target_scenario)

    # 4b. Módulo Satélite Opcional: Desagregación Mensual del IPC (Bridge Model)
    monthly_sec_md = None
    try:
        from src.monthly_cpi import (is_monthly_cpi_available,
                                     run_monthly_cpi_disaggregation,
                                     plot_monthly_cpi_dashboard,
                                     plot_monthly_cpi_scenarios_comparison,
                                     get_monthly_cpi_report_section)
        if is_monthly_cpi_available():
            print("\n[*] [Subproducto] Activando modulo satelite de IPC mensual...")
            # Calcular desagregación mensual para todos los escenarios simulados
            monthly_scenarios_dfs = {}
            for sc_name, sc_df in scenario_dfs.items():
                monthly_scenarios_dfs[sc_name] = run_monthly_cpi_disaggregation(
                    df_hist, sc_df, params=model_params
                )

            df_monthly_cpi = monthly_scenarios_dfs[target_scenario]
            m_img_path = plot_monthly_cpi_dashboard(df_monthly_cpi, scenario_name=target_scenario)
            print(f"   * Grafico mensual de IPC generado en: {m_img_path.name}")

            # Generar gráfico comparativo mensual entre todos los escenarios
            m_comp_img_path = plot_monthly_cpi_scenarios_comparison(monthly_scenarios_dfs)
            print(f"   * Grafico comparativo mensual de IPC generado en: {m_comp_img_path.name}")

            monthly_sec_md = get_monthly_cpi_report_section(
                df_monthly=df_monthly_cpi,
                img_path=m_img_path,
                comp_img_path=m_comp_img_path
            )
    except Exception as e:
        print(f"   * Modulo satelite mensual omitido: {e}")

    report_file = generate_markdown_report(
        df_forecast=scenario_dfs[target_scenario],
        dashboard_img_path=dash_img_path,
        comparison_img_path=comp_img_path,
        scenario_name=target_scenario,
        monthly_section_md=monthly_sec_md,
        df_history=df_hist
    )
    reports_generated.append(report_file)

    # 4c. Generación automática del Informe Ejecutivo en PDF
    pdf_file = None
    try:
        from src.pdf_generator import build_pdf_report
        pdf_file = build_pdf_report(
            df_history=df_hist,
            df_forecast=scenario_dfs[target_scenario],
            scenario_name=target_scenario
        )
    except Exception as e:
        print(f"   * Aviso al generar informe PDF: {e}")

    print("\n" + "=" * 65)
    print("[OK] SIMULACION Y PREVISION COMPLETADAS CON EXITO")
    print("=" * 65)
    print(f"Informe ejecutivo Markdown generado en:")
    print(f"   -> {report_file.resolve()}")
    if pdf_file:
        print(f"Informe ejecutivo PDF generado en:")
        print(f"   -> {pdf_file.resolve()}")
    print("\nResumen de Previsiones Clave (Escenario Central MEcPol):")
    df_central = scenario_dfs[target_scenario]
    from src.reporting import compute_annual_gdp_growth
    ann_gdp_central = compute_annual_gdp_growth(df_hist, df_central)
    proj_years = df_central.index.year.unique()
    ann_proj = ann_gdp_central.loc[ann_gdp_central.index.isin(proj_years)]
    gdp_first_y = ann_gdp_central.get(proj_years[0], 2.2)
    print(f"   * Crecimiento PIB anual primer año proyectado ({proj_years[0]}): {gdp_first_y:.1f}%")
    print(f"   * Crecimiento medio PIB real anual (Cont. Nac.): {ann_proj.mean():.1f}%")
    print(f"   * Inflacion media general:    {df_central['inflation_total'].mean():.1f}%")
    print(f"   * Tasa de paro al final del periodo: {df_central['unemployment_rate'].iloc[-1]:.2f}%")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    main()
