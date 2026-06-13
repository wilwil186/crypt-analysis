import yfinance as yf
import pandas as pd
import numpy as np
import pandas_ta as ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

print("Opciones de temporalidad:")
print("1. 1 dia")
print("2. 12 horas")
print("3. 6 horas")
print("4. 4 horas")
print("5. 1 hora")
print("6. 30 min")
print("7. 15 min")
print("8. 5 min")
print("9. 1 min")

choice = "6"  # Default to 30 min

timeframe_options = {
    "1": ("1d", "1mo"),
    "2": ("1h", "1d"),
    "3": ("1h", "1d"),
    "4": ("1h", "1d"),
    "5": ("1h", "7d"),
    "6": ("30m", "7d"),
    "7": ("15m", "7d"),
    "8": ("5m", "7d"),
    "9": ("1m", "7d")
}

interval, period = timeframe_options.get(choice, ("30m", "7d"))
timeframe = "30 MINUTOS" if choice == "6" else "OTRO"

print(f"Descargando datos de BTC-USD ({interval})...")
data = yf.download("BTC-USD", period=period, interval=interval)

if data is None or data.empty:
    print("Error: No data downloaded.")
    exit(1)

# Calculate indicators using pandas-ta
data['EMA4'] = ta.ema(data['Close'], length=4)
data['EMA20'] = ta.ema(data['Close'], length=20)
data['EMA25'] = ta.ema(data['Close'], length=25)
data['EMA50'] = ta.ema(data['Close'], length=50)
data['EMA200'] = ta.ema(data['Close'], length=200)
data['RSI'] = ta.rsi(data['Close'], length=14)
data['RSI5'] = ta.rsi(data['Close'], length=5)
macd = ta.macd(data['Close'])
if macd is not None:
    data['MACD'] = macd['MACD_12_26_9']
    data['MACDSignal'] = macd['MACDs_12_26_9']
    data['MACDHist'] = macd['MACDh_12_26_9']
else:
    data['MACD'] = np.nan
    data['MACDSignal'] = np.nan
    data['MACDHist'] = np.nan
stoch = ta.stoch(data['High'], data['Low'], data['Close'])
if stoch is not None:
    data['STOCHk'] = stoch['STOCHk_14_3_3']
    data['STOCHd'] = stoch['STOCHd_14_3_3']
else:
    data['STOCHk'] = np.nan
    data['STOCHd'] = np.nan
adx = ta.adx(data['High'], data['Low'], data['Close'])
if adx is not None:
    data['ADX'] = adx['ADX_14']
    data['PLUS_DI'] = adx['DMP_14']
    data['MINUS_DI'] = adx['DMN_14']
else:
    data['ADX'] = np.nan
    data['PLUS_DI'] = np.nan
    data['MINUS_DI'] = np.nan
data['ATR'] = ta.atr(data['High'], data['Low'], data['Close'], length=14)
data['OBV'] = ta.obv(data['Close'], data['Volume'])
data['OBV_EMA'] = ta.ema(data['OBV'], length=20)
bb = ta.bbands(data['Close'], length=20, std=2)
if bb is not None:
    data['BBL'] = bb['BBL_20_2.0']
    data['BBM'] = bb['BBM_20_2.0']
    data['BBU'] = bb['BBU_20_2.0']
else:
    data['BBL'] = np.nan
    data['BBM'] = np.nan
    data['BBU'] = np.nan
data['MFI'] = ta.mfi(data['High'], data['Low'], data['Close'], data['Volume'], length=14)

# Current values
precio_actual = data['Close'].iloc[-1]
rsi_actual = data['RSI'].iloc[-1] if not pd.isna(data['RSI'].iloc[-1]) else 50
rsi5_actual = data['RSI5'].iloc[-1] if not pd.isna(data['RSI5'].iloc[-1]) else 50
macd_actual = data['MACD'].iloc[-1] if not pd.isna(data['MACD'].iloc[-1]) else 0
signal_actual = data['MACDSignal'].iloc[-1] if not pd.isna(data['MACDSignal'].iloc[-1]) else 0
hist_actual = data['MACDHist'].iloc[-1] if not pd.isna(data['MACDHist'].iloc[-1]) else 0
adx_actual = data['ADX'].iloc[-1] if not pd.isna(data['ADX'].iloc[-1]) else 25
stoch_k = data['STOCHk'].iloc[-1] if not pd.isna(data['STOCHk'].iloc[-1]) else 50
stoch_d = data['STOCHd'].iloc[-1] if not pd.isna(data['STOCHd'].iloc[-1]) else 50
mfi_actual = data['MFI'].iloc[-1] if not pd.isna(data['MFI'].iloc[-1]) else 50
atr_actual = data['ATR'].iloc[-1] if not pd.isna(data['ATR'].iloc[-1]) else 0
plus_di_actual = data['PLUS_DI'].iloc[-1] if not pd.isna(data['PLUS_DI'].iloc[-1]) else 25
minus_di_actual = data['MINUS_DI'].iloc[-1] if not pd.isna(data['MINUS_DI'].iloc[-1]) else 25
try:
    ema4 = data['EMA4'].iloc[-1].item()
