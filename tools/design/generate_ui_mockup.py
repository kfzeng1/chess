#!/usr/bin/env python3
"""Generate UI mockup for Xiangqi AI web frontend."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "assets" / "ui-mockup.png"

W, H = 1400, 1000
BG = (248, 246, 242)
CARD_BG = (255, 255, 255)
BORDER = (220, 215, 208)
PRIMARY = (198, 45, 38)
SECONDARY = (52, 48, 45)
TEXT_DARK = (42, 38, 35)
TEXT_LIGHT = (118, 108, 98)
WIN_RED = (235, 75, 62)
WIN_BLACK = (72, 65, 58)
BUTTON_BG = (242, 240, 236)
BUTTON_HOVER = (232, 228, 220)


def get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in paths:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def draw_rounded_rect(draw: ImageDraw.ImageDraw, box: tuple, radius: int, fill: tuple, outline: tuple | None = None, width: int = 1):
    """Draw rounded rectangle."""
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def draw_button(draw: ImageDraw.ImageDraw, box: tuple, text: str, font: ImageFont.FreeTypeFont, bg: tuple = BUTTON_BG):
    """Draw a button."""
    x1, y1, x2, y2 = box
    draw_rounded_rect(draw, box, 6, bg, BORDER, 1)

    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    cx = (x1 + x2) / 2
    cy = (y1 + y2) / 2
    draw.text((cx - tw/2, cy - th/2 - bbox[1]/2), text, font=font, fill=TEXT_DARK)


def draw_text(draw: ImageDraw.ImageDraw, xy: tuple, text: str, font: ImageFont.FreeTypeFont, fill: tuple = TEXT_DARK, align: str = "left"):
    """Draw text."""
    if align == "center":
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        draw.text((xy[0] - tw/2, xy[1]), text, font=font, fill=fill)
    else:
        draw.text(xy, text, font=font, fill=fill)


def draw_win_rate_bar(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, red_win_rate: float):
    """Draw win rate bar."""
    # Background
    draw_rounded_rect(draw, (x, y, x + w, y + h), 8, (235, 235, 235), BORDER)

    # Red portion
    red_w = int(w * red_win_rate)
    if red_w > 0:
        draw_rounded_rect(draw, (x, y, x + red_w, y + h), 8, WIN_RED)

    # Black portion
    if red_w < w:
        draw_rounded_rect(draw, (x + red_w, y, x + w, y + h), 8, WIN_BLACK)

    # Percentage text
    font = get_font(14, bold=True)
    red_pct = f"{int(red_win_rate * 100)}%"
    black_pct = f"{int((1 - red_win_rate) * 100)}%"

    draw_text(draw, (x + 10, y + h//2 - 8), f"红 {red_pct}", font, (255, 255, 255))

    bbox = draw.textbbox((0, 0), f"黑 {black_pct}", font=font)
    tw = bbox[2] - bbox[0]
    draw_text(draw, (x + w - tw - 10, y + h//2 - 8), f"黑 {black_pct}", font, (255, 255, 255))


def render_mockup() -> Image.Image:
    """Render UI mockup."""
    img = Image.new("RGBA", (W, H), BG)
    d = ImageDraw.Draw(img)

    title_font = get_font(24, bold=True)
    heading_font = get_font(18, bold=True)
    label_font = get_font(14, bold=True)
    text_font = get_font(14)
    small_font = get_font(12)

    # Title
    draw_text(d, (W//2, 20), "象棋 AI 对弈", title_font, PRIMARY, align="center")

    # Left panel - Controls
    panel_x = 20
    panel_y = 60
    panel_w = 280

    draw_rounded_rect(d, (panel_x, panel_y, panel_x + panel_w, panel_y + 920), 12, CARD_BG, BORDER, 2)

    # Game controls section
    cy = panel_y + 20
    draw_text(d, (panel_x + 20, cy), "游戏控制", heading_font, TEXT_DARK)
    cy += 40

    buttons = [
        ("开新局", BUTTON_BG),
        ("悔棋", BUTTON_BG),
        ("翻转棋盘", BUTTON_BG),
    ]

    for btn_text, btn_color in buttons:
        draw_button(d, (panel_x + 20, cy, panel_x + panel_w - 20, cy + 40), btn_text, label_font, btn_color)
        cy += 50

    # Player settings
    cy += 10
    draw_text(d, (panel_x + 20, cy), "红方玩家", label_font, TEXT_DARK)
    cy += 30

    # Red player buttons
    draw_button(d, (panel_x + 20, cy, panel_x + 130, cy + 35), "人类", label_font, PRIMARY)
    draw_button(d, (panel_x + 140, cy, panel_x + panel_w - 20, cy + 35), "AI", label_font, BUTTON_BG)
    cy += 45

    draw_text(d, (panel_x + 20, cy), "黑方玩家", label_font, TEXT_DARK)
    cy += 30

    # Black player buttons
    draw_button(d, (panel_x + 20, cy, panel_x + 130, cy + 35), "人类", label_font, BUTTON_BG)
    draw_button(d, (panel_x + 140, cy, panel_x + panel_w - 20, cy + 35), "AI", label_font, SECONDARY)
    cy += 50

    # AI strength
    cy += 10
    draw_text(d, (panel_x + 20, cy), "红方 AI 强度", label_font, TEXT_DARK)
    cy += 30

    # Strength slider mockup
    slider_x = panel_x + 20
    slider_w = panel_w - 40
    d.rounded_rectangle((slider_x, cy, slider_x + slider_w, cy + 8), radius=4, fill=(220, 220, 220))
    d.rounded_rectangle((slider_x, cy, slider_x + int(slider_w * 0.7), cy + 8), radius=4, fill=PRIMARY)
    d.ellipse((slider_x + int(slider_w * 0.7) - 8, cy - 4, slider_x + int(slider_w * 0.7) + 8, cy + 12), fill=PRIMARY, outline=(255, 255, 255), width=2)
    cy += 20
    draw_text(d, (panel_x + 20, cy), "深度: 10", small_font, TEXT_LIGHT)
    cy += 40

    draw_text(d, (panel_x + 20, cy), "黑方 AI 强度", label_font, TEXT_DARK)
    cy += 30

    # Black strength slider
    d.rounded_rectangle((slider_x, cy, slider_x + slider_w, cy + 8), radius=4, fill=(220, 220, 220))
    d.rounded_rectangle((slider_x, cy, slider_x + int(slider_w * 0.9), cy + 8), radius=4, fill=SECONDARY)
    d.ellipse((slider_x + int(slider_w * 0.9) - 8, cy - 4, slider_x + int(slider_w * 0.9) + 8, cy + 12), fill=SECONDARY, outline=(255, 255, 255), width=2)
    cy += 20
    draw_text(d, (panel_x + 20, cy), "深度: 15", small_font, TEXT_LIGHT)
    cy += 50

    # AI action button
    draw_button(d, (panel_x + 20, cy, panel_x + panel_w - 20, cy + 50), "本步 AI 走", label_font, (82, 178, 122))
    cy += 60

    # Status
    draw_text(d, (panel_x + 20, cy), "状态", label_font, TEXT_DARK)
    cy += 30
    draw_text(d, (panel_x + 20, cy), "红方回合", text_font, PRIMARY)
    cy += 25
    draw_text(d, (panel_x + 20, cy), "已走: 12 步", small_font, TEXT_LIGHT)

    # Center - Board with win rate
    board_x = panel_x + panel_w + 30
    board_y = 80
    board_w = 560
    board_h = 620

    # Win rate bar above board
    draw_win_rate_bar(d, board_x, board_y - 50, board_w, 35, 0.65)

    # Board placeholder
    draw_rounded_rect(d, (board_x, board_y, board_x + board_w, board_y + board_h), 12, (222, 207, 186), (138, 118, 95), 3)
    draw_text(d, (board_x + board_w//2, board_y + board_h//2 - 20), "[ 棋盘区域 ]", heading_font, TEXT_LIGHT, align="center")
    draw_text(d, (board_x + board_w//2, board_y + board_h//2 + 10), "560 x 620", text_font, TEXT_LIGHT, align="center")

    # Right panel - Analysis
    right_x = board_x + board_w + 30
    right_w = W - right_x - 20

    # Principal variation
    draw_rounded_rect(d, (right_x, board_y, right_x + right_w, board_y + 280), 12, CARD_BG, BORDER, 2)
    draw_text(d, (right_x + 15, board_y + 15), "主变例", heading_font, TEXT_DARK)

    pv_y = board_y + 55
    pv_lines = [
        "1. h2e2 (+1.76)",
        "2. h9g7 (+1.65)",
        "3. h0g2 (+1.82)",
        "4. i9h9 (+1.71)",
        "5. i0h0 (+1.88)",
    ]

    for i, line in enumerate(pv_lines):
        color = PRIMARY if i % 2 == 0 else SECONDARY
        draw_text(d, (right_x + 20, pv_y), line, text_font, color)
        pv_y += 30

    draw_text(d, (right_x + 20, pv_y + 10), "深度: 15 | 节点: 2.3M", small_font, TEXT_LIGHT)

    # Recommended moves
    rec_y = board_y + 310
    draw_rounded_rect(d, (right_x, rec_y, right_x + right_w, rec_y + 390), 12, CARD_BG, BORDER, 2)
    draw_text(d, (right_x + 15, rec_y + 15), "推荐着法", heading_font, TEXT_DARK)

    rec_moves_y = rec_y + 55
    recommended = [
        ("1", "h2e2", "+1.76", "最佳"),
        ("2", "b2e2", "+0.51", ""),
        ("3", "b0c2", "+0.35", ""),
        ("4", "h0g2", "+0.28", ""),
        ("5", "c3c4", "+0.15", ""),
    ]

    for rank, move, score, tag in recommended:
        # Move box
        box_y = rec_moves_y
        is_best = "最佳" in tag
        bg = (255, 245, 245) if is_best else (248, 248, 248)
        border_color = PRIMARY if is_best else BORDER

        draw_rounded_rect(d, (right_x + 15, box_y, right_x + right_w - 15, box_y + 60), 8, bg, border_color, 2)

        # Rank
        draw_text(d, (right_x + 25, box_y + 12), rank, label_font, TEXT_LIGHT)

        # Move
        draw_text(d, (right_x + 55, box_y + 10), move, heading_font, TEXT_DARK)

        # Score
        score_color = PRIMARY if '+' in score else SECONDARY
        draw_text(d, (right_x + 55, box_y + 35), score, text_font, score_color)

        # Tag
        if tag:
            tag_x = right_x + right_w - 70
            draw_rounded_rect(d, (tag_x, box_y + 15, tag_x + 50, box_y + 35), 4, PRIMARY, None)
            draw_text(d, (tag_x + 25, box_y + 19), tag, small_font, (255, 255, 255), align="center")

        rec_moves_y += 70

    return img


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    mockup = render_mockup()
    mockup.save(OUT, optimize=True)
    print(OUT)
    print(f"UI mockup generated: {W}x{H}")


if __name__ == "__main__":
    main()
