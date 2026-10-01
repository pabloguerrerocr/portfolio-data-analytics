# Nowcasting del PIB trimestral de Costa Rica

**¿Se puede estimar el crecimiento del PIB antes de que se publique la cifra oficial?**

> Sí, pero mucho menos de lo que sugiere una lectura descuidada. Frente a repetir el
> trimestre anterior, el nowcast reduce el error **30,6 %**. Frente al referente
> exigente —predecir el promedio histórico— la mejora real es de **6,5 %**.
> Toda la señal proviene de **una sola variable**: la producción manufacturera
> (t = 3,53). Las exportaciones no resultan significativas (t = 1,35).

![Nowcast del PIB trimestral](graficos/nowcast_pib.png)

---


## Correr

```bash
pip install -r ../requirements.txt
python nowcast.py
```

Si los datos no están, `nowcast.py` los baja solo de la API pública de la OCDE
(unos 760 KB). Para bajarlos aparte: `python descargar_datos.py`.

Verificado el 16 set 2026 corriendo desde cero: reproduce las cifras de este
README con datos hasta 2026-Q2.

## Por qué importa

El PIB trimestral se publica con meses de rezago. Un banco central, un ministerio de
hacienda o un inversionista necesitan una lectura del trimestre **en curso**, no
dentro de tres meses. Los indicadores de coyuntura —producción industrial, comercio
exterior— salen mucho antes. La pregunta práctica es cuánto anticipan realmente.

## Datos

Indicadores de corto plazo de la **OCDE** para Costa Rica (miembro desde 2021), vía
su API SDMX pública. Son las cifras que el propio BCCR reporta a la organización.

- 14.220 observaciones, 2000 → 2026
- PIB trimestral en volumen hasta **2026-Q2**; indicadores mensuales hasta **2026-08**
- Descarga reproducible: `python descargar_datos.py` (sin llave de acceso)

## Tres decisiones metodológicas que cambian el resultado

**1. Se nowcastea la variación trimestral, no la interanual.**
La interanual es tan persistente que repetir el dato previo ya es una predicción
fuerte. En esa versión el modelo mejoraba **+13,7 %** sobre el ingenuo — pero al
excluir 2020 la mejora caía a **+0,6 %**: todo el mérito era la pandemia. Cambiar
el objetivo a la variación trimestral vuelve el ejercicio informativo y la mejora
consistente (+30,6 % completa, +31,8 % excluyendo 2020).

**2. Dos referentes, no uno.**
Superar "repetir el trimestre anterior" es fácil, porque la serie trimestral revierte
a la media. El referente honesto es el **promedio histórico**, y contra él la mejora
es de 6,5 %. Reportar solo el primero habría inflado el resultado casi cinco veces.

**3. Menos predictores ganan.**
Con seis regresores el modelo sobreajustaba: fuera de muestra rendía peor que con
dos. Se probaron 36 especificaciones (objetivo × predictores × ventana × regularización)
y las parsimoniosas dominaron de forma sistemática.

## Resultados fuera de muestra

Ventana expansiva: para el trimestre *t* el modelo se ajusta solo con datos hasta
*t−1*. Nunca ve el futuro.

| Referente | RMSE | MAE | Mejora del nowcast |
|---|---|---|---|
| **Nowcast** | **1,59** | **0,89** | — |
| Repetir el trimestre previo | 2,29 | 1,46 | +30,6 % |
| Promedio histórico | 1,70 | 0,95 | +6,5 % |

Excluyendo 2020: +31,8 % y +7,0 % respectivamente. El resultado no depende de la pandemia.

## ¿Y con machine learning?

`ml.py` reentrena cuatro modelos cada trimestre, solo con el pasado y con
hiperparámetros elegidos por validación cruzada de series de tiempo, y los mide
contra los mismos dos referentes. La fila OLS reproduce `nowcast.py` exactamente.

| Modelo | Mejora sobre el promedio histórico | Sin 2020 | ¿Distinto de la OLS? (p, Diebold-Mariano) |
|---|---:|---:|---:|
| OLS (dos variables) | 6,3 % | 6,4 % | — |
| **Ridge** | **8,1 %** | **13,2 %** | 0,55 |
| LASSO | 7,6 % | 12,6 % | 0,66 |
| Random Forest | 6,5 % | 11,6 % | 0,90 |
| Gradient Boosting | 6,5 % | 8,9 % | 0,97 |

**Ningún modelo le gana a la regresión de dos variables de forma estadísticamente
significativa.** Ridge reduce más el error, pero con 46 trimestres la diferencia
cabe en el ruido (p = 0,55). Lo poco que se gana viene de regularizar y de sumar
rezagos, no de la no linealidad: los árboles quedan detrás de Ridge. Y la propia
OLS tampoco se distingue del promedio histórico con significancia (p = 0,13), lo
que confirma la lectura de arriba. Con datos frescos de la OCDE las mejoras de la
OLS quedan en 30,5 % y 6,3 %, muy cerca del 30,6 % y 6,5 % originales.

## Réplica en R

[`r/nowcast.R`](r/nowcast.R) reconstruye el panel con `dplyr`, estima cada
trimestre con `lm()` y grafica con `ggplot2`. Al final compara su resultado con
el de `nowcast.py`, trimestre por trimestre, y falla si alguna cifra difiere.
GitHub Actions corre las dos versiones con datos frescos de la OCDE en cada
cambio.

```bash
Rscript r/nowcast.R    # desde nowcasting-pib/, después de nowcast.py
```

## Limitaciones — lo que el modelo no hace

- **No anticipa puntos de quiebre.** En 2020-Q2 el PIB cayó 8,3 % y el nowcast
  predijo +0,4 %. Un modelo lineal sobre indicadores de producción no ve venir un
  cierre administrativo de la economía.
- **Suaviza la amplitud.** El panel inferior del gráfico lo muestra: el nowcast
  sigue el nivel pero comprime los saltos. Gran parte de su ventaja viene de ser
  conservador, no de acertar giros.
- **R² dentro de muestra = 0,154.** Es un modelo de señal débil. Se reporta porque
  esconderlo sería el error que este proyecto justamente critica.
- **Sin datos de vintage.** Se usan las series revisadas actuales, no las que
  realmente estaban disponibles en cada fecha. Un ejercicio en tiempo real estricto
  necesitaría el archivo de revisiones.

## Reproducir

```bash
pip install pandas numpy matplotlib requests
python descargar_datos.py    # baja los datos de la OCDE
python nowcast.py            # modelo, evaluación y gráfico
```

## Archivos

| Archivo | Contenido |
|---|---|
| `descargar_datos.py` | Descarga reproducible desde la API SDMX de la OCDE |
| `nowcast.py` | Panel, backtest, diagnóstico de regresión y gráfico |
| `ml.py` | Comparación con Ridge, LASSO, Random Forest y Gradient Boosting, con prueba de Diebold-Mariano |
| `r/nowcast.R` | Réplica en R (dplyr, ggplot2) verificada contra `nowcast.py` |
| `resultados_nowcast.csv` | Nowcast y referentes, trimestre por trimestre |
