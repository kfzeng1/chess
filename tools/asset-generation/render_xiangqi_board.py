#!/usr/bin/env python3
from __future__ import annotations

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "assets" / "board.png"

W, H = 1800, 2000
MARGIN = 50
BOARD_PADDING = 30
GRID_LEFT = 278
GRID_TOP = 298
CELL = 156
GRID_RIGHT = GRID_LEFT + CELL * 8
GRID_BOTTOM = GRID_TOP + CELL * 9

# Modern web color palette - clean and high-contrast
BG_COLOR = (248, 245, 238, 255)  # Warm off-white
BOARD_BASE = (222, 207, 186)      # Light warm tan
BOARD_ACCENT = (198, 178, 152)    # Darker tan
GRID_LINE = (88, 76, 62, 255)     # Dark brown
GRID_ACCENT = (138, 118, 95, 255) # Medium brown
PALACE_LINE = (158, 78, 58, 255)  # Red-brown for palace
COORD_TEXT = (98, 86, 72, 220)    # Subtle text
RIVER_TEXT = (118, 98, 78, 180)   # River text


def get_font(size: int, paths: list[str]) -> ImageFont.FreeTypeFont:
    for path in paths:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def text_font(size: int) -> ImageFont.FreeTypeFont:
    return get_font(size, [
        "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc",
        "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/truetype/arphic-gkai00mp/gkai00mp.ttf",
        "/usr/share/fonts/truetype/arphic-bkai00mp/bkai00mp.ttf",
    ])


def latin_font(size: int) -> ImageFont.FreeTypeFont:
    return get_font(size, [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ])


def center_text(draw: ImageDraw.ImageDraw, xy: tuple[float, float], text: str,
                font: ImageFont.ImageFont, fill: tuple[int, int, int, int]) -> None:
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text((xy[0] - tw / 2, xy[1] - th / 2 - bbox[1] / 2), text, font=font, fill=fill)


def create_clean_board_surface(size: tuple[int, int]) -> Image.Image:
    """Create clean, modern board surface with subtle texture."""
    w, h = size
    img = Image.new("RGBA", size, BG_COLOR)
    px = img.load()

    rng = random.Random(888)

    # Add very subtle paper-like texture
    for y in range(h):
        for x in range(w):
            # Subtle noise
            noise = rng.uniform(-3, 3)

            r = max(0, min(255, BOARD_BASE[0] + int(noise)))
            g = max(0, min(255, BOARD_BASE[1] + int(noise)))
            b = max(0, min(255, BOARD_BASE[2] + int(noise)))

            px[x, y] = (r, g, b, 255)

    # Very light blur for smoothness
    return img.filter(ImageFilter.GaussianBlur(0.3))


def add_subtle_shadow(base: Image.Image, bounds: tuple[int, int, int, int]) -> None:
    """Add clean drop shadow for depth."""
    x1, y1, x2, y2 = bounds
    shadow = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(shadow)
    d.rounded_rectangle((x1 + 8, y1 + 12, x2 + 8, y2 + 12),
                        radius=8, fill=(60, 50, 40, 60))
    base.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(18)))


def draw_grid_lines(draw: ImageDraw.ImageDraw) -> None:
    """Draw clean, precise grid lines with proper hierarchy."""

    # Horizontal lines
    for r in range(10):
        y = GRID_TOP + r * CELL
        width = 4 if r in (0, 9) else 3
        draw.line((GRID_LEFT, y, GRID_RIGHT, y), fill=GRID_LINE, width=width)

    # Vertical lines (split at river)
    for c in range(9):
        x = GRID_LEFT + c * CELL
        width = 4 if c in (0, 8) else 3
        # Top section
        draw.line((x, GRID_TOP, x, GRID_TOP + CELL * 4), fill=GRID_LINE, width=width)
        # Bottom section
        draw.line((x, GRID_TOP + CELL * 5, x, GRID_BOTTOM), fill=GRID_LINE, width=width)

    # Palace diagonals - special color
    for top_rank in (0, 7):
        y0 = GRID_TOP + top_rank * CELL
        y2 = GRID_TOP + (top_rank + 2) * CELL
        x_left = GRID_LEFT + 3 * CELL
        x_right = GRID_LEFT + 5 * CELL

        draw.line((x_left, y0, x_right, y2), fill=PALACE_LINE, width=3)
        draw.line((x_right, y0, x_left, y2), fill=PALACE_LINE, width=3)


