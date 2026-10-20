"""
Main app. Run with:  streamlit run app.py

Each tab lives in its own file inside features/, so everyone can work on
their own file without stepping on each other.
"""
import streamlit as st
from features import calories, medical_files, profile, scanner

st.set_page_config(page_title="SafeBite", page_icon="🥗")
st.title("🥗 SafeBite")

# Simple login: just a username for now (no password). Firebase login comes later.
if "username" not in st.session_state:
    st.session_state.username = ""

with st.sidebar:
    st.header("Log in")
    name = st.text_input("Username", value=st.session_state.username)
    if st.button("Log in") and name.strip() != "":
        st.session_state.username = name.strip().lower()
        st.rerun()
    if st.session_state.username:
        st.write("Logged in as **" + st.session_state.username + "**")
        if st.button("Log out"):
            st.session_state.username = ""
            st.rerun()

if not st.session_state.username:
    st.info("Enter a username in the sidebar to get started.")
    st.stop()

username = st.session_state.username
tab_profile, tab_scanner, tab_calories, tab_files = st.tabs(
    ["Profile", "Food Scanner", "Calories", "Medical Files"]
)

with tab_profile:
    profile.show(username)
with tab_scanner:
    scanner.show(username)
with tab_calories:
    calories.show(username)
with tab_files:
    medical_files.show(username)
