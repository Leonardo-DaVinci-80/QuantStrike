
import streamlit as st
import pandas as pd

from frontend.feature_helpers import choose_asset
from backend.services.feature_journal import (
    create_entry,
    list_entries,
    update_entry,
    delete_entry,
)
from styles import load_css, render_theme_toggle


st.set_page_config(
    page_title="Research Journal | QuantStrike",
    layout="wide",
)

render_theme_toggle()
load_css()

st.title("📓 Research Journal")
st.caption(
    "Save hypotheses, notes and asset references so market research "
    "is reproducible."
)


# --------------------------------------------------
# CREATE A NEW ENTRY
# --------------------------------------------------

st.subheader("New research entry")

repo, variant = choose_asset(key="journal")

with st.form("research_entry"):
    title = st.text_input("Title")
    hypothesis = st.text_area("Hypothesis")
    body = st.text_area("Research notes / evidence")
    submitted = st.form_submit_button("Save research entry")

if submitted:
    try:
        entry_id = create_entry(
            title,
            hypothesis,
            body,
            [variant["skin_id"]] if variant else [],
        )
        st.success(f"Saved research entry #{entry_id}.")
        st.rerun()
    except Exception as e:
        st.error(f"Could not save research entry: {e}")


# --------------------------------------------------
# LOAD EXISTING ENTRIES
# --------------------------------------------------

st.divider()
st.subheader("Previous research entries")

entries = list_entries()

if not entries:
    st.info("No research entries yet.")
else:
    # Keep the table readable by displaying the decoded asset IDs.
    display_entries = []

    for entry in entries:
        display_entry = dict(entry)
        display_entry["asset_ids"] = ", ".join(
            str(asset_id) for asset_id in entry.get("asset_ids", [])
        )
        display_entry.pop("evidence", None)
        display_entries.append(display_entry)

    st.dataframe(
        pd.DataFrame(display_entries),
        use_container_width=True,
        hide_index=True,
    )

    # --------------------------------------------------
    # SELECT AN ENTRY TO EDIT OR DELETE
    # --------------------------------------------------

    st.markdown("### Manage an existing entry")

    selected_entry = st.selectbox(
        "Select research entry",
        entries,
        format_func=lambda entry: (
            f"#{entry['id']} · {entry['title']}"
        ),
        key="journal_manage_entry",
    )

    st.markdown("#### Edit entry")

    with st.form("edit_research_entry"):
        edited_title = st.text_input(
            "Title",
            value=selected_entry.get("title") or "",
            key=f"edit_title_{selected_entry['id']}",
        )
        edited_hypothesis = st.text_area(
            "Hypothesis",
            value=selected_entry.get("hypothesis") or "",
            key=f"edit_hypothesis_{selected_entry['id']}",
        )
        edited_body = st.text_area(
            "Research notes / evidence",
            value=selected_entry.get("body") or "",
            key=f"edit_body_{selected_entry['id']}",
        )

        save_changes = st.form_submit_button("Save changes")

    if save_changes:
        try:
            updated = update_entry(
                entry_id=selected_entry["id"],
                title=edited_title,
                hypothesis=edited_hypothesis,
                body=edited_body,
                asset_ids=selected_entry.get("asset_ids", []),
                evidence=selected_entry.get("evidence", {}),
            )

            if updated:
                st.success("Research entry updated.")
                st.rerun()
            else:
                st.error("The entry was not found or could not be updated.")
        except Exception as e:
            st.error(f"Could not update entry: {e}")

    # --------------------------------------------------
    # DELETE AN ENTRY
    # --------------------------------------------------

    st.markdown("#### Delete entry")

    st.warning(
        "Deleting a research entry is permanent. "
        "The selected entry and its saved notes will be removed."
    )

    confirm_delete = st.checkbox(
        f"I want to permanently delete entry #{selected_entry['id']}.",
        key=f"confirm_delete_journal_{selected_entry['id']}",
    )

    if st.button(
        "Permanently delete research entry",
        disabled=not confirm_delete,
        key=f"delete_journal_{selected_entry['id']}",
    ):
        try:
            deleted = delete_entry(selected_entry["id"])

            if deleted:
                st.success("Research entry deleted.")
                st.rerun()
            else:
                st.info("That research entry no longer exists.")
        except Exception as e:
            st.error(f"Could not delete research entry: {e}")
