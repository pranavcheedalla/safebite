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
    """Present the match result without implying a medical guarantee."""
    if level == "avoid":
        st.error("Avoid this product - an allergy match was found.", icon="\U0001f6ab")
    elif level == "caution":
        st.warning("Review before eating - a potential conflict was found.", icon="\u26a0\ufe0f")
    else:
        st.success("No conflicts found in the available product information.", icon="\u2705")
    for reason in reasons:
        st.markdown(f"- {reason}")
    st.caption("Matches use a limited keyword check. Always read the package label; missing data or an unmatched ingredient does not mean a food is safe.")


def allergen_line(allergens):
    return "Allergens: " + ", ".join(allergens) if allergens else "No allergens listed in the product data."


TEST_SCENARIOS = {
    "Allergy match": {
        "profile": {"allergies": ["milk"], "medications": [], "avoid_foods": []},
        "ingredients": "oats, whey, honey", "allergens": ["milk"], "expected": "avoid",
        "description": "Checks milk and its related ingredient whey.",
    },
    "Medication interaction": {
        "profile": {"allergies": [], "medications": ["tetracycline"], "avoid_foods": []},
        "ingredients": "milk, cocoa", "allergens": ["milk"], "expected": "caution",
        "description": "Checks a food against a medication in the demo interaction list.",
    },
    "Food preference": {
        "profile": {"allergies": [], "medications": [], "avoid_foods": ["sugar"]},
        "ingredients": "oats, sugar, salt", "allergens": [], "expected": "caution",
        "description": "Checks a food on the test profile's avoidance list.",
    },
    "Multiple conflicts": {
        "profile": {"allergies": ["milk"], "medications": ["tetracycline"], "avoid_foods": ["sugar"]},
        "ingredients": "milk, sugar, cocoa", "allergens": ["milk"], "expected": "avoid",
        "description": "An allergy takes priority; all three explanations should still appear.",
    },
    "No matching conflicts": {
        "profile": {"allergies": ["milk"], "medications": [], "avoid_foods": ["sugar"]},
        "ingredients": "rice, water, salt", "allergens": [], "expected": "safe",
        "description": "Checks the no-match result with a populated test profile.",
    },
}


def _comma_list(value):
    """Normalize and deduplicate comma-separated test values."""
    return list(dict.fromkeys(part.strip().lower() for part in value.split(",") if part.strip()))


def show_test_tools(username):
    with st.expander("\U0001f9ea Developer test playground", expanded=False):
        st.caption("Try the scanner logic offline. Test values stay in this session and never change your profile or scan history.")
        scenario_name = st.selectbox("Start with a scenario", list(TEST_SCENARIOS), key=f"scanner_scenario_{username}")
        scenario = TEST_SCENARIOS[scenario_name]
        st.write(scenario["description"])
        prefix = f"scanner_test_{username}_{scenario_name}"
        with st.form(prefix):
            st.markdown("**1 - Test profile**")
            columns = st.columns(3)
            values = {}
            for column, field, label in zip(columns, ("allergies", "medications", "avoid_foods"), ("Allergies", "Medications", "Foods to avoid")):
                values[field] = _comma_list(column.text_input(label, value=", ".join(scenario["profile"][field]), help="Separate multiple entries with commas.", key=f"{prefix}_{field}"))
            st.markdown("**2 - Test product**")
            ingredients = st.text_area("Ingredients", value=scenario["ingredients"], key=f"{prefix}_ingredients")
            allergens = st.text_input("Listed allergens", value=", ".join(scenario["allergens"]), key=f"{prefix}_allergens", help="Separate multiple allergens with commas.")
            run = st.form_submit_button("Run test", type="primary")
        if run:
            product = {"ingredients": ingredients.lower(), "allergens": _comma_list(allergens)}
            level, reasons = check_food(product, values)
            st.markdown("**3 - Test result**")
            show_result(level, reasons)
            unchanged = values == scenario["profile"] and product == {"ingredients": scenario["ingredients"], "allergens": scenario["allergens"]}
            if unchanged:
                if level == scenario["expected"]:
                    st.success(f"Scenario passed: expected {scenario['expected']}, received {level}.")
                else:
                    st.error(f"Scenario failed: expected {scenario['expected']}, received {level}.")
            else:
                st.caption("Custom inputs: the preset's expected result does not apply.")
            with st.expander("Inspect test inputs and output"):
                st.json({"profile": values, "product": product, "level": level, "reasons": reasons})
        with st.expander("Supported checks and limitations"):
            st.write("Allergies and food preferences use substring matching. Milk also checks whey, casein, and lactose. Medication names must match a supported entry exactly.")
            st.write("Supported medications: " + ", ".join(sorted(FOOD_DRUG_INTERACTIONS)))
            st.caption("This playground validates demo behavior, not medical accuracy or comprehensive allergen coverage.")


