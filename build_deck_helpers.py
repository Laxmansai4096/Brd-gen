"""
build_deck_helpers.py
Core layout engine and helper utilities for building the 56-slide master PowerPoint deck.
Implements the Enterprise Clean Light Theme with official Tata & TCS logos, 16:9 canvas,
slide numbering, boundary boxes, and structured Presenter Notes.
"""

import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

# 16:9 Widescreen Canvas
SLIDE_WIDTH = Inches(13.333)
SLIDE_HEIGHT = Inches(7.5)

# Enterprise Clean Light Theme Color Palette
BG_LIGHT = RGBColor(248, 250, 252)        # #F8FAFC Crisp slate light
CARD_BG = RGBColor(255, 255, 255)         # Pure white card
CARD_BORDER = RGBColor(203, 213, 225)     # #CBD5E1 Slate 300
TEXT_DARK = RGBColor(15, 23, 42)          # #0F172A Slate 900
TEXT_SUB = RGBColor(51, 65, 85)           # #334155 Slate 700
TEXT_MUTED = RGBColor(100, 116, 139)      # #64748B Slate 500
TEXT_DIM = RGBColor(148, 163, 184)        # #94A3B8 Slate 400

# Accent Palette
BLUE_PRIMARY = RGBColor(2, 132, 199)      # #0284C7 Sky 600
BLUE_DARK = RGBColor(30, 58, 138)         # #1E3A8A Navy 900
EMERALD_SUCCESS = RGBColor(16, 185, 129)  # #10B981 Success green
AMBER_WARN = RGBColor(217, 119, 6)        # #D97706 Warning amber
PURPLE_ACCENT = RGBColor(126, 34, 206)    # #7E22CE Purple 700
RED_ALERT = RGBColor(220, 38, 38)         # #DC2626 Red 600
TEAL_ACCENT = RGBColor(13, 148, 136)      # #0D9488 Teal 600

TOTAL_SLIDES = 56
CLIENT_NAME = "<Enterprise Client>"
PROJECT_TITLE = "Contract Intelligence & Risk Visibility Platform"
FOOTER_CENTER = f"{CLIENT_NAME} × TCS | {PROJECT_TITLE} | TCS Confidential"

TCS_LOGO_PATH = "exports/assets/tcs_logo_black.png"
TATA_LOGO_PATH = "exports/assets/tata_logo_black.png"

