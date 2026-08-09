"""
pdf_generator.py
Generates admit cards (PDF) styled like a typical board-exam admit card.
"""

import os
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PIL import Image, ImageFilter

CARD_W = 190 * mm
CARD_H = 130 * mm

# Watermark tuning: how blurred and how faint the background logo appears.
WATERMARK_BLUR_RADIUS = 4
WATERMARK_OPACITY = 0.14  # 0 = invisible, 1 = fully opaque

_watermark_cache = {}


def _get_watermark_image(logo_path):
    """
    Loads the school logo, softens it (blur + low opacity) so it can be used
    as a background watermark, and returns a cached ImageReader for reportlab.
    Returns None if the logo is missing or can't be processed.
    """
    if not logo_path or not os.path.exists(logo_path):
        return None

    cache_key = (logo_path, os.path.getmtime(logo_path))
    if cache_key in _watermark_cache:
        return _watermark_cache[cache_key]

    try:
        img = Image.open(logo_path).convert("RGBA")
        img = img.filter(ImageFilter.GaussianBlur(radius=WATERMARK_BLUR_RADIUS))

        r, g, b, a = img.split()
        a = a.point(lambda p: int(p * WATERMARK_OPACITY))
        img.putalpha(a)

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        reader = ImageReader(buf)
    except Exception:
        reader = None

    _watermark_cache[cache_key] = reader
    return reader


def _draw_watermark(c, cx, cy, max_w, max_h, logo_path):
    """Draws the faded/blurred logo centered at (cx, cy), fit within max_w x max_h."""
    reader = _get_watermark_image(logo_path)
    if reader is None:
        return
    try:
        img_w, img_h = reader.getSize()
        scale = min(max_w / img_w, max_h / img_h)
        w, h = img_w * scale, img_h * scale
        c.drawImage(reader, cx - w / 2, cy - h / 2, width=w, height=h,
                    mask='auto', preserveAspectRatio=True)
    except Exception:
        pass


def _draw_placeholder_photo(c, x, y, w, h):
    c.setStrokeColorRGB(0.5, 0.5, 0.5)
    c.rect(x, y, w, h)
    c.setFont("Helvetica", 7)
    c.setFillColorRGB(0.5, 0.5, 0.5)
    c.drawCentredString(x + w / 2, y + h / 2, "PHOTO")
    c.setFillColorRGB(0, 0, 0)


