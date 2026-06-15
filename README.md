# Crypto DCA Analyzer

Sistema de análisis cuantitativo de criptomonedas que produce un plan de inversión mensual mediante DCA (Dollar-Cost Averaging). El análisis completo y las alertas se generan y muestran directamente en el notebook — sin credenciales ni servicios externos de pago.

## ¿Qué hace?

El notebook `crypto_analysis.ipynb` ejecuta un pipeline completo de 71 celdas:

1. Descarga el **top-20 de criptos** por capitalización de mercado (CoinGecko) en tiempo real
2. Calcula **indicadores técnicos** sobre datos diarios y semanales: EMA, RSI, MACD, ATR, Bollinger, Fibonacci, SuperTrend, ADX
3. Analiza el **sentimiento de noticias** (4 feeds RSS, VADER) y el **Fear & Greed Index** (Alternative.me) sin API key
4. Detecta el **régimen de mercado** (BULL / NEUTRAL / BEAR) con un HMM gaussiano sobre BTC semanal
5. Genera un **score DCA 0–100** por activo con tres pilares: tendencia (55) + valor de entrada (35) + sentimiento (10)
6. Asigna **capital mensual** con HRP-CVaR (Riskfolio-Lib) solo a los top-5 altcoins por momentum, más el sleeve de convicción BTC/ETH
7. **Backtestea** la estrategia con walk-forward sin lookahead (~4–5 años de historia)
8. Calcula **señales de venta y rebalanceo**: SELL_SCORE técnico + desviación del peso objetivo (equal-weight 5%)
9. Imprime una **alerta mensual completa** con ranking, zonas de entrada, RSI y señal SuperTrend

---

## Instalación

```bash
git clone https://github.com/wilwil186/crypt-analysis.git
cd crypt-analysis
bash install_talib.sh      # compila TA-Lib nativo + instala dependencias base
source venv/bin/activate
pip install riskfolio-lib hmmlearn feedparser vaderSentiment
```

`install_talib.sh` instala: `numpy`, `pandas`, `plotly`, `mplfinance`, `yfinance`, `TA-Lib`, `prophet`, `scikit-learn`, `scipy`.

## Ejecución

```bash
source venv/bin/activate
jupyter notebook crypto_analysis.ipynb
```

Ejecuta las celdas **de arriba a abajo** — el notebook es stateful y orden-dependiente.

## Parámetros clave

```python
# Celda 03 — configuración global
PRIMARY           = 'BTC-USD'  # activo para el análisis técnico profundo (§2–12)
MAX_CRYPTO        = 20         # tamaño del universo (top-N por capitalización)
BUY_TH, SELL_TH  = 4, -4      # umbrales del score técnico diario
TARGET_WEIGHT     = 1/20       # peso objetivo por activo en §17 (igual-peso 5%)
REBAL_THRESHOLD   = 0.40       # umbral de rebalanceo (±40% del target)

# Celda 36 — parámetros DCA
MONTHLY_CAPITAL   = 200        # capital que inviertes cada mes (USD)
MAX_PER_ASSET     = 0.30       # tope máximo por activo individual
TOP_N             = 5          # máx. altcoins en el sleeve tendencia (por MOM26)
CONVICTION_CRYPTO = 0.30       # % fijo reservado a BTC + ETH
```

---

## Descripción de cada celda

### §0 — Título y presentación
| Celda | Tipo | Qué hace |
|-------|------|----------|
| 00 | Markdown | Portada del notebook |

### §1 — Setup y Configuración
| Celda | Tipo | Qué hace |
|-------|------|----------|
| 01 | Markdown | Encabezado de sección |
| 02 | Código | Importaciones: `numpy`, `pandas`, `yfinance`, `talib`, `plotly`, `scipy`, `sklearn`, `IPython.display` |
| 03 | Código | **`CONFIGURACIÓN GLOBAL`** — define `PRIMARY`, `INTERVAL`, `PERIOD`, universo dinámico top-20 desde CoinGecko (con fallback hardcodeado), `BUY_TH`/`SELL_TH`, `TARGET_WEIGHT`, `REBAL_THRESHOLD`, paleta `COL` |
| 04 | Código | `fetch_fng()` — consulta `api.alternative.me/fng` y expone `FNG_VALUE` (0–100) y `FNG_LABEL`; badge de color 🟢🟡🟠🔴 |

