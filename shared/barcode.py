"""
Shared barcode tools. Used by the Food Scanner AND the Calorie Tracker.

lookup_barcode("737628064502") -> product info from Open Food Facts
read_barcode_from_image(image) -> the barcode number found in a photo
"""
import requests

API_URL = "https://world.openfoodfacts.org/api/v2/product/{}.json"


def lookup_barcode(code):
    """
    Looks up a barcode. Returns a dict like:
    {
        "name": "Peanut Butter",
        "ingredients": "roasted peanuts, sugar, salt",
        "allergens": ["peanuts"],
        "calories_per_100g": 588,
        "calories_per_serving": 190,   (can be None)
        "serving_size": "32 g",        (can be None)
    }
    Returns None if the product isn't found or the request fails.
    """
    code = code.strip()
    if code == "":
        return None

    try:
        response = requests.get(
            API_URL.format(code),
            headers={"User-Agent": "SafeBite-StudentProject/1.0"},
            timeout=10,
        )
        data = response.json()
    except Exception:
        return None

    if data.get("status") != 1:
        return None

    product = data["product"]
    nutrients = product.get("nutriments", {})

    # Allergen tags look like "en:peanuts", so remove the "en:" part
    allergens = []
    tags = product.get("allergens_tags", [])
    for i in range(len(tags)):
        tag = tags[i]
        if ":" in tag:
            tag = tag.split(":")[1]
        allergens.append(tag.replace("-", " "))

    return {
        "name": product.get("product_name") or "Unknown product",
        "ingredients": (product.get("ingredients_text") or "").lower(),
        "allergens": allergens,
        "calories_per_100g": nutrients.get("energy-kcal_100g"),
        "calories_per_serving": nutrients.get("energy-kcal_serving"),
        "serving_size": product.get("serving_size"),
    }


def read_barcode_from_image(image):
    """
    Takes a photo (from st.camera_input or st.file_uploader) and returns the
    barcode number as a string, or None if no barcode was found.
    Needs pyzbar + the zbar system library (see README).
    """
    try:
        from PIL import Image
        from pyzbar.pyzbar import decode
    except Exception:
        return None

    picture = Image.open(image)
    results = decode(picture)
    if len(results) == 0:
        return None
    return results[0].data.decode("utf-8")
