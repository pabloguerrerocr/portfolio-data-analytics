# Portafolio de Análisis de Datos

Ruta de 12 semanas de cero técnico a Data Analyst remoto.
Plan completo con entregables semanales: [Plan 84 Días](https://claude.ai/code/artifact/b8933b6f-298d-499b-8b94-d3cd15d46f94)

## Estructura

| Carpeta | Qué es | Semanas |
|---|---|---|
| `01-sql-practice/` | Práctica de SQL. No va al portafolio público, pero sostiene todo lo demás. | 1–3 |
| `02-proyecto-inmobiliario/` | **Proyecto 1** — ¿Qué determina el precio por m²? | 6 |
| `03-proyecto-retencion/` | **Proyecto 2** — Cohortes, churn y LTV. *El más importante.* | 7–8 |
| `04-proyecto-riesgo/` | **Proyecto 3** — Autopsia de un backtest. | 9 |

## Empezar

```powershell
cd 01-sql-practice
python empezar_aqui.py
```

Genera un dataset inmobiliario sintético (sucio a propósito) y corre tus
primeras tres queries en DuckDB. A partir de ahí, `queries/` es tuyo.

## Entorno

Python 3.13 · pandas · numpy · matplotlib · seaborn · duckdb · openpyxl · requests

```powershell
python -m pip install pandas numpy matplotlib seaborn duckdb openpyxl requests ipykernel
```

## Reglas

1. Commit diario, aunque sea una query.
2. Máximo 30% del tiempo consumiendo tutoriales, mínimo 70% escribiendo código propio.
3. Cada proyecto público lleva README con el **hallazgo en las primeras tres líneas**, con número.
4. Semana sin entregable público es semana perdida.
