# 🥗 SafeBite

Track your allergies and medications, scan food barcodes, and get warned when a food might not be safe for you. Also tracks daily calories.

> Student project. Not medical advice.

## Who owns what

| Tab | File | Owner |
|---|---|---|
| Profile + Alerts | `features/profile.py` | Audrina |
| Food Scanner | `features/scanner.py` | Pranav |
| Calorie Tracker | `features/calories.py` | Vedanth |
| Symptom Checker (AI chatbot) | `features/chatbot.py` | Tharoon |
| Medical Files (stretch) | `features/medical_files.py` | ________ |

**Shared code** lives in `shared/`. Ask the group before changing it, since everyone depends on it:
- `shared/barcode.py`: `lookup_barcode()` and `read_barcode_from_image()`
- `shared/db.py`: `get_user()` and `save_user()` to load and save a user's data
- `shared/interactions.py`: the food–medication interaction list
- `shared/emergency.py`: emergency keyword rules (checked before the AI on every chat message)

## First-time setup

1. Install [Python 3.10+](https://www.python.org/downloads/) and [Git](https://git-scm.com/downloads).
2. Clone the repo and go into it:
```
   git clone https://github.com/pranavcheedalla/safebite.git
   cd safebite
```
3. Install the packages:
```
   pip install -r requirements.txt
```
4. *(Optional, for camera barcode scanning)* Install zbar:
   - Mac: `brew install zbar`
   - Windows: usually works without this step
   - Linux: `sudo apt install libzbar0`

   If this doesn't work, the app still runs. You'll just need to type barcodes instead of scanning them.
5. Run the app:
```
   streamlit run app.py
```
   It opens in your browser. Log in with any username.

**Symptom Checker setup:** the chatbot needs an Anthropic API key.
1. Get one at [console.anthropic.com](https://console.anthropic.com) (it costs a small amount per message).
2. Create a file `.streamlit/secrets.toml` in the project folder containing:
```
   ANTHROPIC_API_KEY = "sk-ant-..."
```
3. **Never commit this file.** It's already in `.gitignore`. Each person uses their own key, or one person shares it privately (not in the repo or group chat).

Without a key, the rest of the app still works.

**Test barcodes:** `3017620422003` (Nutella), `737628064502` (Thai peanut noodles).

## How to work without breaking each other's code

Always work on your own branch, never directly on `main`.

```
git checkout main
git pull                          # get everyone's latest code
git checkout -b pranav-scanner    # make your branch (only the first time)

# ...edit your file, test with streamlit
