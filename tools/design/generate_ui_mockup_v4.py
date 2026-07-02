#!/usr/bin/env python3
"""Generate improved UI mockup v4 - bigger board, compact right panel."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "assets" / "ui-mockup-v4.png"
BOARD_PATH = ROOT / "assets" / "current-draft" / "board.png"

W, H = 1920, 1080
BG = (248, 246, 242)


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


def draw_card(draw, x, y, w, h, title):
    """Draw a white card with title."""
    draw.rounded_rectangle((x, y, x+w, y+h), radius=12, fill=(255, 255, 255), outline=(220, 215, 210), width=2)
    font = load_font(16, bold=True)
    draw.text((x+20, y+18), title, font=font, fill=(42, 38, 35))


def draw_button(draw, x, y, w, h, text, color=(242, 240, 236), text_color=(42, 38, 35)):
    """Draw a button."""
    draw.rounded_rectangle((x, y, x+w, y+h), radius=8, fill=color, outline=(220, 215, 210), width=1)
    font = load_font(13, bold=True)
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text((x + (w-tw)/2, y + (h-th)/2), text, font=font, fill=text_color)


def render() -> Image.Image:
    """Render the mockup."""
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    # Title
    title_font = load_font(30, bold=True)
    title = "象棋 AI 对弈"
    bbox = d.textbbox((0, 0), title, font=title_font)
    tw = bbox[2] - bbox[0]
    d.text((W//2 - tw//2, 25), title, font=title_font, fill=(198, 45, 38))

    # === LEFT PANEL: Controls (280px) ===
    left_x = 25
    left_y = 85
    left_w = 280

    draw_card(d, left_x, left_y, left_w, 960, "游戏控制")

    cy = left_y + 55
    font = load_font(13, bold=True)
    small = load_font(11)

    # Game controls
    draw_button(d, left_x+15, cy, left_w-30, 44, "开新局", (82, 178, 122), (255, 255, 255))
    cy += 52
    draw_button(d, left_x+15, cy, left_w-30, 44, "悔棋", (242, 240, 236))
    cy += 52
    draw_button(d, left_x+15, cy, left_w-30, 44, "翻转棋盘", (242, 240, 236))
    cy += 65

    # Player settings
    d.text((left_x+15, cy), "红方", font=font, fill=(198, 45, 38))
    cy += 28
    draw_button(d, left_x+15, cy, (left_w-35)//2, 38, "人类", (198, 45, 38), (255, 255, 255))
    draw_button(d, left_x+15+(left_w-35)//2+5, cy, (left_w-35)//2, 38, "AI", (242, 240, 236))
    cy += 55

    d.text((left_x+15, cy), "黑方", font=font, fill=(52, 48, 45))
    cy += 28
    draw_button(d, left_x+15, cy, (left_w-35)//2, 38, "人类", (242, 240, 236))
    draw_button(d, left_x+15+(left_w-35)//2+5, cy, (left_w-35)//2, 38, "AI", (52, 48, 45), (255, 255, 255))
    cy += 65

    # AI strength
    d.text((left_x+15, cy), "红方 AI: 深度 10", font=font, fill=(198, 45, 38))
    cy += 28
    d.rounded_rectangle((left_x+15, cy, left_x+left_w-15, cy+8), radius=4, fill=(230, 230, 230))
    d.rounded_rectangle((left_x+15, cy, left_x+15+int((left_w-30)*0.5), cy+8), radius=4, fill=(198, 45, 38))
    cy += 22
    d.text((left_x+15, cy), "深度越高越强", font=small, fill=(118, 108, 98))
    cy += 35

    d.text((left_x+15, cy), "黑方 AI: 深度 15", font=font, fill=(52, 48, 45))
    cy += 28
    d.rounded_rectangle((left_x+15, cy, left_x+left_w-15, cy+8), radius=4, fill=(230, 230, 230))
    d.rounded_rectangle((left_x+15, cy, left_x+15+int((left_w-30)*0.75), cy+8), radius=4, fill=(52, 48, 45))
    cy += 22
    d.text((left_x+15, cy), "深度越高越强", font=small, fill=(118, 108, 98))
    cy += 45

    # AI move button
    draw_button(d, left_x+15, cy, left_w-30, 48, "本步 AI 走", (65, 150, 210), (255, 255, 255))
    cy += 65

    # Status
    d.text((left_x+15, cy), "对局状态", font=font, fill=(42, 38, 35))
    cy += 28
    d.rounded_rectangle((left_x+15, cy, left_x+left_w-15, cy+85), radius=8, fill=(255, 248, 246), outline=(235, 220, 215))
    d.text((left_x+25, cy+15), "当前: 红方回合", font=small, fill=(198, 45, 38))
    d.text((left_x+25, cy+38), "已走: 12 步", font=small, fill=(118, 108, 98))
    d.text((left_x+25, cy+60), "用时: 5分23秒", font=small, fill=(118, 108, 98))

    # === CENTER: Board (bigger!) ===
    board_x = left_x + left_w + 25
    board_y = 85

    # Load board
    board_w = 900
    board_h = 960

    try:
        board_img = Image.open(BOARD_PATH)
        print(f"✓ Loaded board: {board_img.mode}, {board_img.size}")

        # Scale to fit - make it bigger
        target_h = board_h
        target_w = int(board_img.width * target_h / board_img.height)
        board_img = board_img.resize((target_w, target_h), Image.Resampling.LANCZOS)

        # Create background
        board_bg = Image.new("RGB", (target_w, target_h), BG)
        if board_img.mode == 'RGBA':
            board_bg.paste(board_img, (0, 0), board_img)
        else:
            board_bg = board_img.convert("RGB")

        # Win rate bar - SAME WIDTH AS BOARD
        bar_w = target_w
        bar_h = 36
        bar_y = board_y - 48

        # Background
        d.rounded_rectangle((board_x, bar_y, board_x+bar_w, bar_y+bar_h), radius=6, fill=(240, 240, 240))

        # Red portion (60%)
        red_w = int(bar_w * 0.60)
        d.rounded_rectangle((board_x, bar_y, board_x+red_w, bar_y+bar_h), radius=6, fill=(235, 75, 62))

        # Draw portion (5%)
        draw_w = int(bar_w * 0.05)
        d.rectangle((board_x+red_w, bar_y, board_x+red_w+draw_w, bar_y+bar_h), fill=(200, 200, 200))

        # Black portion (35%)
        d.rounded_rectangle((board_x+red_w+draw_w, bar_y, board_x+bar_w, bar_y+bar_h), radius=6, fill=(72, 65, 58))

        bar_font = load_font(13, bold=True)
        d.text((board_x+10, bar_y+10), "红 60%", font=bar_font, fill=(255, 255, 255))

        # Draw label in center
        draw_bbox = d.textbbox((0, 0), "和 5%", font=bar_font)
        draw_tw = draw_bbox[2] - draw_bbox[0]
        d.text((board_x+red_w+draw_w//2-draw_tw//2, bar_y+10), "和 5%", font=bar_font, fill=(80, 80, 80))

        # Black label on right
        black_bbox = d.textbbox((0, 0), "黑 35%", font=bar_font)
        black_tw = black_bbox[2] - black_bbox[0]
        d.text((board_x+bar_w-black_tw-10, bar_y+10), "黑 35%", font=bar_font, fill=(255, 255, 255))

        # Paste board
        img.paste(board_bg, (board_x, board_y))
        board_w = target_w

        print(f"✓ Board placed: ({board_x}, {board_y}), size: {target_w}x{target_h}")
        print(f"✓ Win rate bar: ({board_x}, {bar_y}), width: {bar_w}")

    except Exception as e:
        print(f"✗ Could not load board: {e}")
        import traceback
        traceback.print_exc()

    # === RIGHT PANEL: Analysis (more compact!) ===
    right_x = board_x + board_w + 25
    right_w = W - right_x - 25
    right_y = 85

    # Principal Variation (compact)
    draw_card(d, right_x, right_y, right_w, 260, "主变例")

    font = load_font(13)
    small = load_font(11)
    cy = right_y + 50

    d.text((right_x+15, cy), "最佳着法序列", font=small, fill=(118, 108, 98))
    cy += 30

    moves = [
        ("1. h2e2", "+1.76", (198, 45, 38)),
        ("2. h9g7", "+1.65", (52, 48, 45)),
        ("3. h0g2", "+1.82", (198, 45, 38)),
        ("4. i9h9", "+1.71", (52, 48, 45)),
        ("5. i0h0", "+1.88", (198, 45, 38)),
    ]

    for move, score, color in moves:
        d.text((right_x+20, cy), move, font=font, fill=color)
        d.text((right_x+110, cy), score, font=font, fill=color)
        cy += 26

    cy += 10
    d.text((right_x+20, cy), "深度: 15 | 2.3M 节点", font=small, fill=(118, 108, 98))

    # Recommendations (more compact)
    rec_y = right_y + 285
    draw_card(d, right_x, rec_y, right_w, 760, "推荐着法")

    cy = rec_y + 50
    d.text((right_x+15, cy), "点击着法走棋", font=small, fill=(118, 108, 98))
    cy += 30

    recs = [
        ("1", "h2e2", "+1.76", True),
        ("2", "b2e2", "+0.51", False),
        ("3", "b0c2", "+0.35", False),
        ("4", "h0g2", "+0.28", False),
        ("5", "c3c4", "+0.15", False),
    ]

    for rank, move, score, is_best in recs:
        bg = (255, 248, 246) if is_best else (250, 250, 250)
        border = (198, 45, 38) if is_best else (220, 215, 210)

        d.rounded_rectangle((right_x+15, cy, right_x+right_w-15, cy+80), radius=10, fill=bg, outline=border, width=2)

        # Rank circle
        d.ellipse((right_x+28, cy+26, right_x+46, cy+44), fill=(235, 235, 235))
        rank_bbox = d.textbbox((0, 0), rank, font=small)
        rank_tw = rank_bbox[2] - rank_bbox[0]
        d.text((right_x+37-rank_tw//2, cy+30), rank, font=small, fill=(42, 38, 35))

        # Move and score
        move_font = load_font(14, bold=True)
        d.text((right_x+62, cy+16), move, font=move_font, fill=(42, 38, 35))
        score_color = (198, 45, 38) if '+' in score else (52, 48, 45)
        d.text((right_x+62, cy+44), f"评分: {score}", font=small, fill=score_color)

        # Best tag
        if is_best:
            tag_x = right_x + right_w - 65
            d.rounded_rectangle((tag_x, cy+28, tag_x+42, cy+50), radius=5, fill=(198, 45, 38))
            tag_bbox = d.textbbox((0, 0), "最佳", font=small)
            tag_tw = tag_bbox[2] - tag_bbox[0]
            d.text((tag_x+21-tag_tw//2, cy+33), "最佳", font=small, fill=(255, 255, 255))

        cy += 92

    return img


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    mockup = render()
    mockup.save(OUT, optimize=True, quality=95)
    print(f"\n✓ UI mockup v4 saved: {OUT}")
    print(f"  Resolution: {W}x{H}")

    # Verify the image
    print("\n=== Verification ===")
    verify = Image.open(OUT)
    print(f"✓ File readable: {verify.mode}, {verify.size}")
    print(f"✓ File size: {OUT.stat().st_size // 1024}KB")


if __name__ == "__main__":
    main()