### §2 — Adquisición y Calidad de Datos
| Celda | Tipo | Qué hace |
|-------|------|----------|
| 05 | Markdown | Encabezado de sección |
| 06 | Código | `get_data(ticker)` — descarga OHLCV diario limpio via yfinance; descarga paralela para todo `UNIVERSE` en `DATA` |
| 07 | Código | Reporte de calidad de datos: retorno diario medio, volatilidad anualizada, días faltantes y fecha de inicio por activo |

### §3 — Motor de Indicadores Técnicos
| Celda | Tipo | Qué hace |
|-------|------|----------|
| 08 | Markdown | Descripción de los indicadores calculados |
| 09 | Código | `compute_indicators(d)` — añade EMA 4/9/20/50/200, SAR, ADX, PDI/MDI, RSI, MACD, Stochastic, MFI, CCI, ATR, Bollinger, OBV, CMF, VWAP; aplica a todos los activos en `INDI` |

### §4 — Indicadores Avanzados
| Celda | Tipo | Qué hace |
|-------|------|----------|
| 10 | Markdown | Descripción de Fibonacci, Volume Profile y CVD |
| 11 | Código | `fibonacci_levels(d)` — retrocesos automáticos sobre el swing de 180 días; `volume_profile(d)` — POC y Value Area; `cvd(d)` — Cumulative Volume Delta |
| 12 | Código | Gráfico interactivo: precio + Fibonacci + Volume Profile lateral + CVD sobre `PRIMARY` |

### §5 — Soporte y Resistencia Dinámicos
| Celda | Tipo | Qué hace |
|-------|------|----------|
| 13 | Markdown | Descripción del método de detección |
| 14 | Código | `support_resistance(d)` — swing points con `scipy.argrelextrema`, agrupados por proximidad (1.5%); gráfico con zonas S/R |

### §6 — Detección de Patrones Chartistas
| Celda | Tipo | Qué hace |
|-------|------|----------|
| 15 | Markdown | Descripción de los patrones detectados |
| 16 | Código | `detect_candle_patterns(d)` — 61 patrones TA-Lib en la última vela; `detect_structure_patterns(d)` — triángulos, doble techo/suelo, banderas |

### §7 — Sistema de Scoring
| Celda | Tipo | Qué hace |
|-------|------|----------|
| 17 | Markdown | Descripción del score y sus componentes |
| 18 | Código | `score_series(x)` — score técnico vectorizado: RSI, MACD, SMA cross, Bollinger, ADX, OBV; `label(score)` — COMPRAR / MANTENER / VENDER / ESPERAR |

### §8 — Backtesting de Señales
| Celda | Tipo | Qué hace |
|-------|------|----------|
| 19 | Markdown | Descripción de la metodología |
| 20 | Código | `backtest(x, score)` — long/flat con comisión 0.1%; compara vs buy & hold |
| 21 | Código | Gráfico de curva de equity y drawdown |

### §9 — Análisis de Correlaciones
| Celda | Tipo | Qué hace |
|-------|------|----------|
| 22 | Markdown | Descripción del análisis |
| 23 | Código | Matriz de correlación de retornos diarios; beta respecto a `PRIMARY`; heatmap interactivo |
| 24 | Código | Correlación rolling 30 días entre el activo más y menos correlacionado con `PRIMARY` |

### §10 — Modelos Predictivos
| Celda | Tipo | Qué hace |
|-------|------|----------|
| 25 | Markdown | Descripción de los dos modelos |
| 26 | Código | **Prophet** — forecast de precio a 30 días con intervalo de confianza 80% |
| 27 | Código | **GradientBoosting** — clasificador direccional a 5 días (RSI, MACD, ATR, retornos rezagados); accuracy + matriz de confusión |

