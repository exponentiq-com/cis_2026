# -*- coding: utf-8 -*-
"""CIS 2026 client guide — real screenshots + plain callouts."""
from __future__ import annotations

import math
from pathlib import Path

from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

OUT = Path(__file__).resolve().parent / "CIS_2026_Client_Dashboard_Guide.pdf"
ASSETS = Path(
    r"C:\Users\hp\.cursor\projects\c-Users-hp-Downloads-18-09-2026-18-09-2026\assets"
)

# User-provided screenshots (this turn)
IMG = {
    "login": ASSETS
    / "c__Users_hp_AppData_Roaming_Cursor_User_workspaceStorage_d80ffebb1b675d579c0fdc62d5b1cd67_images_image-2c2d63b3-5931-4965-912d-4cd943b0059b.png",
    "demo_table": ASSETS
    / "c__Users_hp_AppData_Roaming_Cursor_User_workspaceStorage_d80ffebb1b675d579c0fdc62d5b1cd67_images_image-07a1806c-903d-42b6-8152-bf714877cf5d.png",
    "cross_tab": ASSETS
    / "c__Users_hp_AppData_Roaming_Cursor_User_workspaceStorage_d80ffebb1b675d579c0fdc62d5b1cd67_images_image-551fdd75-491f-4a5d-b70e-6e9e09792cb3.png",
    "survey_summary": ASSETS
    / "c__Users_hp_AppData_Roaming_Cursor_User_workspaceStorage_d80ffebb1b675d579c0fdc62d5b1cd67_images_image-0e007f9b-3244-4b16-90c9-51a3912bab04.png",
    "survey_mix": ASSETS
    / "c__Users_hp_AppData_Roaming_Cursor_User_workspaceStorage_d80ffebb1b675d579c0fdc62d5b1cd67_images_image-8094efb2-1fb6-4999-a036-0ba743dfdb74.png",
    "breakdown": ASSETS
    / "c__Users_hp_AppData_Roaming_Cursor_User_workspaceStorage_d80ffebb1b675d579c0fdc62d5b1cd67_images_image-e095c608-99fd-4842-a87d-4082112495d3.png",
}

LINK = "https://cis2026-survey.streamlit.app"
USER = "xxxxx"
PASS = "xxxxx"

W, H = A4
INK = HexColor("#1F2A2E")
SLATE = HexColor("#3D4F56")
TEAL = HexColor("#2F6F6A")
NAVY = HexColor("#1B3A5F")
GOLD = HexColor("#C4A035")
PAPER = HexColor("#F7F5F1")
RED = HexColor("#C0392B")
BOX_BG = HexColor("#FFF8F0")


