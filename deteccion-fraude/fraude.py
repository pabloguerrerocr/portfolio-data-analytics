"""
Detección de fraude con tarjeta: cuánto dinero ahorra cada regla de alerta.

PREGUNTA
    Un banco no decide "¿es fraude?". Decide "¿mando esta transacción a
    revisión?", y cada revisión cuesta. ¿Qué regla de alerta ahorra más dinero,
    y cuánto se equivoca quien elige el modelo por su exactitud?

DECISIONES METODOLÓGICAS
    1. Partición temporal, no aleatoria: entrenamiento con el primer 60 % de las
       transacciones, elección del umbral con el 20 % siguiente y evaluación con
       el último 20 %. En producción el modelo solo conoce el pasado.

    2. La métrica es dinero, no exactitud. Con 0,17 % de fraude, no alertar
       nunca acierta el 99,8 % de las veces y no ahorra nada. Ahorro neto =
       monto del fraude detenido − costo de revisar cada alerta.

    3. Dos formas de decidir. Un umbral único sobre la probabilidad (lo
       habitual), o la regla de valor esperado: alertar cuando
       probabilidad × monto > costo de revisión. La segunda no se ajusta con
       nada: sale directo de la cuenta de costos.

    4. Sensibilidad al costo de revisión. No hay un número público, así que se
       reporta con tres valores (€1, €5 y €15 por alerta).

Supuesto declarado: una alerta revisada detiene el fraude completo.

Uso:  python fraude.py     (baja los datos solo si no están)
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

AQUI = Path(__file__).parent
DATOS = AQUI / "datos" / "creditcard.csv"
GRAFICOS = AQUI / "graficos"
# Copia pública del conjunto de ULB/Worldline (Kaggle), la misma que usa el
# tutorial de datos desbalanceados de TensorFlow. No pide cuenta.
URL = "https://storage.googleapis.com/download.tensorflow.org/data/creditcard.csv"

COSTOS = [1.0, 5.0, 15.0]       # euros por alerta revisada
COSTO_CENTRAL = 5.0
UMBRALES = np.round(np.concatenate([np.arange(0.001, 0.01, 0.001),
                                    np.arange(0.01, 1.0, 0.01)]), 3)
REMUESTREOS = 2000

# Paleta Okabe-Ito, la misma del resto del repositorio.
AZUL = "#0072B2"
NARANJA = "#E69F00"
TINTA = "#3A3A3A"
GRIS = "#B8B8B8"


# ---------------------------------------------------------------- datos ----
def cargar() -> pd.DataFrame:
    if not DATOS.exists():
        import requests
        print("No encuentro los datos. Bajándolos (150 MB)...")
        DATOS.parent.mkdir(parents=True, exist_ok=True)
        with requests.get(URL, stream=True, timeout=300) as r:
            r.raise_for_status()
            with open(DATOS, "wb") as f:
                for trozo in r.iter_content(1 << 20):
                    f.write(trozo)
    df = pd.read_csv(DATOS).sort_values("Time", kind="stable")
    assert len(df) == 284_807 and df["Class"].sum() == 492, "datos inesperados"
    return df.reset_index(drop=True)


def particion(df: pd.DataFrame):
    n = len(df)
    a, b = int(n * 0.6), int(n * 0.8)
    return df.iloc[:a], df.iloc[a:b], df.iloc[b:]


def variables(df: pd.DataFrame) -> pd.DataFrame:
    X = df.drop(columns=["Class", "Time"]).copy()
    X["log_monto"] = np.log1p(X.pop("Amount"))
    X["hora"] = (df["Time"] // 3600) % 24
    return X


# --------------------------------------------------------------- modelos ----
def modelos():
    # Sin pesos de clase: la regla de valor esperado necesita probabilidades
    # que signifiquen lo que dicen, y reponderar las infla.
    return {
        "Regresión logística": make_pipeline(
            StandardScaler(), LogisticRegression(max_iter=2000, C=0.1)),
        "Gradient Boosting": HistGradientBoostingClassifier(
            max_iter=400, learning_rate=0.05, max_leaf_nodes=15,
            l2_regularization=1.0, random_state=0),
    }


# --------------------------------------------------------------- dinero ----
def aportes(alerta, fraude, monto, costo):
    """Ahorro neto por transacción: monto si se detiene un fraude, menos costo."""
    return alerta * (fraude * monto - costo)


def ahorro(alerta, fraude, monto, costo) -> float:
    return float(aportes(alerta, fraude, monto, costo).sum())


def mejor_umbral(p, fraude, monto, costo) -> float:
    valores = [ahorro(p >= u, fraude, monto, costo) for u in UMBRALES]
    return float(UMBRALES[int(np.argmax(valores))])


def intervalo(dif: np.ndarray, semilla=0):
    """Intervalo de 95 % del ahorro total por bootstrap de Poisson."""
    rng = np.random.default_rng(semilla)
    totales = []
    for _ in range(REMUESTREOS // 200):
        w = rng.poisson(1.0, size=(200, len(dif)))
        totales.append(w @ dif)
    totales = np.concatenate(totales)
    return np.percentile(totales, [2.5, 97.5])


# -------------------------------------------------------------- gráfico ----
def graficar(p, fraude, monto, umbral_val, ahorro_ve, total_fraude, nombre):
    GRAFICOS.mkdir(parents=True, exist_ok=True)
    destino = GRAFICOS / "ahorro_por_umbral.png"
    curva = np.array([ahorro(p >= u, fraude, monto, COSTO_CENTRAL)
                      for u in UMBRALES]) / total_fraude * 100

    fig, ax = plt.subplots(figsize=(10, 5.6), dpi=160)
    fig.patch.set_facecolor("white")
    ax.axhline(0, color=GRIS, lw=1, zorder=1)
    ax.plot(UMBRALES, curva, color=AZUL, lw=2.2, zorder=3,
            label=f"Umbral único ({nombre})")
    ax.axhline(ahorro_ve / total_fraude * 100, color=NARANJA, lw=2.2, ls="--",
               zorder=2, label="Regla de valor esperado (probabilidad × monto > costo)")

    decimal = f"{umbral_val:g}".replace(".", ",")
    for u, texto, desfase in [
            (0.5, "umbral 0,5\n(el de fábrica)", (-120, -60)),
            (umbral_val, f"umbral {decimal}\n(elegido en validación)", (8, -34))]:
        y = curva[np.argmin(np.abs(UMBRALES - u))]
        ax.plot([u], [y], "o", color=AZUL, ms=8, markeredgecolor="white",
                markeredgewidth=1.5, zorder=4)
        ax.annotate(texto, xy=(u, y), xytext=desfase, textcoords="offset points",
                    fontsize=8.5, color=TINTA,
                    arrowprops=dict(arrowstyle="-", color=GRIS, lw=0.9))

    ax.set_xscale("log")
    ax.set_xlabel("Umbral de probabilidad para alertar (escala logarítmica)",
                  fontsize=9.5, color=TINTA)
    ax.set_ylabel("Ahorro neto (% del fraude del período)", fontsize=9.5,
                  color=TINTA)
    ax.tick_params(colors=TINTA, labelsize=8.5)
    ax.grid(axis="y", color="#EAEAEA", lw=0.9)
    ax.set_axisbelow(True)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    for lado in ("left", "bottom"):
        ax.spines[lado].set_color(GRIS)
    ax.legend(frameon=False, fontsize=9, loc="lower left")

    fig.suptitle("Detección de fraude: el umbral decide cuánto dinero se ahorra",
                 fontsize=13, fontweight="bold", color=TINTA, x=0.01,
                 ha="left", y=1.0)
    fig.text(0.01, 0.94,
             f"Último 20 % de las transacciones, nunca visto al entrenar. "
             f"Costo de revisión: €{COSTO_CENTRAL:g} por alerta.  "
             "Fuente: ULB / Worldline.",
             fontsize=8.6, color="#6B6B6B", ha="left")
    fig.savefig(destino, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return destino


# ------------------------------------------------------------------ main ----
def main() -> None:
    df = cargar()
    ent, val, pru = particion(df)
    print(f"Entrenamiento {len(ent):,} ({ent['Class'].sum()} fraudes) · "
          f"validación {len(val):,} ({val['Class'].sum()}) · "
          f"prueba {len(pru):,} ({pru['Class'].sum()})")

    fv, mv = val["Class"].to_numpy(), val["Amount"].to_numpy()
    fp, mp = pru["Class"].to_numpy(), pru["Amount"].to_numpy()
    total_fraude = float(mp[fp == 1].sum())
    print(f"Fraude en el período de prueba: €{total_fraude:,.0f}")

    prob_val, prob_pru, calidad = {}, {}, []
    for nombre, m in modelos().items():
        m.fit(variables(ent), ent["Class"])
        prob_val[nombre] = m.predict_proba(variables(val))[:, 1]
        prob_pru[nombre] = m.predict_proba(variables(pru))[:, 1]
        calidad.append({
            "modelo": nombre,
            "pr_auc_validacion": average_precision_score(fv, prob_val[nombre]),
            "pr_auc_prueba": average_precision_score(fp, prob_pru[nombre]),
            "brier_prueba": brier_score_loss(fp, prob_pru[nombre]),
            "fraudes_esperados_prueba": prob_pru[nombre].sum(),
            "fraudes_observados_prueba": int(fp.sum()),
        })
    calidad = pd.DataFrame(calidad)
    print("\n" + calidad.round(4).to_string(index=False))

    # El modelo se elige en validación, nunca mirando la prueba.
    elegido = calidad.loc[calidad["pr_auc_validacion"].idxmax(), "modelo"]
    print(f"\nModelo elegido en validación: {elegido}")

    filas = []
    for nombre in prob_pru:
        pv, pp = prob_val[nombre], prob_pru[nombre]
        for costo in COSTOS:
            u = mejor_umbral(pv, fv, mv, costo)
            politicas = {
                "Sin modelo (nunca alertar)": np.zeros_like(fp, dtype=bool),
                "Umbral 0,5": pp >= 0.5,
                "Umbral elegido en validación": pp >= u,
                "Valor esperado": pp * mp > costo,
            }
            base = aportes(politicas["Umbral elegido en validación"], fp, mp, costo)
            for politica, alerta in politicas.items():
                a = aportes(alerta, fp, mp, costo)
                lo, hi = intervalo(a - base) if politica == "Valor esperado" else (np.nan, np.nan)
                detenido = float(mp[(fp == 1) & alerta].sum())
                filas.append({
                    "modelo": nombre,
                    "costo_revision": costo,
                    "politica": politica,
                    "umbral": u if politica.startswith("Umbral elegido") else np.nan,
                    "alertas": int(alerta.sum()),
                    "fraudes_detectados": int((alerta & (fp == 1)).sum()),
                    "exactitud_pc": float(((alerta) == (fp == 1)).mean() * 100),
                    "fraude_detenido_eur": detenido,
                    "costo_revisiones_eur": float(alerta.sum() * costo),
                    "ahorro_neto_eur": float(a.sum()),
                    "ahorro_pc_del_fraude": float(a.sum() / total_fraude * 100),
                    "dif_vs_umbral_ic95_inf": lo,
                    "dif_vs_umbral_ic95_sup": hi,
                })
    res = pd.DataFrame(filas)

    print("\n" + "=" * 78)
    print(f"AHORRO NETO EN PRUEBA — {elegido}")
    print("=" * 78)
    cols = ["costo_revision", "politica", "alertas", "fraudes_detectados",
            "exactitud_pc", "ahorro_neto_eur", "ahorro_pc_del_fraude",
            "dif_vs_umbral_ic95_inf", "dif_vs_umbral_ic95_sup"]
    print(res[res["modelo"] == elegido][cols].round(2).to_string(index=False))

    central = res[(res["modelo"] == elegido) & (res["costo_revision"] == COSTO_CENTRAL)]
    u = float(central["umbral"].dropna().iloc[0])
    ve = float(central.loc[central["politica"] == "Valor esperado", "ahorro_neto_eur"].iloc[0])
    destino = graficar(prob_pru[elegido], fp, mp, u, ve, total_fraude, elegido)

    res.round(4).to_csv(AQUI / "resultados_fraude.csv", index=False)
    calidad.round(5).to_csv(AQUI / "calidad_modelos.csv", index=False)
    print(f"\ngráfico:     {destino.relative_to(AQUI)}")
    print("resultados:  resultados_fraude.csv, calidad_modelos.csv")


if __name__ == "__main__":
    main()
