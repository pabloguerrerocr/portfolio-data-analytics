// Power Query (M) - tabla "Poblacion"
// Power BI Desktop > Inicio > Obtener datos > Consulta en blanco >
// Editor avanzado > pegar todo esto.
//
// Lee el CSV ya limpio desde GitHub. Para trabajar sin conexión, reemplaza
// Origen por: Csv.Document(File.Contents("C:\ruta\poblacion_mundial_2026.csv"), ...)
let
    Url = "https://raw.githubusercontent.com/pabloguerrerocr/portfolio-data-analytics/main/poblacion-mundial/datos/poblacion_mundial_2026.csv",
    Origen = Csv.Document(
        Web.Contents(Url),
        [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
    ),
    Encabezados = Table.PromoteHeaders(Origen, [PromoteAllScalars = true]),
    // "en-US": el CSV usa punto decimal, sin importar la configuración regional
    // de la máquina (con es-CR, "0.0087" se leería como 87).
    Tipos = Table.TransformColumnTypes(
        Encabezados,
        {
            {"Rank", Int64.Type},
            {"Country", type text},
            {"Population2026", Int64.Type},
            {"YearlyChangePct", Percentage.Type},
            {"NetChange", Int64.Type},
            {"DensityPerKm2", Int64.Type},
            {"LandAreaKm2", Int64.Type},
            {"NetMigrants", Int64.Type},
            {"FertilityRate", type number},
            {"MedianAge", type number},
            {"UrbanPopPct", Percentage.Type},
            {"WorldSharePct", Percentage.Type},
            {"ISO3", type text},
            {"Latitude", type number},
            {"Longitude", type number},
            {"Continent", type text},
            {"Subregion", type text},
            {"Population2025", Int64.Type},
            {"NaturalIncrease", Int64.Type},
            {"GrowthBand", type text}
        },
        "en-US"
    ),
    // Orden de la banda de crecimiento para leyendas y segmentadores.
    OrdenBanda = Table.AddColumn(
        Tipos,
        "GrowthBandOrder",
        each List.PositionOf({"Shrinking", "0-1%", "1-2%", "2%+"}, [GrowthBand]),
        Int64.Type
    )
in
    OrdenBanda
