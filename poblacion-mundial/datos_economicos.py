"""Indicadores económicos por país, en su versión más reciente publicada.

Fuentes (APIs públicas, sin clave):
  - Banco Mundial, World Development Indicators: el último año con dato de
    cada país (suele ir 1-2 años atrás).
  - FMI, World Economic Outlook (DataMapper): estimaciones del año en curso y
    proyecciones, la cifra más actual que existe para crecimiento e inflación.

Salida: datos/economia.csv, una fila por país (ISO3), con el AÑO de cada
indicador al lado del valor. Un dato de 2019 y uno de 2025 no valen lo mismo,
y el reporte tiene que poder decirlo.

Corre después de preparar_datos.py: se une por ISO3 a la tabla de población.
"""

import json
import time
from pathlib import Path

import pandas as pd
import requests

DIR = Path(__file__).resolve().parent
CACHE = DIR / "datos" / "cache_economia"
SALIDA = DIR / "datos" / "economia.csv"
POBLACION = DIR / "datos" / "poblacion_mundial_2026.csv"

AÑO_ACTUAL = 2026

# Banco Mundial: código -> (columna, descripción)
WDI = {
    "NY.GDP.PCAP.PP.KD": ("GdpPcPpp", "PIB per cápita, PPA (USD internacionales constantes de 2021)"),
    "NY.GDP.PCAP.CD": ("GdpPcUsd", "PIB per cápita (USD corrientes)"),
    "SP.POP.1564.TO.ZS": ("WorkingAgePct", "Población de 15 a 64 años (% del total)"),
    "SP.POP.DPND": ("DependencyRatio", "Dependientes por cada 100 personas en edad de trabajar"),
    "SP.DYN.LE00.IN": ("LifeExpectancy", "Esperanza de vida al nacer (años)"),
    "BX.TRF.PWKR.DT.GD.ZS": ("RemittancesPctGdp", "Remesas recibidas (% del PIB)"),
    "SL.UEM.1524.ZS": ("YouthUnemployment", "Desempleo juvenil, 15-24 años (% de la fuerza laboral, OIT)"),
    "SI.POV.GINI": ("Gini", "Índice de Gini"),
}

# FMI WEO: código -> (columna, descripción)
WEO = {
    "NGDP_RPCH": ("GdpGrowth", "Crecimiento del PIB real (%)"),
    "PCPIPCH": ("Inflation", "Inflación, promedio anual (%)"),
    "LUR": ("Unemployment", "Desempleo (% de la fuerza laboral)"),
    "GGXWDG_NGDP": ("PublicDebtPctGdp", "Deuda bruta del gobierno general (% del PIB)"),
}


def bajar(url, nombre):
    """GET con caché en disco y reintentos: las dos APIs fallan de vez en cuando."""
    archivo = CACHE / nombre
    if archivo.exists():
        return json.loads(archivo.read_text(encoding="utf-8"))
    for intento in range(4):
        try:
            r = requests.get(url, timeout=60)
            r.raise_for_status()
            datos = r.json()
            CACHE.mkdir(parents=True, exist_ok=True)
            archivo.write_text(json.dumps(datos), encoding="utf-8")
            return datos
        except requests.RequestException as e:
            if intento == 3:
                raise SystemExit(f"No se pudo bajar {url}: {e}")
            time.sleep(2 ** (intento + 1))


def banco_mundial(codigo):
    """Último valor no vacío de cada país en los últimos 10 años, con su año."""
    url = (f"https://api.worldbank.org/v2/country/all/indicator/{codigo}"
           f"?format=json&per_page=20000&date={AÑO_ACTUAL - 10}:{AÑO_ACTUAL}")
    meta, filas = bajar(url, f"wdi_{codigo}.json")[:2]
    assert meta["pages"] == 1, f"{codigo}: la respuesta viene paginada, subir per_page"
    df = pd.DataFrame(
        {"ISO3": f["countryiso3code"], "year": int(f["date"]), "value": f["value"]}
        for f in filas or [] if f["value"] is not None and f["countryiso3code"]
    )
    return df.sort_values("year").groupby("ISO3").last()


def grupos_de_ingreso():
    datos = bajar("https://api.worldbank.org/v2/country?format=json&per_page=400",
                  "wdi_paises.json")
    return pd.DataFrame(
        {"ISO3": p["id"], "IncomeGroup": p["incomeLevel"]["value"]}
        for p in datos[1] if p["region"]["value"] != "Aggregates"
    ).set_index("ISO3")


def fmi(codigo):
    """Valor del año en curso (estimación o proyección del WEO). Si el FMI no
    lo publica para un país, el último año anterior con dato, nunca uno futuro."""
    datos = bajar(f"https://www.imf.org/external/datamapper/api/v1/{codigo}",
                  f"weo_{codigo}.json")
    filas = []
    for iso, por_año in datos["values"][codigo].items():
        años = [int(a) for a, v in por_año.items() if v is not None and int(a) <= AÑO_ACTUAL]
        if años:
            año = max(años)
            filas.append({"ISO3": iso, "year": año, "value": por_año[str(año)]})
    return pd.DataFrame(filas).set_index("ISO3")


def main():
    pob = pd.read_csv(POBLACION)[["ISO3", "Country", "YearlyChangePct"]].set_index("ISO3")
    eco = pd.DataFrame(index=pob.index)

    for codigo, (col, _) in WDI.items():
        s = banco_mundial(codigo)
        eco[col], eco[col + "Year"] = s["value"], s["year"]
    for codigo, (col, _) in WEO.items():
        s = fmi(codigo)
        eco[col], eco[col + "Year"] = s["value"], s["year"]
    eco = eco.join(grupos_de_ingreso())

    # Derivado: crecimiento del ingreso por persona = PIB real - población.
    # Si la población crece más rápido que la economía, cada persona tiene menos.
    # Solo con PIB del mismo año que la población, para no mezclar años.
    mismo_año = eco["GdpGrowthYear"] == AÑO_ACTUAL
    eco["GdpPcGrowth"] = (eco["GdpGrowth"] - pob["YearlyChangePct"] * 100).where(mismo_año)

    # Reporte de cobertura y frescura: qué tanto del mapa queda con dato y de qué año.
    print(f"{'Indicador':<22}{'Países':>8}{'Año más común':>15}{'Rango de años':>15}")
    for col, _ in [*WDI.values(), *WEO.values()]:
        n = eco[col].notna().sum()
        años = eco[col + "Year"].dropna().astype(int)
        moda = años.mode().iat[0] if n else "-"
        rango = f"{años.min()}-{años.max()}" if n else "-"
        print(f"{col:<22}{n:>8}{moda:>15}{rango:>15}")
    print(f"{'IncomeGroup':<22}{eco['IncomeGroup'].notna().sum():>8}")

    eco.round(4).to_csv(SALIDA, encoding="utf-8")
    print(f"\n{len(eco)} países -> datos/{SALIDA.name}")


if __name__ == "__main__":
    main()
