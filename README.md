# Crypto DCA Analyzer

Sistema de análisis cuantitativo de criptomonedas que produce un plan de inversión mensual mediante DCA (Dollar-Cost Averaging). El análisis completo y la alerta mensual se generan y muestran directamente en el notebook — sin dependencias externas ni credenciales.

## ¿Qué hace?

El notebook `crypto_analysis.ipynb` ejecuta un pipeline completo de 66 celdas:

1. Descarga el **top-20 de criptos** por capitalización de mercado (CoinGecko) en tiempo real
2. Calcula **indicadores técnicos** sobre datos diarios y semanales: SMA, RSI, MACD, ATR, Fibonacci, SuperTrend
3. Genera un **score DCA 0–100** por activo con dos pilares: calidad de tendencia + valor de entrada
4. Asigna **capital mensual** solo a activos en uptrend confirmado (precio > SMA40 semanal)
5. **Backtestea** la estrategia con walk-forward sin lookahead (~4–5 años de historia)
6. Imprime una **alerta mensual completa** con ranking, zonas de entrada, RSI y señal SuperTrend

---

## Instalación

```bash
git clone https://github.com/wilwil186/crypt-analysis.git
cd crypt-analysis
bash install_talib.sh      # compila TA-Lib nativo + instala todas las dependencias Python
source venv/bin/activate
```

`install_talib.sh` instala: `numpy`, `pandas`, `plotly`, `mplfinance`, `yfinance`, `TA-Lib`, `prophet`, `scikit-learn`, `scipy`.

## Ejecución

```bash
source venv/bin/activate
jupyter notebook crypto_analysis.ipynb
```

Ejecuta las celdas **de arriba a abajo** — el notebook es stateful y orden-dependiente. Las variables `UNIVERSE` y `CLASE` se definen en la celda 03 y son consumidas por todo lo demás.

## Parámetros clave

En la celda de `CONFIGURACIÓN GLOBAL` (celda 03) y en parámetros DCA (celda 33):

