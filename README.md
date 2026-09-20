# QuantStrike

### Quantitative Market Intelligence for the Counter-Strike Skin Market

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-App-red)
![Pandas](https://img.shields.io/badge/Pandas-Analytics-150458)
![Plotly](https://img.shields.io/badge/Plotly-Interactive%20Charts-3F4F75)
![License](https://img.shields.io/badge/License-MIT-green)

**QuantStrike** is a quantitative analytics platform built to analyze the Counter-Strike skin market through the lens of financial markets.

Instead of treating skins as simple cosmetic items, QuantStrike treats them as **market assets** — allowing users to explore historical prices, returns, volatility, risk, drawdowns, correlations, and other quantitative signals.

> **Explore the live application:**  
> https://quantstrike.streamlit.app

---

## 📊 What is QuantStrike?

The Counter-Strike skin market contains thousands of assets, constantly changing prices, varying levels of liquidity, and substantial historical volatility.

QuantStrike applies concepts commonly used in financial analysis to this market.

It combines:

- 📈 Historical price analysis
- 💰 Return calculations
- 📉 Volatility & risk analysis
- 📊 Interactive market visualizations
- 🔗 Asset correlation analysis
- 🧮 Quantitative performance metrics
- 🔍 Historical market research
- 🧠 Market-wide analytics

The goal is simple:

**Turn raw skin price history into meaningful market intelligence.**

---

## 🚀 Features

### 🔎 Skin Research

Search through the QuantStrike dataset and investigate individual assets.

Each skin can be examined across its available variants and conditions, with historical market data used to build a detailed asset profile.

---

### 📈 Historical Price Analysis

Explore how an individual skin has behaved over time.

QuantStrike provides interactive historical charts with:

- Price history
- Daily price ranges
- Median prices
- Average prices
- Trading volume
- Multiple time ranges
- Historical observations

Users can also inspect individual historical dates and examine the underlying observations behind the daily statistics.

---

### 📊 Quantitative Analytics

QuantStrike goes beyond displaying prices.

The platform calculates financial-style metrics including:

- Total returns
- Daily returns
- Volatility
- Standard deviation
- Sharpe ratio
- Maximum drawdown
- CAGR
- Historical highs and lows
- Rolling averages

These metrics allow CS2 assets to be studied using concepts normally associated with quantitative finance.

---

### 🔗 Correlation Analysis

Compare the behaviour of different skins through historical returns.

QuantStrike can analyze relationships between assets using:

- Pearson return correlation
- Correlation strength
- Observation counts
- Return scatter plots

This makes it possible to investigate whether different skins have historically moved together or independently.

---

### 📉 Risk Analysis

Price appreciation is only one part of an asset's behaviour.

QuantStrike also examines downside and risk characteristics through:

- Maximum drawdown
- Daily volatility
- Standard deviation
- Sharpe ratio
- Historical return distributions

The objective is to provide a more complete picture of an asset's historical behaviour.

---

### 🧪 Market Data & Anomaly Detection

QuantStrike includes data-cleaning and anomaly-detection systems designed to identify unusual historical observations.

The analytics pipeline can inspect:

- Extreme price movements
- Statistical outliers
- Unusual returns
- Historical anomalies
- Data coverage
- Rejected observations

This helps prevent corrupted or extreme observations from distorting quantitative analysis.

---

## 🏦 QuantStrike Index

QuantStrike is also being developed into a broader market intelligence platform.

The **QuantStrike Index (QSI)** is designed to provide a single measure of overall CS2 market performance.

The index uses an equal-weighted methodology with:

- A base value of **1,000**
- Individual return caps to reduce the influence of extreme observations
- Market coverage requirements
- Historical daily observations

This provides a way to study the broader CS2 market rather than individual assets in isolation.

---

## 🧮 Built Like a Quantitative Research Platform

QuantStrike is designed around a modular architecture rather than a single Streamlit script.

The project separates:

```text
Data Collection
       ↓
Data Cleaning
       ↓
Historical Dataset
       ↓
Repository Layer
       ↓
Analytics Engine
       ↓
Streamlit Interface
