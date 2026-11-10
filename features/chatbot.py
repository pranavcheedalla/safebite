"""
SYMPTOM CHECKER  (owner: Tharoon)

A small Naive Bayes chatbot: the user describes symptoms in plain English and
it estimates how likely each condition is, as a percentage.

IMPORTANT: The numbers in CONDITIONS are rough, hand-written teaching values,
NOT real clinical data. This is a class-project demo, not medical advice.

How it works:
- Every message is checked by shared/emergency.py first.
- Symptoms are remembered across messages (st.session_state), including ones
  the user says they DON'T have ("no cough").
- Naive Bayes: P(condition | symptoms) is proportional to
  P(condition) * product of P(symptom | condition).

Next steps (see TASKS.md): add a real AI reply with the anthropic package.
"""
import re

import streamlit as st
from shared import db
from shared.emergency import find_emergencies

# ---------------------------------------------------------------------------
# 1. KNOWLEDGE BASE
#    Each condition: (prior, {symptom: P(symptom | condition)})
# ---------------------------------------------------------------------------
CONDITIONS = {
    "Common cold": (0.30, {
        "runny nose": 0.90, "sore throat": 0.70, "cough": 0.70, "sneezing": 0.80,
        "fatigue": 0.40, "headache": 0.30, "fever": 0.15, "body aches": 0.25,
    }),
    "Influenza (flu)": (0.12, {
        "fever": 0.85, "body aches": 0.80, "fatigue": 0.85, "cough": 0.80,
        "headache": 0.65, "chills": 0.70, "sore throat": 0.45, "runny nose": 0.40,
    }),
    "COVID-19": (0.10, {
        "fever": 0.60, "cough": 0.70, "fatigue": 0.70, "loss of taste or smell": 0.50,
        "sore throat": 0.45, "headache": 0.50, "body aches": 0.50,
        "shortness of breath": 0.25, "runny nose": 0.30,
    }),
    "Strep throat": (0.05, {
        "sore throat": 0.95, "fever": 0.60, "headache": 0.40, "nausea": 0.25,
        "rash": 0.10, "cough": 0.10, "runny nose": 0.10,
    }),
    "Stomach bug / food poisoning": (0.12, {
        "nausea": 0.85, "vomiting": 0.75, "diarrhea": 0.80, "abdominal pain": 0.75,
        "fever": 0.35, "fatigue": 0.50, "chills": 0.30, "headache": 0.25,
    }),
    "Seasonal allergies": (0.15, {
        "sneezing": 0.90, "runny nose": 0.85, "itchy eyes": 0.80, "cough": 0.30,
        "sore throat": 0.30, "headache": 0.25, "fever": 0.01, "body aches": 0.02,
    }),
    "Migraine": (0.06, {
        "headache": 0.99, "nausea": 0.60, "vomiting": 0.30, "light sensitivity": 0.75,
        "fatigue": 0.40, "fever": 0.01,
    }),
    "Other / not listed": (0.10, {}),   # catch-all so the bot stays humble
}
DEFAULT_P = 0.05          # P(symptom | condition) when a symptom isn't listed
OTHER_P = 0.15            # baseline likelihood used for the catch-all bucket

# Words people might type -> the symptom name used above
SYNONYMS = {
    "fever": ["fever", "feverish", "high temperature", "temperature"],
    "cough": ["cough", "coughing"],
    "sore throat": ["sore throat", "throat hurts", "scratchy throat", "throat pain"],
    "runny nose": ["runny nose", "stuffy nose", "congestion", "congested", "nasal"],
    "sneezing": ["sneeze", "sneezing"],
    "headache": ["headache", "head hurts", "head pain"],
    "fatigue": ["fatigue", "tired", "exhausted", "no energy", "weak"],
    "body aches": ["body ache", "body aches", "muscle ache", "muscle pain", "aching"],
    "chills": ["chills", "shivering"],
    "nausea": ["nausea", "nauseous", "queasy"],
    "vomiting": ["vomit", "vomiting", "throwing up", "threw up"],
    "diarrhea": ["diarrhea", "loose stool"],
    "abdominal pain": ["stomach pain", "stomach ache", "abdominal pain", "belly pain", "cramps"],
    "shortness of breath": ["shortness of breath", "short of breath", "hard to breathe"],
    "loss of taste or smell": ["loss of taste", "loss of smell", "can't taste", "can't smell",
                               "cannot taste", "cannot smell"],
    "rash": ["rash", "hives"],
    "itchy eyes": ["itchy eyes", "watery eyes", "eyes itch"],
    "light sensitivity": ["light sensitivity", "sensitive to light", "bright light hurts"],
}

NEGATIONS = ["no ", "not ", "without ", "don't have ", "dont have ", "never "]

# Symptoms that can also come from a food allergy reaction
ALLERGY_SIGNS = {"rash", "nausea", "vomiting", "abdominal pain", "diarrhea", "shortness of breath"}


