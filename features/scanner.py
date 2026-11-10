"""
FOOD SCANNER  (owner: Pranav)

Scans are saved to user["scan_history"] as
{"code", "name", "level", "reasons", "time"}
level is always "safe", "caution" or "avoid" (the Profile tab reads it).
"""
import html
import io
import re
from datetime import datetime

import streamlit as st
from shared import db
from shared.barcode import lookup_barcode, read_barcode_from_image
from shared.interactions import FOOD_DRUG_INTERACTIONS

TYPE, CAMERA, UPLOAD = "Type barcode", "Use camera", "Upload photo"
EXAMPLES = [("🍫 Nutella", "3017620422003"), ("🥜 Thai peanut noodles", "737628064502")]

# ---------------------------------------------------------------- matching data
# Words that mean the same thing as an allergy / food. "milk" also catches whey, etc.
_MILK = ["milk", "dairy", "whey", "casein", "caseinate", "lactose", "buttermilk",
         "cheese", "yogurt", "yoghurt", "ghee", "lactoglobulin"]
_WHEAT = ["wheat", "gluten", "semolina", "spelt", "durum", "farina", "bulgur",
          "couscous", "seitan"]
_TREE_NUTS = ["nut", "almond", "hazelnut", "walnut", "cashew", "pecan",
              "pistachio", "macadamia", "brazil nut"]
_SOY = ["soy", "soya", "soybean", "soja", "edamame", "tofu", "miso", "tempeh"]
RELATED_TERMS = {
    "milk": _MILK, "dairy": _MILK, "lactose": _MILK,
    "egg": ["egg", "albumin", "albumen", "ovalbumin", "lysozyme", "mayonnaise", "meringue"],
    "peanut": ["peanut", "groundnut", "arachis"],
    "nut": _TREE_NUTS + ["peanut", "groundnut"],
    "tree nut": _TREE_NUTS,
    "soy": _SOY, "soybean": _SOY,
    "wheat": _WHEAT, "gluten": _WHEAT + ["barley", "rye"],
    "shellfish": ["shrimp", "prawn", "crab", "lobster", "crayfish", "crustacean",
                  "mollusc", "mollusk", "clam", "oyster", "mussel", "scallop", "squid"],
    "fish": ["fish", "anchovy", "anchovies", "cod", "salmon", "tuna", "tilapia",
             "haddock", "sardine"],
    "sesame": ["sesame", "tahini"],
    "sulfite": ["sulfite", "sulphite", "sulphur dioxide", "sulfur dioxide"],
}
LEVEL_RANK = {"safe": 0, "caution": 1, "avoid": 2}


def _singular(word):
    """'peanuts' -> 'peanut' (so plural and singular both work)."""
    word = word.strip().lower()
    if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
        word = word[:-1]
    return word


def term_variants(term):
    """Every word we should look for when the user lists `term`."""
    base = _singular(term)
    variants = [base, term.strip().lower()] + RELATED_TERMS.get(base, [])
    return list(dict.fromkeys(v for v in variants if v))


def contains_term(term, text):
    """Whole-word match, so 'egg' matches 'eggs' but NOT 'eggplant'."""
    pattern = r"(?<![a-z0-9])" + re.escape(term.lower()) + r"(?:e?s)?(?![a-z0-9])"
    return re.search(pattern, text) is not None


def find_match(term, text):
    """Returns the first matching word, or None."""
    for variant in term_variants(term):
        if contains_term(variant, text):
            return variant
    return None


