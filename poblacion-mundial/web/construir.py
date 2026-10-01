"""Arma web/index.html: el atlas interactivo con datos y mapa incrustados.

Corre después de preparar_datos.py. Descarga los límites de Natural Earth
1:110m (no se versionan), los simplifica y los mete en la página junto con
la tabla limpia, para que index.html funcione abierto sin servidor.
"""

import json
from pathlib import Path

import pandas as pd
import requests

DIR = Path(__file__).resolve().parent
RAIZ = DIR.parent
GEOJSON = RAIZ / "datos" / "ne_110m_admin_0_countries.geojson"
URL = ("https://raw.githubusercontent.com/nvkelso/natural-earth-vector/"
       "master/geojson/ne_110m_admin_0_countries.geojson")
COLUMNAS = ["Rank", "Country", "ISO3", "Continent", "Subregion", "Population2026",
            "YearlyChangePct", "NetChange", "DensityPerKm2", "LandAreaKm2",
            "NetMigrants", "FertilityRate", "MedianAge", "UrbanPopPct",
            "Latitude", "Longitude", "NaturalIncrease"]


def redondear(c):
    """Coordenadas a 2 decimales (~1 km): a escala mundial no se nota."""
    if isinstance(c[0], (int, float)):
        return [round(c[0], 2), round(c[1], 2)]
    return [redondear(x) for x in c]


def geografia():
    if not GEOJSON.exists():
        r = requests.get(URL, timeout=60)
        r.raise_for_status()
        GEOJSON.write_bytes(r.content)
    feats = []
    for f in json.loads(GEOJSON.read_text(encoding="utf-8"))["features"]:
        p = f["properties"]
        if p["CONTINENT"] == "Antarctica":
            continue
        iso = p["ISO_A3_EH"] if p["ISO_A3_EH"] != "-99" else p["ADM0_A3"]
        g = f["geometry"]
        feats.append({"type": "Feature", "id": iso, "properties": {},
                      "geometry": {"type": g["type"], "coordinates": redondear(g["coordinates"])}})
    return {"type": "FeatureCollection", "features": feats}


def main():
    df = pd.read_csv(RAIZ / "datos" / "poblacion_mundial_2026.csv")[COLUMNAS]
    filas = df.astype(object).where(df.notna(), None).values.tolist()
    datos = {"cols": COLUMNAS, "rows": filas}

    html = (DIR / "plantilla.html").read_text(encoding="utf-8")
    html = html.replace("/*GEO*/null", json.dumps(geografia(), separators=(",", ":")))
    html = html.replace("/*DATA*/null", json.dumps(datos, separators=(",", ":"), ensure_ascii=False))
    (DIR / "index.html").write_text(html, encoding="utf-8")
    print(f"web/index.html ({len(html) / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
