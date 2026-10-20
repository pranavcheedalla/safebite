# 🥗 SafeBite

Track your allergies and medications, scan food barcodes, and get warned when a food might not be safe for you. Also tracks daily calories.

> Student project. Not medical advice.

## Who owns what

| Tab | File | Owner |
|---|---|---|
| Profile + Alerts | `features/profile.py` | ________ |
| Food Scanner | `features/scanner.py` | Pranav |
| Calorie Tracker | `features/calories.py` | Vedanth |
| Medical Files (stretch) | `features/medical_files.py` | ________ |

**Shared code** lives in `shared/`. Ask the group before changing it, since everyone depends on it:
- `shared/barcode.py`: `lookup_barcode()` and `read_barcode_from_image()`
- `shared/db.py`: `get_user()` and `save_user()` to load and save a user's data
- `shared/interactions.py`: the food–medication interaction list

## First-time setup

1. Install [Python 3.10+](https://www.python.org/downloads/) and [Git](https://git-scm.com/downloads).
2. Clone the repo and go into it:
   ```
   git clone <REPO URL>
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

**Test barcodes:** `3017620422003` (Nutella), `737628064502` (Thai peanut noodles).

## How to work without breaking each other's code

Always work on your own branch, never directly on `main`.

```
git checkout main
git pull                          # get everyone's latest code
git checkout -b pranav-scanner    # make your branch (only the first time)

# ...edit your file, test with streamlit run app.py...

git add .
git commit -m "Add allergen matching"
git push -u origin pranav-scanner
```

Then go to the repo on GitHub, click **Compare & pull request**, and have someone look at it before merging.

**Rules:**
- Mostly edit your own file in `features/`.
- Run the app before you push, and make sure it doesn't crash.
- Pull from `main` often to stay up to date.

## Using AI to help

Paste your file into the AI along with something like:

> "This is a Streamlit app. Here's my file `features/calories.py` and the shared helper `shared/barcode.py`. Add a weekly bar chart of calories per day. Keep using `db.get_user()` and `db.save_user()` for data. Explain what you changed."

Always tell the AI which shared functions exist, so it doesn't invent its own.

## Later: switching to Firebase

Right now data is saved in `data/users.json` on each person's own computer. To share data and add real login, we'll rewrite only `shared/db.py` to use Firebase. Every feature file keeps working unchanged.
