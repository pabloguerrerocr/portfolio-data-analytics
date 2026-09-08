# ¿Cuánto dura un cliente y cuánto vale retenerlo?

**Análisis de supervivencia y valor de vida del cliente sobre 7.043 clientes de telecomunicaciones.**

---

## Hallazgos

**1. El tipo de contrato explica el churn mejor que cualquier otra variable del dataset.**
El contrato mes a mes tiene **42,7 % de churn** contra **2,8 %** del contrato a dos años
— una diferencia de 15x, con cuotas mensuales casi idénticas ($66,40 vs $60,77).

**2. Un cliente a dos años vale $1.964 más que uno mes a mes.**
LTV de **$4.344** contra **$2.381**. La diferencia no viene de cobrarle más: viene de que
dura **71,5 meses** en lugar de 35,9.

**3. Hay ~$1,3 millones de ingreso anual en riesgo concentrados en un solo segmento.**
Los 3.875 clientes mes a mes, a su tasa de churn actual, representan
**$1.318.674** de ingreso anual expuesto. Migrar apenas el 10 % de ellos a contrato
anual justifica con holgura el costo de un incentivo de retención.

![Curvas de supervivencia](graficos/supervivencia.png)

---

## Otros factores de riesgo

| Variable | Segmento de mayor riesgo | Churn |
|---|---|---|
| Método de pago | Electronic check | **45,3 %** |
| Servicio de internet | Fiber optic | **41,9 %** |
| Soporte técnico | Sin soporte técnico | **41,6 %** |

El cheque electrónico casi triplica el churn de los métodos automáticos (15-17 %). La
fibra óptica —el producto premium— pierde clientes al doble de ritmo que el DSL, lo que
sugiere un problema de expectativa contra precio, no de tecnología.

---

## Por qué análisis de supervivencia y no una matriz de cohortes

Este dataset es un **corte transversal**: cada cliente aparece una vez, con los meses que
lleva (`tenure`) y si ya se fue o no. No hay fechas de alta, así que **no se puede
construir una matriz de cohortes mes a mes** — el enfoque habitual en estos proyectos.

El método correcto es **Kaplan-Meier**, porque los clientes activos están **censurados por
la derecha**: sabemos que duraron al menos X meses, no cuánto durarán en total. Ignorar
esa censura subestima sistemáticamente la vida del cliente:

| Estimación | Resultado |
|---|---|
| Promedio simple de `tenure` | 32,4 meses |
| **RMST (censura considerada)** | **54,3 meses** |

Usar el promedio simple habría subestimado el LTV en un **40 %**, y con él toda la
justificación económica de invertir en retención.

**Validación:** la implementación de Kaplan-Meier de este repositorio está escrita a mano
(sin dependencias externas) y se verificó contra `lifelines`. Coincide con una diferencia
máxima de **4,33e-15** — precisión de punto flotante.

---

## Método

1. **Limpieza.** `TotalCharges` viene como texto; 11 registros vacíos, todos de clientes
   con `tenure = 0` (dados de alta sin facturar aún). Sin duplicados por `customerID`.
2. **Supervivencia.** Kaplan-Meier con `tenure` como duración y `Churn` como evento.
3. **Vida esperada.** RMST (área bajo la curva de supervivencia), acotada a 72 meses.
4. **LTV por segmento.** RMST del segmento × cuota mensual promedio del segmento.

## Limitaciones

- **Corte transversal, no seguimiento longitudinal.** No se observa la evolución real de
  cada cliente en el tiempo.
- **RMST acotado a 72 meses.** No extrapola más allá del horizonte observado; el LTV real
  de los contratos largos podría ser mayor.
- **Correlación, no causalidad.** Quien firma a dos años probablemente ya era un cliente
  más estable de entrada: hay **autoselección**. El efecto de *forzar* una migración a
  contrato anual sería menor que la diferencia observada. Medirlo bien exigiría un
  experimento o un diseño cuasi-experimental.

## Ejecutar

```bash
pip install pandas numpy matplotlib
python analisis_churn.py
```

## Datos

IBM Telco Customer Churn — 7.043 clientes, 21 variables. Dataset público.
El CSV no se versiona en el repositorio; el script indica la fuente de descarga.