except:
    ema4 = precio_actual
try:
    ema20 = data['EMA20'].iloc[-1].item()
except:
    ema20 = precio_actual
try:
    ema25 = data['EMA25'].iloc[-1].item()
except:
    ema25 = precio_actual
try:
    ema50 = data['EMA50'].iloc[-1].item()
except:
    ema50 = precio_actual
try:
    ema200 = data['EMA200'].iloc[-1].item()
except:
    ema200 = precio_actual
bb_upper = data['BBU'].iloc[-1] if not pd.isna(data['BBU'].iloc[-1]) else precio_actual
bb_lower = data['BBL'].iloc[-1] if not pd.isna(data['BBL'].iloc[-1]) else precio_actual
bb_middle = data['BBM'].iloc[-1] if not pd.isna(data['BBM'].iloc[-1]) else precio_actual
obv_actual = data['OBV'].iloc[-1] if not pd.isna(data['OBV'].iloc[-1]) else 0
obv_ema_actual = data['OBV_EMA'].iloc[-1] if not pd.isna(data['OBV_EMA'].iloc[-1]) else 0

# Calculate points and recommendation
puntos = 0
señales = []

if not np.isnan(ema20) and not np.isnan(ema50) and not np.isnan(ema25) and not np.isnan(ema200) and ema20 > ema50 and ema25 > ema50 and ema50 > ema200:
    puntos += 3
    señales.append("✅ EMAs alineadas alcistas (20,25 > 50 > 200)")
elif not pd.isna(ema20) and not pd.isna(ema50) and not pd.isna(ema25) and not pd.isna(ema200) and ema20 < ema50 and ema25 < ema50 and ema50 < ema200:
    puntos -= 3
    señales.append("❌ EMAs alineadas bajistas (20,25 < 50 < 200)")
else:
    señales.append("⚠️ EMAs sin alineación clara")

if precio_actual > ema4:
    puntos += 1
    señales.append("✅ Precio sobre EMA 4")
else:
    puntos -= 1
    señales.append("❌ Precio bajo EMA 4")

if rsi_actual < 30:
    puntos += 2
    señales.append(f"✅ RSI en sobreventa ({rsi_actual:.1f})")
elif rsi_actual > 70:
    puntos -= 2
    señales.append(f"❌ RSI en sobrecompra ({rsi_actual:.1f})")
elif 40 < rsi_actual < 60:
    señales.append(f"⚪ RSI neutral ({rsi_actual:.1f})")
elif rsi_actual > 50:
    puntos += 1
    señales.append(f"✅ RSI alcista ({rsi_actual:.1f})")
else:
    puntos -= 1
    señales.append(f"❌ RSI bajista ({rsi_actual:.1f})")

if rsi5_actual < 20:
    puntos += 1
    señales.append(f"✅ RSI 5 muy sobreventa ({rsi5_actual:.1f})")
elif rsi5_actual > 80:
    puntos -= 1
    señales.append(f"❌ RSI 5 muy sobrecompra ({rsi5_actual:.1f})")

if macd_actual > signal_actual and hist_actual > 0:
    puntos += 2
    señales.append("✅ MACD positivo")
elif macd_actual < signal_actual and hist_actual < 0:
    puntos -= 2
    señales.append("❌ MACD negativo")

if hist_actual > data['MACDHist'].iloc[-2] and data['MACDHist'].iloc[-2] > data['MACDHist'].iloc[-3]:
    puntos += 1
    señales.append("✅ Histograma MACD creciendo")
elif hist_actual < data['MACDHist'].iloc[-2] and data['MACDHist'].iloc[-2] < data['MACDHist'].iloc[-3]:
    puntos -= 1
    señales.append("❌ Histograma MACD decreciendo")

if adx_actual > 25:
    if plus_di_actual > minus_di_actual:
        puntos += 2
        señales.append(f"✅ ADX fuerte con +DI > -DI ({adx_actual:.1f})")
    else:
        puntos -= 2
        señales.append(f"❌ ADX fuerte con -DI > +DI ({adx_actual:.1f})")
else:
    señales.append(f"⚠️ ADX débil ({adx_actual:.1f})")

if stoch_k < 20 and stoch_d < 20:
    puntos += 1
    señales.append(f"✅ Estocástico sobreventa (K:{stoch_k:.1f}, D:{stoch_d:.1f})")
elif stoch_k > 80 and stoch_d > 80:
    puntos -= 1
    señales.append(f"❌ Estocástico sobrecompra (K:{stoch_k:.1f}, D:{stoch_d:.1f})")

