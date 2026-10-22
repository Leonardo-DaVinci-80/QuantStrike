# Next-cycle integration notes

This package preserves the existing QuantStrike files and adds separate feature modules/pages. No historical data is included.

## Added pages
- Advanced Charting: OHLC, MA, Bollinger Bands; DuckDB query is bounded to one asset and a maximum observation count.
- Portfolio: local transaction ledger, average-cost realized P&L, metadata-price snapshot valuation.
- Watchlist & Alerts: persistent local watchlist and alert rules. Alerts are evaluated manually on page interaction, not by a background scheduler.
- Market Intelligence: manual cross-market observation store; no live marketplace adapter is assumed.
- Strategy Backtesting: SMA crossover baseline with lagged signals and simplified fees.
- AI Analyst: reuses the existing Gemini client and passes compact derived facts.
- Research Journal: persistent notes and linked asset IDs.

## Data assumptions
The existing historical Parquet schema in `backend/analytics/skin_detail.py` is `skin_id`, `timestamp` (Unix seconds), `price`, `volume`. `backend/config.py` now defaults the feature repository to `data/processed/historical_prices.parquet`, matching existing pages. If your actual path/schema differs, set the documented environment variables.

## Limitations
- No live APIs for Steam, Skinport, Buff163, YouPin, or CSFloat are wired into the new cross-market page. Do not interpret manually entered prices as live quotes.
- Intraday bars require intraday observations. Daily observations cannot reconstruct hourly candles.
- Portfolio market value uses metadata snapshot prices; it is not live valuation and does not normalize currency or marketplace fees.
- SQLite is local/single-user. Hosted multi-user deployment needs authentication and a shared database.
- Alert evaluation is not scheduled and no email/push notifications are sent.
- The backtest is a research baseline, not financial advice; slippage, spread, liquidity, and execution constraints are not modeled.
- The package was statically compiled; run the app against your local Parquet data and benchmark RAM/latency before deployment.
