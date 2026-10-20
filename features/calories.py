"""
CALORIE TRACKER  (owner: Vedanth)

Log foods by hand or by barcode, set a daily goal, and see progress.

TODO ideas:
- Weekly chart of calories per day (st.bar_chart)
- Delete a logged food
- Track protein/carbs/fat too (Open Food Facts has them)
"""
from datetime import date

import streamlit as st
from shared import db
from shared.barcode import lookup_barcode


def show(username):
    st.header("Calorie Tracker")
    user = db.get_user(username)
    today = str(date.today())

    goal = st.number_input("Daily calorie goal", min_value=500, max_value=6000, value=user["calorie_goal"], step=50)
    if goal != user["calorie_goal"]:
        user["calorie_goal"] = goal
        db.save_user(username, user)

    st.subheader("Add food")
    method = st.radio("How?", ["Type it in", "Barcode"], horizontal=True)
    name = ""
    calories = 0

    if method == "Type it in":
        name = st.text_input("Food name")
        calories = st.number_input("Calories", min_value=0, step=10)
    else:
        code = st.text_input("Barcode number")
        if code:
            product = lookup_barcode(code)
            if product is None:
                st.error("Product not found.")
            else:
                name = product["name"]
                if product["calories_per_serving"] is not None:
                    calories = int(product["calories_per_serving"])
                    st.write(name + ": " + str(calories) + " cal per serving (" + str(product["serving_size"]) + ")")
                elif product["calories_per_100g"] is not None:
                    calories = int(product["calories_per_100g"])
                    st.write(name + ": " + str(calories) + " cal per 100g")
                else:
                    st.write("No calorie info for this product.")

    if st.button("Add to today") and name != "":
        user["calorie_log"].append({"date": today, "name": name, "calories": calories})
        db.save_user(username, user)
        st.rerun()

    # Today's total
    st.subheader("Today")
    total = 0
    log = user["calorie_log"]
    for i in range(len(log)):
        if log[i]["date"] == today:
            st.write("- " + log[i]["name"] + ": " + str(log[i]["calories"]) + " cal")
            total += log[i]["calories"]

    st.metric("Total", str(total) + " / " + str(goal) + " cal")
    st.progress(min(total / goal, 1.0))