### §16 — Sentimiento de Noticias
| Celda | Tipo | Qué hace |
|-------|------|----------|
| 28 | Markdown | Descripción del análisis RSS + VADER |
| 29 | Código | `fetch_news_sentiment(tickers)` — lee hasta 60 artículos de 4 feeds RSS (CoinTelegraph, CoinDesk, CryptoSlate, Decrypt); aplica VADER al título + resumen; devuelve `NEWS_SENTIMENT = {ticker: {score, n_articles, headlines}}`; tabla coloreada verde/rojo/gris + los 2 titulares más extremos por activo |

### §11 — Dashboard Multi-Activo
| Celda | Tipo | Qué hace |
|-------|------|----------|
| 30 | Markdown | Descripción del dashboard |
| 31 | Código | Aplica score + label + confianza a todos los activos; añade columna `Sentiment` (😀/😐/😰) desde `NEWS_SENTIMENT`; tabla estilizada con colores por recomendación |
| 32 | Código | Heatmap de barras con score por activo; líneas de umbral compra/venta |

### §12 — Conclusiones Accionables
| Celda | Tipo | Qué hace |
|-------|------|----------|
| 33 | Markdown | Encabezado |
| 34 | Código | Síntesis de `PRIMARY`: TP (precio + 2.5×ATR), SL (precio − 1.5×ATR), ratio R/R; recomendación con contexto de mercado |

---

### §13 — Motor DCA (producto principal)
| Celda | Tipo | Qué hace |
|-------|------|----------|
| 35 | Markdown | Introducción al motor DCA de largo plazo y filosofía del score |
| 36 | Código | **Parámetros DCA**: `MONTHLY_CAPITAL`, `MAX_PER_ASSET`, `TOP_N`, `WK_PERIOD`; `get_weekly()` descarga datos semanales (`1wk`) de 5 años en `WK` |
| 37 | Código | `supertrend_signal(h,l,c)` — SuperTrend ATR×3 (OctoBot-inspired); `lt_features(d)` — indicadores semanales LP; `dca_score(x, ticker)` — score DCA 0–100 con **3 pilares**: tendencia 0–55 + valor entrada 0–35 + sentimiento 0–10; penalización FNG > 80 (−15 en entrada); genera `WKI` y `DCA` |

### §12b — Régimen de Mercado (HMM)
| Celda | Tipo | Qué hace |
|-------|------|----------|
| 38 | Markdown | Descripción del modelo HMM de 3 estados |
| 39 | Código | `GaussianHMM(n_components=3)` sobre BTC-USD semanal; features: retorno 4 semanas, volatilidad rolling 8 semanas, RSI semanal; etiqueta estados BULL/NEUTRAL/BEAR por retorno medio; expone `REGIME_NOW`; gráfico Plotly con precio coloreado por régimen |

### §13 (cont.) — Asignación DCA
| Celda | Tipo | Qué hace |
|-------|------|----------|
| 40 | Markdown | Descripción del filtro de elegibilidad |
| 41 | Código | Filtra elegibles (precio > SMA40, `trend_quality ≥ 35`); rankea altcoins por MOM26 y conserva los **top-`TOP_N`** (BTC/ETH excluidos del ranking); calcula pesos con **HRP-CVaR** (Riskfolio-Lib) sobre retornos semanales alineados (union+ffill); fallback a score-proporcional; tope `MAX_PER_ASSET`; tabla `alloc` |
| 42 | Código | Gráfico: dona de pesos + barras de score DCA |
| 43 | Markdown | Descripción de los niveles de entrada |
| 44 | Código | Zonas de entrada por activo: SMA30 (sobreponderar), SMA40 (oportunidad fuerte), SMA40×1.25 (euforia) |
| 45 | Markdown | Descripción de la validación DCA vs Lump Sum |
| 46 | Código | `dca_sim(close, amount)` — simula DCA semanal y compara vs inversión única (Lump Sum) |
| 47 | Markdown | Recomendación final de asignación |
| 48 | Código | Tabla HTML con el plan DCA: activo, USD asignados, precio, niveles SMA, señal SuperTrend |

