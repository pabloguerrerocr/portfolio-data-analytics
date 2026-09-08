# Buscador automático de vacantes

Consulta APIs públicas de portales de empleo remoto, filtra por perfil analítico y
mantiene un CSV de seguimiento que **nunca sobrescribe ediciones manuales**.

```powershell
python buscar_vacantes.py
```

## Qué resuelve

Buscar vacantes a mano en cinco portales es repetitivo y se abandona a las dos semanas.
Este script lo reduce a un comando, y agrega dos datos que los portales muestran pero
nadie revisa sistemáticamente:

- **`accesible_cr`** — si la vacante admite a alguien en Costa Rica. Muchas dicen
  "remoto" pero restringen a un país. Sin este filtro se pierde tiempo aplicando a
  vacantes imposibles.
- **`competencia`** — cuántas personas ya aplicaron (Get on Board lo expone).
  Una vacante con 15 aplicantes vale más que una con 999.

## Fuentes

| Fuente | Cobertura | Nota |
|---|---|---|
| Get on Board | LATAM | Expone `applications_count`. Requiere `remote="true"` como cadena — con `1` la API lo ignora en silencio y devuelve presenciales |
| Himalayas | Remoto global | ~106.000 vacantes, pero **no admite búsqueda por texto**: `search`/`query` se ignoran sin error, hay que paginar y filtrar del lado del cliente |
| RemoteOK | Remoto global | Feed corto (100 vacantes), heterogéneo |

**Descartadas tras probarlas:** We Work Remotely responde 403 (Cloudflare) y forzarlo
sería scraping agresivo. Arbeitnow es un portal alemán: contaminaba los resultados con
vacantes en Alemania.

## Filtros

- **Perfil analítico, no de ingeniería.** Un título con `engineer`, `developer` o
  `architect` se descarta salvo que sea explícitamente `analyst` / `analista` /
  `economist`. `Analytics Engineer` se excluye a propósito: para un perfil junior es
  un puesto de pipelines, no de análisis.
- **El título manda sobre el campo de la API** para la seniority: hay vacantes
  marcadas `Mid-Level` que se titulan `Head of ...`.

## Diseño

El CSV se reescribe conservando las filas previas íntegras y agregando solo URLs
nuevas. Las columnas `estado` y `notas` son para editar a mano — el script no las toca.

## Lo que este script deliberadamente NO hace

No envía aplicaciones automáticamente. LinkedIn e Indeed suspenden cuentas por
auto-apply detectado, y una aplicación generada en cadena sin revisión humana es
precisamente lo que un reclutador descarta. El script automatiza el descubrimiento;
la decisión y el envío quedan en manos de la persona.
