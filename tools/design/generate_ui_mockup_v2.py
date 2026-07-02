#!/usr/bin/env python3
"""Generate improved UI mockup with actual board assets."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "assets" / "ui-mockup-v2.png"
BOARD_PATH = ROOT / "assets" / "current-draft" / "board.png"

W, H = 1600, 1100
BG = (245, 242, 238)
CARD_BG = (255, 255, 255)
BORDER = (215, 210, 205)
PRIMARY = (198, 45, 38)
SECONDARY = (52, 48, 45)
TEXT_DARK = (42, 38, 35)
TEXT_LIGHT = (108, 98, 88)
WIN_RED = (235, 75, 62)
WIN_BLACK = (72, 65, 58)


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


def draw_button(draw: ImageDraw.ImageDraw, box: tuple, text: str, font: ImageFont.FreeTypeFont,
                bg: tuple = (242, 240, 236), text_color: tuple = None, icon: str = ""):
    """Draw a modern button."""
    x1, y1, x2, y2 = box
    if text_color is None:
        text_color = TEXT_DARK

    # Button background with subtle shadow
    draw_rounded_rect(draw, box, 8, bg)

    # Icon + text
    full_text = f"{icon} {text}" if icon else text
    bbox = draw.textbbox((0, 0), full_text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    cx = (x1 + x2) / 2
    cy = (y1 + y2) / 2
    draw.text((cx - tw/2, cy - th/2 - bbox[1]/2), full_text, font=font, fill=text_color)


def draw_label(draw: ImageDraw.ImageDraw, x: int, y: int, text: str, desc: str, font: ImageFont.FreeTypeFont, small_font: ImageFont.FreeTypeFont):
    """Draw label with description."""
    draw.text((x, y), text, font=font, fill=TEXT_DARK)
    draw.text((x, y + 22), desc, font=small_font, fill=TEXT_LIGHT)


def draw_win_rate_bar(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, red_win_rate: float):
    """Draw beautiful win rate bar."""
    # Background
    draw_rounded_rect(draw, (x, y, x + w, y + h), 6, (235, 235, 235))

    # Red portion
    red_w = int(w * red_win_rate)
    if red_w > 0:
        draw_rounded_rect(draw, (x, y, x + red_w, y + h), 6, WIN_RED)

    # Black portion
    if red_w < w:
        draw_rounded_rect(draw, (x + red_w, y, x + w, y + h), 6, WIN_BLACK)

    # Percentage text
    font = get_font(13, bold=True)
    red_pct = f"{int(red_win_rate * 100)}%"
    black_pct = f"{int((1 - red_win_rate) * 100)}%"

    draw.text((x + 12, y + h//2 - 7), f"红 {red_pct}", font, (255, 255, 255))

    bbox = draw.textbbox((0, 0), f"黑 {black_pct}", font=font)
    tw = bbox[2] - bbox[0]
    draw.text((x + w - tw - 12, y + h//2 - 7), f"黑 {black_pct}", font, (255, 255, 255))


def render_mockup() -> Image.Image:
    """Render improved UI mockup with real board."""
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    title_font = get_font(26, bold=True)
    heading_font = get_font(16, bold=True)
    label_font = get_font(14, bold=True)
    text_font = get_font(13)
    small_font = get_font(11)

    # Title
    title_text = "象棋 AI 对弈平台"
    bbox = d.textbbox((0, 0), title_text, font=title_font)
    tw = bbox[2] - bbox[0]
    d.text((W//2 - tw//2, 25), title_text, font=title_font, fill=PRIMARY)

    # Left panel - Controls
    panel_x = 30
    panel_y = 80
    panel_w = 300

    draw_rounded_rect(d, (panel_x, panel_y, panel_x + panel_w, panel_y + 990), 12, CARD_BG, BORDER, 1)

    cy = panel_y + 25

    # Section 1: Game Controls
    d.text((panel_x + 20, cy), "游戏控制", font=heading_font, fill=TEXT_DARK)
    cy += 35

    # New Game button
    draw_button(d, (panel_x + 20, cy, panel_x + panel_w - 20, cy + 45),
                "开新局", label_font, (82, 178, 122), (255, 255, 255), "⟳")
    draw_label(d, panel_x + 20, cy + 50, "", "开始新的对局", small_font, small_font)
    cy += 75

    # Undo button
    draw_button(d, (panel_x + 20, cy, panel_x + panel_w - 20, cy + 45),
                "悔棋", label_font, (245, 245, 245), TEXT_DARK, "↶")
    draw_label(d, panel_x + 20, cy + 50, "", "撤销上一步或两步", small_font, small_font)
    cy += 75

    # Flip board button
    draw_button(d, (panel_x + 20, cy, panel_x + panel_w - 20, cy + 45),
                "翻转棋盘", label_font, (245, 245, 245), TEXT_DARK, "⇅")
    draw_label(d, panel_x + 20, cy + 50, "", "旋转视角", small_font, small_font)
    cy += 85

    # Section 2: Player Settings
    d.text((panel_x + 20, cy), "对局设置", font=heading_font, fill=TEXT_DARK)
    cy += 35

    d.text((panel_x + 20, cy), "红方", font=label_font, fill=TEXT_DARK)
    cy += 28
    draw_button(d, (panel_x + 20, cy, panel_x + 145, cy + 38), "人类", text_font, PRIMARY, (255, 255, 255))
    draw_button(d, (panel_x + 155, cy, panel_x + panel_w - 20, cy + 38), "AI", text_font, (245, 245, 245), TEXT_DARK)
    draw_label(d, panel_x + 20, cy + 43, "", "选择红方由谁控制", small_font, small_font)
    cy += 70

    d.text((panel_x + 20, cy), "黑方", font=label_font, fill=TEXT_DARK)
    cy += 28
    draw_button(d, (panel_x + 20, cy, panel_x + 145, cy + 38), "人类", text_font, (245, 245, 245), TEXT_DARK)
    draw_button(d, (panel_x + 155, cy, panel_x + panel_w - 20, cy + 38), "AI", text_font, SECONDARY, (255, 255, 255))
    draw_label(d, panel_x + 20, cy + 43, "", "选择黑方由谁控制", small_font, small_font)
    cy += 85

    # Section 3: AI Strength
    d.text((panel_x + 20, cy), "AI 强度", font=heading_font, fill=TEXT_DARK)
    cy += 35

    d.text((panel_x + 20, cy), "红方 AI", font=label_font, fill=PRIMARY)
    cy += 25
    # Slider
    slider_x = panel_x + 20
    slider_w = panel_w - 40
    d.rounded_rectangle((slider_x, cy, slider_x + slider_w, cy + 6), radius=3, fill=(230, 230, 230))
    d.rounded_rectangle((slider_x, cy, slider_x + int(slider_w * 0.7), cy + 6), radius=3, fill=PRIMARY)
    d.ellipse((slider_x + int(slider_w * 0.7) - 10, cy - 7, slider_x + int(slider_w * 0.7) + 10, cy + 13),
              fill=PRIMARY, outline=(255, 255, 255), width=3)
    cy += 18
    d.text((panel_x + 20, cy), "搜索深度: 10", font=small_font, fill=TEXT_LIGHT)
    draw_label(d, panel_x + 20, cy + 18, "", "深度越高越强但越慢", small_font, small_font)
    cy += 55

    d.text((panel_x + 20, cy), "黑方 AI", font=label_font, fill=SECONDARY)
    cy += 25
    # Slider
    d.rounded_rectangle((slider_x, cy, slider_x + slider_w, cy + 6), radius=3, fill=(230, 230, 230))
    d.rounded_rectangle((slider_x, cy, slider_x + int(slider_w * 0.9), cy + 6), radius=3, fill=SECONDARY)
    d.ellipse((slider_x + int(slider_w * 0.9) - 10, cy - 7, slider_x + int(slider_w * 0.9) + 10, cy + 13),
              fill=SECONDARY, outline=(255, 255, 255), width=3)
    cy += 18
    d.text((panel_x + 20, cy), "搜索深度: 15", font=small_font, fill=TEXT_LIGHT)
    draw_label(d, panel_x + 20, cy + 18, "", "深度越高越强但越慢", small_font, small_font)
    cy += 70

    # AI Move button
    draw_button(d, (panel_x + 20, cy, panel_x + panel_w - 20, cy + 50),
                "本步 AI 走", label_font, (65, 150, 210), (255, 255, 255), "▶")
    draw_label(d, panel_x + 20, cy + 55, "", "让 AI 帮忙走一步", small_font, small_font)
    cy += 85

    # Section 4: Status
    d.text((panel_x + 20, cy), "对局状态", font=heading_font, fill=TEXT_DARK)
    cy += 30
    draw_rounded_rect(d, (panel_x + 20, cy, panel_x + panel_w - 20, cy + 80), 8, (255, 248, 246), (235, 220, 215))
    d.text((panel_x + 35, cy + 15), "● 红方回合", font=text_font, fill=PRIMARY)
    d.text((panel_x + 35, cy + 40), "已走: 12 步", font=text_font, fill=TEXT_LIGHT)
    d.text((panel_x + 35, cy + 60), "用时: 5分23秒", font=small_font, fill=TEXT_LIGHT)

    # Center - Board area with win rate
    board_x = panel_x + panel_w + 40
    board_y = 110

    # Load and display real board
    board_w = 600
    board_h = 920
    try:
        board_raw = Image.open(BOARD_PATH)
        # Scale board to fit
        target_h = 920
        target_w = int(board_raw.width * target_h / board_raw.height)
        board_raw = board_raw.resize((target_w, target_h), Image.Resampling.LANCZOS)

        # Create background and composite RGBA board
        board_bg = Image.new("RGB", (target_w, target_h), BG)
        if board_raw.mode == 'RGBA':
            board_bg.paste(board_raw, (0, 0), board_raw)
        else:
            board_bg.paste(board_raw, (0, 0))

        # Win rate bar above board
        win_bar_y = board_y - 45
        draw_win_rate_bar(d, board_x, win_bar_y, target_w, 35, 0.68)

        # Composite board
        img.paste(board_bg, (board_x, board_y))

        board_w = target_w
        board_h = target_h
    except Exception as e:
        print(f"Could not load board: {e}")
        draw_rounded_rect(d, (board_x, board_y, board_x + board_w, board_y + board_h), 12, (222, 207, 186))

    # Right panel - Analysis
    right_x = board_x + board_w + 40
    right_w = W - right_x - 30

    # Principal Variation
    pv_y = board_y
    draw_rounded_rect(d, (right_x, pv_y, right_x + right_w, pv_y + 300), 12, CARD_BG, BORDER, 1)
    d.text((right_x + 20, pv_y + 20), "主变例", font=heading_font, fill=TEXT_DARK)
    d.text((right_x + 20, pv_y + 42), "AI 计算的最佳着法序列", font=small_font, fill=TEXT_LIGHT)

    pv_lines_y = pv_y + 75
    pv_lines = [
        ("1. h2e2", "+1.76", PRIMARY),
        ("2. h9g7", "+1.65", SECONDARY),
        ("3. h0g2", "+1.82", PRIMARY),
        ("4. i9h9", "+1.71", SECONDARY),
        ("5. i0h0", "+1.88", PRIMARY),
    ]

    for move, score, color in pv_lines:
        d.text((right_x + 25, pv_lines_y), move, font=text_font, fill=color)
        d.text((right_x + 100, pv_lines_y), score, font=text_font, fill=color)
        pv_lines_y += 32

    d.text((right_x + 25, pv_lines_y + 15), "深度: 15 | 节点: 2.3M | 速度: 450k nps", font=small_font, fill=TEXT_LIGHT)

    # Recommended Moves
    rec_y = pv_y + 330
    draw_rounded_rect(d, (right_x, rec_y, right_x + right_w, rec_y + 690), 12, CARD_BG, BORDER, 1)
    d.text((right_x + 20, rec_y + 20), "推荐着法 (MultiPV)", font=heading_font, fill=TEXT_DARK)
    d.text((right_x + 20, rec_y + 42), "点击着法直接走棋", font=small_font, fill=TEXT_LIGHT)

    rec_y_start = rec_y + 75
    recommendations = [
        ("1", "h2e2", "+1.76", "最佳", True),
        ("2", "b2e2", "+0.51", "", False),
        ("3", "b0c2", "+0.35", "", False),
        ("4", "h0g2", "+0.28", "", False),
        ("5", "c3c4", "+0.15", "", False),
    ]

    for rank, move, score, tag, is_best in recommendations:
        box_y = rec_y_start
        bg = (255, 248, 246) if is_best else (250, 250, 250)
        border_color = PRIMARY if is_best else BORDER

        draw_rounded_rect(d, (right_x + 20, box_y, right_x + right_w - 20, box_y + 100), 10, bg, border_color, 2)

        # Rank circle
        d.ellipse((right_x + 35, box_y + 35, right_x + 55, box_y + 55), fill=(235, 235, 235))
        rank_bbox = d.textbbox((0, 0), rank, font=label_font)
        rank_tw = rank_bbox[2] - rank_bbox[0]
        d.text((right_x + 45 - rank_tw//2, box_y + 38), rank, font=label_font, fill=TEXT_DARK)

        # Move
        d.text((right_x + 75, box_y + 25), move, font=get_font(18, bold=True), fill=TEXT_DARK)

        # Score
        score_color = PRIMARY if '+' in score else SECONDARY
        d.text((right_x + 75, box_y + 55), f"评分: {score}", font=text_font, fill=score_color)

        # Tag
        if tag:
            tag_x = right_x + right_w - 85
            draw_rounded_rect(d, (tag_x, box_y + 35, tag_x + 55, box_y + 60), 5, PRIMARY)
            tag_bbox = d.textbbox((0, 0), tag, font=small_font)
            tag_tw = tag_bbox[2] - tag_bbox[0]
            d.text((tag_x + 27 - tag_tw//2, box_y + 42), tag, font=small_font, fill=(255, 255, 255))

        rec_y_start += 120

    return img


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    mockup = render_mockup()
    mockup.save(OUT, optimize=True, quality=95)
    print(OUT)
    print(f"Improved UI mockup generated: {W}x{H}")


if __name__ == "__main__":
    main()