def check_food(product, user):
    """Returns (level, reasons). level is "safe", "caution" or "avoid"."""
    level = "safe"
    reasons = []

    def raise_level(new):
        nonlocal level
        if LEVEL_RANK[new] > LEVEL_RANK[level]:   # never downgrade
            level = new

    def add(reason):
        if reason not in reasons:
            reasons.append(reason)

    ingredients = (product.get("ingredients") or "").lower()
    allergens = [a.lower() for a in (product.get("allergens") or [])]
    searchable = ingredients + ", " + ", ".join(allergens)

    # No data at all means we cannot promise anything.
    if not ingredients.strip() and not allergens:
        raise_level("caution")
        add("No ingredient or allergen information exists for this product, so it cannot be checked.")

    for allergy in user.get("allergies", []):
        hit = find_match(allergy, searchable)
        if hit:
            raise_level("avoid")
            if hit in (allergy.strip().lower(), _singular(allergy)):
                add(f"Contains {allergy}, which is on your allergy list.")
            else:
                add(f"Contains {hit}, a source of {allergy} (on your allergy list).")

    for medication in user.get("medications", []):
        for drug, pairs in FOOD_DRUG_INTERACTIONS.items():
            if contains_term(drug, medication.lower()):
                for food, message in pairs:
                    if find_match(food, searchable):
                        raise_level("caution")
                        add(f"{medication}: {message}")

    for food in user.get("avoid_foods", []):
        if find_match(food, searchable):
            raise_level("caution")
            add(f"Contains {food}, which is on your foods-to-avoid list.")

    return level, reasons


# ------------------------------------------------------------ barcode checking
def normalize_barcode(value):
    """Remove spaces and hyphens, keep leading zeroes."""
    return re.sub(r"[\s-]+", "", str(value or ""))


def checksum_ok(code):
    """Standard barcode check digit (works for 8, 12, 13 and 14 digits)."""
    digits = [int(c) for c in code]
    body, check = digits[:-1], digits[-1]
    total = sum(d * (3 if i % 2 == 0 else 1) for i, d in enumerate(reversed(body)))
    return (10 - total % 10) % 10 == check


def validate_barcode(code, skip_checksum=False):
    """Returns an error message, or None if the barcode looks valid."""
    if not code:
        return "Enter the barcode digits printed on the package."
    if not code.isascii() or not code.isdigit():
        return "Use digits only. Spaces and hyphens are removed automatically."
    if len(code) not in (8, 12, 13, 14):
        return f"This barcode has {len(code)} digits. Product barcodes have 8, 12, 13 or 14."
    if not skip_checksum and not checksum_ok(code):
        return ("These digits don't pass the barcode check, so one is probably mistyped. "
                "Re-check the number, or tick 'Skip typo check' for store-made codes.")
    return None


def read_code_from_photo(photo):
    """Tries the photo as-is, then sharpened, enlarged and rotated copies."""
    try:
        photo.seek(0)
        raw = photo.read()
    except Exception:
        return ""
    attempts = [raw]
    try:
        from PIL import Image, ImageOps
        base = ImageOps.exif_transpose(Image.open(io.BytesIO(raw))).convert("L")
        base = ImageOps.autocontrast(base)
        variants = [base]
        if base.width < 1000:
            variants.append(base.resize((base.width * 2, base.height * 2)))
        variants += [base.rotate(angle, expand=True) for angle in (90, 180, 270)]
        for image in variants:
            buffer = io.BytesIO()
            image.save(buffer, format="PNG")
            attempts.append(buffer.getvalue())
    except Exception:
        pass
    for data in attempts:
        try:
            code = normalize_barcode(read_barcode_from_image(io.BytesIO(data)))
        except Exception:
            continue
        if code:
            return code
    return ""


# ------------------------------------------------------------------- styling
CSS = """
<style>
.sb-hero{background:linear-gradient(135deg,#0f766e 0%,#14b8a6 55%,#34d399 100%);
 border-radius:22px;padding:28px 32px;color:#fff;margin-bottom:18px;
 box-shadow:0 12px 32px rgba(20,184,166,.28)}
.sb-hero .sb-eyebrow{font-size:12px;letter-spacing:3px;font-weight:700;opacity:.9}
.sb-hero h1{color:#fff !important;margin:6px 0 6px;padding:0;font-size:2rem;line-height:1.2}
.sb-hero p{margin:0;opacity:.92}
.sb-steps{margin-top:14px}
.sb-step{display:inline-block;background:rgba(255,255,255,.2);border-radius:999px;
 padding:4px 14px;margin:3px 8px 3px 0;font-size:.85rem;font-weight:600}
.sb-label{font-size:12px;letter-spacing:2px;font-weight:700;opacity:.6;margin:14px 0 6px}
.sb-verdict{border-radius:16px;padding:18px 22px;margin:12px 0;border:1px solid;
 border-left-width:9px}
.sb-chip{display:inline-block;padding:4px 13px;margin:3px 6px 3px 0;border-radius:999px;
 font-size:.85rem;background:rgba(128,128,128,.16)}
.sb-chip-bad{background:rgba(220,38,38,.18);color:#ef4444;font-weight:700;
 border:1px solid rgba(220,38,38,.55)}
</style>
"""

