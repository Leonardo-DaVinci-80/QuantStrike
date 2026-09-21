import sys
import os
from pathlib import Path

# =========================================================
# PATH
# =========================================================

ROOT = Path(__file__).parent.parent.parent
sys.path.append(str(ROOT))

# =========================================================
# STREAMLIT
# =========================================================

import streamlit as st

st.set_page_config(
    page_title="QuantStrike — Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =========================================================
# UI / THEME
# =========================================================

from styles import (
    load_css,
    render_theme_toggle,
    style_plotly,
)

render_theme_toggle()
load_css()

# =========================================================
# DATA / ANALYTICS
# =========================================================

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from backend.repositories.skin_repository import SkinRepository
from backend.database.historical_store import HistoricalStore

from backend.analytics.correlation import CorrelationAnalyzer
from backend.analytics.performance import PerformanceAnalyzer
from backend.analytics.technical import TechnicalAnalyzer
from backend.analytics.risk import RiskAnalyzer
from backend.analytics.market_metrics import MarketMetrics


# =========================================================
# CONFIG
# =========================================================

st.title("📊 Analytics")

st.caption(
    "Compare 2–6 skins across performance, trends, "
    "correlation, and risk."
)

DEFAULT_METADATA = str(
    ROOT / "data" / "processed" / "skin_metadata.parquet"
)

METADATA_FILE = os.environ.get(
    "QUANTSTRIKE_METADATA_FILE",
    DEFAULT_METADATA,
)

DEFAULT_HISTORICAL = str(
    ROOT / "data" / "processed" / "historical_prices.parquet"
)

HISTORICAL_FILE = os.environ.get(
    "QUANTSTRIKE_HISTORICAL_FILE",
    DEFAULT_HISTORICAL,
)


# =========================================================
# LOAD REPOSITORY
# =========================================================

@st.cache_resource
def load_repository():
    return SkinRepository(
        metadata_file=METADATA_FILE,
    )


@st.cache_resource
def load_historical_store():
    return HistoricalStore(
        historical_file=HISTORICAL_FILE,
    )


repo = load_repository()
historical_store = load_historical_store()


# =========================================================
# CONSTANTS
# =========================================================

WEAR_ORDER = [
    "Vanilla",
    "Factory New",
    "Minimal Wear",
    "Field-Tested",
    "Well-Worn",
    "Battle-Scarred",
]


# =========================================================
# SKIN PICKER
# =========================================================

def skin_picker(label_prefix: str):
    """
    Search for a base skin and then select:
        Base skin → Variant → Condition

    Returns the exact Skin object represented by the selected
    variant, using its unique skin_id.
    """

    query = st.text_input(
        f"Search for {label_prefix}",
        key=f"{label_prefix}_query",
        placeholder="e.g. AK-47 | Redline",
    )

    if not query:
        return None

    options = repo.search_base_skins(
        query,
        limit=50,
    )

    if not options:
        st.warning(
            f"No skins found for {label_prefix}."
        )
        return None

    # -----------------------------------------------------
    # BASE SKIN
    # -----------------------------------------------------

    selected_base = st.selectbox(
        "Select skin",
        options,
        format_func=lambda item: item.name,
        key=f"{label_prefix}_skin",
    )

    # -----------------------------------------------------
    # VARIANTS
    # -----------------------------------------------------

    variants = repo.get_variants(
        selected_base
    )

    if not variants:
        st.warning(
            "No variants were found for this skin."
        )
        return None

    variant_options = []

    has_normal = any(
        not v["stattrak"] and not v["souvenir"]
        for v in variants
    )

    has_stattrak = any(
        v["stattrak"] and not v["souvenir"]
        for v in variants
    )

    has_souvenir = any(
        v["souvenir"]
        for v in variants
    )

    if has_normal:
        variant_options.append("Normal")

    if has_stattrak:
        variant_options.append("StatTrak™")

    if has_souvenir:
        variant_options.append("Souvenir")

    if not variant_options:
        return None

    selected_variant_type = st.selectbox(
        "Select variant",
        variant_options,
        key=f"{label_prefix}_variant",
    )

    # -----------------------------------------------------
    # FILTER VARIANTS
    # -----------------------------------------------------

    if selected_variant_type == "StatTrak™":

        filtered_variants = [
            v
            for v in variants
            if v["stattrak"]
            and not v["souvenir"]
        ]

    elif selected_variant_type == "Souvenir":

        filtered_variants = [
            v
            for v in variants
            if v["souvenir"]
        ]

    else:

        filtered_variants = [
            v
            for v in variants
            if not v["stattrak"]
            and not v["souvenir"]
        ]

    # -----------------------------------------------------
    # CONDITIONS
    # -----------------------------------------------------

    available_conditions = [
        wear
        for wear in WEAR_ORDER
        if any(
            v["condition"] == wear
            for v in filtered_variants
        )
    ]

    # Fallback for unexpected condition values
    if not available_conditions:

        available_conditions = sorted({
            v["condition"]
            for v in filtered_variants
        })

    if not available_conditions:
        st.warning(
            "No conditions available for this variant."
        )
        return None

    condition_key = (
        f"{label_prefix}_condition"
    )

    # Reset condition if it is no longer valid
    if (
        condition_key not in st.session_state
        or st.session_state[condition_key]
        not in available_conditions
    ):
        st.session_state[condition_key] = (
            available_conditions[0]
        )

    selected_condition = st.selectbox(
        "Select condition",
        available_conditions,
        key=condition_key,
    )

    # -----------------------------------------------------
    # FIND EXACT VARIANT
    # -----------------------------------------------------

    selected_variant = next(
        (
            variant
            for variant in filtered_variants
            if variant["condition"]
            == selected_condition
        ),
        None,
    )

    if selected_variant is None:
        st.error(
            "Unable to find the selected skin variant."
        )
        return None

    # -----------------------------------------------------
    # GET EXACT SKIN BY ID
    # -----------------------------------------------------

    selected_exact_skin = repo.get_by_id(
        selected_variant["skin_id"]
    )

    if selected_exact_skin is None:
        st.error(
            "The selected skin could not be loaded."
        )
        return None

    # -----------------------------------------------------
    # DISPLAY HUMAN-READABLE SELECTION
    # -----------------------------------------------------

    st.caption(
        f"Selected: **{selected_exact_skin.name}**"
    )

    return selected_exact_skin


# =========================================================
# SKIN SELECTION
# =========================================================

st.subheader("Select Skins")

st.caption(
    "Choose between 2 and 6 skins. Each selected variant "
    "will be included in the performance, correlation, "
    "and risk analysis below."
)


# ---------------------------------------------------------
# SESSION STATE
# ---------------------------------------------------------

if "comparison_slots" not in st.session_state:
    st.session_state.comparison_slots = 2


# ---------------------------------------------------------
# ADD / REMOVE
# ---------------------------------------------------------

control_col1, control_col2, control_col3 = st.columns(
    [1, 1, 4]
)

with control_col1:

    if st.button(
        "➕ Add Skin",
        disabled=(
            st.session_state.comparison_slots >= 6
        ),
        use_container_width=True,
    ):
        st.session_state.comparison_slots += 1
        st.rerun()


with control_col2:

    if st.button(
        "➖ Remove Skin",
        disabled=(
            st.session_state.comparison_slots <= 2
        ),
        use_container_width=True,
    ):
        st.session_state.comparison_slots -= 1
        st.rerun()


# =========================================================
# CREATE SKIN COLUMNS
# =========================================================

slot_count = st.session_state.comparison_slots

selected_skins = []


for start in range(0, slot_count, 3):

    if start > 0:
        st.markdown("---")

    row_count = min(
        3,
        slot_count - start,
    )

    skin_columns = st.columns(row_count)

    for offset, column in enumerate(skin_columns):

        index = start + offset

        with column:

            st.subheader(
                f"Skin {index + 1}"
            )

            selected = skin_picker(
                f"Skin {index + 1}"
            )

            if selected is not None:
                selected_skins.append(
                    selected
                )


# =========================================================
# VALIDATE SELECTION
# =========================================================

if len(selected_skins) < 2:

    st.info(
        "Select at least two skins to begin the comparison."
    )

    st.stop()


# ---------------------------------------------------------
# CHECK DUPLICATES
# ---------------------------------------------------------

selected_ids = [
    skin.id
    for skin in selected_skins
]

if len(selected_ids) != len(set(selected_ids)):

    st.warning(
        "Two or more selected skins are identical. "
        "Please choose different skins for a meaningful "
        "comparison."
    )

    st.stop()


# =========================================================
# SELECTED SKINS SUMMARY
# =========================================================

st.divider()

st.subheader("Selected Skins")

summary_columns = st.columns(
    len(selected_skins)
)

for column, skin in zip(
    summary_columns,
    selected_skins,
):

    with column:

        st.markdown(
            f"""
            <div class="terminal-label">
                SELECTED SKIN
            </div>

            <div class="terminal-value accent">
                {skin.name}
            </div>
            """,
            unsafe_allow_html=True,
        )


# =========================================================
# LOAD HISTORIES
# =========================================================

histories = {}
metrics = {}


for skin in selected_skins:

    try:

        history = historical_store.load_history(
            skin.id
        )

        if not history:
            st.error(
                f"No historical data available for "
                f"{skin.name}."
            )
            st.stop()

        histories[skin.name] = history

        metrics[skin.name] = MarketMetrics(
            history
        )

    except (
        FileNotFoundError,
        ValueError,
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
        "Sharpe Ratio",
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

        f"{metric.sharpe_ratio:.2f}",
    ]


comparison_df = pd.DataFrame(
    comparison_data
).set_index("Metric")


st.dataframe(
    comparison_df,
    use_container_width=True,
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
    "easier to compare. Extreme historical anomalies are "
    "excluded from the visualization."
)


# ---------------------------------------------------------
# Build normalized performance data
# ---------------------------------------------------------

performance_series = {}

base_skin = selected_skins[0]

for skin in selected_skins[1:]:

    try:

        analyzer = PerformanceAnalyzer(
            histories[base_skin.name],
            histories[skin.name]
        )

        df = analyzer.normalized_returns.copy()

        if df.empty:
            continue

        required_columns = {
            "timestamp",
            "asset_a_normalized",
            "asset_b_normalized"
        }

        if not required_columns.issubset(df.columns):
            continue

        # Base skin
        if base_skin.name not in performance_series:

            base_df = df[
                [
                    "timestamp",
                    "asset_a_normalized"
                ]
            ].copy()

            base_df = base_df.rename(
                columns={
                    "asset_a_normalized":
                        base_skin.name
                }
            )

            performance_series[
                base_skin.name
            ] = base_df

        # Comparison skin
        skin_df = df[
            [
                "timestamp",
                "asset_b_normalized"
            ]
        ].copy()

        skin_df = skin_df.rename(
            columns={
                "asset_b_normalized":
                    skin.name
            }
        )

        performance_series[
            skin.name
        ] = skin_df

    except Exception as e:

        st.warning(
            f"Could not calculate relative performance "
            f"for {skin.name}: {e}"
        )


# ---------------------------------------------------------
# Combine all series
# ---------------------------------------------------------

if len(performance_series) < 2:

    st.warning(
        "Not enough overlapping data to calculate "
        "relative performance."
    )

else:

    performance_df = None

    for name, frame in performance_series.items():

        if performance_df is None:

            performance_df = frame

        else:

            performance_df = pd.merge(
                performance_df,
                frame,
                on="timestamp",
                how="outer"
            )


    # -----------------------------------------------------
    # Clean timestamps
    # -----------------------------------------------------

    performance_df["timestamp"] = pd.to_datetime(
        performance_df["timestamp"],
        errors="coerce"
    )

    performance_df = (
        performance_df
        .dropna(subset=["timestamp"])
        .sort_values("timestamp")
    )


    # -----------------------------------------------------
    # Remove invalid normalized values
    # -----------------------------------------------------

    skin_columns = [
        skin.name
        for skin in selected_skins
        if skin.name in performance_df.columns
    ]

    for column in skin_columns:

        performance_df[column] = pd.to_numeric(
            performance_df[column],
            errors="coerce"
        )

        # Normalized values must be positive.
        performance_df.loc[
            performance_df[column] <= 0,
            column
        ] = None

        # Remove impossible/extreme values.
        #
        # Normalized data starts around 100.
        # Values hundreds/thousands of times larger than
        # the baseline are almost certainly corrupted.
        performance_df.loc[
            performance_df[column] > 10000,
            column
        ] = None


    # -----------------------------------------------------
    # Additional robust outlier protection
    # -----------------------------------------------------

    for column in skin_columns:

        series = performance_df[column].dropna()

        if len(series) < 20:
            continue

        # Use the 99.5th percentile as a second safeguard.
        upper_limit = series.quantile(0.995)

        # Never allow the chart to be destroyed by a tiny
        # number of extreme observations.
        upper_limit = max(
            upper_limit * 3,
            500
        )

        performance_df.loc[
            performance_df[column] > upper_limit,
            column
        ] = None


    # -----------------------------------------------------
    # Remove rows where every skin is missing
    # -----------------------------------------------------

    performance_df = performance_df.dropna(
        subset=skin_columns,
        how="all"
    )


    # -----------------------------------------------------
    # Draw chart
    # -----------------------------------------------------

    if performance_df.empty:

        st.warning(
            "No valid normalized performance data "
            "was available."
        )

    else:

        fig = go.Figure()


        for skin in selected_skins:

            name = skin.name

            if name not in performance_df.columns:
                continue

            series = performance_df[
                ["timestamp", name]
            ].dropna()

            if series.empty:
                continue

            fig.add_trace(
                go.Scatter(
                    x=series["timestamp"],
                    y=series[name],
                    mode="lines",
                    name=name,
                    connectgaps=False,
                    line=dict(
                        width=2
                    )
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
                t=50,
                b=20
            ),

            legend=dict(
                orientation="v"
            )
        )


        # -------------------------------------------------
        # Force sensible Y-axis behaviour
        # -------------------------------------------------

        valid_values = performance_df[
            skin_columns
        ].stack()

        if not valid_values.empty:

            chart_max = valid_values.max()

            # Give the chart some breathing room.
            y_max = chart_max * 1.10

            # Prevent a single remaining anomaly from
            # destroying the visual scale.
            y_max = min(y_max, 10000)

            fig.update_yaxes(
                range=[
                    0,
                    y_max
                ]
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
    key="moving_average_skin",
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
            mode="lines",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=ma_df["timestamp"],
            y=ma_df["MA30"],
            name="30D Moving Average",
            mode="lines",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=ma_df["timestamp"],
            y=ma_df["MA90"],
            name="90D Moving Average",
            mode="lines",
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
            t=55,
            b=20,
        ),
    )

    fig = style_plotly(fig)

    st.plotly_chart(
        fig,
        use_container_width=True,
        key="moving_average_chart",
    )


