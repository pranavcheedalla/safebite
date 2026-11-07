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

RELATED_TERMS = {
    "milk": ["whey", "casein", "lactose"],
}


def check_food(product, user):
    """Returns (level, reasons). level is "safe", "caution" or "avoid"."""
    level = "safe"
    reasons = []

    ingredients_text = product.get("ingredients") or ""
    allergens_list = product.get("allergens") or []
    searchable = (ingredients_text + " " + " ".join(allergens_list)).lower()

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
                break

    for medication in user.get("medications", []):
        for food, message in FOOD_DRUG_INTERACTIONS.get(medication.lower(), []):
            if food in searchable:
                if level != "avoid":
                    level = "caution"
                reasons.append(f"{medication}: {message}")

    for food in user.get("avoid_foods", []):
        if food.lower() in searchable:
            if level != "avoid":
                level = "caution"
            reasons.append(f"Contains {food}, which is on your foods-to-avoid list.")

    return level, reasons


def show_result(level, reasons):
    """Task 1: shows the colored result box. Edit the three messages here."""
    if level == "avoid":
        st.error("🔴 Do NOT eat this. It conflicts with your profile.")
    elif level == "caution":
        st.warning("🟡 Be careful. Check the notes below.")
    else:
        st.success("🟢 Safe to eat!")

    for reason in reasons:
        st.write("• " + reason)


def allergen_line(allergens):
    """Task 2: turns ["milk", "nuts"] into "Allergens: milk, nuts"."""
    if len(allergens) == 0:
        return "No allergens listed."

    text = ""
    for i in range(len(allergens)):       # i = 0, 1, 2, ...
        text = text + allergens[i]
        if i < len(allergens) - 1:        # no comma after the last one
            text = text + ", "
    return "Allergens: " + text


def add_test_item(username, user, field, value):
    """TEMPORARY helper: adds a value to one of the user's lists and saves."""
    if value not in user[field]:
        user[field].append(value)
        db.save_user(username, user)


def show(username):
    st.header("🔍 SafeBite Food Scanner")   # Task 1: new title
    st.caption("Scan or type a barcode to check a food against your profile.")

    user = db.get_user(username)

    # ---- TEMPORARY test tools (delete once the Profile tab works) ----
    with st.expander("🛠 Developer test tools"):
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

    code = st.text_input("Enter a barcode", key="barcode_input",
                         placeholder="e.g. 3017620422003")
    with st.expander("📷 Or scan with the camera"):
        photo = st.camera_input("Take a photo of the barcode", key="barcode_photo")

    if photo and not code:
        code = read_barcode_from_image(photo)
        if not code:
            st.error("Couldn't read a barcode from that photo. Try again or type it.")
            return

    if not code:
        st.info("Try 3017620422003 (Nutella) or 737628064502 (Thai peanut noodles).")
        return

    code = str(code).strip()

    product = lookup_barcode(code)
    if product is None:
        st.error("Product not found. Check the barcode and try again.")
        return

    name = product.get("name", "Unknown product")
    allergens = product.get("allergens") or []
    image_url = product.get("image_url")      # Task 3: None until barcode.py is edited
    calories = product.get("calories_per_100g")

    st.divider()

    # Picture on the left, details on the right.
    if image_url:
        pic_col, info_col = st.columns([1, 2])
        with pic_col:
            st.image(image_url, width=200)
    else:
        info_col = st.container()

    with info_col:
        st.subheader(name)                          # Task 2
        st.write(allergen_line(allergens))
        if calories is not None:
            st.metric("Calories per 100g", f"{calories} kcal")

    with st.expander("📝 Full ingredients"):
        st.write(product.get("ingredients") or "No ingredients listed.")

    st.divider()

    level, reasons = check_food(product, user)
    show_result(level, reasons)

    if st.button("💾 Save to history", key="save_history"):
        user["scan_history"].append({
            "code": code,
            "name": name,
            "level": level,
            "reasons": reasons,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        })
        db.save_user(username, user)
        st.success("Saved to your scan history.")