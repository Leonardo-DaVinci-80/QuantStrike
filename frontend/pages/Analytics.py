import sys
import plotly.express as px
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).parent.parent.parent
sys.path.append(str(ROOT))

import streamlit as st  # type: ignore
from backend.repositories.skin_repository import SkinRepository
from backend.analytics.correlation import CorrelationAnalyzer
from backend.analytics.performance import PerformanceAnalyzer
import plotly.graph_objects as go
from backend.analytics.technical import TechnicalAnalyzer
from backend.analytics.risk import RiskAnalyzer


st.set_page_config(page_title="QuantStrike — Analytics", layout="wide")

st.title("📊 Analytics")
st.caption("Compare two skins side by side: return, volatility, correlation, and drawdown.")

INDEX_FILE = str(ROOT / "data" / "demo" / "item_index.csv")
ITEMS_DIRECTORY = str(ROOT / "data" / "demo" / "items")


@st.cache_resource
def load_repository():
    return SkinRepository(
        index_file=INDEX_FILE,
        items_directory=ITEMS_DIRECTORY
    )


repo = load_repository()


def skin_picker(label_prefix: str):
    """Reusable search -> variant -> condition -> skin picker."""
    query = st.text_input(f"Search for {label_prefix}", key=f"{label_prefix}_query")

    if not query:
        return None

    options = repo.search_base_skins(query)
    if not options:
        st.warning("No skins found.")
        return None

    selected_skin = st.selectbox(
        "Select skin", options, key=f"{label_prefix}_skin"
    )
    variants = repo.get_variants(selected_skin)

    variant_options = []
    for variant in variants:
        if variant["stattrak"]:
            name = "StatTrak™"
        elif variant["souvenir"]:
            name = "Souvenir"
        else:
            name = "Normal"
        if name not in variant_options:
            variant_options.append(name)

    selected_variant = st.selectbox(
        "Select variant", variant_options, key=f"{label_prefix}_variant"
    )

    conditions = []
    for variant in variants:
        is_selected_variant = False
        if selected_variant == "StatTrak™":
            is_selected_variant = variant["stattrak"]
        elif selected_variant == "Souvenir":
            is_selected_variant = variant["souvenir"]
        elif selected_variant == "Normal":
            is_selected_variant = (
                not variant["stattrak"] and not variant["souvenir"]
            )
        if is_selected_variant:
            conditions.append(variant["condition"])

    WEAR_ORDER = [
        "Vanilla", "Factory New", "Minimal Wear",
        "Field-Tested", "Well-Worn", "Battle-Scarred"
    ]
    wear_matches = [w for w in WEAR_ORDER if w in set(conditions)]
    conditions = wear_matches if wear_matches else sorted(set(conditions))

    selected_condition = st.selectbox(
        "Select condition", conditions, key=f"{label_prefix}_condition"
    )

    prefix = ""
    if selected_variant == "StatTrak™":
        prefix = "StatTrak™ "
    elif selected_variant == "Souvenir":
        prefix = "Souvenir "

    if selected_condition == "Vanilla":
        final_name = f"{prefix}{selected_skin}"
    else:
        final_name = f"{prefix}{selected_skin} ({selected_condition})"

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

