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

## Notebook architecture (62 cells)

One linear pipeline that **funnels to a single visible recommendation**. Sections §2–12 analyse `PRIMARY` (BTC-USD) in depth (research); §13–14 build + validate the investment engine **silently**; §15 renders the one actionable output. Cell indices below are approximate — the reorg deleted 9 redundant preview cells, so match by cell `id`/content, not by number.

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

### §13 Motor DCA (silent engine) — id prefix `dca_cd*`
Core investment engine. **All allocation previews here are silenced** (deleted or display-stripped) so nothing competes with the §15 recommendation.
- **`dca_cd01`** — `MONTHLY_CAPITAL`, `MAX_PER_ASSET`, `TOP_N`, `get_weekly()`. Downloads 5y weekly data into `WK`. **Stale filter**: assets whose last candle is >30 days old are excluded — catches delisted tickers without errors.
- **`dca_cd02`** — `supertrend_signal()`, `lt_features()`, `dca_score(x, ticker)` (3-pillar score 0–100: Tendencia 0–55 + Valor entrada 0–35 + Sentimiento 0–10). Builds `WKI` and `DCA`. Shows the DCA score ranking table (`dca_tbl`) — the one analytical table kept in §13.
- **`regime-code-01`** — `GaussianHMM(n_components=3)` on BTC weekly (ret4w, vol8w, RSIw); exposes `REGIME_NOW` (BULL/NEUTRAL/BEAR). **Guard in `opt_cd05`**: `REGIME_NOW = locals().get('REGIME_NOW', 'NEUTRAL')`.
- **`dca_cd04`** — eligibility filter (price > SMA40, trend_quality ≥ 35); ranks altcoins by MOM26, keeps top-`TOP_N` (BTC/ETH excluded from ranking); HRP-CVaR via `riskfolio_lib.HCPortfolio` → `weights`. Now **silent** (only a one-line print).
- **Deleted in reorg**: allocation donut, entry-zones table, DCA-vs-lump-sum sim, and the two big HTML "Plan DCA" cards. They duplicated the final recommendation.

### §14 Optimización + validación (silent engine) — id prefix `opt_cd*`
`perf_stats`, conviction sleeve (BTC+ETH 30% fixed), regime/FNG adjustments. `opt_cd05` builds `final_w`/`conv_w`/`trend_w` (**display silenced**). Kept **visible as evidence**: risk metrics (`opt_cd02/03`) and the walk-forward backtest (`opt_cd07/08`, `weights_at(t, mode)` with modes `btc`/`equal`/`conviction`/`hrp`/`strategy`). These are validation, not recommendations.

### §15 TU RECOMENDACIÓN DEL MES — THE PRODUCT — id prefix `al_cd*`, `nt_cd02`
- **`al_cd02`** — `final_w2` (base plan weights = conviction + trend) and `sleeve_of(tk)`. **Silent** (the base allocation is an engine input, never shown).
- **`al_cd04/05`** — strategy-comparison backtest (evidence). The old "sleeve de oro" markdown is vestigial — there is no gold in the crypto universe; markdown was relabeled to drop it.
- **`al_cd07`** — **`sell_score(tk)`** defined HERE first (needed before `monthly_alert` runs). Defines `APORTE_MULT` (see below) and **`monthly_alert(plan_weights)`** which:
  1. Classifies every universe asset by zone (EUFORIA / PULLBACK / OPORTUNIDAD / NORMAL / FUERA)
  2. Calls `sell_score(tk)` → `SELL_SCORE` column
  3. Applies **7-rule ACCIÓN_FINAL cascade** (see below) → `ACCIÓN_FINAL` column
  4. `Aporte base` = `final_w2` weight × capital; `Aporte ajustado` = base × `APORTE_MULT[acción]`, capped at `MAX_PER_ASSET × capital`
  5. Returns `alert` DataFrame — **source of truth for §15 and §17**
  Then builds the **two plans**: `PLAN_PRUDENTE`/`CASH_PRUDENTE` (deploy only what signals justify, hold the rest as cash; rescaled down if adjusted total > capital) and `PLAN_TODO`/`CASH_TODO` (redeploy the freed cash into the top-3 external 🔵/🟢 buy signals, proportional to DCA Score, per-asset capped).
