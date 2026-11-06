"""
MEDICAL FILES  (stretch goal, owner: ________)

Upload and view files like prescriptions or doctor's notes.
USE FAKE TEST FILES ONLY. Never upload real medical documents to this app.

What to build:
- Upload a file (st.file_uploader) and save it under data/uploads/<username>/
- Record it in user["files"] as {"name", "path"}
- List the user's files with a download button for each

Useful shared code:
- db.get_user(username) / db.save_user(username, user)
"""
import streamlit as st
from shared import db


def show(username):
    st.header("Medical Files")
    st.caption("Demo only: please upload fake test files, not real medical records.")
    st.info("Not built yet.")
