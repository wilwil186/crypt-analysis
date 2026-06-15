# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A single Jupyter notebook (`crypto_analysis.ipynb`) that runs an end-to-end quantitative analysis of the top-20 crypto market and produces a **monthly DCA investment alert** — the only visible output. No app, no test suite, no package. Code, comments, and output are in Spanish; keep new code in Spanish to match.

## Environment & running

- Dependencies live in `venv/` (gitignored). Activate with `source venv/bin/activate`.
- `talib` requires the native TA-Lib C library — **not** pip-installable alone. `install_talib.sh` builds it from source and installs: `numpy`, `pandas`, `plotly`, `mplfinance`, `yfinance`, `TA-Lib`, `prophet`, `scikit-learn`, `scipy`.
- Additional pip installs required: `riskfolio-lib`, `hmmlearn`, `feedparser`, `vaderSentiment`.
- Run the notebook **top-to-bottom**. Cells are stateful and order-dependent — never run a later cell in isolation.
- Live network calls at execution time: CoinGecko (`api.coingecko.com`) for the dynamic universe, Yahoo Finance (`yfinance`) for prices, Alternative.me (`api.alternative.me/fng`) for Fear & Greed, and 4 RSS feeds for news sentiment. All have `try/except` fallbacks to hardcoded defaults — preserve that pattern.

## Notebook architecture (71 cells)

One linear pipeline. Sections §2–12 analyse `PRIMARY` (BTC-USD) in depth; §13+ build the investment product.

### §1 Setup (cells 01–04)
- **Cell 03** `CONFIGURACIÓN GLOBAL` — defines `PRIMARY`, `INTERVAL`, `PERIOD`, the dynamic universe (`UNIVERSE` ticker→name from CoinGecko top-20, fallback hardcoded), `BUY_TH`/`SELL_TH`, `TARGET_WEIGHT`, `REBAL_THRESHOLD`, palette `COL`. **Everything depends on this cell.**
- **Cell 04** `fetch_fng()` — queries Alternative.me; exposes `FNG_VALUE` (int 0–100) and `FNG_LABEL`. Used by `dca_score()` (penalty −15 when FNG > 80) and `_lineas()` (badge in header).

### §2–6 BTC-USD deep analysis (cells 05–16)
`get_data`, `compute_indicators` (EMA/RSI/MACD/ATR/BB/ADX/SuperTrend etc.), Fibonacci + Volume Profile, support/resistance, candle patterns.

### §7–8 Scoring + backtest (cells 17–21)
Daily technical score, backtesting with fees.

### §9–10 Correlations + predictive models (cells 22–27)
Correlation matrix, Prophet 30-day forecast, GradientBoosting 5-day classifier (AUC typically ~0.45 — treat as weak signal).

### §16 Sentimiento de Noticias (cells 28–29)
`fetch_news_sentiment(tickers)` — reads up to 60 articles from 4 RSS feeds (CoinTelegraph, CoinDesk, CryptoSlate, Decrypt); applies VADER; produces `NEWS_SENTIMENT = {ticker: {score, n_articles, headlines}}`. Third pillar of `dca_score()`.

### §11 Dashboard multi-activo (cells 30–32)
Styled table with score + sentiment column (`_sent_emoji(NEWS_SENTIMENT[tk]['score'])`).

### §12 Conclusiones (cells 33–34)

### §13 Motor DCA (cells 35–48)
Core investment product:
- **Cell 36** — `MONTHLY_CAPITAL`, `MAX_PER_ASSET`, `TOP_N`, `get_weekly()`. Downloads 5y weekly data into `WK`. **Stale filter**: assets whose last candle is >30 days old are excluded — catches delisted tickers without errors.
- **Cell 37** — `supertrend_signal()`, `lt_features()`, `dca_score(x, ticker)` (3-pillar score 0–100: Tendencia 0–55 + Valor entrada 0–35 + Sentimiento 0–10). Builds `WKI` and `DCA`.
- **Cell 39** — `GaussianHMM(n_components=3)` on BTC weekly (ret4w, vol8w, RSIw); exposes `REGIME_NOW` (BULL/NEUTRAL/BEAR). **Guard in cell 54**: `REGIME_NOW = locals().get('REGIME_NOW', 'NEUTRAL')`.
- **Cell 41** — eligibility filter (price > SMA40, trend_quality ≥ 35); ranks altcoins by MOM26, keeps top-`TOP_N` (BTC/ETH excluded from ranking); HRP-CVaR via `riskfolio_lib.HCPortfolio`.
- Cells 42–48: allocation charts, entry zones, DCA-vs-lump-sum simulation, plan table.

