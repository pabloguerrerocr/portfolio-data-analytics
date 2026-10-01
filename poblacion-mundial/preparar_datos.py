"""Limpia la tabla de población 2026 y la deja lista para el mapa de Power BI.

Entrada:  datos/worldometer_2026.tsv  (tabla de Worldometer, copiada tal cual)
Salida:   datos/poblacion_mundial_2026.csv

Agrega a cada país su código ISO3, un punto de etiqueta (latitud y longitud),
continente y subregión, tomados de Natural Earth. Con eso Power BI ubica cada
país sin adivinar por el nombre, que es donde suelen fallar los mapas.

Antes de escribir la salida verifica que la tabla sea coherente consigo misma:
si una verificación falla, el script se detiene en vez de producir un mapa
bonito con datos rotos.
"""

import json
from pathlib import Path

import pandas as pd
import requests

DIR = Path(__file__).resolve().parent
ENTRADA = DIR / "datos" / "worldometer_2026.tsv"
SALIDA = DIR / "datos" / "poblacion_mundial_2026.csv"
GEOJSON = DIR / "datos" / "ne_50m_admin_0_countries.geojson"
URL_GEOJSON = (
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/"
    "master/geojson/ne_50m_admin_0_countries.geojson"
)

COLUMNAS = {
    "#": "Rank",
    "Country (or dependency)": "Country",
    "Population 2026": "Population2026",
    "Yearly Change": "YearlyChangePct",
    "Net Change": "NetChange",
    "Density (P/Km²)": "DensityPerKm2",
    "Land Area (Km²)": "LandAreaKm2",
    "Migrants (net)": "NetMigrants",
    "Fert. Rate": "FertilityRate",
    "Median Age": "MedianAge",
    "Urban Pop %": "UrbanPopPct",
    "World Share": "WorldSharePct",
}

# Nombres de Worldometer que Natural Earth escribe distinto.
ALIAS = {
    "DR Congo": "COD",
    "Czech Republic (Czechia)": "CZE",
    "State of Palestine": "PSX",
    "Sao Tome & Principe": "STP",
    "Turks and Caicos": "TCA",
    "St. Vincent & Grenadines": "VCT",
    "U.S. Virgin Islands": "VIR",
    "Saint Kitts & Nevis": "KNA",
    "Saint Pierre & Miquelon": "SPM",
    "Wallis & Futuna": "WLF",
}

# Territorios que Natural Earth 1:50m no separa (los departamentos de
# ultramar franceses van dentro de Francia) o no incluye. Punto de etiqueta
# aproximado al centro del territorio habitado.
MANUALES = {
    "French Guiana": ("GUF", 4.0, -53.0, "South America", "South America"),
    "Réunion": ("REU", -21.1, 55.5, "Africa", "Eastern Africa"),
    "Guadeloupe": ("GLP", 16.2, -61.6, "North America", "Caribbean"),
    "Martinique": ("MTQ", 14.6, -61.0, "North America", "Caribbean"),
    "Mayotte": ("MYT", -12.8, 45.15, "Africa", "Eastern Africa"),
    "Caribbean Netherlands": ("BES", 12.2, -68.26, "North America", "Caribbean"),
    "Tokelau": ("TKL", -9.2, -171.8, "Oceania", "Polynesia"),
    "Gibraltar": ("GIB", 36.14, -5.35, "Europe", "Southern Europe"),
}


def numero(serie):
    """'1,234' / '−0.42%' / '–' -> float (porcentajes como fracción)."""
    s = (
        serie.astype(str)
        .str.strip()
        .str.replace("−", "-", regex=False)  # signo menos tipográfico
        .str.replace(",", "", regex=False)
        .replace({"–": None, "N.A.": None, "": None})
    )
    es_pct = s.str.endswith("%", na=False)
    valores = pd.to_numeric(s.str.rstrip("%"), errors="raise")
    return valores.where(~es_pct, valores / 100)


def cargar_geografia():
    if not GEOJSON.exists():
        print(f"Descargando Natural Earth -> {GEOJSON.name}")
        r = requests.get(URL_GEOJSON, timeout=60)
        r.raise_for_status()
        GEOJSON.write_bytes(r.content)
    feats = json.loads(GEOJSON.read_text(encoding="utf-8"))["features"]

    por_codigo, por_nombre = {}, {}
    for f in feats:
        p = f["properties"]
        iso = p["ISO_A3_EH"] if p["ISO_A3_EH"] != "-99" else p["ADM0_A3"]
        info = (iso, p["LABEL_Y"], p["LABEL_X"], p["CONTINENT"], p["SUBREGION"])
        por_codigo[p["ADM0_A3"]] = info
        for k in ("NAME", "NAME_LONG", "ADMIN", "NAME_EN", "GEOUNIT", "BRK_NAME",
                  "FORMAL_EN", "NAME_ALT", "NAME_SORT"):
            if p.get(k):
                por_nombre[p[k].lower()] = info
    return por_codigo, por_nombre