### §14 — Optimización de Rentabilidad
| Celda | Tipo | Qué hace |
|-------|------|----------|
| 49 | Markdown | Introducción a las mejoras de optimización |
| 50 | Markdown | Encabezado §14.1 |
| 51 | Código | `perf_stats(close)` — CAGR, volatilidad, Sharpe, Sortino, MaxDrawdown, Calmar; tabla comparativa de todos los activos |
| 52 | Código | Mapa riesgo-retorno: scatter CAGR vs volatilidad, tamaño del punto = Sharpe |
| 53 | Markdown | Encabezado §14.2 — sleeve de convicción |
| 54 | Código | `CONVICTION_CRYPTO = 0.30` (BTC+ETH fijo); aplica `REGIME_NOW`: BEAR=solo convicción, NEUTRAL=tendencia al 50%, BULL=sin cambios; aplica reducción FNG > 80 (tendencia al 60%); combina en `final_w` y `final_alloc` |
| 55 | Markdown | Encabezado §14.3 — backtest walk-forward |
| 56 | Código | Matriz `PX` (union+ffill); `weights_at(t, mode)` — pesos en cada fecha sin lookahead (modos: `btc`, `equal`, `conviction`, `hrp`, `strategy`); `run_dca(mode)` — simula DCA semana a semana |
| 57 | Código | Gráfico de curvas de equity; IRR anual y MaxDrawdown |
| 58 | Markdown | Encabezado §14.4 — plan final |
| 59 | Código | Tabla HTML del plan optimizado con IRR, retorno total, MaxDD, múltiplo |

### §15 — Sistema de Alertas Semanales
| Celda | Tipo | Qué hace |
|-------|------|----------|
| 60 | Markdown | Introducción a la sección final |
| 61 | Markdown | Encabezado §15.1 |
| 62 | Código | `final_w2` (convicción + tendencia); `sleeve_of(tk)`; tabla `alloc2` con distribución final |
| 63 | Markdown | Encabezado §15.2 — re-validación walk-forward |
| 64 | Código | Walk-forward v2: estrategia completa vs solo-convicción vs equal-weight vs solo-BTC; tabla con Sharpe y Calmar |
| 65 | Código | Gráfico comparativo de las 4 curvas de valor acumulado |
| 66 | Markdown | Encabezado §15.3 — alerta mensual |
| 67 | Código | `monthly_alert(plan_weights)` — recorre todos los activos del universo; clasifica por zona (euforia / pullback / oportunidad / normal / fuera de tendencia); devuelve `alert` ordenada por urgencia |
| 68 | Código | **Celda final de alerta** — imprime badge FNG + plan DCA mensual completo: cartera con % por activo, ranking top-20 con barra de score visual, activos fuera de tendencia, activos en vigilancia, instrucciones de acción |

### §17 — Señales de Venta y Rebalanceo
| Celda | Tipo | Qué hace |
|-------|------|----------|
| 69 | Markdown | Descripción de las dos capas de señales |
| 70 | Código | **Capa 1** `sell_score(tk)` (0–100): +25 EMA bajista (Close < EMA50 < EMA200), +20 RSI > 75, +15 MACD < señal con histograma decreciendo 3 velas, +15 precio > BBu, +10 ADX > 30 con MDI > PDI, +15 SuperTrend semanal −1. **Capa 2** rebalanceo hipotético: simula portafolio igual-peso desde hace 52 semanas, calcula desviación actual vs `TARGET_WEIGHT`. **Tabla consolidada**: Activo \| Precio \| SELL_SCORE \| Señal Técnica \| Peso actual % \| Desviación % \| DCA Score \| Acción (⚫ SALIR / 🔴 REDUCIR FUERTE / 🟠 REDUCIR PARCIAL / 🟢 AUMENTAR / 🟡 MANTENER). Gráfico scatter SELL_SCORE vs Desviación con umbrales. Resumen de texto por categoría |

---

## Indicadores utilizados

