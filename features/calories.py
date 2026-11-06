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
import streamlit as st
from datetime import date
from shared import db

# Skipped barcode import for now to keep it simple

def show(username):
    st.header("Calorie Tracker")
    
    # 1. Load the user's data
    user = db.get_user(username)
    
    # 2. Daily Goal Input
    # Uses st.number_input and saves it back to the database if changed
    current_goal = user.get("calorie_goal", 2000)
    new_goal = st.number_input("Daily Calorie Goal", min_value=1, value=current_goal)
    
    if new_goal != current_goal:
        user["calorie_goal"] = new_goal
        db.save_user(username, user)
        
    # 3. Filter today's foods
    today_str = str(date.today())
    if "calorie_log" not in user:
        user["calorie_log"] = []
        
    today_log = [entry for entry in user["calorie_log"] if entry.get("date") == today_str]
    total_calories = sum(entry.get("calories", 0) for entry in today_log)
    
    # 4. Display Progress
    st.metric("Today's Total Calories", f"{total_calories} / {user['calorie_goal']} kcal")
    
    # Progress bar maxes out at 1.0 (100%), so we cap the value to prevent errors
    progress_val = min(total_calories / user["calorie_goal"], 1.0)
    st.progress(progress_val)
    
    if total_calories > user["calorie_goal"]:
        st.warning("You have exceeded your daily calorie goal!")
        
    st.divider()

    # 5. Add Food Form
    st.subheader("Add Food")
    with st.form("add_food_form", clear_on_submit=True):
        food_name = st.text_input("Food Name")
        food_cals = st.number_input("Calories", min_value=0, step=50)
        submitted = st.form_submit_button("Add")
        
        if submitted and food_name:
            user["calorie_log"].append({
                "date": today_str,
                "name": food_name,
                "calories": food_cals
            })
            db.save_user(username, user)
            st.rerun() # Refreshes the page to show the new data instantly

    # 6. List Today's Foods and Remove Buttons
    st.subheader("Today's Foods")
    if not today_log:
        st.info("No foods logged today yet.")
    else:
        # Loop through the whole log, but only show today's items
        for i, entry in enumerate(user["calorie_log"]):
            if entry.get("date") == today_str:
                col1, col2, col3 = st.columns([3, 1, 1])
                col1.write(entry["name"])
                col2.write(f"{entry['calories']} kcal")
                
                # Each button needs a unique key, so we use the index 'i'
                if col3.button("Remove", key=f"remove_{i}"):
                    user["calorie_log"].pop(i)
                    db.save_user(username, user)
                    st.rerun()
