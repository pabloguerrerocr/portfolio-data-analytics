"""
Nowcasting del PIB trimestral de Costa Rica.

PREGUNTA
    El PIB trimestral se publica con meses de rezago. Los indicadores de
    coyuntura (producción industrial, comercio exterior) salen mucho antes.
    ¿Alcanzan para anticipar el crecimiento del PIB, y cuánto valor agregan
    realmente frente a no hacer nada?

DECISIONES METODOLÓGICAS
    1. Se nowcastea la variación TRIMESTRAL (t/t-1), no la interanual.
       La interanual es tan persistente que repetir el dato anterior ya es
       una predicción difícil de superar: el ejercicio se vuelve trivial y
       engañoso. La trimestral es la que efectivamente se nowcastea.

    2. Evaluación fuera de muestra con ventana expansiva: para el trimestre t
       el modelo se ajusta sólo con información hasta t-1. Nunca ve el futuro.

    3. Dos referentes, no uno. Superar al "ingenuo" (repetir t-1) es fácil
       porque la serie trimestral revierte a la media. El referente exigente
       es el PROMEDIO HISTÓRICO, y contra él se mide el valor real del modelo.

    4. Pocos predictores. Con ~100 trimestres, seis regresores sobreajustan:
       en pruebas fuera de muestra rindieron peor que dos.

Uso:  python nowcast.py     (requiere correr antes descargar_datos.py)
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

AQUI = Path(__file__).parent
DATOS = AQUI / "datos" / "cri_kei.csv"
GRAFICOS = AQUI / "graficos"

# Paleta Okabe-Ito, diseñada para ser distinguible con daltonismo.
AZUL = "#0072B2"
NARANJA = "#E69F00"
TINTA = "#3A3A3A"
GRIS = "#B8B8B8"

PREDICTORES = ["produccion_manufacturera", "exportaciones"]
INICIO_PRUEBA = "2015Q1"


# ---------------------------------------------------------------- datos ----
def a_trimestre(periodo: str) -> pd.Period:
    if "Q" in periodo:
        return pd.Period(periodo, freq="Q")
    return pd.Period(periodo, freq="M").asfreq("Q")


def serie(df, measure, freq, transformacion=None, actividad=None):
    m = (df["MEASURE"] == measure) & (df["FREQ"] == freq)
    if transformacion is not None:
        m &= df["TRANSFORMATION"] == transformacion
    if actividad is not None:
        m &= df["ACTIVITY"] == actividad
    sub = df[m].copy()
    if sub.empty:
        return pd.Series(dtype=float)
    sub["trim"] = sub["TIME_PERIOD"].map(a_trimestre)
    # Mensual -> trimestral: promedio de los meses del trimestre.
    return sub.groupby("trim")["valor"].mean().sort_index()


def construir_panel() -> pd.DataFrame:
    df = pd.read_csv(DATOS)
    panel = pd.DataFrame({
        "pib": serie(df, "B1GQ_Q", "Q", transformacion="G1"),
        "produccion_manufacturera": serie(df, "PRVM", "M",
                                          transformacion="G1", actividad="C"),
        "exportaciones": serie(df, "EX", "M", transformacion="G1"),
    })
    panel.index = panel.index.astype(str)
    return panel


# --------------------------------------------------------------- modelo ----
def ajustar(X: np.ndarray, y: np.ndarray) -> np.ndarray:
    A = np.column_stack([np.ones(len(X)), X])
    coef, *_ = np.linalg.lstsq(A, y, rcond=None)
    return coef


def backtest(panel: pd.DataFrame) -> pd.DataFrame:
    d = panel[["pib"] + PREDICTORES].dropna().copy()
    d["ingenuo"] = d["pib"].shift(1)
    d = d.dropna()

    trimestres = list(d.index)
    inicio = next(i for i, t in enumerate(trimestres) if t >= INICIO_PRUEBA)

    filas = []
    for i in range(inicio, len(trimestres)):
        historia = d.iloc[:i]                    # sólo el pasado
        actual = d.iloc[i]
        coef = ajustar(historia[PREDICTORES].to_numpy(float),
                       historia["pib"].to_numpy(float))
        x = actual[PREDICTORES].to_numpy(float)
        filas.append({
            "trimestre": trimestres[i],
            "observado": actual["pib"],
            "nowcast": float(coef[0] + coef[1:] @ x),
            "ingenuo": actual["ingenuo"],
            "promedio": float(historia["pib"].mean()),
        })
    return pd.DataFrame(filas).set_index("trimestre")


def diagnostico(panel: pd.DataFrame) -> None:
    """Regresión sobre toda la muestra, con errores estándar y t."""
    d = panel[["pib"] + PREDICTORES].dropna()
    A = np.column_stack([np.ones(len(d)), d[PREDICTORES].to_numpy(float)])
    y = d["pib"].to_numpy(float)
    coef, *_ = np.linalg.lstsq(A, y, rcond=None)
    residuo = y - A @ coef
    n, k = len(y), A.shape[1]
    r2 = 1 - (residuo ** 2).sum() / ((y - y.mean()) ** 2).sum()
    ee = np.sqrt((residuo ** 2).sum() / (n - k) * np.diag(np.linalg.inv(A.T @ A)))

    print(f"\n  n = {n} trimestres    R² (dentro de muestra) = {r2:.3f}")
    print(f"  {'variable':<28}{'coef.':>9}{'e.e.':>9}{'t':>8}")
    for nombre, b, s in zip(["intercepto"] + PREDICTORES, coef, ee):
        marca = "  significativa" if abs(b / s) > 2 else ""
        print(f"  {nombre:<28}{b:>9.4f}{s:>9.4f}{b / s:>8.2f}{marca}")


def rmse(a, b) -> float:
    return float(np.sqrt(((a - b) ** 2).mean()))


def comparar(res: pd.DataFrame, etiqueta: str) -> None:
    print(f"\n  {etiqueta}  (n = {len(res)} trimestres)")
    base = rmse(res["nowcast"], res["observado"])
    print(f"    {'':<26}{'RMSE':>8}{'MAE':>8}{'mejora':>12}")
    print(f"    {'NOWCAST':<26}{base:>8.2f}"
          f"{(res['nowcast'] - res['observado']).abs().mean():>8.2f}"
          f"{'—':>12}")
    for nombre, col in [("repetir el trimestre previo", "ingenuo"),
                        ("promedio histórico", "promedio")]:
        r = rmse(res[col], res["observado"])
        mae = (res[col] - res["observado"]).abs().mean()
        print(f"    {nombre:<26}{r:>8.2f}{mae:>8.2f}"
              f"{(1 - base / r) * 100:>+11.1f}%")


# -------------------------------------------------------------- gráfico ----
def _trazar(ax, datos, mostrar_leyenda: bool) -> None:
    x = np.arange(len(datos))
    ax.axhline(0, color=GRIS, lw=1, zorder=1)
    ax.plot(x, datos["observado"], color=AZUL, lw=2.2, zorder=3,
            marker="o", ms=4.5, markeredgecolor="white", markeredgewidth=0.8,
            label="PIB observado")
    ax.plot(x, datos["nowcast"], color=NARANJA, lw=2.2, ls="--", zorder=2,
            marker="s", ms=4, markeredgecolor="white", markeredgewidth=0.8,
            label="Nowcast (fuera de muestra)")

    paso = max(1, len(datos) // 12)
    ax.set_xticks(x[::paso])
    ax.set_xticklabels(datos.index[::paso], rotation=45, ha="right", fontsize=8.2)
    ax.tick_params(colors=TINTA, labelsize=8.2)
    ax.grid(axis="y", color="#EAEAEA", lw=0.9)
    ax.set_axisbelow(True)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    for lado in ("left", "bottom"):
        ax.spines[lado].set_color(GRIS)
    if mostrar_leyenda:
        ax.legend(frameon=False, fontsize=9.5, loc="lower left", ncols=2)


def graficar(res: pd.DataFrame) -> Path:
    GRAFICOS.mkdir(parents=True, exist_ok=True)
    destino = GRAFICOS / "nowcast_pib.png"

    normal = res[res.index >= "2021Q1"]

    fig, (arriba, abajo) = plt.subplots(
        2, 1, figsize=(11, 8), dpi=160,
        gridspec_kw={"height_ratios": [1, 1], "hspace": 0.55})
    fig.patch.set_facecolor("white")
    for ax in (arriba, abajo):
        ax.set_facecolor("white")

    fig.suptitle("Nowcasting del PIB trimestral de Costa Rica",
                 fontsize=14, fontweight="bold", color=TINTA, x=0.008,
                 ha="left", y=0.985)
    fig.text(0.008, 0.945,
             "Cada punto se estima usando únicamente información previa a ese "
             "trimestre.  Fuente: OCDE, indicadores de corto plazo.",
             fontsize=8.8, color="#6B6B6B", ha="left")

    _trazar(arriba, res, mostrar_leyenda=True)
    arriba.set_title("Muestra completa: la caída de 2020 no se anticipó",
                     fontsize=10.5, color=TINTA, loc="left", pad=8)
    arriba.set_ylabel("Variación trimestral (%)", fontsize=9.5, color=TINTA)
    arriba.annotate("−8,3 %\nno anticipado", xy=(21, -8.3), xytext=(24, -6.2),
                    fontsize=8.5, color="#8A5A00",
                    arrowprops=dict(arrowstyle="->", color="#8A5A00", lw=1.1))

    _trazar(abajo, normal, mostrar_leyenda=False)
    abajo.set_title("Desde 2021: el nowcast sigue el nivel, pero suaviza los "
                    "saltos trimestrales", fontsize=10.5, color=TINTA,
                    loc="left", pad=8)
    abajo.set_ylabel("Variación trimestral (%)", fontsize=9.5, color=TINTA)

    fig.savefig(destino, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return destino


# ------------------------------------------------------------------ main ----
def main() -> None:
    panel = construir_panel()
    res = backtest(panel)

    print("=" * 74)
    print("DIAGNÓSTICO DE LA REGRESIÓN")
    print("=" * 74)
    diagnostico(panel)

    print()
    print("=" * 74)
    print("DESEMPEÑO FUERA DE MUESTRA, CONTRA DOS REFERENTES")
    print("=" * 74)
    comparar(res, "muestra completa 2015–2026")
    comparar(res[~res.index.str.startswith("2020")], "excluyendo 2020")

    print()
    print("=" * 74)
    print("ÚLTIMOS 8 TRIMESTRES")
    print("=" * 74)
    print(res.tail(8).round(2).to_string())

    destino = graficar(res)
    res.round(3).to_csv(AQUI / "resultados_nowcast.csv")
    print(f"\ngráfico:     {destino.relative_to(AQUI)}")
    print("resultados:  resultados_nowcast.csv")


if __name__ == "__main__":
    main()
