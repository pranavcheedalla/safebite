"""
FOOD SCANNER  (owner: Pranav)

Scans are saved to user["scan_history"] as
{"code", "name", "level", "reasons", "time"}
"""
from datetime import datetime

import streamlit as st
from shared import db
from shared.barcode import lookup_barcode, read_barcode_from_image
from shared.interactions import FOOD_DRUG_INTERACTIONS

# Extra words that count as an allergy (the stretch task).
# If the user is allergic to "milk", we also look for these words.
RELATED_TERMS = {
    "milk": ["whey", "casein", "lactose"],
}


def check_food(product, user):
    """Decide if a food is safe for this user.
    Returns a pair: (level, reasons)
    level   is "safe", "caution" or "avoid"
    reasons is a list of sentences explaining why
    """
    level = "safe"
    reasons = []

    # One big lowercase string to search inside.
    ingredients_text = product.get("ingredients") or ""
    allergens_list = product.get("allergens") or []
    searchable = (ingredients_text + " " + " ".join(allergens_list)).lower()

    # 1. Allergies -> "avoid"
    for allergy in user.get("allergies", []):
        allergy = allergy.lower()
        words = [allergy] + RELATED_TERMS.get(allergy, [])
        for word in words:
            if word in searchable:
                level = "avoid"
                if word == allergy:
                    reasons.append(f"Contains {allergy}, which you are allergic to.")
                else:
                    reasons.append(f"Contains {word}, which comes from {allergy} (you are allergic to {allergy}).")
                break  # one reason per allergy is enough

    # 2. Medication interactions -> "caution"
    for medication in user.get("medications", []):
        interactions = FOOD_DRUG_INTERACTIONS.get(medication.lower(), [])
        for food, message in interactions:
            if food in searchable:
                if level != "avoid":   # never downgrade an "avoid"
                    level = "caution"
                reasons.append(f"{medication}: {message}")

    # 3. Foods the user wants to avoid -> "caution"
    for food in user.get("avoid_foods", []):
        if food.lower() in searchable:
            if level != "avoid":
                level = "caution"
            reasons.append(f"Contains {food}, which is on your foods-to-avoid list.")

    return level, reasons


def add_test_item(username, user, field, value):
    """TEMPORARY helper: adds a value to one of the user's lists and saves."""
    if value not in user[field]:
        user[field].append(value)
        db.save_user(username, user)


def show(username):
    st.header("Food Scanner")

    user = db.get_user(username)

    # ---- TEMPORARY test buttons (delete once the Profile tab works) ----
    if st.button("Add test allergy: milk", key="t_allergy"):
        add_test_item(username, user, "allergies", "milk")
    if st.button("Add test medication: tetracycline", key="t_med"):
        add_test_item(username, user, "medications", "tetracycline")
    if st.button("Add test avoid food: sugar", key="t_avoid"):
        add_test_item(username, user, "avoid_foods", "sugar")
    if st.button("Clear test data", key="t_clear"):
        user["allergies"] = []
        user["medications"] = []
        user["avoid_foods"] = []
        db.save_user(username, user)

    st.write("Allergies:", user["allergies"])
    st.write("Medications:", user["medications"])
    st.write("Avoid foods:", user["avoid_foods"])
    # ---- end temporary block ----

    # Get a barcode: typed in, or read from a camera photo.
    code = st.text_input("Enter a barcode", key="barcode_input")
    with st.expander("Or scan with the camera"):
        photo = st.camera_input("Take a photo of the barcode", key="barcode_photo")

    # A typed code wins. Only use the photo if nothing was typed.
    if photo and not code:
        code = read_barcode_from_image(photo)
        if not code:
            st.error("Couldn't read a barcode from that photo. Try again or type it.")
            return

    if not code:
        st.caption("Try 3017620422003 (Nutella) or 737628064502 (Thai peanut noodles).")
        return

    code = str(code).strip()

    product = lookup_barcode(code)
    if product is None:
        st.error("Product not found. Check the barcode and try again.")
        return

    name = product.get("name", "Unknown product")
    st.subheader(name)
    with st.expander("Ingredients"):
        st.write(product.get("ingredients") or "No ingredients listed.")
        st.write("Allergens:", ", ".join(product.get("allergens") or []) or "none listed")

    level, reasons = check_food(product, user)

    if level == "avoid":
        st.error("AVOID")
    elif level == "caution":
        st.warning("CAUTION")
    else:
        st.success("SAFE: no conflicts found with your profile.")

    for reason in reasons:
        st.write("- " + reason)

    # Save this scan so the Profile tab can count the warnings.
    if st.button("Save to history", key="save_history"):
        user["scan_history"].append({
            "code": code,
            "name": name,
            "level": level,
            "reasons": reasons,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        })
        db.save_user(username, user)
        st.success("Saved to your scan history.")