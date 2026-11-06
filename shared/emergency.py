"""
Emergency keyword rules. The chatbot checks every message against these
BEFORE doing anything else. If one matches, show "Call 911".
"""

EMERGENCY_PHRASES = [
    "can't breathe", "cant breathe", "cannot breathe", "trouble breathing",
    "difficulty breathing", "throat swelling", "throat is swelling",
    "throat closing", "tongue swelling", "lips swelling", "anaphylaxis",
    "chest pain", "stiff neck", "confusion", "seizure", "fainted",
    "passed out", "unconscious", "blood", "worst headache", "suicidal",
]


def find_emergencies(message):
    """Returns the list of emergency phrases found in the message (empty if none)."""
    text = message.lower().replace("’", "'")
    return [phrase for phrase in EMERGENCY_PHRASES if phrase in text]


def is_emergency(message):
    return len(find_emergencies(message)) > 0