def create_base_slide(prs, slide_num: int, title: str, subtitle: str, category_badge: str, notes: dict):
    """Creates a base light-themed slide with header, slide number, category badge, footer branding, and presenter notes."""
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)
    
    # 1. Background Fill
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = BG_LIGHT
    
    # 2. Header Slide Number (Top Right)
    num_box = slide.shapes.add_textbox(Inches(10.5), Inches(0.32), Inches(2.2), Inches(0.35))
    tf_n = num_box.text_frame
    p_n = tf_n.paragraphs[0]
    p_n.alignment = PP_ALIGN.RIGHT
    p_n.text = f"SLIDE {slide_num:02d} / {TOTAL_SLIDES:02d}"
    p_n.font.size = Pt(11)
    p_n.font.bold = True
    p_n.font.color.rgb = BLUE_PRIMARY
    
    # 3. Category Badge & Title Area
    header_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.32), Inches(9.6), Inches(1.05))
    tf_h = header_box.text_frame
    tf_h.word_wrap = True
    
    p_cat = tf_h.paragraphs[0]
    p_cat.text = category_badge.upper()
    p_cat.font.size = Pt(9)
    p_cat.font.bold = True
    p_cat.font.color.rgb = BLUE_PRIMARY
    
    p_title = tf_h.add_paragraph()
    p_title.text = title
    p_title.font.size = Pt(19)
    p_title.font.bold = True
    p_title.font.color.rgb = TEXT_DARK
    
    if subtitle:
        p_sub = tf_h.add_paragraph()
        p_sub.text = subtitle
        p_sub.font.size = Pt(10.5)
        p_sub.font.color.rgb = TEXT_MUTED
        
    # 4. Footer Branding & Logos
    # Left: TCS Logo (Black)
    if os.path.exists(TCS_LOGO_PATH):
        try:
            slide.shapes.add_picture(TCS_LOGO_PATH, Inches(0.8), Inches(6.92), width=Inches(1.8))
        except Exception:
            pass
            
    # Right: Tata Logo (Black)
    if os.path.exists(TATA_LOGO_PATH):
        try:
            slide.shapes.add_picture(TATA_LOGO_PATH, Inches(11.8), Inches(6.92), width=Inches(0.75))
        except Exception:
            pass
            
    # Center: Confidentiality text
    foot_box = slide.shapes.add_textbox(Inches(2.8), Inches(6.95), Inches(7.7), Inches(0.35))
    tf_f = foot_box.text_frame
    p_f = tf_f.paragraphs[0]
    p_f.alignment = PP_ALIGN.CENTER
    p_f.text = FOOTER_CENTER
    p_f.font.size = Pt(8.5)
    p_f.font.color.rgb = TEXT_MUTED
    
    # 5. Structured Presenter Notes
    notes_slide = slide.notes_slide
    text_frame = notes_slide.notes_text_frame
    notes_content = (
        f"=== PRESENTER NOTES (SLIDE {slide_num:02d} / {TOTAL_SLIDES:02d}) ===\n\n"
        f"📌 LOGIC (THE WHY):\n{notes.get('logic', 'N/A')}\n\n"
        f"📐 DESIGNS (THE WHAT):\n{notes.get('designs', 'N/A')}\n\n"
        f"⭐ HIGHLIGHTS:\n{notes.get('highlights', 'N/A')}\n\n"
        f"🔍 DETAILS:\n{notes.get('details', 'N/A')}\n"
    )
    text_frame.text = notes_content
    
    return slide

def add_card(slide, left: float, top: float, width: float, height: float, title: str, items: list, header_color=BLUE_PRIMARY, bg_color=CARD_BG, border_color=CARD_BORDER):
    """Draws an enterprise card with top header and structured bullet items."""
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
    card.fill.solid()
    card.fill.fore_color.rgb = bg_color
    card.line.color.rgb = border_color
    card.line.width = Pt(1)
    
    # Header strip inside card
    h_strip = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(left + 0.02), Inches(top + 0.02), Inches(width - 0.04), Inches(0.36))
    h_strip.fill.solid()
    h_strip.fill.fore_color.rgb = RGBColor(241, 245, 249)
    h_strip.line.fill.background()
    
    # Title Text
    tb_t = slide.shapes.add_textbox(Inches(left + 0.15), Inches(top + 0.05), Inches(width - 0.3), Inches(0.35))
    tf_t = tb_t.text_frame
    p0 = tf_t.paragraphs[0]
    p0.text = title
    p0.font.size = Pt(11)
    p0.font.bold = True
    p0.font.color.rgb = header_color
    
    # Body items
    tb = slide.shapes.add_textbox(Inches(left + 0.15), Inches(top + 0.42), Inches(width - 0.3), Inches(height - 0.48))
    tf = tb.text_frame
    tf.word_wrap = True
    
    for idx, item in enumerate(items):
        p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
        p.text = f"• {item}" if not item.startswith(" ") and not item.startswith("•") else item
        p.font.size = Pt(9.2)
        p.font.color.rgb = TEXT_SUB
        p.space_after = Pt(2.5)

