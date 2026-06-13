import yfinance as yf
import pandas as pd
import numpy as np
import talib
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import os

ticker = "BTC-USD"

print("\n" + "=" * 60)
print("ANÁLISIS TÉCNICO BTC - SELECCIÓN DE TEMPORALIDAD")
print("=" * 60)
print("1. 1 día")
print("2. 12 horas") 
print("3. 6 horas")
print("4. 4 horas")
print("5. 1 hora")
print("6. 30 min")
print("7. 15 min")
print("8. 5 min")
print("9. 1 min")
print("=" * 60)

choice = input("\nElige temporalidad (1-9) [Enter = 30min]: ").strip()
if not choice:
    choice = "6"

config = {
    '1': ("1d", "2y", "1 DÍA"),
    '2': ("1h", "60d", "12 HORAS"),
    '3': ("1h", "60d", "6 HORAS"),
    '4': ("1h", "60d", "4 HORAS"),
    '5': ("1h", "7d", "1 HORA"),
    '6': ("30m", "7d", "30 MIN"),
    '7': ("15m", "5d", "15 MIN"),
    '8': ("5m", "5d", "5 MIN"),
    '9': ("1m", "1d", "1 MIN")
}

interval, periodo, timeframe = config.get(choice, ("30m", "7d", "30 MIN"))

print(f"\n📊 Descargando {ticker} ({timeframe})...\n")
data = yf.download(ticker, period=periodo, interval=interval, progress=False)

if data.empty:
    print("❌ Error descargando datos")
    exit(1)

close = np.asarray(data['Close'].dropna().values, dtype=float).flatten()
high = np.asarray(data['High'].dropna().values, dtype=float).flatten()
low = np.asarray(data['Low'].dropna().values, dtype=float).flatten()
volume = np.asarray(data['Volume'].dropna().values, dtype=float).flatten()
open_prices = np.asarray(data['Open'].dropna().values, dtype=float).flatten()

ema_4 = talib.EMA(close, timeperiod=4)
ema_20 = talib.EMA(close, timeperiod=20)
ema_25 = talib.EMA(close, timeperiod=25)
ema_50 = talib.EMA(close, timeperiod=50)
ema_200 = talib.EMA(close, timeperiod=200)
rsi = talib.RSI(close, timeperiod=14)
rsi_5 = talib.RSI(close, timeperiod=5)
macd, signal, hist = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
slowk, slowd = talib.STOCH(high, low, close, fastk_period=14, slowk_period=3, slowd_period=3)
adx = talib.ADX(high, low, close, timeperiod=14)
atr = talib.ATR(high, low, close, timeperiod=14)
obv = talib.OBV(close, volume)
obv_ema = talib.EMA(obv, timeperiod=20)
upper, middle, lower = talib.BBANDS(close, timeperiod=20, nbdevup=2, nbdevdn=2)
mfi = talib.MFI(high, low, close, volume, timeperiod=14)
plus_di = talib.PLUS_DI(high, low, close, timeperiod=14)
minus_di = talib.MINUS_DI(high, low, close, timeperiod=14)

precio = close[-1]
puntos = 0
señales = []

if ema_20[-1] > ema_50[-1] and ema_50[-1] > ema_200[-1]:
    puntos += 3
    tendencia = "🟢 ALCISTA"
    señales.append("✅ EMAs alcistas")
elif ema_20[-1] < ema_50[-1] and ema_50[-1] < ema_200[-1]:
    puntos -= 3
    tendencia = "🔴 BAJISTA"
    señales.append("❌ EMAs bajistas")
else:
    tendencia = "⚪ NEUTRAL"
    señales.append("⚠️ EMAs neutral")

if precio > ema_4[-1]:
    puntos += 1
    señales.append(f"✅ Precio > EMA4")
else:
    puntos -= 1
    señales.append(f"❌ Precio < EMA4")

if rsi[-1] < 30:
    puntos += 2
    señales.append(f"✅ RSI sobreventa ({rsi[-1]:.1f})")
elif rsi[-1] > 70:
    puntos -= 2
    señales.append(f"❌ RSI sobrecompra ({rsi[-1]:.1f})")
elif rsi[-1] > 50:
    puntos += 1
    señales.append(f"✅ RSI alcista ({rsi[-1]:.1f})")
else:
    puntos -= 1
    señales.append(f"❌ RSI bajista ({rsi[-1]:.1f})")

if macd[-1] > signal[-1]:
    puntos += 2
    señales.append("✅ MACD positivo")
else:
    puntos -= 2
    señales.append("❌ MACD negativo")

if adx[-1] > 25:
    if plus_di[-1] > minus_di[-1]:
        puntos += 2
        señales.append(f"✅ Tendencia fuerte alcista")
    else:
        puntos -= 2
        señales.append(f"❌ Tendencia fuerte bajista")

if slowk[-1] < 20:
    puntos += 1
    señales.append(f"✅ Estocástico sobreventa")
elif slowk[-1] > 80:
    puntos -= 1
    señales.append(f"❌ Estocástico sobrecompra")

