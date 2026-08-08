import sys
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

ROOT = Path(__file__).parent.parent.parent
sys.path.append(str(ROOT))

import streamlit as st  # type: ignore
from backend.repositories.skin_repository import SkinRepository
from backend.analytics.correlation import CorrelationAnalyzer
from backend.analytics.performance import PerformanceAnalyzer
from backend.analytics.technical import TechnicalAnalyzer
from backend.analytics.risk import RiskAnalyzer
from backend.collectors.csv_collector import CSVCollector
from backend.analytics.market_metrics import MarketMetrics

st.set_page_config(page_title="QuantStrike — Analytics", layout="wide")
st.title("📊 Analytics")
st.caption("Compare two skins across performance, trends, correlation, and risk.")

INDEX_FILE = str(ROOT / "data" / "demo" / "item_index.csv")
ITEMS_DIRECTORY = str(ROOT / "data" / "demo" / "items")

@st.cache_resource
def load_repository():
    return SkinRepository(index_file=INDEX_FILE, items_directory=ITEMS_DIRECTORY)

repo = load_repository()

def skin_picker(label_prefix: str):
    query = st.text_input(f"Search for {label_prefix}", key=f"{label_prefix}_query")
    if not query:
        return None

    options = repo.search_base_skins(query)
    if not options:
        st.warning(f"No skins found for {label_prefix}.")
        return None

    selected_skin = st.selectbox("Select skin", options, key=f"{label_prefix}_skin")
    variants = repo.get_variants(selected_skin)

    variant_options = []
    for variant in variants:
        name = "StatTrak™" if variant["stattrak"] else "Souvenir" if variant["souvenir"] else "Normal"
        if name not in variant_options:
            variant_options.append(name)

    selected_variant = st.selectbox("Select variant", variant_options, key=f"{label_prefix}_variant")

    conditions = []
    for variant in variants:
        if selected_variant == "StatTrak™":
            selected = variant["stattrak"]
        elif selected_variant == "Souvenir":
            selected = variant["souvenir"]
        else:
            selected = not variant["stattrak"] and not variant["souvenir"]
        if selected:
            conditions.append(variant["condition"])

    wear_order = ["Vanilla", "Factory New", "Minimal Wear", "Field-Tested", "Well-Worn", "Battle-Scarred"]
    wear_matches = [w for w in wear_order if w in set(conditions)]
    conditions = wear_matches if wear_matches else sorted(set(conditions))

    if not conditions:
        st.warning("No conditions available for this variant.")
        return None

    selected_condition = st.selectbox("Select condition", conditions, key=f"{label_prefix}_condition")

    prefix = "StatTrak™ " if selected_variant == "StatTrak™" else "Souvenir " if selected_variant == "Souvenir" else ""
    final_name = f"{prefix}{selected_skin}" if selected_condition == "Vanilla" else f"{prefix}{selected_skin} ({selected_condition})"

    try:
        return repo.find(final_name)
    except ValueError as e:
        st.error(str(e))
        return None

col1, col2 = st.columns(2)

with col1:
    st.subheader("Skin A")
    skin_a = skin_picker("Skin A")

with col2:
    st.subheader("Skin B")
    skin_b = skin_picker("Skin B")

if not skin_a or not skin_b:
    st.info("Select both Skin A and Skin B to begin the comparison.")
    st.stop()

if skin_a.name == skin_b.name:
    st.warning("Skin A and Skin B are identical. Select two different skins for a meaningful comparison.")
    st.stop()

st.divider()
st.success(f"Comparing: **{skin_a.name}** vs **{skin_b.name}**")

collector = CSVCollector()

try:
    history_a = collector.load_history(skin_a.history_file)
    metrics_a = MarketMetrics(history_a)
except (FileNotFoundError, ValueError) as e:
    st.error(f"Could not load data for {skin_a.name}: {e}")
    st.stop()

try:
    history_b = collector.load_history(skin_b.history_file)
    metrics_b = MarketMetrics(history_b)
    correlation_analyzer = CorrelationAnalyzer(history_a, history_b)
except (FileNotFoundError, ValueError) as e:
    st.error(f"Could not load data for {skin_b.name}: {e}")
    st.stop()

def pct(value):
    return f"{value:+.2f}%"

st.divider()
st.subheader("Performance Metrics")
st.caption("Historical performance and risk statistics calculated from the available price history.")

comparison_data = {
    "Metric": ["Current Price", "Weekly Return", "Monthly Return", "Annual Return", "CAGR", "Daily Volatility", "Max Drawdown", "Standard Deviation", "Sharpe Ratio"],
    skin_a.name: [
        f"${metrics_a.current_price:.2f}", pct(metrics_a.weekly_return), pct(metrics_a.monthly_return),
        pct(metrics_a.annual_return), pct(metrics_a.cagr), f"{metrics_a.volatility:.2f}%",
        f"{metrics_a.max_drawdown:.2f}%", f"${metrics_a.standard_deviation:.2f}", f"{metrics_a.sharpe_ratio:.2f}"
    ],
    skin_b.name: [
        f"${metrics_b.current_price:.2f}", pct(metrics_b.weekly_return), pct(metrics_b.monthly_return),
        pct(metrics_b.annual_return), pct(metrics_b.cagr), f"{metrics_b.volatility:.2f}%",
        f"{metrics_b.max_drawdown:.2f}%", f"${metrics_b.standard_deviation:.2f}", f"{metrics_b.sharpe_ratio:.2f}"
    ],
}

