"""
Buscador automatico de vacantes remotas — Data / AI / Economia / RevOps.

Fuentes (APIs publicas, sin credenciales, sin scraping):
  - Get on Board  -> LATAM (espanol/ingles). Expone cuantas personas ya aplicaron.
  - Himalayas     -> remoto global (ingles). Expone restricciones geograficas.
  - RemoteOK      -> remoto global, feed corto.

Descartadas tras probarlas:
  - WeWorkRemotely: responde 403 (Cloudflare). Forzarlo seria scraping agresivo.
  - Arbeitnow: es un portal aleman; contaminaba los resultados con vacantes en Alemania.

DISENO: el script NUNCA sobreescribe tus ediciones. Solo agrega vacantes nuevas
(deduplicadas por URL). Las columnas 'estado' y 'notas' son tuyas.

Uso:   python buscar_vacantes.py
"""

from __future__ import annotations

import csv
import re
import sys
import time
from datetime import date
from pathlib import Path

import requests

AQUI = Path(__file__).parent
CSV_SALIDA = AQUI / "vacantes.csv"
TIMEOUT = 25
UA = {"User-Agent": "Mozilla/5.0 (busqueda-empleo personal)"}

# --- que buscar ----------------------------------------------------------
CONSULTAS_LATAM = [
    "analista de datos", "business intelligence", "data analyst",
    "analista financiero", "economista", "power bi", "revenue operations",
    "analista de negocio", "inteligencia artificial",
]

KEYWORDS = [
    # data
    "data analyst", "analista de datos", "business intelligence", "bi analyst",
    "data analytics", "power bi", "analytics",
    # ai
    "ai analyst", "llm", "prompt engineer", "machine learning", "data scientist",
    "generative ai", "inteligencia artificial", "ai automation",
    # revops / negocio
    "revops", "revenue operations", "sales analyst", "business analyst",
    "operations analyst", "growth analyst", "analista de negocio",
    # economia / finanzas
    "economist", "economista", "research analyst", "financial analyst",
    "analista financiero", "quantitative", "market research",
]

SENIOR = ["senior", "sr.", "lead", "principal", "head of", "director",
          "manager", "vp ", "staff ", "chief", "cto", "cfo"]
JUNIOR = ["junior", "jr.", "entry level", "entry-level", "graduate",
          "trainee", "associate", "practicante", "pasante"]

# Roles de ingenieria de software: NO son perfil de analista.
# Se descartan salvo que el titulo tambien sea explicitamente analitico.
INGENIERIA = ["engineer", "engineering", "ingenier", "back-end", "backend",
              "front-end", "frontend", "full stack", "full-stack", "fullstack",
              "developer", "desarrollador", "architect", "arquitecto", "devops",
              "sre", "qa ", "tester", "programador", "mobile", "android", "ios "]
# Solo el sustantivo del ROL rescata un titulo de ingenieria. 'Analytics Engineer'
# NO se rescata a proposito: para un perfil junior es un puesto de pipelines.
ANALITICO = ["analyst", "analista", "economist", "economista"]


def es_de_ingenieria(titulo: str) -> bool:
    """True si el puesto es de construccion de software, no de analisis."""
    t = (titulo or "").lower()
    if any(a in t for a in ANALITICO):
        return False          # 'Data Analyst / Developer' si pasa
    return any(i in t for i in INGENIERIA)

# Paises desde los que Jose Pablo puede trabajar / que no lo excluyen
LATAM = {"costa rica", "latam", "latin america", "worldwide", "anywhere",
         "global", "remote", "americas", "north america", "south america"}


def nivel_por_titulo(titulo: str) -> str:
    t = (titulo or "").lower()
    if any(s in t for s in SENIOR):
        return "senior"
    if any(j in t for j in JUNIOR):
        return "junior"
    return "sin especificar"


def keys_en(texto: str) -> list[str]:
    t = re.sub(r"\s+", " ", (texto or "").lower())
    return [k for k in KEYWORDS if k in t]


