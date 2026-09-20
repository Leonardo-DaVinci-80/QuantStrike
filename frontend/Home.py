import sys
from pathlib import Path
from datetime import timedelta
import os
import random

# ============================================================
# Project path
# ============================================================

ROOT = Path(__file__).parent.parent
sys.path.append(str(ROOT))

# ============================================================
# Imports
# ============================================================

import streamlit as st  # type: ignore
import plotly.graph_objects as go

from styles import load_css, render_theme_toggle, style_plotly
from backend.repositories.skin_repository import SkinRepository
from backend.database.historical_store import HistoricalStore
from backend.analytics.market_metrics import MarketMetrics


# ============================================================
# Streamlit configuration
# ============================================================

st.set_page_config(
    page_title="QuantStrike",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# Theme
# ============================================================

render_theme_toggle()
load_css()


# ============================================================
# Project configuration
# ============================================================

DEFAULT_METADATA = str(
    ROOT
    / "data"
    / "processed"
    / "skin_metadata.parquet"
)

METADATA_FILE = os.environ.get(
    "QUANTSTRIKE_METADATA_FILE",
    DEFAULT_METADATA,
)

DEFAULT_HISTORICAL = str(
    ROOT
    / "data"
    / "processed"
    / "historical_prices.parquet"
)

HISTORICAL_FILE = os.environ.get(
    "QUANTSTRIKE_HISTORICAL_FILE",
    DEFAULT_HISTORICAL,
)


# ============================================================
# Cached data access
# ============================================================

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

# ============================================================
# Page header
# ============================================================

st.title("📈 QuantStrike")

st.caption(
    "Counter-Strike Market Intelligence Platform"
)

st.caption(
    "Historical Steam prices, data cutoff at 4th May 2024. "
    "Prices may be inaccurate."
)


# ============================================================
# Dataset information
# ============================================================

with st.expander("ℹ️ Dataset Information"):

    st.write(
        f"This version uses the full processed metadata dataset "
        f"containing **{len(repo.index):,} indexed items**."
    )

    st.write(
        "The historical price dataset contains price and volume "
        "observations collected from the Steam market dataset."
    )

    featured_skins = [
        "AK-47 | Fire Serpent",
        "AK-47 | Vulcan",
        "AWP | Asiimov",
        "M4A4 | Neo-Noir",
        "M4A1-S | Printstream",
        "Karambit | Doppler",
        "Butterfly Knife | Fade",
        "M9 Bayonet | Lore",
    ]

    available = []

    for skin_name in featured_skins:

        if (
            repo.index["name"]
            .astype(str)
            .str.contains(
                skin_name,
                regex=False,
                na=False,
            )
            .any()
        ):
            available.append(skin_name)

    if available:
        st.write(
            "**Example items:** "
            + ", ".join(available)
        )


# ============================================================
# Search placeholders
# ============================================================

PLACEHOLDER_SKINS = [
    "AK-47 | Redline",
    "AK-47 | Fire Serpent",
    "AK-47 | Vulcan",
    "AWP | Asiimov",
    "M4A1-S | Printstream",
    "USP-S | Kill Confirmed",
    "★ Karambit | Doppler",
    "★ Butterfly Knife | Fade",
    "★ M9 Bayonet | Lore",
    "Desert Eagle | Blaze",
    "Sealed Graffiti | Karambit",
    "Clutch Case",
    "10 Year Birthday Sticker Capsule",
]


st.markdown(
    """
    <style>
    @keyframes placeholderFade {
        0% {
            opacity: 0;
        }

        15% {
            opacity: 1;
        }

        85% {
            opacity: 1;
        }

        100% {
            opacity: 0;
        }
    }

    .search-hint {
        font-size: 0.85rem;
        color: rgba(128, 128, 128, 0.8);
        margin-bottom: 0.25rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


if "search_placeholder" not in st.session_state:
    st.session_state.search_placeholder = (
        random.choice(PLACEHOLDER_SKINS)
    )


# ============================================================
# Search
# ============================================================

query = st.text_input(
    "Search for a skin's name",
    placeholder=st.session_state.search_placeholder,
)


skin = None


if query:

    options = repo.search_base_skins(query)

    if not options:

        st.warning(
            "No skins found. Try a different search."
        )

    else:

        # ----------------------------------------------------
        # Select base skin
        # ----------------------------------------------------

        selected_skin = st.selectbox(
            "Select skin",
            options,
            format_func=lambda item: item.name,
        )

        # ----------------------------------------------------
        # Get all variants
        # ----------------------------------------------------

        variants = repo.get_variants(
            selected_skin
        )

        if not variants:

            st.warning(
                "No variants were found for this skin."
            )

        else:

            # ------------------------------------------------
            # Build variant type list
            # ------------------------------------------------

            variant_options = []

            has_normal = any(
                not v["stattrak"]
                and not v["souvenir"]
                for v in variants
            )

            has_stattrak = any(
                v["stattrak"]
                and not v["souvenir"]
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

            # ------------------------------------------------
            # Select variant type
            # ------------------------------------------------

            selected_variant_type = st.selectbox(
                "Select variant",
                variant_options,
            )

            # ------------------------------------------------
            # Filter variants by type
            # ------------------------------------------------

            if selected_variant_type == "StatTrak™":

                filtered_variants = [
                    variant
                    for variant in variants
                    if (
                        variant["stattrak"]
                        and not variant["souvenir"]
                    )
                ]

            elif selected_variant_type == "Souvenir":

                filtered_variants = [
                    variant
                    for variant in variants
                    if variant["souvenir"]
                ]

            else:

                filtered_variants = [
                    variant
                    for variant in variants
                    if (
                        not variant["stattrak"]
                        and not variant["souvenir"]
                    )
                ]

            # ------------------------------------------------
            # Wear order
            # ------------------------------------------------

            WEAR_ORDER = [
                "Vanilla",
                "Factory New",
                "Minimal Wear",
                "Field-Tested",
                "Well-Worn",
                "Battle-Scarred",
            ]

            available_conditions = [
                wear
                for wear in WEAR_ORDER
                if any(
                    variant["condition"] == wear
                    for variant in filtered_variants
                )
            ]

            # Safety fallback for unusual item types.
            if not available_conditions:

                available_conditions = sorted(
                    {
                        variant["condition"]
                        for variant in filtered_variants
                    }
                )

            # ------------------------------------------------
            # Select condition
            # ------------------------------------------------

            condition_key = (
                "condition_"
                + selected_skin.name
                + "_"
                + selected_variant_type
            )

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

            # ------------------------------------------------
            # Find exact selected variant
            # ------------------------------------------------

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

            else:

                # --------------------------------------------
                # Retrieve exact Skin object
                # --------------------------------------------

                skin = repo.get_by_id(
                    selected_variant["skin_id"]
                )

                # --------------------------------------------
                # Display selection
                # --------------------------------------------

                if skin is not None:

                    st.write(
                        f"**Selected:** {skin.name}"
                    )


# ============================================================
# Display analytics
# ============================================================

if skin:

    st.divider()

    # ========================================================
    # Historical data
    # ========================================================

    historical_store = load_historical_store()
    history = historical_store.load_history(
        skin.id
    )

    metrics = MarketMetrics(history)

    # ========================================================
    # Quick Summary
    # ========================================================

    st.header(skin.name)

    st.caption(
        f"{skin.weapon} | {skin.finish} | "
        f"{skin.condition}"
    )

    summary_col1, summary_col2, summary_col3, summary_col4 = (
        st.columns(4)
    )

    with summary_col1:

        st.metric(
            "Current Price",
            f"${metrics.current_price:.2f}",
        )

    with summary_col2:

        st.metric(
            "24H Change",
            f"{metrics.daily_change_percent:.2f}%",
        )

    with summary_col3:

        st.metric(
            "1Y Return",
            f"{metrics.annual_return:.2f}%",
        )

    with summary_col4:

        st.metric(
            "CAGR",
            f"{metrics.cagr:.2f}%",
        )


    # ========================================================
    # Historical Price Chart
    # ========================================================

    st.divider()

    st.subheader(
        "Historical Price Chart"
    )

    range_choice = st.radio(
        "Range",
        [
            "1W",
            "1M",
            "3M",
            "1Y",
            "3Y",
            "5Y",
            "All",
        ],
        horizontal=True,
    )

    RANGE_DAYS = {
        "1W": 7,
        "1M": 30,
        "3M": 90,
        "1Y": 365,
        "3Y": 365 * 3,
        "5Y": 365 * 5,
        "All": None,
    }

    days = RANGE_DAYS[range_choice]

    if days:

        cutoff = (
            metrics.history[-1].timestamp
            - timedelta(days=days)
        )

        filtered = [
            point
            for point in metrics.history
            if point.timestamp >= cutoff
        ]

    else:

        filtered = metrics.history

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=[
                point.timestamp
                for point in filtered
            ],
            y=[
                point.price
                for point in filtered
            ],
            mode="lines",
            name=skin.name,
        )
    )

    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Price ($)",
        height=400,
    )

    fig = style_plotly(fig)

    st.plotly_chart(
        fig,
        use_container_width=True,
    )


    # ========================================================
    # Market Statistics
    # ========================================================

    with st.expander(
        "Market Statistics",
        expanded=True,
    ):

        col1, col2, col3 = st.columns(3)

        with col1:

            st.metric(
                "Current Price",
                f"${metrics.current_price:.2f}",
            )

        with col2:

            st.metric(
                "24H Change",
                f"${metrics.daily_change:.2f}",
            )

        with col3:

            st.metric(
                "24H Change %",
                f"{metrics.daily_change_percent:.2f}%",
            )

        col4, col5, col6 = st.columns(3)

        with col4:

            st.metric(
                "All-Time High",
                f"${metrics.all_time_high:.2f}",
            )

        with col5:

            st.metric(
                "All-Time Low",
                f"${metrics.all_time_low:.2f}",
            )

        with col6:

            st.metric(
                "Standard Deviation",
                f"${metrics.standard_deviation:.2f}",
            )


    # ========================================================
    # Performance
    # ========================================================

    with st.expander(
        "Performance Metrics",
        expanded=True,
    ):

        col1, col2, col3, col4 = st.columns(4)

        with col1:

            st.metric(
                "Weekly Return",
                f"{metrics.weekly_return:.2f}%",
            )

        with col2:

            st.metric(
                "Monthly Return",
                f"{metrics.monthly_return:.2f}%",
            )

        with col3:

            st.metric(
                "1Y Return",
                f"{metrics.annual_return:.2f}%",
            )

        with col4:

            st.metric(
                "CAGR",
                f"{metrics.cagr:.2f}%",
            )


    # ========================================================
    # Risk
    # ========================================================

    with st.expander(
        "⚠ Risk Metrics",
        expanded=False,
    ):

        col1, col2 = st.columns(2)

        with col1:

            st.metric(
                "Volatility",
                f"{metrics.volatility:.2f}%",
            )

        with col2:

            st.metric(
                "Maximum Drawdown",
                f"{metrics.max_drawdown:.2f}%",
            )


    # ========================================================
    # Technical Indicators
    # ========================================================

    with st.expander(
        "Technical Indicators",
        expanded=False,
    ):

        col1, col2 = st.columns(2)

        with col1:

            st.metric(
                "30-Day MA",
                f"${metrics.moving_average(30):.2f}",
            )

        with col2:

            st.metric(
                "90-Day MA",
                f"${metrics.moving_average(90):.2f}",
            )