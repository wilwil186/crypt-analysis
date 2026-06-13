#!/usr/bin/env python3
"""
🔔 Alerta DCA Semanal — versión standalone del motor del notebook.

Descarga datos semanales frescos, recalcula la asignación DCA (sleeve de tendencia
+ convicción cripto + convicción oro) y emite las acciones de la semana.

Uso:
    python3 alerta_semanal.py                 # alerta en terminal
    python3 alerta_semanal.py --capital 300   # cambia el aporte semanal
    python3 alerta_semanal.py --html          # además exporta alerta_semanal.html
    python3 alerta_semanal.py --email         # envía la alerta por email
    python3 alerta_semanal.py --telegram      # envía la alerta por Telegram
    python3 alerta_semanal.py --no-color      # sin colores ANSI

Telegram — requiere un bot (gratis, 2 min). El @usuario/teléfono NO bastan:
    1. En Telegram abre @BotFather, manda /newbot y sigue los pasos.
       Te dará un TOKEN tipo 123456789:AAxx...  -> exporta:
         export TELEGRAM_BOT_TOKEN="123456789:AAxx..."
    2. Abre tu nuevo bot en Telegram y mándale /start (cualquier mensaje).
    3. Descubre tu chat_id ejecutando:
         python3 alerta_semanal.py --telegram-setup
       Copia el id que imprime y expórtalo:
         export TELEGRAM_CHAT_ID="123456789"
    4. Listo: python3 alerta_semanal.py --telegram

Email (Gmail) — requiere una "Contraseña de aplicación" de Google, NO tu clave normal:
    1. Activa la verificación en 2 pasos en https://myaccount.google.com/security
    2. Crea una App Password en https://myaccount.google.com/apppasswords
    3. Exporta las credenciales (en ~/.bashrc para que persistan):
         export SMTP_USER="tucorreo@gmail.com"
         export SMTP_PASS="la-app-password-de-16-letras"
       Opcionales: SMTP_TO (destinatario), SMTP_HOST, SMTP_PORT
    Destinatario por defecto: edujerezwilson@gmail.com

Automatizar (cron, cada lunes 9:00, usando el venv del proyecto):
    0 9 * * 1  cd /home/wilson/Documentos/crypto-analysis && \
               SMTP_USER="tucorreo@gmail.com" SMTP_PASS="app-password" \
               venv/bin/python alerta_semanal.py --email --html >> alerta.log 2>&1
"""
import os, sys, ssl, smtplib, argparse, warnings
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import requests
import numpy as np
import pandas as pd
import yfinance as yf
import talib

warnings.filterwarnings('ignore')

# ───────────────────────────── CONFIGURACIÓN ──────────────────────────────────
UNIVERSE = {
    'BTC-USD':'Bitcoin','ETH-USD':'Ethereum','SOL-USD':'Solana',
    'SPY':'S&P 500','QQQ':'Nasdaq 100','GLD':'Oro','IWM':'Russell 2000',
    'TLT':'Bonos 20Y+','XLF':'Financiero','XLE':'Energía',
}
CLASE = {
    'BTC-USD':'Cripto','ETH-USD':'Cripto','SOL-USD':'Cripto',
    'SPY':'Renta Variable','QQQ':'Renta Variable','IWM':'Renta Variable',
    'XLF':'Renta Variable','XLE':'Renta Variable',
    'GLD':'Refugio','TLT':'Refugio',
}
WK_PERIOD          = '5y'
MIN_TREND_QUALITY  = 35       # de 60
MAX_PER_ASSET      = 0.30
CRYPTO_CAP         = 0.40
CONVICTION_CRYPTO  = 0.15
CONVICTION_ASSETS  = ['BTC-USD', 'ETH-USD']
CONVICTION_GOLD    = 0.10
GOLD_ASSET         = 'GLD'

