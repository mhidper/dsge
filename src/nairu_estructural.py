"""
NAIRU ESTRUCTURAL — PRUEBA AISLADA (no forma parte del motor).

Estima la NAIRU (u*) como un estado no observable dentro de un modelo en
espacio de estados, identificándola CONJUNTAMENTE con la inflación (curva de
Phillips) — a diferencia del filtro HP actual, puramente estadístico. Es un
filtro de componentes no observados estilo Kuttner (1994) / Apel-Jansson
(1999) / filtro multivariante del FMI (Blagrave et al., 2015).

Sistema (frecuencia trimestral), sobre el paro DESESTACIONALIZADO u^sa:

  Estado  α_t = [u*_t, c_t, c_{t-1}]     (u* = NAIRU; c = paro cíclico)
    u*_t = u*_{t-1} + η_t                 (paseo aleatorio suave; σ_η acotada)
    c_t  = φ1 c_{t-1} + φ2 c_{t-2} + ε_t  (ciclo AR(2))
  Medidas y_t = [u^sa_t, Δπ^serv_t]
    u^sa_t   = u*_t + c_t                 (identidad; ruido ínfimo)
    Δπ^serv_t = -β c_{t-1} + ε^π_t        (Phillips acelerador: la brecha de
                                           paro presiona la inflación de servicios)

Parámetros θ = [φ1, φ2, β, σ_η, σ_c, σ_π] por máxima verosimilitud (Kalman);
σ_η acotada para que la NAIRU sea suave pero responda a la señal de inflación
(equivalente estructural a la λ del HP). Suavizador RTS para la senda de u*.

NO importa ni modifica el motor: solo lee series y devuelve una pd.Series.
"""

from __future__ import annotations
from typing import Dict, Optional, Tuple
import numpy as np
import pandas as pd
from scipy.optimize import minimize


def _factores_estacionales(u: pd.Series) -> Dict[int, float]:
    """Factores estacionales aditivos (suma cero) del paro, por trimestre."""
    u = u.dropna()
    if len(u) < 16:
        return {1: 0.52, 2: -0.12, 3: -0.30, 4: -0.10}
    ma4 = u.rolling(4, center=True).mean()
    diff = (u - ma4)
    by_q = diff.groupby(diff.index.quarter).mean()
    return (by_q - by_q.mean()).to_dict()


def _desestacionalizar(u: pd.Series) -> pd.Series:
    f = _factores_estacionales(u)
    return u - u.index.quarter.map(lambda q: f.get(q, 0.0))


def _construir_matrices(theta: np.ndarray, beta_signo: float = 1.0):
    phi1, phi2, beta, s_eta, s_c, s_pi = theta
    T = np.array([[1.0, 0.0, 0.0],
                  [0.0, phi1, phi2],
                  [0.0, 1.0, 0.0]])
    R = np.array([[1.0, 0.0],
                  [0.0, 1.0],
                  [0.0, 0.0]])
    Q = np.diag([s_eta ** 2, s_c ** 2])
    RQR = R @ Q @ R.T
    # Z y H se construyen por observación (manejo de faltantes) en el filtro.
    return T, RQR, beta


def _kalman(theta: np.ndarray, Y: np.ndarray, suavizar: bool = False):
    """Filtro (y opcional suavizador RTS). Y: (T,2) con NaN en faltantes.
    Devuelve (-loglik) si suavizar=False; si True, la senda suavizada de estados."""
    T_mat, RQR, beta = _construir_matrices(theta)
    n = Y.shape[0]
    m = 3
    H_u = 1e-6                      # identidad u=u*+c (ruido ínfimo)
    H_pi = theta[5] ** 2
    Zfull = np.array([[1.0, 1.0, 0.0],
                      [0.0, 0.0, -beta]])
    Hfull = np.array([H_u, H_pi])

    # Inicialización difusa moderada
    a = np.array([np.nanmean(Y[:8, 0]) if np.isfinite(np.nanmean(Y[:8, 0])) else 15.0, 0.0, 0.0])
    P = np.diag([10.0, 2.0, 2.0])

    llf = 0.0
    a_filt = np.zeros((n, m)); P_filt = np.zeros((n, m, m))
    a_pred = np.zeros((n, m)); P_pred = np.zeros((n, m, m))

    for t in range(n):
        # Predicción
        if t == 0:
            at, Pt = a, P
        else:
            at = T_mat @ a_filt[t - 1]
            Pt = T_mat @ P_filt[t - 1] @ T_mat.T + RQR
        a_pred[t] = at; P_pred[t] = Pt

        # Selección de observaciones disponibles
        obs = np.where(np.isfinite(Y[t]))[0]
        if len(obs) == 0:
            a_filt[t] = at; P_filt[t] = Pt
            continue
        Z = Zfull[obs, :]; d = Y[t, obs]; Hd = np.diag(Hfull[obs])
        v = d - Z @ at
        F = Z @ Pt @ Z.T + Hd
        try:
            Finv = np.linalg.inv(F)
        except np.linalg.LinAlgError:
            return 1e10
        K = Pt @ Z.T @ Finv
        a_filt[t] = at + K @ v
        P_filt[t] = Pt - K @ Z @ Pt
        sign, logdet = np.linalg.slogdet(F)
        if sign <= 0:
            return 1e10
        llf += -0.5 * (len(obs) * np.log(2 * np.pi) + logdet + v @ Finv @ v)

    if not suavizar:
        return -llf

    # Suavizador RTS
    a_sm = a_filt.copy(); P_sm = P_filt.copy()
    for t in range(n - 2, -1, -1):
        Pp = P_pred[t + 1]
        try:
            C = P_filt[t] @ T_mat.T @ np.linalg.inv(Pp)
        except np.linalg.LinAlgError:
            C = P_filt[t] @ T_mat.T @ np.linalg.pinv(Pp)
        a_sm[t] = a_filt[t] + C @ (a_sm[t + 1] - a_pred[t + 1])
        P_sm[t] = P_filt[t] + C @ (P_sm[t + 1] - Pp) @ C.T
    return a_sm


