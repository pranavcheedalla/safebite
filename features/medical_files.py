"""
MEDICAL FILES  (stretch goal, owner: ________)

Upload and view files like prescriptions or doctor's notes.
USE FAKE TEST FILES ONLY. Never upload real medical documents to this app.

TODO ideas:
- Show image previews
- Add a note/label to each file
- Delete files
"""
import os

import streamlit as st
from shared import db

UPLOAD_FOLDER = os.path.join("data", "uploads")


def show(username):
    st.header("Medical Files")
    st.caption("Demo only: please upload fake test files, not real medical records.")
    user = db.get_user(username)

    uploaded = st.file_uploader("Upload a file", type=["pdf", "png", "jpg", "jpeg"])
    if uploaded is not None and st.button("Save file"):
        folder = os.path.join(UPLOAD_FOLDER, username)
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, uploaded.name)
        with open(path, "wb") as file:
            file.write(uploaded.getbuffer())
        user["files"].append({"name": uploaded.name, "path": path})
        db.save_user(username, user)
        st.success("Saved " + uploaded.name)

    st.subheader("My Files")
    files = user["files"]
    if len(files) == 0:
        st.write("No files yet.")
    for i in range(len(files)):
        path = files[i]["path"]
        if os.path.exists(path):
            with open(path, "rb") as file:
                st.download_button(files[i]["name"], file.read(), file_name=files[i]["name"], key="file_" + str(i))