def draw_position_markers(draw: ImageDraw.ImageDraw) -> None:
    """Draw clean position markers."""
    positions = [
        (1, 2), (7, 2),
        (0, 3), (2, 3), (4, 3), (6, 3), (8, 3),
        (0, 6), (2, 6), (4, 6), (6, 6), (8, 6),
        (1, 7), (7, 7),
    ]

    for file, rank in positions:
        x = GRID_LEFT + file * CELL
        y = GRID_TOP + rank * CELL

        gap = 12
        length = 20
        width = 3

        # Draw corner marks with proper bounds checking
        corners = [
            (file > 0, rank > 0, -1, -1),  # top-left
            (file < 8, rank > 0, 1, -1),   # top-right
            (file > 0, rank < 9, -1, 1),   # bottom-left
            (file < 8, rank < 9, 1, 1),    # bottom-right
        ]

        for can_h, can_v, dx, dy in corners:
            if can_h and can_v:
                cx = x + dx * gap
                cy = y + dy * gap
                # Horizontal
                draw.line((cx, cy, cx + dx * length, cy), fill=GRID_ACCENT, width=width)
                # Vertical
                draw.line((cx, cy, cx, cy + dy * length), fill=GRID_ACCENT, width=width)


def draw_river_decoration(draw: ImageDraw.ImageDraw) -> None:
    """Draw elegant river text in modern style."""
    river_y = GRID_TOP + int(4.5 * CELL)
    font = text_font(68)

    # Draw characters with proper spacing
    center_text(draw, (GRID_LEFT + 2 * CELL, river_y), "楚", font, RIVER_TEXT)
    center_text(draw, (GRID_LEFT + 3 * CELL, river_y), "河", font, RIVER_TEXT)
    center_text(draw, (GRID_LEFT + 5 * CELL, river_y), "汉", font, RIVER_TEXT)
    center_text(draw, (GRID_LEFT + 6 * CELL, river_y), "界", font, RIVER_TEXT)


def draw_coordinate_labels(draw: ImageDraw.ImageDraw) -> None:
    """Draw clean coordinate labels."""
    font = latin_font(30)

    top_y = GRID_TOP - 85
    bottom_y = GRID_BOTTOM + 85
    left_x = GRID_LEFT - 75
    right_x = GRID_RIGHT + 75

    # File labels (a-i)
    for file_idx, label in enumerate("abcdefghi"):
        x = GRID_LEFT + file_idx * CELL
        center_text(draw, (x, top_y), label, font, COORD_TEXT)
        center_text(draw, (x, bottom_y), label, font, COORD_TEXT)

    # Rank labels (0-9)
    for rank_idx in range(10):
        label = str(9 - rank_idx)
        y = GRID_TOP + rank_idx * CELL
        center_text(draw, (left_x, y), label, font, COORD_TEXT)
        center_text(draw, (right_x, y), label, font, COORD_TEXT)


def render_board() -> Image.Image:
    """Render modern web-style xiangqi board."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    # Calculate board bounds
    board_x1 = GRID_LEFT - 120
    board_y1 = GRID_TOP - 140
    board_x2 = GRID_RIGHT + 120
    board_y2 = GRID_BOTTOM + 140

    # Add shadow first
    add_subtle_shadow(img, (board_x1, board_y1, board_x2, board_y2))

    # Create clean board surface
    board_w = board_x2 - board_x1
    board_h = board_y2 - board_y1
    board_surface = create_clean_board_surface((board_w, board_h))

    # Composite onto base with rounded corners
    mask = Image.new("L", (board_w, board_h), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, board_w, board_h), radius=8, fill=255)
    img.alpha_composite(
        Image.composite(board_surface, Image.new("RGBA", board_surface.size, (0, 0, 0, 0)), mask),
        (board_x1, board_y1)
    )

    # Draw clean border
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((board_x1, board_y1, board_x2, board_y2),
                       radius=8, outline=(138, 118, 95, 255), width=3)
    d.rounded_rectangle((board_x1 + 8, board_y1 + 8, board_x2 - 8, board_y2 - 8),
                       radius=4, outline=(178, 158, 132, 180), width=1)

    # Draw all grid elements
    draw_grid_lines(d)
    draw_position_markers(d)
    draw_river_decoration(d)
    draw_coordinate_labels(d)

    return img


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    board = render_board()
    board.save(OUT, optimize=True)
    print(OUT)


if __name__ == "__main__":
    main()
