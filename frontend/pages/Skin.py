from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))

from backend.analytics.skin_detail import SkinDetailAnalyzer
from backend.repositories.skin_repository import SkinRepository

from frontend.styles import (
    get_colors,
    load_css,
    render_theme_toggle,
    style_plotly,
)
# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="QuantStrike — Skin Detail",
    page_icon="🛠️",
    layout="wide",
)

load_css()
render_theme_toggle()
# ============================================================
# PATHS
# ============================================================

HISTORICAL_FILE = (
    ROOT
    / "data"
    / "processed"
    / "historical_prices.parquet"
)

INDEX_FILE = (
    ROOT
    / "data"
    / "processed"
    / "skin_metadata.parquet"
)

CACHE_FILE = (
    ROOT
    / "data"
    / "cache"
    / "skin_daily.parquet"
)


# ============================================================
# QUANTSTRIKE UI STYLING
# ============================================================

st.markdown(
    """
    <style>

    /* =====================================================
       GLOBAL
       ===================================================== */

    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1500px;
    }

    /* =====================================================
       SECTION TITLES
       ===================================================== */

    .section-title {
        font-size: 1.05rem;
        font-weight: 700;
        letter-spacing: 0.01em;
        margin-top: 1.8rem;
        margin-bottom: 0.9rem;
    }

    /* =====================================================
       SKIN HEADER
       ===================================================== */

    .research-card {
        padding: 1.45rem 1.55rem;
        border-radius: 16px;

        border: 1px solid rgba(128, 128, 128, 0.18);

        background:
            linear-gradient(
                135deg,
                rgba(128, 128, 128, 0.085),
                rgba(128, 128, 128, 0.035)
            );

        margin-top: 1rem;
        margin-bottom: 1.5rem;

        box-shadow:
            0 8px 30px rgba(0, 0, 0, 0.06);
    }

    .skin-name {
        font-size: 2rem;
        font-weight: 750;
        line-height: 1.15;
        margin-bottom: 0.45rem;
    }

    .skin-meta {
        color: rgba(128, 128, 128, 0.9);
        font-size: 0.92rem;
    }

    /* =====================================================
       STREAMLIT INPUTS
       ===================================================== */

    div[data-baseweb="input"] {
        border-radius: 10px !important;
    }

    div[data-baseweb="select"] > div {
        border-radius: 10px !important;
    }

    div[data-baseweb="input"]:focus-within {
        box-shadow: none !important;
    }

    /* =====================================================
       METRICS
       ===================================================== */

    [data-testid="stMetric"] {
        border:
            1px solid rgba(128, 128, 128, 0.16);

        border-radius:
            14px;

        padding:
            0.95rem 1rem;

        background:
            rgba(128, 128, 128, 0.045);
    }

    [data-testid="stMetricLabel"] {
        font-size: 0.78rem;
    }

    [data-testid="stMetricValue"] {
        font-weight: 700;
    }

    /* =====================================================
       TABLES
       ===================================================== */

    [data-testid="stDataFrame"] {
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid rgba(128, 128, 128, 0.15);
    }

    /* =====================================================
       EXPANDERS
       ===================================================== */

    [data-testid="stExpander"] {
        border:
            1px solid rgba(128, 128, 128, 0.16);

        border-radius:
            12px;

        overflow:
            hidden;
    }

    /* =====================================================
       RADIO BUTTONS
       ===================================================== */

    div[role="radiogroup"] {
        gap: 0.35rem;
    }

    /* =====================================================
       BUTTONS
       ===================================================== */

    button {
        border-radius: 9px !important;
    }

    /* =====================================================
       DIVIDERS
       ===================================================== */

    hr {
        border-color:
            rgba(128, 128, 128, 0.15);
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# DISPLAY HELPERS
# ============================================================

def clean_dataframe_for_display(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Prepare backend data for user-facing tables.

    Internal identifiers such as skin_id are removed.
    Underscores in column names are replaced with spaces.
    """
    if df.empty:
        return df

    display_df = df.copy()

    # Never expose internal identifiers.
    internal_columns = {
        "skin_id",
    }

    display_df = display_df.drop(
        columns=[
            column
            for column in display_df.columns
            if str(column).lower() in internal_columns
        ],
        errors="ignore",
    )

    # Make column names readable.
    display_df.columns = [
        str(column)
        .replace("_", " ")
        .strip()
        .title()
        for column in display_df.columns
    ]

    return display_df


def format_timestamp_column(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Convert timestamp columns into readable datetimes
    without changing the original backend dataframe.
    """
    if df.empty:
        return df

    result = df.copy()

    if "timestamp" in result.columns:
        result["timestamp"] = pd.to_datetime(
            result["timestamp"],
            errors="coerce",
        )

    return result


# ============================================================
# LOAD METADATA
# ============================================================

@st.cache_data
def load_index():
    if not INDEX_FILE.exists():
        return pd.DataFrame()

    return pd.read_parquet(INDEX_FILE)


index = load_index()


# ============================================================
# LOAD REPOSITORY
# ============================================================

@st.cache_resource
def load_repository():
    return SkinRepository(
        metadata_file=str(INDEX_FILE)
    )


repo = load_repository()


# ============================================================
# LOAD ANALYZER
# ============================================================

@st.cache_resource
def load_analyzer():
    return SkinDetailAnalyzer(
        historical_file=HISTORICAL_FILE,
        cache_file=CACHE_FILE,
    )


try:
    analyzer = load_analyzer()

except FileNotFoundError as exc:
    st.error(str(exc))
    st.stop()


# ============================================================
# SKIN SELECTOR
# ============================================================

st.markdown(
    '<div class="section-title">Asset Research</div>',
    unsafe_allow_html=True,
)

query = st.text_input(
    "Search for a skin's name",
    placeholder="e.g. Butterfly Knife | Lore",
    key="skin_detail_search",
)

skin = None
selected_skin = None
selected_condition = None


if query:

    options = repo.search_base_skins(query)

    if not options:

        st.warning(
            "No skins found. Try a different search."
        )

    else:

        selected_skin = st.selectbox(
            "Select skin",
            options,
            format_func=lambda item: item.name,
            key="skin_detail_base_skin",
        )

        variants = repo.get_variants(
            selected_skin
        )

        # ----------------------------------------------------
        # VARIANT TYPE
        # ----------------------------------------------------

        variant_options = []

        has_normal = any(
            not bool(v.get("stattrak", False))
            and not bool(v.get("souvenir", False))
            for v in variants
        )

        has_stattrak = any(
            bool(v.get("stattrak", False))
            for v in variants
        )

        has_souvenir = any(
            bool(v.get("souvenir", False))
            for v in variants
        )

        if has_normal:
            variant_options.append("Normal")

        if has_stattrak:
            variant_options.append("StatTrak™")

        if has_souvenir:
            variant_options.append("Souvenir")

        if not variant_options:
            st.warning(
                "No variants are available for this skin."
            )
            st.stop()

        selected_variant_type = st.selectbox(
            "Select variant",
            variant_options,
            key="skin_detail_variant",
        )

        # ----------------------------------------------------
        # FILTER VARIANTS
        # ----------------------------------------------------

        if selected_variant_type == "Normal":

            filtered_variants = [
                v
                for v in variants
                if not bool(v.get("stattrak", False))
                and not bool(v.get("souvenir", False))
            ]

        elif selected_variant_type == "StatTrak™":

            filtered_variants = [
                v
                for v in variants
                if bool(v.get("stattrak", False))
            ]

        else:

            filtered_variants = [
                v
                for v in variants
                if bool(v.get("souvenir", False))
            ]

        # ----------------------------------------------------
        # CONDITIONS
        # ----------------------------------------------------

        WEAR_ORDER = [
            "Vanilla",
            "Factory New",
            "Minimal Wear",
            "Field-Tested",
            "Well-Worn",
            "Battle-Scarred",
        ]

        available_conditions = sorted(
            {
                str(v.get("condition"))
                for v in filtered_variants
                if v.get("condition") is not None
            },
            key=lambda value: (
                WEAR_ORDER.index(value)
                if value in WEAR_ORDER
                else len(WEAR_ORDER)
            ),
        )

        if not available_conditions:

            st.warning(
                "No conditions are available for this variant."
            )

            st.stop()

        selected_condition = st.selectbox(
            "Select condition",
            available_conditions,
            key="skin_detail_condition",
        )

        # ----------------------------------------------------
        # RESOLVE EXACT VARIANT
        # ----------------------------------------------------

        selected_variant = next(
            (
                v
                for v in filtered_variants
                if str(v.get("condition"))
                == selected_condition
            ),
            None,
        )

        if selected_variant is not None:

            skin = repo.get_by_id(
                selected_variant["skin_id"]
            )

# ============================================================
# STOP UNTIL A SKIN IS SELECTED
# ============================================================

if skin is None:
    st.stop()


# IMPORTANT:
# skin_id remains internal and is NEVER rendered in the UI.
skin_id = str(skin.id)


# ============================================================
# LOAD HISTORICAL DATA
# ============================================================

with st.spinner(
    "Loading historical market data..."
):

    try:

        history = analyzer.get_history(
            skin_id=skin_id
        )

    except Exception as exc:

        st.error(
            f"Unable to load historical data: {exc}"
        )

        st.stop()


if history.empty:

    st.warning(
        "No historical observations were found for this item."
    )

    st.stop()


# ============================================================
# ANALYTICS
# ============================================================

with st.spinner(
    "Calculating analytics..."
):

    daily = analyzer.get_daily_history(
        skin_id=skin_id
    )

    performance = analyzer.performance(
        daily
    )

    statistics = analyzer.statistics(
        history,
        daily
    )

    anomalies = analyzer.detect_anomalies(
        history
    )


# ============================================================
# PRICE HISTORY
# ============================================================

st.markdown(
    '<div class="section-title">Price History</div>',
    unsafe_allow_html=True,
)

range_choice = st.radio(
    "Range",
    [
        "7D",
        "30D",
        "90D",
        "1Y",
        "ALL",
    ],
    horizontal=True,
    index=4,
    key="skin_detail_range",
)


# ============================================================
# RANGE FILTER
# ============================================================

chart_daily = daily.copy()

if not chart_daily.empty:

    latest_date = chart_daily["date"].max()

    if range_choice == "7D":

        cutoff = (
            latest_date
            - pd.Timedelta(days=7)
        )

    elif range_choice == "30D":

        cutoff = (
            latest_date
            - pd.Timedelta(days=30)
        )

    elif range_choice == "90D":

        cutoff = (
            latest_date
            - pd.Timedelta(days=90)
        )

    elif range_choice == "1Y":

        cutoff = (
            latest_date
            - pd.Timedelta(days=365)
        )

    else:

        cutoff = chart_daily["date"].min()

    chart_daily = chart_daily[
        chart_daily["date"] >= cutoff
    ].copy()


# ============================================================
# MAIN PRICE CHART
# ============================================================

fig = go.Figure()


# ------------------------------------------------------------
# High boundary
# ------------------------------------------------------------

fig.add_trace(
    go.Scatter(
        x=chart_daily["date"],
        y=chart_daily["high"],
        mode="lines",
        line=dict(width=0),
        hoverinfo="skip",
        showlegend=False,
    )
)


# ------------------------------------------------------------
# Low boundary
# ------------------------------------------------------------

fig.add_trace(
    go.Scatter(
        x=chart_daily["date"],
        y=chart_daily["low"],
        mode="lines",
        fill="tonexty",
        line=dict(width=0),
        name="Daily Range",
        hovertemplate=(
            "%{x|%d %b %Y}"
            "<br>Low: $%{y:,.2f}"
            "<extra></extra>"
        ),
    )
)


# ------------------------------------------------------------
# Median
# ------------------------------------------------------------

fig.add_trace(
    go.Scatter(
        x=chart_daily["date"],
        y=chart_daily["median"],
        mode="lines",
        name="Median",
        customdata=chart_daily[
            [
                "low",
                "median",
                "average",
                "high",
                "observations",
                "volume",
            ]
        ],
        hovertemplate=(
            "<b>%{x|%d %b %Y}</b>"
            "<br>Median: $%{y:,.2f}"
            "<br>Low: $%{customdata[0]:,.2f}"
            "<br>Average: $%{customdata[2]:,.2f}"
            "<br>High: $%{customdata[3]:,.2f}"
            "<br>Observations: %{customdata[4]:,}"
            "<br>Volume: %{customdata[5]:,}"
            "<extra></extra>"
        ),
    )
)


# ------------------------------------------------------------
# Daily close
# ------------------------------------------------------------

if "close" in chart_daily.columns:

    fig.add_trace(
        go.Scatter(
            x=chart_daily["date"],
            y=chart_daily["close"],
            mode="markers",
            name="Close",
            marker=dict(
                size=6
            ),
            hovertemplate=(
                "<b>%{x|%d %b %Y}</b>"
                "<br>Close: $%{y:,.2f}"
                "<extra></extra>"
            ),
        )
    )


# ============================================================
# ANOMALY OVERLAY
# ============================================================

if not anomalies.empty:

    anomaly_dates = pd.to_datetime(
        anomalies["timestamp"],
        errors="coerce",
    ).dt.normalize()

    anomaly_points = chart_daily[
        chart_daily["date"].isin(
            anomaly_dates
        )
    ]

    if not anomaly_points.empty:

        fig.add_trace(
            go.Scatter(
                x=anomaly_points["date"],
                y=anomaly_points["median"],
                mode="markers",
                name="Anomaly",
                marker=dict(
                    symbol="diamond",
                    size=9,
                ),
                hovertemplate=(
                    "<b>Anomalous observation</b>"
                    "<br>%{x|%d %b %Y}"
                    "<br>Price: $%{y:,.2f}"
                    "<extra></extra>"
                ),
            )
        )


# ============================================================
# CHART LAYOUT
# ============================================================

fig.update_layout(
    height=520,
    margin=dict(
        l=10,
        r=10,
        t=20,
        b=10,
    ),
    hovermode="x unified",
    xaxis_title=None,
    yaxis_title="Price (USD)",
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="left",
        x=0,
    ),
)


# ============================================================
# CLICKABLE CHART
# ============================================================

chart_event = st.plotly_chart(
    fig,
    use_container_width=True,
    on_select="rerun",
    selection_mode="points",
    key="skin_detail_price_chart",
)


# ============================================================
# DATE EXPLORER
# ============================================================

st.markdown(
    '<div class="section-title">Historical Price Explorer</div>',
    unsafe_allow_html=True,
)


selected_date = None


# ------------------------------------------------------------
# Try to extract clicked date
# ------------------------------------------------------------

try:

    if chart_event and chart_event.selection:

        points = chart_event.selection.get(
            "points",
            []
        )

        if points:

            point = points[0]

            if point.get("x") is not None:

                selected_date = pd.Timestamp(
                    point["x"]
                ).date()

except Exception:

    selected_date = None


# ------------------------------------------------------------
# Fallback date picker
# ------------------------------------------------------------

if selected_date is None:

    default_date = (
        daily["date"]
        .max()
        .date()
    )

    selected_date = st.date_input(
        "Select date",
        value=default_date,
        min_value=(
            daily["date"]
            .min()
            .date()
        ),
        max_value=default_date,
        key="skin_detail_date",
    )


selected_date = pd.Timestamp(
    selected_date
).date()


# ============================================================
# DATE SUMMARY
# ============================================================

try:

    summary = analyzer.get_date_summary(
        date=selected_date,
        skin_id=skin_id,
    )

    observations = analyzer.get_date_observations(
        date=selected_date,
        skin_id=skin_id,
    )

except Exception as exc:

    st.error(
        f"Unable to load date data: {exc}"
    )

    summary = {}
    observations = pd.DataFrame()


if summary:

    date_cols = st.columns(6)

    date_metrics = [
        (
            "Low",
            summary.get("low"),
        ),
        (
            "Median",
            summary.get("median"),
        ),
        (
            "Average",
            summary.get("average"),
        ),
        (
            "High",
            summary.get("high"),
        ),
        (
            "Observations",
            summary.get("observations"),
        ),
        (
            "Volume",
            summary.get("volume"),
        ),
    ]

    for col, (label, value) in zip(
        date_cols,
        date_metrics,
    ):

        with col:

            if value is None or pd.isna(value):

                display_value = "—"

            elif label in {
                "Observations",
                "Volume",
            }:

                display_value = (
                    f"{int(value):,}"
                )

            else:

                display_value = (
                    f"${float(value):,.2f}"
                )

            st.metric(
                label,
                display_value,
            )


# ============================================================
# EXACT OBSERVATIONS
# ============================================================

if not observations.empty:

    st.markdown(
        f"""
        **Exact observations — {
            selected_date.strftime("%d %B %Y")
        }**
        """
    )

    display_observations = (
        observations.copy()
    )

    display_observations = (
        format_timestamp_column(
            display_observations
        )
    )

    if "price" in display_observations.columns:

        display_observations["price"] = (
            display_observations["price"]
            .round(4)
        )

    st.dataframe(
        clean_dataframe_for_display(
            display_observations
        ),
        use_container_width=True,
        hide_index=True,
    )

else:

    st.info(
        "No observations were found for this date."
    )


# ============================================================
# HISTORICAL STATISTICS
# ============================================================

st.markdown(
    '<div class="section-title">Historical Statistics</div>',
    unsafe_allow_html=True,
)


stat_cols = st.columns(6)


ath = statistics.get("ath")
atl = statistics.get("atl")
median_price = statistics.get("median")
average_price = statistics.get("average")
volatility = statistics.get("volatility")
total_volume = statistics.get("total_volume")


stats = [
    (
        "All-Time High",
        (
            f"${float(ath):,.2f}"
            if ath is not None
            else "—"
        ),
    ),
    (
        "All-Time Low",
        (
            f"${float(atl):,.2f}"
            if atl is not None
            else "—"
        ),
    ),
    (
        "Historical Median",
        (
            f"${float(median_price):,.2f}"
            if median_price is not None
            else "—"
        ),
    ),
    (
        "Historical Average",
        (
            f"${float(average_price):,.2f}"
            if average_price is not None
            else "—"
        ),
    ),
    (
        "Volatility",
        (
            f"{float(volatility):.2f}%"
            if volatility is not None
            else "—"
        ),
    ),
    (
        "Total Volume",
        (
            f"{int(total_volume):,}"
            if total_volume is not None
            else "—"
        ),
    ),
]


for col, (label, value) in zip(
    stat_cols,
    stats,
):

    with col:

        st.metric(
            label,
            value,
        )


# ============================================================
# PRICE DISTRIBUTION
# ============================================================

st.markdown(
    '<div class="section-title">Price Distribution</div>',
    unsafe_allow_html=True,
)


distribution_fig = go.Figure()


distribution_fig.add_trace(
    go.Box(
        y=history["price"],
        name=skin.name,
        boxmean=True,
        hovertemplate=(
            "$%{y:,.4f}"
            "<extra></extra>"
        ),
    )
)


distribution_fig.update_layout(
    height=450,
    margin=dict(
        l=10,
        r=10,
        t=20,
        b=10,
    ),
    yaxis_title="Price (USD)",
    showlegend=False,
)


st.plotly_chart(
    distribution_fig,
    use_container_width=True,
)


# ============================================================
# PRICE & VOLUME
# ============================================================

st.markdown(
    '<div class="section-title">Price & Volume</div>',
    unsafe_allow_html=True,
)


price_volume_fig = go.Figure()


price_volume_fig.add_trace(
    go.Scatter(
        x=daily["date"],
        y=daily["median"],
        mode="lines",
        name="Median Price",
        yaxis="y",
        hovertemplate=(
            "%{x|%d %b %Y}"
            "<br>Median: $%{y:,.2f}"
            "<extra></extra>"
        ),
    )
)


price_volume_fig.add_trace(
    go.Bar(
        x=daily["date"],
        y=daily["volume"],
        name="Volume",
        yaxis="y2",
        opacity=0.35,
        hovertemplate=(
            "%{x|%d %b %Y}"
            "<br>Volume: %{y:,}"
            "<extra></extra>"
        ),
    )
)


price_volume_fig.update_layout(
    height=500,
    margin=dict(
        l=10,
        r=10,
        t=20,
        b=10,
    ),
    yaxis=dict(
        title="Price (USD)",
    ),
    yaxis2=dict(
        title="Volume",
        overlaying="y",
        side="right",
    ),
    hovermode="x unified",
)


st.plotly_chart(
    price_volume_fig,
    use_container_width=True,
)


# ============================================================
# HISTORICAL ANOMALIES
# ============================================================

st.markdown(
    '<div class="section-title">Historical Anomalies</div>',
    unsafe_allow_html=True,
)


if anomalies.empty:

    st.success(
        "No statistically unusual observations were detected."
    )

else:

    st.caption(
        f"{len(anomalies):,} anomalous observations detected."
    )

    anomaly_display = (
        anomalies.copy()
    )

    anomaly_display = (
        format_timestamp_column(
            anomaly_display
        )
    )

    st.dataframe(
        clean_dataframe_for_display(
            anomaly_display
        ),
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# COMPLETE RAW HISTORY
# ============================================================

with st.expander(
    "View complete historical observations"
):

    raw_history = history.copy()

    raw_history = (
        format_timestamp_column(
            raw_history
        )
    )

    st.dataframe(
        clean_dataframe_for_display(
            raw_history
        ),
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <div style="
        margin-top: 3rem;
        padding-top: 1rem;
        border-top: 1px solid rgba(128,128,128,0.18);
        color: rgba(128,128,128,0.70);
        font-size: 0.8rem;
    ">
        QuantStrike · Historical market analytics
    </div>
    """,
    unsafe_allow_html=True,
)