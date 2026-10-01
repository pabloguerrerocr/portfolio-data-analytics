# Credit card fraud detection: how much money each alert rule saves

*[Versión en español](README.md)*

**Never raising an alert is 99.87% accurate and saves nothing.**

A bank does not decide "is this fraud?". It decides "do I send this transaction to
review?", and every review costs money. This project scores models in money saved,
not accuracy, on 284,807 real transactions with 0.17% fraud.

| Cost per review | Best single threshold | Expected-value rule | Difference (95% CI) |
|---|---:|---:|---:|
| €1 | 67.9% | 74.0% | −€179 to +€2,349 |
| €5 | 64.1% | 64.4% | −€52 to +€104 |
| **€15** | **54.5%** | **62.0%** | **+€379 to +€782** |

*Net savings as a share of test-period fraud, with Gradient Boosting.*

When review is expensive, alerting on **probability × amount > cost** saves 7.5
points more than the best threshold, and the gap is significant. It does so by
catching **fewer** frauds (21 vs 57): it lets the €1 ones go and chases the ones
worth reviewing. When review is cheap, the gap is not significant.

![Savings by threshold](graficos/ahorro_por_umbral.png)

## The default threshold is expensive

`predict()` alerts above 0.5. With logistic regression that saves **30.3%** of
fraud; the threshold chosen on validation (0.09) saves **55.5%**. Same model,
almost twice the money, from one number almost nobody touches.

## Method

1. **Time-based split**: train on the first 60%, choose model and threshold on
   the next 20%, evaluate on the last 20%.
2. **Model chosen on validation** (Gradient Boosting, PR-AUC 0.75 vs 0.62).
3. **Unweighted probabilities**, so the expected-value rule means what it says
   (69.8 expected vs 75 observed frauds in test).
4. **Sensitivity to review cost** (€1, €5, €15) instead of hiding the assumption.
5. **Bootstrap intervals** (2,000 resamples) for the difference between rules.

## Limitations

- The test set holds 75 frauds worth €7,729, so no winner is declared at €1 or €5.
- Assumes a reviewed alert stops the whole fraud.
- Two days of 2013 data: no drift over months.
- Features are anonymous principal components: no explanation of the pattern.

## Run it

```bash
pip install -r requirements.txt
python deteccion-fraude/fraude.py
```

Data: ULB Machine Learning Group and Worldline (Dal Pozzolo et al., 2015),
downloaded automatically from TensorFlow's public copy.
