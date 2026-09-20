from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))

from frontend.styles import load_css, render_theme_toggle


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="QuantStrike — Market",
    page_icon="📊",
    layout="wide",
)


# ============================================================
# QUANTSTRIKE THEME
# ============================================================

load_css()
render_theme_toggle()


# ============================================================
# MARKET INTELLIGENCE — TEMPORARY PLACEHOLDER
# ============================================================

st.markdown(
    """
    <div style="
        margin-top: 5rem;
        text-align: center;
    ">
        <div class="terminal-label">
            MARKET INTELLIGENCE
        </div>

        <div
            class="terminal-value"
            style="
                font-size: 2.5rem;
                margin-top: 0.75rem;
            "
        >
            COMING SOON
        </div>

        <div
            style="
                color: var(--qs-text-muted);
                font-family: var(--qs-font-mono);
                margin-top: 1rem;
                font-size: 0.9rem;
            "
        >
            The QuantStrike market engine is currently under development.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# PLANNED MARKET SYSTEMS
# ============================================================

st.markdown(
    """
    <div style="
        max-width: 900px;
        margin: 3rem auto 0 auto;
    ">
        <div class="terminal-label">
            PLANNED SYSTEMS
        </div>

        <div style="
            margin-top: 1rem;
            padding: 1.5rem;
            border: 1px solid var(--qs-border);
            background: var(--qs-card);
        ">
            <div class="terminal-value">
                MARKET-WIDE ANALYTICS
            </div>

            <div style="
                margin-top: 0.5rem;
                color: var(--qs-text-muted);
                font-family: var(--qs-font-mono);
                line-height: 1.8;
            ">
                Price movements · Volume flows · Trending assets
                · Market volatility · Weapon analysis ·
                Market anomalies · Cross-skin correlations
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# ORIGINAL MARKET IMPLEMENTATION
# ============================================================
#
# Temporarily disabled.
#
# Change:
#
#     if False:
#
# to:
#
#     if True:
#
# when we're ready to bring the old implementation back.
# ============================================================

if False:

    import os
    import pandas as pd
    import plotly.graph_objects as go

    from frontend.styles import style_plotly
    from backend.repositories.skin_repository import SkinRepository
    from backend.analytics.market_overview import MarketOverviewAnalyzer


    # =========================================================
    # CONFIG
    # =========================================================

    st.set_page_config(
        page_title="QuantStrike — Market",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    render_theme_toggle()
    load_css()


    # =========================================================
    # PATHS
    # =========================================================

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

    @st.cache_resource(
        show_spinner="Loading market repository..."
    )
    def load_repository():

        return SkinRepository(
            metadata_file=METADATA_FILE
        )


    repo = load_repository()


    # =========================================================
    # LOAD ANALYZER
    # =========================================================

    @st.cache_resource(
        show_spinner="Initializing market analytics..."
    )
    def load_analyzer():

        return MarketOverviewAnalyzer(
            repository=load_repository(),
            historical_file=HISTORICAL_FILE,
            cache_version="qsi_v4_parquet",
        )


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
        "QuantStrike Index, market breadth, category performance "
        "and historical market structure."
    )


    # =========================================================
    # LOAD MARKET ANALYTICS
    # =========================================================

    @st.cache_data(
        ttl=900,
        show_spinner="Calculating market analytics..."
    )
    def load_market_analytics(_analyzer):

        qsi = _analyzer.calculate_qsi()

        snapshot = _analyzer.latest_market_snapshot()

        gainers, losers = _analyzer.top_movers(10)

        breadth = _analyzer.market_breadth()

        category_indices = _analyzer.category_indices()

        category_returns = _analyzer.category_returns()

        return (
            qsi,
            snapshot,
            gainers,
            losers,
            breadth,
            category_indices,
            category_returns,
        )


    (
        qsi,
        snapshot,
        gainers,
        losers,
        breadth,
        category_indices,
        category_returns,
    ) = load_market_analytics(analyzer)


    # =========================================================
    # BASIC DATA VALIDATION
    # =========================================================

    if qsi is None or len(qsi) == 0:

        st.error(
            "QuantStrike Index data is currently unavailable."
        )

        st.stop()


    latest_qsi = float(qsi.iloc[-1])


    # =========================================================
    # DERIVED MARKET SIGNALS
    # =========================================================

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


    if len(qsi) >= 31:

        qsi_30d_change = (
            latest_qsi / float(qsi.iloc[-31]) - 1
        ) * 100

    else:

        qsi_30d_change = None


    if len(qsi) >= 365:

        qsi_52w_change = (
            latest_qsi / float(qsi.iloc[-365]) - 1
        ) * 100

    else:

        qsi_52w_change = None


    # =========================================================
    # MARKET REGIME
    # =========================================================

    advancing = int(snapshot.get("advancing", 0))
    declining = int(snapshot.get("declining", 0))

    if advancing + declining > 0:

        breadth_ratio = (
            advancing /
            (advancing + declining)
        )

    else:

        breadth_ratio = None


    if breadth_ratio is None:

        regime = "Insufficient data"

    elif breadth_ratio >= 0.60:

        regime = "Broadly Advancing"

    elif breadth_ratio <= 0.40:

        regime = "Broadly Declining"

    else:

        regime = "Mixed Market"


    # =========================================================
    # QUANTSTRIKE INDEX
    # =========================================================

    st.divider()

    st.subheader("QuantStrike Index")

    qsi_col, change_col, month_col, year_col = st.columns(4)


    with qsi_col:

        st.metric(
            "QSI",
            f"{latest_qsi:,.2f}",
        )


    with change_col:

        st.metric(
            "24H",
            (
                f"{qsi_change:+.2f}%"
                if qsi_change is not None
                else "—"
            ),
        )


    with month_col:

        st.metric(
            "30D",
            (
                f"{qsi_30d_change:+.2f}%"
                if qsi_30d_change is not None
                else "—"
            ),
        )


    with year_col:

        st.metric(
            "52W",
            (
                f"{qsi_52w_change:+.2f}%"
                if qsi_52w_change is not None
                else "—"
            ),
        )


    # =========================================================
    # QSI CHART
    # =========================================================

    qsi_chart = pd.DataFrame(
        {
            "QSI": qsi
        }
    )


    if len(qsi_chart) >= 30:

        qsi_chart["MA30"] = (
            qsi_chart["QSI"]
            .rolling(30)
            .mean()
        )


    fig = go.Figure()


    fig.add_trace(
        go.Scatter(
            x=qsi_chart.index,
            y=qsi_chart["QSI"],
            mode="lines",
            name="QSI",
            line=dict(width=2),
        )
    )


    if "MA30" in qsi_chart.columns:

        fig.add_trace(
            go.Scatter(
                x=qsi_chart.index,
                y=qsi_chart["MA30"],
                mode="lines",
                name="30D MA",
                line=dict(
                    width=1.5,
                    dash="dash",
                ),
            )
        )


    fig.update_layout(
        title="QuantStrike Market Index",
        xaxis_title="Date",
        yaxis_title="Index Value",
        hovermode="x unified",
        height=420,
        margin=dict(
            l=20,
            r=20,
            t=45,
            b=20,
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
    )


    fig = style_plotly(fig)


    st.plotly_chart(
        fig,
        use_container_width=True,
        key="qsi_chart",
    )


    st.caption(
        "QSI base value: 1,000. Asset returns are capped at "
        "±50% and assets contribute only when new price "
        "observations are available."
    )


    # =========================================================
    # MARKET SNAPSHOT
    # =========================================================

    st.divider()

    st.subheader("Market Snapshot")

    st.caption(
        "Statistics calculated from assets with actual price "
        "observations in the latest available session."
    )


    col1, col2, col3, col4, col5 = st.columns(5)


    with col1:

        st.metric(
            "Market Return",
            f"{snapshot['market_return'] * 100:+.2f}%",
        )


    with col2:

        st.metric(
            "Advancing",
            f"{snapshot['advancing']:,}",
        )


    with col3:

        st.metric(
            "Declining",
            f"{snapshot['declining']:,}",
        )


    with col4:

        st.metric(
            "Active Assets",
            f"{snapshot['active_assets']:,}",
        )


    with col5:

        st.metric(
            "Coverage",
            f"{snapshot['coverage'] * 100:.2f}%",
        )


    # =========================================================
    # MARKET REGIME
    # =========================================================

    st.subheader("Market Regime")

    regime_col, breadth_col, volatility_col = st.columns(3)


    with regime_col:

        st.metric(
            "Current Regime",
            regime,
        )


    with breadth_col:

        st.metric(
            "Advance Ratio",
            (
                f"{breadth_ratio * 100:.1f}%"
                if breadth_ratio is not None
                else "—"
            ),
        )


    with volatility_col:

        st.metric(
            "Market Volatility",
            f"{snapshot['volatility'] * 100:.2f}%",
        )


    # =========================================================
    # MARKET BREADTH
    # =========================================================

    st.divider()

    st.subheader("Market Breadth")

    st.caption(
        f"{snapshot['active_assets']:,} active assets out of "
        f"{snapshot['tracked_assets']:,} tracked assets."
    )


    breadth_clean = (
        breadth
        .dropna(how="all")
        .copy()
    )


    if not breadth_clean.empty:

        fig = go.Figure()


        if "advancing" in breadth_clean.columns:

            fig.add_trace(
                go.Scatter(
                    x=breadth_clean.index,
                    y=breadth_clean["advancing"],
                    mode="lines",
                    name="Advancing",
                )
            )


        if "declining" in breadth_clean.columns:

            fig.add_trace(
                go.Scatter(
                    x=breadth_clean.index,
                    y=breadth_clean["declining"],
                    mode="lines",
                    name="Declining",
                )
            )


        fig.update_layout(
            title="Advancing vs Declining Assets",
            height=320,
            hovermode="x unified",
            margin=dict(
                l=20,
                r=20,
                t=45,
                b=20,
            ),
        )


        fig = style_plotly(fig)


        st.plotly_chart(
            fig,
            use_container_width=True,
            key="breadth_chart",
        )


    # =========================================================
    # MARKET INDICES
    # =========================================================

    st.divider()

    st.subheader("Market Indices")

    st.caption(
        "Category-level indices track major segments of the "
        "CS2 market."
    )


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
                    "—",
                )

                continue


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
                ),
            )


    # =========================================================
    # TOP MOVERS
    # =========================================================

    st.divider()

    gainers_col, losers_col = st.columns(2)


    def format_movers(df):

        if df is None or df.empty:

            return pd.DataFrame(
                columns=[
                    "Skin",
                    "Price",
                    "24H",
                    "Category",
                ]
            )


        display = df.reset_index().copy()


        display.columns = [
            "Skin",
            "Price",
            "24H",
            "Category",
        ]


        display["Price"] = pd.to_numeric(
            display["Price"],
            errors="coerce",
        )


        display["24H"] = pd.to_numeric(
            display["24H"],
            errors="coerce",
        )


        display["Price"] = display["Price"].map(
            lambda x: (
                f"${x:,.2f}"
                if pd.notna(x)
                else "—"
            )
        )


        display["24H"] = display["24H"].map(
            lambda x: (
                f"{x * 100:+.2f}%"
                if pd.notna(x)
                else "—"
            )
        )


        return display


    with gainers_col:

        st.subheader("🚀 Top Gainers")

        display_gainers = format_movers(gainers)

        st.dataframe(
            display_gainers,
            hide_index=True,
            use_container_width=True,
        )


    with losers_col:

        st.subheader("📉 Top Losers")

        display_losers = format_movers(losers)

        st.dataframe(
            display_losers,
            hide_index=True,
            use_container_width=True,
        )


    # =========================================================
    # MARKET HEATMAP
    # =========================================================

    st.divider()

    st.subheader("Market Heatmap")

    st.caption(
        "24H performance across major CS2 market categories."
    )


    heatmap_data = []


    for category in display_categories:

        value = category_returns.get(category)


        heatmap_data.append(
            {
                "Category": category,
                "Value": (
                    value * 100
                    if value is not None
                    and pd.notna(value)
                    else None
                ),
            }
        )


    heatmap = pd.DataFrame(heatmap_data)


    fig = go.Figure(
        data=go.Heatmap(
            z=[
                heatmap["Value"]
                .fillna(0)
                .tolist()
            ],

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
                title="Return",
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
            b=20,
        ),
    )


    fig = style_plotly(fig)


    st.plotly_chart(
        fig,
        use_container_width=True,
        key="market_heatmap",
    )


    # =========================================================
    # MARKET DATA SOURCES
    # =========================================================

    st.divider()

    st.subheader("Market Data")

    st.info(
        "QuantStrike currently uses the historical dataset "
        "for market analytics. Live Market.CSGO pricing and "
        "sales history can be connected as an additional data "
        "source in a future update."
    )


    # =========================================================
    # DIAGNOSTICS
    # =========================================================

    st.divider()

    with st.expander(
        "🔬 QuantStrike Diagnostics",
        expanded=False,
    ):

        st.caption(
            "Technical diagnostics for validating the market "
            "data cleaning and return calculations."
        )


        @st.cache_data(
            ttl=900,
            show_spinner="Running diagnostics..."
        )
        def load_diagnostics(_analyzer):

            outlier_stats = (
                _analyzer.outlier_diagnostics()
            )

            return_stats = (
                _analyzer.return_diagnostics()
            )

            rejected = (
                _analyzer.rejected_observations(25)
            )

            return (
                outlier_stats,
                return_stats,
                rejected,
            )


        (
            outlier_stats,
            return_stats,
            rejected,
        ) = load_diagnostics(analyzer)


        col1, col2, col3 = st.columns(3)


        with col1:

            st.metric(
                "Rejected Outliers",
                f"{outlier_stats['rejected_count']:,}",
            )


        with col2:

            st.metric(
                "Negative Outliers",
                f"{outlier_stats['negative_count']:,}",
            )


        with col3:

            st.metric(
                "Positive Outliers",
                f"{outlier_stats['positive_count']:,}",
            )


        st.write(
            "Return distribution after V3 cleaning:"
        )


        st.json(return_stats)


        if rejected.empty:

            st.info(
                "No observations were rejected by the "
                "V3 z-score filter."
            )

        else:

            st.write(
                "Most extreme rejected observations:"
            )


            display_rejected = rejected.copy()


            if "return" in display_rejected.columns:

                display_rejected["return"] = (
                    display_rejected["return"] * 100
                ).map(
                    lambda x: f"{x:+.2f}%"
                )


            if "z_score" in display_rejected.columns:

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


    # =========================================================
    # PERFORMANCE INFORMATION
    # =========================================================

    with st.expander(
        "⚙️ Performance Information",
        expanded=False,
    ):

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