# ───────────────────────────── COLORES ANSI ───────────────────────────────────
class C:
    R='\033[0m'; B='\033[1m'; DIM='\033[2m'
    GRN='\033[92m'; CYAN='\033[96m'; YEL='\033[93m'; RED='\033[91m'; GRY='\033[90m'
    BLU='\033[94m'
def nocolor():
    for k in vars(C):
        if not k.startswith('_'): setattr(C, k, '')

# ───────────────────────────── MOTOR DCA ──────────────────────────────────────
def get_weekly(ticker, period=WK_PERIOD):
    raw = yf.download(ticker, period=period, interval='1wk', progress=False, auto_adjust=True)
    if raw is None or raw.empty: return None
    d = raw.copy()
    if isinstance(d.columns, pd.MultiIndex):
        d.columns = d.columns.droplevel(1)
    d = d[['Open','High','Low','Close','Volume']].dropna()
    if d.index.tz is not None:
        d.index = d.index.tz_localize(None)
    return d

def lt_features(d):
    x = d.copy()
    c = np.asarray(x.Close.values, dtype=np.float64)
    h = np.asarray(x.High.values,  dtype=np.float64)
    l = np.asarray(x.Low.values,   dtype=np.float64)
    x['SMA10'] = x.Close.rolling(10).mean()
    x['SMA30'] = x.Close.rolling(30).mean()
    x['SMA40'] = x.Close.rolling(40).mean()
    x['RSIw']  = talib.RSI(c, 14)
    x['MACDw'], x['MACDws'], _ = talib.MACD(c, 12, 26, 9)
    x['MOM26'] = x.Close.pct_change(26) * 100
    x['ATH52'] = x.High.rolling(52).max()
    x['DDhigh']= (x.Close / x.ATH52 - 1) * 100
    return x

def dca_score(x):
    r = x.iloc[-1]; price = r.Close
    tq = 0
    if not np.isnan(r.SMA40) and price > r.SMA40:             tq += 20
    if not np.isnan(r.SMA40) and r.SMA10 > r.SMA30 > r.SMA40: tq += 15
    if not np.isnan(r.MOM26) and r.MOM26 > 0:                 tq += 15
    if not np.isnan(r.MACDw)  and r.MACDw > r.MACDws:         tq += 10
    ev = 0
    if not np.isnan(r.SMA40) and price > r.SMA40:
        if   price <= r.SMA10 * 1.02: ev += 20
        elif price <= r.SMA10 * 1.08: ev += 12
        else:                          ev += 4
    if not np.isnan(r.RSIw):
        if   r.RSIw < 65: ev += 10
        elif r.RSIw < 75: ev += 5
    if not np.isnan(r.DDhigh):
        if   -35 <= r.DDhigh <= -8: ev += 10
        elif -8  <  r.DDhigh <= -3: ev += 6
        elif r.DDhigh < -35:        ev += 3
    return dict(score=tq+ev, trend_quality=tq, price=price,
                sma30=r.SMA30, sma40=r.SMA40, rsiw=r.RSIw)

def build_allocation(DCA):
    # Sleeve de tendencia: activos no-cripto, no-oro, en uptrend confirmado
    elig = {tk: s for tk, s in DCA.items()
            if CLASE[tk] != 'Cripto' and tk != GOLD_ASSET
            and s['price'] > s['sma40'] and s['trend_quality'] >= MIN_TREND_QUALITY
            and s['score'] > 0}
    weights = {}
    if elig:
        raw = {tk: s['score'] for tk, s in elig.items()}
        tot = sum(raw.values()); weights = {tk: v/tot for tk, v in raw.items()}
        for tk in list(weights): weights[tk] = min(weights[tk], MAX_PER_ASSET)
        s0 = sum(weights.values()); weights = {k: v/s0 for k, v in weights.items()}

    reserved = CONVICTION_CRYPTO + CONVICTION_GOLD
    trend = {a: w*(1-reserved) for a, w in weights.items()}
    cs = {a: max(DCA[a]['score'], 1) for a in CONVICTION_ASSETS if a in DCA}
    csum = sum(cs.values()) or 1
    conv = {a: CONVICTION_CRYPTO*cs[a]/csum for a in cs}
    gold = {GOLD_ASSET: CONVICTION_GOLD} if GOLD_ASSET in DCA else {}

    final = {}
    for d in (trend, conv, gold):
        for a, w in d.items(): final[a] = final.get(a, 0)+w
    s = sum(final.values()) or 1
    return {k: v/s for k, v in final.items()}

