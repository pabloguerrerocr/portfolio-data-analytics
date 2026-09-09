"""
PROYECTO 1 — Churn y valor de vida del cliente
Dataset: IBM Telco Customer Churn (7.043 clientes, publico)

Pregunta de negocio:
  De cada segmento de clientes, cuantos meses duran realmente, cuanto valen,
  y donde conviene gastar en retenerlos?

Nota metodologica importante:
  Este dataset es una FOTO en un momento dado -- no tiene fechas de alta, asi
  que no permite una matriz de cohortes mes a mes. Lo correcto aqui es analisis
  de supervivencia: 'tenure' es el tiempo observado y los clientes activos estan
  CENSURADOS por la derecha (sabemos que duraron al menos X meses, no cuanto
  duraran en total). Ignorar la censura subestima la vida del cliente.

Correr con:  python analisis_churn.py
"""

import urllib.request
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # sin ventana grafica

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

AQUI = Path(__file__).parent
CSV = AQUI / "datos" / "telco_churn.csv"
GRAFICOS = AQUI / "graficos"
GRAFICOS.mkdir(exist_ok=True)

FUENTE = ("https://raw.githubusercontent.com/IBM/"
          "telco-customer-churn-on-icp4d/master/data/Telco-Customer-Churn.csv")

HORIZONTE = 72  # meses; es el maximo 'tenure' observado en el dataset


# --------------------------------------------------------------------------
# Kaplan-Meier, implementado a mano
# --------------------------------------------------------------------------
def kaplan_meier(duraciones, eventos):
    """Estimador de Kaplan-Meier.

    duraciones : meses observados por cliente
    eventos    : 1 si el cliente se fue (evento observado), 0 si sigue activo
                 (censurado por la derecha)

    Devuelve (t, S) donde S[i] es la probabilidad de seguir siendo cliente
    despues de t[i] meses.
    """
    df = pd.DataFrame({"t": duraciones, "e": eventos})
    tiempos = np.sort(df.loc[df["e"] == 1, "t"].unique())

    t_out, s_out = [0.0], [1.0]
    s = 1.0
    for t in tiempos:
        en_riesgo = (df["t"] >= t).sum()      # aun observables justo antes de t
        se_fueron = ((df["t"] == t) & (df["e"] == 1)).sum()
        if en_riesgo > 0:
            s *= 1 - se_fueron / en_riesgo
        t_out.append(float(t))
        s_out.append(s)

    return np.array(t_out), np.array(s_out)


def rmst(t, s, horizonte=HORIZONTE):
    """Restricted Mean Survival Time: area bajo la curva de supervivencia.

    Es la vida media esperada del cliente en meses, acotada al horizonte
    observado. A diferencia del promedio simple de 'tenure', esta si toma en
    cuenta la censura.
    """
    t = np.append(t, horizonte)
    s = np.append(s, s[-1])
    t = t[t <= horizonte]
    s = s[: len(t)]
    return float(np.trapezoid(s, t)) if hasattr(np, "trapezoid") else float(np.trapz(s, t))


# --------------------------------------------------------------------------
# Carga y limpieza
# --------------------------------------------------------------------------
def cargar():
    # El CSV no se versiona (ver .gitignore). Si no esta, se descarga: asi
    # cualquiera que clone el repositorio puede reproducir el analisis.
    if not CSV.exists():
        print(f"Descargando datos desde {FUENTE} ...")
        CSV.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(FUENTE, CSV)

    df = pd.read_csv(CSV)

    # TotalCharges viene como texto: los clientes con tenure=0 traen "" (aun no
    # facturados). Se convierte a numerico y se documenta el hueco.
    df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")
    nulos = df["TotalCharges"].isna().sum()

    df["evento"] = (df["Churn"] == "Yes").astype(int)

    print("=" * 72)
    print("LIMPIEZA")
    print("=" * 72)
    print(f"  Filas: {len(df):,}   Columnas: {df.shape[1]}")
    print(f"  TotalCharges no numericos: {nulos} "
          f"(todos con tenure=0, clientes recien dados de alta)")
    print(f"  Duplicados por customerID: {df['customerID'].duplicated().sum()}")
    return df


