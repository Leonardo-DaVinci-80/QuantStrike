
import streamlit as st
import pandas as pd

from frontend.feature_helpers import choose_asset, latest_price_map
from backend.services.feature_portfolio import (
    add_transaction,
    get_transactions,
    holdings,
    delete_holding_transactions,
)
from styles import load_css, render_theme_toggle


st.set_page_config(
    page_title="Portfolio | QuantStrike",
    layout="wide",
)

render_theme_toggle()
load_css()

st.title("💼 Portfolio Tracker")
st.caption(
    "Local transaction ledger with average-cost realized P&L. "
    "Market values use the latest price in the bundled metadata "
    "snapshot, not live exchange quotes."
)

portfolio_id = st.text_input("Portfolio name / ID", "main")
repo, variant = choose_asset(key="portfolio")

with st.form("portfolio_tx"):
    side = st.selectbox("Transaction", ["BUY", "SELL"])
    quantity = st.number_input(
        "Quantity", min_value=0.001, value=1.0, step=0.1
    )
    unit_price = st.number_input(
        "Unit price (USD)", min_value=0.0, value=0.0, step=1.0
    )
    fees = st.number_input(
        "Fees (USD)", min_value=0.0, value=0.0, step=0.1
    )
    note = st.text_input("Note (optional)")
    submitted = st.form_submit_button("Record transaction")

if submitted:
    if not variant:
        st.error("Search for and select an asset first.")
    else:
        try:
            add_transaction(
                portfolio_id,
                variant["skin_id"],
                variant["name"],
                side,
                quantity,
                unit_price,
                fees,
                "USD",
                note=note,
            )
            st.success("Transaction recorded.")
            st.rerun()
        except Exception as e:
            st.error(f"Could not record transaction: {e}")


st.subheader("Open holdings")
portfolio_holdings = holdings(portfolio_id)

if portfolio_holdings:
    prices = latest_price_map(
        [item["asset_id"] for item in portfolio_holdings]
    )
    display_holdings = []

    for item in portfolio_holdings:
        display_item = dict(item)
        market_price = prices.get(str(item["asset_id"]))
        display_item["market_price_snapshot"] = market_price

        if market_price is not None:
            market_value = item["quantity"] * market_price
            display_item["market_value_snapshot"] = market_value
            display_item["unrealized_pnl_snapshot"] = (
                market_value - item["cost_basis"]
            )
        else:
            display_item["market_value_snapshot"] = None
            display_item["unrealized_pnl_snapshot"] = None

        display_holdings.append(display_item)

    df = pd.DataFrame(display_holdings)
    col1, col2, col3 = st.columns(3)

    col1.metric("Open positions", len(portfolio_holdings))
    col2.metric("Cost basis", f"${df['cost_basis'].sum():,.2f}")

    pnl = df["unrealized_pnl_snapshot"].dropna().sum()
    col3.metric(
        "Snapshot unrealized P&L",
        f"${pnl:,.2f}",
        help="Only assets with an available metadata latest price are included.",
    )

    st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("#### Remove an open holding")
    st.warning(
        "This permanently deletes every recorded transaction for the "
        "selected asset in this portfolio. Transaction history and "
        "realized P&L for that asset will be lost. This is not a sale."
    )

    selected_holding = st.selectbox(
        "Holding to remove",
        portfolio_holdings,
        format_func=lambda item: (
            f"{item['asset_name']} — "
            f"{item['quantity']:g} units"
        ),
        key="delete_holding_asset",
    )

    confirm_remove = st.checkbox(
        "I understand that this deletes the holding's transaction history.",
        key="confirm_delete_holding",
    )

    if st.button(
        "Permanently remove holding",
        disabled=not confirm_remove,
        type="secondary",
    ):
        try:
            deleted = delete_holding_transactions(
                portfolio_id,
                selected_holding["asset_id"],
            )

            if deleted:
                st.success(
                    f"Removed {selected_holding['asset_name']} "
                    "and its transaction history."
                )
                st.rerun()
            else:
                st.info("No matching transactions were found.")
        except Exception as e:
            st.error(f"Could not remove holding: {e}")

else:
    st.info(
        "No open holdings yet. Record a buy transaction above to begin."
    )


with st.expander("Transaction history"):
    transactions = get_transactions(portfolio_id)

    if transactions:
        st.dataframe(
            pd.DataFrame(transactions),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.caption("No transactions recorded.")
