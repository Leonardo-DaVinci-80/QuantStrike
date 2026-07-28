# QuantStrike

Quantitative analytics platform applying financial modeling — volatility,
returns, risk metrics — to the Counter-Strike skin market. Built on
historical CS:GO-era Steam price data.

> **Note:** The dataset covers historical CS:GO-era Steam Community Market
> prices (pre–CS2 release). Prices reflect that period and may not match
> current market conditions.

## Features (available now)

- Search any skin, including StatTrak™, Souvenir, and vanilla items
- Historical price chart with adjustable range (1W / 1M / 3M / 1Y / All)
- Volume chart alongside price history
- Market statistics: current price, daily change, all-time high/low,
  52-week high/low, average price, standard deviation

## Coming soon

- Weekly / monthly / annual returns, CAGR, moving averages, max drawdown
- Skin-to-skin comparison (return, volatility, correlation, Sharpe ratio)
- Portfolio tracker with ROI and allocation breakdown
- Research reports (e.g. Operation impact on case/knife prices)
- Price prediction models with confidence intervals
- Market-wide dashboard: gainers, losers, heat map
- Portfolio optimization (efficient frontier, min variance, max Sharpe)

See [ROADMAP.md](ROADMAP.md) for the full version-by-version plan.

## Installation

git clone https://github.com/Leonardo-DaVinci-80/QuantStrike.git
cd QuantStrike
python -m venv .venv
.venv\Scripts\activate      # Windows
source .venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
python scripts/download_dataset.py
streamlit run frontend/Home.py