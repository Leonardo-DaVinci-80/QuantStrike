
import streamlit as st
import pandas as pd

from frontend.feature_helpers import choose_asset, latest_price_map
from backend.services.feature_watchlist import (
    add_item,
    remove_item,
    list_items,
    create_alert,
    alert_rules,
    alert_history,
    evaluate_alerts,
    delete_alert_rule,
)
from styles import load_css, render_theme_toggle


st.set_page_config(
    page_title="Watchlist & Alerts | QuantStrike",
    layout="wide",
)

render_theme_toggle()
load_css()

st.title("🔔 Watchlist & Price Alerts")
st.caption(
    "Alerts are evaluated when this page is opened or refreshed. "
    "Background scheduling and push notifications are not enabled."
)


# Asset selection and alert creation
repo, variant = choose_asset(key="watch")

if variant:
    if st.button("Add selected asset to watchlist"):
        try:
            add_item(variant["skin_id"], variant["name"])
            st.success("Added to watchlist.")
        except Exception as e:
            st.error(f"Could not add asset: {e}")

    with st.form("alert_rule"):
        metric = st.selectbox("Metric", ["price", "return_pct"])
        operator = st.selectbox("Condition", [">=", "<=", ">", "<"])
        threshold = st.number_input("Threshold", value=100.0)
        cooldown = st.number_input(
            "Cooldown (minutes)", min_value=0, value=60
        )
        save = st.form_submit_button("Create alert")

    if save:
        try:
            create_alert(
                variant["skin_id"],
                metric,
                operator,
                threshold,
                cooldown,
            )
            st.success("Alert rule saved.")
            st.rerun()
        except Exception as e:
            st.error(f"Could not create alert: {e}")


# Watchlist
st.subheader("Watchlist")
items = list_items()

if items:
    prices = latest_price_map([item["asset_id"] for item in items])
    display_items = []

    for item in items:
        display_item = dict(item)
        display_item["metadata_price_snapshot"] = prices.get(
            str(item["asset_id"])
        )
        display_items.append(display_item)

    st.dataframe(
        pd.DataFrame(display_items),
        use_container_width=True,
        hide_index=True,
    )

    selected_item = st.selectbox(
        "Remove asset",
        items,
        format_func=lambda item: item["asset_name"],
        key="remove_watch",
    )

    if st.button("Remove from watchlist"):
        try:
            remove_item(selected_item["asset_id"])
            st.rerun()
        except Exception as e:
            st.error(f"Could not remove asset: {e}")

    if st.button("Evaluate price alerts now"):
        values = {}

        for item in items:
            asset_id = str(item["asset_id"])
            if asset_id in prices:
                values[asset_id] = {"price": prices[asset_id]}

        try:
            fired = evaluate_alerts(values)

            if fired:
                for message in fired:
                    st.warning(message)
            else:
                st.info(
                    "No rules triggered by the available "
                    "latest-price snapshots."
                )
        except Exception as e:
            st.error(f"Could not evaluate alerts: {e}")
else:
    st.info("Your watchlist is empty.")


# Configured rules and deletion
st.subheader("Configured rules")
rules = alert_rules()

if rules:
    st.dataframe(
        pd.DataFrame(rules),
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("#### Delete an alert rule")
    st.warning(
        "Deleting a rule also deletes its associated alert history. "
        "Other rules and their history are not affected."
    )

    selected_rule = st.selectbox(
        "Rule to delete",
        rules,
        format_func=lambda rule: (
            f"#{rule['id']} · {rule['asset_id']} · "
            f"{rule['metric']} {rule['operator']} {rule['threshold']}"
        ),
        key="delete_alert_rule",
    )

    confirm_rule_delete = st.checkbox(
        "I understand this also deletes the selected rule's alert history.",
        key="confirm_delete_alert_rule",
    )

    if st.button(
        "Permanently delete alert rule",
        disabled=not confirm_rule_delete,
    ):
        try:
            deleted = delete_alert_rule(selected_rule["id"])

            if deleted:
                st.success("Alert rule deleted.")
                st.rerun()
            else:
                st.info("That alert rule no longer exists.")
        except Exception as e:
            st.error(f"Could not delete alert rule: {e}")
else:
    st.caption("No alert rules yet.")


# Alert history
st.subheader("Alert history")
history = alert_history()

if history:
    st.dataframe(
        pd.DataFrame(history),
        use_container_width=True,
        hide_index=True,
    )
else:
    st.caption("No alerts have fired.")