def sleeve_of(tk):
    if tk in CONVICTION_ASSETS: return 'Convicción-Cripto'
    if tk == GOLD_ASSET:        return 'Convicción-Oro'
    return 'Tendencia'

def classify(tk, s):
    price, sma30, sma40, rsi = s['price'], s['sma30'], s['sma40'], s['rsiw']
    is_conv = (tk in CONVICTION_ASSETS) or (tk == GOLD_ASSET)
    euf = sma40*1.25 if not np.isnan(sma40) else np.inf
    if price > euf or (not np.isnan(rsi) and rsi > 75):
        return 3, '🔴 EUFORIA', 'Reduce o salta el aporte', C.RED
    if not np.isnan(sma30) and price <= sma30:
        return 1, '🟢 PULLBACK', 'Sobreponderá (aporte extra)', C.GRN
    if not np.isnan(sma40) and price <= sma40*1.05:
        return 0, '🔵 OPORTUNIDAD', 'DOBLA el aporte', C.CYAN
    if (not is_conv) and not np.isnan(sma40) and price < sma40:
        return 4, '⚫ FUERA', 'Deja de acumular (perdió SMA40)', C.GRY
    return 2, '🟡 NORMAL', 'Aporte normal a mercado', C.YEL

# ───────────────────────────── SALIDA ─────────────────────────────────────────
def run(capital, want_html, want_email, email_to, want_telegram):
    print(f'{C.DIM}Descargando datos semanales del universo...{C.R}')
    DCA = {}
    for tk in UNIVERSE:
        d = get_weekly(tk)
        if d is not None and len(d) >= 45:
            DCA[tk] = dca_score(lt_features(d))
    if not DCA:
        print(f'{C.RED}No se pudieron descargar datos.{C.R}'); return

    fecha = max(get_weekly(next(iter(DCA))).index[-1], get_weekly('SPY').index[-1] if 'SPY' in DCA else datetime.now())
    # fecha de referencia simple: última semana del primer activo
    fecha = datetime.now().strftime('%d/%m/%Y')

    final = build_allocation(DCA)
    alerts = []
    for tk in final:
        urg, zona, accion, col = classify(tk, DCA[tk])
        alerts.append(dict(tk=tk, urg=urg, zona=zona, accion=accion, col=col,
                           aporte=final[tk]*capital, **DCA[tk]))
    alerts.sort(key=lambda a: a['urg'])

    W = 70
    print()
    print(C.B + '═'*W + C.R)
    print(f'{C.B}  🔔 ALERTA DCA SEMANAL{C.R}  ·  datos al {fecha}')
    print(C.B + '═'*W + C.R)
    by_class = {}
    for a in alerts: by_class[CLASE[a['tk']]] = by_class.get(CLASE[a['tk']], 0)+a['aporte']
    div = '  '.join(f'{k} {v/capital*100:.0f}%' for k, v in sorted(by_class.items(), key=lambda x:-x[1]))
    print(f'  Capital: {C.B}${capital}{C.R}/sem   ·   {div}')
    print()

    # Plan de aporte
    print(f'{C.B}  PLAN DE APORTE{C.R}')
    print(f'  {"Activo":<9}{"Clase":<16}{"Sleeve":<19}{"Aporte":>9}{"Precio":>13}')
    print(f'  {C.DIM}{"-"*64}{C.R}')
    for a in sorted(alerts, key=lambda x:-x['aporte']):
        print(f'  {a["tk"]:<9}{CLASE[a["tk"]]:<16}{sleeve_of(a["tk"]):<19}'
              f'{C.B}${a["aporte"]:>7.0f}{C.R}{a["price"]:>13,.2f}')
    print()

    # Acciones por prioridad
    print(f'{C.B}  ACCIONES DE ESTA SEMANA{C.R}')
    grupos = {}
    for a in alerts: grupos.setdefault(a['urg'], []).append(a)
    orden = [(0,'🔵 OPORTUNIDAD — DOBLA el aporte'),(1,'🟢 PULLBACK — sobreponderá'),
             (2,'🟡 NORMAL — aporte a mercado'),(3,'🔴 EUFORIA — reduce o salta'),
             (4,'⚫ FUERA — deja de acumular')]
    for urg, titulo in orden:
        if urg not in grupos: continue
        col = grupos[urg][0]['col']
        print(f'\n  {col}{C.B}{titulo}{C.R}')
        for a in grupos[urg]:
            d30 = (a['sma30']/a['price']-1)*100
            d40 = (a['sma40']/a['price']-1)*100
            print(f'    {col}•{C.R} {a["tk"]:<9} ${a["price"]:>10,.2f}  aporte ${a["aporte"]:>5.0f}'
                  f'   {C.DIM}a SMA30 {d30:+.1f}% · a SMA40 {d40:+.1f}% · RSI {a["rsiw"]:.0f}{C.R}')

    extra = sum(a['aporte'] for a in alerts if a['urg'] in (0,1))
    print()
    print(C.B + '─'*W + C.R)
    print(f'  Aporta {C.B}${capital}{C.R} base. Donde haya 🔵/🟢, considera hasta '
          f'{C.B}${extra:.0f}{C.R} extra si tu liquidez lo permite.')
    print(f'  {C.DIM}Educativo, no es asesoría financiera.{C.R}')
    print(C.B + '═'*W + C.R)

    if want_html:
        export_html(alerts, final, capital, fecha, by_class)
    if want_email:
        send_email(alerts, final, capital, fecha, by_class, email_to)
    if want_telegram:
        send_telegram(alerts, final, capital, fecha, by_class)

