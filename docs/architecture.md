# QuantStrike Architecture

## Overview

QuantStrike is a quantitative analytics platform for the CS2 skin market. It applies traditional financial analysis techniques to virtual assets by collecting historical price data, calculating market metrics, and visualizing investment-style analytics.

The system is separated into four main layers:


Data Layer
↓
Analytics Engine
↓
Backend Services
↓
Frontend Interface


---

# System Architecture

## 1. Data Layer

Responsible for storing and loading CS2 skin market data.

### Demo Dataset

Location:


data/demo/


Contains:

- Skin metadata
- Historical price data
- Search indexes

The deployed version uses a curated dataset of approximately 9,500 skins to maintain fast loading times while providing broad market coverage.

---

# 2. Data Collection Layer

Location:


backend/collectors/


Responsible for converting raw market data into usable formats.

## CSVCollector

Responsibilities:

- Load historical price files
- Convert raw CSV data into structured objects
- Validate price history

Output:


List[PricePoint]


---

# 3. Analytics Engine

Location:


backend/analytics/


The analytics engine contains quantitative models used throughout QuantStrike.

## Market Metrics

Calculates:

- Current price
- Daily price changes
- Weekly, monthly, and annual returns
- CAGR
- Volatility
- Standard deviation
- Maximum drawdown
- Moving averages
- Sharpe ratio

---

## Performance Analysis

Compares two assets using normalized returns.

Features:

- Relative performance comparison
- Growth comparison
- Historical trend visualization

---

## Technical Analysis

Provides market trend indicators.

Currently implemented:

- 30-day moving average
- 90-day moving average

---

## Risk Analysis

Evaluates downside risk.

Currently implemented:

- Historical drawdown analysis

---

## Correlation Analysis

Measures the relationship between two skins.

Uses:

- Daily percentage returns
- Pearson correlation coefficient

---

# 4. Backend Repository Layer

Location:


backend/repositories/


## SkinRepository

Responsible for:

- Searching skins
- Loading variants
- Retrieving metadata
- Connecting skins with price history

---

# 5. Frontend Layer

Location:


frontend/


Built using Streamlit.

## Pages

### Home

Provides:

- Skin search
- Historical price charts
- Market statistics
- Return metrics
- Risk metrics

---

### Analytics

Provides:

- Two-skin comparison
- Performance comparison charts
- Moving average analysis
- Correlation analysis
- Drawdown analysis

---

# Data Flow

Example user workflow:

1. User searches for a CS2 skin
2. SkinRepository finds matching assets
3. CSVCollector loads historical prices
4. Analytics modules calculate financial metrics
5. Streamlit visualizes the results


User
|
v
Streamlit UI
|
v
SkinRepository
|
v
CSVCollector
|
v
Analytics Engine
|
v
Visualization


---

# Future Architecture Goals

Planned improvements:

- PostgreSQL database integration
- Automated market data ingestion
- REST API backend
- Machine learning price prediction
- Portfolio optimization engine
- QuantStrike Index (QSI)