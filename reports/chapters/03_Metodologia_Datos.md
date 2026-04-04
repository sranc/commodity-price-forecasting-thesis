# Capítulo: Datos y Metodología de Extracción

## 1. Proceso de Adquisición de Datos
Para garantizar la reproducibilidad y escalabilidad de la investigación, el proceso de obtención de datos se automatizó mediante un flujo de ingeniería de datos en Python. Se extrajeron series de tiempo continuas desde dos de las fuentes financieras más robustas y consolidadas del sector: **Yahoo Finance** para información de cotización de mercado (precios diarios) y el **Federal Reserve Economic Data (FRED)** para indicadores macroeconómicos. El periodo de estudio abarca datos estructurados a partir del 1 de Julio de 2015.

## 2. Definición de Variables

### 2.1 Variables Endógenas (Variables Objetivo)
Las variables objetivo corresponden a los precios internacionales de cuatro *commodities* principales: **Oro, Plata, Cobre y Zinc**. Estos datos fueron extraídos con una frecuencia diaria en base a los días de negociación (*Trading Days*) bajo el estándar financiero OHLCV. 

La estructura OHLCV captura la dinámica intra-diaria de los mercados financieros y se define de la siguiente manera:
*   **Open (Apertura):** El precio exacto al que comenzó a cotizar el metal en la apertura de la bolsa de valores para ese día específico. Se expresa en Dólares Estadounidenses (USD).
*   **High (Máximo):** El precio más alto que logró alcanzar el metal durante la sesión de cotización de ese día. Refleja los picos de demanda o volatilidad alcista.
*   **Low (Mínimo):** El precio más bajo cotizado durante la sesión.
*   **Close (Cierre):** El último precio registrado al finalizar la jornada bursátil. Es el dato más vital y ampliamente utilizado para modelos de *Machine Learning* y análisis econométrico, ya que representa el consenso final del mercado para ese día.
*   **Volume (Volumen):** La cantidad física o el número de contratos de derivados que cambiaron de manos en dicho día. Representa la liquidez y la fuerza del mercado detrás del movimiento de precios.

### 2.2 Variables Exógenas 
Se extrajeron predictores sistémicos separados en dos dimensiones operativas: **Mercado** y **Macroeconomía**.

**Dimensión de Mercado (Frecuencia Diaria):**
Obtenidos también mediante Yahoo Finance, actúan como termómetros de control del estrés global.
*   **Petróleo WTI (Crude Oil):** Costo energético global en USD por barril.
*   **Índice Dólar (DXY):** Un índice promedio ponderado que mide el valor relativo del Dólar Estadounidense frente a una canasta de monedas de primer nivel.

**Dimensión Macroeconómica (Frecuencia Mensual):**
Estos datos sistémicos de la economía de Estados Unidos y China fueron extraídos puramente mediante la API de FRED, preservando su frecuencia oficial.
*   **Inflación (IPC):** Índice de Precios al Consumidor.
*   **Producción Industrial:** Indicador puro de la manufactura nacional.
*   **Indicador Líder OECD (Composite Leading Indicator):** Sustituto metodológico del Producto Interno Bruto (PIB).

## 3. Justificación Metodológica: OECD CLI vs. PIB (GDP)

Tradicionalmente, el Producto Interno Bruto (PIB) se utiliza como la máxima medida del crecimiento de la economía de un país. Sin embargo, su incursión en modelos predictivos de frecuencia diaria/semanal presenta serios obstáculos temporales: el PIB se reporta oficialmente **una vez cada tres meses (Trimestral)** y además sufre de un grave desfase de publicación. Intentar inyectar el PIB trimestral a una red neuronal diaria para predecir precios de corto plazo introduce ruido (por la interpolación) y un severo riesgo temporal (asumir que en Enero el modelo ya conocía el PIB que recién el gobierno publicaría en Marzo).

Para solucionar este nudo metodológico, se decidió sustituir el PIB por el **Composite Leading Indicator (CLI)** de la Organización para la Cooperación y el Desarrollo Económicos (OECD).

El `oecd_cli` es un índice adelantado diseñado sistemáticamente para proveer señales tempranas sobre los puntos de inflexión de la actividad económica, fluctuando alrededor de su potencial a largo plazo (cuyo valor base de equilibrio es 100). Posee dos ventajas determinantes sobre el PIB en la ciencia de datos financieros:
1.  **Frecuencia Mensual:** Ofrece una resolución mucho más fina y cercana al mercado bursátil, permitiendo ser anclada al inicio de cada mes de actividad financiera.
2.  **Capacidad Predictiva (Leading):** A diferencia del PIB que es un indicador "rezagado" (cuenta lo que ya pasó), el índice compuesto compila encuestas de consumo, permisos de manufactura e indicadores de bolsa para alertar sobre la contracción o expansión económica con **6 a 9 meses de anticipación**. Por lo tanto, un índice mayor a 100 informa al modelo matemático algoritmicamente sobre escenarios expansivos que aumentarán la futura presión de compra sobre metales estratégicos como el Cobre o Zinc.
