"""
SEMANA 1 - TAREA 1: tu primer SELECT.

Genera un dataset inmobiliario sintetico (a proposito: sucio, como los reales)
y corre tus primeras tres queries en DuckDB.

Correlo con:   python empezar_aqui.py

NOTA: los datos son SINTETICOS, generados aqui mismo. Sirven para practicar SQL.
Para el Proyecto 1 vas a usar datos publicos reales -- nunca presentes datos
inventados como si fueran reales en tu portafolio.
"""

from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

AQUI = Path(__file__).parent
CSV = AQUI / "datos" / "viviendas.csv"

COLONIAS = [
    ("Centro", 62000, 0.9), ("Del Valle", 78000, 1.2), ("Roma Norte", 95000, 1.5),
    ("Condesa", 98000, 1.6), ("Napoles", 71000, 1.1), ("Escandon", 66000, 1.0),
    ("Portales", 54000, 0.8), ("Doctores", 41000, 0.7), ("Narvarte", 68000, 1.0),
    ("Polanco", 128000, 2.1),
]


def generar_datos(n=10_000, semilla=42):
    """Construye el CSV con imperfecciones deliberadas: nulos, duplicados,
    texto inconsistente y algunos outliers absurdos."""
    rng = np.random.default_rng(semilla)

    idx = rng.integers(0, len(COLONIAS), n)
    nombres = np.array([c[0] for c in COLONIAS])
    precio_m2_base = np.array([c[1] for c in COLONIAS])
    factor = np.array([c[2] for c in COLONIAS])

    m2 = np.round(rng.gamma(shape=6.0, scale=13.0, size=n) + 35, 1)
    recamaras = np.clip(np.round(m2 / 42 + rng.normal(0, 0.6, n)), 1, 5).astype(int)
    banos = np.clip(np.round(recamaras * 0.7 + rng.normal(0, 0.4, n)), 1, 4).astype(int)
    antiguedad = rng.integers(0, 45, n)
    km_metro = np.round(np.abs(rng.gamma(2.0, 0.9, n)), 2)

    # El precio depende de fundamentales + ruido. Hay senal real que encontrar.
    precio_m2 = (
        precio_m2_base[idx]
        * (1 - antiguedad * 0.006)
        * (1 - np.clip(km_metro, 0, 5) * 0.035)
        * (1 + rng.normal(0, 0.12, n))
    )
    precio = np.round(precio_m2 * m2, -3)

    df = pd.DataFrame({
        "id": np.arange(1, n + 1),
        "colonia": nombres[idx],
        "metros_cuadrados": m2,
        "recamaras": recamaras,
        "banos": banos,
        "antiguedad_anios": antiguedad,
        "km_al_metro": km_metro,
        "precio_mxn": precio,
        "tipo": rng.choice(["departamento", "casa", "loft"], n, p=[0.68, 0.27, 0.05]),
        "fecha_publicacion": pd.to_datetime("2025-01-01")
        + pd.to_timedelta(rng.integers(0, 610, n), unit="D"),
    })

    # --- suciedad deliberada, para que practiques limpieza ---
    df.loc[rng.choice(n, 420, replace=False), "precio_mxn"] = np.nan
    df.loc[rng.choice(n, 260, replace=False), "km_al_metro"] = np.nan

    ruido = rng.choice(n, 500, replace=False)
    df.loc[ruido, "colonia"] = df.loc[ruido, "colonia"].str.upper()
    ruido2 = rng.choice(n, 300, replace=False)
    df.loc[ruido2, "colonia"] = "  " + df.loc[ruido2, "colonia"] + " "

    df.loc[rng.choice(n, 25, replace=False), "precio_mxn"] *= 100  # outliers absurdos

    df = pd.concat([df, df.sample(180, random_state=1)], ignore_index=True)  # duplicados

    CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(CSV, index=False, encoding="utf-8")
    return df


