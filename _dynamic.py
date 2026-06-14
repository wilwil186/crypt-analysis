#!/usr/bin/env python3
"""Universo dinámico desde la web + fecha actual + etiqueta cripto/ETF."""
import json, pathlib

NEW_CONFIG = '''# ───────────────────────── CONFIGURACIÓN GLOBAL ─────────────────────────
PRIMARY   = 'BTC-USD'          # activo para el análisis profundo
INTERVAL  = '1d'               # temporalidad
PERIOD    = '2y'               # histórico
ANNUALIZE = 252                # factor de anualización (1d -> 252)

# ── Universo DINÁMICO desde la web ──
#   Cripto: top por capitalización (CoinGecko) · ETFs: screener de Yahoo + núcleo líquido
MAX_CRYPTO = 6
MAX_ETF    = 10

import requests as _rq
_STABLE = {'USDT','USDC','DAI','USDS','TUSD','USDE','FDUSD','PYUSD','BUSD','USD1','BSC-USD','LEO'}
_WRAP   = {'WBTC','WETH','WBETH','STETH','WSTETH','WEETH','RETH','CBBTC','LBTC','SOLVBTC','BGB'}
_REFUGIO = {'GLD','IAU','GLDM','SGOL','SLV','TLT','IEF','SHY','BND','AGG','LQD'}
_ETF_CORE = {'SPY':'S&P 500','QQQ':'Nasdaq 100','VTI':'Total Market US','IWM':'Russell 2000',
             'VEA':'Desarrollados ex-US','VWO':'Emergentes','GLD':'Oro','TLT':'Bonos 20Y+',
             'XLF':'Financiero','XLE':'Energia','XLK':'Tecnologia','VNQ':'Inmobiliario'}

def fetch_cryptos(n):
    try:
        r = _rq.get('https://api.coingecko.com/api/v3/coins/markets',
                    params={'vs_currency':'usd','order':'market_cap_desc','per_page':60,'page':1}, timeout=20)
        out = {}
        for c in r.json():
            s = c['symbol'].upper()
            if s in _STABLE or s in _WRAP or '_' in s: continue
            out[f'{s}-USD'] = c['name']
            if len(out) >= n: break
        out.setdefault('BTC-USD','Bitcoin'); out.setdefault('ETH-USD','Ethereum')  # sleeves convicción
        return out
    except Exception as e:
        print('  ⚠️ CoinGecko falló, uso cripto base:', e)
        return {'BTC-USD':'Bitcoin','ETH-USD':'Ethereum','SOL-USD':'Solana'}

def fetch_etfs(n):
    etfs = dict(list(_ETF_CORE.items())[:n])      # núcleo líquido garantizado
    try:
        res = yf.screen('top_etfs_us', size=25)    # extras dinámicos desde la web
        for x in res.get('quotes', []):
            s = x.get('symbol')
            if s and s not in etfs and len(etfs) < n + 4:
                etfs[s] = (x.get('shortName') or s)[:22]
    except Exception as e:
        print('  ⚠️ Screener ETF falló, uso núcleo:', e)
    return etfs

print('Construyendo universo dinámico desde la web...')
_cry = fetch_cryptos(MAX_CRYPTO)
_etf = fetch_etfs(MAX_ETF)
UNIVERSE, CLASE = {}, {}
for _tk, _nm in _cry.items(): UNIVERSE[_tk] = _nm; CLASE[_tk] = 'Cripto'
for _tk, _nm in _etf.items(): UNIVERSE[_tk] = _nm; CLASE[_tk] = ('Refugio' if _tk in _REFUGIO else 'Renta Variable')

BUY_TH, SELL_TH = 4, -4
COL = dict(bull='#00c853', bear='#ff1744', neutral='#9e9e9e',
           accent='#667eea', warn='#ffd600', bg='#0e1117')
PLOT_TPL = 'plotly_dark'

_nc = sum(v == 'Cripto' for v in CLASE.values())
print(f'Activo principal: {PRIMARY} | {INTERVAL} / {PERIOD}')
print(f'Universo: {len(UNIVERSE)} activos  ·  {_nc} cripto + {len(UNIVERSE)-_nc} ETF')
print('  Cripto:', ', '.join(t for t in UNIVERSE if CLASE[t]=='Cripto'))
print('  ETF:   ', ', '.join(t for t in UNIVERSE if CLASE[t]!='Cripto'))'''

nb = json.loads(pathlib.Path('crypto_analysis.ipynb').read_text(encoding='utf-8'))
patched = []

def set_src(cell, text):
    lines = text.splitlines(True)
    if lines and lines[-1].endswith('\n'): lines[-1] = lines[-1][:-1]
    cell['source'] = lines
    cell['outputs'] = []
    cell['execution_count'] = None

for c in nb['cells']:
    if c['cell_type'] != 'code':
        continue
    s = ''.join(c['source'])

    # 1) Celda de configuración del universo
    if 'UNIVERSE = {' in s and 'PRIMARY' in s and 'CONFIGURACIÓN GLOBAL' in s:
        set_src(c, NEW_CONFIG); patched.append('config-universo'); continue

    # 2) Quitar la CLASE estática de la celda DCA
    if 'CLASE = {' in s and 'WEEKLY_CAPITAL' in s:
        import re
        s2 = re.sub(r"CLASE = \{[^}]*\}\n\n", "# CLASE se define en la Sección 1 (universo dinámico)\n\n", s, count=1)
        set_src(c, s2); patched.append('quitar-clase-estatica'); continue

    # 3) Fecha actual en lugar de la última vela semanal
    if "fecha_hoy = WKI[PRIMARY].index[-1].strftime('%d/%m/%Y')" in s:
        s2 = s.replace("fecha_hoy = WKI[PRIMARY].index[-1].strftime('%d/%m/%Y')",
                       "fecha_hoy = datetime.now().strftime('%d/%m/%Y')")
        set_src(c, s2); patched.append('fecha-actual'); continue

    # 4) Etiqueta cripto/ETF en el mensaje
    if "L.append(f'   • <b>{tk}</b> ({UNIVERSE[tk]}): invierte <b>{pct:.0f}%</b>')" in s:
        s2 = s.replace(
            "L.append(f'   • <b>{tk}</b> ({UNIVERSE[tk]}): invierte <b>{pct:.0f}%</b>')",
            "tipo = '🪙 CRIPTO' if CLASE[tk]=='Cripto' else '📈 ETF'\n"
            "            L.append(f'   • <b>{tk}</b> [{tipo}] — {UNIVERSE[tk]}: invierte <b>{pct:.0f}%</b>')")
        set_src(c, s2); patched.append('etiqueta-tipo'); continue

nb['cells'] = nb['cells']
pathlib.Path('crypto_analysis.ipynb').write_text(
    json.dumps(nb, ensure_ascii=False, indent=1), encoding='utf-8')
print('Parches aplicados:', patched)
assert set(patched) >= {'config-universo','quitar-clase-estatica','fecha-actual','etiqueta-tipo'}, 'Faltan parches'
