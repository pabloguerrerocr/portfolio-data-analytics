# Nowcasting del PIB trimestral de Costa Rica, replicado en R.
#
# Reproduce nowcast.py con dplyr y ggplot2: mismo panel, misma ventana
# expansiva, mismos dos referentes. Al final compara trimestre por trimestre
# contra resultados_nowcast.csv y falla si alguna cifra difiere. Una réplica
# que no se verifica es una segunda versión, no una réplica.
#
# Uso (desde nowcasting-pib/):
#   python descargar_datos.py   # baja los datos de la OCDE
#   python nowcast.py           # versión de referencia
#   Rscript r/nowcast.R

suppressPackageStartupMessages({
  library(dplyr)
  library(tidyr)
  library(ggplot2)
})

PREDICTORES <- c("produccion_manufacturera", "exportaciones")
INICIO_PRUEBA <- "2015Q1"

# Paleta Okabe-Ito, la misma de la versión en Python.
AZUL <- "#0072B2"
NARANJA <- "#E69F00"
TINTA <- "#3A3A3A"

# ---------------------------------------------------------------- datos ----
a_trimestre <- function(periodo) {
  ifelse(grepl("Q", periodo),
         sub("-", "", periodo),
         paste0(substr(periodo, 1, 4), "Q",
                (as.integer(substr(periodo, 6, 7)) - 1) %/% 3 + 1))
}

serie <- function(df, measure, freq, transformacion, actividad = NULL, nombre) {
  sub <- df |>
    filter(MEASURE == measure, FREQ == freq, TRANSFORMATION == transformacion)
  if (!is.null(actividad)) sub <- filter(sub, ACTIVITY == actividad)
  # Mensual -> trimestral: promedio de los meses del trimestre.
  sub |>
    mutate(trimestre = a_trimestre(TIME_PERIOD)) |>
    group_by(trimestre) |>
    summarise("{nombre}" := mean(valor), .groups = "drop")
}

construir_panel <- function(ruta = "datos/cri_kei.csv") {
  if (!file.exists(ruta)) stop("No encuentro los datos. Corre descargar_datos.py")
  df <- read.csv(ruta, stringsAsFactors = FALSE)
  serie(df, "B1GQ_Q", "Q", "G1", nombre = "pib") |>
    full_join(serie(df, "PRVM", "M", "G1", "C", "produccion_manufacturera"),
              by = "trimestre") |>
    full_join(serie(df, "EX", "M", "G1", nombre = "exportaciones"),
              by = "trimestre") |>
    arrange(trimestre)
}

# --------------------------------------------------------------- modelo ----
backtest <- function(panel) {
  d <- panel |>
    drop_na(all_of(c("pib", PREDICTORES))) |>
    mutate(ingenuo = lag(pib)) |>
    drop_na(ingenuo)

  inicio <- which(d$trimestre >= INICIO_PRUEBA)[1]
  formula <- reformulate(PREDICTORES, response = "pib")

  bind_rows(lapply(inicio:nrow(d), function(i) {
    historia <- d[seq_len(i - 1), ]               # solo el pasado
    actual <- d[i, ]
    modelo <- lm(formula, data = historia)
    tibble(trimestre = actual$trimestre,
           observado = actual$pib,
           nowcast = unname(predict(modelo, newdata = actual)),
           ingenuo = actual$ingenuo,
           promedio = mean(historia$pib))
  }))
}

rmse <- function(a, b) sqrt(mean((a - b)^2))

comparar <- function(res, etiqueta) {
  base <- rmse(res$nowcast, res$observado)
  cat(sprintf("\n  %s  (n = %d trimestres)\n", etiqueta, nrow(res)))
  cat(sprintf("    %-28s RMSE %5.2f\n", "NOWCAST", base))
  for (ref in c("ingenuo", "promedio")) {
    r <- rmse(res[[ref]], res$observado)
    cat(sprintf("    %-28s RMSE %5.2f   mejora %+6.1f %%\n",
                ref, r, (1 - base / r) * 100))
  }
}

# -------------------------------------------------------------- gráfico ----
graficar <- function(res, destino = "graficos/nowcast_pib_r.png") {
  largo <- res |>
    select(trimestre, observado, nowcast) |>
    pivot_longer(-trimestre, names_to = "serie", values_to = "valor") |>
    mutate(serie = factor(recode(serie, observado = "PIB observado",
                                 nowcast = "Nowcast (fuera de muestra)"),
                          levels = c("PIB observado", "Nowcast (fuera de muestra)")))
  quiebres <- res$trimestre[seq(1, nrow(res), by = 4)]

  g <- ggplot(largo, aes(trimestre, valor, colour = serie, linetype = serie,
                         group = serie)) +
    geom_hline(yintercept = 0, colour = "#B8B8B8") +
    geom_line(linewidth = 0.9) +
    geom_point(size = 1.6) +
    scale_colour_manual(values = c("PIB observado" = AZUL,
                                   "Nowcast (fuera de muestra)" = NARANJA)) +
    scale_linetype_manual(values = c("PIB observado" = "solid",
                                     "Nowcast (fuera de muestra)" = "dashed")) +
    scale_x_discrete(breaks = quiebres) +
    labs(title = "Nowcasting del PIB trimestral de Costa Rica (réplica en R)",
         subtitle = "Cada punto usa solo información previa a ese trimestre. Fuente: OCDE.",
         x = NULL, y = "Variación trimestral (%)", colour = NULL, linetype = NULL) +
    theme_minimal(base_size = 10) +
    theme(text = element_text(colour = TINTA),
          plot.title = element_text(face = "bold"),
          legend.position = "bottom",
          panel.grid.major.x = element_blank(),
          panel.grid.minor = element_blank(),
          axis.text.x = element_text(angle = 45, hjust = 1))
  dir.create(dirname(destino), showWarnings = FALSE, recursive = TRUE)
  ggsave(destino, g, width = 10, height = 5, dpi = 160, bg = "white")
  destino
}

# ---------------------------------------------------------- verificación ----
verificar <- function(res, ruta = "resultados_nowcast.csv") {
  python <- read.csv(ruta, stringsAsFactors = FALSE)
  junto <- inner_join(res, python, by = "trimestre", suffix = c("_r", "_py"))
  if (nrow(junto) != nrow(python) || nrow(junto) != nrow(res))
    stop("Los trimestres de R y de Python no coinciden")
  # Python guarda con tres decimales: la tolerancia es medio milésimo.
  dif <- max(abs(round(junto$nowcast_r, 3) - junto$nowcast_py),
             abs(round(junto$promedio_r, 3) - junto$promedio_py))
  cat(sprintf("\nR contra Python: %d trimestres, diferencia máxima %.4f\n",
              nrow(junto), dif))
  if (dif > 0.0011) stop("La réplica en R no reproduce nowcast.py")
}

# ------------------------------------------------------------------ main ----
panel <- construir_panel()
res <- backtest(panel)

cat(strrep("=", 60), "\nDESEMPEÑO FUERA DE MUESTRA, CONTRA DOS REFERENTES\n",
    strrep("=", 60), sep = "")
comparar(res, "muestra completa")
comparar(filter(res, !startsWith(trimestre, "2020")), "excluyendo 2020")

cat("\ngráfico:", graficar(res), "\n")
verificar(res)