if mfi[-1] < 20:
    puntos += 1
    señales.append(f"✅ MFI sobreventa")
elif mfi[-1] > 80:
    puntos -= 1
    señales.append(f"❌ MFI sobrecompra")

if obv[-1] > obv_ema[-1]:
    puntos += 1
    señales.append("✅ Volumen comprando")
else:
    puntos -= 1
    señales.append("❌ Volumen vendiendo")

atr_val = atr[-1]

if puntos >= 8:
    rec = "🟢 COMPRA FUERTE"
    color = "green"
    tp = precio + (atr_val * 3)
    act_sl = precio - (atr_val * 1)
    sl = precio - (atr_val * 1.5)
elif puntos >= 4:
    rec = "🟢 COMPRA"
    color = "lightgreen"
    tp = precio + (atr_val * 2.5)
    act_sl = precio - (atr_val * 1)
    sl = precio - (atr_val * 1.5)
elif puntos >= 1:
    rec = "🟡 COMPRA DÉBIL"
    color = "yellow"
    tp = precio + (atr_val * 2)
    act_sl = precio - (atr_val * 0.8)
    sl = precio - (atr_val * 1.2)
elif puntos <= -8:
    rec = "🔴 VENTA FUERTE"
    color = "red"
    tp = precio - (atr_val * 3)
    act_sl = precio + (atr_val * 1)
    sl = precio + (atr_val * 1.5)
elif puntos <= -4:
    rec = "🔴 VENTA"
    color = "lightcoral"
    tp = precio - (atr_val * 2.5)
    act_sl = precio + (atr_val * 1)
    sl = precio + (atr_val * 1.5)
elif puntos <= -1:
    rec = "🟠 VENTA DÉBIL"
    color = "orange"
    tp = precio - (atr_val * 2)
    act_sl = precio + (atr_val * 0.8)
    sl = precio + (atr_val * 1.2)
else:
    rec = "⚪ NEUTRAL"
    color = "gray"
    tp = act_sl = sl = None

oco_type = "COMPRA" if "COMPRA" in rec else "VENTA"

fig = make_subplots(rows=5, cols=1, shared_xaxes=True, vertical_spacing=0.05)

fig.add_trace(go.Candlestick(x=data.index, open=open_prices, high=high, low=low, close=close, name='BTC'), row=1, col=1)
fig.add_trace(go.Scatter(x=data.index, y=ema_4, mode='lines', name='EMA4', line=dict(color='purple', width=1)), row=1, col=1)
fig.add_trace(go.Scatter(x=data.index, y=ema_20, mode='lines', name='EMA20', line=dict(color='yellow', width=2)), row=1, col=1)
fig.add_trace(go.Scatter(x=data.index, y=ema_50, mode='lines', name='EMA50', line=dict(color='red', width=2)), row=1, col=1)
fig.add_trace(go.Scatter(x=data.index, y=ema_200, mode='lines', name='EMA200', line=dict(color='white', width=1, dash='dash')), row=1, col=1)

fig.add_trace(go.Bar(x=data.index, y=volume/1e6, name='Vol', marker_color='steelblue'), row=2, col=1)
fig.add_trace(go.Scatter(x=data.index, y=rsi, mode='lines', name='RSI', line=dict(color='purple')), row=3, col=1)
fig.add_hline(y=70, row=3, col=1, line_dash="dash", line_color="red", line_width=1)
fig.add_hline(y=30, row=3, col=1, line_dash="dash", line_color="green", line_width=1)

fig.add_trace(go.Scatter(x=data.index, y=macd, mode='lines', name='MACD', line=dict(color='blue')), row=4, col=1)
fig.add_trace(go.Scatter(x=data.index, y=signal, mode='lines', name='Signal', line=dict(color='red')), row=4, col=1)
colors = ['green' if h > 0 else 'red' for h in hist]
fig.add_trace(go.Bar(x=data.index, y=hist, name='Hist', marker_color=colors), row=4, col=1)

fig.add_trace(go.Scatter(x=data.index, y=slowk, mode='lines', name='%K', line=dict(color='blue')), row=5, col=1)
fig.add_trace(go.Scatter(x=data.index, y=slowd, mode='lines', name='%D', line=dict(color='red')), row=5, col=1)
fig.add_hline(y=80, row=5, col=1, line_dash="dash", line_color="red", line_width=1)
fig.add_hline(y=20, row=5, col=1, line_dash="dash", line_color="green", line_width=1)

fig.update_layout(
    title=f'BTC-USD | {timeframe} | {rec}',
    height=1200,
    showlegend=False,
    template='plotly_dark',
    font=dict(size=10)
)

