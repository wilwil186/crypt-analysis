import json
from datetime import datetime
import requests
import hmac
import hashlib
import time

class BinancePortfolio:
    def __init__(self, api_key=None, api_secret=None):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = 'https://api.binance.com'
        self.assets = []
    
    def _sign_request(self, params):
        query_string = '&'.join([f"{key}={value}" for key, value in params.items()])
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def get_account_balance(self):
        if not self.api_key or not self.api_secret:
            print("Error: Se requieren API Key y Secret")
            return None
        
        timestamp = int(time.time() * 1000)
        params = {'timestamp': timestamp}
        signature = self._sign_request(params)
        
        headers = {'X-MBX-APIKEY': self.api_key}
        url = f'{self.base_url}/api/v3/account'
        
        try:
            response = requests.get(
                url,
                headers=headers,
                params={**params, 'signature': signature}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error al obtener balance: {e}")
            return None
    
    def get_all_prices(self):
        try:
            url = f'{self.base_url}/api/v3/ticker/price'
            response = requests.get(url)
            response.raise_for_status()
            prices = {item['symbol']: float(item['price']) for item in response.json()}
            return prices
        except Exception as e:
            print(f"Error al obtener precios: {e}")
            return {}
    
    def load_from_api(self, min_value_usd=1):
        print("Conectando con Binance API...")
        account_data = self.get_account_balance()
        
        if not account_data:
            print("No se pudo obtener datos de la cuenta")
            return False
        
        print("Obteniendo precios actuales...")
        prices = self.get_all_prices()
        
        self.assets = []
        
        for balance in account_data.get('balances', []):
            asset = balance['asset']
            free = float(balance['free'])
            locked = float(balance['locked'])
            total = free + locked
            
            if total > 0:
                current_price = 0
                
                if asset in ['USDT', 'BUSD', 'USDC', 'TUSD']:
                    current_price = 1.0
                else:
                    for quote in ['USDT', 'BUSD', 'USDC']:
                        symbol = f'{asset}{quote}'
                        if symbol in prices:
                            current_price = prices[symbol]
                            break
                
                value_usd = total * current_price
                
                if value_usd >= min_value_usd:
                    self.assets.append({
                        'symbol': asset,
                        'quantity': total,
                        'free': free,
                        'locked': locked,
                        'current_price': current_price,
                        'value_usd': value_usd,
                        'buy_price': 0,
                        'source': 'api'
                    })
        
        self.assets.sort(key=lambda x: x['value_usd'], reverse=True)
        
        print(f"✓ Cargados {len(self.assets)} activos desde Binance")
        print(f"✓ Valor total: ${sum(a['value_usd'] for a in self.assets):.2f}")
        
        return True
    
    def add_manual(self, symbol, quantity, buy_price, current_price=None):
        if current_price is None:
            prices = self.get_all_prices()
            symbol_pair = f'{symbol}USDT'
            current_price = prices.get(symbol_pair, 0)
        
        value_usd = quantity * current_price
        
        self.assets.append({
            'symbol': symbol.upper(),
            'quantity': float(quantity),
            'free': float(quantity),
            'locked': 0,
            'current_price': float(current_price),
            'value_usd': value_usd,
            'buy_price': float(buy_price),
            'source': 'manual'
        })
    
    def update_buy_price(self, symbol, buy_price):
        for asset in self.assets:
            if asset['symbol'] == symbol:
                asset['buy_price'] = float(buy_price)
                print(f"✓ Precio de compra actualizado para {symbol}: ${buy_price}")
                return True
        print(f"✗ No se encontró {symbol} en el portfolio")
        return False
    
    def calculate_totals(self):
        total_value = sum(a['value_usd'] for a in self.assets)
        total_cost = sum(a['quantity'] * a['buy_price'] for a in self.assets if a['buy_price'] > 0)
        total_pl = total_value - total_cost
        
        assets_with_cost = [a for a in self.assets if a['buy_price'] > 0]
        
        return {
            'total_value': total_value,
            'total_cost': total_cost,
            'total_pl': total_pl,
            'total_pl_percent': (total_pl / total_cost * 100) if total_cost > 0 else 0,
            'assets_count': len(self.assets),
            'assets_with_pl': len(assets_with_cost)
        }
    
    def generate_html(self, filename='binance_portfolio.html'):
        totals = self.calculate_totals()
        
        table_rows = ''
        for asset in self.assets:
            value = asset['value_usd']
            cost = asset['quantity'] * asset['buy_price'] if asset['buy_price'] > 0 else 0
            pl = value - cost if asset['buy_price'] > 0 else 0
            pl_percent = (pl / cost * 100) if cost > 0 else 0
            
            pl_color = 'positive' if pl >= 0 else 'negative'
            
            buy_price_str = f"${asset['buy_price']:.2f}" if asset['buy_price'] > 0 else '<span style="color:#999">N/A</span>'
            pl_str = f'<span class="{pl_color}"><strong>${pl:.2f}</strong></span>' if asset['buy_price'] > 0 else '<span style="color:#999">N/A</span>'
            pl_percent_str = f'<span class="{pl_color}"><strong>{pl_percent:+.2f}%</strong></span>' if asset['buy_price'] > 0 else '<span style="color:#999">N/A</span>'
            
            locked_display = f'<br><small style="color:#999">Bloqueado: {asset["locked"]:.8f}</small>' if asset['locked'] > 0 else ''
            
            table_rows += f'''
                <tr>
                    <td><strong>{asset['symbol']}</strong></td>
                    <td>{asset['quantity']:.8f}{locked_display}</td>
                    <td>{buy_price_str}</td>
                    <td>${asset['current_price']:.8f}</td>
                    <td><strong>${value:.2f}</strong></td>
                    <td>{pl_str}</td>
                    <td>{pl_percent_str}</td>
                </tr>
            '''
        
        chart_labels = [a['symbol'] for a in self.assets[:10]]
        chart_values = [a['value_usd'] for a in self.assets[:10]]
        
        assets_with_pl = [a for a in self.assets if a['buy_price'] > 0]
        pl_labels = [a['symbol'] for a in sorted(assets_with_pl, key=lambda x: (x['value_usd'] - x['quantity'] * x['buy_price']), reverse=True)]
        pl_values = [(a['value_usd'] - a['quantity'] * a['buy_price']) for a in sorted(assets_with_pl, key=lambda x: (x['value_usd'] - x['quantity'] * x['buy_price']), reverse=True)]
        
        perf_labels = [a['symbol'] for a in sorted(assets_with_pl, key=lambda x: ((a['current_price'] - a['buy_price']) / a['buy_price'] * 100) if a['buy_price'] > 0 else 0, reverse=True)]
        perf_values = [((a['current_price'] - a['buy_price']) / a['buy_price'] * 100) if a['buy_price'] > 0 else 0 for a in sorted(assets_with_pl, key=lambda x: ((a['current_price'] - a['buy_price']) / a['buy_price'] * 100) if a['buy_price'] > 0 else 0, reverse=True)]
        
        total_pl_color = 'positive' if totals['total_pl'] >= 0 else 'negative'
        
        html_content = f'''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Portfolio Binance</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #f7931a 0%, #f5a623 100%);
            padding: 20px;
            min-height: 100vh;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}

        h1 {{
            color: white;
            text-align: center;
            margin-bottom: 10px;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}

        .subtitle {{
            color: rgba(255,255,255,0.9);
            text-align: center;
            margin-bottom: 30px;
            font-size: 1.1em;
        }}

        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}

        .summary-card {{
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 8px 16px rgba(0,0,0,0.2);
            text-align: center;
        }}

        .summary-card h3 {{
            color: #555;
            margin-bottom: 10px;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        .summary-card .amount {{
            font-size: 2em;
            font-weight: bold;
            color: #f7931a;
        }}

        .summary-card .change {{
            margin-top: 10px;
            font-size: 1.2em;
            font-weight: bold;
        }}

        .positive {{ color: #10b981; }}
        .negative {{ color: #ef4444; }}

        .content {{
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 8px 16px rgba(0,0,0,0.2);
            margin-bottom: 20px;
        }}

        h2 {{
            color: #f7931a;
            margin-bottom: 20px;
            font-size: 1.8em;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 30px;
        }}

        th {{
            background: #f7931a;
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: bold;
        }}

        td {{
            padding: 15px;
            border-bottom: 1px solid #eee;
        }}

        tr:hover {{
            background: #fff8f0;
        }}

        .charts {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }}

        .chart-container {{
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 8px 16px rgba(0,0,0,0.2);
        }}

        .chart-container h3 {{
            text-align: center;
            margin-bottom: 20px;
            color: #f7931a;
            font-size: 1.3em;
        }}

        .timestamp {{
            text-align: center;
            color: white;
            margin-top: 20px;
            font-size: 0.9em;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
        }}

        .info-note {{
            background: #fff3cd;
            border-left: 4px solid #f7931a;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 5px;
            color: #856404;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔸 Portfolio Binance</h1>
        <div class="subtitle">Control y análisis de criptomonedas</div>

        <div class="summary">
            <div class="summary-card">
                <h3>Valor Total</h3>
                <div class="amount">${totals['total_value']:.2f}</div>
            </div>
            <div class="summary-card">
                <h3>Total Activos</h3>
                <div class="amount">{totals['assets_count']}</div>
            </div>
            <div class="summary-card">
                <h3>Inversión Total</h3>
                <div class="amount">${totals['total_cost']:.2f}</div>
            </div>
            <div class="summary-card">
                <h3>Ganancia/Pérdida</h3>
                <div class="amount {total_pl_color}">${totals['total_pl']:+.2f}</div>
                <div class="change {total_pl_color}">{totals['total_pl_percent']:+.2f}%</div>
            </div>
        </div>

        <div class="content">
            <h2>📋 Detalle de Activos</h2>
            
            {f'<div class="info-note">💡 <strong>Nota:</strong> {totals["assets_with_pl"]} de {totals["assets_count"]} activos tienen precio de compra registrado. Los activos sin precio de compra no muestran ganancia/pérdida.</div>' if totals['assets_with_pl'] < totals['assets_count'] else ''}
            
            <table>
                <thead>
                    <tr>
                        <th>Activo</th>
                        <th>Cantidad</th>
                        <th>Precio Compra</th>
                        <th>Precio Actual</th>
                        <th>Valor Total</th>
                        <th>G/P ($)</th>
                        <th>G/P (%)</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
        </div>

        <div class="charts">
            <div class="chart-container">
                <h3>Top 10 Activos por Valor</h3>
                <canvas id="assetsChart"></canvas>
            </div>
            {'<div class="chart-container"><h3>Ganancia/Pérdida por Activo</h3><canvas id="plChart"></canvas></div>' if len(pl_labels) > 0 else ''}
            {'<div class="chart-container"><h3>Performance (%) por Activo</h3><canvas id="perfChart"></canvas></div>' if len(perf_labels) > 0 else ''}
        </div>

        <div class="timestamp">
            Generado el {datetime.now().strftime('%d/%m/%Y a las %H:%M:%S')}
        </div>
    </div>

    <script>
        new Chart(document.getElementById('assetsChart'), {{
            type: 'bar',
            data: {{
                labels: {json.dumps(chart_labels)},
                datasets: [{{
                    label: 'Valor (USD)',
                    data: {json.dumps(chart_values)},
                    backgroundColor: '#f7931a'
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{ display: false }},
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                return '$' + context.parsed.y.toFixed(2);
                            }}
                        }}
                    }}
                }},
                scales: {{
                    y: {{ 
                        beginAtZero: true,
                        ticks: {{
                            callback: function(value) {{
                                return '$' + value.toFixed(0);
                            }}
                        }}
                    }}
                }}
            }}
        }});

        {f'''
        new Chart(document.getElementById('plChart'), {{
            type: 'bar',
            data: {{
                labels: {json.dumps(pl_labels)},
                datasets: [{{
                    label: 'G/P (USD)',
                    data: {json.dumps(pl_values)},
                    backgroundColor: {json.dumps(pl_values)}.map(v => v >= 0 ? '#10b981' : '#ef4444')
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{ display: false }},
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                return '$' + context.parsed.y.toFixed(2);
                            }}
                        }}
                    }}
                }},
                scales: {{
                    y: {{ 
                        beginAtZero: true,
                        ticks: {{
                            callback: function(value) {{
                                return '$' + value.toFixed(0);
                            }}
                        }}
                    }}
                }}
            }}
        }});
        ''' if len(pl_labels) > 0 else ''}

        {f'''
        new Chart(document.getElementById('perfChart'), {{
            type: 'bar',
            data: {{
                labels: {json.dumps(perf_labels)},
                datasets: [{{
                    label: 'Performance (%)',
                    data: {json.dumps(perf_values)},
                    backgroundColor: {json.dumps(perf_values)}.map(v => v >= 0 ? '#10b981' : '#ef4444')
                }}]
            }},
            options: {{
                responsive: true,
                indexAxis: 'y',
                plugins: {{
                    legend: {{ display: false }},
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                return context.parsed.x.toFixed(2) + '%';
                            }}
                        }}
                    }}
                }},
                scales: {{
                    x: {{ 
                        beginAtZero: true,
                        ticks: {{
                            callback: function(value) {{
                                return value + '%';
                            }}
                        }}
                    }}
                }}
            }}
        }});
        ''' if len(perf_labels) > 0 else ''}
    </script>
</body>
</html>'''
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"\n✓ Portfolio generado: {filename}")
        return filename


if __name__ == '__main__':
    API_KEY = 'bg4e2OtRu1vsJj3pbbMfddiN45nxRt7VZYQSH2BFUsHd0E4aiBB0Bc3Z2oYVSKx5'
    API_SECRET = 'hqQBdms16CKeXt21XK5EY3czofBj29EqJXBPbFPzhNiyEJqnx8KColpkPyjqnbRF'
    
    portfolio = BinancePortfolio(API_KEY, API_SECRET)
    
    portfolio.load_from_api(min_value_usd=1)
    
    portfolio.update_buy_price('BTC', 45000)
    portfolio.update_buy_price('ETH', 2500)
    portfolio.update_buy_price('BNB', 300)
    
    portfolio.generate_html('binance_portfolio.html')