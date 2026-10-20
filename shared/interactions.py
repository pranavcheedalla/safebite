"""
Food and medication interactions to check against.

Format: medication keyword -> list of (food keyword, reason).
Matching is simple: if the user's medication contains the medication keyword
and the food's ingredients contain the food keyword, we warn them.

This list is for a demo, NOT medical advice. Add more as a team.
"""

FOOD_DRUG_INTERACTIONS = {
    "atorvastatin": [("grapefruit", "Grapefruit can raise statin levels in the blood.")],
    "simvastatin": [("grapefruit", "Grapefruit can raise statin levels in the blood.")],
    "warfarin": [
        ("kale", "High vitamin K foods can make warfarin less effective."),
        ("spinach", "High vitamin K foods can make warfarin less effective."),
    ],
    "levothyroxine": [("soy", "Soy can reduce how well thyroid medication is absorbed.")],
    "tetracycline": [("milk", "Dairy can block absorption of this antibiotic.")],
    "lisinopril": [("potassium chloride", "Salt substitutes high in potassium can raise potassium too much.")],
}
