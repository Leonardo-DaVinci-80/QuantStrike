import sys
from pathlib import Path
from styles import load_css, render_theme_toggle

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
render_theme_toggle()
load_css()



# =========================================================
# CONFIG
# =========================================================

st.set_page_config(
    page_title="QuantStrike — Analytics",
    layout="wide"
)

st.title("📊 Analytics")

st.caption(
    "Compare 2–6 skins across performance, trends, correlation, and risk."
)

DEFAULT_INDEX = str(
    ROOT / "data" / "raw" / "name_conversion_table.csv"
)

DEFAULT_ITEMS = str(
    ROOT / "data" / "raw" / "items"
)


# =========================================================
# LOAD REPOSITORY
# =========================================================

@st.cache_resource
def load_repository():
    return SkinRepository(
        index_file=DEFAULT_INDEX,
        items_directory=DEFAULT_ITEMS
    )


repo = load_repository()


# =========================================================
# SKIN PICKER
# =========================================================

def skin_picker(label_prefix: str):
    query = st.text_input(
        f"Search for {label_prefix}",
        key=f"{label_prefix}_query"
    )

    if not query:
        return None

    options = repo.search_base_skins(query)

    if not options:
        st.warning(
            f"No skins found for {label_prefix}."
        )
        return None

    selected_skin = st.selectbox(
        "Select skin",
        options,
        key=f"{label_prefix}_skin"
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
        "Select variant",
        variant_options,
        key=f"{label_prefix}_variant"
    )

    conditions = []

    for variant in variants:

        if selected_variant == "StatTrak™":
            selected = variant["stattrak"]

        elif selected_variant == "Souvenir":
            selected = variant["souvenir"]

        else:
            selected = (
                not variant["stattrak"]
                and not variant["souvenir"]
            )

        if selected:
            conditions.append(
                variant["condition"]
            )

    wear_order = [
        "Vanilla",
        "Factory New",
        "Minimal Wear",
        "Field-Tested",
        "Well-Worn",
        "Battle-Scarred"
    ]

    wear_matches = [
        wear
        for wear in wear_order
        if wear in set(conditions)
    ]

    conditions = (
        wear_matches
        if wear_matches
        else sorted(set(conditions))
    )

    if not conditions:

        st.warning(
            "No conditions available for this variant."
        )

        return None

    selected_condition = st.selectbox(
        "Select condition",
        conditions,
        key=f"{label_prefix}_condition"
    )

    prefix = ""

    if selected_variant == "StatTrak™":
        prefix = "StatTrak™ "

    elif selected_variant == "Souvenir":
        prefix = "Souvenir "

    if selected_condition == "Vanilla":
        final_name = f"{prefix}{selected_skin}"

    else:
        final_name = (
            f"{prefix}{selected_skin} "
            f"({selected_condition})"
        )

    try:
        return repo.find(final_name)

    except ValueError as e:

        st.error(str(e))

        return None


# =========================================================
# SKIN SELECTION
# =========================================================

st.subheader("Select Skins")

st.caption(
    "Choose between 2 and 6 skins. Each selected skin will be "
    "included in the performance, correlation, and risk analysis below."
)


# Start with two slots
if "comparison_slots" not in st.session_state:
    st.session_state.comparison_slots = 2


# Add / remove controls
control_col1, control_col2, control_col3 = st.columns(
    [1, 1, 4]
)

with control_col1:

    if st.button(
        "➕ Add Skin",
        disabled=st.session_state.comparison_slots >= 6
    ):
        st.session_state.comparison_slots += 1
        st.rerun()


with control_col2:

    if st.button(
        "➖ Remove Skin",
        disabled=st.session_state.comparison_slots <= 2
    ):
        st.session_state.comparison_slots -= 1
        st.rerun()


# Create columns
slot_count = st.session_state.comparison_slots

if slot_count <= 3:

    skin_columns = st.columns(slot_count)

else:

    skin_columns = st.columns(3)


selected_skins = []


for i in range(slot_count):

    if i < 3:
        column = skin_columns[i]

    else:
        if i == 3:
            st.markdown("---")
            skin_columns = st.columns(3)

        column = skin_columns[i - 3]

    with column:

        st.subheader(f"Skin {i + 1}")

        selected = skin_picker(
            f"Skin {i + 1}"
        )

        if selected is not None:
            selected_skins.append(selected)


# =========================================================
# VALIDATE SELECTION
# =========================================================

if len(selected_skins) < 2:

    st.info(
        "Select at least two skins to begin the comparison."
    )

    st.stop()


# Check duplicates
selected_names = [
    skin.name
    for skin in selected_skins
]

if len(selected_names) != len(set(selected_names)):

    st.warning(
        "Two or more selected skins are identical. "
        "Please choose different skins for a meaningful comparison."
    )

    st.stop()


# =========================================================
# SUMMARY
# =========================================================

st.divider()

st.success(
    "Comparing: "
    + " • ".join(
        f"**{name}**"
        for name in selected_names
    )
)


# =========================================================
# LOAD HISTORIES
# =========================================================

collector = CSVCollector()

histories = {}
metrics = {}


