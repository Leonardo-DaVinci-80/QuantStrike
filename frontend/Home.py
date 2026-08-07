import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.append(str(ROOT))

import streamlit as st  # type: ignore
from backend.repositories.skin_repository import SkinRepository
from backend.collectors.csv_collector import CSVCollector
from backend.analytics.market_metrics import MarketMetrics
import random
from datetime import timedelta
import plotly.graph_objects as go
import os

DEFAULT_INDEX = str(ROOT / "data" / "demo" / "item_index.csv")
DEFAULT_ITEMS = str(ROOT / "data" / "demo" / "items")

INDEX_FILE = os.environ.get("QUANTSTRIKE_INDEX_FILE", DEFAULT_INDEX)
ITEMS_DIRECTORY = os.environ.get("QUANTSTRIKE_ITEMS_DIR", DEFAULT_ITEMS)

st.set_page_config(
    page_title="QuantStrike",
    layout="wide"
)

st.title("📈 QuantStrike")
st.caption("CS:GO Market Intelligence Platform")
st.caption(
    "Historical Steam prices before CS2 release. "
    "prices may be inaccurate."
)

@st.cache_resource
def load_repository():
    return SkinRepository(
        index_file=INDEX_FILE,
        items_directory=ITEMS_DIRECTORY
    )

repo = load_repository()
with st.expander("ℹ️ Demo Dataset — Available Skins"):
    st.write(
        f"This deployed version uses a curated subset of the full dataset "
        f"({len(repo.index):,} items) to keep load times fast. "
        f"The dataset includes popular weapons, knives, and collectibles. "
        f"Examples:"
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

    available = [
        skin
        for skin in featured_skins
        if any(skin in name for name in repo.index["name"])
    ]

    st.write(", ".join(available))
    
PLACEHOLDER_SKINS = [
    "Redline",
    "Aquamarine Revenge",
    "Printstream",
    "Vulcan",
    "Asiimov",
    "Fire Serpent",
    "Doppler",
    "Fade",
    "Hyper Beast",
    "Neo-Noir",
]

if "search_placeholder" not in st.session_state:
    st.session_state.search_placeholder = random.choice(PLACEHOLDER_SKINS)

query = st.text_input(
    "Search for a skin's name",
    placeholder=st.session_state.search_placeholder
)

skin = None

if query:
    options = repo.search_base_skins(query)
    if not options:
        st.warning("No skins found.")
    else:
        selected_skin = st.selectbox("Select skin", options)
        variants = repo.get_variants(selected_skin)

        # -----------------------------
        # Select skin type
        # -----------------------------
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
            variant_options
        )

        # -----------------------------
        # Select condition
        # -----------------------------
        conditions = []
        for variant in variants:
            is_selected_variant = False
            if selected_variant == "StatTrak™":
                is_selected_variant = variant["stattrak"]
            elif selected_variant == "Souvenir":
                is_selected_variant = variant["souvenir"]
            elif selected_variant == "Normal":
                is_selected_variant = (
                    not variant["stattrak"]
                    and not variant["souvenir"]
                )
            if is_selected_variant:
                conditions.append(variant["condition"])

        WEAR_ORDER = [
            "Vanilla",
            "Factory New",
            "Minimal Wear",
            "Field-Tested",
            "Well-Worn",
            "Battle-Scarred"
        ]

        conditions = [
            wear
            for wear in WEAR_ORDER
            if wear in set(conditions)
        ]

        selected_condition = st.selectbox(
            "Select condition",
            conditions
        )

        # -----------------------------
        # Build Steam name
        # -----------------------------
        prefix = ""
        if selected_variant == "StatTrak™":
            prefix = "StatTrak™ "
        elif selected_variant == "Souvenir":
            prefix = "Souvenir "

        if selected_condition == "Vanilla":
            final_name = f"{prefix}{selected_skin}"
        else:
            final_name = f"{prefix}{selected_skin} ({selected_condition})"

        st.write("Selected:", final_name)

        try:
            skin = repo.find(final_name)
        except ValueError as e:
            st.error(str(e))
            skin = None