def build_html(alerts, final, capital, fecha, by_class):
    cls_color = {'Cripto':'#f7931a','Renta Variable':'#42a5f5','Refugio':'#ffd54f'}
    zcol = {0:'#26c6da',1:'#00c853',2:'#ffd600',3:'#ff5252',4:'#777'}
    titulos = {0:'🔵 OPORTUNIDAD — DOBLA el aporte',1:'🟢 PULLBACK — sobreponderá',
               2:'🟡 NORMAL — aporte a mercado',3:'🔴 EUFORIA — reduce o salta',
               4:'⚫ FUERA — deja de acumular'}
    bloques = ''
    for urg in sorted(set(a['urg'] for a in alerts)):
        subs = [a for a in alerts if a['urg'] == urg]
        items = ''.join(
            f'<div style="padding:8px 12px;margin:5px 0;background:#1a1d27;border-radius:8px;border-left:4px solid {zcol[urg]}">'
            f'<b>{a["tk"]}</b> <span style="color:#888">({UNIVERSE[a["tk"]]})</span> · ${a["price"]:,.2f} · '
            f'aporte <b>${a["aporte"]:.0f}</b>'
            f'<span style="color:#888;font-size:12px"> · a SMA30 {(a["sma30"]/a["price"]-1)*100:+.1f}% · '
            f'a SMA40 {(a["sma40"]/a["price"]-1)*100:+.1f}%</span></div>'
            for a in subs)
        bloques += (f'<div style="margin-bottom:14px"><div style="color:{zcol[urg]};font-weight:bold;'
                    f'font-size:15px;margin-bottom:4px">{titulos[urg]}</div>{items}</div>')
    chips = ' '.join(f'<span style="background:{cls_color[k]};color:#000;padding:4px 12px;border-radius:10px;margin:3px;display:inline-block"><b>{k}: {v/capital*100:.0f}%</b></span>'
                     for k, v in sorted(by_class.items(), key=lambda x:-x[1]))
    extra = sum(a['aporte'] for a in alerts if a['urg'] in (0,1))
    html = f'''<!DOCTYPE html><html lang="es"><head><meta charset="utf-8">
<title>Alerta DCA — {fecha}</title></head>
<body style="background:#0a0a0a;margin:0;padding:24px">
<div style="font-family:Segoe UI,sans-serif;background:#0e1117;color:#eee;padding:26px;border-radius:16px;max-width:1000px;margin:auto">
  <h1 style="color:#667eea;margin-top:0">🔔 Alerta DCA — semana del {fecha}</h1>
  <div style="margin:12px 0">{chips}</div>
  <p style="color:#aaa">Aporte base <b>${capital}</b>. Donde haya 🔵/🟢, considera hasta <b>${extra:.0f}</b> extra.</p>
  {bloques}
  <p style="color:#555;font-size:12px;text-align:center">Generado {datetime.now().strftime('%d/%m/%Y %H:%M')} · Educativo, no es asesoría financiera.</p>
</div></body></html>'''
    return html

