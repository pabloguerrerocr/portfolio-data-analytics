# Proyecto 3 — Nowcasting del PIB con el IMAE

> **Estado:** por iniciar. Es tu pieza insignia — abordarla con pandas ya rodado.

## Pregunta

¿Se puede estimar el crecimiento trimestral del PIB **antes** de que el dato
oficial se publique, usando el Índice Mensual de Actividad Económica (IMAE)?

## Por qué este es tu proyecto diferenciador

El *nowcasting* es lo que hacen los propios bancos centrales: el PIB sale con
rezago de meses, el IMAE sale mensual. Estimar uno con el otro es un problema
real de política monetaria, no un ejercicio de clase.

Casi ningún candidato junior lo intenta, porque exige entender series de tiempo
de verdad —rezagos, estacionalidad, frecuencias distintas— y no solo aplicar
`.fit()`. Vos ya tenés esa formación de tu trabajo en econometría.

**Para un evaluador de banco, fintech u organismo, este proyecto dice: "este
candidato entiende de qué está hecho el dato, no solo cómo graficarlo".**

## Fuentes (públicas, del portal de Indicadores Económicos del BCCR)

| Serie | Frecuencia |
|---|---|
| IMAE (Índice Mensual de Actividad Económica) | Mensual |
| PIB trimestral | Trimestral |
| IPC / inflación | Mensual |
| Tipo de cambio | Diario / mensual |

⚠️ **Solo series publicadas en el portal abierto.** Nada de lo que veas en la
base interna durante la práctica.

## Retos técnicos reales (esto es lo que lo hace valioso)

- **Frecuencias distintas:** mensual contra trimestral. Hay que agregar el IMAE
  a trimestre o desagregar el PIB.
- **Estacionalidad:** ambas series la tienen; decidir si trabajar con series
  desestacionalizadas o modelarla explícitamente.
- **Validación honesta:** evaluar con datos que el modelo no vio, respetando el
  orden temporal. Nada de mezclar futuro con pasado.

## Entregables

- [ ] Descarga reproducible de las series
- [ ] Análisis de la relación IMAE ↔ PIB (rezagos, correlación)
- [ ] Modelo de nowcasting con validación fuera de muestra
- [ ] Gráfico de estimado vs. real
- [ ] README con el error de predicción, en número
