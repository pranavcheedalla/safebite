# 🧭 Build-your-tab tasks

Each person builds their own tab from scratch. Your file in `features/` is a stub with a `show(username)` function and notes on what to build. These tasks break it into small steps. Each one should take 10–30 minutes, and you should run the app after each step to check it works.

Work on your own branch (see the README). Only change your own file. Ask the group before touching `shared/` or `app.py`.

---

## 👥 Everyone (do these first)

- [ ] **Run the app.** Follow "First-time setup" in the README. Log in as `test`. You'll see "Not built yet." on each tab.
- [ ] **Read `app.py`.** Find the line that calls *your* file's `show(username)`.
- [ ] **Read `shared/db.py`.** Answer: what does `get_user()` return for a new user? What fields does a user have? (Look at `empty_user()`.)
- [ ] **Try saving data.** In your `show()`, call `user = db.get_user(username)`, change something, call `db.save_user(username, user)`, then open `data/users.json` and find your change.
- [ ] **Make your branch.** `git checkout -b yourname-feature` and push it once so the group can see it.

---

## 👤 Audrina: Profile + Alerts (`features/profile.py`)

Everyone else's tab reads the lists you save, so build yours first.

- [ ] Show the user's allergies as a list (it starts empty).
- [ ] Add a text box and an "Add" button that adds an allergy and saves it. Save it in **lowercase**.
- [ ] Add a "Remove" button next to each allergy. (Every Streamlit button needs a unique `key=`.)
- [ ] Do the same for medications and foods to avoid. Can you write one function and reuse it 3 times?
- [ ] **Alerts:** count entries in `user["scan_history"]` where `"level"` isn't `"safe"` and show `st.warning` if there are any. (This will be empty until Pranav's scanner saves history.)
- [ ] **Stretch:** a dropdown of common allergies (peanuts, milk, eggs, soy, wheat, shellfish).

---

## 📷 Pranav: Food Scanner (`features/scanner.py`)

- [ ] Add a text box for a barcode. Call `lookup_barcode(code)` and show the product name. Test with `3017620422003`.
- [ ] Handle `None` (product not found) with `st.error`.
- [ ] Show the ingredients in an `st.expander`.
- [ ] Write `check_food(product, user)`, which returns `"avoid"` if any allergy appears in the ingredients or allergens. Test it by adding the allergy `milk` on the Profile tab.
- [ ] Extend it: `"caution"` for medication interactions (use `FOOD_DRUG_INTERACTIONS`) and for foods to avoid. Return the reasons too. Make sure a caution never overwrites an avoid.
- [ ] Show the result in red, yellow or green (`st.error` / `st.warning` / `st.success`) along with the reasons.
- [ ] Add a "Save to history" button that saves to `user["scan_history"]` with the fields listed in the file's notes.
- [ ] Add photo scanning with `st.camera_input` and `read_barcode_from_image`.
- [ ] **Stretch:** a "milk" allergy should also catch "whey" and "casein".

---

## 🔥 Vedanth: Calorie Tracker (`features/calories.py`)

- [ ] Add a number input for the daily goal and save it to `user["calorie_goal"]`.
- [ ] Add a food by typing a name and calories, and save it to `user["calorie_log"]` with today's date (`str(date.today())`).
- [ ] List today's foods and show the total with `st.metric`.
- [ ] Add a progress bar (`st.progress`) toward the goal. What happens if the total goes over the goal?
- [ ] Add foods by barcode with `lookup_barcode(code)`. Some products only have `calories_per_100g`, so decide what to do then (e.g. ask for grams).
- [ ] Add a "Remove" button for each food.
- [ ] **Stretch:** a weekly chart with `st.bar_chart`.

---

## 💬 Tharoon: Symptom Checker chatbot (`features/chatbot.py`)

This file doesn't exist yet, so you'll create it.

- [ ] Create `features/chatbot.py` with a `show(username)` that shows a header. Copy the pattern from any other stub.
- [ ] Add a "Symptom Checker" tab in `app.py`. `app.py` is shared, so tell the group first.
- [ ] Use `st.chat_input` and `st.chat_message` to repeat back what the user types. Keep past messages in `st.session_state` so they don't disappear when the page reruns.
- [ ] Set up `.streamlit/secrets.toml` (see the README). Run `git status` and confirm the file does **not** show up.
- [ ] Add `anthropic` to `requirements.txt` and replace the echo with a real AI reply.
- [ ] Give the AI the user's allergies and medications (from `db.get_user`) so its answers fit the user.
- [ ] **Emergency rules:** create `shared/emergency.py` with phrases like "can't breathe" or "throat swelling". If a message matches, show "Call 911" and skip the AI.

---

## 📁 Unassigned: Medical Files (stretch, `features/medical_files.py`)

Whoever picks this up, put your name in the README table and the file's notes.

- [ ] Add `st.file_uploader` for pdf/png/jpg files.
- [ ] Save the uploaded file to `data/uploads/<username>/` and record it in `user["files"]`.
- [ ] List the user's files with an `st.download_button` for each.
- [ ] Show image previews with `st.image`.
- [ ] What happens if someone uploads the same file twice? Handle it.

---

## ✅ When you're done

Open a pull request for your branch and post in the group chat: one thing that was hard, and one thing you want to add next.
