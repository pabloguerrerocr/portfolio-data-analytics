# Portafolio de Análisis de Datos — José Pablo Guerrero

Economista (Universidad Latina de Costa Rica) con formación en econometría y series de
tiempo. Este repositorio reúne análisis construidos con datos públicos, priorizando
preguntas de negocio sobre demostraciones de herramientas.

---

## 🟢 Proyecto terminado

### [Churn y valor de vida del cliente](02-churn-retencion/)

**¿Cuánto dura un cliente y cuánto vale retenerlo?** Análisis de supervivencia sobre
7.043 clientes de telecomunicaciones.

> El contrato mes a mes tiene **42,7 % de churn** contra **2,8 %** del contrato a dos
> años. Un cliente a dos años vale **$1.964 más** en LTV, cobrándole una cuota mensual
> casi idéntica. El segmento mes a mes concentra **~$1,3 M** de ingreso anual en riesgo.

![Curvas de supervivencia](02-churn-retencion/graficos/supervivencia.png)

**Lo técnicamente relevante:** el dataset es transversal y no tiene fechas de alta, así
que no admite una matriz de cohortes. El método correcto es Kaplan-Meier, tratando a los
clientes activos como censurados por la derecha. El estimador está **implementado a mano
y validado contra `lifelines`** (diferencia máxima 4,33e-15).

Ignorar la censura habría subestimado la permanencia en un 40 % (32,4 vs 54,3 meses) —
y con ella, toda la justificación económica de invertir en retención.

---

## 🟡 En construcción

| Proyecto | Pregunta |
|---|---|
| [Vivienda vs. fundamentales macro](03-vivienda-cr/) | ¿Qué explica el precio por m² en Costa Rica y dónde hay zonas subvaloradas? |
| [Nowcasting del PIB con el IMAE](04-nowcasting-imae/) | ¿Se puede estimar el crecimiento trimestral antes de que se publique el dato oficial? |
| [Autopsia de una estrategia de trading](05-trading-autopsia/) | De un backtest positivo, ¿cuánto es señal y cuánto artefacto de medición? |

Cada carpeta documenta la pregunta, las fuentes públicas candidatas y el criterio de
calidad antes de escribir una línea de código.

---

## Stack

`Python` · `pandas` · `numpy` · `matplotlib` · `SQL` · `DuckDB` · `Excel / Power Query`

## Criterios que sigo en cada proyecto

- **El hallazgo va primero**, con número, en las primeras líneas del README.
- **Las limitaciones se declaran.** Correlación no es causalidad, y decirlo suma.
- **Datos públicos únicamente**, con descarga reproducible desde el propio script.
- **Los datos crudos no se versionan** — el código los obtiene solo.

---

📍 Costa Rica · Español nativo, inglés C1 · [LinkedIn](https://linkedin.com/in/jpguerreroc)
