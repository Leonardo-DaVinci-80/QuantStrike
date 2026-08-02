# Changelog

All notable changes to QuantStrike will be documented in this file.

## [Unreleased]

### Added
- Historical price chart with range selector (1W / 1M / 3M / 1Y / All)
- Volume bar chart displayed beneath the price chart, sharing the same x-axis
- `average_price` and `standard_deviation` metrics added to Market Statistics
- Support for vanilla items (knives/gloves with no finish or wear condition)
- Variant selector (Normal / StatTrak™ / Souvenir) now correctly filters to only
  the variants that actually exist for a given skin

### Fixed
- `parse_name()` no longer silently returns `None` for valid skin names
  (unreachable `return` inside a dead `else` branch)
- Variant/condition selection no longer throws `NameError` when a search
  returns no results
- Removed duplicated "Market Statistics" and skin-info block in `Home.py`
- Non-wear items (e.g. stickers with tournament/edition names instead of wear
  conditions) no longer produce an empty condition dropdown

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