```python
PRIMARY           = 'BTC-USD'  # activo para el análisis técnico profundo (§2–12)
MONTHLY_CAPITAL   = 200        # capital que inviertes cada mes (USD)
MAX_CRYPTO        = 20         # tamaño del universo (top-N por capitalización)
CONVICTION_CRYPTO = 0.30       # % fijo reservado a BTC + ETH (sleeve de convicción)
MAX_PER_ASSET     = 0.30       # tope máximo por activo individual
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
| 03 | Código | **`CONFIGURACIÓN GLOBAL`** — define `PRIMARY`, `INTERVAL`, `PERIOD`, universo dinámico de top-20 cryptos desde CoinGecko (con fallback hardcodeado), `BUY_TH`/`SELL_TH`, paleta de colores `COL` |

### §2 — Adquisición y Calidad de Datos
| Celda | Tipo | Qué hace |
|-------|------|----------|
| 04 | Markdown | Encabezado de sección |
| 05 | Código | `get_data(ticker)` — descarga OHLCV diario limpio via yfinance; descarga paralela para todo `UNIVERSE` en `DATA` |
| 06 | Código | Reporte de calidad de datos: retorno diario medio, volatilidad anualizada, días faltantes y fecha de inicio por activo |

### §3 — Motor de Indicadores Técnicos
| Celda | Tipo | Qué hace |
|-------|------|----------|
| 07 | Markdown | Descripción de los indicadores calculados |
| 08 | Código | `compute_indicators(d)` — añade al DataFrame: SMA20/50/200, EMA12/26, RSI(14), MACD, Bandas de Bollinger, ATR, OBV, VWAP, Stochastic, CCI, Williams %R, ADX; aplica a todos los activos en `INDI` |

### §4 — Indicadores Avanzados
| Celda | Tipo | Qué hace |
|-------|------|----------|
| 09 | Markdown | Descripción de Fibonacci, Volume Profile y CVD |
| 10 | Código | `fibonacci_levels(d)` — retrocesos automáticos sobre el swing alto/bajo de los últimos 180 días; `volume_profile(d)` — POC y Value Area (VAH/VAL) con histograma de volumen por precio; `cvd(d)` — Cumulative Volume Delta como proxy de order flow |
| 11 | Código | Gráfico interactivo (Plotly): precio + Fibonacci + Volume Profile lateral + CVD sobre el activo `PRIMARY` |

### §5 — Soporte y Resistencia Dinámicos
| Celda | Tipo | Qué hace |
|-------|------|----------|
| 12 | Markdown | Descripción del método de detección |
| 13 | Código | `support_resistance(d)` — detecta swing points con `scipy.argrelextrema`, los agrupa por proximidad (tolerancia 1.5%) y devuelve los niveles más relevantes; gráfico con zonas S/R sobre `PRIMARY` |

### §6 — Detección de Patrones Chartistas
| Celda | Tipo | Qué hace |
|-------|------|----------|
| 14 | Markdown | Descripción de los patrones detectados |
| 15 | Código | `detect_candle_patterns(d)` — escanea 61 patrones de velas de TA-Lib activos en la última vela; `detect_structure_patterns(d)` — detecta triángulos, doble techo/suelo, banderas; imprime resumen para `PRIMARY` |

### §7 — Sistema de Scoring
| Celda | Tipo | Qué hace |
|-------|------|----------|
| 16 | Markdown | Descripción del score y sus componentes |
| 17 | Código | `score_series(x)` — score técnico vectorizado (Serie temporal): pondera RSI, MACD, SMA cross, Bollinger, ADX, OBV; `label(score)` — traduce score a recomendación (COMPRAR / MANTENER / VENDER / ESPERAR); aplica a `PRIMARY` |

### §8 — Backtesting de Señales
| Celda | Tipo | Qué hace |
|-------|------|----------|
| 18 | Markdown | Descripción de la metodología de backtest |
| 19 | Código | `backtest(x, score)` — estrategia long/flat: entra cuando `score >= BUY_TH`, sale cuando `score <= SELL_TH`; aplica comisión 0.1% por operación; compara vs buy & hold |
| 20 | Código | Gráfico de curva de equity y drawdown del backtest vs buy & hold |

### §9 — Análisis de Correlaciones
| Celda | Tipo | Qué hace |
|-------|------|----------|
| 21 | Markdown | Descripción del análisis |
| 22 | Código | Matriz de correlación de retornos diarios entre todos los activos; beta respecto a `PRIMARY`; heatmap interactivo |
| 23 | Código | Correlación rolling 30 días entre el activo más y menos correlacionado con `PRIMARY` |

### §10 — Modelos Predictivos
| Celda | Tipo | Qué hace |
|-------|------|----------|
| 24 | Markdown | Descripción de los dos modelos |
| 25 | Código | **Prophet** — forecast de precio a 30 días con intervalo de confianza 80%; gráfico con componentes de tendencia y estacionalidad |
| 26 | Código | **GradientBoosting** — clasificador direccional (sube / baja a 5 días): features = RSI, MACD, ATR, retornos rezagados, Bollinger width; muestra accuracy, matriz de confusión y predicción para la próxima semana |

### §11 — Dashboard Multi-Activo
| Celda | Tipo | Qué hace |
|-------|------|----------|
| 27 | Markdown | Descripción del dashboard |
| 28 | Código | Aplica el pipeline completo (score + label + confianza) a todos los activos del universo; construye tabla resumen `dash` |
| 29 | Código | Heatmap de barras con score por activo (verde = COMPRAR, rojo = VENDER); tabla HTML con recomendaciones y métricas |

### §12 — Conclusiones Accionables
| Celda | Tipo | Qué hace |
|-------|------|----------|
| 30 | Markdown | Encabezado |
| 31 | Código | Síntesis de `PRIMARY`: calcula TP (precio + 2.5×ATR), SL (precio − 1.5×ATR), ratio R/R; imprime recomendación con contexto de mercado |

### §12b — Régimen de Mercado (HMM)
| Celda | Tipo | Qué hace |
|-------|------|----------|
| 37 | Markdown | Descripción del modelo de régimen de mercado |
| 38 | Código | Entrena un `GaussianHMM` de 3 estados sobre BTC-USD semanal con features: retorno 4 semanas, volatilidad rolling 8 semanas, RSI semanal. Etiqueta los estados como BULL/NEUTRAL/BEAR por retorno medio histórico. Expone `REGIME_NOW`. Muestra gráfico Plotly con precio BTC coloreado por régimen |

---

### §13 — Motor DCA (producto principal)
| Celda | Tipo | Qué hace |
|-------|------|----------|
| 32 | Markdown | Introducción al motor DCA de largo plazo |
| 33 | Código | **Parámetros DCA**: `MONTHLY_CAPITAL`, `MAX_PER_ASSET`, `WK_PERIOD`; descarga datos **semanales** (`1wk`) de 5 años para todo el universo en `WK` |
| 34 | Código | `supertrend_signal(h,l,c)` — SuperTrend basado en ATR×factor (inspirado en OctoBot); `lt_features(d)` — indicadores semanales LP: SMA10/30/40, RSI, MACD, MOM26/52, ATR, DDhigh, SuperTrend; `dca_score(x)` — score DCA 0–100 (tendencia 0–60 + valor entrada 0–40 + bonus ST); aplica a todo `WK` generando `WKI` y `DCA` |
| 35 | Markdown | Descripción de la asignación de capital |
| 36 | Código | Filtra activos elegibles (precio > SMA40 + `trend_quality ≥ 35`); calcula pesos con **HRP-CVaR** (Riskfolio-Lib) usando retornos semanales alineados; fallback a score-proporcional; tope `MAX_PER_ASSET`; tabla `alloc` con USD asignados este mes |
| 39 | Código | Gráfico de asignación: dona de pesos + barras de score DCA por activo |
| 40 | Markdown | Descripción de los niveles de entrada |
| 39 | Código | Calcula zonas de entrada por activo: SMA30 (sobreponderar), SMA40 (oportunidad fuerte), SMA40×1.25 (euforia) |
| 40 | Markdown | Descripción de la validación DCA vs Lump Sum |
| 41 | Código | `dca_sim(close, amount)` — simula DCA aportando cantidad fija cada semana; compara vs inversión única (Lump Sum) sobre `PRIMARY` y la cesta diversificada |
| 42 | Markdown | Recomendación final de asignación |
| 43 | Código | Tabla HTML interactiva con el plan DCA: activo, aporte en USD, precio, niveles SMA30/SMA40, señal SuperTrend, estado de zona |

### §14 — Optimización de Rentabilidad
| Celda | Tipo | Qué hace |
|-------|------|----------|
| 44 | Markdown | Introducción a las tres mejoras de optimización |
| 45 | Markdown | Encabezado §14.1 |
| 46 | Código | `perf_stats(close)` — métricas ajustadas por riesgo: CAGR, volatilidad, Sharpe, Sortino, MaxDrawdown, Calmar; tabla comparativa de todos los activos |
| 47 | Código | Mapa riesgo-retorno: scatter CAGR vs volatilidad, tamaño del punto = Sharpe |
| 48 | Markdown | Encabezado §14.2 — sleeve de convicción |
| 51 | Código | Define `CONVICTION_CRYPTO = 0.30` (BTC + ETH siempre); aplica `REGIME_NOW`: BEAR=solo convicción, NEUTRAL=tendencia al 50%, BULL=sin cambios; combina en `final_w` y `final_alloc` |
| 50 | Markdown | Encabezado §14.3 — backtest walk-forward |
| 51 | Código | Construye `PX` (matriz de precios semanal alineada con unión de fechas + ffill); `weights_at(t, mode)` — calcula pesos en cada fecha sin lookahead; `run_dca(mode)` — simula DCA semana a semana; compara estrategia convicción+tendencia vs equal-weight vs solo-BTC |
| 52 | Código | Gráfico de curvas de equity de las tres estrategias; imprime IRR anual y MaxDrawdown |
| 53 | Markdown | Encabezado §14.4 — plan final |
| 54 | Código | Tabla HTML final del plan optimizado con métricas del backtest: IRR, retorno total, MaxDD, múltiplo |

### §15 — Validación final y Alerta Mensual
| Celda | Tipo | Qué hace |
|-------|------|----------|
| 55 | Markdown | Introducción a la sección final |
| 56 | Markdown | Encabezado §15.1 |
| 57 | Código | Construye `final_w2` (pesos finales = convicción BTC/ETH + tendencia resto); `sleeve_of(tk)` para etiquetar cada activo; tabla `alloc2` |
| 58 | Markdown | Encabezado §15.2 — re-validación walk-forward |
| 59 | Código | Re-ejecuta walk-forward comparando 4 variantes: estrategia completa, solo convicción (BTC+ETH), equal-weight, solo BTC; tabla de métricas con Sharpe y Calmar |
| 60 | Código | Gráfico comparativo de las 4 curvas de valor acumulado |
| 61 | Markdown | Encabezado §15.3 — alerta mensual |
| 62 | Código | `monthly_alert(plan_weights)` — recorre **todos los activos del universo** (no solo los del plan); calcula zona de precio (euforia / pullback / oportunidad / normal / fuera), distancia a SMA30/SMA40, RSI, SuperTrend; devuelve `alert` con las 20 criptos ordenadas por urgencia |
| 63 | Código | **Celda final** — imprime el plan DCA mensual completo: cartera del mes con % de aporte por activo, ranking top-20 con barra de score visual, sección de activos fuera de tendencia, sección en vigilancia, e instrucciones de acción |

---

## Indicadores utilizados

| Indicador | Uso |
|---|---|
| SMA 10 / 30 / 40 (semanal) | Tendencia de corto, medio y largo plazo; filtro de elegibilidad DCA |
| SMA 20 / 50 / 200 (diario) | Análisis técnico del activo principal |
| RSI (14) | Momentum y zonas de sobrecompra/sobreventa |
| MACD (12/26/9) | Confirmación de tendencia y señales de cruce |
| ATR (14) | Volatilidad, niveles de stop y SuperTrend |
| Bandas de Bollinger | Compresión/expansión de volatilidad |
| SuperTrend (ATR×3, período 10) | Filtro de dirección tendencial (inspirado en OctoBot) |
| Stochastic RSI | Señales de sobrecompra/sobreventa de segundo orden |
| ADX | Fuerza de la tendencia |
| OBV / CVD | Order flow y presión compradora/vendedora |
| Volume Profile (POC/VAH/VAL) | Zonas de valor y precio de control |
| Fibonacci (automático) | Retrocesos sobre el swing reciente |
| Prophet | Forecast de precio a 30 días con incertidumbre |
| GradientBoosting | Clasificador direccional a 5 días |
| HMM Gaussiano (3 estados) | Régimen de mercado BULL/NEUTRAL/BEAR sobre BTC semanal |
| HRP-CVaR (Riskfolio-Lib) | Pesos óptimos del sleeve de tendencia por Hierarchical Risk Parity |

## Score DCA — cómo se calcula

```
Score DCA (0–100) = Tendencia (0–60) + Valor de entrada (0–40) + Bonus SuperTrend

Tendencia:
  +20  precio > SMA40 semanal (uptrend confirmado)
  +15  SMA10 > SMA30 > SMA40  (alineación alcista perfecta)
  +15  MOM26 > 0              (momentum positivo a 6 meses)
  +10  MACD > señal           (momentum semanal al alza)
  +5   SuperTrend alcista ↑   (bonus)

Valor de entrada:
  +20 / +12 / +4   precio cerca / algo extendido / muy extendido vs SMA10
  +10 / +5         RSI < 65 / RSI < 75
  +10 / +6 / +3    drawdown desde máximo en zona óptima (-35% a -8%) / moderada / severa
```

## Notas

- Los datos se descargan en tiempo real al ejecutar: CoinGecko (universo) y Yahoo Finance (precios + histórico)
- Ambas fuentes tienen fallback a cestas hardcodeadas si la API falla
- Los archivos `.html` generados están en `.gitignore`
- El notebook se ejecuta y commitea con sus outputs para que el ranking y las predicciones sean visibles directamente en GitHub
- **Educativo — no es asesoría financiera**