def show(username):
    st.header("\U0001f50e Food scanner")
    st.caption("Check a product against your allergies, medications, and food preferences.")
    user = db.get_user(username)

    with st.container(border=True):
        st.markdown("**Your scanning profile**")
        columns = st.columns(3)
        for column, field, label in zip(columns, ("allergies", "medications", "avoid_foods"), ("Allergies", "Medications", "Foods to avoid")):
            column.metric(label, len(user.get(field, [])))
            column.caption(", ".join(user.get(field, [])) or "None added")
        st.caption("Update these entries in the Profile tab.")

    st.subheader("Find a product")
    code = st.text_input("Enter a barcode", key=f"barcode_input_{username}", placeholder="e.g. 3017620422003", help="Type the digits printed below the barcode.")
    with st.expander("\U0001f4f7 Scan with your camera"):
        st.caption("Use good lighting and keep the entire barcode in focus. Leave the typed barcode empty to use a photo.")
        photo = st.camera_input("Take a photo of the barcode", key=f"barcode_photo_{username}")

    if photo and not code.strip():
        try:
            code = read_barcode_from_image(photo)
        except Exception:
            code = None
        if not code:
            st.warning("Couldn't read that barcode. Retake the photo or enter the digits above.")
    code = str(code or "").strip()
    if not code:
        st.info("Enter a barcode or take a photo to get started. Example: 3017620422003 (Nutella).")
    elif not code.isascii() or not code.isdigit() or len(code) not in (8, 12, 13, 14):
        st.warning("Enter a barcode with 8, 12, 13, or 14 digits, without spaces or dashes.")
    else:
        # Reuse the lookup during test-form and save-button reruns.
        cache_key = f"scanner_product_{username}"
        cached = st.session_state.get(cache_key)
        if cached is None or cached[0] != code:
            with st.spinner("Looking up product details..."):
                product = lookup_barcode(code)
            st.session_state[cache_key] = (code, product)
        else:
            product = cached[1]
        if product is None:
            st.warning("Product details are unavailable. Check the barcode or try again; the lookup service may be unreachable.")
            if st.button("Retry lookup", key=f"scanner_retry_{username}"):
                del st.session_state[cache_key]
                st.rerun()
        else:
            st.divider()
            name = product.get("name") or "Unknown product"
            with st.container(border=True):
                if product.get("image_url"):
                    picture, details = st.columns([1, 2])
                    picture.image(product["image_url"], width=160)
                else:
                    details = st.container()
                with details:
                    st.subheader(name)
                    st.caption(f"Barcode - {code}")
                    st.write(allergen_line(product.get("allergens") or []))
                    calories = product.get("calories_per_100g")
                    if calories is not None:
                        st.metric("Energy per 100 g", f"{calories} kcal")
                level, reasons = check_food(product, user)
                show_result(level, reasons)
                if not product.get("ingredients"):
                    st.warning("Ingredient information is missing. Review the package before making a decision.")
                with st.expander("\U0001f4cb Full ingredients"):
                    st.write(product.get("ingredients") or "No ingredients listed.")
                if st.button("Save to scan history", key=f"save_history_{username}", type="primary"):
                    user.setdefault("scan_history", []).append({
                        "code": code, "name": name, "level": level, "reasons": reasons,
                        "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    })
                    db.save_user(username, user)
                    st.success("Saved to your scan history.")
    st.divider()
    show_test_tools(username)