def ubicar(pais, por_codigo, por_nombre):
    if pais in MANUALES:
        return MANUALES[pais]
    if pais in ALIAS:
        return por_codigo[ALIAS[pais]]
    return por_nombre[pais.lower()]


def verificar(df):
    """Chequeos de coherencia interna. Devuelve una lista de textos."""
    reporte = []

    assert df["Country"].is_unique, "países duplicados"
    assert df["Rank"].is_unique and set(df["Rank"]) == set(range(1, len(df) + 1)), \
        "el ranking no es 1..N"
    assert df["ISO3"].is_unique, "códigos ISO3 duplicados"

    ranking = df.sort_values("Population2026", ascending=False)["Rank"].tolist()
    assert ranking == list(range(1, len(df) + 1)), "el ranking no sigue a la población"
    reporte.append("Ranking = orden por población: OK")

    total = df["Population2026"].sum()
    cuota = df["WorldSharePct"].sum()
    assert abs(cuota - 1) < 0.01, f"las cuotas suman {cuota:.4f}"
    reporte.append(f"Población total: {total:,.0f} | cuotas suman {cuota:.2%}")

    # Cambio anual reportado vs. el que implican población y cambio neto.
    base = df["Population2026"] - df["NetChange"]
    implicito = df["NetChange"] / base
    dif = (implicito - df["YearlyChangePct"]).abs()
    assert (dif < 0.0001).all(), df.loc[dif >= 0.0001, "Country"].tolist()
    reporte.append(f"Cambio anual reproducible: máx. diferencia {dif.max():.5%}")

    # Densidad = población / superficie. La fuente redondea ambas a entero, así
    # que se acepta cualquier densidad compatible con superficie ±0,5 km²
    # (Mónaco figura con 1 km² y una densidad que implica 1,49 km²).
    a = df[df["LandAreaKm2"] > 0]
    minimo = a["Population2026"] / (a["LandAreaKm2"] + 0.5) - 1
    maximo = a["Population2026"] / (a["LandAreaKm2"] - 0.5) + 1
    ok = a["DensityPerKm2"].between(minimo, maximo)
    assert ok.all(), a.loc[~ok, "Country"].tolist()
    reporte.append("Densidad = población / superficie: OK (dentro del redondeo)")
    con_area = df["LandAreaKm2"] > 0

    # La migración mundial tiene que sumar casi cero: lo que sale de un país
    # entra a otro.
    migracion = df["NetMigrants"].sum()
    assert abs(migracion) < 0.001 * df["NetChange"].sum(), f"migración suma {migracion}"
    reporte.append(f"Migración neta mundial: {migracion:+,} (≈ 0, como debe ser)")

    sin_area = df.loc[~con_area, "Country"].tolist()
    reporte.append(f"Superficie 0 km² en la fuente: {', '.join(sin_area)}")

    sin_urb = df["UrbanPopPct"].isna().sum()
    reporte.append(f"Sin dato de población urbana: {sin_urb} países (quedan vacíos)")
    return reporte


def main():
    df = pd.read_csv(ENTRADA, sep="\t", dtype=str).rename(columns=COLUMNAS)
    for col in df.columns.drop("Country"):
        df[col] = numero(df[col])
    enteros = ["Rank", "Population2026", "NetChange", "DensityPerKm2",
               "LandAreaKm2", "NetMigrants"]
    df[enteros] = df[enteros].astype("int64")

    por_codigo, por_nombre = cargar_geografia()
    geo = [ubicar(p, por_codigo, por_nombre) for p in df["Country"]]
    df[["ISO3", "Latitude", "Longitude", "Continent", "Subregion"]] = pd.DataFrame(
        geo, index=df.index
    )

    # Natural Earth pone a las islas oceánicas en "Seven seas"; se las asigna
    # al continente de su subregión (Mauricio, Maldivas, Seychelles, Santa Elena).
    mar = df["Continent"].str.startswith("Seven seas")
    df.loc[mar, "Continent"] = df.loc[mar, "Subregion"].str.split().str[-1]

    # Columnas derivadas que el reporte usa directamente.
    df["Population2025"] = df["Population2026"] - df["NetChange"]
    df["NaturalIncrease"] = df["NetChange"] - df["NetMigrants"]
    df["GrowthBand"] = pd.cut(
        df["YearlyChangePct"],
        bins=[-1, 0, 0.01, 0.02, 1],
        labels=["Shrinking", "0-1%", "1-2%", "2%+"],
        right=False,
    )

    for linea in verificar(df):
        print(linea)

    df = df.sort_values("Rank").round(
        {"Latitude": 4, "Longitude": 4, "YearlyChangePct": 6, "UrbanPopPct": 6}
    )
    # Sin notación científica: Power BI en configuración regional española
    # lee mal "6.1e-08".
    df["WorldSharePct"] = df["WorldSharePct"].map(lambda x: f"{x:.10f}".rstrip("0"))
    df.to_csv(SALIDA, index=False, encoding="utf-8")
    print(f"\n{len(df)} países -> {SALIDA.relative_to(DIR)}")


if __name__ == "__main__":
    main()