# ---------------------------------------------------------------------------
# 2. UNDERSTANDING THE USER'S MESSAGE
# ---------------------------------------------------------------------------
def extract_symptoms(text):
    """Return (present, absent) sets of symptom names found in the text."""
    text = text.lower().replace("’", "'")
    present, absent = set(), set()
    for symptom, phrases in SYNONYMS.items():
        for phrase in phrases:
            for m in re.finditer(re.escape(phrase), text):
                before = text[max(0, m.start() - 18):m.start()]
                if any(neg in before for neg in NEGATIONS):
                    absent.add(symptom)
                else:
                    present.add(symptom)
    present -= absent          # an explicit "no X" wins
    return present, absent


# ---------------------------------------------------------------------------
# 3. THE PROBABILITY ENGINE (Naive Bayes)
# ---------------------------------------------------------------------------
def likelihood(condition, symptom):
    if condition == "Other / not listed":
        return OTHER_P
    return CONDITIONS[condition][1].get(symptom, DEFAULT_P)


def posterior(present, absent):
    scores = {}
    for name, (prior, _) in CONDITIONS.items():
        p = prior
        for s in present:
            p *= likelihood(name, s)
        for s in absent:
            p *= 1 - likelihood(name, s)
        scores[name] = p
    total = sum(scores.values()) or 1
    return {name: p / total for name, p in scores.items()}


def next_question(present, absent, probs):
    """Pick the unasked symptom that best separates the top two conditions."""
    top = [n for n, _ in sorted(probs.items(), key=lambda x: -x[1])
           if n != "Other / not listed"][:2]
    if len(top) < 2:
        return None
    best, best_gap = None, 0
    for s in SYNONYMS:
        if s in present or s in absent:
            continue
        gap = abs(likelihood(top[0], s) - likelihood(top[1], s))
        if gap > best_gap:
            best, best_gap = s, gap
    return best


# ---------------------------------------------------------------------------
# 4. BUILDING THE REPLY
# ---------------------------------------------------------------------------
def make_reply(text, username):
    state = st.session_state
    lines = []

    flags = find_emergencies(text)
    if flags:
        lines.append("🚨 **You mentioned something that can be serious ("
                     + ", ".join(flags) + "). Call 911 or get emergency help now.**")
        if "suicidal" in flags:
            lines.append("You can also call or text **988** (Suicide & Crisis Lifeline, US).")
        lines.append("")

    new_present, new_absent = extract_symptoms(text)
    if not new_present and not new_absent:
        if not flags:
            lines.append("I didn't recognize a symptom there. Try words like "
                         "*fever*, *cough*, *headache*, *nausea*...")
        return "\n".join(lines)

    state.chat_present |= new_present
    state.chat_absent |= new_absent
    state.chat_present -= state.chat_absent
    present, absent = state.chat_present, state.chat_absent

    lines.append("**Symptoms:** " + (", ".join(sorted(present)) or "none"))
    if absent:
        lines.append("**Not present:** " + ", ".join(sorted(absent)))
    lines.append("")
    lines.append("**Estimated likelihood (based on symptoms so far):**")
    probs = posterior(present, absent)
    for name, p in sorted(probs.items(), key=lambda x: -x[1])[:5]:
        lines.append("- " + name + ": " + str(round(p * 100, 1)) + "%")

    user = db.get_user(username)
    if user["allergies"] and present & ALLERGY_SIGNS:
        lines.append("")
        lines.append("⚠️ Some of these can also be an allergic reaction. Your saved allergies: "
                     + ", ".join(user["allergies"]) + ". Did you eat any of these recently?")

    q = next_question(present, absent, probs)
    if q:
        lines.append("")
        lines.append("To narrow it down: do you have **" + q + "**?")

    lines.append("")
    lines.append("_Estimates only, not medical advice. A doctor can give a real diagnosis._")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 5. THE TAB
# ---------------------------------------------------------------------------
def reset_chat():
    st.session_state.chat_messages = []
    st.session_state.chat_present = set()
    st.session_state.chat_absent = set()


def show(username):
    st.header("Symptom Checker")
    st.caption("Describe how you feel, e.g. *I have a fever, sore throat and no cough*. "
               "Demo only, not medical advice. In an emergency, call 911.")

    if "chat_messages" not in st.session_state:
        reset_chat()

    if st.button("Start over", key="chatbot_reset"):
        reset_chat()

    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    text = st.chat_input("Type your symptoms...", key="chatbot_input")
    if text:
        if text.strip().lower() == "reset":
            reset_chat()
        else:
            reply = make_reply(text, username)
            st.session_state.chat_messages.append({"role": "user", "content": text})
            st.session_state.chat_messages.append({"role": "assistant", "content": reply})
        st.rerun()
