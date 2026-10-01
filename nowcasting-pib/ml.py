"""
¿Le gana el machine learning a una regresión de dos variables?

Mismo panel, misma ventana de evaluación (2015-Q1 en adelante, ventana
expansiva) y mismos dos referentes que nowcast.py. Cada trimestre se reentrena
cada modelo solo con el pasado y se predice el trimestre siguiente. Los
hiperparámetros se eligen dentro de cada ventana con validación cruzada de
series de tiempo, para no mirar el futuro.

Modelos:
  - OLS de nowcast.py (producción manufacturera y exportaciones)
  - Ridge y LASSO sobre un conjunto ampliado (rezagos incluidos)
  - Random Forest y Gradient Boosting sobre el mismo conjunto ampliado

Salidas: resultados_ml.csv (predicción por trimestre y modelo)
         tabla_ml.csv     (RMSE, mejora contra cada referente y valor p de
                           Diebold-Mariano contra la OLS y contra el promedio)

Uso: python ml.py
"""

from __future__ import annotations

import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Lasso, LinearRegression, Ridge
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from nowcast import INICIO_PRUEBA, PREDICTORES, backtest, construir_panel, rmse

warnings.filterwarnings("ignore")
AQUI = Path(__file__).parent
SEMILLA = 7


def caracteristicas(panel: pd.DataFrame) -> pd.DataFrame:
    """Predictores base más sus rezagos y el rezago del PIB."""
    d = panel[["pib"] + PREDICTORES].copy()
    for c in PREDICTORES + ["pib"]:
        d[f"{c}_rez1"] = d[c].shift(1)
    d["ingenuo"] = d["pib"].shift(1)
    return d.dropna()


AMPLIADO = PREDICTORES + [f"{c}_rez1" for c in PREDICTORES] + ["pib_rez1"]


def modelos() -> dict:
    cv = TimeSeriesSplit(n_splits=4)
    escalar = lambda m: make_pipeline(StandardScaler(), m)
    return {
        "OLS (nowcast.py)": (LinearRegression(), PREDICTORES, None),
        "Ridge": (escalar(Ridge()), AMPLIADO,
                  {"ridge__alpha": [0.1, 1, 10, 100]}),
        "LASSO": (escalar(Lasso(max_iter=20000)), AMPLIADO,
                  {"lasso__alpha": [0.01, 0.05, 0.1, 0.5]}),
        "Random Forest": (RandomForestRegressor(n_estimators=300, random_state=SEMILLA), AMPLIADO,
                          {"min_samples_leaf": [3, 6], "max_depth": [2, 4]}),
        "Gradient Boosting": (GradientBoostingRegressor(random_state=SEMILLA), AMPLIADO,
                              {"learning_rate": [0.03, 0.1], "max_depth": [1, 2],
                               "n_estimators": [100, 300]}),
    }, cv


def backtest_ml(d: pd.DataFrame) -> pd.DataFrame:
    especs, cv = modelos()
    trimestres = list(d.index)
    inicio = next(i for i, t in enumerate(trimestres) if t >= INICIO_PRUEBA)
    filas = []
    for i in range(inicio, len(trimestres)):
        historia, actual = d.iloc[:i], d.iloc[[i]]
        fila = {"trimestre": trimestres[i], "observado": float(actual["pib"].iloc[0]),
                "ingenuo": float(actual["ingenuo"].iloc[0]),
                "promedio": float(historia["pib"].mean())}
        for nombre, (modelo, cols, rejilla) in especs.items():
            X, y = historia[cols].to_numpy(float), historia["pib"].to_numpy(float)
            if rejilla:
                modelo = GridSearchCV(modelo, rejilla, cv=cv,
                                      scoring="neg_root_mean_squared_error").fit(X, y)
            else:
                modelo.fit(X, y)
            fila[nombre] = float(modelo.predict(actual[cols].to_numpy(float))[0])
        filas.append(fila)
        print(f"  {trimestres[i]} listo", end="\r")
    print()
    return pd.DataFrame(filas).set_index("trimestre")


def diebold_mariano(a, b, y) -> float:
    """Valor p de Diebold-Mariano (pérdida cuadrática, horizonte 1, corrección
    de Harvey, Leybourne y Newbold). H0: los dos pronósticos son igual de buenos."""
    d = (y - a) ** 2 - (y - b) ** 2
    n = len(d)
    estad = d.mean() / np.sqrt(d.var(ddof=1) / n) * np.sqrt((n - 1) / n)
    return float(2 * (1 - stats.t.cdf(abs(estad), n - 1)))


def tabla(res: pd.DataFrame, etiqueta: str) -> pd.DataFrame:
    nombres = [c for c in res.columns if c not in ("observado", "ingenuo", "promedio")]
    r_ing = rmse(res["ingenuo"], res["observado"])
    r_prom = rmse(res["promedio"], res["observado"])
    filas = []
    for n in nombres:
        r = rmse(res[n], res["observado"])
        y = res["observado"]
        filas.append({"muestra": etiqueta, "modelo": n, "rmse": r,
                      "mejora_vs_ingenuo_pc": (1 - r / r_ing) * 100,
                      "mejora_vs_promedio_pc": (1 - r / r_prom) * 100,
                      "p_dm_vs_ols": (np.nan if n.startswith("OLS")
                                      else diebold_mariano(res[n], res["OLS (nowcast.py)"], y)),
                      "p_dm_vs_promedio": diebold_mariano(res[n], res["promedio"], y)})
    return pd.DataFrame(filas)


def main() -> None:
    panel = construir_panel()
    d = caracteristicas(panel)
    print(f"Panel: {len(d)} trimestres, evaluación desde {INICIO_PRUEBA}")
    res = backtest_ml(d)

    # Control: la columna OLS tiene que reproducir el nowcast de nowcast.py.
    original = backtest(panel)["nowcast"].reindex(res.index)
    dif = float((res["OLS (nowcast.py)"] - original).abs().max())
    print(f"OLS contra nowcast.py: diferencia máxima {dif:.2e}")
    assert dif < 1e-8, "la OLS no reproduce nowcast.py: la comparación no sería justa"
    t = pd.concat([tabla(res, "completa"),
                   tabla(res[~res.index.str.startswith("2020")], "sin 2020")])
    res.round(3).to_csv(AQUI / "resultados_ml.csv")
    t.round(3).to_csv(AQUI / "tabla_ml.csv", index=False)
    with pd.option_context("display.width", 120):
        print(t.round(2).to_string(index=False))


if __name__ == "__main__":
    main()
