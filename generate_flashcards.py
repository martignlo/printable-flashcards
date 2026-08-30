#!/usr/bin/env python3
"""
Generate printable, double-sided flashcards from a CSV file.

Positional arguments:
    csv_path: Path to CSV file (Column 1 = Front, Column 2 = Rear)
    cards_per_page: Number of cards per page (e.g. 2, 4, 6, 8, 9, 10, 12)
    output_pdf: Path to output PDF file
"""

import argparse
import csv
import math
import sys
from typing import List, Optional, Tuple

from reportlab.lib import pagesizes
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph


def parse_grid_dimensions(cards_per_page: int) -> Tuple[int, int]:
    """
    Determine the optimal (rows, cols) for a given number of cards per page
    for a portrait-oriented page.
    """
    if cards_per_page <= 0:
        raise ValueError("cards_per_page must be a positive integer.")

    # Known optimal presets for standard portrait pages
    presets = {
        1: (1, 1),
        2: (2, 1),
        3: (3, 1),
        4: (2, 2),
        6: (3, 2),
        8: (4, 2),
        9: (3, 3),
        10: (5, 2),
        12: (4, 3),
        14: (7, 2),
        15: (5, 3),
        16: (4, 4),
        18: (6, 3),
        20: (5, 4),
        24: (6, 4),
    }

    if cards_per_page in presets:
        return presets[cards_per_page]

    # Find factor pair (r, c) such that r * c == cards_per_page
    # and r >= c with aspect ratio closest to standard page ratio (~1.3 - 1.4)
    best_pair = None
    best_diff = float("inf")
    for c in range(1, int(math.isqrt(cards_per_page)) + 1):
        if cards_per_page % c == 0:
            r = cards_per_page // c
            # We prefer portrait grids where rows >= cols
            diff = abs((r / c) - 1.35)
            if diff < best_diff:
                best_diff = diff
                best_pair = (r, c)

    if best_pair:
        return best_pair

    # If prime number, arrange in a single column
    return (cards_per_page, 1)