VERDICTS = {
    "avoid": ("#dc2626", "rgba(220,38,38,.10)", "🚫", "Avoid this product",
              "Something in it matches your profile."),
    "caution": ("#d97706", "rgba(245,158,11,.12)", "⚠️", "Check before eating",
                "Something here needs a second look."),
    "safe": ("#16a34a", "rgba(34,197,94,.10)", "✅", "No conflicts found",
             "Nothing in the available product data matches your profile."),
}


def esc(value):
    """Product data comes from the internet, so escape it before putting it in HTML."""
    return html.escape(str(value))


def show_result(level, reasons):
    """The big colored verdict card. Edit the wording in VERDICTS above."""
    color, tint, icon, title, subtitle = VERDICTS[level]
    items = "".join(f"<li>{esc(r)}</li>" for r in reasons)
    block = f"<ul style='margin:10px 0 0 18px;padding:0'>{items}</ul>" if reasons else ""
    st.markdown(
        f"<div class='sb-verdict' style='background:{tint};border-color:{color}'>"
        f"<div style='font-size:1.4rem;font-weight:800;color:{color}'>{icon} {title}</div>"
        f"<div style='opacity:.85;margin-top:2px'>{subtitle}</div>{block}</div>",
        unsafe_allow_html=True,
    )


def allergen_chips(allergens, user):
    """Allergen tags; the ones matching your allergies turn red."""
    if not allergens:
        return "<span class='sb-chip'>No allergens listed</span>"
    chips = []
    for allergen in allergens:
        bad = any(find_match(a, allergen.lower()) for a in user.get("allergies", []))
        css = "sb-chip sb-chip-bad" if bad else "sb-chip"
        chips.append(f"<span class='{css}'>{'⚠️ ' if bad else ''}{esc(allergen)}</span>")
    return "".join(chips)


# ---------------------------------------------------------------- page pieces
def show_hero():
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown(
        "<div class='sb-hero'><div class='sb-eyebrow'>SAFEBITE / FOOD SCANNER</div>"
        "<h1>A little clarity before your next bite.</h1>"
        "<p>Scan a package, see how it matches your profile, keep what matters.</p>"
        "<div class='sb-steps'><span class='sb-step'>1 · Find product</span>"
        "<span class='sb-step'>2 · Review result</span>"
        "<span class='sb-step'>3 · Save to history</span></div></div>",
        unsafe_allow_html=True,
    )


def show_profile_summary(user):
    fields = (("allergies", "🥜", "allergies"), ("medications", "💊", "medications"),
              ("avoid_foods", "🚫", "foods to avoid"))
    chips = "".join(
        f"<span class='sb-chip'>{icon} {len(user.get(field, []))} {label}</span>"
        for field, icon, label in fields
    )
    st.markdown(f"<div class='sb-label'>YOUR ACTIVE PROFILE</div>{chips}", unsafe_allow_html=True)
    with st.expander("See what's being checked"):
        for field, icon, label in fields:
            st.write(f"**{label.capitalize()}:** " + (", ".join(user.get(field, [])) or "None added"))
        st.caption("Change these in the Profile tab. Results always use your latest saved profile.")
    if not any(user.get(field) for field, _, _ in fields):
        st.info("Your profile is empty, so nothing can be flagged yet. Add allergies, "
                "medications or foods to avoid in the Profile tab.")


def load_example(username, code):
    """Button callback: fill in a barcode and run the lookup on the next rerun."""
    st.session_state[f"scanner_mode_{username}"] = TYPE
    st.session_state[f"barcode_input_{username}"] = code
    st.session_state[f"scanner_autorun_{username}"] = code


