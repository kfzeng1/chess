#!/usr/bin/env python3
"""Generate high quality UI mockup v5 - crisp fonts, better colors, clean design."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "assets" / "ui-mockup-v5.png"
BOARD_PATH = ROOT / "assets" / "current-draft" / "board.png"

# Larger resolution for better quality
W, H = 2400, 1350
BG = (250, 248, 245)

# Better colors
CARD_BG = (255, 255, 255)
BORDER = (225, 220, 215)
PRIMARY_RED = (220, 53, 45)
PRIMARY_BLACK = (45, 42, 39)
TEXT_DARK = (35, 32, 29)
TEXT_LIGHT = (120, 110, 100)
GREEN = (76, 175, 120)
BLUE = (70, 160, 220)


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Load font with fallback."""
    if bold:
        paths = [
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ]
    else:
        paths = [
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]

    for path in paths:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def draw_card(draw, x, y, w, h, title, title_size=20):
    """Draw a clean card."""
    # Card with subtle shadow effect
    shadow_offset = 3
    draw.rounded_rectangle((x+shadow_offset, y+shadow_offset, x+w+shadow_offset, y+h+shadow_offset),
                          radius=16, fill=(0, 0, 0, 15))
    draw.rounded_rectangle((x, y, x+w, y+h), radius=16, fill=CARD_BG, outline=BORDER, width=2)

    # Title
    font = load_font(title_size, bold=True)
    draw.text((x+25, y+25), title, font=font, fill=TEXT_DARK)

    # Separator line
    draw.line((x+25, y+60, x+w-25, y+60), fill=BORDER, width=1)


def draw_button(draw, x, y, w, h, text, color=None, text_color=None, size=16):
    """Draw a high quality button."""
    if color is None:
        color = (245, 245, 245)
    if text_color is None:
        text_color = TEXT_DARK

    # Button shadow
    draw.rounded_rectangle((x+2, y+2, x+w+2, y+h+2), radius=10, fill=(0, 0, 0, 20))
    # Button
    draw.rounded_rectangle((x, y, x+w, y+h), radius=10, fill=color, outline=BORDER, width=2)

    # Text
    font = load_font(size, bold=True)
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text((x + (w-tw)/2, y + (h-th)/2 - 1), text, font=font, fill=text_color)


