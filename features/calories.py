"""
CALORIE TRACKER  (owner: Vedanth)

Log foods by hand or by barcode, set a daily goal, and see progress.

What to build:
- Let the user set user["calorie_goal"]
- Add foods to user["calorie_log"] as {"date", "name", "calories"}
- Add foods by barcode using the product's calorie info
- Show today's foods, the total, and progress toward the goal

Useful shared code:
- lookup_barcode(code)  (see shared/barcode.py for the fields it returns)
- db.get_user(username) / db.save_user(username, user)
"""
import streamlit as st
from shared import db
from shared.barcode import lookup_barcode


def show(username):
    st.header("Calorie Tracker")
    st.info("Not built yet.")