def show_barcode_form(username):
    st.markdown("<div class='sb-label'>01 / FIND YOUR PRODUCT</div>", unsafe_allow_html=True)
    with st.container(border=True):
        mode = st.radio("How do you want to enter the barcode?", [TYPE, CAMERA, UPLOAD],
                        horizontal=True, key=f"scanner_mode_{username}")
        code, photo, skip = "", None, False
        with st.form(f"scanner_lookup_{username}_{mode}", border=False):
            if mode == TYPE:
                code = st.text_input(
                    "Barcode number", key=f"barcode_input_{username}",
                    placeholder="e.g. 3017620422003",
                    help="Spaces and hyphens are removed. Leading zeroes are kept.")
                skip = st.checkbox("Skip typo check (only for store-made codes)",
                                   key=f"scanner_skip_{username}")
            elif mode == CAMERA:
                st.caption("Bright, even light. Keep every bar and the white margins in focus.")
                photo = st.camera_input("Photograph the barcode", key=f"barcode_photo_{username}")
            else:
                st.caption("Upload a close-up where every bar is visible.")
                photo = st.file_uploader("Barcode photo", type=["png", "jpg", "jpeg"],
                                         key=f"barcode_upload_{username}")
            submitted = st.form_submit_button("🔍 Check this product", type="primary")

        st.caption("Or try an example:")
        columns = st.columns(len(EXAMPLES))
        for column, (label, example) in zip(columns, EXAMPLES):
            column.button(label, key=f"example_{username}_{example}",
                          on_click=load_example, args=(username, example))
    return submitted, mode, code, photo, skip


def show_product(username, user, code, product):
    level, reasons = check_food(product, user)
    st.markdown("<div class='sb-label'>02 / YOUR RESULT</div>", unsafe_allow_html=True)
    with st.container(border=True):
        if product.get("image_url"):
            picture, details = st.columns([1, 3])
            picture.image(product["image_url"], width=140)
        else:
            details = st.container()
        with details:
            st.subheader(product.get("name") or "Unknown product")
            st.caption(f"Barcode {code} · checked against your current profile")

        show_result(level, reasons)

        st.markdown("<div class='sb-label'>LISTED ALLERGENS</div>", unsafe_allow_html=True)
        st.markdown(allergen_chips(product.get("allergens") or [], user), unsafe_allow_html=True)

        calories = product.get("calories_per_100g")
        per_serving = product.get("calories_per_serving")
        c1, c2, c3 = st.columns(3)
        c1.metric("Calories / 100 g", f"{round(calories)} kcal" if isinstance(calories, (int, float)) else "n/a")
        c2.metric("Calories / serving", f"{round(per_serving)} kcal" if isinstance(per_serving, (int, float)) else "n/a")
        c3.metric("Serving size", product.get("serving_size") or "n/a")

        with st.expander("📝 Read full ingredients"):
            st.write(product.get("ingredients") or "No ingredients listed.")
        save_scan(username, user, code, product, level, reasons)


def save_scan(username, user, code, product, level, reasons):
    history = user.setdefault("scan_history", [])
    already = any(h.get("code") == code and h.get("level") == level
                  and h.get("reasons") == reasons for h in history)
    if already:
        st.button("✔ Saved to history", key=f"save_history_{username}", disabled=True)
    elif st.button("💾 Save to scan history", key=f"save_history_{username}", type="primary"):
        history.append({
            "code": code, "name": product.get("name") or "Unknown product",
            "level": level, "reasons": reasons,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        })
        db.save_user(username, user)
        st.rerun()


def show_recent_scans(username, user):
    recent = [h for h in user.get("scan_history", []) if h.get("code")][-5:][::-1]
    if not recent:
        return
    dots = {"safe": "🟢", "caution": "🟡", "avoid": "🔴"}
    with st.expander(f"🕘 Recent scans ({len(recent)})"):
        for i, item in enumerate(recent):
            left, right = st.columns([4, 1])
            left.write(f"{dots.get(item.get('level'), '⚪')} **{item.get('name', 'Unknown')}** "
                       f"· {item.get('time', '')}")
            right.button("Check again", key=f"recheck_{username}_{i}",
                         on_click=load_example, args=(username, item["code"]))