def main():
    if not CSV.exists():
        print("Generando dataset...")
        generar_datos()
    print(f"Dataset: {CSV}\n")

    con = duckdb.connect()
    con.execute(f"CREATE VIEW viviendas AS SELECT * FROM read_csv_auto('{CSV.as_posix()}')")

    print("=" * 68)
    print("QUERY 1 - Cuantos registros hay, y cuantos vienen rotos?")
    print("=" * 68)
    print(con.execute("""
        SELECT
            COUNT(*)                                        AS filas_totales,
            COUNT(DISTINCT id)                              AS ids_unicos,
            COUNT(*) - COUNT(precio_mxn)                    AS precios_nulos,
            COUNT(DISTINCT TRIM(LOWER(colonia)))            AS colonias_reales,
            COUNT(DISTINCT colonia)                         AS colonias_como_estan
        FROM viviendas
    """).df().to_string(index=False))
    print("\n  ^ Fijate: 'colonias_como_estan' es mayor por mayusculas y espacios.")
    print("    Ese es el trabajo real de un analista.\n")

    print("=" * 68)
    print("QUERY 2 - Precio por m2 por colonia (limpiando sobre la marcha)")
    print("=" * 68)
    print(con.execute("""
        SELECT
            TRIM(LOWER(colonia))                            AS colonia,
            COUNT(*)                                        AS propiedades,
            ROUND(MEDIAN(precio_mxn / metros_cuadrados))    AS precio_m2_mediana,
            ROUND(AVG(precio_mxn / metros_cuadrados))       AS precio_m2_promedio
        FROM viviendas
        WHERE precio_mxn IS NOT NULL
          AND precio_mxn < 40000000          -- descarta los outliers absurdos
        GROUP BY 1
        ORDER BY precio_m2_mediana DESC
    """).df().to_string(index=False))
    print("\n  ^ Mediana y promedio salen casi identicos... porque el WHERE ya")
    print("    filtro los outliers. PRUEBA ESTO: borra la linea del WHERE que")
    print("    dice 'precio_mxn < 40000000' y vuelve a correrlo. El promedio se")
    print("    dispara y la mediana casi no se mueve. Por eso en precios se")
    print("    reporta mediana: 25 registros basura de 10,180 rompen un promedio.\n")

    print("=" * 68)
    print("QUERY 3 - Cuanto cuesta estar lejos del metro?")
    print("=" * 68)
    print(con.execute("""
        SELECT
            CASE
                WHEN km_al_metro < 0.5 THEN 'a. menos de 500 m'
                WHEN km_al_metro < 1.0 THEN 'b. 500 m a 1 km'
                WHEN km_al_metro < 2.0 THEN 'c. 1 a 2 km'
                ELSE                       'd. mas de 2 km'
            END                                             AS distancia,
            COUNT(*)                                        AS propiedades,
            ROUND(MEDIAN(precio_mxn / metros_cuadrados))    AS precio_m2_mediana
        FROM viviendas
        WHERE precio_mxn IS NOT NULL
          AND km_al_metro IS NOT NULL
          AND precio_mxn < 40000000
        GROUP BY 1
        ORDER BY 1
    """).df().to_string(index=False))
    print("\n  ^ Esto ya es un HALLAZGO, no una tabla. Asi se escribe un README.\n")

    print("=" * 68)
    print("TU TURNO")
    print("=" * 68)
    print("""
  Abre queries/ y escribe las tuyas. Arranca con estas cinco:

   1. Las 10 propiedades mas caras por m2, con su colonia y antiguedad.
   2. Precio mediano por numero de recamaras. Sube siempre?
   3. Que colonia tiene la mayor DISPERSION de precios? (pista: STDDEV)
   4. Cuantas publicaciones hubo por mes? (pista: DATE_TRUNC)
   5. Compara casa contra departamento en el mismo rango de m2.

  Regla de la semana 1: 50 queries propias y commit todos los dias.
""")


if __name__ == "__main__":
    main()
