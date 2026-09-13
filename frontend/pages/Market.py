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
def load_analyzer(cache_version="qsi_v3_clean_1"):
    return MarketOverviewAnalyzer(
        repository=load_repository()
    )

repo = load_repository()
analyzer = load_analyzer("qsi_v4")

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

with st.spinner("Loading market analytics..."):
    qsi = analyzer.calculate_qsi()
    snapshot = analyzer.latest_market_snapshot()
    gainers, losers = analyzer.top_movers(10)
    breadth = analyzer.market_breadth()

# =========================================================
# QUANTSTRIKE INDEX
# =========================================================

st.divider()

st.subheader("QuantStrike Index")

latest_qsi = float(qsi.iloc[-1])

if len(qsi) >= 2:

    previous_qsi = float(qsi.iloc[-2])

    if previous_qsi != 0:
        qsi_change = (
            latest_qsi / previous_qsi - 1
        ) * 100
    else:
        qsi_change = None

else:

    qsi_change = None


qsi_col, change_col = st.columns([3, 1])

with qsi_col:

    st.metric(
        "QSI",
        f"{latest_qsi:,.2f}"
    )

with change_col:

    if qsi_change is not None:

        st.metric(
            "24H",
            f"{qsi_change:+.2f}%"
        )

    else:

        st.metric(
            "24H",
            "—"
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
    "capped at ±50%. Assets contribute only when new price "
    "observations are available."
)

# =========================================================
# MARKET SNAPSHOT
# =========================================================

col1, col2, col3, col4, col5 = st.columns(5)
st.caption(
    "Market statistics are calculated from assets with "
    "actual price observations in the latest available session."
)
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
        "Active Assets",
        f"{snapshot['active_assets']:,}"
    )

with col5:
    st.metric(
        "Coverage",
        f"{snapshot['coverage'] * 100:.2f}%"
    )

# =========================================================
# MARKET BREADTH
# =========================================================

st.divider()
st.subheader("Market Breadth")

st.caption(
    f"Statistics based on {snapshot['active_assets']:,} assets "
    f"with new price observations in the latest available session "
    f"out of {snapshot['tracked_assets']:,} tracked assets."
)

latest_breadth = (
    breadth
    .dropna(how="all")
    .iloc[-1]
)

col1, col2, col3, col4, col5 = st.columns(5)

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
        "Active Assets",
        f"{snapshot['active_assets']:,}"
    )

with col5:

    st.metric(
        "Volatility",
        f"{snapshot['volatility'] * 100:.2f}%"
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

category_indices = analyzer.category_indices()
display_categories = [
    "Rifles",
    "Pistols",
    "SMGs",
    "Heavy Weapons",
    "Knives",
    "Gloves",
    "Cases",
    "Stickers",
    "Capsules",
    "Agents",
    "Graffiti",
    "Patches",
    "Music Kits",
    "Keys",
]

cols = st.columns(5)

for i, category in enumerate(display_categories):

    with cols[i % 5]:

        series = category_indices.get(category)

        if series is None or series.empty:

            st.metric(
                category,
                "—"
            )

        else:

            latest = float(series.iloc[-1])

            if len(series) >= 2:

                previous = float(series.iloc[-2])

                if previous != 0:

                    change = (
                        latest / previous - 1
                    ) * 100

                else:

                    change = None

            else:

                change = None

            st.metric(
                category,
                f"{latest:,.2f}",
                (
                    f"{change:+.2f}%"
                    if change is not None
                    else None
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
        "24H",
        "Category",
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
        use_container_width=True,
    )


with losers_col:

    st.subheader("📉 Top Losers")

    display = losers.reset_index()

    display.columns = [
        "Skin",
        "Price",
        "24H",
        "Category"
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
        use_container_width=True,
    )


# =========================================================
# MARKET HEATMAP
# =========================================================

st.divider()

st.subheader("Market Heatmap")

st.caption(
    "24H performance across major CS2 market categories. "
    "Only assets with new price observations contribute."
)

category_returns = analyzer.category_returns()

heatmap_categories = [
    "Rifles",
    "Pistols",
    "SMGs",
    "Heavy Weapons",
    "Knives",
    "Gloves",
    "Cases",
    "Stickers",
    "Capsules",
    "Agents",
    "Graffiti",
    "Patches",
    "Music Kits",
    "Keys",
]

heatmap_data = []

for category in heatmap_categories:

    value = category_returns.get(category)

    if value is None or pd.isna(value):

        heatmap_data.append(
            {
                "Category": category,
                "24H Return": None,
            }
        )

    else:

        heatmap_data.append(
            {
                "Category": category,
                "24H Return": value * 100,
            }
        )

heatmap = pd.DataFrame(heatmap_data)

heatmap = pd.DataFrame(heatmap_data)

heatmap["Value"] = heatmap["24H Return"]

fig = go.Figure(
    data=go.Heatmap(
        z=[heatmap["Value"].fillna(0).tolist()],
        x=heatmap["Category"],
        y=["24H Return"],
        text=[
            [
                "—"
                if pd.isna(value)
                else f"{value:+.2f}%"
                for value in heatmap["Value"]
            ]
        ],
        texttemplate="%{text}",
        hovertemplate=(
            "<b>%{x}</b><br>"
            "24H Return: %{text}"
            "<extra></extra>"
        ),
        colorbar=dict(
            title="Return"
        ),
        zmid=0,
    )
)

fig.update_layout(
    height=220,
    margin=dict(
        l=20,
        r=20,
        t=20,
        b=20
    ),
)

st.plotly_chart(
    fig,
    use_container_width=True
)
# =========================================================
# MARKET DATA SOURCES
# =========================================================

st.divider()

st.subheader("Market Data Sources")

st.info(
    "QuantStrike currently uses the historical dataset "
    "for market analytics. Live Market.CSGO pricing and "
    "sales history will be connected in a future update."
)

# =========================================================
# V3 DIAGNOSTICS
# =========================================================

st.divider()

st.subheader("🔬 QuantStrike V3 Diagnostics")

outlier_stats = analyzer.outlier_diagnostics()
return_stats = analyzer.return_diagnostics()

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Rejected Outliers",
        f"{outlier_stats['rejected_count']:,}"
    )

with col2:
    st.metric(
        "Negative Outliers",
        f"{outlier_stats['negative_count']:,}"
    )

with col3:
    st.metric(
        "Positive Outliers",
        f"{outlier_stats['positive_count']:,}"
    )

st.write("Return distribution after V3 cleaning:")

st.json(return_stats)

rejected = analyzer.rejected_observations(25)

if rejected.empty:

    st.info(
        "No observations were rejected by the V3 z-score filter."
    )

else:

    st.write("Most extreme rejected observations:")

    display_rejected = rejected.copy()

    display_rejected["return"] = (
        display_rejected["return"] * 100
    ).map(
        lambda x: f"{x:+.2f}%"
    )

    display_rejected["z_score"] = (
        display_rejected["z_score"]
        .map(
            lambda x: f"{x:.2f}"
        )
    )

    st.dataframe(
        display_rejected,
        hide_index=True,
        use_container_width=True,
    )

st.write(
    "Performance:"
)

st.write(
    f"History loading: "
    f"{analyzer._load_time:.2f}s"
    if analyzer._load_time is not None
    else "History loading: loaded from cache"
)

st.write(
    f"Market matrix processing: "
    f"{analyzer._processing_time:.2f}s"
    if analyzer._processing_time is not None
    else "Market matrix processing: loaded from cache"
)