# =========================================================
# CORRELATION ANALYSIS
# =========================================================

st.divider()

st.subheader("Correlation Analysis")

st.caption(
    "Pearson correlation measures how closely the skins' "
    "daily returns move together. +1 indicates strong "
    "positive co-movement, 0 indicates little linear "
    "relationship, and -1 indicates strong negative "
    "co-movement."
)

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

    # -----------------------------------------------------
    # Clean timestamps
    # -----------------------------------------------------

    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        errors="coerce"
    )

    df["price"] = pd.to_numeric(
        df["price"],
        errors="coerce"
    )

    # Remove invalid observations
    df = df.dropna(
        subset=["timestamp", "price"]
    )

    if df.empty:
        continue

    # -----------------------------------------------------
    # Handle duplicate timestamps
    # -----------------------------------------------------
    #
    # Some skin histories contain multiple observations
    # for the same timestamp. Keep the latest observation.
    #
    # This prevents Pandas from encountering duplicate index
    # labels when the individual return series are combined.
    # -----------------------------------------------------

    df = (
        df.sort_values("timestamp")
        .drop_duplicates(
            subset="timestamp",
            keep="last"
        )
    )

    # -----------------------------------------------------
    # Create return series
    # -----------------------------------------------------

    df = df.set_index("timestamp")

    returns = (
        df["price"]
        .pct_change()
        .replace(
            [float("inf"), float("-inf")],
            pd.NA
        )
    )

    # Make absolutely certain the index is unique
    returns = returns[
        ~returns.index.duplicated(
            keep="last"
        )
    ]

    returns.name = skin.name

    return_series[skin.name] = returns