def estimar_nairu_estructural(unemployment: pd.Series, inflation_services: pd.Series,
                              sigma_eta_max: float = 0.25) -> Dict:
    """
    Estima la NAIRU estructural. Devuelve dict con 'nairu' (pd.Series suavizada),
    'gap' (paro cíclico), 'params' y 'llf'.
    """
    u = unemployment.dropna().astype(float)
    u_sa = _desestacionalizar(u)
    pis = inflation_services.reindex(u_sa.index).astype(float)
    dpi = pis.diff()  # acelerador: Δ inflación de servicios

    Y = np.column_stack([u_sa.values, dpi.values])  # (T,2), NaN en dpi[0]

    # θ = [phi1, phi2, beta, s_eta, s_c, s_pi]
    theta0 = np.array([1.30, -0.40, 0.15, 0.10, 0.35, 0.40])
    bounds = [(0.0, 1.95), (-0.98, 0.60), (0.0, 1.5),
              (0.02, sigma_eta_max), (0.05, 2.0), (0.05, 3.0)]

    def neg_llf(th):
        # Estacionariedad AR(2): raíces fuera del círculo unidad
        phi1, phi2 = th[0], th[1]
        if phi2 >= 1 - abs(phi1):   # condición de estacionariedad AR(2)
            return 1e9
        return _kalman(th, Y, suavizar=False)

    res = minimize(neg_llf, theta0, method="L-BFGS-B", bounds=bounds)
    theta = res.x
    estados = _kalman(theta, Y, suavizar=True)
    nairu = pd.Series(estados[:, 0], index=u_sa.index, name="nairu_estructural")
    gap = pd.Series(estados[:, 1], index=u_sa.index, name="paro_ciclico")

    return {
        "nairu": nairu,
        "gap": gap,
        "u_sa": u_sa,
        "params": dict(zip(["phi1", "phi2", "beta", "sigma_eta", "sigma_c", "sigma_pi"], theta)),
        "llf": -res.fun,
        "convergencia": bool(res.success),
    }


# ==============================================================================
# VARIANTE MULTIVARIANTE (estilo filtro FMI): añade la ley de Okun como segunda
# ecuación de medida, que ata el paro cíclico a la brecha de PIB observada. Con
# dos señales del ciclo (inflación + actividad), u* queda mejor identificada
# como tendencia, en vez de absorber el nivel del paro.
# ==============================================================================

