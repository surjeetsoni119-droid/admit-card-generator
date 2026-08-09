# Admit Card Generator (Desktop App)

A simple desktop app for your school to create exam admit cards — similar in
layout to a CBSE board admit card. Add students one by one, or import your
whole class from an Excel sheet, then generate a single PDF with one admit
card per student, ready to print.

---

## 1. What you need on the computer

- **Windows / Mac / Linux** desktop or laptop
- **Python 3.9 or higher** installed
  - Check by opening Command Prompt / Terminal and typing: `python --version`
  - If not installed, download from https://www.python.org/downloads/
  - On Windows, tick **"Add Python to PATH"** during install.

## 2. First-time setup

1. Copy the whole `admit_card_app` folder onto the school computer.
2. Open Command Prompt (Windows) or Terminal (Mac/Linux) in that folder.
3. Install the required libraries (only needed once):

   ```
   pip install -r requirements.txt
   ```

   (On Mac/Linux, if that doesn't work, try `pip3 install -r requirements.txt`)

## 3. Running the app

In the same folder, run:

```
python main.py
```

(Use `python3 main.py` on Mac/Linux if needed.)

The app window will open with 4 tabs.

---

## 4. How to use the app

### Tab 1 — School Setup
Fill in your school name, board name (e.g. "Central Board of Secondary
Education"), address, affiliation number, and principal's name. You can also
upload your **school logo** and **principal's signature** (as image files —
PNG or JPG). Click **Save School Info**.

### Tab 2 — Students
You can add students in two ways:

- **Add manually**: Click "+ Add Student" and fill the form (you can also
  attach the student's photo here).
- **Import from Excel**: Click "Import from Excel" and select an `.xlsx` or
  `.csv` file. A sample template is included: `sample_students_template.xlsx`.
  Your Excel file must have these column headers (in the first row):

  | roll_no | name | class_section | father_name | mother_name | dob | exam_center |
  |---------|------|---------------|-------------|-------------|-----|-------------|

  Only `roll_no` and `name` are required — the rest are optional.

  Importing again with the same roll numbers will **update** those existing
  records instead of duplicating them.

You can edit or delete any student from the list, or delete all of them to
start fresh for a new exam session.

### Tab 3 — Exam Schedule
Add each subject with its code, name, exam date, and time. This same subject
list is printed on every student's admit card.

### Tab 4 — Generate Admit Cards
Click **"Generate Admit Cards PDF"**. This creates one PDF file with one
admit card per page (one per student), saved inside the
`generated_admit_cards` folder. Click **"Open Output Folder"** to find it and
print directly, or open it with any PDF reader.

---

## 5. Where your data is stored

All school, student, and exam data is saved locally in a file called
`admit_card_data.db` inside the app folder (no internet needed, nothing is
sent anywhere). Back up this file if you want to keep your records safe —
just copy it somewhere safe occasionally.

## 6. Common issues

- **"pip not recognized"** → Python wasn't added to PATH during install;
  reinstall Python and tick that option, or use `py -m pip install -r requirements.txt`.
- **Photo not showing on card** → Make sure the photo is a `.jpg` or `.png`
  file and was correctly selected using "Browse" in the Add Student form.
- **App looks small/large on screen** → You can resize the app window
  normally, like any desktop program.

---

## 7. Turning this into a single-click app (optional, later)

Once you're happy with it, you can use a tool called **PyInstaller** to turn
this into a single `.exe` (Windows) file that any computer in the school can
run without installing Python. Ask if you'd like help setting that up.