# ------------------------------------------------------------- developer tools
SELF_TESTS = [
    ("Milk allergy, whey in food", {"allergies": ["milk"]}, "oats, whey", [], "avoid"),
    ("Plural allergy name", {"allergies": ["peanuts"]}, "roasted peanut butter", [], "avoid"),
    ("Egg is not eggplant", {"allergies": ["egg"]}, "eggplant, salt", [], "safe"),
    ("Medication interaction", {"medications": ["Warfarin 5mg"]}, "kale, salt", [], "caution"),
    ("Food to avoid", {"avoid_foods": ["sugar"]}, "oats, sugar", [], "caution"),
    ("Allergy beats caution", {"allergies": ["milk"], "avoid_foods": ["sugar"]},
     "milk, sugar", ["milk"], "avoid"),
    ("No data is never safe", {"allergies": ["milk"]}, "", [], "caution"),
    ("Nothing matches", {"allergies": ["milk"]}, "rice, water, salt", [], "safe"),
]


def comma_list(value):
    return list(dict.fromkeys(p.strip().lower() for p in value.split(",") if p.strip()))


def show_dev_tools(username):
    with st.container(border=True):
        st.subheader("🛠 Developer tools")
        st.caption("Offline tests. Nothing here changes your saved profile or history.")
        if st.button("Run all self-tests", key=f"scanner_selftest_{username}"):
            for name, profile, ingredients, allergens, expected in SELF_TESTS:
                full = {"allergies": [], "medications": [], "avoid_foods": [], **profile}
                level, _ = check_food({"ingredients": ingredients, "allergens": allergens}, full)
                st.write(("✅" if level == expected else "❌") + f" {name}: expected {expected}, got {level}")
            for code, ok in (("3017620422003", True), ("737628064502", True), ("3017620422004", False)):
                st.write(("✅" if checksum_ok(code) == ok else "❌") + f" barcode check {code}")
        with st.form(f"scanner_playground_{username}"):
            cols = st.columns(3)
            allergies = cols[0].text_input("Allergies")
            meds = cols[1].text_input("Medications")
            avoid = cols[2].text_input("Foods to avoid")
            ingredients = st.text_area("Ingredients")
            allergens = st.text_input("Listed allergens")
            run = st.form_submit_button("Run custom test")
        if run:
            profile = {"allergies": comma_list(allergies), "medications": comma_list(meds),
                       "avoid_foods": comma_list(avoid)}
            level, reasons = check_food({"ingredients": ingredients.lower(),
                                         "allergens": comma_list(allergens)}, profile)
            show_result(level, reasons)


# ----------------------------------------------------------------- main page
def show(username):
    show_hero()
    user = db.get_user(username)
    show_profile_summary(user)

    submitted, mode, code, photo, skip = show_barcode_form(username)

    # Example / "Check again" buttons ask for an automatic lookup.
    auto = st.session_state.pop(f"scanner_autorun_{username}", None)
    if auto:
        submitted, mode, code, photo, skip = True, TYPE, auto, None, True

    result_key = f"scanner_product_{username}"
    if submitted:
        st.session_state.pop(result_key, None)   # never leave an old product on screen
        error = None
        if mode != TYPE:
            if photo is None:
                error = "Take a photo first." if mode == CAMERA else "Choose a barcode photo first."
            else:
                with st.spinner("Reading the barcode in your photo..."):
                    code = read_code_from_photo(photo)
                if not code:
                    error = ("No readable barcode found. Try a sharper close-up, or use Type barcode. "
                             "Photo scanning also needs the barcode reader (pyzbar) installed.")
        if error is None:
            code = normalize_barcode(code)
            error = validate_barcode(code, skip_checksum=(skip and mode == TYPE))
        if error:
            st.warning(error)
        else:
            with st.spinner("Finding your product and checking your profile..."):
                product = lookup_barcode(code)
            if product is None:
                st.warning("We couldn't retrieve this product. Check the digits, or the product may "
                           "be missing from the database or the service may be down.")
            else:
                st.session_state[result_key] = (code, product)

    result = st.session_state.get(result_key)
    if result:
        show_product(username, user, result[0], result[1])
    elif not submitted:
        with st.container(border=True):
            st.markdown("**Your result will appear here**")
            st.caption("Check a barcode to see profile matches, allergens and ingredients together.")

    show_recent_scans(username, user)
    st.caption("Product data comes from Open Food Facts and can be incomplete or out of date. "
               "SafeBite uses a keyword check and may miss things. Always read the package label.")
    st.divider()
    if st.toggle("Developer mode", value=False, key=f"scanner_dev_{username}"):
        show_dev_tools(username)