def estimar_nairu_multivariante(unemployment: pd.Series, inflation_services: pd.Series,
                                 output_gap: pd.Series, sigma_eta_max: float = 0.20) -> Dict:
    from scipy.optimize import minimize
    u = unemployment.dropna().astype(float)
    u_sa = _desestacionalizar(u)
    pis = inflation_services.reindex(u_sa.index).astype(float)
    og = output_gap.reindex(u_sa.index).astype(float)
    dpi = pis.diff()
    Y = np.column_stack([u_sa.values, dpi.values, og.values])  # (T,3)

    # θ = [phi1, phi2, beta, gamma, s_eta, s_c, s_pi, s_og]
    theta0 = np.array([1.30, -0.40, 0.15, 0.80, 0.08, 0.35, 0.40, 0.50])
    bounds = [(0.0, 1.95), (-0.98, 0.60), (0.0, 1.5), (0.0, 3.0),
              (0.02, sigma_eta_max), (0.05, 2.0), (0.05, 3.0), (0.05, 3.0)]

    def matrices(th):
        phi1, phi2 = th[0], th[1]
        T = np.array([[1, 0, 0], [0, phi1, phi2], [0, 1, 0]], float)
        R = np.array([[1, 0], [0, 1], [0, 0]], float)
        Q = np.diag([th[4] ** 2, th[5] ** 2])
        return T, R @ Q @ R.T

    def kalman(th, smooth=False):
        T_mat, RQR = matrices(th)
        beta, gamma = th[2], th[3]
        Zf = np.array([[1, 1, 0], [0, 0, -beta], [0, -gamma, 0]], float)
        Hf = np.array([1e-6, th[6] ** 2, th[7] ** 2])
        n, m = Y.shape[0], 3
        a = np.array([np.nanmean(Y[:8, 0]), 0.0, 0.0]); P = np.diag([10., 2., 2.])
        llf = 0.0
        af = np.zeros((n, m)); Pf = np.zeros((n, m, m))
        ap = np.zeros((n, m)); Pp = np.zeros((n, m, m))
        for t in range(n):
            if t == 0:
                at, Pt = a, P
            else:
                at = T_mat @ af[t - 1]; Pt = T_mat @ Pf[t - 1] @ T_mat.T + RQR
            ap[t] = at; Pp[t] = Pt
            obs = np.where(np.isfinite(Y[t]))[0]
            if len(obs) == 0:
                af[t] = at; Pf[t] = Pt; continue
            Z = Zf[obs]; d = Y[t, obs]; Hd = np.diag(Hf[obs])
            v = d - Z @ at; F = Z @ Pt @ Z.T + Hd
            try: Finv = np.linalg.inv(F)
            except np.linalg.LinAlgError: return 1e10
            K = Pt @ Z.T @ Finv
            af[t] = at + K @ v; Pf[t] = Pt - K @ Z @ Pt
            s, ld = np.linalg.slogdet(F)
            if s <= 0: return 1e10
            llf += -0.5 * (len(obs) * np.log(2 * np.pi) + ld + v @ Finv @ v)
        if not smooth: return -llf
        asm = af.copy()
        for t in range(n - 2, -1, -1):
            try: C = Pf[t] @ T_mat.T @ np.linalg.inv(Pp[t + 1])
            except np.linalg.LinAlgError: C = Pf[t] @ T_mat.T @ np.linalg.pinv(Pp[t + 1])
            asm[t] = af[t] + C @ (asm[t + 1] - ap[t + 1])
        return asm

    def neg_llf(th):
        if th[1] >= 1 - abs(th[0]): return 1e9
        return kalman(th, smooth=False)

    res = minimize(neg_llf, theta0, method="L-BFGS-B", bounds=bounds)
    est = kalman(res.x, smooth=True)
    nairu = pd.Series(est[:, 0], index=u_sa.index, name="nairu_multivariante")
    return {"nairu": nairu, "gap": pd.Series(est[:, 1], index=u_sa.index),
            "u_sa": u_sa,
            "params": dict(zip(["phi1", "phi2", "beta", "gamma", "s_eta", "s_c", "s_pi", "s_og"], res.x)),
            "llf": -res.fun, "convergencia": bool(res.success)}


# ==============================================================================
# VARIANTE AJUSTADA POR CRISIS (Gordon "triángulo" + tratamiento COVID).
# Controla la Gran Recesión (2009-2013) y el COVID (2020-2021) en la curva de
# Phillips con dummies estimadas, y desempondera las medidas del COVID (ERTE
# distorsionó la EPA). Objetivo: que β se identifique con los periodos normales.
# ==============================================================================

