"""
PROFILE + ALERTS

Manage profile details, allergies, medications, and foods to avoid. The scanner
reads the lowercase allergy and medication names saved here.
"""
from datetime import date

import streamlit as st
from shared import db


COMMON_ALLERGIES = ["peanuts", "milk", "eggs", "soy", "wheat", "shellfish"]
SEVERITY = ["Mild", "Moderate", "Severe"]
BLOOD_TYPES = ["Not set", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]


def _render_profile_details(username, user):
    details = user.get("profile_details", {})
    st.subheader("Personal and health details")

    with st.form("profile_details_form"):
        name = st.text_input("Full name", value=details.get("name", ""))
        sex = st.selectbox(
            "Sex",
            ["Not set", "Male", "Female", "Other"],
            index=["Not set", "Male", "Female", "Other"].index(
                details.get("sex", "Not set")
                if details.get("sex", "Not set") in ["Not set", "Male", "Female", "Other"]
                else "Not set"
            ),
        )
        dob = st.text_input(
            "Date of birth (YYYY-MM-DD)", value=details.get("dob", "")
        )
        height_cm = st.number_input(
            "Height (cm)", min_value=0, max_value=300,
            value=int(details.get("height_cm") or 0),
        )
        weight_kg = st.number_input(
            "Weight (kg)", min_value=0, max_value=500,
            value=int(details.get("weight_kg") or 0),
        )
        blood = st.selectbox(
            "Blood type",
            BLOOD_TYPES,
            index=BLOOD_TYPES.index(
                details.get("blood", "Not set")
                if details.get("blood", "Not set") in BLOOD_TYPES
                else "Not set"
            ),
        )
        conditions = st.text_input(
            "Conditions", value=details.get("conditions", "")
        )
        diet = st.text_input(
            "Dietary needs", value=details.get("diet", "")
        )
        submitted = st.form_submit_button("Save details")

    if submitted:
        dob = dob.strip()
        if dob:
            try:
                parsed_dob = date.fromisoformat(dob)
            except ValueError:
                st.error("Enter a valid date in YYYY-MM-DD format.")
                return
            if parsed_dob > date.today():
                st.error("Date of birth cannot be in the future.")
                return

        user["profile_details"] = {
            "name": name.strip(),
            "sex": sex,
            "dob": dob,
            "height_cm": int(height_cm) or "",
            "weight_kg": int(weight_kg) or "",
            "blood": blood,
            "conditions": conditions.strip(),
            "diet": diet.strip(),
        }
        db.save_user(username, user)
        st.rerun()


def _render_list(username, user, label, field, details_field=None):
    st.subheader(label)
    items = user.get(field, [])
    details = user.setdefault(details_field, {}) if details_field else {}
    item_label = {
        "Allergies": "Allergy",
        "Medications": "Medication",
        "Foods to avoid": "Food to avoid",
    }.get(label, label)

    with st.form(f"profile_add_{field}"):
        value = st.text_input(item_label)
        severity = None
        reaction = None
        dose = None
        frequency = None
        if field == "allergies":
            severity = st.selectbox("Severity", SEVERITY, index=1)
            reaction = st.text_input("Reaction")
        elif field == "medications":
            dose = st.text_input("Dose")
            frequency = st.text_input("How often")
        submitted = st.form_submit_button("Add")

    if submitted:
        item = value.strip().lower()
        if not item:
            st.error("Enter a value first.")
        elif item in items:
            st.info(f"{item.capitalize()} is already on your list.")
        else:
            items.append(item)
            if details_field and field == "allergies":
                details[item] = {
                    "severity": severity,
                    "reaction": reaction.strip(),
                }
            elif details_field and field == "medications":
                details[item] = {
                    "dose": dose.strip(),
                    "frequency": frequency.strip(),
                }
            db.save_user(username, user)
            st.rerun()

    for index, item in enumerate(items):
        name, remove = st.columns([5, 1])
        name.write(item)
        item_details = details.get(item, {})
        if field == "allergies":
            description = " · ".join(
                value for value in (
                    item_details.get("severity"),
                    item_details.get("reaction"),
                ) if value
            )
        elif field == "medications":
            description = " · ".join(
                value for value in (
                    item_details.get("dose"),
                    item_details.get("frequency"),
                ) if value
            )
        else:
            description = ""
        if description:
            name.caption(description)
        if remove.button("Remove", key=f"profile_remove_{field}_{index}"):
            items.pop(index)
            if details_field:
                details.pop(item, None)
            db.save_user(username, user)
            st.rerun()

    if not items:
        st.caption(f"No {label.lower()} added yet.")


def show(username):
    st.header("My Profile")
    user = db.get_user(username)

    alerts = [
        scan for scan in user.get("scan_history", [])
        if str(scan.get("level", "")).lower() != "safe"
    ]
    if alerts:
        st.warning(f"You have {len(alerts)} food scan alert(s) to review.")
        for scan in alerts:
            name = scan.get("name", "Unknown food")
            level = scan.get("level", "unknown")
            st.write(f"- **{name}** — {level}")
            for reason in scan.get("reasons", []):
                st.caption(reason)
    else:
        st.success("No food scan alerts.")

    _render_profile_details(username, user)

    st.subheader("Common allergies")
    common = st.selectbox(
        "Choose a common allergy",
        ["Choose one..."] + COMMON_ALLERGIES,
        key="profile_common_allergy",
    )
    if st.button("Add common allergy", key="profile_add_common_allergy"):
        if common == "Choose one...":
            st.error("Choose an allergy first.")
        elif common in user["allergies"]:
            st.info(f"{common.capitalize()} is already on your allergy list.")
        else:
            user["allergies"].append(common)
            db.save_user(username, user)
            st.rerun()

    _render_list(
        username, user, "Allergies", "allergies", "allergy_details"
    )
    _render_list(
        username, user, "Medications", "medications", "medication_details"
    )
    _render_list(username, user, "Foods to avoid", "avoid_foods")

    st.subheader("Daily calories")
    with st.form("profile_calorie_goal"):
        goal = st.number_input(
            "Calories per day",
            min_value=800,
            max_value=6000,
            value=max(800, min(6000, int(user.get("calorie_goal", 2000)))),
            step=100,
        )
        save_goal = st.form_submit_button("Save calorie goal")
    if save_goal:
        user["calorie_goal"] = int(goal)
        db.save_user(username, user)
        st.rerun()
