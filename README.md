# Crypto DCA Analyzer

Sistema de análisis cuantitativo de criptomonedas que produce un plan de inversión mensual mediante DCA (Dollar-Cost Averaging) y lo envía automáticamente a Telegram.

## ¿Qué hace?

El notebook `crypto_analysis.ipynb` ejecuta un pipeline completo:

1. **Descarga el top-20 de criptos** por capitalización de mercado (CoinGecko) en tiempo real
2. **Calcula indicadores técnicos** sobre datos semanales: SMA, RSI, MACD, ATR, Fibonacci, SuperTrend
3. **Genera un score DCA 0–100** por activo con dos pilares: calidad de tendencia + valor de entrada
4. **Asigna capital mensual** solo a activos en uptrend confirmado (precio > SMA40 semanal)
5. **Backtestea** la estrategia con walk-forward sin lookahead (~4–5 años de historia)
6. **Imprime una alerta mensual** con el ranking de las 20 criptos, zonas de entrada, RSI y señal SuperTrend

## Estructura del pipeline

| Sección | Qué hace |
|---|---|
| §1 Setup | Universo dinámico top-20 desde CoinGecko |
| §2–6 | Indicadores técnicos, Fibonacci, soporte/resistencia, patrones de velas |
| §7–8 | Score de confianza + backtest con fees |
| §9–11 | Correlaciones, Prophet, clasificador GradientBoosting |
| §13 Motor DCA | Elegibilidad, asignación semanal, zonas de entrada |
| §14 Optimización | Métricas ajustadas por riesgo, sleeve de convicción BTC/ETH, walk-forward |
| §15 Alertas | `monthly_alert()` — genera el reporte de todas las 20 criptos |
| §16 Alerta | Imprime el plan DCA mensual completo en el notebook |

## Instalación

```bash
git clone <este-repo>
cd crypto-analysis
bash install_talib.sh          # instala TA-Lib nativo + dependencias Python
source venv/bin/activate
```

`install_talib.sh` compila TA-Lib desde fuente e instala: `numpy`, `pandas`, `plotly`, `mplfinance`, `yfinance`, `TA-Lib`, `prophet`, `scikit-learn`, `scipy`.

## Ejecución

```bash
source venv/bin/activate
jupyter notebook crypto_analysis.ipynb
```

Ejecuta las celdas de arriba a abajo. El notebook es **stateful y orden-dependiente**: `UNIVERSE` y `CLASE` se definen en §1 y son consumidos por todo lo demás.

## Parámetros clave

En la celda `CONFIGURACIÓN GLOBAL` (§1) y en la celda de parámetros DCA (§13):

```python
PRIMARY          = 'BTC-USD'   # activo para análisis técnico profundo
MONTHLY_CAPITAL  = 200         # capital que inviertes cada mes (USD)
MAX_CRYPTO       = 20          # tamaño del universo (top-N por mkt cap)
CONVICTION_CRYPTO = 0.30       # % fijo reservado a BTC+ETH (sleeve convicción)
MAX_PER_ASSET    = 0.30        # tope máximo por activo
```

## Alerta mensual (última celda)

La última celda imprime el plan DCA completo directamente en el notebook:

- **Tu cartera este mes**: activos elegibles con % de aporte, precio, RSI, SuperTrend (↑/↓) y distancia a SMA40
- **Ranking top-20**: barra de score visual, señal SuperTrend y RSI para cada cripto analizada
- **Fuera de tendencia**: criptos que perdieron su SMA40 (no acumular)
- **En vigilancia**: criptos en mejora que aún no califican

## Indicadores utilizados

| Indicador | Uso |
|---|---|
| SMA10 / SMA30 / SMA40 | Tendencia de corto, medio y largo plazo |
| RSI (14, semanal) | Momentum y zonas de sobrecompra/sobreventa |
| MACD (12/26/9, semanal) | Confirmación de tendencia |
| ATR (14, semanal) | Volatilidad y niveles de stop |
| SuperTrend (ATR×3, período 10) | Filtro de dirección tendencial (inspirado en OctoBot) |
| Fibonacci | Zonas de retroceso automáticas |
| Prophet + GradientBoosting | Modelos predictivos direccionales |

## Notas

- Los datos de mercado se descargan en tiempo real al ejecutar: CoinGecko (universo) y Yahoo Finance (precios)
- Ambas fuentes tienen fallback a cestas hardcodeadas si la API falla
- Los archivos `.html` generados están en `.gitignore`
- **Educativo — no es asesoría financiera**