# ---------------------------------------------------------
# Combine all skins
# ---------------------------------------------------------

if len(return_series) < 2:

    st.warning(
        "Not enough valid return data to calculate "
        "correlation."
    )

    returns_df = pd.DataFrame()

else:

    returns_df = pd.concat(
        return_series.values(),
        axis=1,
        join="outer"
    )

    returns_df.columns = list(
        return_series.keys()
    )

    returns_df = returns_df.dropna(
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
        use_container_width=True,
    )

# ---------------------------------------------------------
# PAIRWISE SCATTER / DENSITY
# ---------------------------------------------------------

st.subheader("Return Correlation Scatter Plot")

st.caption(
    "Compare the daily returns of any two skins. "
    "Transparent points reveal observation density, while "
    "density contours highlight the overall shape of the "
    "relationship."
)


scatter_col1, scatter_col2 = st.columns(2)


with scatter_col1:

    scatter_skin_a = st.selectbox(
        "First skin",
        ma_skin_names,
        key="correlation_skin_a",
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
        key="correlation_skin_b",
    )


if scatter_skin_a == scatter_skin_b:

    st.warning(
        "Select two different skins for the "
        "correlation scatter plot."
    )

else:

    try:

        correlation_analyzer = CorrelationAnalyzer(
            histories[scatter_skin_a],
            histories[scatter_skin_b],
        )

        correlation_value = (
            correlation_analyzer.correlation
        )

        observation_count = (
            correlation_analyzer.observation_count
        )

        # -------------------------------------------------
        # CORRELATION SUMMARY
        # -------------------------------------------------

        col1, col2, col3 = st.columns(3)

        with col1:

            st.metric(
                "Pearson Correlation",
                f"{correlation_value:.3f}",
            )

        with col2:

            st.metric(
                "Relationship",
                correlation_analyzer.correlation_strength,
            )

        with col3:

            st.metric(
                "Observations",
                f"{observation_count:,}",
            )

        st.caption(
            "Pearson r is the primary measure of relationship "
            "strength. With large samples, very small "
            "correlations can produce statistically significant "
            "p-values, so practical effect size should be "
            "considered alongside sample size."
        )

        returns_df_scatter = (
            correlation_analyzer.return_pairs
            .copy()
        )

        if returns_df_scatter.empty:

            st.warning(
                "Not enough overlapping return data "
                "to generate the correlation plot."
            )

        else:

            # -------------------------------------------------
            # CLEAN RETURN DATA
            # -------------------------------------------------

            returns_df_scatter["return_a"] = pd.to_numeric(
                returns_df_scatter["return_a"],
                errors="coerce",
            )

            returns_df_scatter["return_b"] = pd.to_numeric(
                returns_df_scatter["return_b"],
                errors="coerce",
            )

            returns_df_scatter = (
                returns_df_scatter
                .replace(
                    [float("inf"), float("-inf")],
                    pd.NA,
                )
                .dropna(
                    subset=[
                        "return_a",
                        "return_b",
                    ]
                )
            )

            if returns_df_scatter.empty:

                st.warning(
                    "No valid return observations remain "
                    "after cleaning."
                )

            else:

                # -------------------------------------------------
                # VISUALIZATION MODE
                # -------------------------------------------------

                visualization_mode = st.radio(
                    "Visualization",
                    [
                        "Density + Scatter",
                        "Density Only",
                        "Scatter Only",
                    ],
                    horizontal=True,
                    key="correlation_visualization_mode",
                )

                # -------------------------------------------------
                # CONVERT TO PERCENTAGE RETURNS
                # -------------------------------------------------

                plot_df = returns_df_scatter.copy()

                plot_df["return_a_pct"] = (
                    plot_df["return_a"] * 100
                )

                plot_df["return_b_pct"] = (
                    plot_df["return_b"] * 100
                )

                # -------------------------------------------------
                # LIMIT VISUAL RANGE FOR DENSITY
                # -------------------------------------------------
                #
                # Extreme returns can stretch the chart dramatically.
                # We keep all observations for the correlation calculation,
                # but use robust percentile limits for visualization only.
                #

                if len(plot_df) >= 50:

                    x_low, x_high = plot_df["return_a_pct"].quantile(
                        [0.005, 0.995]
                    )

                    y_low, y_high = plot_df["return_b_pct"].quantile(
                        [0.005, 0.995]
                    )

                else:

                    x_low, x_high = (
                        plot_df["return_a_pct"].min(),
                        plot_df["return_a_pct"].max(),
                    )

                    y_low, y_high = (
                        plot_df["return_b_pct"].min(),
                        plot_df["return_b_pct"].max(),
                    )

                # -------------------------------------------------
                # BUILD FIGURE
                # -------------------------------------------------

                fig = go.Figure()

                # -------------------------------------------------
                # DENSITY CONTOURS
                # -------------------------------------------------

                if visualization_mode in [
                    "Density + Scatter",
                    "Density Only",
                ]:

                    fig.add_trace(
                        go.Histogram2dContour(
                            x=plot_df["return_a_pct"],
                            y=plot_df["return_b_pct"],

                            colorscale="Blues",

                            contours=dict(
                                coloring="fill",
                                showlabels=False,
                            ),

                            ncontours=12,

                            opacity=0.65,

                            showscale=False,

                            hovertemplate=(
                                f"{scatter_skin_a}: "
                                "%{x:.2f}%<br>"
                                f"{scatter_skin_b}: "
                                "%{y:.2f}%<br>"
                                "Density: %{z}"
                                "<extra></extra>"
                            ),
                        )
                    )

                # -------------------------------------------------
                # TRANSPARENT RAW POINTS
                # -------------------------------------------------

                if visualization_mode in [
                    "Density + Scatter",
                    "Scatter Only",
                ]:

                    fig.add_trace(
                        go.Scattergl(
                            x=plot_df["return_a_pct"],
                            y=plot_df["return_b_pct"],

                            mode="markers",

                            name="Daily Returns",

                            marker=dict(
                                size=4,
                                opacity=0.10,
                            ),

                            hovertemplate=(
                                f"{scatter_skin_a}: "
                                "%{x:.2f}%<br>"
                                f"{scatter_skin_b}: "
                                "%{y:.2f}%"
                                "<extra></extra>"
                            ),
                        )
                    )

                # -------------------------------------------------
                # ZERO REFERENCE LINES
                # -------------------------------------------------

                fig.add_hline(
                    y=0,
                    line_dash="dash",
                    opacity=0.35,
                )

                fig.add_vline(
                    x=0,
                    line_dash="dash",
                    opacity=0.35,
                )

                # -------------------------------------------------
                # TREND LINE
                # -------------------------------------------------

                if (
                    visualization_mode
                    in [
                        "Density + Scatter",
                        "Scatter Only",
                    ]
                    and len(plot_df) >= 2
                ):

                    x = plot_df["return_a_pct"]
                    y = plot_df["return_b_pct"]

                    slope, intercept = (
                        __import__("numpy").polyfit(
                            x,
                            y,
                            1,
                        )
                    )

                    x_min = x.min()
                    x_max = x.max()

                    trend_x = [
                        x_min,
                        x_max,
                    ]

                    trend_y = [
                        slope * x_min + intercept,
                        slope * x_max + intercept,
                    ]

                    fig.add_trace(
                        go.Scatter(
                            x=trend_x,
                            y=trend_y,
                            mode="lines",
                            name="Linear Trend",
                            line=dict(
                                dash="dash",
                                width=2,
                            ),
                            hoverinfo="skip",
                        )
                    )

                # -------------------------------------------------
                # LAYOUT
                # -------------------------------------------------

                fig.update_layout(
                    title=(
                        "Daily Return Relationship"
                        f" — r = {correlation_value:.3f}"
                    ),

                    xaxis_title=(
                        f"{scatter_skin_a} Daily Return (%)"
                    ),

                    yaxis_title=(
                        f"{scatter_skin_b} Daily Return (%)"
                    ),

                    hovermode="closest",

                    margin=dict(
                        l=20,
                        r=20,
                        t=60,
                        b=20,
                    ),

                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="left",
                        x=0,
                    ),
                )

                fig = style_plotly(fig)

                st.plotly_chart(
                    fig,
                    use_container_width=True,
                    key="correlation_chart",
                )
                fig.update_xaxes(
                    range=[
                        x_low,
                        x_high,
                    ]
                )

                fig.update_yaxes(
                    range=[
                        y_low,
                        y_high,
                    ]
                )
                # -------------------------------------------------
                # INTERPRETATION
                # -------------------------------------------------

                st.caption(
                    f"The chart contains "
                    f"{len(plot_df):,} overlapping daily "
                    "return observations. Darker density regions "
                    "represent areas where observations are more "
                    "concentrated. The dashed line shows the "
                    "linear trend corresponding to Pearson "
                    "correlation."
                )

    except ValueError as e:

        st.warning(str(e))

