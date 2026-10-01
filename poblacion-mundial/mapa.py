"""Vista previa estática de los dos mapas del reporte de Power BI.

Genera:
  graficos/mapa_crecimiento.png  coropleta del cambio anual de población
  graficos/mapa_poblacion.png    burbujas proporcionales a la población

Corre después de preparar_datos.py (usa su CSV y el GeoJSON que descarga).
"""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from matplotlib.patches import Polygon

DIR = Path(__file__).resolve().parent
DATOS = DIR / "datos" / "poblacion_mundial_2026.csv"
GEOJSON = DIR / "datos" / "ne_50m_admin_0_countries.geojson"
GRAFICOS = DIR / "graficos"

SUPERFICIE = "#fcfcfb"
TINTA = "#0b0b0b"
TINTA_2 = "#52514e"
SIN_DATO = "#d9d8d4"
AZUL = "#2a78d6"
# Divergente: azul = la población se achica, rojo = crece, gris = sin cambio.
DIVERGENTE = LinearSegmentedColormap.from_list(
    "cambio", ["#104281", "#5598e7", "#cde2fb", "#f0efec",
               "#f6c4c3", "#e34948", "#9c2423"]
)


def codigo(p):
    return p["ISO_A3_EH"] if p["ISO_A3_EH"] != "-99" else p["ADM0_A3"]


def anillos(geometria):
    if geometria["type"] == "Polygon":
        return [geometria["coordinates"][0]]
    return [poly[0] for poly in geometria["coordinates"]]


def lienzo(titulo, subtitulo):
    fig, ax = plt.subplots(figsize=(14, 6.9), facecolor=SUPERFICIE)
    ax.set_facecolor(SUPERFICIE)
    ax.set_xlim(-170, 190)
    ax.set_ylim(-58, 84)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.text(0.04, 0.95, titulo, fontsize=17, weight="bold", color=TINTA)
    fig.text(0.04, 0.915, subtitulo, fontsize=11, color=TINTA_2)
    fig.text(0.04, 0.03, "Fuente: Worldometer (población 2026), límites de "
             "Natural Earth 1:50m.", fontsize=8.5, color=TINTA_2)
    return fig, ax


def dibujar_paises(ax, feats, color_de):
    for f in feats:
        p = f["properties"]
        if p["CONTINENT"] == "Antarctica":
            continue
        for anillo in anillos(f["geometry"]):
            ax.add_patch(Polygon(anillo, closed=True, facecolor=color_de(codigo(p)),
                                 edgecolor=SUPERFICIE, linewidth=0.35))


def mapa_crecimiento(df, feats):
    cambio = df.set_index("ISO3")["YearlyChangePct"]
    norma = TwoSlopeNorm(vmin=-0.02, vcenter=0, vmax=0.035)
    fig, ax = lienzo(
        "La mitad del crecimiento mundial ocurre en África",
        "Cambio anual de la población, 2025 → 2026. "
        "Azul: se achica · rojo: crece.",
    )
    dibujar_paises(ax, feats,
                   lambda iso: DIVERGENTE(norma(cambio[iso])) if iso in cambio else SIN_DATO)

    barra = fig.colorbar(plt.cm.ScalarMappable(norm=norma, cmap=DIVERGENTE), ax=ax,
                         orientation="horizontal", fraction=0.035, pad=0.02,
                         aspect=45, shrink=0.45)
    barra.set_ticks([-0.02, -0.01, 0, 0.01, 0.02, 0.03])
    barra.set_ticklabels(["−2 %", "−1 %", "0", "+1 %", "+2 %", "+3 %"])
    barra.outline.set_visible(False)
    barra.ax.tick_params(labelsize=9, colors=TINTA_2, length=0)

    for pais, dx, dy in [("Niger", 2, 12), ("DR Congo", -26, -8), ("Japan", 8, 4),
                         ("China", 6, -16), ("Bulgaria", -6, 14)]:
        f = df[df["Country"] == pais].iloc[0]
        valor = f"{f['YearlyChangePct']:+.2%}".replace(".", ",").replace("-", "\u2212")
        ax.annotate(f"{pais} {valor}",
                    (f["Longitude"], f["Latitude"]),
                    (f["Longitude"] + dx, f["Latitude"] + dy),
                    fontsize=9, color=TINTA, ha="right" if dx < 0 else "left",
                    arrowprops=dict(arrowstyle="-", color=TINTA_2, lw=0.6))

    fig.savefig(GRAFICOS / "mapa_crecimiento.png", dpi=150, facecolor=SUPERFICIE,
                bbox_inches="tight")
    plt.close(fig)


def mapa_poblacion(df, feats):
    fig, ax = lienzo(
        "Dos países concentran el 35 % de la humanidad",
        "Población 2026. El área de cada círculo es proporcional a la población.",
    )
    dibujar_paises(ax, feats, lambda iso: "#e9e8e4")

    escala = 2600 / df["Population2026"].max()  # India = 2600 pt²
    orden = df.sort_values("Population2026", ascending=False)
    ax.scatter(orden["Longitude"], orden["Latitude"],
               s=orden["Population2026"] * escala, color=AZUL, alpha=0.78,
               edgecolor=SUPERFICIE, linewidth=1.2, zorder=3)

    # Desplazamiento de cada etiqueta (grados) para que no se pisen en Asia.
    etiquetas = {"India": (-8, -25), "China": (26, 14), "United States": (0, 13),
                 "Indonesia": (0, -14), "Pakistan": (-22, 12), "Nigeria": (-20, -12),
                 "Brazil": (12, -14), "Bangladesh": (22, -14)}
    for _, f in orden.head(len(etiquetas)).iterrows():
        dx, dy = etiquetas[f["Country"]]
        millones = f"{f['Population2026'] / 1e6:,.0f}".replace(",", ".")
        ax.annotate(f"{f['Country']}\n{millones} M", (f["Longitude"], f["Latitude"]),
                    (f["Longitude"] + dx, f["Latitude"] + dy), ha="center", va="center",
                    fontsize=8.5, color=TINTA, weight="bold", zorder=4,
                    arrowprops=dict(arrowstyle="-", color=TINTA_2, lw=0.6))

    for m in (10, 100, 1000):
        ax.scatter([], [], s=m * 1e6 * escala, color=AZUL, alpha=0.78,
                   edgecolor=SUPERFICIE, label=f"{m:,} M".replace(",", "."))
    ax.legend(loc="lower left", frameon=False, labelspacing=2.6, borderpad=1.5, handletextpad=2.5,
              title="Población", title_fontsize=9, fontsize=9, labelcolor=TINTA_2)

    fig.savefig(GRAFICOS / "mapa_poblacion.png", dpi=150, facecolor=SUPERFICIE,
                bbox_inches="tight")
    plt.close(fig)


def main():
    df = pd.read_csv(DATOS)
    feats = json.loads(GEOJSON.read_text(encoding="utf-8"))["features"]
    GRAFICOS.mkdir(exist_ok=True)
    mapa_crecimiento(df, feats)
    mapa_poblacion(df, feats)
    print("Mapas -> graficos/")


if __name__ == "__main__":
    main()
