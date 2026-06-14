# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A single Jupyter notebook (`crypto_analysis.ipynb`) that runs an end-to-end quantitative analysis of crypto + ETF markets and produces a long-term DCA (dollar-cost-averaging) investment plan with weekly alerts. There is no app, no test suite, and no package — the notebook *is* the deliverable. Code, comments, and output are in Spanish; keep new code in Spanish to match.

## Environment & running

- Dependencies live in `venv/` (gitignored). Activate with `source venv/bin/activate`.
- `talib` requires the native TA-Lib C library, which is **not** pip-installable alone. `install_talib.sh` builds it from source and pip-installs the full stack (numpy, pandas, plotly, mplfinance, yfinance, TA-Lib). Other imports also needed: `prophet`, `scikit-learn`, `scipy`.
- Run the notebook top-to-bottom. Cells are **stateful and order-dependent** — `UNIVERSE` and `CLASE` are defined once in Section 1 and consumed everywhere downstream, so you cannot run a later cell in isolation without first running setup.
- Live network calls run at execution time: CoinGecko (`api.coingecko.com`) for the crypto universe and Yahoo Finance (`yfinance`) for prices and the ETF screener. Both have `try/except` fallbacks to hardcoded baskets when the API fails — preserve that pattern.

## Notebook architecture (the pipeline)

The 68 cells form one linear pipeline. Sections 1–12 do deep single-asset analysis of `PRIMARY` (BTC-USD); 13+ build the actual investment product.

- **§1 Setup** — `CONFIGURACIÓN GLOBAL` cell defines `PRIMARY`, `INTERVAL`, `PERIOD`, the **dynamic universe** (`UNIVERSE` ticker→name, `CLASE` ticker→'Cripto'/'Renta Variable'/'Refugio'), thresholds `BUY_TH`/`SELL_TH`, and the dark-theme color palette `COL`. Everything depends on this cell.
- **§2–6** — data acquisition (`get_data`), the indicator engine (`compute_indicators`), Fibonacci/volume-profile, support/resistance, candlestick patterns.
- **§7–8** — a composite confidence **score** per asset and a **backtest** of that score (with fees).
- **§9–11** — correlations, predictive models (Prophet + a GradientBoosting directional classifier), and a consolidated multi-asset dashboard.
- **§13 DCA engine** — eligibility filter (confirmed long-term uptrend), weekly-capital allocation, entry zones, and a DCA-vs-lump-sum simulation. This is the core long-term product.
- **§14 Optimization** — risk-adjusted metrics, a conviction crypto sleeve, and a **walk-forward backtest without lookahead** (the rentability proof).
- **§15 Gold sleeve + alerts** — adds a fixed gold sleeve, re-validates walk-forward, then `weekly_alert(plan_weights)` builds a percentage-based actionable alert.
- **§16 Notifications** — sends the alert via Telegram and/or email. Credentials come from env vars: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `SMTP_USER`, `SMTP_PASS`, `SMTP_TO`. Toggles `ENVIAR_TELEGRAM`/`ENVIAR_EMAIL` control delivery. Gmail needs an App Password.

## `_dynamic.py` — the notebook patcher

`_dynamic.py` is **not** part of the analysis. It is a maintenance script that loads `crypto_analysis.ipynb` as JSON and surgically rewrites four specific cells (the universe config, removing the static `CLASE`, using `datetime.now()` for the alert date, and adding crypto/ETF labels), then writes the notebook back. Run with `python3 _dynamic.py`. It matches cells by substring of their source — if you edit those cells, its `str.replace`/`re.sub` anchors will silently stop matching, and its closing `assert set(patched) >= {...}` will fail. Update the anchors when you change those cells.

## Conventions

- `*.html` is gitignored: `crypto_analysis.html`, `quant_report.html`, `etf_analysis.html`, and `alerta_semanal.html` are generated reports, not source — don't commit them.
- Plotly charts use `template='plotly_dark'` and the `COL` palette; keep new visuals consistent.
- Never hardcode credentials in cells — read from `os.environ` with an empty-string default, as §16 already does.
