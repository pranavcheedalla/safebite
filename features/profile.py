"""
PROFILE + ALERTS

Manage allergies, medications, and foods to avoid. The scanner reads these
lists when checking products.
"""
import streamlit as st
from shared import db


COMMON_ALLERGIES = ["peanuts", "milk", "eggs", "soy", "wheat", "shellfish"]


def _render_list(username, user, label, field):
    st.subheader(label)
    items = user.get(field, [])

    with st.form(f"profile_add_{field}"):
        value = st.text_input(f"Add {label.lower()}")
        submitted = st.form_submit_button("Add")

    if submitted:
        item = value.strip().lower()
        if not item:
            st.error("Enter a value first.")
        elif item in items:
            st.info(f"{item.capitalize()} is already on your list.")
        else:
            items.append(item)
            db.save_user(username, user)
            st.rerun()

    for index, item in enumerate(items):
        name, remove = st.columns([5, 1])
        name.write(item)
        if remove.button("Remove", key=f"profile_remove_{field}_{index}"):
            items.pop(index)
            db.save_user(username, user)
            st.rerun()

    if not items:
        st.caption(f"No {label.lower()} added yet.")


def show(username):
    st.header("My Profile")
    user = db.get_user(username)

    alerts = [
        scan for scan in user.get("scan_history", [])
        if str(scan.get("level", "")).lower() != "safe"
    ]
    if alerts:
        st.warning(f"You have {len(alerts)} food scan alert(s) to review.")
        for scan in alerts:
            name = scan.get("name", "Unknown food")
            level = scan.get("level", "unknown")
            st.write(f"- **{name}** — {level}")
    else:
        st.success("No food scan alerts.")

    st.subheader("Common allergies")
    common = st.selectbox(
        "Choose a common allergy",
        ["Choose one..."] + COMMON_ALLERGIES,
        key="profile_common_allergy",
    )
    if st.button("Add common allergy", key="profile_add_common_allergy"):
        if common == "Choose one...":
            st.error("Choose an allergy first.")
        elif common in user["allergies"]:
            st.info(f"{common.capitalize()} is already on your allergy list.")
        else:
            user["allergies"].append(common)
            db.save_user(username, user)
            st.rerun()

    _render_list(username, user, "Allergies", "allergies")
    _render_list(username, user, "Medications", "medications")
    _render_list(username, user, "Foods to avoid", "avoid_foods")