def read_flashcards_csv(csv_path: str, has_header: Optional[bool] = None) -> List[Tuple[str, str]]:
    """
    Read flashcards from a CSV file.
    Returns list of (front_text, rear_text) tuples.
    """
    cards = []
    with open(csv_path, mode="r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        rows = [row for row in reader if row and any(cell.strip() for cell in row)]

    if not rows:
        return []

    # Auto-detect header if not specified
    start_idx = 0
    if has_header is None:
        first_row = [cell.strip().lower() for cell in rows[0]]
        # Common header keywords
        header_keywords = {"front", "rear", "back", "question", "answer", "term", "definition", "side a", "side b"}
        if len(first_row) >= 2 and (first_row[0] in header_keywords or first_row[1] in header_keywords):
            start_idx = 1
    elif has_header:
        start_idx = 1

    for row_num, row in enumerate(rows[start_idx:], start=start_idx + 1):
        if len(row) < 2:
            front = row[0].strip() if len(row) == 1 else ""
            rear = ""
        else:
            front = row[0].strip()
            rear = row[1].strip()
        cards.append((front, rear))

    return cards


def draw_card_content(
    canv: canvas.Canvas,
    text: str,
    x: float,
    y: float,
    width: float,
    height: float,
    padding: float = 10.0,
    max_font_size: float = 18.0,
    min_font_size: float = 7.0,
    font_name: str = "Helvetica",
):
    """
    Draw text inside the card bounded by (x, y, width, height) with auto-scaling
    and vertical & horizontal centering.
    """
    available_width = max(width - 2 * padding, 10)
    available_height = max(height - 2 * padding, 10)

    # Clean up newlines for ReportLab Paragraph (<br/> tag)
    formatted_text = text.replace("\r\n", "\n").replace("\r", "\n")
    html_text = "<br/>".join(formatted_text.split("\n"))

    # Iteratively reduce font size until paragraph fits inside available bounds
    current_font_size = max_font_size
    p = None
    w, h = 0, 0

    while current_font_size >= min_font_size:
        leading = current_font_size * 1.25
        style = ParagraphStyle(
            name=f"CardStyle_{current_font_size}",
            fontName=font_name,
            fontSize=current_font_size,
            leading=leading,
            alignment=1,  # Centered
            textColor=HexColor("#1A1A1A"),
        )
        p = Paragraph(html_text, style)
        w, h = p.wrap(available_width, available_height)
        if h <= available_height:
            break
        current_font_size -= 1.0

    if p is not None:
        # Calculate centered Y position
        # In reportlab: drawOn(canvas, x, y) puts baseline/bottom-left at y
        draw_x = x + padding
        draw_y = y + (height - h) / 2.0
        p.drawOn(canv, draw_x, draw_y)


def draw_cut_borders(
    canv: canvas.Canvas,
    x: float,
    y: float,
    width: float,
    height: float,
    border_style: str = "dashed",
):
    """Draw border or cutting guidelines for a single card cell."""
    canv.saveState()
    if border_style == "dashed":
        canv.setStrokeColor(HexColor("#B0B0B0"))
        canv.setLineWidth(0.6)
        canv.setDash(4, 3)
        canv.rect(x, y, width, height, stroke=1, fill=0)
    elif border_style == "solid":
        canv.setStrokeColor(HexColor("#CCCCCC"))
        canv.setLineWidth(0.5)
        canv.rect(x, y, width, height, stroke=1, fill=0)
    elif border_style == "crop-marks":
        canv.setStrokeColor(HexColor("#888888"))
        canv.setLineWidth(0.5)
        mark_len = 8.0
        # Draw corner crop marks
        # Bottom-left
        canv.line(x, y, x + mark_len, y)
        canv.line(x, y, x, y + mark_len)
        # Bottom-right
        canv.line(x + width, y, x + width - mark_len, y)
        canv.line(x + width, y, x + width, y + mark_len)
        # Top-left
        canv.line(x, y + height, x + mark_len, y + height)
        canv.line(x, y + height, x, y + height - mark_len)
        # Top-right
        canv.line(x + width, y + height, x + width - mark_len, y + height)
        canv.line(x + width, y + height, x + width, y + height - mark_len)
    canv.restoreState()


def create_flashcards_pdf(
    csv_path: str,
    cards_per_page: int,
    output_pdf: str,
    page_size_name: str = "letter",
    rows: Optional[int] = None,
    cols: Optional[int] = None,
    margin_in_inches: float = 0.5,
    border_style: str = "dashed",
    duplex_flip: str = "long-edge",
    max_font_size: float = 18.0,
    has_header: Optional[bool] = None,
):
    """
    Main function to generate the PDF flashcards.
    """
    cards = read_flashcards_csv(csv_path, has_header=has_header)
    if not cards:
        print(f"Warning: No flashcard records found in {csv_path}", file=sys.stderr)
        cards = []

    # Get page size
    page_size_map = {
        "letter": pagesizes.LETTER,
        "a4": pagesizes.A4,
        "legal": pagesizes.LEGAL,
    }
    page_size = page_size_map.get(page_size_name.lower(), pagesizes.LETTER)
    page_width, page_height = page_size

    # Grid calculation
    if rows is not None and cols is not None:
        if rows * cols != cards_per_page:
            print(
                f"Note: Provided grid ({rows}x{cols}={rows*cols}) overrides cards_per_page ({cards_per_page}).",
                file=sys.stderr,
            )
            cards_per_page = rows * cols
        grid_rows, grid_cols = rows, cols
    else:
        grid_rows, grid_cols = parse_grid_dimensions(cards_per_page)

    margin = margin_in_inches * inch
    usable_width = page_width - (2 * margin)
    usable_height = page_height - (2 * margin)

    card_width = usable_width / grid_cols
    card_height = usable_height / grid_rows

    canv = canvas.Canvas(output_pdf, pagesize=page_size)

    total_cards = len(cards)
    total_pages = math.ceil(total_cards / cards_per_page) if total_cards > 0 else 1

    for page_idx in range(total_pages):
        start_card_idx = page_idx * cards_per_page
        page_cards = cards[start_card_idx : start_card_idx + cards_per_page]

        # --- 1. FRONT PAGE ---
        for slot_idx, card in enumerate(page_cards):
            r = slot_idx // grid_cols  # 0 is top row
            c = slot_idx % grid_cols   # 0 is left column

            # In PDF coordinates, (0,0) is bottom-left
            card_x = margin + c * card_width
            card_y = page_height - margin - (r + 1) * card_height

            if border_style != "none":
                draw_cut_borders(canv, card_x, card_y, card_width, card_height, border_style)

            draw_card_content(
                canv,
                card[0],
                card_x,
                card_y,
                card_width,
                card_height,
                padding=8.0,
                max_font_size=max_font_size,
            )

        canv.showPage()

        # --- 2. BACK PAGE (DUPLEX MIRRORED) ---
        for slot_idx, card in enumerate(page_cards):
            r = slot_idx // grid_cols
            c = slot_idx % grid_cols

            # Mirror columns for long-edge duplex (flip on long edge / portrait)
            if duplex_flip == "long-edge":
                mirrored_c = (grid_cols - 1) - c
                mirrored_r = r
            elif duplex_flip == "short-edge":
                mirrored_c = c
                mirrored_r = (grid_rows - 1) - r
            else:  # none / simplex
                mirrored_c = c
                mirrored_r = r

            card_x = margin + mirrored_c * card_width
            card_y = page_height - margin - (mirrored_r + 1) * card_height

            if border_style != "none":
                draw_cut_borders(canv, card_x, card_y, card_width, card_height, border_style)

            draw_card_content(
                canv,
                card[1],
                card_x,
                card_y,
                card_width,
                card_height,
                padding=8.0,
                max_font_size=max_font_size,
            )

        canv.showPage()

    canv.save()
    print(f"Successfully generated '{output_pdf}' ({total_cards} cards across {total_pages * 2} pages).")


def main():
    parser = argparse.ArgumentParser(
        description="Generate printable double-sided flashcards in PDF format from a CSV file."
    )
    parser.add_argument("csv_path", help="Path to CSV file with flashcard text (col 1: front, col 2: rear)")
    parser.add_argument("cards_per_page", type=int, help="Number of flashcards to place on each page (e.g. 4, 8, 10)")
    parser.add_argument("output_pdf", help="Path of the generated output PDF file")

    parser.add_argument(
        "--page-size",
        choices=["letter", "a4", "legal"],
        default="letter",
        help="Paper size for printing (default: letter)",
    )
    parser.add_argument(
        "--grid",
        type=str,
        default=None,
        help="Custom grid layout as ROWSxCOLS (e.g. '4x2', '3x3'). Overrides default auto-grid.",
    )
    parser.add_argument(
        "--margin",
        type=float,
        default=0.5,
        help="Page margin in inches (default: 0.5)",
    )
    parser.add_argument(
        "--border-style",
        choices=["dashed", "solid", "crop-marks", "none"],
        default="dashed",
        help="Cutting guide style around each card (default: dashed)",
    )
    parser.add_argument(
        "--flip",
        dest="duplex_flip",
        choices=["long-edge", "short-edge", "none"],
        default="long-edge",
        help="Duplex printing alignment flip direction (default: long-edge)",
    )
    parser.add_argument(
        "--font-size",
        type=float,
        default=18.0,
        help="Maximum font size in points (default: 18.0)",
    )
    parser.add_argument(
        "--has-header",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Explicitly indicate whether CSV contains a header row (auto-detected by default)",
    )

    args = parser.parse_args()

    rows, cols = None, None
    if args.grid:
        try:
            parts = args.grid.lower().split("x")
            rows, cols = int(parts[0]), int(parts[1])
        except Exception:
            parser.error("--grid must be in the format ROWSxCOLS, e.g. '4x2'")

    create_flashcards_pdf(
        csv_path=args.csv_path,
        cards_per_page=args.cards_per_page,
        output_pdf=args.output_pdf,
        page_size_name=args.page_size,
        rows=rows,
        cols=cols,
        margin_in_inches=args.margin,
        border_style=args.border_style,
        duplex_flip=args.duplex_flip,
        max_font_size=args.font_size,
        has_header=args.has_header,
    )


if __name__ == "__main__":
    main()
