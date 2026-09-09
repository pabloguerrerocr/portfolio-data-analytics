"""
Descarga las series de coyuntura de Costa Rica desde la API pública de la OCDE.

Costa Rica es miembro de la OCDE desde 2021, y la organización publica sus
indicadores de corto plazo (Key Economic Indicators) en un servicio SDMX abierto,
sin llave de acceso. Los datos son los que reporta el propio Banco Central de
Costa Rica a la OCDE.

Salida: datos/cri_kei.csv  (formato largo, una fila por observación)

Uso:  python descargar_datos.py
"""

from pathlib import Path

import pandas as pd
import requests

URL = ("https://sdmx.oecd.org/public/rest/data/"
       "OECD.SDD.STES,DSD_KEI@DF_KEI,4.0/CRI......")
PARAMS = {
    "format": "jsondata",
    "startPeriod": "2000-01",
    "dimensionAtObservation": "AllDimensions",
}
CABECERAS = {"User-Agent": "Mozilla/5.0"}

AQUI = Path(__file__).parent
SALIDA = AQUI / "datos" / "cri_kei.csv"


def descargar() -> pd.DataFrame:
    print("Consultando la API de la OCDE...")
    r = requests.get(URL, params=PARAMS, timeout=120, headers=CABECERAS)
    r.raise_for_status()
    print(f"  {len(r.content):,} bytes recibidos")

    d = r.json()
    estructura = d["data"]["structures"][0]
    dimensiones = estructura["dimensions"]["observation"]

    # Catálogo de códigos por dimensión, en el mismo orden que la clave.
    catalogo = {
        dim["id"]: [(v["id"], v.get("name", "")) for v in dim["values"]]
        for dim in dimensiones
    }
    orden = [dim["id"] for dim in dimensiones]

    filas = []
    for clave, valor in d["data"]["dataSets"][0]["observations"].items():
        indices = [int(x) for x in clave.split(":")]
        registro = {}
        for posicion, dim_id in enumerate(orden):
            codigo, nombre = catalogo[dim_id][indices[posicion]]
            registro[dim_id] = codigo
            if dim_id == "MEASURE":
                registro["MEASURE_NOMBRE"] = nombre
        registro["valor"] = valor[0]
        filas.append(registro)

    return pd.DataFrame(filas)


def main() -> None:
    df = descargar()
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(SALIDA, index=False, encoding="utf-8")

    print(f"\n{len(df):,} observaciones guardadas en {SALIDA.name}")
    print("\nCobertura por frecuencia:")
    for freq, etiqueta in [("M", "mensual"), ("Q", "trimestral"), ("A", "anual")]:
        sub = df[df["FREQ"] == freq]
        if not sub.empty:
            print(f"  {etiqueta:<11} {len(sub):>6,} obs  "
                  f"{sub['MEASURE'].nunique():>3} medidas  "
                  f"hasta {sub['TIME_PERIOD'].max()}")


if __name__ == "__main__":
    main()