def export_html(alerts, final, capital, fecha, by_class):
    html = build_html(alerts, final, capital, fecha, by_class)
    with open('alerta_semanal.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'  {C.GRN}✓ HTML exportado: alerta_semanal.html{C.R}')

def email_subject(alerts, fecha):
    opps  = [a['tk'] for a in alerts if a['urg'] == 0]
    pulls = [a['tk'] for a in alerts if a['urg'] == 1]
    if opps:
        return f"🔵 DCA {fecha}: OPORTUNIDAD en {', '.join(opps)} (dobla aporte)"
    if pulls:
        return f"🟢 DCA {fecha}: pullback en {', '.join(pulls)} (sobreponderá)"
    return f"🔔 DCA {fecha}: aporte semanal normal"

def send_email(alerts, final, capital, fecha, by_class, to_addr):
    user = os.environ.get('SMTP_USER')
    pw   = os.environ.get('SMTP_PASS')
    host = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
    port = int(os.environ.get('SMTP_PORT', '587'))
    if not user or not pw:
        print(f'  {C.RED}✗ Email no enviado: faltan SMTP_USER / SMTP_PASS '
              f'(ver instrucciones en la cabecera del script).{C.R}')
        return False
    html = build_html(alerts, final, capital, fecha, by_class)
    msg = MIMEMultipart('alternative')
    msg['Subject'] = email_subject(alerts, fecha)
    msg['From'], msg['To'] = user, to_addr
    resumen = '; '.join(f'{a["tk"]} {a["zona"]}' for a in alerts)
    msg.attach(MIMEText(f'Alerta DCA {fecha}\n{resumen}\n\n(abre en HTML para el detalle)', 'plain'))
    msg.attach(MIMEText(html, 'html'))
    try:
        ctx = ssl.create_default_context()
        with smtplib.SMTP(host, port, timeout=30) as s:
            s.starttls(context=ctx)
            s.login(user, pw)
            s.sendmail(user, [to_addr], msg.as_string())
        print(f'  {C.GRN}✓ Email enviado a {to_addr}{C.R}')
        return True
    except Exception as e:
        print(f'  {C.RED}✗ Error enviando email: {e}{C.R}')
        return False

# ───────────────────────────── TELEGRAM ───────────────────────────────────────
def build_telegram_text(alerts, capital, fecha, by_class):
    titulos = {0:'🔵 OPORTUNIDAD — DOBLA', 1:'🟢 PULLBACK — sobreponderá',
               2:'🟡 NORMAL', 3:'🔴 EUFORIA — reduce', 4:'⚫ FUERA — no acumular'}
    div = ' · '.join(f'{k} {v/capital*100:.0f}%' for k, v in sorted(by_class.items(), key=lambda x:-x[1]))
    lines = [f'<b>🔔 Alerta DCA — {fecha}</b>', f'Capital ${capital:.0f}/sem · {div}', '']
    for urg in sorted(set(a['urg'] for a in alerts)):
        subs = [a for a in alerts if a['urg'] == urg]
        lines.append(f'<b>{titulos[urg]}</b>')
        for a in subs:
            lines.append(f'• {a["tk"]} ${a["price"]:,.2f} (aporte ${a["aporte"]:.0f})')
        lines.append('')
    extra = sum(a['aporte'] for a in alerts if a['urg'] in (0, 1))
    lines.append(f'Aporta ${capital:.0f} base; hasta ${extra:.0f} extra en 🔵/🟢.')
    return '\n'.join(lines)

def send_telegram(alerts, final, capital, fecha, by_class):
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat  = os.environ.get('TELEGRAM_CHAT_ID')
    if not token or not chat:
        print(f'  {C.RED}✗ Telegram no enviado: faltan TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID '
              f'(ver instrucciones en la cabecera del script).{C.R}')
        return False
    text = build_telegram_text(alerts, capital, fecha, by_class)
    try:
        r = requests.post(f'https://api.telegram.org/bot{token}/sendMessage',
                          data={'chat_id': chat, 'text': text, 'parse_mode': 'HTML',
                                'disable_web_page_preview': True}, timeout=30)
        if r.status_code == 200 and r.json().get('ok'):
            print(f'  {C.GRN}✓ Telegram enviado (chat {chat}){C.R}')
            return True
        print(f'  {C.RED}✗ Telegram rechazado: {r.text[:200]}{C.R}')
        return False
    except Exception as e:
        print(f'  {C.RED}✗ Error enviando Telegram: {e}{C.R}')
        return False

def telegram_setup():
    """Descubre tu chat_id tras enviarle /start al bot."""
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    if not token:
        print(f'{C.RED}Exporta TELEGRAM_BOT_TOKEN primero (ver cabecera del script).{C.R}')
        return
    try:
        r = requests.get(f'https://api.telegram.org/bot{token}/getUpdates', timeout=30)
        data = r.json()
    except Exception as e:
        print(f'{C.RED}Error consultando Telegram: {e}{C.R}'); return
    if not data.get('ok'):
        print(f'{C.RED}Token inválido o error: {data}{C.R}'); return
    chats = {}
    for u in data.get('result', []):
        m = u.get('message') or u.get('edited_message') or u.get('channel_post') or {}
        ch = m.get('chat', {})
        if ch.get('id'): chats[ch['id']] = ch
    if not chats:
        print(f'{C.YEL}No hay mensajes todavía. Abre tu bot en Telegram y mándale /start, '
              f'luego repite este comando.{C.R}')
        return
    print(f'{C.GRN}Chats encontrados (usa el id en TELEGRAM_CHAT_ID):{C.R}')
    for cid, ch in chats.items():
        quien = ch.get('username') or ch.get('first_name') or ch.get('title') or '?'
        print(f'  {C.B}{cid}{C.R}  ({quien})')

# ───────────────────────────── MAIN ───────────────────────────────────────────
if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='Alerta DCA semanal')
    ap.add_argument('--capital', type=float, default=200, help='Aporte semanal en USD')
    ap.add_argument('--html', action='store_true', help='Exporta alerta_semanal.html')
    ap.add_argument('--email', action='store_true', help='Envía la alerta por email (SMTP)')
    ap.add_argument('--email-to', default=os.environ.get('SMTP_TO', 'edujerezwilson@gmail.com'),
                    help='Destinatario del email')
    ap.add_argument('--telegram', action='store_true', help='Envía la alerta por Telegram')
    ap.add_argument('--telegram-setup', action='store_true',
                    help='Descubre tu chat_id (mándale /start al bot antes)')
    ap.add_argument('--no-color', action='store_true', help='Desactiva colores ANSI')
    args = ap.parse_args()
    if args.no_color or not sys.stdout.isatty():
        nocolor()
    if args.telegram_setup:
        telegram_setup()
        sys.exit(0)
    run(args.capital, args.html, args.email, args.email_to, args.telegram)
