"""
PROFILE + ALERTS  (owner: ________)

Lets the user save allergies, medications and foods to avoid.
Everything else in the app reads from this, so build it first.

TODO ideas:
- Show recent warning alerts from scan history on this page
- Let users remove an item by clicking an X next to it
- Suggest common allergies from a dropdown
"""
import streamlit as st
from shared import db


def edit_list(user, key, label, placeholder):
    st.subheader(label)
    items = user[key]

    for i in range(len(items)):
        left, right = st.columns([5, 1])
        left.write("• " + items[i])
        if right.button("Remove", key=key + "_remove_" + str(i)):
            items.pop(i)
            return True

    new_item = st.text_input("Add to " + label.lower(), placeholder=placeholder, key=key + "_input")
    if st.button("Add", key=key + "_add") and new_item.strip() != "":
        items.append(new_item.strip().lower())
        return True
    return False


def show(username):
    st.header("My Profile")
    user = db.get_user(username)

    # Alerts: count recent scans with warnings
    history = user["scan_history"]
    warning_count = 0
    for i in range(len(history)):
        if history[i]["level"] != "safe":
            warning_count += 1
    if warning_count > 0:
        st.warning(str(warning_count) + " of your scanned foods had warnings. Check the Food Scanner tab.")

    changed = False
    if edit_list(user, "allergies", "Allergies", "e.g. peanuts"):
        changed = True
    if edit_list(user, "medications", "Medications", "e.g. warfarin"):
        changed = True
    if edit_list(user, "avoid_foods", "Foods to Avoid", "e.g. gluten"):
        changed = True

    if changed:
        db.save_user(username, user)
        st.rerun()