# =========================================================
# DRAWDOWN ANALYSIS
# =========================================================

st.divider()

st.subheader("Drawdown Analysis")

st.caption(
    "Drawdown measures the percentage decline from a "
    "previous peak. More negative values indicate larger "
    "losses from a previous high."
)


selected_dd_skin = st.selectbox(
    "Select skin",
    ma_skin_names,
    key="drawdown_skin",
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
            fill="tozeroy",
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
            t=55,
            b=20,
        ),
    )

    fig = style_plotly(fig)

    st.plotly_chart(
        fig,
        use_container_width=True,
        key="drawdown_chart",
    )


# =========================================================
# RISK VS RETURN
# =========================================================

st.divider()

st.subheader("Risk vs Return")

st.caption(
    "Compare historical return with daily volatility over a period "
    "of your choice."
)

analysis_period = st.radio(
    "Analysis Period",
    options=["7D", "30D", "90D", "6M", "1Y", "2Y", "3Y", "ALL"],
    index=4,
    horizontal=True,
    key="risk_return_period",
)


def get_period_days(period):
    return {
        "7D": 7,
        "30D": 30,
        "90D": 90,
        "6M": 182,
        "1Y": 365,
        "2Y": 730,
        "3Y": 1095,
        "ALL": None,
    }[period]