if skin_a and skin_b:
    st.divider()
    st.success(f"Comparing: **{skin_a.name}** vs **{skin_b.name}**")

    from backend.collectors.csv_collector import CSVCollector
    from backend.analytics.market_metrics import MarketMetrics

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
        correlation_analyzer = CorrelationAnalyzer(history_a,history_b)
    except (FileNotFoundError, ValueError) as e:
        st.error(f"Could not load data for {skin_b.name}: {e}")
        st.stop()

    st.divider()

    st.subheader("Performance Metrics")

    comparison_data = {
        "Metric": [
            "Current Price",
            "Weekly Return",
            "Monthly Return",
            "Annual Return",
            "CAGR",
            "Volatility (daily)",
            "Max Drawdown",
            "Standard Deviation",
            "Sharpe Ratio",
        ],
        skin_a.name: [
            f"${metrics_a.current_price:.2f}",
            f"{metrics_a.weekly_return:.2f}%",
            f"{metrics_a.monthly_return:.2f}%",
            f"{metrics_a.annual_return:.2f}%",
            f"{metrics_a.cagr:.2f}%",
            f"{metrics_a.volatility:.2f}%",
            f"{metrics_a.max_drawdown:.2f}%",
            f"${metrics_a.standard_deviation:.2f}",
            f"{metrics_a.sharpe_ratio:.2f}",
        ],
        skin_b.name: [
            f"${metrics_b.current_price:.2f}",
            f"{metrics_b.weekly_return:.2f}%",
            f"{metrics_b.monthly_return:.2f}%",
            f"{metrics_b.annual_return:.2f}%",
            f"{metrics_b.cagr:.2f}%",
            f"{metrics_b.volatility:.2f}%",
            f"{metrics_b.max_drawdown:.2f}%",
            f"${metrics_b.standard_deviation:.2f}",
            f"{metrics_b.sharpe_ratio:.2f}",
        ],
    }

    comparison_df = pd.DataFrame(comparison_data).set_index("Metric")
    st.table(comparison_df)

    st.divider()

    st.subheader("Relative Performance")

    performance = PerformanceAnalyzer(
            history_a,
            history_b
        )

    performance_df = performance.normalized_returns

    fig = go.Figure()

    fig.add_trace(
            go.Scatter(
                x=performance_df["timestamp"],
                y=performance_df["asset_a_normalized"],
                mode="lines",
                name=skin_a.name
            )
        )

    fig.add_trace(
            go.Scatter(
                x=performance_df["timestamp"],
                y=performance_df["asset_b_normalized"],
                mode="lines",
                name=skin_b.name
            )
        )

    fig.update_layout(
            title="Normalized Price Performance (Starting Value = 100)",
            xaxis_title="Date",
            yaxis_title="Growth (%)",
            hovermode="x unified",
            margin=dict(
                l=20,
                r=20,
                t=40,
                b=20
            )
        )

    st.plotly_chart(
            fig,
            use_container_width=True
        )

    st.divider()

    st.subheader("Moving Average Analysis")

    selected_ma_skin = st.radio(
        "Select skin",
        [
            skin_a.name,
            skin_b.name
        ],
        horizontal=True
    )

    if selected_ma_skin == skin_a.name:
        technical = TechnicalAnalyzer(history_a)
    else:
        technical = TechnicalAnalyzer(history_b)


    ma_df = technical.moving_average_data


    fig = go.Figure()


    fig.add_trace(
        go.Scatter(
            x=ma_df["timestamp"],
            y=ma_df["price"],
            name="Price",
            mode="lines"
        )
    )


    fig.add_trace(
        go.Scatter(
            x=ma_df["timestamp"],
            y=ma_df["MA30"],
            name="30 Day MA",
            mode="lines"
        )
    )


    fig.add_trace(
        go.Scatter(
            x=ma_df["timestamp"],
            y=ma_df["MA90"],
            name="90 Day MA",
            mode="lines"
        )
    )


    fig.update_layout(
        title=f"{selected_ma_skin} Moving Average Trend",
        xaxis_title="Date",
        yaxis_title="Price ($)",
        hovermode="x unified",
        margin=dict(
            l=20,
            r=20,
            t=40,
            b=20
        )
    )


    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.divider()

    st.subheader("Correlation Analysis")

    correlation_value = correlation_analyzer.correlation

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Pearson Correlation",
            f"{correlation_value:.3f}"
        )

    with col2:
        st.metric(
            "Relationship",
            correlation_analyzer.correlation_strength
        )

    st.caption(f"Calculated from {correlation_analyzer.observation_count} ""overlapping observations")

    st.subheader("Return Correlation Scatter Plot")

    returns_df = correlation_analyzer.return_pairs

    fig = px.scatter(
        returns_df,
        x="return_a",
        y="return_b",
        labels={
            "return_a": f"{skin_a.name} Daily Return",
            "return_b": f"{skin_b.name} Daily Return",
        },
        title="Daily Return Relationship",
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.divider()

st.subheader("Drawdown Analysis")

if skin_a and skin_b:

    st.divider()

    st.subheader("Drawdown Analysis")

    selected_dd_skin = st.radio(
        "Select skin for drawdown analysis",
        [
            skin_a.name,
            skin_b.name
        ],
        horizontal=True,
        key="drawdown_skin"
    )

    if selected_dd_skin == skin_a.name:
        risk = RiskAnalyzer(history_a)
    else:
        risk = RiskAnalyzer(history_b)

    drawdown_df = risk.drawdown_data

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=drawdown_df["timestamp"],
            y=drawdown_df["drawdown"],
            mode="lines",
            name="Drawdown (%)",
            fill="tozeroy"
        )
    )

    fig.update_layout(
        title=f"{selected_dd_skin} Historical Drawdown",
        xaxis_title="Date",
        yaxis_title="Drawdown (%)",
        hovermode="x unified",
        margin=dict(
            l=20,
            r=20,
            t=40,
            b=20
        )
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


    if selected_dd_skin == skin_a.name:
        risk = RiskAnalyzer(history_a)
    else:
        risk = RiskAnalyzer(history_b)


    drawdown_df = risk.drawdown_data


fig = go.Figure()


fig.add_trace(
    go.Scatter(
        x=drawdown_df["timestamp"],
        y=drawdown_df["drawdown"],
        mode="lines",
        name="Drawdown (%)",
        fill="tozeroy"
    )
)


fig.update_layout(
    title=f"{selected_dd_skin} Historical Drawdown",
    xaxis_title="Date",
    yaxis_title="Drawdown (%)",
    hovermode="x unified",
    margin=dict(
        l=20,
        r=20,
        t=40,
        b=20
    )
)


st.plotly_chart(
    fig,
    use_container_width=True
)