# Nowcasting Costa Rica's quarterly GDP

*[Versión en español](README.md)*

**The naive benchmark is hard to beat, and almost nobody reports it.**

Estimating GDP growth before the official figure is published, using OECD
short-term indicators. The result has two numbers, not one, and that is half the
point:

| Compared against | Error reduction |
|---|---:|
| Repeating last quarter (the easy benchmark) | **30.6%** |
| Predicting the historical mean (the demanding benchmark) | **6.5%** |

Almost all published nowcasting work reports the first one. The second is the one
that tells you whether the model adds anything, and here it adds little: the R² is
**0.154**.

![GDP nowcast](nowcasting-pib/graficos/nowcast_pib.png)

## Why the honest result is worth more than the pretty one

The first version nowcast **year-over-year** growth and showed a +13.7%
improvement. Excluding 2020 it fell to **+0.6%**: all the merit was the pandemic.
A model that only gets the crash year right is useless for next quarter.

Switching the target to **quarter-over-quarter** growth and evaluating against
**two** benchmarks instead of one makes the result consistent and far less
flashy. 36 specifications were tested; the parsimonious ones systematically beat
those with six predictors.

All the signal comes from a single variable: **manufacturing production**
(t = 3.53). Exports are not significant, which is a finding in itself for an
economy that thinks of itself as export-driven.

## What the model does not do

In 2020-Q2 GDP fell **8.3%** and the nowcast predicted **+0.4%**. It does not
anticipate structural breaks and does not claim to. That is stated in the code, in
the report and here.

## Run it

```bash
pip install -r requirements.txt
python nowcasting-pib/nowcast.py
```

The data downloads itself from the OECD. No raw data is versioned.

---

## Other repositories

| Repository | What it is about |
|---|---|
| [warehouse-sector-externo](https://github.com/pabloguerrerocr/warehouse-sector-externo) | DuckDB star schema over the external-sector panel, with a data quality engine. The SQL de-accumulation reconciles to `5.7e-14` |
| [brecha-espejo-cr](https://github.com/pabloguerrerocr/brecha-espejo-cr) | Costa Rica reports $19.9 bn in exports and its partners report $34.0 bn in imports. Ten years of mirror-statistics gap, analyzed in SQL |
| [comercio-exterior-cr](https://github.com/pabloguerrerocr/comercio-exterior-cr) | Foreign trade concentrated instead of diversifying: Herfindahl from 0.160 to 0.248 between 2010 and 2024 |

---

## Principles I follow

- **The finding comes first**, with a number, in the first lines.
- **Limitations are stated.** A result that does not survive scrutiny is a
  finding, not a failure to hide.
- **Public data only**, with reproducible downloads from the script itself.
- **Raw data is not versioned** — the code fetches it.

---

📍 Costa Rica · Native Spanish, C1 English · [LinkedIn](https://linkedin.com/in/pabloguerrerocr)
