import streamlit as st
import requests
from datetime import date
from shared import db

def get_nutrition_data(query):
    app_id = "2298590f"
    app_key = "9705fc9b3e97fede0990ff90c5d9bea0"
    
    url = "https://api.edamam.com/api/nutrition-data"
    params = {
        "app_id": app_id,
        "app_key": app_key,
        "ingr": query,
        "nutrition-type": "logging"
    }
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        return None
    return None

def show(username):
    st.header("Calorie Tracker")
    
    user = db.get_user(username)
    
    current_goal = user.get("calorie_goal", 2000)
    new_goal = st.number_input("Daily Calorie Goal", min_value=1, value=current_goal)
    
    if new_goal != current_goal:
        user["calorie_goal"] = new_goal
        db.save_user(username, user)
        
    today_str = str(date.today())
    if "calorie_log" not in user:
        user["calorie_log"] = []
        
    today_log = [entry for entry in user["calorie_log"] if entry.get("date") == today_str]
    total_calories = sum(entry.get("calories", 0) for entry in today_log)
    
    st.metric("Today's Total Calories", f"{total_calories} / {user['calorie_goal']} kcal")
    
    progress_val = min(total_calories / user["calorie_goal"], 1.0)
    st.progress(progress_val)
    
    if total_calories > user["calorie_goal"]:
        st.warning("You have exceeded your daily calorie goal!")
        
    st.divider()

    st.subheader("Add Food")
    
    if "searched_food" not in st.session_state:
        st.session_state.searched_food = None

    search_query = st.text_input("What did you eat?", placeholder="e.g., 1 cup milk, 2 eggs, or 100g chicken breast")
    
    if st.button("Search Calories"):
        if search_query:
            with st.spinner("Calculating calories..."):
                data = get_nutrition_data(search_query)
                
                if data and data.get("calories", 0) > 0:
                    st.session_state.searched_food = {
                        "name": search_query.capitalize(),
                        "calories": round(data["calories"])
                    }
                else:
                    st.error("Could not find nutritional info. Check your spelling or try being more specific.")

    if st.session_state.searched_food:
        food = st.session_state.searched_food
        st.success(f"Calculated: **{food['name']}** is **{food['calories']} kcal**")
        
        if st.button("Add to Log"):
            user["calorie_log"].append({
                "date": today_str,
                "name": food['name'],
                "calories": food['calories']
            })
            db.save_user(username, user)
            st.session_state.searched_food = None 
            st.rerun()

    st.divider()

    st.subheader("Today's Foods")
    if not today_log:
        st.info("No foods logged today yet.")
    else:
        for i, entry in enumerate(user["calorie_log"]):
            if entry.get("date") == today_str:
                col1, col2, col3 = st.columns([3, 1, 1])
                col1.write(entry["name"])
                col2.write(f"{entry['calories']} kcal")
                
                if col3.button("Remove", key=f"remove_{i}"):
                    user["calorie_log"].pop(i)
                    db.save_user(username, user)
                    st.rerun()