- **`nt_cd02`** — `_lineas()` — the **only visible output of the notebook**. Single scannable panel: `▎ PLAN RECOMENDADO — prudente` (COMPRA AHORA + 💵 efectivo a guardar) · `▎ SI PREFIERES DESPLEGAR TODO` (freed cash → best buys) · `▎ 👀 EN OBSERVACIÓN` (top-6 weak candidates) · `▎ ⚫ NO ACUMULAR` (⚫/🔴) · footer "Cómo usarlo".

**`APORTE_MULT`** (in `al_cd07`) — makes deployed dollars coherent with the signal:
`🔴 REDUCIR/SALIR`→×0 · `⚫ PAUSAR`→×0 · `🟠 REDUCIR PARCIAL`→×0.5 · `🟡 NORMAL`→×1.0 · `🟢 SOBREPONDERAR`→×1.25 · `🔵 DOBLAR`→×1.5 (capped `MAX_PER_ASSET`).

### §17 Señales de Venta (`sell-code-01`) — secondary detail table
- Redefines `sell_score(tk)` (overwrites `al_cd07` definition, no conflict). Builds `sell_tbl` with `Zona DCA` and `Acción` **imported from `alert['ACCIÓN_FINAL']`** (never recalculated). Now **displays** a styled sell-signals/rebalance table (SELL_SCORE + technical signal + hypothetical 52w equal-weight deviation vs `TARGET_WEIGHT`) as a secondary detail view under the main recommendation. `_classify()` kept as fallback.

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

- `sell_score()` is intentionally defined twice: `al_cd07` (early, for `monthly_alert`) and `sell-code-01` (§17, overwrites). Do not collapse into one — the ordering dependency is load-bearing.
- `ACCIÓN_FINAL` in `alert` is the single source of truth. §17's `sell_tbl['Acción']` must import from `alert`, never recalculate independently.
- **`Aporte ajustado` must stay coherent with `ACCIÓN_FINAL`** via `APORTE_MULT`. Never show a "reduce" action next to a full contribution again — that contradiction was the whole point of the reorg.
- `PLAN_PRUDENTE` + `CASH_PRUDENTE` must sum to `MONTHLY_CAPITAL`; `PLAN_TODO` = prudente + freed cash into external buys. Both are built in `al_cd07` and only rendered in `nt_cd02`.
- Stale filter threshold is 30 days (`dca_cd01`). If a ticker's last candle > 30 days old, it's excluded from `WK`, `WKI`, `DCA`, and therefore the alert.
- **`nt_cd02` (`_lineas()`) is the primary product output** (the buy recommendation). Other visible cells are supporting, not competing: `dca_cd02` (score ranking), `regime-code-01`, validation backtests (`opt_cd02/03`, `opt_cd07/08`, `al_cd04/05`), and `sell-code-01` (§17 sell-signals detail table). The deleted preview cells were the ones that *duplicated* the recommendation — don't reintroduce a second $-allocation table.

## `_dynamic.py` — notebook patcher (LEGACY / defunct)

Not part of the analysis. It once converted a static universe/config into the dynamic (CoinGecko) version by substring-matching and rewriting cells. **All 4 of its anchors already fail to match the current notebook** (the dynamic universe is baked into the committed cells; params use `MONTHLY_CAPITAL` not the old `WEEKLY_CAPITAL`; the output cell was rewritten). Running `python3 _dynamic.py` today just trips its closing `assert`. Treat it as dead unless you deliberately resurrect it — if you do, rewrite the anchors against the current cells first.

## Conventions

- `*.html` files are gitignored — generated reports, never commit.
- Plotly charts use `template='plotly_dark'` and the `COL` palette.
- Never hardcode credentials — read from `os.environ` with empty-string default.
- No Telegram/email delivery cells in the notebook. The alert is printed to cell output only.
- The notebook is committed with outputs so the alert is visible on GitHub without running it.
