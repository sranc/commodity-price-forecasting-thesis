# Diccionario de Datos y Estrategia de Preprocesamiento

Este documento detalla todas las variables crudas (Raw Data) extraídas para el pronóstico de precios de _Commodities_, incluyendo sus metadatos económicos y la metodología técnica que se utilizará para su limpieza y preparación (Feature Engineering) de cara a los modelos de Machine Learning y Econométricos (ARIMA, GARCH, LSTM).

---

## 1. Tabla de Variables Extraídas

| Categoría               | Variable              | Ticker / Fuente    | Frecuencia Real       | Tipo de Dato        | Unidad / Dimensión                          |
| :---------------------- | :-------------------- | :----------------- | :-------------------- | :------------------ | :------------------------------------------ |
| **Target**              | Oro (_Gold_)          | `GC=F` (YFinance)  | Diario (Días Hábiles) | Precio Continuo     | USD por Onza Troy                           |
| **Target**              | Plata (_Silver_)      | `SI=F` (YFinance)  | Diario (Días Hábiles) | Precio Continuo     | USD por Onza                                |
| **Target**              | Cobre (_Copper_)      | `HG=F` (YFinance)  | Diario (Días Hábiles) | Precio Continuo     | USD por Libra                               |
| **Target**              | Zinc (_Zinc_)         | `ZNC=F` (YFinance) | Diario (Días Hábiles) | Precio Continuo     | USD por Tonelada Métrica                    |
| **Exógena: Market**     | Petróleo WTI          | `CL=F` (YFinance)  | Diario (Días Hábiles) | Precio Continuo     | USD por Barril                              |
| **Exógena: Market**     | Índice Dólar          | `DX=F` (YFinance)  | Diario (Días Hábiles) | Índice Ponderado    | Índice base (Dólar vs canasta)              |
| **Exógena: Macro (US)** | Inflación (CPI)       | `CPIAUCSL` (FRED)  | Mensual               | Índice de Precios   | Índice base 1982-1984=100                   |
| **Exógena: Macro (US)** | Producción Industrial | `INDPRO` (FRED)    | Mensual               | Índice Cuantitativo | Índice base 2017=100                        |
| **Exógena: Macro (US)** | CLI OECD              | `USALOLITONOSTSAM` | Mensual               | Leading Indicator   | Amplitud Ajustada (Largo plazo=100)         |
| **Exógena: Macro (CH)** | Inflación (CPI)       | `CHNCPIALLMINMEI`  | Mensual               | Índice de Precios   | Crecimiento Interanual (Porcentaje / Nivel) |
| **Exógena: Macro (CH)** | Producción Industrial | `CHNPRINTO01IXPYM` | Mensual               | Índice Cuantitativo | Índice base especificado por OECD           |
| **Exógena: Macro (CH)** | CLI OECD              | `CHNLOLITOAASTSAM` | Mensual               | Leading Indicator   | Amplitud Ajustada (Largo plazo=100)         |

---

## 2. Metodología de Preprocesamiento

Los datos crudos (Raw Data) tienen dos problemas principales que deben resolverse antes de alimentar los modelos: **Frecuencias temporales mixtas** (Diario vs Mensual) y **Distribuciones no estacionarias** (los precios financieros tienen tendencias).

Para solucionar esto, el módulo lógico `src/preprocessing/` ejecutará las siguientes tareas en cascada:

### A. Alineación Temporal y Manejo de Nulos (Imputation)

1. **Calendario Común:** Se creará un calendario de "Días de Trading" (_Business Days_).
2. **Targets y Mercado Diario:** Los feriados o días sin cotización en Yahoo Finance generarán filas `NaN`. Se utilizará **Forward Fill (`ffill`)** para reemplazar esos vacíos con el precio de cierre del día hábil inmediatamente anterior.
3. **Pilar Macroeconómico:** Los indicadores macro (Inflación, CLI, Prod. Industrial) solo cambian una vez al mes. Se fusionarán con la tabla diaria utilizando también un **Forward Fill**, lo que significa que el valor del "1 de Marzo" se propagará hacia los días 2, 3, 4..., simulando que la "información conocida por el mercado" de esa variable se mantiene constante durante ese mes.

### B. Estacionariedad y Transformación (Feature Engineering)

Los modelos econométricos (ARIMA, GARCH) exigen datos estacionarios (media y varianza constantes sobre el tiempo). Usar los precios absolutos directamente es un error técnico.

1. **Para los Targets (Oro, Plata, Cobre, Zinc) y Market (Crudo, DXY):**
   - Se calcularán los **Retornos Logarítmicos Diarios**: $R_t = \ln(P_t / P_{t-1})$.
   - Esta transformación estabiliza la varianza y convierte tendencias exponenciales en estacionarias, siendo la representación estándar del "Rendimiento" en finanzas.
2. **Medias Móviles y Momento (Technical Indicators):**
   - Se crearán columnas calculadas sobre el precio base crudo: $SMA_{7}$ (Media Móvil Semanal), $SMA_{21}$ (Mensual) y Volatilidad Rodante (Desviación Estandar de los últimos 21 días) para proveerle memoria de corto plazo al LSTM.

3. **Para los Indicadores Macro (Inflación, CLI, INDPRO):**
   - Al ser índices numéricos con base (ej. 100), se transformarán en **Tasa de Crecimiento Porcentual mes a mes (MoM %)** o **Crecimiento Interanual (YoY %)** antes de propagarlas con _Forward fill_.
   - Esto convierte al dato macro en una variable dinámica entendible por la red neuronal, eliminando el ruido absoluto del índice general.

### C. Normalización y Escalado (Scaling)

1. Antes de entrar al modelo LSTM, todas las columnas transformadas pasarán por un `MinMaxScaler(-1, 1)` o `StandardScaler` de la librería `scikit-learn`.
2. El escalador se "ajustará" (`fit`) **solo sobre el conjunto de Entrenamiento (Train Data)** para prevenir Fuga de Información (_Data Leakage_) hacia el conjunto de Validación o Prueba (Test Data).
3. Los parámetros del escalador se guardarán en `models/scalers/` para posteriormente invertir la predicción (_Inverse Transform_) y reportar las métricas de error (RMSE, MAE) en dólares reales.
