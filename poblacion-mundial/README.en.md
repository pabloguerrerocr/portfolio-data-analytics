# World population 2026: a Power BI map

*[Versión en español](README.md)*

**[Explore the interactive atlas →](https://pabloguerrerocr.github.io/atlas/)** (in Spanish)

[![Economic data](https://github.com/pabloguerrerocr/portfolio-data-analytics/actions/workflows/datos-economicos.yml/badge.svg)](https://github.com/pabloguerrerocr/portfolio-data-analytics/actions/workflows/datos-economicos.yml)

**Africa holds 19% of the world's population and accounts for 51% of its growth.**

Meanwhile, 62 countries are shrinking, and 27% of the world's people live in them.
And 73% of humanity lives in a country with fertility below replacement (2.1
children per woman).

| | 2026 |
|---|---:|
| World population | **8,299 M** |
| Net growth over the year | **+69.1 M (+0.84%)** |
| Africa's share of growth | **50.8%** |
| Countries losing population | **62** (27% of world population) |
| Largest absolute decline | China, **−3.18 M** |
| Largest absolute increase | India, **+12.76 M** |

![Yearly population change](graficos/mapa_crecimiento.png)

![Population by country](graficos/mapa_poblacion.png)

These two images are the Python preview. The deliverable is the Power BI report you
build with the guide below. It has the same maps, plus continent filters, per-country
tooltips and cards that recalculate with the selection.

## Interactive atlas

[`web/index.html`](web/index.html) opens in any browser, with no server and no
Power BI. It has the map with 18 population and economic indicators, continent and income filters, a profile for each
country, a simulator that projects population at the current rate, and the full
sortable table. Rebuild it with `python web/construir.py`.

## Economic data that updates itself

`datos_economicos.py` pulls GDP per capita, growth, inflation, debt, life expectancy,
remittances, youth unemployment, dependency and Gini from the **World Bank** (latest
year published per country) and the **IMF** (2026 estimates and projections). Every
value carries its year, and IMF figures more than two years old are dropped so nothing
stale passes as current. A GitHub Actions workflow runs it on the 5th of each month and
commits `datos/economia.csv` when something changed.

What it adds:

- Low and lower-middle income countries hold **45%** of the population and **85%** of
  its growth. High-income countries: 17% and 3%.
- In **20 countries** (488 M people) population grows faster than the economy in 2026,
  so income per person falls.
- Wealth and fertility have a rank correlation of **−0.80** across 198 countries.

## Why the map doesn't lie

A population map looks just as convincing with broken data as with good data, so
`preparar_datos.py` validates the table before producing anything:

| Check | Result |
|---|---|
| Rank matches population order | OK, 234 of 234 |
| World shares add up to 100% | 99.90% (the source rounds each share) |
| Yearly change reproduces from population and net change | Max. difference 0.005 pp |
| Density = population / land area | OK within source rounding |
| Global net migration sums to zero | +13,500 against 69 M growth, so ≈ 0 |

If any check fails, the script stops. It also reports what's missing: 24 territories
don't publish urban population (left blank, not zero), and the Holy See is listed
with 0 km² of land.

Two calculation choices change the numbers:

- **Rates are population-weighted.** A plain average of the 234 growth rates gives
  Tuvalu (9,362 people) the same weight as India. The DAX measures divide net growth
  by population instead of averaging percentages.
- **World share is computed, not copied.** The source rounds China to 17%; the
  actual value is 17.03%.

## What the map doesn't do

- **It isn't a projection.** It's a 2025 → 2026 snapshot. One year's rates don't
  extrapolate to 2050.
- **Small territories don't show on the filled map.** Monaco, Tokelau and Gibraltar
  have no visible area at world scale. They do appear as bubbles and in the table.
- **The figures are Worldometer estimates** (based on the UN *World Population
  Prospects*), not censuses. Ukraine is shown growing +1.43%. For a country at war,
  that's a model assumption, not a count.

## Building the report in Power BI

On Google Maps: Power BI has no built-in Google Maps visual, and third-party ones
need a Google API key. The native visual is **Azure Maps**, which replaced the Bing
maps. It does the same job with no key and no cost. If it's missing, a tenant admin
has to enable it under *Admin portal > Tenant settings > Azure Maps*.

### 1. Load the data

1. *Home > Get data > Blank query > Advanced editor*.
2. Paste [`powerbi/poblacion.pq`](powerbi/poblacion.pq), rename the query to
   **Poblacion**, then *Close & apply*.
3. In data view, set `Country` to *Column tools > Data category > Country/Region*.
   Set `Latitude` to *Latitude* and `Longitude` to *Longitude* the same way.
4. Sort `GrowthBand` by `GrowthBandOrder` (*Sort by column*).

### 2. Measures and theme

1. Create each measure in [`powerbi/medidas.dax`](powerbi/medidas.dax) (*Modeling >
   New measure*). Format the `%` measures as percentages with 2 decimals, and the
   population measures as whole numbers with a thousands separator.
2. *View > Themes > Browse for themes* > [`powerbi/tema_poblacion.json`](powerbi/tema_poblacion.json).

### 3. "World map" page

```
┌──────────────────────────────────────────────────────────────┐
│ [Título del mapa]                      [Slicer: Continent]   │
├──────────┬──────────┬──────────┬──────────┬──────────────────┤
│ Total    │ Yearly   │ Share of │ Shrinking│ % below          │
│ pop.     │ change % │ growth % │ countries│ replacement      │
├──────────┴──────────┴──────────┴──────────┴──────────────────┤
│                                                              │
│          Azure Maps: filled map + bubbles                    │
│                                                              │
├──────────────────────────────┬───────────────────────────────┤
│ Bars: top 10 net growth      │ Bars: top 10 decline          │
└──────────────────────────────┴───────────────────────────────┘
```

**Map (Azure Maps)**

| Well | Field |
|---|---|
| Location | `Country` |
| Latitude / Longitude | `Latitude` / `Longitude` |
| Size | `Población total` |
| Tooltips | `Cambio anual %`, `Crecimiento natural`, `Migración neta`, `Fecundidad ponderada`, `Edad mediana ponderada`, `Urbanización %` |

- *Filled map layer*: on. *Fill color > fx > Field value >* `Color cambio anual`.
  It uses the same blue-gray-red scale as the preview.
- *Bubble layer*: color `#2A78D6`, 25% transparency, 1 px white border, min size 2,
  max 40.
- Map style: *Grayscale (light)*, so the colors you see are the data, not the
  basemap.

Latitude and longitude come from Natural Earth label points. That's why Georgia
lands in the Caucasus rather than the US, and Congo isn't confused with DR Congo,
which is the classic failure when geocoding by name.

**Cards**: `Población total`, `Cambio anual %`, `Cuota del crecimiento mundial %`,
`Países que se achican`, `% bajo reemplazo`. For the title, add a text box with
*fx* > `Título del mapa`.

**Bars**: axis `Country`, value `Crecimiento neto`, Top N filter = 10. Sort the
second chart ascending to show who loses the most people.

### 4. "Detail" page (optional)

- Scatter: X `FertilityRate`, Y `MedianAge`, size `Population2026`, legend
  `Continent`. It shows the whole demographic transition in one chart.
- A table with every column and conditional formatting on `YearlyChangePct`.

## Run

```bash
pip install -r ../requirements.txt
python preparar_datos.py   # cleans, validates, writes datos/poblacion_mundial_2026.csv
python mapa.py             # preview: graficos/*.png
```

`preparar_datos.py` downloads only the Natural Earth boundaries (3 MB, not
committed). The population table is committed as `datos/worldometer_2026.tsv`, copied
as-is from [Worldometer](https://www.worldometers.info/world-population/population-by-country/),
because Worldometer offers no reproducible download.