| Indicador | Uso |
|---|---|
| EMA 4 / 9 / 20 / 50 / 200 (diario) | Tendencia y cruces de media |
| SMA 10 / 30 / 40 (semanal) | Filtro de elegibilidad DCA y niveles de entrada |
| RSI (14) | Momentum, sobrecompra/sobreventa, señal de venta |
| MACD (12/26/9) | Confirmación de tendencia, divergencia, señal de venta |
| ATR (14) | Volatilidad, niveles de stop, SuperTrend |
| Bandas de Bollinger | Extensión de precio, señal de venta (sobre BBu) |
| ADX / PDI / MDI | Fuerza y dirección de tendencia; señal de venta (MDI > PDI) |
| SuperTrend (ATR×3, período 10) | Dirección tendencial diaria y semanal (OctoBot-inspired) |
| Stochastic / MFI / CCI / Williams %R | Oscilladores de momentum secundarios |
| OBV / CMF / CVD | Order flow y presión compradora/vendedora |
| Volume Profile (POC/VAH/VAL) | Zonas de valor y precio de control |
| Fibonacci (automático) | Retrocesos sobre el swing de 180 días |
| SAR Parabólico | Trailing stop dinámico |
| Prophet | Forecast de precio a 30 días con incertidumbre |
| GradientBoosting | Clasificador direccional a 5 días |
| HMM Gaussiano (3 estados) | Régimen de mercado BULL/NEUTRAL/BEAR sobre BTC semanal |
| HRP-CVaR (Riskfolio-Lib) | Pesos óptimos del sleeve tendencia por Hierarchical Risk Parity |
| VADER Sentiment | Score de sentimiento (−1 a +1) sobre noticias RSS cripto |
| Fear & Greed Index | Sentimiento agregado del mercado (0–100, Alternative.me) |

## Score DCA — cómo se calcula

```
Score DCA (0–100) = Tendencia (0–55) + Valor de entrada (0–35) + Sentimiento (0–10)

Tendencia (máx 55):
  +20  precio > SMA40 semanal (uptrend confirmado)
  +15  SMA10 > SMA30 > SMA40  (alineación alcista perfecta)
  +15  MOM26 > 0              (momentum positivo a 6 meses)
  +5   MACD > señal           (momentum semanal al alza)
  +5   SuperTrend alcista ↑   (bonus, cap en 55)

Valor de entrada (máx 35):
  +20 / +12 / +4   precio cerca / algo extendido / muy extendido vs SMA10
  +7 / +3          RSI < 65 / RSI < 75
  +8 / +5 / +2     drawdown desde máximo en zona óptima / moderada / severa
  −15              penalización si FNG > 80 (euforia extrema)

Sentimiento (0–10):
  +10  VADER score > 0.10 (positivo)
  +5   VADER score 0 a 0.10 (levemente positivo)
  +2   VADER score −0.10 a 0 (levemente negativo)
  +0   VADER score < −0.10 (negativo)
```

## SELL_SCORE — señales de salida

```
SELL_SCORE (0–100) = suma de señales técnicas bajistas diarias + ST semanal

  +25  Close < EMA50 < EMA200 (downtrend confirmado)
  +20  RSI > 75 (sobrecompra extrema)
  +15  MACD < señal Y histograma decreciendo 3 velas consecutivas
  +15  precio > BBu (fuera de banda superior Bollinger)
  +10  ADX > 30 Y MDI > PDI (tendencia bajista fuerte)
  +15  SuperTrend semanal = −1

Acciones por umbral:
  ⚫ SALIR           → SELL_SCORE > 80
  🔴 REDUCIR FUERTE  → SELL_SCORE > 70 O desviación peso > 60%
  🟠 REDUCIR PARCIAL → SELL_SCORE > 45 O desviación peso > 40%
  🟢 AUMENTAR        → DCA Score ≥ 55 Y desviación peso < −40%
  🟡 MANTENER        → sin señales relevantes
```

## Notas

- Los datos se descargan en tiempo real: CoinGecko (universo), Yahoo Finance (precios), Alternative.me (FNG), feeds RSS (noticias)
- Todas las fuentes tienen fallback si la API falla — el notebook siempre termina
- Los archivos `.html` generados están en `.gitignore`
- El notebook se commitea con sus outputs para que el ranking sea visible directamente en GitHub
- **Educativo — no es asesoría financiera**
