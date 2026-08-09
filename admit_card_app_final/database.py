"""
database.py
Handles all SQLite database operations for the Admit Card Generator.
"""

import sqlite3
import os
from utils import get_base_dir

DB_PATH = os.path.join(get_base_dir(), "admit_card_data.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS school_info (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            school_name TEXT,
            board_name TEXT,
            address TEXT,
            affiliation_no TEXT,
            logo_path TEXT,
            signature_path TEXT,
            principal_name TEXT,
            exam_type TEXT,
            instructions TEXT
        )
    """)

    # Migrate older databases that were created before these columns existed.
    cur.execute("PRAGMA table_info(school_info)")
    existing_cols = {row["name"] for row in cur.fetchall()}
    if "exam_type" not in existing_cols:
        cur.execute("ALTER TABLE school_info ADD COLUMN exam_type TEXT")
    if "instructions" not in existing_cols:
        cur.execute("ALTER TABLE school_info ADD COLUMN instructions TEXT")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_no TEXT UNIQUE,
            name TEXT NOT NULL,
            class_section TEXT,
            father_name TEXT,
            mother_name TEXT,
            dob TEXT,
            exam_center TEXT,
            photo_path TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_code TEXT,
            subject_name TEXT,
            exam_date TEXT,
            exam_time TEXT,
            class_section TEXT
        )
    """)

    cur.execute("PRAGMA table_info(subjects)")
    subject_cols = {row["name"] for row in cur.fetchall()}
    if "class_section" not in subject_cols:
        cur.execute("ALTER TABLE subjects ADD COLUMN class_section TEXT")

    # Ensure a single school_info row always exists
    cur.execute("SELECT COUNT(*) as c FROM school_info")
    if cur.fetchone()["c"] == 0:
        cur.execute("""
            INSERT INTO school_info (id, school_name, board_name, address, affiliation_no,
                                      logo_path, signature_path, principal_name, exam_type, instructions)
            VALUES (1, '', 'Central Board of Secondary Education', '', '', '', '', '', '', '')
        """)

    conn.commit()
    conn.close()


# ---------------- School Info ----------------

def save_school_info(data: dict):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE school_info SET
            school_name = ?, board_name = ?, address = ?, affiliation_no = ?,
            logo_path = ?, signature_path = ?, principal_name = ?,
            exam_type = ?, instructions = ?
        WHERE id = 1
    """, (
        data.get("school_name", ""),
        data.get("board_name", ""),
        data.get("address", ""),
        data.get("affiliation_no", ""),
        data.get("logo_path", ""),
        data.get("signature_path", ""),
        data.get("principal_name", ""),
        data.get("exam_type", ""),
        data.get("instructions", ""),
    ))
    conn.commit()
    conn.close()


def get_school_info():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM school_info WHERE id = 1")
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else {}


# ---------------- Students ----------------

def add_student(data: dict):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO students (roll_no, name, class_section, father_name, mother_name,
                               dob, exam_center, photo_path)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("roll_no", ""),
        data.get("name", ""),
        data.get("class_section", ""),
        data.get("father_name", ""),
        data.get("mother_name", ""),
        data.get("dob", ""),
        data.get("exam_center", ""),
        data.get("photo_path", ""),
    ))
    conn.commit()
    conn.close()


def bulk_add_students(rows: list):
    """rows: list of dicts with same keys as add_student"""
    conn = get_connection()
    cur = conn.cursor()
    for data in rows:
        try:
            cur.execute("""
                INSERT INTO students (roll_no, name, class_section, father_name, mother_name,
                                       dob, exam_center, photo_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(data.get("roll_no", "")).strip(),
                str(data.get("name", "")).strip(),
                str(data.get("class_section", "")).strip(),
                str(data.get("father_name", "")).strip(),
                str(data.get("mother_name", "")).strip(),
                str(data.get("dob", "")).strip(),
                str(data.get("exam_center", "")).strip(),
                str(data.get("photo_path", "")).strip(),
            ))
        except sqlite3.IntegrityError:
            # duplicate roll_no -> update existing record instead
            cur.execute("""
                UPDATE students SET name=?, class_section=?, father_name=?, mother_name=?,
                       dob=?, exam_center=?, photo_path=?
                WHERE roll_no=?
            """, (
                str(data.get("name", "")).strip(),
                str(data.get("class_section", "")).strip(),
                str(data.get("father_name", "")).strip(),
                str(data.get("mother_name", "")).strip(),
                str(data.get("dob", "")).strip(),
                str(data.get("exam_center", "")).strip(),
                str(data.get("photo_path", "")).strip(),
                str(data.get("roll_no", "")).strip(),
            ))
    conn.commit()
    conn.close()


def get_all_students():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM students ORDER BY roll_no")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def update_student(student_id, data: dict):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE students SET roll_no=?, name=?, class_section=?, father_name=?, mother_name=?,
               dob=?, exam_center=?, photo_path=?
        WHERE id=?
    """, (
        data.get("roll_no", ""), data.get("name", ""), data.get("class_section", ""),
        data.get("father_name", ""), data.get("mother_name", ""), data.get("dob", ""),
        data.get("exam_center", ""), data.get("photo_path", ""), student_id
    ))
    conn.commit()
    conn.close()


def delete_student(student_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM students WHERE id = ?", (student_id,))
    conn.commit()
    conn.close()


def delete_all_students():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM students")
    conn.commit()
    conn.close()


# ---------------- Subjects / Exam Schedule ----------------

def add_subject(data: dict):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO subjects (subject_code, subject_name, exam_date, exam_time, class_section)
        VALUES (?, ?, ?, ?, ?)
    """, (
        data.get("subject_code", ""), data.get("subject_name", ""),
        data.get("exam_date", ""), data.get("exam_time", ""),
        data.get("class_section", "").strip(),
    ))
    conn.commit()
    conn.close()


def get_all_subjects():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM subjects ORDER BY exam_date")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def delete_subject(subject_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM subjects WHERE id = ?", (subject_id,))
    conn.commit()
    conn.close()


def delete_all_subjects():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM subjects")
    conn.commit()
    conn.close()