for skin in selected_skins:

    try:

        history = collector.load_history(
            skin.history_file
        )

        histories[skin.name] = history
        metrics[skin.name] = MarketMetrics(
            history
        )

    except (
        FileNotFoundError,
        ValueError
    ) as e:

        st.error(
            f"Could not load data for "
            f"{skin.name}: {e}"
        )

        st.stop()


# =========================================================
# HELPERS
# =========================================================

def pct(value):
    return f"{value:+.2f}%"


# =========================================================
# PERFORMANCE METRICS
# =========================================================

st.divider()

st.subheader("Performance Metrics")

st.caption(
    "Historical performance and risk statistics calculated "
    "from the available price history."
)


comparison_data = {
    "Metric": [
        "Current Price",
        "Weekly Return",
        "Monthly Return",
        "Annual Return",
        "CAGR",
        "Daily Volatility",
        "Max Drawdown",
        "Standard Deviation",
        "Sharpe Ratio"
    ]
}


for skin in selected_skins:

    name = skin.name
    metric = metrics[name]

    comparison_data[name] = [

        f"${metric.current_price:.2f}",

        pct(metric.weekly_return),

        pct(metric.monthly_return),

        pct(metric.annual_return),

        pct(metric.cagr),

        f"{metric.volatility:.2f}%",

        f"{metric.max_drawdown:.2f}%",

        f"${metric.standard_deviation:.2f}",

        f"{metric.sharpe_ratio:.2f}"
    ]


comparison_df = pd.DataFrame(
    comparison_data
).set_index("Metric")


st.dataframe(
    comparison_df,
    use_container_width=True
)


st.caption(
    "Sharpe Ratio estimates return relative to volatility. "
    "Because CS2 skins do not have a conventional risk-free "
    "benchmark, this should be treated as an approximate "
    "risk-adjusted performance measure."
)


# =========================================================
# RELATIVE PERFORMANCE
# =========================================================

st.divider()

st.subheader("Relative Performance")

st.caption(
    "All selected skins are rebased to 100 at the start of "
    "the overlapping period, making their relative growth "
    "easier to compare."
)


# Use first skin as anchor and progressively merge
performance_frames = []

base_skin = selected_skins[0]

for skin in selected_skins[1:]:

    analyzer = PerformanceAnalyzer(
        histories[base_skin.name],
        histories[skin.name]
    )

    df = analyzer.normalized_returns

    if df.empty:
        continue

    temp = df[
        [
            "timestamp",
            "asset_a_normalized",
            "asset_b_normalized"
        ]
    ].copy()

    temp = temp.rename(
        columns={
            "asset_a_normalized":
                base_skin.name,
            "asset_b_normalized":
                skin.name
        }
    )

    performance_frames.append(temp)


if not performance_frames:

    st.warning(
        "Not enough overlapping data to calculate "
        "relative performance."
    )

else:

    # Build a common comparison frame
    performance_df = None

    for frame in performance_frames:

        if performance_df is None:

            performance_df = frame

        else:

            performance_df = pd.merge(
                performance_df,
                frame[
                    [
                        "timestamp",
                        frame.columns[-1]
                    ]
                ],
                on="timestamp",
                how="outer"
            )

    if performance_df is None or performance_df.empty:

        st.warning(
            "Not enough overlapping data to calculate "
            "relative performance."
        )

    else:

        fig = go.Figure()

        for skin in selected_skins:

            if skin.name in performance_df.columns:

                fig.add_trace(
                    go.Scatter(
                        x=performance_df["timestamp"],
                        y=performance_df[skin.name],
                        mode="lines",
                        name=skin.name
                    )
                )

        fig.update_layout(
            title=(
                "Relative Price Performance "
                "(Starting Value = 100)"
            ),
            xaxis_title="Date",
            yaxis_title="Normalized Value",
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
            use_container_width=True,
            key="performance_chart"
        )


# =========================================================
# MOVING AVERAGE ANALYSIS
# =========================================================

st.divider()

st.subheader("Moving Average Analysis")

st.caption(
    "30D MA shows the shorter-term trend; 90D MA shows "
    "the longer-term trend. Crossovers can indicate changes "
    "in momentum, but are not guaranteed signals."
)


ma_skin_names = [
    skin.name
    for skin in selected_skins
]


selected_ma_skin = st.selectbox(
    "Select skin",
    ma_skin_names,
    key="moving_average_skin"
)


technical = TechnicalAnalyzer(
    histories[selected_ma_skin]
)


ma_df = technical.moving_average_data


if ma_df.empty:

    st.warning(
        "Not enough data to calculate moving averages."
    )

else:

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
            name="30D Moving Average",
            mode="lines"
        )
    )

    fig.add_trace(
        go.Scatter(
            x=ma_df["timestamp"],
            y=ma_df["MA90"],
            name="90D Moving Average",
            mode="lines"
        )
    )

    fig.update_layout(
        title=(
            f"{selected_ma_skin} "
            "Moving Average Trend"
        ),
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
        use_container_width=True,
        key="moving_average_chart"
    )


# =========================================================
# CORRELATION ANALYSIS
# =========================================================