def accesible_desde_cr(restricciones: list[str]) -> str:
    """Devuelve 'si', 'revisar' o la restriccion concreta."""
    if not restricciones:
        return "si (sin restriccion)"
    low = [str(r).lower() for r in restricciones]
    if any(any(ok in r for ok in LATAM) for r in low):
        return "si"
    return "NO: " + ", ".join(str(r) for r in restricciones[:3])


CAMPOS = ["fecha_encontrada", "titulo", "empresa", "fuente", "nivel",
          "accesible_cr", "competencia", "salario", "url", "keywords",
          "estado", "notas"]


def registro(**kw) -> dict:
    base = {c: "" for c in CAMPOS}
    base["fecha_encontrada"] = date.today().isoformat()
    base["estado"] = "nueva"
    base.update(kw)
    return base


# ------------------------------ fuentes ----------------------------------
def de_getonbrd() -> list[dict]:
    """LATAM. Una consulta por termino; la API pagina de a 20."""
    out, vistos = [], set()
    for q in CONSULTAS_LATAM:
        try:
            r = requests.get(
                "https://www.getonbrd.com/api/v0/search/jobs",
                # OJO: remote debe ir como la cadena "true". Con 1 la API lo
                # ignora en silencio y devuelve vacantes presenciales.
                params={"query": q, "per_page": 30, "remote": "true"},
                headers=UA, timeout=TIMEOUT,
            )
            r.raise_for_status()
            for item in r.json().get("data", []):
                slug = item.get("id")
                if not slug or slug in vistos:
                    continue
                a = item.get("attributes", {})
                titulo = a.get("title", "")
                ks = keys_en(f"{titulo} {a.get('category_name','')}")
                if not ks or es_de_ingenieria(titulo):
                    continue
                vistos.add(slug)

                paises = a.get("countries") or []
                if a.get("remote"):
                    acc = accesible_desde_cr(paises) if paises else "si (remoto)"
                else:
                    acc = f"NO: presencial/hibrido en {', '.join(paises) or '?'}"

                sal = ""
                if a.get("min_salary") or a.get("max_salary"):
                    sal = f"{a.get('min_salary') or '?'}-{a.get('max_salary') or '?'} USD"

                out.append(registro(
                    titulo=titulo,
                    empresa="",   # la API rompe con expand=company; se ve al abrir el link
                    fuente="GetOnBoard",
                    nivel=nivel_por_titulo(titulo),
                    accesible_cr=acc,
                    competencia=str(a.get("applications_count") or ""),
                    salario=sal,
                    url=f"https://www.getonbrd.com/jobs/{slug}",
                    keywords=", ".join(sorted(set(ks))[:4]),
                ))
            time.sleep(0.4)   # cortesia con la API
        except Exception as e:
            print(f"    ! GetOnBoard '{q}': {e}")
    return out


def de_himalayas(paginas: int = 24) -> list[dict]:
    """Remoto global. Pagina de a 50.

    La API tiene ~106.000 vacantes pero NO admite busqueda por texto
    (los parametros search/query se ignoran sin error), asi que la unica
    via es paginar y filtrar del lado nuestro. ~24 paginas = 1.200 vacantes.
    """
    out, offset = [], 0
    for _ in range(paginas):
        try:
            r = requests.get("https://himalayas.app/jobs/api",
                             params={"limit": 50, "offset": offset},
                             headers=UA, timeout=TIMEOUT)
            r.raise_for_status()
            jobs = r.json().get("jobs", [])
            if not jobs:
                break
            for j in jobs:
                titulo = j.get("title", "")
                ks = keys_en(f"{titulo} {' '.join(j.get('categories') or [])}")
                if not ks or es_de_ingenieria(titulo):
                    continue
                # El titulo manda sobre el campo de la API: hay vacantes
                # marcadas 'Mid-Level' que se titulan 'Head of ...'.
                nivel = nivel_por_titulo(titulo)
                if nivel == "sin especificar":
                    sen = j.get("seniority") or []
                    nivel = ", ".join(sen).lower() if sen else nivel

                sal = ""
                if j.get("minSalary") or j.get("maxSalary"):
                    cur = j.get("currency") or "USD"
                    sal = f"{j.get('minSalary') or '?'}-{j.get('maxSalary') or '?'} {cur}"

                out.append(registro(
                    titulo=titulo,
                    empresa=j.get("companyName", ""),
                    fuente="Himalayas",
                    nivel=nivel,
                    accesible_cr=accesible_desde_cr(j.get("locationRestrictions") or []),
                    salario=sal,
                    url=j.get("applicationLink") or j.get("guid") or "",
                    keywords=", ".join(sorted(set(ks))[:4]),
                ))
            offset += 50
            time.sleep(0.4)
        except Exception as e:
            print(f"    ! Himalayas offset {offset}: {e}")
            break
    return out


