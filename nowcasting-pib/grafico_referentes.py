"""
El hallazgo del proyecto en una imagen: el error fuera de muestra de cada modelo
frente a los dos referentes.

Todos los modelos le ganan con holgura a repetir el trimestre anterior, y
ninguno por mucho al promedio histórico. Lee resultados_ml.csv, así que todas
las cifras salen de una misma corrida de ml.py y de una misma descarga de la OCDE.

Uso:  python grafico_referentes.py     (después de ml.py; no baja nada)
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

AQUI = Path(__file__).parent
GRAFICOS = AQUI / "graficos"

# Paleta Okabe-Ito, la misma del resto del repositorio.
AZUL = "#0072B2"
NARANJA = "#E69F00"
TINTA = "#3A3A3A"
GRIS = "#8C8C8C"

MODELOS = {
    "OLS (nowcast.py)": "Regresión de dos variables",
    "Ridge": "Ridge",
    "LASSO": "LASSO",
    "Random Forest": "Random Forest",
    "Gradient Boosting": "Gradient Boosting",
}


def rmse(a: pd.Series, b: pd.Series) -> float:
    return float(np.sqrt(((a - b) ** 2).mean()))


def coma(x: float) -> str:
    return f"{x:.2f}".replace(".", ",")


def main() -> None:
    r = pd.read_csv(AQUI / "resultados_ml.csv", index_col="trimestre")
    errores = (pd.Series({nombre: rmse(r[col], r["observado"])
                          for col, nombre in MODELOS.items()})
               .sort_values(ascending=False))
    ingenuo = rmse(r["ingenuo"], r["observado"])
    promedio = rmse(r["promedio"], r["observado"])

    fig, ax = plt.subplots(figsize=(10, 4.8), dpi=160)
    fig.patch.set_facecolor("white")
    y = np.arange(len(errores))
    ax.barh(y, errores.values, height=0.56, color=AZUL, zorder=2)
    for yi, v in zip(y, errores.values):
        # El valor va dentro de la barra: afuera chocaria con la línea del promedio.
        ax.text(v - 0.03, yi, coma(v), va="center", ha="right", fontsize=9.5,
                color="white", fontweight="bold", zorder=3)
    ax.set_yticks(y, errores.index, fontsize=10, color=TINTA)
    ax.tick_params(axis="y", length=0)

    tope = len(errores) - 0.3
    for x, color, texto in ((promedio, NARANJA, "promedio\nhistórico"),
                            (ingenuo, GRIS, "repetir el trimestre\nanterior")):
        ax.axvline(x, color=color, lw=2.2, zorder=1)
        ax.text(x + 0.03, tope, f"{texto}: {coma(x)}", color=TINTA, fontsize=9,
                va="bottom", ha="left")

    ax.set_xlim(0, ingenuo * 1.32)
    ax.set_ylim(-0.6, len(errores) + 0.55)
    ax.set_xlabel("error fuera de muestra (RMSE, puntos de variación trimestral del PIB)",
                  fontsize=9.5, color=TINTA)
    ax.grid(axis="x", color="#EAEAEA", lw=0.9, zorder=0)
    for lado in ("top", "right", "left"):
        ax.spines[lado].set_visible(False)
    ax.spines["bottom"].set_color("#B8B8B8")
    ax.tick_params(axis="x", colors=TINTA, labelsize=9)
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.1f}".replace(".", ",")))

    mejora_facil = (1 - errores.min() / ingenuo) * 100
    mejora_dificil = (1 - errores.min() / promedio) * 100
    fig.suptitle("Todos le ganan al referente fácil; ninguno, por mucho, al exigente",
                 fontsize=13.5, fontweight="bold", color=TINTA, x=0.01, ha="left",
                 y=1.0)
    fig.text(0.01, 0.925,
             f"El mejor modelo reduce el error {mejora_facil:.0f} % frente a repetir el "
             f"trimestre anterior, pero solo {mejora_dificil:.0f} % frente al promedio "
             f"histórico.\nNowcast del PIB trimestral de Costa Rica, {len(r)} trimestres "
             f"fuera de muestra ({r.index[0]}-{r.index[-1]}). Fuente: OCDE.",
             fontsize=9, color="#5A5A5A", ha="left", va="top")
    fig.tight_layout(rect=[0, 0, 1, 0.84])

    GRAFICOS.mkdir(parents=True, exist_ok=True)
    destino = GRAFICOS / "referentes.png"
    fig.savefig(destino, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"gráfico: {destino.relative_to(AQUI)}")
    print(errores.round(3).to_string())
    print(f"referentes: repetir {ingenuo:.3f}  promedio {promedio:.3f}")


if __name__ == "__main__":
    main()