st.table(pd.DataFrame(comparison_data).set_index("Metric"))
st.caption("Sharpe Ratio estimates return relative to volatility. Because CS2 skins do not have a conventional risk-free benchmark, this should be treated as an approximate risk-adjusted performance measure.")

st.divider()
st.subheader("Relative Performance")
st.caption("Both skins are rebased to 100 at the start of the overlapping period, making their relative growth easier to compare.")

performance_df = PerformanceAnalyzer(history_a, history_b).normalized_returns
if performance_df.empty:
    st.warning("Not enough overlapping data to calculate relative performance.")
else:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=performance_df["timestamp"], y=performance_df["asset_a_normalized"], mode="lines", name=skin_a.name))
    fig.add_trace(go.Scatter(x=performance_df["timestamp"], y=performance_df["asset_b_normalized"], mode="lines", name=skin_b.name))
    fig.update_layout(title="Relative Price Performance (Starting Value = 100)", xaxis_title="Date", yaxis_title="Normalized Value", hovermode="x unified", margin=dict(l=20,r=20,t=40,b=20))
    st.plotly_chart(fig, use_container_width=True, key="performance_chart")

st.divider()
st.subheader("Moving Average Analysis")
st.caption("30D MA shows the shorter-term trend; 90D MA shows the longer-term trend. Crossovers can indicate changes in momentum, but are not guaranteed signals.")

selected_ma_skin = st.radio("Select skin", [skin_a.name, skin_b.name], horizontal=True, key="moving_average_skin")
technical = TechnicalAnalyzer(history_a if selected_ma_skin == skin_a.name else history_b)
ma_df = technical.moving_average_data

if ma_df.empty:
    st.warning("Not enough data to calculate moving averages.")
else:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ma_df["timestamp"], y=ma_df["price"], name="Price", mode="lines"))
    fig.add_trace(go.Scatter(x=ma_df["timestamp"], y=ma_df["MA30"], name="30D Moving Average", mode="lines"))
    fig.add_trace(go.Scatter(x=ma_df["timestamp"], y=ma_df["MA90"], name="90D Moving Average", mode="lines"))
    fig.update_layout(title=f"{selected_ma_skin} Moving Average Trend", xaxis_title="Date", yaxis_title="Price ($)", hovermode="x unified", margin=dict(l=20,r=20,t=40,b=20))
    st.plotly_chart(fig, use_container_width=True, key="moving_average_chart")

st.divider()
st.subheader("Correlation Analysis")
st.caption("Pearson correlation measures how closely the skins' daily returns move together. +1 indicates strong positive co-movement, 0 indicates little linear relationship, and -1 indicates strong negative co-movement.")

correlation_value = correlation_analyzer.correlation
col1, col2 = st.columns(2)

with col1:
    st.metric("Pearson Correlation", f"{correlation_value:.3f}")

with col2:
    st.metric("Relationship", correlation_analyzer.correlation_strength)

st.caption(f"Calculated from {correlation_analyzer.observation_count} overlapping observations.")
st.subheader("Return Correlation Scatter Plot")
returns_df = correlation_analyzer.return_pairs

if returns_df.empty:
    st.warning("Not enough overlapping return data to generate the correlation plot.")
else:
    fig = px.scatter(
        returns_df, x="return_a", y="return_b",
        labels={"return_a": f"{skin_a.name} Daily Return", "return_b": f"{skin_b.name} Daily Return"},
        title="Daily Return Relationship"
    )
    st.plotly_chart(fig, use_container_width=True, key="correlation_chart")

st.divider()
st.subheader("Drawdown Analysis")
st.caption("Drawdown measures the percentage decline from a previous peak. More negative values indicate larger losses from a previous high.")

selected_dd_skin = st.radio("Select skin", [skin_a.name, skin_b.name], horizontal=True, key="drawdown_skin")
risk = RiskAnalyzer(history_a if selected_dd_skin == skin_a.name else history_b)
drawdown_df = risk.drawdown_data

if drawdown_df.empty:
    st.warning("Not enough data to calculate drawdown.")
else:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=drawdown_df["timestamp"], y=drawdown_df["drawdown"], mode="lines", name="Drawdown (%)", fill="tozeroy"))
    fig.update_layout(title=f"{selected_dd_skin} Historical Drawdown", xaxis_title="Date", yaxis_title="Drawdown (%)", hovermode="x unified", margin=dict(l=20,r=20,t=40,b=20))
    st.plotly_chart(fig, use_container_width=True, key="drawdown_chart")

st.divider()
st.subheader("Risk vs Return")
st.caption("Annualized return compared with daily volatility. Higher returns are generally preferable, while lower volatility indicates less day-to-day price variation. Use alongside drawdown and Sharpe Ratio when evaluating risk-adjusted performance.")

risk_return_df = pd.DataFrame({
    "Skin": [skin_a.name, skin_b.name],
    "Annual Return (%)": [metrics_a.annual_return, metrics_b.annual_return],
    "Daily Volatility (%)": [metrics_a.volatility, metrics_b.volatility]
})

fig = px.scatter(risk_return_df, x="Daily Volatility (%)", y="Annual Return (%)", text="Skin", title="Risk vs Return Profile")
fig.update_traces(marker=dict(size=14), textposition="top center")
fig.add_hline(y=0, line_dash="dash", opacity=0.5)
fig.update_layout(hovermode="closest", margin=dict(l=20,r=20,t=40,b=20))
st.plotly_chart(fig, use_container_width=True, key="risk_return_chart")