"""
main.py
Admit Card Generator - Desktop App
Run with: python main.py
"""

import os
import sys
import shutil
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import customtkinter as ctk
import pandas as pd
from PIL import Image

import database as db
from pdf_generator import generate_admit_cards_pdf
from utils import get_base_dir, get_resource_dir

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

APP_DIR = get_base_dir()
PHOTOS_DIR = os.path.join(APP_DIR, "student_photos")
OUTPUT_DIR = os.path.join(APP_DIR, "generated_admit_cards")
for d in (PHOTOS_DIR, OUTPUT_DIR):
    os.makedirs(d, exist_ok=True)


def ensure_assets_available():
    """
    Copies the bundled default logo/icon into a persistent 'assets' folder
    next to the app (or .exe), so they survive between runs even when
    PyInstaller extracts bundled files into a temporary folder.
    """
    persistent_assets = os.path.join(APP_DIR, "assets")
    os.makedirs(persistent_assets, exist_ok=True)
    bundled_assets = os.path.join(get_resource_dir(), "assets")
    if os.path.isdir(bundled_assets):
        for fname in ("app_icon.png", "school_logo.png"):
            src = os.path.join(bundled_assets, fname)
            dst = os.path.join(persistent_assets, fname)
            if os.path.exists(src) and not os.path.exists(dst):
                shutil.copy(src, dst)
    return persistent_assets


ASSETS_DIR = ensure_assets_available()


