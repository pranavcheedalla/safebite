"""
PROFILE + ALERTS  (owner: Audrina)

Lets the user save allergies, medications and foods to avoid.
Everything else in the app reads from this, so build it first.

What to build:
- Add/remove items in user["allergies"], user["medications"], user["avoid_foods"]
- Save items in lowercase (the scanner compares lowercase text)
- Show an alert if any entry in user["scan_history"] has a "level" that isn't "safe"

Useful shared code:
- db.get_user(username) / db.save_user(username, user)  (see shared/db.py)
"""
import streamlit as st
from shared import db


def show(username):
    st.header("My Profile")
    st.info("Not built yet.")
