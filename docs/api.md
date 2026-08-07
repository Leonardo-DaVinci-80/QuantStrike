# QuantStrike API Documentation

## Overview

QuantStrike currently uses an internal Python-based API architecture.

The backend provides reusable services for retrieving market data and performing quantitative analysis.

Future versions may expose these services through a REST API.

---

# Repository API

## SkinRepository

Location:


backend/repositories/skin_repository.py


Responsible for retrieving CS2 skin information.

---

## Search Base Skins

```python
search_base_skins(query: str)

Searches available skins by name.

Parameters
Parameter	Type	Description
query	str	Search term
Returns
List[str]

Example:

[
    "AK-47 | Asiimov",
    "AK-47 | Redline"
]
Get Variants
get_variants(skin_name: str)

Returns available versions of a skin.

Includes:

Normal
StatTrak™
Souvenir
Wear conditions
Find Skin
find(name: str)

Retrieves complete skin metadata.

Returns:

Skin
Collector API
CSVCollector

Location:

backend/collectors/csv_collector.py
Load History
load_history(file_path)

Loads historical price data.

Returns:

List[PricePoint]

Example:

PricePoint(
    timestamp=date,
    price=120.50
)
Analytics API
MarketMetrics

Calculates financial statistics.

Example:

metrics = MarketMetrics(history)

Available properties:

current_price
daily_change
weekly_return
monthly_return
annual_return
cagr
volatility
standard_deviation
max_drawdown
sharpe_ratio
CorrelationAnalyzer

Compares two assets.

Example:

analysis = CorrelationAnalyzer(
    history_a,
    history_b
)

Returns:

correlation
correlation_strength
return_pairs
observation_count
PerformanceAnalyzer

Measures relative performance.

Example:

performance = PerformanceAnalyzer(
    history_a,
    history_b
)

Provides:

normalized_returns
TechnicalAnalyzer

Provides technical indicators.

Currently supports:

moving_average_data

Includes:

Price history
30-day moving average
90-day moving average
RiskAnalyzer

Provides risk measurements.

Currently supports:

drawdown_data

Used for historical drawdown visualization.

Future API Plans

Future versions may introduce:

FastAPI backend
REST endpoints
Automated market data ingestion API
User portfolio API
Authentication system
Real-time market updates