def de_remoteok() -> list[dict]:
    try:
        r = requests.get("https://remoteok.com/api", headers=UA, timeout=TIMEOUT)
        r.raise_for_status()
    except Exception as e:
        print(f"    ! RemoteOK: {e}")
        return []
    out = []
    for j in r.json():
        if not isinstance(j, dict) or not j.get("position"):
            continue
        titulo = j.get("position", "")
        ks = keys_en(f"{titulo} {' '.join(j.get('tags') or [])}")
        if not ks or es_de_ingenieria(titulo):
            continue
        out.append(registro(
            titulo=titulo,
            empresa=j.get("company", ""),
            fuente="RemoteOK",
            nivel=nivel_por_titulo(titulo),
            accesible_cr=accesible_desde_cr([j.get("location")] if j.get("location") else []),
            url=j.get("url", ""),
            keywords=", ".join(sorted(set(ks))[:4]),
        ))
    return out


# ------------------------------- main ------------------------------------
def cargar_existentes() -> tuple[list[dict], set[str]]:
    if not CSV_SALIDA.exists():
        return [], set()
    with CSV_SALIDA.open(encoding="utf-8-sig", newline="") as fh:
        filas = [{c: f.get(c, "") for c in CAMPOS} for f in csv.DictReader(fh)]
    return filas, {f["url"] for f in filas}


def main() -> int:
    print("Buscando vacantes...\n")
    encontradas: list[dict] = []
    for nombre, fn in [("GetOnBoard (LATAM)", de_getonbrd),
                       ("Himalayas (global)", de_himalayas),
                       ("RemoteOK", de_remoteok)]:
        res = fn()
        print(f"  {nombre:22} {len(res):3} coincidencias")
        encontradas.extend(res)

    previas, urls = cargar_existentes()
    nuevas, ahora = [], set()
    for f in encontradas:
        u = f["url"]
        if not u or u in urls or u in ahora:
            continue
        ahora.add(u)
        nuevas.append(f)

    if not nuevas:
        print(f"\nSin vacantes nuevas. El archivo ya tiene {len(previas)}.")
        return 0

    with CSV_SALIDA.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=CAMPOS)
        w.writeheader()
        w.writerows(previas + nuevas)

    accesibles = [f for f in nuevas if not f["accesible_cr"].startswith("NO")]
    no_senior = [f for f in accesibles if "senior" not in f["nivel"].lower()
                 and "executive" not in f["nivel"].lower()]

    print(f"\n{len(nuevas)} vacantes NUEVAS -> {CSV_SALIDA.name}")
    print(f"  {len(accesibles)} accesibles desde Costa Rica")
    print(f"  {len(no_senior)} de esas, no son senior/executive  <- empeza por aqui\n")

    print("Mejores candidatas:")
    # Menos competencia primero cuando el dato existe
    def comp(f):
        try:
            return int(f["competencia"])
        except (ValueError, TypeError):
            return 9999
    for f in sorted(no_senior, key=comp)[:10]:
        c = f["competencia"] or "?"
        print(f"  [{c:>4} aplicantes] {f['titulo'][:48]:48} | {f['empresa'][:18]:18} | {f['fuente']}")

    print(f"\nAbri {CSV_SALIDA.name}, marca 'estado' a mano, y volve a correrlo cuando quieras.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