if stoch_k > stoch_d and data['STOCHk'].iloc[-2] < data['STOCHd'].iloc[-2]:
    puntos += 1
    señales.append("✅ Cruce alcista en Estocástico")
elif stoch_k < stoch_d and data['STOCHk'].iloc[-2] > data['STOCHd'].iloc[-2]:
    puntos -= 1
    señales.append("❌ Cruce bajista en Estocástico")

if mfi_actual < 20:
    puntos += 1
    señales.append(f"✅ MFI sobreventa ({mfi_actual:.1f})")
elif mfi_actual > 80:
    puntos -= 1
    señales.append(f"❌ MFI sobrecompra ({mfi_actual:.1f})")

if obv_actual > obv_ema_actual:
    puntos += 1
    señales.append("✅ OBV sobre su EMA")
else:
    puntos -= 1
    señales.append("❌ OBV bajo su EMA")

if precio_actual < bb_lower:
    puntos += 1
    señales.append("✅ Precio bajo banda inferior Bollinger")
elif precio_actual > bb_upper:
    puntos -= 1
    señales.append("❌ Precio sobre banda superior Bollinger")

bb_width = (bb_upper - bb_lower) / bb_middle * 100
if bb_width < 2:
    señales.append(f"⚠️ Bollinger Bands comprimidas ({bb_width:.2f}%)")

# Recommendation
if puntos >= 8:
    recomendacion = "🟢 COMPRA FUERTE"
    stop_loss = precio_actual - (atr_actual * 1.5)
    target = precio_actual + (atr_actual * 3)
elif puntos >= 4:
    recomendacion = "🟢 COMPRA"
    stop_loss = precio_actual - (atr_actual * 1.5)
    target = precio_actual + (atr_actual * 2)
elif puntos >= 1:
    recomendacion = "🟡 COMPRA DÉBIL"
    stop_loss = precio_actual - (atr_actual * 1.5)
    target = precio_actual + (atr_actual * 1.5)
elif puntos <= -8:
    recomendacion = "🔴 VENTA FUERTE"
    stop_loss = precio_actual + (atr_actual * 1.5)
    target = precio_actual - (atr_actual * 3)
elif puntos <= -4:
    recomendacion = "🔴 VENTA"
    stop_loss = precio_actual + (atr_actual * 1.5)
    target = precio_actual - (atr_actual * 2)
elif puntos <= -1:
    recomendacion = "🟠 VENTA DÉBIL"
    stop_loss = precio_actual + (atr_actual * 1.5)
    target = precio_actual - (atr_actual * 1.5)
else:
    recomendacion = "⚪ NEUTRAL - ESPERAR"
    stop_loss = None
    target = None

# Print output
print("\n" + "=" * 100)
print(f"BITCOIN (BTC-USD) - ANÁLISIS TÉCNICO Y PREDICCIÓN - TIMEFRAME {timeframe}".center(100))
print("=" * 100)

print(f"\n{'📊 DATOS ACTUALES':^100}")
print("-" * 100)
print(f"Precio actual:              ${precio_actual:,.2f}")
print(f"Fecha/Hora:                 {data.index[-1]}")
print(f"Volumen (30m):              {data['Volume'].iloc[-1]:,.0f} BTC")

print(f"\n{'🎯 MEDIAS MÓVILES EXPONENCIALES (EMAs)':^100}")
print("-" * 100)
print(f"EMA 4:                      ${ema4:,.2f}")
print(f"EMA 20 (🟡 Amarillo):        ${ema20:,.2f}")
print(f"EMA 25 (🔵 Azul):            ${ema25:,.2f}")
print(f"EMA 50 (🔴 Rojo):            ${ema50:,.2f}")
print(f"EMA 200:                    ${ema200:,.2f}")

print(f"\n{'📈 INDICADORES DE MOMENTUM':^100}")
print("-" * 100)
print(f"RSI (14):                   {rsi_actual:.2f}")
print(f"RSI (5):                    {rsi5_actual:.2f}")
print(f"MACD:                       {macd_actual:.2f}")
print(f"Signal:                     {signal_actual:.2f}")
print(f"Histogram:                  {hist_actual:.2f}")

print(f"\n{'⚡ OSCILADORES':^100}")
print("-" * 100)
print(f"Stochastic %K:              {stoch_k:.2f}")
print(f"Stochastic %D:              {stoch_d:.2f}")
print(f"MFI (Money Flow):           {mfi_actual:.2f}")

print(f"\n{'📊 TENDENCIA Y VOLATILIDAD':^100}")
print("-" * 100)
print(f"ADX (Fuerza):               {adx_actual:.2f}")
print(f"+DI:                        {plus_di_actual:.2f}")
print(f"-DI:                        {minus_di_actual:.2f}")
print(f"ATR (Volatilidad):          ${atr_actual:,.2f}")