def render() -> Image.Image:
    """Render high quality mockup."""
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    # Title
    title_font = load_font(40, bold=True)
    title = "象棋 AI 对弈平台"
    bbox = d.textbbox((0, 0), title, font=title_font)
    tw = bbox[2] - bbox[0]
    d.text((W//2 - tw//2, 30), title, font=title_font, fill=PRIMARY_RED)

    # === LEFT PANEL ===
    left_x = 35
    left_y = 110
    left_w = 350

    draw_card(d, left_x, left_y, left_w, 1190, "游戏控制", 22)

    cy = left_y + 80
    label_font = load_font(16, bold=True)
    small_font = load_font(14)

    # Buttons
    draw_button(d, left_x+20, cy, left_w-40, 55, "开新局", GREEN, (255, 255, 255), 18)
    cy += 70
    draw_button(d, left_x+20, cy, left_w-40, 55, "悔棋", None, TEXT_DARK, 18)
    cy += 70
    draw_button(d, left_x+20, cy, left_w-40, 55, "翻转棋盘", None, TEXT_DARK, 18)
    cy += 90

    # Player settings
    d.text((left_x+20, cy), "红方玩家", font=label_font, fill=PRIMARY_RED)
    cy += 35
    btn_w = (left_w - 50) // 2
    draw_button(d, left_x+20, cy, btn_w, 50, "人类", PRIMARY_RED, (255, 255, 255), 16)
    draw_button(d, left_x+30+btn_w, cy, btn_w, 50, "AI", None, TEXT_DARK, 16)
    cy += 70

    d.text((left_x+20, cy), "黑方玩家", font=label_font, fill=PRIMARY_BLACK)
    cy += 35
    draw_button(d, left_x+20, cy, btn_w, 50, "人类", None, TEXT_DARK, 16)
    draw_button(d, left_x+30+btn_w, cy, btn_w, 50, "AI", PRIMARY_BLACK, (255, 255, 255), 16)
    cy += 85

    # AI strength
    d.text((left_x+20, cy), "红方 AI 强度", font=label_font, fill=PRIMARY_RED)
    cy += 35

    # Slider track
    slider_w = left_w - 40
    d.rounded_rectangle((left_x+20, cy, left_x+20+slider_w, cy+10), radius=5, fill=(230, 230, 230))
    # Slider fill
    fill_w = int(slider_w * 0.5)
    d.rounded_rectangle((left_x+20, cy, left_x+20+fill_w, cy+10), radius=5, fill=PRIMARY_RED)
    # Slider handle
    handle_x = left_x+20+fill_w
    d.ellipse((handle_x-12, cy-7, handle_x+12, cy+17), fill=PRIMARY_RED, outline=(255, 255, 255), width=3)

    cy += 25
    d.text((left_x+20, cy), "搜索深度: 10", font=small_font, fill=TEXT_LIGHT)
    cy += 50

    d.text((left_x+20, cy), "黑方 AI 强度", font=label_font, fill=PRIMARY_BLACK)
    cy += 35
    d.rounded_rectangle((left_x+20, cy, left_x+20+slider_w, cy+10), radius=5, fill=(230, 230, 230))
    fill_w = int(slider_w * 0.75)
    d.rounded_rectangle((left_x+20, cy, left_x+20+fill_w, cy+10), radius=5, fill=PRIMARY_BLACK)
    handle_x = left_x+20+fill_w
    d.ellipse((handle_x-12, cy-7, handle_x+12, cy+17), fill=PRIMARY_BLACK, outline=(255, 255, 255), width=3)

    cy += 25
    d.text((left_x+20, cy), "搜索深度: 15", font=small_font, fill=TEXT_LIGHT)
    cy += 60

    # AI move button
    draw_button(d, left_x+20, cy, left_w-40, 60, "本步 AI 走", BLUE, (255, 255, 255), 18)
    cy += 90

    # Status box
    d.text((left_x+20, cy), "对局状态", font=label_font, fill=TEXT_DARK)
    cy += 35
    d.rounded_rectangle((left_x+20, cy, left_x+left_w-20, cy+110), radius=12,
                       fill=(255, 250, 248), outline=(240, 220, 215), width=2)
    status_font = load_font(15)
    d.text((left_x+35, cy+20), "当前回合: 红方", font=status_font, fill=PRIMARY_RED)
    d.text((left_x+35, cy+50), "已走步数: 12 步", font=status_font, fill=TEXT_LIGHT)
    d.text((left_x+35, cy+80), "用时: 5分23秒", font=status_font, fill=TEXT_LIGHT)

    # === CENTER: BOARD ===
    board_x = left_x + left_w + 40
    board_y = 110

    try:
        board_img = Image.open(BOARD_PATH)
        print(f"✓ Loaded board: {board_img.size}")

        # Scale board
        target_h = 1190
        target_w = int(board_img.width * target_h / board_img.height)
        board_img = board_img.resize((target_w, target_h), Image.Resampling.LANCZOS)

        # Composite board
        board_bg = Image.new("RGB", (target_w, target_h), BG)
        if board_img.mode == 'RGBA':
            board_bg.paste(board_img, (0, 0), board_img)
        else:
            board_bg = board_img.convert("RGB")

        # Win rate bar - same width as board
        bar_w = target_w
        bar_h = 45
        bar_y = board_y - 60

        # Background
        d.rounded_rectangle((board_x, bar_y, board_x+bar_w, bar_y+bar_h), radius=8, fill=(235, 235, 235))

        # Red (60%)
        red_w = int(bar_w * 0.60)
        d.rounded_rectangle((board_x, bar_y, board_x+red_w, bar_y+bar_h), radius=8, fill=(240, 85, 75))

        # Draw (5%)
        draw_w = int(bar_w * 0.05)
        d.rectangle((board_x+red_w, bar_y, board_x+red_w+draw_w, bar_y+bar_h), fill=(210, 210, 210))

        # Black (35%)
        d.rounded_rectangle((board_x+red_w+draw_w, bar_y, board_x+bar_w, bar_y+bar_h), radius=8, fill=(75, 70, 65))

        # Labels
        bar_font = load_font(16, bold=True)
        d.text((board_x+15, bar_y+13), "红方 60%", font=bar_font, fill=(255, 255, 255))

        draw_bbox = d.textbbox((0, 0), "和 5%", font=bar_font)
        draw_tw = draw_bbox[2] - draw_bbox[0]
        d.text((board_x+red_w+draw_w//2-draw_tw//2, bar_y+13), "和 5%", font=bar_font, fill=(90, 90, 90))

        black_bbox = d.textbbox((0, 0), "黑方 35%", font=bar_font)
        black_tw = black_bbox[2] - black_bbox[0]
        d.text((board_x+bar_w-black_tw-15, bar_y+13), "黑方 35%", font=bar_font, fill=(255, 255, 255))

        # Place board
        img.paste(board_bg, (board_x, board_y))
        board_w = target_w

        print(f"✓ Board: {target_w}x{target_h} at ({board_x}, {board_y})")
        print(f"✓ Win bar: {bar_w}px wide")

    except Exception as e:
        print(f"✗ Board error: {e}")
        board_w = 1000

    # === RIGHT PANEL ===
    right_x = board_x + board_w + 40
    right_w = W - right_x - 35

    # Principal Variation
    draw_card(d, right_x, 110, right_w, 320, "主变例", 20)

    cy = 110 + 80
    text_font = load_font(16)
    small = load_font(14)
    d.text((right_x+25, cy), "AI 计算的最佳着法序列", font=small, fill=TEXT_LIGHT)
    cy += 40

    moves = [
        ("1. h2e2", "+1.76", PRIMARY_RED),
        ("2. h9g7", "+1.65", PRIMARY_BLACK),
        ("3. h0g2", "+1.82", PRIMARY_RED),
        ("4. i9h9", "+1.71", PRIMARY_BLACK),
        ("5. i0h0", "+1.88", PRIMARY_RED),
    ]

    for move, score, color in moves:
        d.text((right_x+30, cy), move, font=text_font, fill=color)
        d.text((right_x+140, cy), score, font=text_font, fill=color)
        cy += 32

    cy += 15
    d.text((right_x+30, cy), "深度: 15 | 节点: 2.3M | 速度: 450k/s", font=small, fill=TEXT_LIGHT)

    # Recommendations
    draw_card(d, right_x, 460, right_w, 840, "推荐着法 (MultiPV)", 20)

    cy = 460 + 80
    d.text((right_x+25, cy), "点击着法可直接走棋", font=small, fill=TEXT_LIGHT)
    cy += 40

    recs = [
        ("1", "h2e2", "+1.76", True),
        ("2", "b2e2", "+0.51", False),
        ("3", "b0c2", "+0.35", False),
        ("4", "h0g2", "+0.28", False),
        ("5", "c3c4", "+0.15", False),
    ]

    for rank, move, score, is_best in recs:
        box_h = 100
        bg = (255, 250, 248) if is_best else (252, 252, 252)
        border = PRIMARY_RED if is_best else BORDER

        d.rounded_rectangle((right_x+20, cy, right_x+right_w-20, cy+box_h),
                          radius=12, fill=bg, outline=border, width=3 if is_best else 2)

        # Rank
        d.ellipse((right_x+38, cy+35, right_x+62, cy+59), fill=(240, 240, 240), outline=BORDER, width=2)
        rank_font = load_font(16, bold=True)
        rank_bbox = d.textbbox((0, 0), rank, font=rank_font)
        rank_tw = rank_bbox[2] - rank_bbox[0]
        d.text((right_x+50-rank_tw//2, cy+39), rank, font=rank_font, fill=TEXT_DARK)

        # Move
        move_font = load_font(19, bold=True)
        d.text((right_x+80, cy+22), move, font=move_font, fill=TEXT_DARK)

        # Score
        score_font = load_font(15)
        score_color = PRIMARY_RED if '+' in score else PRIMARY_BLACK
        d.text((right_x+80, cy+55), f"评分: {score}", font=score_font, fill=score_color)

        # Best badge
        if is_best:
            badge_x = right_x + right_w - 85
            d.rounded_rectangle((badge_x, cy+35, badge_x+55, cy+63), radius=6, fill=PRIMARY_RED)
            badge_font = load_font(14, bold=True)
            badge_bbox = d.textbbox((0, 0), "最佳", font=badge_font)
            badge_tw = badge_bbox[2] - badge_bbox[0]
            d.text((badge_x+27-badge_tw//2, cy+40), "最佳", font=badge_font, fill=(255, 255, 255))

        cy += 115

    return img


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    mockup = render()
    mockup.save(OUT, optimize=False, quality=100)

    print(f"\n✓ High quality mockup saved: {OUT}")
    print(f"  Resolution: {W}x{H}")
    print(f"  File size: {OUT.stat().st_size // 1024}KB")

    # Verify
    verify = Image.open(OUT)
    print(f"✓ Verified: {verify.mode}, {verify.size}")


if __name__ == "__main__":
    main()
