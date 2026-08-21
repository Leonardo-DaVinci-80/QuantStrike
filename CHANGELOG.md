# Changelog

All notable changes to QuantStrike will be documented in this file.

## v1.3.0 - Market Intelligence Update — 2026-08-21

### Added

#### Market Overview
- Added initial Market Overview dashboard.
- Added historical QuantStrike Index (QSI).
- Added market-wide return analysis.
- Added market breadth analysis showing advancing, declining, and unchanged assets.
- Added initial placeholders for category-level market indices, including:
  - Rifles
  - Pistols
  - SMGs
  - Machine Guns
  - Shotguns
  - Knives
  - Gloves
  - Stickers
  - Agents
  - Cases
- Added Top Gainers and Top Losers sections.
- Added Market Heatmap placeholder.

#### QSI
- Added equal-weighted QSI methodology with a base value of 1,000.
- Added a minimum 50% market coverage requirement for QSI calculations.
- Added a ±50% cap on individual asset returns to reduce the effect of extreme historical outliers.
- Added QSI diagnostic analysis for market coverage, returns, and index behavior.

#### Market.CSGO
- Added Market.CSGO price API integration.
- Added Market.CSGO historical item discovery.
- Added Market.CSGO historical sales history retrieval.
- Added coverage testing between Market.CSGO and the QuantStrike tracked dataset.
- Achieved 96.37% historical coverage across the 9,488 assets tracked by QuantStrike.

### Improved
- Improved market-wide data processing through a daily price matrix and return matrix.
- Improved QSI stability by filtering low-coverage periods and capping extreme individual returns.

### Notes
- Market Overview currently uses the historical QuantStrike dataset.
- Live Market.CSGO data will be connected in a future update.

## v1.2.0 - Advanced Analytics Update

### Added
- Expanded demo dataset to ~9,500 CS2 skins
- Moving average trend analysis (30D / 90D)
- Historical drawdown visualization
- Interactive performance comparison charts
- Return correlation scatter plot
- Additional quantitative risk analysis tools

### Improved
- Analytics dashboard now provides deeper market analysis
- Increased searchable skin coverage
- Improved comparison experience between assets

### Removed
- Removed redundant backend analytics files

## [v1.1.0] - 2026-08-05

### Added

#### Analytics Page Improvements
- Added two-skin comparison analytics dashboard.
- Added comparison table for:
  - Current price
  - Weekly return
  - Monthly return
  - Annual return
  - CAGR
  - Daily volatility
  - Maximum drawdown
  - Standard deviation
  - Sharpe ratio

#### Correlation Analysis
- Added Pearson return correlation analysis between two skins.
- Added correlation strength classification.
- Added observation count to provide statistical context.
- Added return correlation scatter plot visualization.

#### Quantitative Metrics
- Added Sharpe Ratio calculation to `MarketMetrics`.
- Sharpe Ratio assumes a risk-free rate of 0 because CS skins do not have a traditional risk-free alternative.
- Documented assumptions behind applying financial metrics to CS skin markets.

### Improved

#### Analytics Architecture
- Expanded quantitative analysis capabilities.
- Improved separation between:
  - Market data collection
  - Financial calculations
  - Correlation analysis
  - Frontend visualization

### Notes

This release advances QuantStrike from a historical price tracking tool into a quantitative market analysis platform for CS skin markets.


---

## [1.0.0] - 2026-08-02

### Added
- Historical price chart with range selector (1W / 1M / 3M / 1Y / All)
- Volume bar chart displayed beneath the price chart, sharing the same x-axis
- `average_price` and `standard_deviation` metrics added to Market Statistics
- Support for vanilla items (knives/gloves with no finish or wear condition)
- Variant selector (Normal / StatTrak™ / Souvenir) now correctly filters to only
  the variants that actually exist for a given skin
- Rotating placeholder text in the search box (locked per session via
  `st.session_state`)
- "Coming soon" pages for Market, Skin, Portfolio, and Analytics, so sidebar
  navigation no longer shows blank pages
- Curated 928-item demo dataset (`data/demo/`) for fast deployment on
  Streamlit Cloud, built via `scripts/build_demo_dataset.py`
- Info expander on the home page listing example searchable skins in the
  demo dataset, generated dynamically from the loaded index
- Deployed live on Streamlit Community Cloud

### Fixed
- `parse_name()` no longer silently returns `None` for valid skin names
  (unreachable `return` inside a dead `else` branch)
- `parse_name()` now correctly handles vanilla knives/gloves (names with no
  `" | "` separator) instead of raising `ValueError`
- Variant/condition selection no longer throws `NameError` when a search
  returns no results
- Removed duplicated "Market Statistics" and skin-info block in `Home.py`
- Non-wear items (e.g. stickers with tournament/edition names instead of wear
  conditions) no longer produce an empty condition dropdown
- Search box now tolerates a full name with condition (e.g.
  `"Desert Eagle | Blaze (Factory New)"`) by stripping the trailing
  parenthetical before matching
- Fixed missing `@property` decorator on `average_price`
- Consistent 4-column grid for Market Statistics metrics (was an uneven
  3+2 split)
- Replaced hardcoded local Windows paths with relative, deployment-safe paths
- Flattened repository structure (removed redundant nested `QuantStrike/`
  folder) to match Streamlit Cloud's expected entrypoint path
- Moved `requirements.txt` to the repo root so Streamlit Cloud installs
  dependencies correctly (previously nested too deep to be detected)
- Pinned Python version via Streamlit Cloud's Advanced Settings to avoid
  incompatibility with newer Python releases lacking wheels for key
  dependencies (plotly, pandas)
- Removed accidentally tracked `__pycache__`/`.pyc` files from version control

### Known issues
- A small number of dataset entries (e.g. some stickers) have incomplete or
  malformed names in the source dataset and will correctly fail to resolve
  with "No skin found" — this reflects a data quality issue upstream, not a
  parsing bug

## [0.1.0] - Sprint 1
### Added
- `PricePoint` and `Skin` domain models
- `MarketMetrics` analytics engine: current price, daily change, all-time
  high/low, 52-week high/low, median price, total return, daily returns
- `CSVCollector` for loading historical price data
- `SkinRepository` for searching and resolving skins from the dataset index
- Initial Streamlit frontend (`Home.py`) with search, skin selection, and
  basic statistics display
- Unit tests for `MarketMetrics`