def _draw_card(c, x0, y0, student, school_info, subjects):
    """Draws one admit card with its top-left corner at (x0, y0)."""

    # Outer border
    c.setLineWidth(1)
    c.setStrokeColorRGB(0, 0, 0)
    c.rect(x0, y0 - CARD_H, CARD_W, CARD_H)

    top = y0

    # --- Header ---
    header_h = 20 * mm
    c.setLineWidth(0.75)
    c.line(x0, top - header_h, x0 + CARD_W, top - header_h)

    logo_path = school_info.get("logo_path", "")
    text_x = x0 + 6 * mm
    if logo_path and os.path.exists(logo_path):
        try:
            img = ImageReader(logo_path)
            c.drawImage(img, x0 + 4 * mm, top - header_h + 3 * mm, width=14 * mm, height=14 * mm,
                        preserveAspectRatio=True, mask='auto')
            text_x = x0 + 22 * mm
        except Exception:
            pass

    c.setFont("Helvetica-Bold", 13)
    c.drawString(text_x, top - 8 * mm, school_info.get("school_name", "SCHOOL NAME"))
    c.setFont("Helvetica", 8)
    c.drawString(text_x, top - 12.5 * mm, school_info.get("address", ""))
    c.setFont("Helvetica-Bold", 9)
    c.drawString(text_x, top - 17 * mm, school_info.get("board_name", ""))
    if school_info.get("affiliation_no"):
        c.setFont("Helvetica", 7)
        c.drawRightString(x0 + CARD_W - 4 * mm, top - 6 * mm,
                           f"Affiliation No: {school_info.get('affiliation_no')}")

    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(x0 + CARD_W / 2, top - header_h - 6 * mm, "ADMIT CARD")

    exam_type = (school_info.get("exam_type") or "").strip()
    if exam_type:
        c.setFont("Helvetica-Bold", 8.5)
        c.drawCentredString(x0 + CARD_W / 2, top - header_h - 10.5 * mm, exam_type)

    # Extra vertical offset to make room for the exam-type line, if present
    exam_type_offset = 5 * mm if exam_type else 0 * mm

    # --- Photo box (top right) ---
    photo_w, photo_h = 26 * mm, 32 * mm
    photo_x = x0 + CARD_W - photo_w - 5 * mm
    photo_y = top - header_h - photo_h - 3 * mm - exam_type_offset
    photo_path = student.get("photo_path", "")
    if photo_path and os.path.exists(photo_path):
        try:
            img = ImageReader(photo_path)
            c.drawImage(img, photo_x, photo_y, width=photo_w, height=photo_h,
                        preserveAspectRatio=True, anchor='c', mask='auto')
            c.rect(photo_x, photo_y, photo_w, photo_h)
        except Exception:
            _draw_placeholder_photo(c, photo_x, photo_y, photo_w, photo_h)
    else:
        _draw_placeholder_photo(c, photo_x, photo_y, photo_w, photo_h)

    # --- Student details ---
    detail_x = x0 + 6 * mm
    detail_y_start = top - header_h - 12 * mm - exam_type_offset
    line_gap = 6.5 * mm

    fields = [
        ("Student Name", student.get("name", "")),
        ("Roll No.", student.get("roll_no", "")),
        ("Class / Section", student.get("class_section", "")),
        ("Father's Name", student.get("father_name", "")),
        ("Mother's Name", student.get("mother_name", "")),
        ("Date of Birth", student.get("dob", "")),
        ("Exam Center", student.get("exam_center", "")),
    ]

    # Info-box watermark: the faded/blurred school logo filling the details
    # area, drawn first so the text above renders on top of it.
    info_box_top = top - header_h - exam_type_offset
    info_box_bottom = detail_y_start - len(fields) * line_gap - 4 * mm
    _draw_watermark(
        c,
        cx=x0 + CARD_W / 2,
        cy=(info_box_top + info_box_bottom) / 2,
        max_w=CARD_W - 10 * mm,
        max_h=info_box_top - info_box_bottom - 4 * mm,
        logo_path=logo_path,
    )

    detail_y = detail_y_start
    c.setFont("Helvetica-Bold", 9)
    for label, value in fields:
        c.setFont("Helvetica-Bold", 9)
        c.drawString(detail_x, detail_y, f"{label}:")
        c.setFont("Helvetica", 9)
        c.drawString(detail_x + 32 * mm, detail_y, str(value))
        detail_y -= line_gap

    # --- Subjects table ---
    table_top = detail_y - 4 * mm
    table_x = x0 + 4 * mm
    table_w = CARD_W - 8 * mm
    col_widths = [table_w * 0.18, table_w * 0.42, table_w * 0.20, table_w * 0.20]
    row_h = 6 * mm

    headers = ["Code", "Subject", "Date", "Time"]
    c.setFont("Helvetica-Bold", 8)
    cx = table_x
    header_y = table_top
    c.rect(table_x, header_y - row_h, table_w, row_h)
    for i, h in enumerate(headers):
        c.drawString(cx + 2, header_y - row_h + 2, h)
        cx += col_widths[i]

    c.setFont("Helvetica", 8)
    row_y = header_y - row_h
    max_rows = min(len(subjects), 5)
    for s in subjects[:max_rows]:
        row_y -= row_h
        cx = table_x
        c.rect(table_x, row_y, table_w, row_h)
        vals = [s.get("subject_code", ""), s.get("subject_name", ""),
                s.get("exam_date", ""), s.get("exam_time", "")]
        for i, v in enumerate(vals):
            c.drawString(cx + 2, row_y + 2, str(v))
            cx += col_widths[i]
        # vertical column separators
    # vertical lines across the whole table block
    total_h = row_h * (max_rows + 1)
    cx = table_x
    for w in col_widths[:-1]:
        cx += w
        c.line(cx, header_y - total_h, cx, header_y)

    # --- Signature area ---
    sig_y = y0 - CARD_H + 14 * mm
    sig_path = school_info.get("signature_path", "")
    if sig_path and os.path.exists(sig_path):
        try:
            img = ImageReader(sig_path)
            c.drawImage(img, x0 + CARD_W - 45 * mm, sig_y, width=30 * mm, height=10 * mm,
                        preserveAspectRatio=True, mask='auto')
        except Exception:
            pass
    c.line(x0 + CARD_W - 45 * mm, sig_y - 1 * mm, x0 + CARD_W - 8 * mm, sig_y - 1 * mm)
    c.setFont("Helvetica", 7)
    c.drawCentredString(x0 + CARD_W - 26.5 * mm, sig_y - 5 * mm,
                         school_info.get("principal_name", "") or "Principal's Signature")

    c.setFont("Helvetica", 7)
    c.drawString(x0 + 6 * mm, sig_y - 5 * mm, "Student's Signature: ______________________")

    # Instructions footer
    c.setFont("Helvetica-Oblique", 6.5)
    c.drawString(x0 + 4 * mm, y0 - CARD_H + 4 * mm,
                 "Bring this admit card to every exam. No entry without admit card & school ID.")


