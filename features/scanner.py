"""
FOOD SCANNER  (owner: Pranav)

Scan or type a barcode, look up the food, and warn the user if it conflicts
with their allergies, medications or foods to avoid.

TODO ideas:
- Smarter matching (e.g. "milk" allergy should also catch "whey", "casein")
- Show the product photo from Open Food Facts
- Filter/sort scan history
"""
from datetime import datetime

import streamlit as st
from shared import db
from shared.barcode import lookup_barcode, read_barcode_from_image
from shared.interactions import FOOD_DRUG_INTERACTIONS


def check_food(product, user):
    """Returns (level, reasons). level is "safe", "caution" or "avoid"."""
    reasons = []
    level = "safe"
    text = product["ingredients"] + " " + " ".join(product["allergens"])

    # Allergies -> avoid
    allergies = user["allergies"]
    for i in range(len(allergies)):
        if allergies[i] in text:
            reasons.append("Contains " + allergies[i] + " (allergy)")
            level = "avoid"

    # Medication interactions -> caution
    medications = user["medications"]
    for i in range(len(medications)):
        for drug in FOOD_DRUG_INTERACTIONS:
            if drug in medications[i]:
                pairs = FOOD_DRUG_INTERACTIONS[drug]
                for j in range(len(pairs)):
                    food = pairs[j][0]
                    if food in text:
                        reasons.append(food.capitalize() + " + " + medications[i] + ": " + pairs[j][1])
                        if level == "safe":
                            level = "caution"

    # Foods to avoid -> caution
    avoid_foods = user["avoid_foods"]
    for i in range(len(avoid_foods)):
        if avoid_foods[i] in text:
            reasons.append("Contains " + avoid_foods[i] + " (on your avoid list)")
            if level == "safe":
                level = "caution"

    return level, reasons


def show_result(level, reasons):
    if level == "avoid":
        st.error("🔴 AVOID")
    elif level == "caution":
        st.warning("🟡 CAUTION")
    else:
        st.success("🟢 Looks safe based on your profile")
    for i in range(len(reasons)):
        st.write("- " + reasons[i])


def show(username):
    st.header("Food Scanner")
    user = db.get_user(username)

    code = st.text_input("Type a barcode number", placeholder="e.g. 3017620422003")
    photo = st.camera_input("Or take a photo of the barcode")
    if photo is not None:
        found = read_barcode_from_image(photo)
        if found is None:
            st.info("Couldn't read a barcode from that photo. Try typing it instead.")
        else:
            code = found
            st.write("Found barcode: " + code)

    if code:
        product = lookup_barcode(code)
        if product is None:
            st.error("Product not found.")
        else:
            st.subheader(product["name"])
            level, reasons = check_food(product, user)
            show_result(level, reasons)
            with st.expander("Ingredients"):
                st.write(product["ingredients"] or "No ingredients listed.")

            if st.button("Save to history"):
                user["scan_history"].append({
                    "code": code,
                    "name": product["name"],
                    "level": level,
                    "reasons": reasons,
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                })
                db.save_user(username, user)
                st.success("Saved!")

    st.subheader("Scan History")
    history = user["scan_history"]
    if len(history) == 0:
        st.write("No scans yet.")
    for i in range(len(history) - 1, -1, -1):
        entry = history[i]
        st.write(entry["time"] + " - " + entry["name"] + " (" + entry["level"] + ")")