def estimar_nairu_ajustado(unemployment: pd.Series, inflation_services: pd.Series,
                            sigma_eta_max: float = 0.30) -> Dict:
    from scipy.optimize import minimize
    u = unemployment.dropna().astype(float)
    u_sa = _desestacionalizar(u)
    pis = inflation_services.reindex(u_sa.index).astype(float)
    dpi = pis.diff()
    idx = u_sa.index

    # Dummies de crisis (sobre la curva de Phillips)
    yr = idx.year; q = idx.quarter
    d_gfc = np.asarray(((yr >= 2009) & (yr <= 2013)), dtype=float)
    d_cov = np.asarray(((yr == 2020) | ((yr == 2021) & (q <= 2))), dtype=float)
    # Desemponderación de medidas COVID (ERTE / trabajo de campo EPA 2020)
    covid_dw = np.asarray((yr == 2020), dtype=float)

    Y = np.column_stack([u_sa.values, dpi.values])
    n = len(idx)

    # θ = [phi1, phi2, beta, d_gfc, d_cov, s_eta, s_c, s_pi]
    theta0 = np.array([1.30, -0.40, 0.20, -0.5, -0.5, 0.10, 0.35, 0.40])
    bounds = [(0.0, 1.95), (-0.98, 0.60), (0.0, 1.5), (-3.0, 3.0), (-5.0, 5.0),
              (0.02, sigma_eta_max), (0.05, 2.0), (0.05, 3.0)]

    def matrices(th):
        T = np.array([[1, 0, 0], [0, th[0], th[1]], [0, 1, 0]], float)
        R = np.array([[1, 0], [0, 1], [0, 0]], float)
        Q = np.diag([th[5] ** 2, th[6] ** 2])
        return T, R @ Q @ R.T

    def kalman(th, smooth=False):
        T_mat, RQR = matrices(th)
        beta, dg, dc = th[2], th[3], th[4]
        Zf = np.array([[1, 1, 0], [0, 0, -beta]], float)
        H_pi = th[7] ** 2
        m = 3
        a = np.array([np.nanmean(Y[:8, 0]), 0.0, 0.0]); P = np.diag([10., 2., 2.])
        llf = 0.0
        af = np.zeros((n, m)); Pf = np.zeros((n, m, m))
        ap = np.zeros((n, m)); Pp = np.zeros((n, m, m))
        for t in range(n):
            if t == 0:
                at, Pt = a, P
            else:
                at = T_mat @ af[t - 1]; Pt = T_mat @ Pf[t - 1] @ T_mat.T + RQR
            ap[t] = at; Pp[t] = Pt
            # H variable: COVID desemponderado en la identidad de paro
            H_u = 1e-6 + 4.0 * covid_dw[t]
            reg = np.array([0.0, dg * d_gfc[t] + dc * d_cov[t]])  # término determinista Phillips
            obs = [i for i in range(2) if np.isfinite(Y[t, i])]
            if not obs:
                af[t] = at; Pf[t] = Pt; continue
            Z = Zf[obs]; d = Y[t, obs] - reg[obs]; Hd = np.diag([H_u, H_pi])[np.ix_(obs, obs)]
            v = d - Z @ at; F = Z @ Pt @ Z.T + Hd
            try: Finv = np.linalg.inv(F)
            except np.linalg.LinAlgError: return 1e10
            K = Pt @ Z.T @ Finv
            af[t] = at + K @ v; Pf[t] = Pt - K @ Z @ Pt
            s, ld = np.linalg.slogdet(F)
            if s <= 0: return 1e10
            llf += -0.5 * (len(obs) * np.log(2 * np.pi) + ld + v @ Finv @ v)
        if not smooth: return -llf
        asm = af.copy()
        for t in range(n - 2, -1, -1):
            try: C = Pf[t] @ T_mat.T @ np.linalg.inv(Pp[t + 1])
            except np.linalg.LinAlgError: C = Pf[t] @ T_mat.T @ np.linalg.pinv(Pp[t + 1])
            asm[t] = af[t] + C @ (asm[t + 1] - ap[t + 1])
        return asm

    def neg(th):
        if th[1] >= 1 - abs(th[0]): return 1e9
        return kalman(th, smooth=False)

    res = minimize(neg, theta0, method="L-BFGS-B", bounds=bounds)
    est = kalman(res.x, smooth=True)
    nairu = pd.Series(est[:, 0], index=idx, name="nairu_ajustado")
    return {"nairu": nairu, "gap": pd.Series(est[:, 1], index=idx), "u_sa": u_sa,
            "params": dict(zip(["phi1","phi2","beta","d_gfc","d_covid","s_eta","s_c","s_pi"], res.x)),
            "llf": -res.fun, "convergencia": bool(res.success)}


# ==============================================================================
# VARIANTE EN NIVELES (la que encaja con el scatter: corr paro–serv ≈ -0,77).
# Phillips en NIVELES:  π^serv_t = μ - γ·(u_t - u*_t) + dummies_crisis + ε
# con la NAIRU DISCIPLINADA (σ_η baja) para que la brecha (u-u*) conserve la
# variación de nivel que correlaciona con la inflación. u* queda anclada por la
# identidad u^sa = u* + c con c estacionario de media cero.
# ==============================================================================