DEFAULT_INSTRUCTIONS = [
    "Candidates must bring this admit card to the examination center on every day of the examination.",
    "Report to the exam center at least 30 minutes before the scheduled reporting time.",
    "This admit card must be carried along with a valid school ID card; entry will not be allowed without both.",
    "Mobile phones, smart watches, calculators, or any other electronic/communication device are strictly prohibited inside the examination hall.",
    "Candidates must occupy only the seat allotted to them and must not exchange stationery or any material during the exam.",
    "Any change in the exam date, time, or center will be communicated separately; candidates are advised to check regularly.",
    "Tampering, altering, or defacing this admit card in any manner will lead to cancellation of candidature.",
    "Candidates found using unfair means during the examination will be disqualified as per the institution's examination rules.",
]


def _draw_instructions(c, x0, y_top, width, instructions=None):
    """
    Draws an 'Instructions for Candidates' block starting at y_top (the top
    edge of the block) spanning `width`, immediately below the admit card.
    Returns the y-coordinate of the bottom of the block.
    """
    if isinstance(instructions, str):
        # Saved instructions come from the UI as one instruction per line.
        instructions = [line.strip() for line in instructions.splitlines() if line.strip()]

    instructions = instructions or DEFAULT_INSTRUCTIONS

    heading_font_size = 9
    body_font_size = 7.5
    line_gap = 3.6 * mm
    wrap_indent = 5 * mm
    bullet_indent = 4 * mm

    y = y_top

    c.setFont("Helvetica-Bold", heading_font_size)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(x0, y, "Instructions for Candidates:")
    y -= line_gap + 1 * mm

    c.setFont("Helvetica", body_font_size)
    max_width = width - wrap_indent

    for idx, instruction in enumerate(instructions, start=1):
        prefix = f"{idx}. "
        text = prefix + instruction

        # simple word-wrap to fit within max_width
        words = text.split()
        line = ""
        wrapped_lines = []
        for word in words:
            trial = f"{line} {word}".strip()
            if c.stringWidth(trial, "Helvetica", body_font_size) <= max_width:
                line = trial
            else:
                if line:
                    wrapped_lines.append(line)
                line = word
        if line:
            wrapped_lines.append(line)

        for i, wline in enumerate(wrapped_lines):
            indent = 0 if i == 0 else bullet_indent
            c.drawString(x0 + indent, y, wline)
            y -= line_gap

    return y


def _subjects_for_student(subjects, student):
    """
    Returns only the subjects that apply to this student: subjects with no
    class_section (common to all classes) plus any whose class_section
    matches the student's class_section (case-insensitive, trimmed).
    """
    student_class = (student.get("class_section") or "").strip().lower()
    matched = []
    for s in subjects:
        subject_class = (s.get("class_section") or "").strip().lower()
        if not subject_class or subject_class == student_class:
            matched.append(s)
    return matched


def generate_admit_cards_pdf(students, school_info, subjects, output_path):
    """
    Generates a single PDF with one admit card per page (per student).
    students: list of student dicts
    school_info: dict
    subjects: list of subject dicts. Each may optionally carry a
        'class_section' - if set, that subject only appears on admit cards
        for students in that class; if blank, it appears for every student.
    output_path: path to save the PDF
    """
    c = canvas.Canvas(output_path, pagesize=A4)
    page_w, page_h = A4
    margin_x = (page_w - CARD_W) / 2
    margin_y = (page_h - CARD_H) / 2 + CARD_H  # top-left y of the card

    instructions = school_info.get("instructions") or None

    for student in students:
        student_subjects = _subjects_for_student(subjects, student)
        _draw_card(c, margin_x, margin_y, student, school_info, student_subjects)

        # Instructions block, printed just below the admit card on the same page
        instr_top = margin_y - CARD_H - 10 * mm
        _draw_instructions(c, margin_x, instr_top, CARD_W, instructions)

        c.showPage()

    c.save()
    return output_path


def generate_single_admit_card(student, school_info, subjects, output_path):
    return generate_admit_cards_pdf([student], school_info, subjects, output_path)