def wrap(text: str, max_w: float, c: canvas.Canvas, font="Helvetica", size=9) -> list[str]:
    words = text.split()
    lines, cur = [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if c.stringWidth(test, font, size) <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines or [""]


def arrow(c: canvas.Canvas, x1, y1, x2, y2, color=RED, width=1.8):
    c.setStrokeColor(color)
    c.setFillColor(color)
    c.setLineWidth(width)
    c.line(x1, y1, x2, y2)
    ang = math.atan2(y2 - y1, x2 - x1)
    size = 7
    a1 = ang + math.pi * 0.82
    a2 = ang - math.pi * 0.82
    path = c.beginPath()
    path.moveTo(x2, y2)
    path.lineTo(x2 + size * math.cos(a1), y2 + size * math.sin(a1))
    path.lineTo(x2 + size * math.cos(a2), y2 + size * math.sin(a2))
    path.close()
    c.drawPath(path, fill=1, stroke=0)


def badge(c: canvas.Canvas, n: int, x, y, r=7):
    c.setFillColor(RED)
    c.circle(x, y, r, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(x, y - 2.5, str(n))


def header(c: canvas.Canvas, page: int, total: int, title: str):
    c.setFillColor(PAPER)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFillColor(NAVY)
    c.rect(0, H - 14 * mm, W, 14 * mm, fill=1, stroke=0)
    c.setFillColor(GOLD)
    c.rect(0, H - 14 * mm, 3 * mm, 14 * mm, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(10 * mm, H - 8.5 * mm, "CIS 2026 · How to use the dashboard")
    c.setFont("Helvetica", 8.5)
    c.drawRightString(W - 10 * mm, H - 8.5 * mm, f"{page} / {total}")
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(10 * mm, H - 24 * mm, title)


def footer(c: canvas.Canvas):
    c.setFillColor(SLATE)
    c.setFont("Helvetica", 7)
    c.drawString(10 * mm, 6 * mm, "Confidential · For authorised readers only")


def draw_image(c: canvas.Canvas, path: Path, x, y, max_w, max_h):
    """Draw image fitted inside box; return (x, y, w, h) used."""
    ir = ImageReader(str(path))
    iw, ih = ir.getSize()
    scale = min(max_w / iw, max_h / ih)
    w, h = iw * scale, ih * scale
    c.drawImage(ir, x, y, width=w, height=h, preserveAspectRatio=True, mask="auto")
    # thin border
    c.setStrokeColor(HexColor("#C9C1B4"))
    c.setLineWidth(0.6)
    c.rect(x, y, w, h, fill=0, stroke=1)
    return x, y, w, h


def note_row(c: canvas.Canvas, n: int, text: str, x, y, max_w):
    badge(c, n, x + 6, y + 3)
    c.setFillColor(INK)
    c.setFont("Helvetica", 8.5)
    lines = wrap(text, max_w - 14, c, "Helvetica", 8.5)
    yy = y
    for i, ln in enumerate(lines):
        c.drawString(x + 16, yy if i == 0 else yy, ln)
        yy -= 11
    return 8 + 11 * len(lines)


def page_cover(c, page, total):
    header(c, page, total, "Start here")
    y = H - 34 * mm
    c.setFillColor(SLATE)
    c.setFont("Helvetica", 10)
    for ln in wrap(
        "This short guide shows how to open the dashboard and read the screens. "
        "Follow the steps in order. Numbers on the pictures match the notes.",
        W - 20 * mm,
        c,
        "Helvetica",
        10,
    ):
        c.drawString(10 * mm, y, ln)
        y -= 13

    # Link
    c.setFillColor(NAVY)
    c.roundRect(10 * mm, y - 42 * mm, W - 20 * mm, 40 * mm, 5, fill=1, stroke=0)
    c.setFillColor(GOLD)
    c.rect(10 * mm, y - 42 * mm, 3 * mm, 40 * mm, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(16 * mm, y - 10 * mm, "Step 1 — Open this link")
    c.setFont("Helvetica", 9)
    c.drawString(16 * mm, y - 18 * mm, "Copy and paste into Chrome or Edge:")
    c.setFillColor(HexColor("#E8EEF4"))
    c.roundRect(16 * mm, y - 32 * mm, W - 36 * mm, 10 * mm, 3, fill=1, stroke=0)
    c.setFillColor(NAVY)
    c.setFont("Courier-Bold", 10)
    c.drawString(18 * mm, y - 28.5 * mm, LINK)

    y = y - 52 * mm
    c.setFillColor(white)
    c.setStrokeColor(TEAL)
    c.setLineWidth(1.4)
    c.roundRect(10 * mm, y - 40 * mm, W - 20 * mm, 40 * mm, 5, fill=1, stroke=1)
    c.setFillColor(TEAL)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(16 * mm, y - 10 * mm, "Step 2 — Sign-in details")
    c.setFillColor(INK)
    c.setFont("Helvetica", 10)
    c.drawString(16 * mm, y - 20 * mm, "On the next screen, enter:")
    c.setFont("Courier-Bold", 12)
    c.drawString(16 * mm, y - 30 * mm, f"Username:  {USER}")
    c.drawString(16 * mm, y - 38 * mm, f"Password:  {PASS}")

    y = y - 55 * mm
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(10 * mm, y, "What you will see next")
    c.setFont("Helvetica", 9)
    c.setFillColor(SLATE)
    items = [
        "Demographic profiles — who answered the survey",
        "Survey findings — what they said, country by country",
        "Filters — narrow by gender, age, area, education, income",
        "Charts + tables — same numbers, two ways to read them",
    ]
    y -= 14
    for it in items:
        c.drawString(12 * mm, y, "•  " + it)
        y -= 12

    footer(c)
    c.showPage()


def page_login(c, page, total):
    header(c, page, total, "Step 3 — Sign-in screen")
    c.setFillColor(SLATE)
    c.setFont("Helvetica", 9)
    c.drawString(10 * mm, H - 32 * mm, "This is the first screen after you open the link.")

    ix, iy, iw, ih = draw_image(
        c, IMG["login"], 10 * mm, 55 * mm, W - 20 * mm, 115 * mm
    )

    # callouts pointing into image (approx positions as % of image)
    # username field ~ mid-left of form
    badge(c, 1, ix + iw * 0.18, iy + ih * 0.58)
    arrow(c, ix + iw * 0.18 + 8, iy + ih * 0.58, ix + iw * 0.35, iy + ih * 0.55)
    badge(c, 2, ix + iw * 0.18, iy + ih * 0.42)
    arrow(c, ix + iw * 0.18 + 8, iy + ih * 0.42, ix + iw * 0.35, iy + ih * 0.40)
    badge(c, 3, ix + iw * 0.18, iy + ih * 0.28)
    arrow(c, ix + iw * 0.18 + 8, iy + ih * 0.28, ix + iw * 0.28, iy + ih * 0.30)

    y = 48 * mm
    y -= note_row(c, 1, "Type your Username here.", 10 * mm, y, W - 20 * mm)
    y -= 4
    y -= note_row(c, 2, "Type your Password here.", 10 * mm, y, W - 20 * mm)
    y -= 4
    y -= note_row(c, 3, "Click Sign in.", 10 * mm, y, W - 20 * mm)
    y -= 6
    c.setFillColor(SLATE)
    c.setFont("Helvetica", 8)
    c.drawString(10 * mm, y, "If it says incorrect username or password, check Caps Lock and try again.")
    footer(c)
    c.showPage()


def page_demo(c, page, total):
    header(c, page, total, "Step 4 — Demographic profiles (who answered)")
    c.setFillColor(SLATE)
    c.setFont("Helvetica", 9)
    for ln in wrap(
        "After login you land here. Use the left panel to choose Section and Countries.",
        W - 20 * mm,
        c,
        "Helvetica",
        9,
    ):
        c.drawString(10 * mm, H - 32 * mm, ln)

    ix, iy, iw, ih = draw_image(
        c, IMG["demo_table"], 8 * mm, 58 * mm, W - 16 * mm, 118 * mm
    )

    # 1 Section radio
    badge(c, 1, ix + iw * 0.08, iy + ih * 0.78)
    # 2 Countries
    badge(c, 2, ix + iw * 0.08, iy + ih * 0.55)
    # 3 Country profile tab
    badge(c, 3, ix + iw * 0.32, iy + ih * 0.62)
    # 4 Table
    badge(c, 4, ix + iw * 0.55, iy + ih * 0.40)

    y = 52 * mm
    bits = [
        (1, "Section → Demographic profiles = sample makeup (gender, age, education…)."),
        (2, "Countries → tick which countries to include. Select all / Unselect all for speed."),
        (3, "Country profile tab → one summary row per country (N, Male%, Urban%, etc.)."),
        (4, "Table numbers → scroll down for Demographic charts under the table."),
    ]
    for n, t in bits:
        y -= note_row(c, n, t, 8 * mm, y, W - 16 * mm)
        y -= 2
    footer(c)
    c.showPage()


def page_cross(c, page, total):
    header(c, page, total, "Step 5 — Cross-tab (two demographics together)")
    c.setFillColor(SLATE)
    c.setFont("Helvetica", 9)
    c.drawString(
        10 * mm,
        H - 32 * mm,
        "Still in Demographic profiles. Click the Cross-tab tab.",
    )

    ix, iy, iw, ih = draw_image(
        c, IMG["cross_tab"], 8 * mm, 62 * mm, W - 16 * mm, 115 * mm
    )

    badge(c, 1, ix + iw * 0.38, iy + ih * 0.62)
    badge(c, 2, ix + iw * 0.42, iy + ih * 0.48)
    badge(c, 3, ix + iw * 0.58, iy + ih * 0.48)
    badge(c, 4, ix + iw * 0.78, iy + ih * 0.48)
    badge(c, 5, ix + iw * 0.42, iy + ih * 0.38)

    y = 56 * mm
    bits = [
        (1, "Cross-tab tab — switch from Country profile."),
        (2, "Rows — first demographic (example: Gender)."),
        (3, "Columns — second demographic (example: Age group)."),
        (4, "Country — All countries, or one country only."),
        (5, "Show — Row % (shares) or Counts (raw numbers)."),
    ]
    for n, t in bits:
        y -= note_row(c, n, t, 8 * mm, y, W - 16 * mm)
        y -= 1
    footer(c)
    c.showPage()


def page_survey(c, page, total):
    header(c, page, total, "Step 6 — Survey findings (what people said)")
    c.setFillColor(SLATE)
    c.setFont("Helvetica", 9)
    for ln in wrap(
        "On the left, change Section to Survey findings. Then set filters and pick a question.",
        W - 20 * mm,
        c,
        "Helvetica",
        9,
    ):
        c.drawString(10 * mm, H - 32 * mm, ln)

    ix, iy, iw, ih = draw_image(
        c, IMG["survey_summary"], 8 * mm, 58 * mm, W - 16 * mm, 115 * mm
    )

    badge(c, 1, ix + iw * 0.10, iy + ih * 0.82)
    badge(c, 2, ix + iw * 0.10, iy + ih * 0.45)
    badge(c, 3, ix + iw * 0.45, iy + ih * 0.78)
    badge(c, 4, ix + iw * 0.45, iy + ih * 0.58)
    badge(c, 5, ix + iw * 0.55, iy + ih * 0.22)

    y = 52 * mm
    bits = [
        (1, "Section → Survey findings."),
        (2, "Filters (Gender, Age, Urban/rural, Education, Income) — leave All to see everyone."),
        (3, "Top cards — how many respondents / countries / languages are in view now."),
        (4, "Question box — shows the exact question wording."),
        (5, "Bars = country results. Dotted grey line = average across countries in view."),
    ]
    for n, t in bits:
        y -= note_row(c, n, t, 8 * mm, y, W - 16 * mm)
        y -= 1
    footer(c)
    c.showPage()


def page_mix(c, page, total):
    header(c, page, total, "Step 7 — Chart view & choosing a question")
    c.setFillColor(SLATE)
    c.setFont("Helvetica", 9)
    c.drawString(
        10 * mm,
        H - 32 * mm,
        "Scroll further down the left panel to pick the question and chart type.",
    )

    ix, iy, iw, ih = draw_image(
        c, IMG["survey_mix"], 8 * mm, 58 * mm, W - 16 * mm, 115 * mm
    )

    badge(c, 1, ix + iw * 0.12, iy + ih * 0.55)
    badge(c, 2, ix + iw * 0.12, iy + ih * 0.42)
    badge(c, 3, ix + iw * 0.12, iy + ih * 0.28)
    badge(c, 4, ix + iw * 0.55, iy + ih * 0.35)

    y = 52 * mm
    bits = [
        (1, "Questionnaire section — e.g. General impressions."),
        (2, "Question — e.g. Q2. Interest in China."),
        (
            3,
            "Chart view → Country comparison (summary %) = one bar per country for key answers. "
            "Full answer mix by country = every answer choice shown (this screen).",
        ),
        (4, "Coloured groups = each answer option. Dotted line = average for the top answer."),
    ]
    for n, t in bits:
        y -= note_row(c, n, t, 8 * mm, y, W - 16 * mm)
        y -= 2
    footer(c)
    c.showPage()


def page_breakdown(c, page, total):
    header(c, page, total, "Step 8 — Breakdown (optional split)")
    c.setFillColor(SLATE)
    c.setFont("Helvetica", 9)
    for ln in wrap(
        "At the bottom of Survey findings: Breakdown within the filtered sample. "
        "Use only if you want to split answers inside each country.",
        W - 20 * mm,
        c,
        "Helvetica",
        9,
    ):
        c.drawString(10 * mm, H - 32 * mm, ln)
        break
    c.drawString(
        10 * mm,
        H - 42 * mm,
        "Leave Split by = None if you do not need this.",
    )

    ix, iy, iw, ih = draw_image(
        c, IMG["breakdown"], 8 * mm, 55 * mm, W - 16 * mm, 112 * mm
    )

    badge(c, 1, ix + iw * 0.35, iy + ih * 0.78)
    badge(c, 2, ix + iw * 0.55, iy + ih * 0.45)
    badge(c, 3, ix + iw * 0.45, iy + ih * 0.18)

    y = 48 * mm
    bits = [
        (1, "Split by — pick Gender, Age group, Urban/rural, Education, Income, or City."),
        (2, "Chart — for each country, bars show the share for each split group."),
        (3, "Table under the chart — same numbers (Percent and N)."),
    ]
    for n, t in bits:
        y -= note_row(c, n, t, 8 * mm, y, W - 16 * mm)
        y -= 2
    footer(c)
    c.showPage()


def page_cheat(c, page, total):
    header(c, page, total, "Cheat sheet")
    rows = [
        ("Link", LINK),
        ("Login", f"Username {USER}  ·  Password {PASS}"),
        ("Section", "Demographic profiles = who answered. Survey findings = what they said."),
        ("Countries", "Tick countries to compare. Use Select all / Unselect all."),
        ("Filters", "Only in Survey findings. Narrow who is included. All = everyone."),
        ("Question", "Pick Questionnaire section → Question → Chart view."),
        ("Summary %", "One simple bar per country for the main favourable answers."),
        ("Full mix", "Shows every answer option for each country."),
        ("Dotted line", "Average across countries currently selected."),
        ("Cross-tab", "In Demographic profiles: two demographics crossed (e.g. Gender × Age)."),
        ("Breakdown", "Optional split inside countries at the bottom of Survey findings."),
        ("No data?", "Widen filters or select more countries."),
    ]
    y = H - 36 * mm
    c.setFillColor(NAVY)
    c.rect(10 * mm, y, W - 20 * mm, 8 * mm, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 8.5)
    c.drawString(12 * mm, y + 2.5 * mm, "Item")
    c.drawString(42 * mm, y + 2.5 * mm, "What to do / what it means")
    y -= 1 * mm
    for i, (a, b) in enumerate(rows):
        y -= 10 * mm
        c.setFillColor(HexColor("#FBF9F5") if i % 2 == 0 else white)
        c.rect(10 * mm, y, W - 20 * mm, 10 * mm, fill=1, stroke=0)
        c.setFillColor(TEAL)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(12 * mm, y + 3.2 * mm, a)
        c.setFillColor(INK)
        c.setFont("Helvetica", 7.5)
        for ln in wrap(b, 145 * mm, c, "Helvetica", 7.5):
            c.drawString(42 * mm, y + 3.2 * mm, ln)
            break

    c.setFillColor(SLATE)
    c.setFont("Helvetica-Oblique", 8)
    c.drawString(10 * mm, 18 * mm, "Replace xxxxx with the real password before sending to the client.")
    footer(c)
    c.showPage()


def main():
    for k, p in IMG.items():
        if not p.exists():
            raise FileNotFoundError(f"Missing screenshot [{k}]: {p}")

    c = canvas.Canvas(str(OUT), pagesize=A4)
    c.setTitle("CIS 2026 Client Dashboard Guide")
    c.setAuthor("CIS 2026")
    pages = [
        page_cover,
        page_login,
        page_demo,
        page_cross,
        page_survey,
        page_mix,
        page_breakdown,
        page_cheat,
    ]
    total = len(pages)
    for i, fn in enumerate(pages, 1):
        fn(c, i, total)
    c.save()
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