risk_return_data = []


for skin in selected_skins:

    metric = metrics[skin.name]

    history = pd.DataFrame(metric.history)

    if history.empty:
        continue

    history["timestamp"] = pd.to_datetime(
        history["timestamp"],
        errors="coerce",
    )

    history = history.dropna(
        subset=["timestamp", "price"]
    ).sort_values("timestamp")

    if history.empty:
        continue

    # -----------------------------------------------------
    # Select analysis period
    # -----------------------------------------------------

    end_date = history["timestamp"].max()

    period_days = get_period_days(
        analysis_period
    )

    if period_days is None:

        period_history = history.copy()

    else:

        start_date = (
            end_date
            - pd.Timedelta(days=period_days)
        )

        period_history = history[
            history["timestamp"] >= start_date
        ].copy()

    if len(period_history) < 2:
        continue

    # -----------------------------------------------------
    # Return
    # -----------------------------------------------------

    start_price = period_history["price"].iloc[0]
    end_price = period_history["price"].iloc[-1]

    if start_price <= 0:
        continue

    period_return = (
        (end_price / start_price) - 1
    ) * 100

    # -----------------------------------------------------
    # Daily volatility
    # -----------------------------------------------------

    daily_prices = (
        period_history
        .set_index("timestamp")["price"]
        .resample("1D")
        .last()
        .dropna()
    )

    daily_returns = (
        daily_prices
        .pct_change()
        .dropna()
    )

    if len(daily_returns) < 2:
        volatility = 0.0
    else:
        volatility = (
            daily_returns.std()
            * 100
        )

    risk_return_data.append(
        {
            "Skin": skin.name,
            "Return (%)": period_return,
            "Daily Volatility (%)": volatility,
        }
    )


risk_return_df = pd.DataFrame(
    risk_return_data
)


if risk_return_df.empty:

    st.info(
        "Not enough historical data is available "
        "for the selected analysis period."
    )

else:

    fig = px.scatter(
        risk_return_df,
        x="Daily Volatility (%)",
        y="Return (%)",
        text="Skin",
        title=(
            f"Risk vs Return — "
            f"{analysis_period}"
        ),
    )

    fig.update_traces(
        marker=dict(size=14),
        textposition="top center",
    )

    fig.add_hline(
        y=0,
        line_dash="dash",
        opacity=0.5,
    )

    fig.update_layout(
        hovermode="closest",
        margin=dict(
            l=20,
            r=20,
            t=55,
            b=20,
        ),
    )

    fig = style_plotly(fig)

    st.plotly_chart(
        fig,
        use_container_width=True,
        key="risk_return_chart",
    )
# =========================================================
# END
# =========================================================

st.divider()

st.caption(
    "QuantStrike Analytics • Historical Steam market data"
)