### §14 Optimización (cells 49–59)
`perf_stats`, conviction sleeve (BTC+ETH 30% fixed), regime/FNG adjustments, walk-forward backtest (`weights_at(t, mode)` with modes: `btc`, `equal`, `conviction`, `hrp`, `strategy`).

### §15 Sistema de Alertas (cells 60–68) — THE PRODUCT
- **Cell 62** — `final_w2` (conviction + trend weights), `sleeve_of(tk)`.
- **Cell 64–65** — walk-forward v2 validation.
- **Cell 67** — **`sell_score(tk)`** defined HERE first (needed before `monthly_alert` runs). Also defines **`monthly_alert(plan_weights)`** which:
  1. Classifies every universe asset by zone (EUFORIA / PULLBACK / OPORTUNIDAD / NORMAL / FUERA)
  2. Calls `sell_score(tk)` → adds `SELL_SCORE` column
  3. Applies **7-rule ACCIÓN_FINAL cascade** (see below) → adds `ACCIÓN_FINAL` column
  4. Applies `Aporte ajustado` multipliers: 🔴→×0, 🟠→×0.5, 🟡/🟢→×1, 🔵→×1.5 (capped `MAX_PER_ASSET`)
  5. Returns `alert` DataFrame — **source of truth for both §15 and §17**
- **Cell 68** — `_lineas()` — the **only visible output** of the entire notebook. Three blocks: 💼 CARTERA (plan assets with ACCIÓN_FINAL + Aporte ajustado), 💡 CANDIDATOS (all 🔵 + top-3 🟢 by score), ⚫ PAUSAR DCA. Contextual footer.

### §17 Señales de Venta (cells 69–70) — silent computation
- **Cell 70** — redefines `sell_score(tk)` (overwrites cell 67 definition, no conflict). Builds `sell_tbl` with `Zona DCA` and `Acción` imported from `alert['ACCIÓN_FINAL']`. **No display, no chart, no print** — internal only. `_classify()` kept as fallback.

## ACCIÓN_FINAL — 7 rules (priority order)

```
1. SELL_SCORE > 70                           → 🔴 REDUCIR / SALIR
2. SELL_SCORE > 45                           → 🟠 REDUCIR PARCIAL
3. zona contains '⚫ FUERA'                  → ⚫ PAUSAR DCA
4. zona contains '🔴 EUFORIA'               → 🟠 REDUCIR PARCIAL
5. SELL_SCORE ≤ 45 AND zona '🔵 OPORTUNIDAD' → 🔵 DOBLAR APORTE
6. SELL_SCORE ≤ 45 AND zona '🟢 PULLBACK'    → 🟢 SOBREPONDERAR
7. else                                      → 🟡 APORTE NORMAL
```

Rules 1–2 (sell signals) always override buy zones — no contradictions.

## Key invariants

- `sell_score()` is intentionally defined twice: cell 67 (early, for `monthly_alert`) and cell 70 (§17, overwrites). Do not collapse into one — the ordering dependency is load-bearing.
- `ACCIÓN_FINAL` in `alert` is the single source of truth. §17's `sell_tbl['Acción']` must import from `alert`, never recalculate independently.
- Stale filter threshold is 30 days (cell 36). If a ticker's last candle > 30 days old, it's excluded from `WK`, `WKI`, `DCA`, and therefore the alert.
- `_lineas()` (cell 68) is the only cell that produces visible output in the final section. All other §15/§17 cells are silent.

## `_dynamic.py` — notebook patcher

Not part of the analysis. Loads the notebook as JSON and surgically rewrites specific cells. Matches by substring — if you edit those cells, its anchors silently stop matching and the closing `assert` fails. **Update the anchors when you change the target cells.** Run with `python3 _dynamic.py`.

## Conventions

- `*.html` files are gitignored — generated reports, never commit.
- Plotly charts use `template='plotly_dark'` and the `COL` palette.
- Never hardcode credentials — read from `os.environ` with empty-string default.
- No Telegram/email delivery cells in the notebook. The alert is printed to cell output only.
- The notebook is committed with outputs so the alert is visible on GitHub without running it.
