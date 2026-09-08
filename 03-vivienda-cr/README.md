# Proyecto 2 — Precio de vivienda vs. fundamentales macro (Costa Rica)

> **Estado:** por iniciar. Arranca cuando el proyecto de churn esté publicado.

## Pregunta de negocio

¿Qué explica realmente el precio por m² en Costa Rica —tasas de interés, remesas,
turismo, oferta— y dónde hay zonas cotizando por debajo de lo que predicen sus
propios fundamentales?

## Por qué este proyecto

Conecta tu interés en bienes raíces con una pregunta de inversión concreta. A
diferencia del proyecto de churn (dataset limpio y acotado), aquí el trabajo real
está en **conseguir y conciliar los datos** — que es exactamente la habilidad que
más se paga y menos se enseña.

## Fuentes candidatas (todas públicas)

| Fuente | Qué aporta |
|---|---|
| BCCR – Indicadores Económicos | Tasa básica pasiva, tipo de cambio, IPC |
| INEC | Censo, vivienda, población por cantón |
| Encuesta Nacional de Hogares (INEC) | Ingreso por hogar y región |
| Portales inmobiliarios | Precios de listado (requiere scraping cuidadoso) |
| Banco Mundial / FMI | Remesas, turismo |

⚠️ **Ninguna fuente interna del BCCR.** Solo lo publicado abiertamente.

## Entregables

- [ ] Notebook de obtención y limpieza, con cada decisión justificada
- [ ] Análisis exploratorio: 4-5 gráficas que respondan algo concreto
- [ ] Modelo simple de precio vs. fundamentales (y sus limitaciones declaradas)
- [ ] README con el hallazgo, en número, en las primeras tres líneas

## Trampa a evitar

Terminar en «entrené un modelo con R² de 0,87». Nadie contrata por eso. El
entregable es una **decisión**: qué zonas están baratas y por qué.
