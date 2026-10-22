# QuantStrike

### Quantitative Market Intelligence for the Counter-Strike Skin Market

![Python](https://img.shields.io/badge/Python-3.11-blue) ![Streamlit](https://img.shields.io/badge/Streamlit-App-red) ![Pandas](https://img.shields.io/badge/Pandas-Analytics-**150458**) ![DuckDB](https://img.shields.io/badge/DuckDB-Query%20Engine-**FFF000**) ![Plotly](https://img.shields.io/badge/Plotly-Interactive%20Charts-**3F4F75**) ![License](https://img.shields.io/badge/License-**MIT**-green)

**QuantStrike** is a quantitative analytics platform built to analyze the Counter-Strike 2 (**CS2**) skin market through the lens of financial markets.

Instead of treating skins as simple cosmetic items, QuantStrike treats them as **market assets** — allowing users to explore historical prices, returns, volatility, risk, drawdowns, correlations, anomalies, and other quantitative signals.

> **Explore the live application:** > [https://quantstrike.streamlit.app](https://quantstrike.streamlit.app)

---

## What is QuantStrike?

The Counter-Strike skin market contains thousands of assets, fluctuating prices, varying levels of liquidity, and substantial historical volatility.

QuantStrike applies concepts commonly used in financial analysis to this market, transforming historical price data into an environment for quantitative research.

The platform combines:

- Historical price analysis
- Return and performance calculations
- Volatility and risk analysis
- Interactive market visualizations
- Asset correlation analysis
- Quantitative performance metrics
- Historical market research
- Statistical anomaly detection
- Market-wide index development
- Watchlists and configurable alerts
- Portfolio tracking
- Research journaling

The goal is simple:

**Turn raw skin price history into meaningful market intelligence.**

---

## Features

### Skin Research

Search the QuantStrike dataset to investigate individual **CS2** assets.

The asset-resolution workflow supports available skin variants and conditions, allowing users to select a human-readable asset and retrieve the corresponding historical observations.

Features include:

- Searchable skin selection
- Normal, StatTrak™ and Souvenir variants where supported
- Wear-condition selection where applicable
- Support for vanilla items without conventional wear conditions
- Exact historical asset identification
- Historical statistics and price exploration

---

### Historical Price Analysis

Explore how individual assets have behaved over time using interactive historical charts.

QuantStrike provides:

- Historical price charts
- Daily price ranges
- Daily low, median, average, high and closing prices
- Historical trading volume
- Multiple historical time ranges
- Exact-date historical observation queries
- Underlying observation inspection
- Historical price distributions
- Price and volume analysis

Users can investigate individual dates and examine the observations underlying the daily statistics.

#### Historical Statistics

Depending on the selected asset and available data, QuantStrike calculates:

- All-time high and low
- Historical median and average
- Price volatility
- Total volume
- Observation count

---

### Historical Data Engine

QuantStrike is built to analyze a large historical dataset without requiring the entire dataset to be loaded into Pandas memory.

The historical data infrastructure uses **Parquet and DuckDB** to support targeted, analytical queries over large volumes of price observations.

Current dataset scale:

- Approximately **22,**495** tracked **CS2** assets**
- Approximately ****105** million historical observations**

The data architecture includes:

- A historical Parquet dataset
- A structured skin metadata index
- Exact historical asset resolution
- Targeted queries for individual assets
- Daily historical aggregation
- Historical statistics computed within DuckDB
- Optional daily historical cache generation

This architecture is designed to make large-scale historical analysis more practical under limited memory constraints.

---

### Quantitative Analytics

QuantStrike goes beyond displaying prices.

The platform implements financial-style metrics to help users evaluate historical asset performance, including:

- Total returns
- Daily returns
- **CAGR**
- Daily volatility
- Standard deviation
- Sharpe ratio
- Maximum drawdown
- Historical highs and lows
- Moving averages
- Return correlation

These metrics allow **CS2** assets to be studied using concepts commonly associated with quantitative finance.

**Note:** Financial metrics describe historical behavior and do not imply that **CS2** skins behave like regulated financial instruments.

---

### Correlation Analysis

Investigate relationships between assets through their historical returns.

QuantStrike supports:

- Pearson return correlation
- Correlation strength classification
- Observation counts
- Return scatter plots
- Multi-asset performance comparison

This makes it possible to investigate whether different skins have historically moved together or independently.

---

### Risk Analysis

Price appreciation is only one part of an asset's behavior.

QuantStrike also examines downside risk and historical variability through:

- Maximum drawdown
- Daily volatility
- Standard deviation
- Sharpe ratio
- Historical return distributions
- Comparative performance analysis

The objective is to provide a more complete picture of an asset's historical behavior rather than relying on price appreciation alone.

---

### Market Data & Anomaly Detection

QuantStrike includes statistical anomaly detection designed to identify unusual historical price observations.

The detection system classifies suspicious observations using historical price behavior and volume-related context.

Current anomaly classifications include:

- `normal`
- `isolated_single_sale_anomaly`
- `isolated_multi_sale_anomaly`
- `structurally_invalid`

Additional capabilities include:

- Detection of isolated price crashes followed by recoveries
- Local price-behavior analysis
- Anomaly markers on historical charts
- Dedicated anomaly tables
- Dataset-wide anomaly diagnostics

**Data integrity principle:** Anomalous observations are flagged rather than silently deleted. This preserves the original historical record and makes suspicious data available for further investigation.

---

### QuantStrike Index (QSI)

The **QuantStrike Index (**QSI**)** is designed to measure broader **CS2** market performance through a single index value.

The initial **QSI** framework uses:

- An equal-weighted methodology
- A base value of **1,**000****
- Individual return caps to limit the influence of extreme observations
- Minimum market-coverage requirements
- Historical daily index observations

The initial methodology includes a minimum 50% market-coverage requirement and a ±50% cap on individual asset returns.

The index is intended to support market-wide analysis rather than limiting research to individual skins.

> **Development status:** Market Intelligence is being redesigned around the expanded historical dataset. The **QSI** framework and Market.**CSGO** integration remain part of the broader market-intelligence roadmap.

---

### Portfolio Management

Track selected **CS2** assets through a dedicated portfolio workflow.

Portfolio management supports:

- Portfolio transaction tracking
- Holdings overview
- Portfolio performance and P&L calculations
- Removal of unwanted holdings
- Confirmation before destructive deletion actions

Deleting a holding removes its associated transaction history; it does not record a sale. This affects the portfolio's transaction-based calculations and P&L.

---

### Watchlist & Alerts

Keep track of assets and manage configured alert rules.

Features include:

- Watchlist management
- Configurable alert rules
- Alert evaluation and history
- Removal of obsolete alert rules
- Confirmation before deleting an alert rule

Deleting an alert rule also removes its associated alert events.

---

### Research Journal

Record and maintain research into individual assets and market behavior.

The Research Journal supports:

- Creating research entries
- Recording hypotheses and research notes
- Associating entries with assets
- Storing supporting evidence
- Editing existing entries
- Deleting entries with confirmation

This provides a place to document observations and hypotheses alongside quantitative analysis.

---

## Architecture

QuantStrike is organized into modular components rather than relying on a single Streamlit script.

The architecture separates data handling, historical queries, quantitative calculations, and frontend visualization.

```text
### Historical Data Sources
    |
    v
Data Processing & Validation
    |
    v
### Historical Parquet Dataset
    |
    +--------------------+
    |                    |
    v                    v
Skin Metadata Index       DuckDB Query Engine
    |                    |
    +---------+----------+
    |
    v
    Historical Data Layer
    |
    v
    Quantitative Analytics
    |
    +---------+----------+
    |                    |
    v                    v
    Risk & Return Analysis   Anomaly Detection
    |                    |
    +---------+----------+
    |
    v
    Streamlit Interface
    |
    v
    Interactive Visualizations
```

The application also includes dedicated services for portfolio management, watchlists, alerts, and research journaling.

### Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core application and analytics |
| Streamlit | Interactive web application |
| Pandas | Data manipulation and analysis |
| DuckDB | Analytical queries over large historical datasets |
| Parquet | Columnar historical data storage |
| Plotly | Interactive charts and visualizations |
| SQLite | Local application feature storage |

---

## Design Principles

QuantStrike follows several principles intended to support reliable quantitative research.

### 1. Preserve Historical Data

Suspicious observations are classified rather than silently removed from the source dataset.

### 2. Query Only What Is Needed

Targeted DuckDB queries and daily aggregation reduce the need to load the full historical dataset into memory.

### 3. Separate Data From Analytics

Historical storage, asset resolution, quantitative calculations, and visualization are handled by separate layers.

### 4. Make Analysis Inspectable

Historical observations, statistics, and anomaly classifications help users investigate how analytical results are derived.

### 5. Treat Results as Historical Evidence

Quantitative metrics describe observed historical behavior. They should not be interpreted as guarantees of future prices or returns.

---

## Running Locally

### Prerequisites

- Python 3.11
- Git
- The required project dependencies
- Access to the historical dataset for historical analytics

### Installation

Clone the repository:

```bash git clone [https://github.com/YOUR_USERNAME/QuantStrike.git](https://github.com/YOUR_USERNAME/QuantStrike.git) cd QuantStrike ```

Create and activate a virtual environment:

```bash python -m venv .venv ```

Windows:

```powershell .venv\Scripts\activate ```

macOS / Linux:

```bash source .venv/bin/activate ```

Install the dependencies:

```bash pip install -r requirements.txt ```

Start the application:

```bash streamlit run app.py ```

Open the local **URL** printed by Streamlit in your terminal.

> **Note:** Replace `YOUR_USERNAME` in the clone **URL** with the actual GitHub username or organization that owns the repository. The historical dataset may not be included in a fresh clone, depending on how the repository distributes its data.

---

## Roadmap

QuantStrike's broader development direction includes:

- Rebuilding Market Intelligence around the expanded historical dataset
- Further developing the QuantStrike Index
- Expanding market-wide and category-level analytics
- Improving historical data quality diagnostics
- Further optimizing large-scale historical queries
- Expanding market-data integrations
- Developing additional quantitative research tools

The roadmap may evolve as the historical data infrastructure and market analytics mature.

---

## Disclaimer

QuantStrike is an independent analytical project focused on the Counter-Strike skin market.

It is not financial advice, an investment service, or a guarantee of future performance. **CS2** skin markets can be volatile, illiquid, and affected by platform policies, trading restrictions, transaction costs, and other factors.

Historical prices and quantitative metrics do not guarantee future outcomes.

QuantStrike is not affiliated with or endorsed by Valve Corporation or the Counter-Strike development team.

---

## License

QuantStrike is released under the **MIT** License. See the [`**LICENSE**`](**LICENSE**) file for details, if included in the repository.

---

**QuantStrike — Bringing quantitative market intelligence to the **CS2** skin market.**