def add_table(slide, left: float, top: float, width: float, height: float, headers: list, rows: list, col_widths=None):
    """Creates a clean enterprise data table with styled header and alternating row colors."""
    num_rows = len(rows) + 1
    num_cols = len(headers)
    table_shape = slide.shapes.add_table(num_rows, num_cols, Inches(left), Inches(top), Inches(width), Inches(height))
    tbl = table_shape.table
    
    if col_widths and len(col_widths) == num_cols:
        for idx, w in enumerate(col_widths):
            tbl.columns[idx].width = Inches(w)
            
    # Headers
    for c_idx, h_text in enumerate(headers):
        cell = tbl.cell(0, c_idx)
        cell.fill.solid()
        cell.fill.fore_color.rgb = RGBColor(15, 23, 42)
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = cell.text_frame.paragraphs[0]
        p.text = str(h_text)
        p.font.bold = True
        p.font.size = Pt(9.5)
        p.font.color.rgb = RGBColor(255, 255, 255)
        p.alignment = PP_ALIGN.LEFT
        
    # Rows
    for r_idx, row_vals in enumerate(rows):
        bg_col = RGBColor(255, 255, 255) if r_idx % 2 == 0 else RGBColor(248, 250, 252)
        for c_idx, val in enumerate(row_vals):
            cell = tbl.cell(r_idx + 1, c_idx)
            cell.fill.solid()
            cell.fill.fore_color.rgb = bg_col
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            p = cell.text_frame.paragraphs[0]
            p.text = str(val)
            p.font.size = Pt(8.5)
            p.font.color.rgb = TEXT_DARK
            p.alignment = PP_ALIGN.LEFT

def add_kpi_metric(slide, left: float, top: float, width: float, height: float, label: str, val: str, sub: str, color=BLUE_PRIMARY):
    """Draws a metric KPI card."""
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
    card.fill.solid()
    card.fill.fore_color.rgb = CARD_BG
    card.line.color.rgb = CARD_BORDER
    card.line.width = Pt(1)
    
    tb = slide.shapes.add_textbox(Inches(left + 0.1), Inches(top + 0.1), Inches(width - 0.2), Inches(height - 0.2))
    tf = tb.text_frame
    tf.word_wrap = True
    
    p0 = tf.paragraphs[0]
    p0.text = label.upper()
    p0.font.size = Pt(8.5)
    p0.font.bold = True
    p0.font.color.rgb = TEXT_MUTED
    
    p1 = tf.add_paragraph()
    p1.text = val
    p1.font.size = Pt(17)
    p1.font.bold = True
    p1.font.color.rgb = color
    
    p2 = tf.add_paragraph()
    p2.text = sub
    p2.font.size = Pt(8)
    p2.font.color.rgb = TEXT_SUB

def add_boundary_box(slide, left: float, top: float, width: float, height: float, title: str, subtitle: str, boundary_type: str, color=BLUE_PRIMARY, bg_color=RGBColor(248, 250, 252)):
    """Draws an architecture boundary zone (e.g. Virtual Server, Agentic Framework, Serverless Container, FaaS)."""
    box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
    box.fill.solid()
    box.fill.fore_color.rgb = bg_color
    box.line.color.rgb = color
    box.line.width = Pt(1.5)
    
    # Boundary title strip
    tb = slide.shapes.add_textbox(Inches(left + 0.15), Inches(top + 0.1), Inches(width - 0.3), Inches(0.5))
    tf = tb.text_frame
    p0 = tf.paragraphs[0]
    p0.text = f"[{boundary_type.upper()}]  {title}"
    p0.font.size = Pt(11)
    p0.font.bold = True
    p0.font.color.rgb = color
    
    if subtitle:
        p1 = tf.add_paragraph()
        p1.text = subtitle
        p1.font.size = Pt(8.5)
        p1.font.color.rgb = TEXT_MUTED

def add_image_slide(slide, image_path: str, left=0.8, top=1.45, width=11.733, height=5.25):
    """Embeds an image into the slide canvas with subtle border frame."""
    if os.path.exists(image_path):
        slide.shapes.add_picture(image_path, Inches(left), Inches(top), width=Inches(width), height=Inches(height))
    else:
        # Placeholder text if missing
        tb = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
        tf = tb.text_frame
        p = tf.paragraphs[0]
        p.text = f"[Image File Not Found: {image_path}]"
        p.font.size = Pt(14)
        p.font.color.rgb = RED_ALERT
