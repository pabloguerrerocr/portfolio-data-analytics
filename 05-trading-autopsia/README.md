# Proyecto 4 — Autopsia de una estrategia de trading retail

> **Estado:** por iniciar. Va al final: el tono analítico se afina con los
> proyectos previos.

## El encuadre lo es todo

**Esto NO es "construí un bot que gana dinero".** Cualquier analista senior
descarta ese portafolio en diez segundos, porque sabe que un backtest positivo
es fácil de fabricar por accidente.

**Esto es una autopsia:** tomás una estrategia popular, la medís con honestidad,
y demostrás **por qué su backtest miente**.

Ese giro es el proyecto. Un candidato que prueba que su propio resultado no es
confiable proyecta más criterio que uno que promete retornos.

## Pregunta

Esta estrategia muestra X % de retorno en el backtest. ¿Cuánto de eso es señal
y cuánto es artefacto de cómo se midió?

## Estructura

**1. La estrategia.** Algo deliberadamente común: cruce de medias móviles, RSI.
Cuanto más popular, mejor — el punto es desarmar lo que todo el mundo repite.

**2. Medirla en serio.**

| Métrica | Qué revela |
|---|---|
| Retorno acumulado | El número que todos muestran |
| **Máximo drawdown** | Cuánto habrías perdido en el peor tramo |
| Volatilidad anualizada | El riesgo que estás tomando de verdad |
| Sharpe | Retorno ajustado por riesgo |
| Comparación con *buy & hold* | ¿Le ganás a no hacer nada? |

**3. Desarmarla.** La parte que hace valioso el proyecto:

- **Look-ahead bias** — usar información que no existía en ese momento.
- **Sobreajuste** — probar 200 combinaciones de parámetros y quedarte con la
  mejor es *garantizar* un resultado bonito e irreproducible.
- **Survivorship bias** — analizar solo empresas que siguen existiendo hoy.
- **Costos de transacción** — comisiones y *slippage* borran muchas estrategias
  que en papel funcionaban.

**4. La conclusión honesta.** Cuánto del retorno sobrevive después de corregir
todo lo anterior. Si no sobrevive nada, ese *es* el hallazgo — y es un hallazgo
más fuerte que un retorno inventado.

## Datos

Precios históricos vía `yfinance` (público, gratuito).

## Lo que demuestra ante un evaluador

Madurez estadística: que sabés **cuándo un número miente**. Es lo más escaso en
un portafolio junior y lo que un evaluador de fintech reconoce al instante.
