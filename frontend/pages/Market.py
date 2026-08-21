import sys
from pathlib import Path

import streamlit as st
import pandas as pd
import plotly.graph_objects as go


ROOT = Path(__file__).parent.parent.parent
sys.path.append(str(ROOT))

from backend.repositories.skin_repository import SkinRepository
from backend.analytics.market_overview import MarketOverviewAnalyzer


# =========================================================
# CONFIG
# =========================================================

st.set_page_config(
    page_title="QuantStrike — Market",
    layout="wide"
)

INDEX_FILE = str(
    ROOT / "data" / "demo" / "item_index.csv"
)

ITEMS_DIRECTORY = str(
    ROOT / "data" / "demo" / "items"
)


# =========================================================
# LOAD DATA
# =========================================================

@st.cache_resource
def load_repository():

    return SkinRepository(
        index_file=INDEX_FILE,
        items_directory=ITEMS_DIRECTORY
    )


@st.cache_resource
def load_analyzer():

    return MarketOverviewAnalyzer(
        repository=load_repository()
    )


repo = load_repository()
analyzer = load_analyzer()


# =========================================================
# HEADER
# =========================================================

st.title("📊 Market Overview")

st.caption(
    f"CS2 Market Intelligence · "
    f"{len(repo.index):,} tracked assets"
)

st.caption(
    "Historical market data · QSI currently based on "
    "the QuantStrike historical dataset."
)


# =========================================================
# LOAD ANALYTICS
# =========================================================
def format_qsi(value):
    return f"{value:,.2f}"

with st.spinner("Loading market analytics..."):

    qsi = analyzer.calculate_qsi()

    if qsi.empty:
        st.metric("QSI", "—")
        st.info("QSI historical data is unavailable.")
    else:
        latest_qsi = qsi.iloc[-1]

        # Previous valid session
        previous_qsi = qsi.iloc[-2] if len(qsi) > 1 else None

        if previous_qsi is not None and previous_qsi != 0:
            qsi_change = (
                (latest_qsi / previous_qsi) - 1
            ) * 100
        else:
            qsi_change = None

        qsi_col, change_col = st.columns([3, 1])

        with qsi_col:
            st.metric(
                "QSI",
                format_qsi(latest_qsi)
            )

        with change_col:
            if qsi_change is not None:
                st.metric(
                    "24H",
                    f"{qsi_change:+.2f}%"
                )
            else:
                st.metric("24H", "—")

        st.caption(
            "QSI base value: 1,000. "
            "Individual asset returns are capped at ±50%. "
            "Only dates with at least 50% market coverage are included."
        )

    snapshot = analyzer.latest_market_snapshot()

    gainers, losers = analyzer.top_movers(10)

    breadth = analyzer.market_breadth()


# =========================================================
# QUANTSTRIKE INDEX
# =========================================================

st.divider()

st.subheader("QuantStrike Index")

qsi_col, change_col = st.columns([3, 1])

latest_qsi = qsi.iloc[-1]

if len(qsi) >= 2:

    qsi_change = (
        qsi.iloc[-1] / qsi.iloc[-2] - 1
    ) * 100

else:

    qsi_change = 0


with qsi_col:

    st.metric(
        "QSI",
        f"{latest_qsi:,.2f}",
        f"{qsi_change:+.2f}%"
    )


with change_col:

    st.metric(
        "24H",
        f"{qsi_change:+.2f}%"
    )


# =========================================================
# QSI CHART
# =========================================================

fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=qsi.index,
        y=qsi.values,
        mode="lines",
        name="QSI"
    )
)

