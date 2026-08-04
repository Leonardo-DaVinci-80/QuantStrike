import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.append(str(ROOT))

import streamlit as st  # type: ignore
from backend.repositories.skin_repository import SkinRepository

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
    except (FileNotFoundError, ValueError) as e:
        st.error(f"Could not load data for {skin_b.name}: {e}")
        st.stop()

    st.subheader("Comparison")

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
        ],
    }

    import pandas as pd
    comparison_df = pd.DataFrame(comparison_data).set_index("Metric")
    st.table(comparison_df)