# --------------------------------------------------------------------------
# Analisis
# --------------------------------------------------------------------------
def main():
    df = cargar()

    tasa = df["evento"].mean()
    print(f"\n  Tasa de churn global: {tasa:.1%}  "
          f"({df['evento'].sum():,} de {len(df):,})")

    # ---- 1. Supervivencia global -----------------------------------------
    print("\n" + "=" * 72)
    print("1. CUANTO DURA UN CLIENTE (Kaplan-Meier)")
    print("=" * 72)

    t, s = kaplan_meier(df["tenure"], df["evento"])
    vida_global = rmst(t, s)

    def sobrevive_a(mes):
        return s[t <= mes][-1]

    print(f"  Sigue activo a los 12 meses: {sobrevive_a(12):.1%}")
    print(f"  Sigue activo a los 24 meses: {sobrevive_a(24):.1%}")
    print(f"  Sigue activo a los 48 meses: {sobrevive_a(48):.1%}")
    print(f"\n  Vida media esperada (RMST, {HORIZONTE} meses): {vida_global:.1f} meses")
    print(f"  Promedio simple de 'tenure':                  {df['tenure'].mean():.1f} meses")
    print("    ^ El promedio simple SUBESTIMA: trata a los clientes activos")
    print("      como si ya se hubieran ido. Por eso se usa RMST.")

    # ---- 2. Supervivencia y LTV por tipo de contrato ---------------------
    print("\n" + "=" * 72)
    print("2. EL CONTRATO LO EXPLICA CASI TODO")
    print("=" * 72)

    filas = []
    for contrato, g in df.groupby("Contract"):
        tc, sc = kaplan_meier(g["tenure"], g["evento"])
        vida = rmst(tc, sc)
        mensual = g["MonthlyCharges"].mean()
        filas.append({
            "contrato": contrato,
            "clientes": len(g),
            "churn": g["evento"].mean(),
            "vida_meses": vida,
            "cuota_mensual": mensual,
            "ltv": vida * mensual,
        })

    res = pd.DataFrame(filas).sort_values("ltv")
    print(res.to_string(index=False, formatters={
        "churn": "{:.1%}".format,
        "vida_meses": "{:.1f}".format,
        "cuota_mensual": "${:.2f}".format,
        "ltv": "${:,.0f}".format,
    }))

    # ---- 3. Otros factores de riesgo -------------------------------------
    print("\n" + "=" * 72)
    print("3. QUE MAS MUEVE LA AGUJA")
    print("=" * 72)

    for col in ["InternetService", "TechSupport", "PaymentMethod"]:
        print(f"\n  -- {col} --")
        g = (df.groupby(col)
               .agg(clientes=("evento", "size"), churn=("evento", "mean"))
               .sort_values("churn", ascending=False))
        print(g.to_string(formatters={"churn": "{:.1%}".format}))

    # ---- 4. Graficos ------------------------------------------------------
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

    ax1.step(t, s * 100, where="post", color="#0E5C4A", linewidth=2)
    ax1.set_title("Supervivencia global del cliente", fontsize=12, fontweight="bold")
    ax1.set_xlabel("Meses como cliente")
    ax1.set_ylabel("% que sigue activo")
    ax1.set_ylim(0, 100)
    ax1.grid(alpha=0.25)

    colores = {"Month-to-month": "#B2551A", "One year": "#3B7EA1", "Two year": "#0E5C4A"}
    for contrato, g in df.groupby("Contract"):
        tc, sc = kaplan_meier(g["tenure"], g["evento"])
        ax2.step(tc, sc * 100, where="post", linewidth=2,
                 label=contrato, color=colores.get(contrato))
    ax2.set_title("Supervivencia por tipo de contrato", fontsize=12, fontweight="bold")
    ax2.set_xlabel("Meses como cliente")
    ax2.set_ylabel("% que sigue activo")
    ax2.set_ylim(0, 100)
    ax2.legend(frameon=False)
    ax2.grid(alpha=0.25)

    plt.tight_layout()
    salida = GRAFICOS / "supervivencia.png"
    plt.savefig(salida, dpi=140, bbox_inches="tight")
    print(f"\n  Grafico guardado: {salida}")

    # ---- 5. Hallazgos cuantificados ---------------------------------------
    print("\n" + "=" * 72)
    print("4. HALLAZGOS (con numero, que es lo que se pone en el README)")
    print("=" * 72)

    m2m = res[res["contrato"] == "Month-to-month"].iloc[0]
    dos = res[res["contrato"] == "Two year"].iloc[0]
    brecha = dos["ltv"] - m2m["ltv"]

    n_m2m = int(m2m["clientes"])
    ingreso_riesgo = m2m["churn"] * n_m2m * m2m["cuota_mensual"] * 12

    print(f"""
  1. El contrato mes a mes tiene {m2m['churn']:.0%} de churn contra {dos['churn']:.0%}
     del contrato a dos anios. Es la variable con mayor poder explicativo
     del dataset.

  2. Un cliente de dos anios vale ${brecha:,.0f} mas en LTV que uno mes a mes
     (${dos['ltv']:,.0f} contra ${m2m['ltv']:,.0f}), aun cobrandole una cuota
     mensual parecida.

  3. Los {n_m2m:,} clientes mes a mes representan aproximadamente
     ${ingreso_riesgo:,.0f} de ingreso anual en riesgo. Migrar aunque sea
     el 10% a contrato anual justifica con holgura un incentivo de retencion.
""")

    print("  Limitaciones a declarar en el README (esto suma, no resta):")
    print("   - Es un corte transversal, no un seguimiento en el tiempo.")
    print("   - RMST esta acotado a 72 meses: no extrapola mas alla de lo observado.")
    print("   - Correlacion, no causalidad: quien firma a dos anios probablemente")
    print("     ya era un cliente mas estable de entrada (autoseleccion).")


if __name__ == "__main__":
    main()