def open_folder(path):
    try:
        if sys.platform.startswith("win"):
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.run(["open", path])
        else:
            subprocess.run(["xdg-open", path])
    except Exception:
        pass


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Kopal Public School - Admit Card Generator")
        self.geometry("1050x720")
        self.minsize(950, 620)

        db.init_db()
        self.prefill_school_branding()
        self.set_window_icon()
        self.build_header()

        self.tabview = ctk.CTkTabview(self, width=1020, height=630)
        self.tabview.pack(padx=15, pady=(0, 15), fill="both", expand=True)

        self.tab_school = self.tabview.add("School Setup")
        self.tab_students = self.tabview.add("Students")
        self.tab_subjects = self.tabview.add("Exam Schedule")
        self.tab_generate = self.tabview.add("Generate Admit Cards")

        self.build_school_tab()
        self.build_students_tab()
        self.build_subjects_tab()
        self.build_generate_tab()

    def prefill_school_branding(self):
        """On first run (empty school info), pre-fill Kopal Public School branding."""
        info = db.get_school_info()
        if not info.get("school_name"):
            logo_path = os.path.join(ASSETS_DIR, "school_logo.png")
            db.save_school_info({
                "school_name": "Kopal Public School",
                "board_name": "Central Board of Secondary Education",
                "address": "",
                "affiliation_no": "",
                "principal_name": "",
                "logo_path": logo_path if os.path.exists(logo_path) else "",
                "signature_path": "",
            })

    def set_window_icon(self):
        """Sets the app window/taskbar icon from the school logo, if present."""
        icon_path = os.path.join(ASSETS_DIR, "app_icon.png")
        if os.path.exists(icon_path):
            try:
                icon_img = Image.open(icon_path)
                self._icon_photo = tk.PhotoImage(file=icon_path) if icon_path.endswith(".png") else None
                self.iconphoto(True, self._icon_photo)
            except Exception:
                pass

    def build_header(self):
        """Branded header banner shown above the tabs, with logo + school name."""
        header = ctk.CTkFrame(self, fg_color="#1e3a8a", height=64, corner_radius=0)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        logo_path = os.path.join(ASSETS_DIR, "school_logo.png")
        inner = ctk.CTkFrame(header, fg_color="transparent")
        inner.pack(side="left", padx=18, pady=8)

        if os.path.exists(logo_path):
            try:
                pil_img = Image.open(logo_path)
                ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(46, 46))
                ctk.CTkLabel(inner, image=ctk_img, text="").pack(side="left", padx=(0, 12))
            except Exception:
                pass

        text_frame = ctk.CTkFrame(inner, fg_color="transparent")
        text_frame.pack(side="left")
        ctk.CTkLabel(text_frame, text="Kopal Public School", font=("Arial", 17, "bold"),
                     text_color="white").pack(anchor="w")
        ctk.CTkLabel(text_frame, text="Admit Card Generator", font=("Arial", 11),
                     text_color="#d4af37").pack(anchor="w")

    # ---------------------------------------------------------------
    # SCHOOL SETUP TAB
    # ---------------------------------------------------------------
    def build_school_tab(self):
        frame = ctk.CTkFrame(self.tab_school, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        info = db.get_school_info()

        ctk.CTkLabel(frame, text="School Details", font=("Arial", 18, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 15))

        self.school_name_var = ctk.StringVar(value=info.get("school_name", ""))
        self.board_name_var = ctk.StringVar(value=info.get("board_name", ""))
        self.address_var = ctk.StringVar(value=info.get("address", ""))
        self.affiliation_var = ctk.StringVar(value=info.get("affiliation_no", ""))
        self.principal_var = ctk.StringVar(value=info.get("principal_name", ""))
        self.logo_path_var = ctk.StringVar(value=info.get("logo_path", ""))
        self.signature_path_var = ctk.StringVar(value=info.get("signature_path", ""))
        self.exam_type_var = ctk.StringVar(value=info.get("exam_type", ""))

        fields = [
            ("School Name", self.school_name_var),
            ("Board Name (e.g. CBSE)", self.board_name_var),
            ("Address", self.address_var),
            ("Affiliation No.", self.affiliation_var),
            ("Principal Name", self.principal_var),
            ("Examination Type (e.g. Annual Examination 2025-26)", self.exam_type_var),
        ]

        r = 1
        for label, var in fields:
            ctk.CTkLabel(frame, text=label, width=180, anchor="w").grid(row=r, column=0, sticky="w", pady=6)
            ctk.CTkEntry(frame, textvariable=var, width=420).grid(row=r, column=1, sticky="w", pady=6)
            r += 1

        ctk.CTkLabel(frame, text="School Logo", width=180, anchor="w").grid(row=r, column=0, sticky="w", pady=6)
        logo_row = ctk.CTkFrame(frame, fg_color="transparent")
        logo_row.grid(row=r, column=1, sticky="w")
        ctk.CTkEntry(logo_row, textvariable=self.logo_path_var, width=320, state="readonly").pack(side="left")
        ctk.CTkButton(logo_row, text="Browse", width=80,
                      command=lambda: self.browse_image(self.logo_path_var)).pack(side="left", padx=6)
        r += 1

        ctk.CTkLabel(frame, text="Principal Signature", width=180, anchor="w").grid(row=r, column=0, sticky="w", pady=6)
        sig_row = ctk.CTkFrame(frame, fg_color="transparent")
        sig_row.grid(row=r, column=1, sticky="w")
        ctk.CTkEntry(sig_row, textvariable=self.signature_path_var, width=320, state="readonly").pack(side="left")
        ctk.CTkButton(sig_row, text="Browse", width=80,
                      command=lambda: self.browse_image(self.signature_path_var)).pack(side="left", padx=6)
        r += 1

        ctk.CTkLabel(frame, text="Exam Instructions", width=180, anchor="nw").grid(
            row=r, column=0, sticky="nw", pady=6)
        instr_frame = ctk.CTkFrame(frame, fg_color="transparent")
        instr_frame.grid(row=r, column=1, sticky="w", pady=6)
        self.instructions_box = ctk.CTkTextbox(instr_frame, width=420, height=140)
        self.instructions_box.pack(side="left")
        default_instructions = info.get("instructions", "")
        if default_instructions:
            self.instructions_box.insert("1.0", default_instructions)
        ctk.CTkLabel(instr_frame, text="One instruction per line.\nLeave blank to use the built-in\ndefault instructions.",
                     font=("Arial", 10), text_color="gray", justify="left").pack(side="left", padx=10, anchor="n")
        r += 1

        ctk.CTkButton(frame, text="Save School Info", command=self.save_school_info,
                      fg_color="#1f8a3d", hover_color="#166b2e").grid(row=r, column=0, pady=20, sticky="w")

    def browse_image(self, var):
        path = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg")])
        if path:
            var.set(path)

    def save_school_info(self):
        data = {
            "school_name": self.school_name_var.get(),
            "board_name": self.board_name_var.get(),
            "address": self.address_var.get(),
            "affiliation_no": self.affiliation_var.get(),
            "principal_name": self.principal_var.get(),
            "logo_path": self.logo_path_var.get(),
            "signature_path": self.signature_path_var.get(),
            "exam_type": self.exam_type_var.get(),
            "instructions": self.instructions_box.get("1.0", "end").strip(),
        }
        db.save_school_info(data)
        messagebox.showinfo("Saved", "School information saved successfully.")

    # ---------------------------------------------------------------
    # STUDENTS TAB
    # ---------------------------------------------------------------
    def build_students_tab(self):
        frame = ctk.CTkFrame(self.tab_students, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=15, pady=15)

        btn_row = ctk.CTkFrame(frame, fg_color="transparent")
        btn_row.pack(fill="x", pady=(0, 10))

        ctk.CTkButton(btn_row, text="+ Add Student", command=self.open_add_student_dialog).pack(side="left", padx=4)
        ctk.CTkButton(btn_row, text="Import from Excel", command=self.import_excel).pack(side="left", padx=4)
        ctk.CTkButton(btn_row, text="Edit Selected", command=self.edit_selected_student).pack(side="left", padx=4)
        ctk.CTkButton(btn_row, text="Delete Selected", fg_color="#b3261e", hover_color="#8f1e18",
                      command=self.delete_selected_student).pack(side="left", padx=4)
        ctk.CTkButton(btn_row, text="Delete All", fg_color="#b3261e", hover_color="#8f1e18",
                      command=self.delete_all_students).pack(side="left", padx=4)
        self.student_count_label = ctk.CTkLabel(btn_row, text="")
        self.student_count_label.pack(side="right", padx=4)

        columns = ("id", "roll_no", "name", "class_section", "father_name", "exam_center")
        self.student_tree = ttk.Treeview(frame, columns=columns, show="headings", height=18)
        headings = {"id": "ID", "roll_no": "Roll No.", "name": "Name",
                    "class_section": "Class/Sec", "father_name": "Father's Name",
                    "exam_center": "Exam Center"}
        widths = {"id": 40, "roll_no": 90, "name": 200, "class_section": 100,
                  "father_name": 180, "exam_center": 200}
        for c in columns:
            self.student_tree.heading(c, text=headings[c])
            self.student_tree.column(c, width=widths[c])
        self.student_tree.column("id", width=0, stretch=False)  # hide id visually but keep column
        self.student_tree.pack(fill="both", expand=True)

        self.refresh_students_table()

    def refresh_students_table(self):
        for row in self.student_tree.get_children():
            self.student_tree.delete(row)
        students = db.get_all_students()
        for s in students:
            self.student_tree.insert("", "end", values=(
                s["id"], s["roll_no"], s["name"], s["class_section"],
                s["father_name"], s["exam_center"]
            ))
        self.student_count_label.configure(text=f"Total students: {len(students)}")
        self._students_cache = {s["id"]: s for s in students}

    def open_add_student_dialog(self, existing=None):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Edit Student" if existing else "Add Student")
        dialog.geometry("420x480")
        dialog.grab_set()

        fields = ["roll_no", "name", "class_section", "father_name", "mother_name", "dob", "exam_center"]
        labels = {"roll_no": "Roll No.", "name": "Student Name", "class_section": "Class/Section",
                  "father_name": "Father's Name", "mother_name": "Mother's Name",
                  "dob": "Date of Birth (DD-MM-YYYY)", "exam_center": "Exam Center"}
        vars_map = {}

        for i, f in enumerate(fields):
            ctk.CTkLabel(dialog, text=labels[f]).pack(anchor="w", padx=20, pady=(10 if i == 0 else 4, 0))
            v = ctk.StringVar(value=existing.get(f, "") if existing else "")
            ctk.CTkEntry(dialog, textvariable=v, width=360).pack(padx=20)
            vars_map[f] = v

        photo_var = ctk.StringVar(value=existing.get("photo_path", "") if existing else "")
        ctk.CTkLabel(dialog, text="Student Photo").pack(anchor="w", padx=20, pady=(10, 0))
        photo_row = ctk.CTkFrame(dialog, fg_color="transparent")
        photo_row.pack(padx=20, anchor="w")
        ctk.CTkEntry(photo_row, textvariable=photo_var, width=280, state="readonly").pack(side="left")
        ctk.CTkButton(photo_row, text="Browse", width=70,
                      command=lambda: self.browse_image(photo_var)).pack(side="left", padx=6)

        def save():
            data = {f: vars_map[f].get().strip() for f in fields}
            data["photo_path"] = photo_var.get()
            if not data["roll_no"] or not data["name"]:
                messagebox.showwarning("Missing info", "Roll No. and Name are required.")
                return
            if existing:
                db.update_student(existing["id"], data)
            else:
                try:
                    db.add_student(data)
                except Exception as e:
                    messagebox.showerror("Error", f"Could not save student.\n{e}")
                    return
            dialog.destroy()
            self.refresh_students_table()

        ctk.CTkButton(dialog, text="Save", command=save, fg_color="#1f8a3d",
                      hover_color="#166b2e").pack(pady=20)

    def edit_selected_student(self):
        sel = self.student_tree.selection()
        if not sel:
            messagebox.showinfo("No selection", "Please select a student to edit.")
            return
        student_id = self.student_tree.item(sel[0])["values"][0]
        existing = self._students_cache.get(student_id)
        self.open_add_student_dialog(existing=existing)

    def delete_selected_student(self):
        sel = self.student_tree.selection()
        if not sel:
            messagebox.showinfo("No selection", "Please select a student to delete.")
            return
        student_id = self.student_tree.item(sel[0])["values"][0]
        if messagebox.askyesno("Confirm", "Delete this student?"):
            db.delete_student(student_id)
            self.refresh_students_table()

    def delete_all_students(self):
        if messagebox.askyesno("Confirm", "Delete ALL students? This cannot be undone."):
            db.delete_all_students()
            self.refresh_students_table()

    def import_excel(self):
        path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx *.xls *.csv")])
        if not path:
            return
        try:
            if path.lower().endswith(".csv"):
                df = pd.read_csv(path, dtype=str).fillna("")
            else:
                df = pd.read_excel(path, dtype=str).fillna("")
        except Exception as e:
            messagebox.showerror("Error reading file", str(e))
            return

        # Normalize column names: lowercase, strip spaces/underscores
        col_map = {}
        for col in df.columns:
            key = col.strip().lower().replace(" ", "_")
            col_map[col] = key
        df = df.rename(columns=col_map)

        expected = ["roll_no", "name", "class_section", "father_name", "mother_name", "dob", "exam_center"]
        missing = [c for c in ["roll_no", "name"] if c not in df.columns]
        if missing:
            messagebox.showerror(
                "Missing columns",
                "Your Excel file must have at least these column headers:\n"
                "roll_no, name\n\n(optional: class_section, father_name, mother_name, dob, exam_center)\n\n"
                f"Missing: {', '.join(missing)}"
            )
            return

        rows = []
        for _, r in df.iterrows():
            row = {c: r.get(c, "") for c in expected}
            row["photo_path"] = ""
            rows.append(row)

        db.bulk_add_students(rows)
        self.refresh_students_table()
        messagebox.showinfo("Import complete", f"Imported/updated {len(rows)} student records.")

    # ---------------------------------------------------------------
    # EXAM SCHEDULE TAB
    # ---------------------------------------------------------------
    def build_subjects_tab(self):
        frame = ctk.CTkFrame(self.tab_subjects, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=15, pady=15)

        btn_row = ctk.CTkFrame(frame, fg_color="transparent")
        btn_row.pack(fill="x", pady=(0, 10))
        ctk.CTkButton(btn_row, text="+ Add Subject", command=self.open_add_subject_dialog).pack(side="left", padx=4)
        ctk.CTkButton(btn_row, text="Delete Selected", fg_color="#b3261e", hover_color="#8f1e18",
                      command=self.delete_selected_subject).pack(side="left", padx=4)
        ctk.CTkButton(btn_row, text="Delete All", fg_color="#b3261e", hover_color="#8f1e18",
                      command=self.delete_all_subjects).pack(side="left", padx=4)

        columns = ("id", "subject_code", "subject_name", "class_section", "exam_date", "exam_time")
        self.subject_tree = ttk.Treeview(frame, columns=columns, show="headings", height=18)
        headings = {"id": "ID", "subject_code": "Code", "subject_name": "Subject", "class_section": "Class",
                    "exam_date": "Date", "exam_time": "Time"}
        widths = {"id": 0, "subject_code": 90, "subject_name": 230, "class_section": 90,
                  "exam_date": 130, "exam_time": 130}
        for c in columns:
            self.subject_tree.heading(c, text=headings[c])
            self.subject_tree.column(c, width=widths[c], stretch=(c != "id"))
        self.subject_tree.pack(fill="both", expand=True)

        self.refresh_subjects_table()

    def refresh_subjects_table(self):
        for row in self.subject_tree.get_children():
            self.subject_tree.delete(row)
        for s in db.get_all_subjects():
            self.subject_tree.insert("", "end", values=(
                s["id"], s["subject_code"], s["subject_name"],
                s.get("class_section", "") or "All", s["exam_date"], s["exam_time"]
            ))

    def open_add_subject_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Add Subject")
        dialog.geometry("360x380")
        dialog.grab_set()

        fields = ["subject_code", "subject_name", "class_section", "exam_date", "exam_time"]
        labels = {"subject_code": "Subject Code", "subject_name": "Subject Name",
                  "class_section": "Class / Section (blank = all classes)",
                  "exam_date": "Exam Date (DD-MM-YYYY)", "exam_time": "Exam Time (e.g. 10:00 AM)"}
        vars_map = {}
        for i, f in enumerate(fields):
            ctk.CTkLabel(dialog, text=labels[f]).pack(anchor="w", padx=20, pady=(14 if i == 0 else 6, 0))
            v = ctk.StringVar()
            ctk.CTkEntry(dialog, textvariable=v, width=300).pack(padx=20)
            vars_map[f] = v

        ctk.CTkLabel(dialog, text="Leave Class/Section blank for a subject common to every class\n"
                                   "(e.g. English), or set it (e.g. '10-A') for a class-specific subject\n"
                                   "(e.g. an elective only senior students take).",
                     font=("Arial", 10), text_color="gray", justify="left").pack(anchor="w", padx=20, pady=(8, 0))

        def save():
            data = {f: vars_map[f].get().strip() for f in fields}
            if not data["subject_name"]:
                messagebox.showwarning("Missing info", "Subject name is required.")
                return
            db.add_subject(data)
            dialog.destroy()
            self.refresh_subjects_table()

        ctk.CTkButton(dialog, text="Save", command=save, fg_color="#1f8a3d",
                      hover_color="#166b2e").pack(pady=20)

    def delete_selected_subject(self):
        sel = self.subject_tree.selection()
        if not sel:
            messagebox.showinfo("No selection", "Please select a subject to delete.")
            return
        subject_id = self.subject_tree.item(sel[0])["values"][0]
        db.delete_subject(subject_id)
        self.refresh_subjects_table()

    def delete_all_subjects(self):
        if messagebox.askyesno("Confirm", "Delete ALL subjects?"):
            db.delete_all_subjects()
            self.refresh_subjects_table()

    # ---------------------------------------------------------------
    # GENERATE TAB
    # ---------------------------------------------------------------
    def build_generate_tab(self):
        frame = ctk.CTkFrame(self.tab_generate, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(frame, text="Generate Admit Cards", font=("Arial", 18, "bold")).pack(anchor="w", pady=(0, 10))
        ctk.CTkLabel(frame, text="This will create one PDF containing an admit card for every student,\n"
                                  "using the currently saved School Info and Exam Schedule.",
                     justify="left").pack(anchor="w", pady=(0, 15))

        self.gen_summary_label = ctk.CTkLabel(frame, text="", font=("Arial", 13))
        self.gen_summary_label.pack(anchor="w", pady=(0, 15))

        ctk.CTkButton(frame, text="Generate Admit Cards PDF", height=45, font=("Arial", 14, "bold"),
                      fg_color="#1f8a3d", hover_color="#166b2e",
                      command=self.generate_pdf).pack(anchor="w", pady=10)

        ctk.CTkButton(frame, text="Open Output Folder", command=lambda: open_folder(OUTPUT_DIR)).pack(anchor="w", pady=5)

        self.tabview.configure(command=self.on_tab_change)

    def on_tab_change(self):
        if self.tabview.get() == "Generate Admit Cards":
            n_students = len(db.get_all_students())
            n_subjects = len(db.get_all_subjects())
            self.gen_summary_label.configure(
                text=f"Students in database: {n_students}   |   Subjects scheduled: {n_subjects}")

    def generate_pdf(self):
        students = db.get_all_students()
        subjects = db.get_all_subjects()
        school_info = db.get_school_info()

        if not students:
            messagebox.showwarning("No students", "Please add students before generating admit cards.")
            return
        if not school_info.get("school_name"):
            messagebox.showwarning("Missing school info", "Please fill in School Setup first.")
            return

        output_path = os.path.join(OUTPUT_DIR, "admit_cards.pdf")
        try:
            generate_admit_cards_pdf(students, school_info, subjects, output_path)
        except Exception as e:
            messagebox.showerror("Error generating PDF", str(e))
            return

        messagebox.showinfo("Success", f"Generated {len(students)} admit card(s).\nSaved to:\n{output_path}")
        open_folder(OUTPUT_DIR)


if __name__ == "__main__":
    app = App()
    app.mainloop()