st.divider()

st.subheader("Correlation Analysis")

st.caption(
    "Pearson correlation measures how closely the skins' "
    "daily returns move together. +1 indicates strong positive "
    "co-movement, 0 indicates little linear relationship, "
    "and -1 indicates strong negative co-movement."
)


# ---------------------------------------------------------
# Pairwise correlation matrix
# ---------------------------------------------------------

return_series = {}

for skin in selected_skins:

    history = histories[skin.name]

    df = pd.DataFrame(
        [
            {
                "timestamp": point.timestamp,
                "price": point.price
            }
            for point in history
        ]
    )

    if df.empty:
        continue

    df["timestamp"] = pd.to_datetime(
        df["timestamp"]
    )

    df = (
        df.sort_values("timestamp")
        .set_index("timestamp")
    )

    returns = df["price"].pct_change()

    return_series[skin.name] = returns


returns_df = pd.DataFrame(
    return_series
).dropna(
    how="all"
)


if len(return_series) < 2:

    st.warning(
        "Not enough data to calculate correlation."
    )

else:

    correlation_matrix = returns_df.corr()

    st.dataframe(
        correlation_matrix.round(3),
        use_container_width=True
    )


# ---------------------------------------------------------
# Pairwise scatter plot
# ---------------------------------------------------------

st.subheader("Return Correlation Scatter Plot")

st.caption(
    "Select any two skins to inspect their daily return "
    "relationship in more detail."
)


scatter_col1, scatter_col2 = st.columns(2)


with scatter_col1:

    scatter_skin_a = st.selectbox(
        "First skin",
        ma_skin_names,
        key="correlation_skin_a"
    )


with scatter_col2:

    scatter_skin_b = st.selectbox(
        "Second skin",
        ma_skin_names,
        index=(
            1
            if len(ma_skin_names) > 1
            else 0
        ),
        key="correlation_skin_b"
    )


if scatter_skin_a == scatter_skin_b:

    st.warning(
        "Select two different skins for the correlation scatter plot."
    )

else:

    try:

        correlation_analyzer = CorrelationAnalyzer(
            histories[scatter_skin_a],
            histories[scatter_skin_b]
        )

        correlation_value = (
            correlation_analyzer.correlation
        )

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

        st.caption(
            f"Calculated from "
            f"{correlation_analyzer.observation_count:,} "
            f"overlapping observations."
        )

        returns_df_scatter = (
            correlation_analyzer.return_pairs
        )

        if returns_df_scatter.empty:

            st.warning(
                "Not enough overlapping return data "
                "to generate the correlation plot."
            )

        else:

            fig = px.scatter(
                returns_df_scatter,
                x="return_a",
                y="return_b",
                labels={
                    "return_a":
                        f"{scatter_skin_a} Daily Return",
                    "return_b":
                        f"{scatter_skin_b} Daily Return"
                },
                title="Daily Return Relationship"
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
                key="correlation_chart"
            )

    except ValueError as e:

        st.warning(str(e))


# =========================================================
# DRAWDOWN ANALYSIS
# =========================================================

st.divider()

st.subheader("Drawdown Analysis")

st.caption(
    "Drawdown measures the percentage decline from a previous "
    "peak. More negative values indicate larger losses from "
    "a previous high."
)


selected_dd_skin = st.selectbox(
    "Select skin",
    ma_skin_names,
    key="drawdown_skin"
)


risk = RiskAnalyzer(
    histories[selected_dd_skin]
)


drawdown_df = risk.drawdown_data


if drawdown_df.empty:

    st.warning(
        "Not enough data to calculate drawdown."
    )

else:

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
        title=(
            f"{selected_dd_skin} "
            "Historical Drawdown"
        ),
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
        use_container_width=True,
        key="drawdown_chart"
    )


# =========================================================
# RISK VS RETURN
# =========================================================

st.divider()

st.subheader("Risk vs Return")

st.caption(
    "Annualized return compared with daily volatility. "
    "Higher returns are generally preferable, while lower "
    "volatility indicates less day-to-day price variation. "
    "Use alongside drawdown and Sharpe Ratio when evaluating "
    "risk-adjusted performance."
)


risk_return_data = []

for skin in selected_skins:

    metric = metrics[skin.name]

    risk_return_data.append(
        {
            "Skin": skin.name,
            "Annual Return (%)":
                metric.annual_return,
            "Daily Volatility (%)":
                metric.volatility
        }
    )


risk_return_df = pd.DataFrame(
    risk_return_data
)


fig = px.scatter(
    risk_return_df,
    x="Daily Volatility (%)",
    y="Annual Return (%)",
    text="Skin",
    title="Risk vs Return Profile"
)


fig.update_traces(
    marker=dict(size=14),
    textposition="top center"
)


fig.add_hline(
    y=0,
    line_dash="dash",
    opacity=0.5
)


fig.update_layout(
    hovermode="closest",
    margin=dict(
        l=20,
        r=20,
        t=40,
        b=20
    )
)


st.plotly_chart(
    fig,
    use_container_width=True,
    key="risk_return_chart"
)