fig.update_layout(
    title="QuantStrike Index",
    xaxis_title="Date",
    yaxis_title="Index Value",
    hovermode="x unified",
    height=400,
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


st.caption(
    "QSI base value: 1,000. Individual asset returns are "
    "capped at ±50% and dates require at least 50% market coverage."
)


# =========================================================
# MARKET SNAPSHOT
# =========================================================

st.divider()

st.subheader("Market Snapshot")

col1, col2, col3, col4 = st.columns(4)


with col1:

    st.metric(
        "Market Return",
        f"{snapshot['market_return'] * 100:+.2f}%"
    )


with col2:

    st.metric(
        "Advancing",
        f"{snapshot['advancing']:,}"
    )


with col3:

    st.metric(
        "Declining",
        f"{snapshot['declining']:,}"
    )


with col4:

    st.metric(
        "Volatility",
        f"{snapshot['volatility'] * 100:.2f}%"
    )


# =========================================================
# MARKET BREADTH
# =========================================================

st.divider()

st.subheader("Market Breadth")

st.caption(
    "Number of tracked assets advancing, declining, "
    "or unchanged during the latest available session."
)

latest_breadth = (
    breadth
    .dropna(how="all")
    .iloc[-1]
)

col1, col2, col3 = st.columns(3)

with col1:

    st.metric(
        "Advancing",
        f"{int(latest_breadth['advancing']):,}"
    )

with col2:

    st.metric(
        "Declining",
        f"{int(latest_breadth['declining']):,}"
    )

with col3:

    st.metric(
        "Unchanged",
        f"{int(latest_breadth['unchanged']):,}"
    )


# =========================================================
# MARKET INDICES
# =========================================================

st.divider()

st.subheader("Market Indices")

st.caption(
    "Category-level indices will track major segments "
    "of the CS2 market."
)

categories = [
    "Rifles",
    "Pistols",
    "Knives",
    "Gloves",
    "Cases",
    "Stickers",
    "Agents",
    "SMGs",
    "Shotguns",
    "Machine Guns"
]

cols = st.columns(5)

for i, category in enumerate(categories):

    with cols[i % 5]:

        st.metric(
            category,
            "—",
            help=(
                f"The {category} market index will be "
                "connected once category classification "
                "is implemented."
            )
        )


# =========================================================
# TOP GAINERS / LOSERS
# =========================================================

st.divider()

gainers_col, losers_col = st.columns(2)


with gainers_col:

    st.subheader("🚀 Top Gainers")

    display = gainers.reset_index()

    display.columns = [
        "Skin",
        "Price",
        "24H"
    ]

    display["Price"] = display["Price"].map(
        lambda x: f"${x:,.2f}"
    )

    display["24H"] = display["24H"].map(
        lambda x: f"{x * 100:+.2f}%"
    )

    st.dataframe(
        display,
        hide_index=True,
        use_container_width=True
    )


with losers_col:

    st.subheader("📉 Top Losers")

    display = losers.reset_index()

    display.columns = [
        "Skin",
        "Price",
        "24H"
    ]

    display["Price"] = display["Price"].map(
        lambda x: f"${x:,.2f}"
    )

    display["24H"] = display["24H"].map(
        lambda x: f"{x * 100:+.2f}%"
    )

    st.dataframe(
        display,
        hide_index=True,
        use_container_width=True
    )


# =========================================================
# MARKET HEATMAP
# =========================================================

st.divider()

st.subheader("Market Heatmap")

st.caption(
    "Category performance heatmap — classification "
    "and category indices coming next."
)

heatmap_categories = [
    "Rifles",
    "Pistols",
    "Knives",
    "Gloves",
    "Cases",
    "Stickers"
]

heatmap = pd.DataFrame(
    {
        "Category": heatmap_categories,
        "24H Return": [None] * len(heatmap_categories)
    }
)

st.dataframe(
    heatmap,
    hide_index=True,
    use_container_width=True
)


# =========================================================
# UPCOMING MARKET DATA
# =========================================================

st.divider()

st.subheader("Market Data Sources")

st.info(
    "QuantStrike currently uses the historical dataset "
    "for market analytics. Live Market.CSGO pricing and "
    "sales history will be connected in a future update."
)