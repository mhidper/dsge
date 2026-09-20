"""PRUEBA AISLADA: NAIRU estructural (Kalman+Phillips) vs NAIRU HP actual.
No toca el motor. Imprime métricas de mejora y guarda un gráfico comparativo."""
import sys; sys.path.insert(0, ".")
import warnings; warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.datos.ensamblado import construir_dataset
from src.nairu_estructural import estimar_nairu_estructural, _desestacionalizar
from src.data_pipeline import hp_filter

df = construir_dataset()
u = df["unemployment_rate"].dropna()
pis = df["inflation_services"].reindex(u.index)
u_sa = _desestacionalizar(u)

# --- Estructural ---
est = estimar_nairu_estructural(u, pis)
nairu_est = est["nairu"]
print("=== NAIRU ESTRUCTURAL (Kalman + Phillips) ===")
print("  convergencia:", est["convergencia"], "| log-verosimilitud:", round(est["llf"], 1))
print("  parámetros:", {k: round(v, 3) for k, v in est["params"].items()})
print(f"  NAIRU: primer {nairu_est.iloc[0]:.2f}  último {nairu_est.iloc[-1]:.2f}")

# --- HP (mismo insumo desestacionalizado, λ=6400 como el motor) ---
hp_tr, _ = hp_filter(u_sa, lamb=6400)
nairu_hp = hp_tr.reindex(u_sa.index)
print(f"\n=== NAIRU HP (λ=6400, actual) ===")
print(f"  NAIRU: primer {nairu_hp.iloc[0]:.2f}  último {nairu_hp.iloc[-1]:.2f}")

def phillips_fit(nairu, nombre):
    """Regresión Δπ^serv_t = a + b·gap_{t-1} + e. Buen NAIRU: b<0 y R² alto."""
    gap = (u_sa - nairu)
    dpi = pis.diff()
    X = gap.shift(1)
    d = pd.concat([dpi, X], axis=1).dropna()
    d.columns = ["dpi", "gap_lag"]
    x = d["gap_lag"].values; y = d["dpi"].values
    b, a = np.polyfit(x, y, 1)
    yhat = a + b * x
    ss_res = np.sum((y - yhat) ** 2); ss_tot = np.sum((y - y.mean()) ** 2)
    r2 = 1 - ss_res / ss_tot
    n = len(x); se = np.sqrt(ss_res / (n - 2) / np.sum((x - x.mean()) ** 2))
    tstat = b / se
    print(f"  [{nombre}] Δπ_serv ~ gap(-1):  b={b:+.3f}  t={tstat:+.2f}  R²={r2:.3f}  (b<0 y |t|>2 = consistente con inflación)")
    return r2, b, tstat

print("\n=== MÉTRICA 1: consistencia con la inflación (curva de Phillips) ===")
r2_e, b_e, t_e = phillips_fit(nairu_est, "estructural")
r2_h, b_h, t_h = phillips_fit(nairu_hp, "HP        ")

# --- MÉTRICA 2: estabilidad de fin de muestra (revisión) ---
print("\n=== MÉTRICA 2: revisión de fin de muestra (menor = mejor) ===")
def revision_hp(k=8):
    revs = []
    for cut in range(len(u_sa) - k, len(u_sa)):
        tr, _ = hp_filter(u_sa.iloc[:cut + 1], lamb=6400)
        rt = tr.iloc[-1]            # estimación en tiempo real del punto 'cut'
        final = nairu_hp.iloc[cut]  # estimación con toda la muestra
        revs.append(abs(rt - final))
    return np.mean(revs)

def revision_estructural(k=8):
    revs = []
    for cut in range(len(u_sa) - k, len(u_sa)):
        sub = estimar_nairu_estructural(u.iloc[:cut + 1], pis.iloc[:cut + 1])
        rt = sub["nairu"].iloc[-1]
        final = nairu_est.iloc[cut]
        revs.append(abs(rt - final))
    return np.mean(revs)

rev_h = revision_hp(); rev_e = revision_estructural()
print(f"  revisión media |tiempo real - final| (últimos 8T):  HP={rev_h:.3f} pp   estructural={rev_e:.3f} pp")

# --- MÉTRICA 3: plausibilidad ---
print("\n=== MÉTRICA 3: plausibilidad (consenso u*_SS ≈ 8,8-9,0%) ===")
print(f"  HP último: {nairu_hp.iloc[-1]:.2f}%   estructural último: {nairu_est.iloc[-1]:.2f}%")
print(f"  suavidad (desv. de la 1ª dif.):  HP={nairu_hp.diff().std():.3f}  estructural={nairu_est.diff().std():.3f}")

# --- Gráfico ---
fig, ax = plt.subplots(figsize=(11, 5.5))
ax.plot(u_sa.index, u_sa.values, color="#9aa0a6", lw=1, label="Paro desestacionalizado")
ax.plot(nairu_hp.index, nairu_hp.values, color="#1a73e8", lw=2, label="NAIRU HP (actual)")
ax.plot(nairu_est.index, nairu_est.values, color="#d93025", lw=2, label="NAIRU estructural (Kalman+Phillips)")
ax.set_title("NAIRU: HP actual vs estructural (prueba, no sustituye)", fontweight="bold")
ax.set_ylabel("% población activa"); ax.legend(); ax.grid(alpha=0.3)
fig.tight_layout()
out = "reports/figures/prueba_nairu_estructural.png"
fig.savefig(out, dpi=130)
print(f"\nGráfico guardado en: {out}")

# --- Veredicto sintético ---
print("\n=== VEREDICTO ===")
mejora_infl = (abs(t_e) > abs(t_h)) and (b_e < 0)
mejora_estab = rev_e < rev_h
print(f"  ¿mejor consistencia con inflación?  {'SÍ' if mejora_infl else 'NO'}  (|t| {abs(t_e):.2f} vs {abs(t_h):.2f})")
print(f"  ¿menor revisión de fin de muestra?  {'SÍ' if mejora_estab else 'NO'}  ({rev_e:.3f} vs {rev_h:.3f} pp)")
