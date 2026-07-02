#!/usr/bin/env python3
"""Generate clean UI mockup with real board and proper fonts."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "assets" / "ui-mockup-v3.png"
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
            except Exception as e:
                print(f"Failed to load {path}: {e}")
                continue

    print("WARNING: Using default font")
    return ImageFont.load_default()


def draw_card(draw, x, y, w, h, title, content_func):
    """Draw a white card with title."""
    # Card background
    draw.rounded_rectangle((x, y, x+w, y+h), radius=12, fill=(255, 255, 255), outline=(220, 215, 210), width=2)

    # Title
    font = load_font(18, bold=True)
    draw.text((x+20, y+20), title, font=font, fill=(42, 38, 35))

    # Content area
    if content_func:
        content_func(draw, x, y+60, w)


def draw_button(draw, x, y, w, h, text, color=(242, 240, 236), text_color=(42, 38, 35)):
    """Draw a button."""
    draw.rounded_rectangle((x, y, x+w, y+h), radius=8, fill=color, outline=(220, 215, 210), width=1)
    font = load_font(14, bold=True)
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text((x + (w-tw)/2, y + (h-th)/2), text, font=font, fill=text_color)


def render() -> Image.Image:
    """Render the mockup."""
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    # Title
    title_font = load_font(32, bold=True)
    title = "象棋 AI 对弈平台"
    bbox = d.textbbox((0, 0), title, font=title_font)
    tw = bbox[2] - bbox[0]
    d.text((W//2 - tw//2, 30), title, font=title_font, fill=(198, 45, 38))

    # === LEFT PANEL: Controls ===
    left_x = 30
    left_y = 100
    left_w = 320

    def controls_content(draw, x, y, w):
        cy = y
        font = load_font(14, bold=True)
        small = load_font(12)

        # Game controls
        draw_button(draw, x+20, cy, w-40, 48, "开新局", (82, 178, 122), (255, 255, 255))
        cy += 60
        draw_button(draw, x+20, cy, w-40, 48, "悔棋", (242, 240, 236), (42, 38, 35))
        cy += 60
        draw_button(draw, x+20, cy, w-40, 48, "翻转棋盘", (242, 240, 236), (42, 38, 35))
        cy += 80

        # Player settings
        draw.text((x+20, cy), "红方", font=font, fill=(198, 45, 38))
        cy += 30
        draw_button(draw, x+20, cy, (w-50)//2, 40, "人类", (198, 45, 38), (255, 255, 255))
        draw_button(draw, x+20+(w-50)//2+10, cy, (w-50)//2, 40, "AI", (242, 240, 236))
        cy += 60

        draw.text((x+20, cy), "黑方", font=font, fill=(52, 48, 45))
        cy += 30
        draw_button(draw, x+20, cy, (w-50)//2, 40, "人类", (242, 240, 236))
        draw_button(draw, x+20+(w-50)//2+10, cy, (w-50)//2, 40, "AI", (52, 48, 45), (255, 255, 255))
        cy += 70

        # AI strength
        draw.text((x+20, cy), "红方 AI 强度: 10", font=font, fill=(198, 45, 38))
        cy += 30
        draw.rounded_rectangle((x+20, cy, x+w-20, cy+8), radius=4, fill=(230, 230, 230))
        draw.rounded_rectangle((x+20, cy, x+20+int((w-40)*0.5), cy+8), radius=4, fill=(198, 45, 38))
        cy += 30
        draw.text((x+20, cy), "搜索深度控制", font=small, fill=(118, 108, 98))
        cy += 40

        draw.text((x+20, cy), "黑方 AI 强度: 15", font=font, fill=(52, 48, 45))
        cy += 30
        draw.rounded_rectangle((x+20, cy, x+w-20, cy+8), radius=4, fill=(230, 230, 230))
        draw.rounded_rectangle((x+20, cy, x+20+int((w-40)*0.75), cy+8), radius=4, fill=(52, 48, 45))
        cy += 30
        draw.text((x+20, cy), "搜索深度控制", font=small, fill=(118, 108, 98))
        cy += 50

        # AI move button
        draw_button(draw, x+20, cy, w-40, 50, "本步 AI 走", (65, 150, 210), (255, 255, 255))
        cy += 70

        # Status
        draw.text((x+20, cy), "对局状态", font=font, fill=(42, 38, 35))
        cy += 30
        draw.rounded_rectangle((x+20, cy, x+w-20, cy+80), radius=8, fill=(255, 248, 246), outline=(235, 220, 215))
        draw.text((x+35, cy+15), "当前: 红方回合", font=small, fill=(198, 45, 38))
        draw.text((x+35, cy+40), "已走: 12 步", font=small, fill=(118, 108, 98))
        draw.text((x+35, cy+60), "用时: 5分23秒", font=small, fill=(118, 108, 98))

    draw_card(d, left_x, left_y, left_w, 920, "游戏控制", controls_content)

    # === CENTER: Board ===
    board_x = left_x + left_w + 30
    board_y = 100

    # Try to load real board
    try:
        board_img = Image.open(BOARD_PATH)
        print(f"Loaded board: {board_img.mode}, {board_img.size}")

        # Scale to fit
        target_h = 900
        target_w = int(board_img.width * target_h / board_img.height)
        board_img = board_img.resize((target_w, target_h), Image.Resampling.LANCZOS)

        # Create background for transparent board
        board_bg = Image.new("RGB", (target_w, target_h), BG)
        if board_img.mode == 'RGBA':
            board_bg.paste(board_img, (0, 0), board_img)
        else:
            board_bg = board_img.convert("RGB")

        # Win rate bar
        bar_w = target_w
        bar_h = 40
        bar_y = board_y - 55
        d.rounded_rectangle((board_x, bar_y, board_x+bar_w, bar_y+bar_h), radius=6, fill=(235, 235, 235))

        red_w = int(bar_w * 0.68)
        d.rounded_rectangle((board_x, bar_y, board_x+red_w, bar_y+bar_h), radius=6, fill=(235, 75, 62))
        d.rounded_rectangle((board_x+red_w, bar_y, board_x+bar_w, bar_y+bar_h), radius=6, fill=(72, 65, 58))

        bar_font = load_font(14, bold=True)
        d.text((board_x+12, bar_y+12), "红 68%", font=bar_font, fill=(255, 255, 255))
        bbox = d.textbbox((0, 0), "黑 32%", font=bar_font)
        tw = bbox[2] - bbox[0]
        d.text((board_x+bar_w-tw-12, bar_y+12), "黑 32%", font=bar_font, fill=(255, 255, 255))

        # Paste board
        img.paste(board_bg, (board_x, board_y))

        board_w = target_w
        print(f"Board placed at ({board_x}, {board_y}), size: {target_w}x{target_h}")

    except Exception as e:
        print(f"Could not load board: {e}")
        import traceback
        traceback.print_exc()
        board_w = 800
        d.rounded_rectangle((board_x, board_y, board_x+board_w, board_y+900), radius=12, fill=(222, 207, 186))
        font = load_font(24, bold=True)
        d.text((board_x+board_w//2-100, board_y+board_h//2), "棋盘加载失败", font=font, fill=(118, 108, 98))

    # === RIGHT PANEL: Analysis ===
    right_x = board_x + board_w + 30
    right_w = W - right_x - 30
    right_y = 100

    def pv_content(draw, x, y, w):
        font = load_font(14)
        small = load_font(12)
        cy = y

        draw.text((x+20, cy), "AI 计算的最佳着法序列", font=small, fill=(118, 108, 98))
        cy += 35

        moves = [
            ("1. h2e2", "+1.76", (198, 45, 38)),
            ("2. h9g7", "+1.65", (52, 48, 45)),
            ("3. h0g2", "+1.82", (198, 45, 38)),
            ("4. i9h9", "+1.71", (52, 48, 45)),
            ("5. i0h0", "+1.88", (198, 45, 38)),
        ]

        for move, score, color in moves:
            draw.text((x+25, cy), move, font=font, fill=color)
            draw.text((x+120, cy), score, font=font, fill=color)
            cy += 28

        cy += 15
        draw.text((x+25, cy), "深度: 15 | 节点: 2.3M", font=small, fill=(118, 108, 98))

    draw_card(d, right_x, right_y, right_w, 280, "主变例", pv_content)

    def rec_content(draw, x, y, w):
        font = load_font(15, bold=True)
        small = load_font(12)
        cy = y

        draw.text((x+20, cy), "点击着法直接走棋", font=small, fill=(118, 108, 98))
        cy += 35

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

            draw.rounded_rectangle((x+20, cy, x+w-20, cy+85), radius=10, fill=bg, outline=border, width=2)

            # Rank circle
            draw.ellipse((x+35, cy+28, x+55, cy+48), fill=(235, 235, 235))
            rank_bbox = draw.textbbox((0, 0), rank, font=small)
            rank_tw = rank_bbox[2] - rank_bbox[0]
            draw.text((x+45-rank_tw//2, cy+32), rank, font=small, fill=(42, 38, 35))

            # Move and score
            draw.text((x+75, cy+18), move, font=font, fill=(42, 38, 35))
            score_color = (198, 45, 38) if '+' in score else (52, 48, 45)
            draw.text((x+75, cy+48), f"评分: {score}", font=small, fill=score_color)

            # Best tag
            if is_best:
                tag_x = x + w - 75
                draw.rounded_rectangle((tag_x, cy+30, tag_x+45, cy+55), radius=5, fill=(198, 45, 38))
                tag_bbox = draw.textbbox((0, 0), "最佳", font=small)
                tag_tw = tag_bbox[2] - tag_bbox[0]
                draw.text((tag_x+22-tag_tw//2, cy+36), "最佳", font=small, fill=(255, 255, 255))

            cy += 100

    draw_card(d, right_x, right_y+310, right_w, 710, "推荐着法", rec_content)

    return img


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    mockup = render()
    mockup.save(OUT, optimize=True, quality=95)
    print(f"\n✓ UI mockup saved to: {OUT}")
    print(f"  Size: {W}x{H}")


if __name__ == "__main__":
    main()