print(f"\n{'💰 VOLUMEN':^100}")
print("-" * 100)
print(f"OBV:                        {obv_actual:,.0f}")
print(f"OBV EMA:                    {obv_ema_actual:,.0f}")

print(f"\n{'📉 BOLLINGER BANDS':^100}")
print("-" * 100)
print(f"Superior:                   ${bb_upper:,.2f}")
print(f"Media:                      ${bb_middle:,.2f}")
print(f"Inferior:                   ${bb_lower:,.2f}")
print(f"Ancho de banda:             {bb_width:.2f}%")

print(f"\n{'🎯 PREDICCIÓN Y RECOMENDACIÓN':^100}")
print("=" * 100)
print(f"PUNTUACIÓN TOTAL:           {puntos:+d} / 20")
print(f"RECOMENDACIÓN:              {recomendacion}")
if stop_loss is not None and target is not None:
    print(f"STOP-LOSS SUGERIDO:         ${stop_loss:,.2f}")
    print(f"TARGET SUGERIDO:            ${target:,.2f}")
    print(f"Riesgo-Recompensa:          1:{(target - precio_actual) / (precio_actual - stop_loss):.1f}")
print("=" * 100)

print(f"\n{'🔍 SEÑALES DETECTADAS':^100}")
print("-" * 100)
for i, señal in enumerate(señales, 1):
    print(f"{i:2d}. {señal}")

print("\n" + "=" * 100)
print(f"💾 Gráfico guardado: 'btc_tradingview.html'")
print("=" * 100 + "\n")

# Generate chart
fig = make_subplots(rows=5, cols=1, shared_xaxes=True, vertical_spacing=0.05, subplot_titles=('Price', 'Volume', 'RSI', 'MACD', 'Stochastic'))

fig.add_trace(go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'], name='BTC'), row=1, col=1)
fig.add_trace(go.Scatter(x=data.index, y=data['EMA4'], mode='lines', name='EMA 4', line=dict(color='purple')), row=1, col=1)
fig.add_trace(go.Scatter(x=data.index, y=data['EMA20'], mode='lines', name='EMA 20', line=dict(color='yellow')), row=1, col=1)
fig.add_trace(go.Scatter(x=data.index, y=data['EMA50'], mode='lines', name='EMA 50', line=dict(color='red')), row=1, col=1)
fig.add_trace(go.Scatter(x=data.index, y=data['EMA200'], mode='lines', name='EMA 200', line=dict(color='black', dash='dash')), row=1, col=1)
fig.add_trace(go.Scatter(x=data.index, y=data['BBU'], mode='lines', name='BB Upper', line=dict(color='gray', dash='dot')), row=1, col=1)
fig.add_trace(go.Scatter(x=data.index, y=data['BBL'], mode='lines', name='BB Lower', line=dict(color='gray', dash='dot')), row=1, col=1)

fig.add_trace(go.Bar(x=data.index, y=data['Volume'] / 1e6, name='Volume', marker_color='steelblue'), row=2, col=1)

fig.add_trace(go.Scatter(x=data.index, y=data['RSI'], mode='lines', name='RSI 14', line=dict(color='purple')), row=3, col=1)
fig.add_trace(go.Scatter(x=data.index, y=data['RSI5'], mode='lines', name='RSI 5', line=dict(color='cyan')), row=3, col=1)
fig.add_hline(y=70, row=3, col=1, line_dash="dash", line_color="red")
fig.add_hline(y=30, row=3, col=1, line_dash="dash", line_color="green")

fig.add_trace(go.Scatter(x=data.index, y=data['MACD'], mode='lines', name='MACD', line=dict(color='blue')), row=4, col=1)
fig.add_trace(go.Scatter(x=data.index, y=data['MACDSignal'], mode='lines', name='Signal', line=dict(color='red')), row=4, col=1)
colors = ['green' if h > 0 else 'red' for h in data['MACDHist']]
fig.add_trace(go.Bar(x=data.index, y=data['MACDHist'], name='Histogram', marker_color=colors), row=4, col=1)

fig.add_trace(go.Scatter(x=data.index, y=data['STOCHk'], mode='lines', name='%K', line=dict(color='blue')), row=5, col=1)
fig.add_trace(go.Scatter(x=data.index, y=data['STOCHd'], mode='lines', name='%D', line=dict(color='red')), row=5, col=1)
fig.add_hline(y=80, row=5, col=1, line_dash="dash", line_color="red")
fig.add_hline(y=20, row=5, col=1, line_dash="dash", line_color="green")

fig.update_layout(title='Bitcoin (BTC-USD) - TradingView Style Analysis', height=1200, showlegend=False, template='plotly_dark')

fig.write_html('btc_tradingview.html')