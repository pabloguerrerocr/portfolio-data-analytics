# Nowcasting del PIB trimestral de Costa Rica

**El referente ingenuo es difícil de vencer, y casi nadie lo reporta.**

Estimar el crecimiento del PIB antes de que se publique la cifra oficial, con
indicadores de coyuntura de la OCDE. El resultado tiene dos números, no uno, y esa
es la mitad del punto:

| Contra qué se compara | Reducción del error |
|---|---:|
| Repetir el trimestre anterior (el referente fácil) | **30,6 %** |
| Predecir el promedio histórico (el referente exigente) | **6,5 %** |

Casi todo el trabajo publicado de nowcasting reporta el primero. El segundo es el
que dice si el modelo aporta algo, y acá aporta poco: el R² es **0,154**.

![Nowcast del PIB](nowcasting-pib/graficos/nowcast_pib.png)

## Por qué el resultado honesto vale más que el resultado bonito

La primera versión nowcasteaba la variación **interanual** y daba +13,7 % de mejora.
Al excluir 2020 caía a **+0,6 %**: todo el mérito era la pandemia. Un modelo que solo
acierta el año del derrumbe no sirve para el trimestre que viene.

Cambiar el objetivo a la variación **trimestral** y evaluar contra **dos** referentes
en lugar de uno vuelve el resultado consistente y mucho menos vistoso. Se probaron 36
especificaciones; las parsimoniosas superaron sistemáticamente a las de seis
predictores.

Toda la señal viene de una sola variable: la **producción manufacturera** (t = 3,53).
Las exportaciones no resultan significativas, que es en sí mismo un hallazgo para una
economía que se piensa a sí misma como exportadora.

## Lo que el modelo no hace

En 2020-Q2 el PIB cayó **8,3 %** y el nowcast predijo **+0,4 %**. No anticipa quiebres
y no pretende hacerlo. Está declarado en el código, en el reporte y acá.

## Correr

```bash
pip install -r requirements.txt
python nowcasting-pib/nowcast.py
```

Los datos se descargan solos desde la OCDE. No se versiona nada crudo.

---

## Otros repositorios

| Repositorio | De qué va |
|---|---|
| [warehouse-sector-externo](https://github.com/pabloguerrerocr/warehouse-sector-externo) | Esquema estrella en DuckDB sobre el panel del sector externo, con motor de calidad. La desacumulación en SQL reconcilia a `5,7e-14` |
| [brecha-espejo-cr](https://github.com/pabloguerrerocr/brecha-espejo-cr) | Costa Rica declara exportar $19,9 mm y sus socios declaran importar $34,0 mm. Diez años de brecha espejo, analizados en SQL |
| [comercio-exterior-cr](https://github.com/pabloguerrerocr/comercio-exterior-cr) | El comercio exterior se concentró en vez de diversificarse: Herfindahl de 0,160 a 0,248 entre 2010 y 2024 |

---

## Criterios que sigo

- **El hallazgo va primero**, con número, en las primeras líneas.
- **Las limitaciones se declaran.** Un resultado que no sobrevive al escrutinio es un
  hallazgo, no un fracaso que esconder.
- **Datos públicos únicamente**, con descarga reproducible desde el propio script.
- **Los datos crudos no se versionan** — el código los obtiene solo.

---

📍 Costa Rica · Español nativo, inglés C1 · [LinkedIn](https://linkedin.com/in/pabloguerrerocr)