def estimar_nairu_niveles(unemployment: pd.Series, inflation_services: pd.Series,
                           sigma_eta_max: float = 0.08, x0=None, maxiter=None) -> Dict:
    from scipy.optimize import minimize
    u = unemployment.dropna().astype(float)
    u_sa = _desestacionalizar(u)
    pis = inflation_services.reindex(u_sa.index).astype(float)   # NIVEL, no Δ
    idx = u_sa.index
    yr = idx.year; q = idx.quarter
    d_gfc = np.asarray(((yr >= 2009) & (yr <= 2013)), dtype=float)
    d_cov = np.asarray(((yr == 2020) | ((yr == 2021) & (q <= 2))), dtype=float)
    covid_dw = np.asarray((yr == 2020), dtype=float)
    Y = np.column_stack([u_sa.values, pis.values]); n = len(idx)

    # θ = [phi1, phi2, gamma, mu_s, d_gfc, d_covid, s_eta, s_c, s_pi]
    theta0 = np.array([1.40, -0.50, 0.15, 2.5, -1.0, -1.0, 0.04, 0.40, 0.60])
    bounds = [(0.0, 1.95), (-0.98, 0.60), (0.0, 3.0), (0.0, 6.0), (-6.0, 6.0),
              (-6.0, 6.0), (0.01, sigma_eta_max), (0.05, 3.0), (0.05, 3.0)]

    def matrices(th):
        T = np.array([[1, 0, 0], [0, th[0], th[1]], [0, 1, 0]], float)
        R = np.array([[1, 0], [0, 1], [0, 0]], float)
        Q = np.diag([th[6] ** 2, th[7] ** 2])
        return T, R @ Q @ R.T

    def kalman(th, smooth=False):
        T_mat, RQR = matrices(th)
        gamma, mu_s, dg, dc = th[2], th[3], th[4], th[5]
        Zf = np.array([[1, 1, 0], [0, -gamma, 0]], float)
        H_pi = th[8] ** 2; m = 3
        a = np.array([np.nanmean(Y[:8, 0]), 0.0, 0.0]); P = np.diag([10., 3., 3.])
        llf = 0.0
        af = np.zeros((n, m)); Pf = np.zeros((n, m, m)); ap = np.zeros((n, m)); Pp = np.zeros((n, m, m))
        for t in range(n):
            if t == 0: at, Pt = a, P
            else: at = T_mat @ af[t-1]; Pt = T_mat @ Pf[t-1] @ T_mat.T + RQR
            ap[t] = at; Pp[t] = Pt
            H_u = 1e-6 + 4.0 * covid_dw[t]
            reg = np.array([0.0, mu_s + dg*d_gfc[t] + dc*d_cov[t]])  # término determinista Phillips
            obs = [i for i in range(2) if np.isfinite(Y[t, i])]
            if not obs: af[t] = at; Pf[t] = Pt; continue
            Z = Zf[obs]; dd = Y[t, obs] - reg[obs]; Hd = np.diag([H_u, H_pi])[np.ix_(obs, obs)]
            v = dd - Z @ at; F = Z @ Pt @ Z.T + Hd
            try: Finv = np.linalg.inv(F)
            except np.linalg.LinAlgError: return 1e10
            K = Pt @ Z.T @ Finv; af[t] = at + K @ v; Pf[t] = Pt - K @ Z @ Pt
            s, ld = np.linalg.slogdet(F)
            if s <= 0: return 1e10
            llf += -0.5 * (len(obs)*np.log(2*np.pi) + ld + v @ Finv @ v)
        if not smooth: return -llf
        asm = af.copy()
        for t in range(n-2, -1, -1):
            try: C = Pf[t] @ T_mat.T @ np.linalg.inv(Pp[t+1])
            except np.linalg.LinAlgError: C = Pf[t] @ T_mat.T @ np.linalg.pinv(Pp[t+1])
            asm[t] = af[t] + C @ (asm[t+1] - ap[t+1])
        return asm

    def neg(th):
        if th[1] >= 1 - abs(th[0]): return 1e9
        return kalman(th, smooth=False)

    x_ini = np.asarray(x0) if x0 is not None else theta0
    opts = {"maxiter": maxiter} if maxiter else None
    res = minimize(neg, x_ini, method="L-BFGS-B", bounds=bounds, options=opts)
    est = kalman(res.x, smooth=True)
    nairu = pd.Series(est[:, 0], index=idx, name="nairu_niveles")
    return {"nairu": nairu, "gap": pd.Series(est[:, 1], index=idx), "u_sa": u_sa,
            "params": dict(zip(["phi1","phi2","gamma","mu_serv","d_gfc","d_covid","s_eta","s_c","s_pi"], res.x)),
            "llf": -res.fun, "convergencia": bool(res.success)}
