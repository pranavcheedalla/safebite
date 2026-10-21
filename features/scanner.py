"""
FOOD SCANNER  (owner: Pranav)

Scan or type a barcode, look up the food, and warn the user if it conflicts
with their allergies, medications or foods to avoid.

What to build:
- Get a barcode (typed in, or from a photo with st.camera_input)
- Look up the product and show its name and ingredients
- Decide "safe", "caution" or "avoid" using the user's profile, and show why
- Save scans to user["scan_history"] as {"code", "name", "level", "reasons", "time"}
  (the Profile tab reads "level" from these)

Useful shared code:
- lookup_barcode(code), read_barcode_from_image(photo)  (see shared/barcode.py)
- FOOD_DRUG_INTERACTIONS  (see shared/interactions.py)
- db.get_user(username) / db.save_user(username, user)
"""
import streamlit as st
from shared import db
from shared.barcode import lookup_barcode, read_barcode_from_image
from shared.interactions import FOOD_DRUG_INTERACTIONS


def show(username):
    st.header("Food Scanner")
    st.info("Not built yet.")