# ============================
# Display analytics
# ============================
if skin:

    st.divider()

    collector = CSVCollector()
    history = collector.load_history(skin.history_file)
    metrics = MarketMetrics(history)

    # ============================
    # Quick Summary
    # ============================

    st.header(skin.name)

    st.caption(
        f"{skin.weapon} | {skin.finish} | "
        f"{skin.condition}"
    )

    summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)

    with summary_col1:
        st.metric(
            "Current Price",
            f"${metrics.current_price:.2f}"
        )

    with summary_col2:
        st.metric(
            "24H Change",
            f"{metrics.daily_change_percent:.2f}%"
        )

    with summary_col3:
        st.metric(
            "1Y Return",
            f"{metrics.annual_return:.2f}%"
        )

    with summary_col4:
        st.metric(
            "CAGR",
            f"{metrics.cagr:.2f}%"
        )


    # ============================
    # Chart + Key Statistics
    # ============================

    st.divider()

    chart_col = st.container()


    with chart_col:

        st.subheader("Historical Price Chart")

        range_choice = st.radio(
            "Range",
            ["1W", "1M", "3M", "1Y", "3Y", "5Y", "All"],
            horizontal=True
        )


        RANGE_DAYS = {
            "1W":7,
            "1M":30,
            "3M":90,
            "1Y":365,
            "3Y":365*3,
            "5Y":365*5,
            "All":None
        }

        days = RANGE_DAYS[range_choice]


        if days:
            cutoff = (
                metrics.history[-1].timestamp
                - timedelta(days=days)
            )

            filtered = [
                p for p in metrics.history
                if p.timestamp >= cutoff
            ]

        else:
            filtered = metrics.history


        fig = go.Figure(
            data=go.Scatter(
                x=[p.timestamp for p in filtered],
                y=[p.price for p in filtered],
                mode="lines"
            )
        )


        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Price ($)",
            margin=dict(
                l=10,
                r=10,
                t=20,
                b=10
            ),
            height=400
        )


        st.plotly_chart(
            fig,
            use_container_width=True
        )

    # ============================
    # Market Statistics
    # ============================

    with st.expander(
        "Market Statistics",
        expanded=True
    ):

        col1,col2,col3,col4 = st.columns(4)

        with col1:
            st.metric(
                "Current Price",
                f"${metrics.current_price:.2f}"
            )

        with col2:
            st.metric(
                "24H Change",
                f"${metrics.daily_change:.2f}"
            )

        with col3:
            st.metric(
                "24H Change %",
                f"{metrics.daily_change_percent:.2f}%"
            )

        with col4:
            st.metric(
                "Std Deviation",
                f"${metrics.standard_deviation:.2f}"
            )


    # ============================
    # Performance
    # ============================

    with st.expander(
        "Performance Metrics",
        expanded=True
    ):

        col1,col2,col3,col4 = st.columns(4)

        with col1:
            st.metric(
                "Weekly Return",
                f"{metrics.weekly_return:.2f}%"
            )

        with col2:
            st.metric(
                "Monthly Return",
                f"{metrics.monthly_return:.2f}%"
            )

        with col3:
            st.metric(
                "1Y Return",
                f"{metrics.annual_return:.2f}%"
            )

        with col4:
            st.metric(
                "CAGR",
                f"{metrics.cagr:.2f}%"
            )


    # ============================
    # Risk
    # ============================

    with st.expander(
        "⚠ Risk Metrics",
        expanded=False
    ):

        col1,col2,col3 = st.columns(3)

        with col1:
            st.metric(
                "Volatility",
                f"{metrics.volatility:.2f}%"
            )

        with col2:
            st.metric(
                "Maximum Drawdown",
                f"{metrics.max_drawdown:.2f}%"
            )

        with col3:
            st.metric(
                "Standard Deviation",
                f"${metrics.standard_deviation:.2f}"
            )


    # ============================
    # Technical Indicators
    # ============================

    with st.expander(
        "Technical Indicators",
        expanded=False
    ):

        col1,col2 = st.columns(2)

        with col1:
            st.metric(
                "30-Day MA",
                f"${metrics.moving_average(30):.2f}"
            )

        with col2:
            st.metric(
                "90-Day MA",
                f"${metrics.moving_average(90):.2f}"
            )