html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>BTC Analysis | {timeframe}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: 'Segoe UI', sans-serif;
            background: #0a0a0a;
            color: #fff;
            padding: 20px;
        }}
        .container {{ max-width: 1600px; margin: 0 auto; }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 25px;
            border-radius: 12px;
            margin-bottom: 25px;
            text-align: center;
        }}
        h1 {{ font-size: 32px; margin-bottom: 10px; }}
        .price {{ font-size: 36px; font-weight: bold; margin: 15px 0; }}
        .oco-box {{
            background: #1a1a1a;
            border: 3px solid {color};
            border-radius: 12px;
            padding: 25px;
            margin: 25px 0;
            box-shadow: 0 4px 20px rgba(0,0,0,0.5);
        }}
        .oco-title {{
            font-size: 26px;
            font-weight: bold;
            color: {color};
            margin-bottom: 20px;
            text-align: center;
        }}
        .oco-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 15px;
        }}
        .oco-item {{
            background: #252525;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid {color};
        }}
        .label {{ 
            font-size: 11px; 
            color: #888; 
            text-transform: uppercase; 
            margin-bottom: 5px;
            letter-spacing: 1px;
        }}
        .value {{ 
            font-size: 22px; 
            font-weight: bold; 
            color: #fff; 
        }}
        .rec-box {{
            text-align: center;
            padding: 15px;
            background: #252525;
            border-radius: 8px;
            margin-top: 15px;
        }}
        .rec {{ color: {color}; font-size: 24px; font-weight: bold; }}
        .signals {{
            background: #1a1a1a;
            padding: 20px;
            border-radius: 12px;
            margin: 25px 0;
        }}
        .signal-item {{
            padding: 10px;
            margin: 6px 0;
            background: #252525;
            border-radius: 6px;
            border-left: 3px solid #667eea;
            font-size: 14px;
        }}
        .chart {{ 
            background: #1a1a1a; 
            padding: 15px; 
            border-radius: 12px; 
            margin: 25px 0; 
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 BITCOIN ANÁLISIS TÉCNICO</h1>
            <div style="font-size: 18px; margin: 10px 0;">⏱️ {timeframe} | {data.index[-1]}</div>
            <div class="price">${precio:.2f}</div>
            <div style="font-size: 16px;">{tendencia}</div>
        </div>

         <div class="oco-box">
             <div class="oco-title">🎯 PARÁMETROS OCO BINANCE ({oco_type})</div>
            <div class="oco-grid">
                 <div class="oco-item">
                     <div class="label">Precio Actual</div>
                     <div class="value">${precio:.2f}</div>
                 </div>
"""

if tp is not None:
    rr = abs((tp - precio) / (precio - act_sl)) if act_sl else 0
    html += f"""
                 <div class="oco-item">
                     <div class="label">TP Limit</div>
                     <div class="value">${tp:.2f}</div>
                 </div>
                 <div class="oco-item">
                     <div class="label">Activador SL</div>
                     <div class="value">${act_sl:.2f}</div>
                 </div>
                 <div class="oco-item">
                     <div class="label">SL Limit</div>
                     <div class="value">${sl:.2f}</div>
                 </div>
                <div class="oco-item">
                    <div class="label">Risk/Reward</div>
                    <div class="value">1:{rr:.2f}</div>
                </div>
"""
else:
    html += """
                <div class="oco-item" style="grid-column: 1/-1;">
                    <div class="label">Estado</div>
                    <div class="value">⚠️ NO OPERAR</div>
                </div>
"""

html += f"""
            </div>
            <div class="rec-box">
                <div class="rec">{rec}</div>
                <div style="margin-top: 8px;">Puntuación: {puntos:+d}/20</div>
            </div>
        </div>

        <div class="signals">
            <h2 style="color: #667eea; margin-bottom: 15px;">🔍 Señales</h2>
"""

for i, s in enumerate(señales, 1):
    html += f'            <div class="signal-item">{i}. {s}</div>\n'

html += f"""
        </div>

        <div class="chart">
            <h2 style="color: #667eea; margin-bottom: 15px;">📈 Gráfico</h2>
            {fig.to_html(include_plotlyjs='cdn', full_html=False)}
        </div>
    </div>
</body>
</html>
"""

output_file = 'btc_analysis.html'
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(html)

print("\n" + "=" * 80)
print(f"  BTC-USD | {timeframe}".center(80))
print("=" * 80)
print(f"\n💰 Precio: ${precio:,.2f}")
print(f"📅 Fecha:  {data.index[-1]}")
print(f"📊 Tendencia: {tendencia}")

print(f"\n🎯 ORDEN OCO BINANCE ({oco_type})")
print("-" * 80)
if tp is not None:
    print(f"  TP Limit:      ${tp:.2f}")
    print(f"  Activador SL:  ${act_sl:.2f}")
    print(f"  SL Limit:      ${sl:.2f}")
    print(f"  Risk/Reward:   1:{rr:.2f}")
else:
    print("  ⚠️ NO OPERAR - Condiciones no favorables")

print(f"\n📈 RECOMENDACIÓN: {rec}")
print(f"🎲 Puntuación: {puntos:+d}/20")

print(f"\n🔍 Señales:")
for i, s in enumerate(señales, 1):
    print(f"  {i}. {s}")

print(f"\n✅ Guardado: {os.path.abspath(output_file)}")
print("=" * 80 + "\n")

try:
    import webbrowser
    webbrowser.open(f'file://{os.path.abspath(output_file)}')
    print("🌐 Abriendo navegador...\n")
except:
    print(f"⚠️ Abre manualmente: {output_file}\n")
