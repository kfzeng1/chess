#!/usr/bin/env python3
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[2]
PIECE_DIR = ROOT / "assets" / "pieces"

SIZE = 512
SCALE = 4
CANVAS = SIZE * SCALE

# Premium modern palette - beautiful and elegant
RED_PALETTE = {
    "bg_outer": (212, 52, 42),      # Vibrant red
    "bg_mid": (235, 75, 62),        # Bright coral red
    "bg_inner": (248, 95, 82),      # Light red
    "face": (255, 253, 248),        # Pure cream
    "border_dark": (145, 35, 28),   # Deep red
    "border_light": (255, 205, 195), # Light red tint
    "ring": (195, 48, 38),          # Medium red
    "text": (138, 28, 22),          # Rich red text
    "text_shadow": (88, 18, 15),    # Deep shadow
}

BLACK_PALETTE = {
    "bg_outer": (52, 48, 45),       # Rich charcoal
    "bg_mid": (72, 65, 58),         # Warm gray
    "bg_inner": (95, 85, 75),       # Light warm gray
    "face": (255, 250, 242),        # Warm cream
    "border_dark": (32, 30, 28),    # Deep black
    "border_light": (215, 205, 195), # Light gray tint
    "ring": (58, 52, 48),           # Dark gray
    "text": (42, 38, 35),           # Rich black text
    "text_shadow": (22, 20, 18),    # Deep shadow
}

PIECES = {
    "red_king": ("red", "帅"),
    "red_advisor": ("red", "仕"),
    "red_bishop": ("red", "相"),
    "red_rook": ("red", "车"),
    "red_knight": ("red", "马"),
    "red_cannon": ("red", "炮"),
    "red_pawn": ("red", "兵"),
    "black_king": ("black", "将"),
    "black_advisor": ("black", "士"),
    "black_bishop": ("black", "象"),
    "black_rook": ("black", "车"),
    "black_knight": ("black", "马"),
    "black_cannon": ("black", "炮"),
    "black_pawn": ("black", "卒"),
}

def get_font(size: int, paths: list[str]) -> ImageFont.FreeTypeFont:
    for path in paths:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def text_font(size: int) -> ImageFont.FreeTypeFont:
    return get_font(size, [
        "/usr/share/fonts/opentype/noto/NotoSerifCJK-Black.ttc",
        "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/truetype/arphic-gkai00mp/gkai00mp.ttf",
        "/usr/share/fonts/truetype/arphic-bkai00mp/bkai00mp.ttf",
    ])


def centered_text(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str,
                  font: ImageFont.ImageFont, fill: tuple[int, int, int],
                  shadow_color: tuple[int, int, int]) -> None:
    """Draw centered text with subtle shadow."""
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x = xy[0] - tw / 2 - bbox[0]
    y = xy[1] - th / 2 - bbox[1]

    # Subtle shadow for depth
    draw.text((x + 3 * SCALE, y + 3 * SCALE), text, font=font, fill=shadow_color + (90,))

    # Main text - crisp and bold
    draw.text((x, y), text, font=font, fill=fill + (255,))


def create_radial_fill(size: int, palette: dict) -> Image.Image:
    """Create beautiful radial gradient."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    px = img.load()

    cx, cy = size * 0.5, size * 0.38
    max_dist = math.hypot(size - cx, size - cy)

    for y in range(size):
        for x in range(size):
            dist = math.hypot(x - cx, y - cy) / max_dist

            if dist < 0.25:
                # Bright center highlight
                t = dist / 0.25
                color = tuple(
                    int(palette["face"][i] + (palette["bg_inner"][i] - palette["face"][i]) * t * 0.12)
                    for i in range(3)
                )
            elif dist < 0.6:
                # Main gradient zone
                t = (dist - 0.25) / 0.35
                color = tuple(
                    int(palette["face"][i] + (palette["face"][i] - palette["bg_inner"][i]) * 0.18 * t)
                    for i in range(3)
                )
            elif dist < 0.82:
                # Edge darkening
                t = (dist - 0.6) / 0.22
                color = tuple(
                    int(palette["face"][i] + (palette["face"][i] - palette["bg_inner"][i]) * 0.25 * t)
                    for i in range(3)
                )
            else:
                # Outer edge
                color = tuple(
                    int(palette["face"][i] + (palette["face"][i] - palette["bg_inner"][i]) * 0.25)
                    for i in range(3)
                )

            px[x, y] = color + (255,)

    return img


def render_piece(side: str, glyph: str) -> Image.Image:
    """Render beautiful modern xiangqi piece."""
    palette = RED_PALETTE if side == "red" else BLACK_PALETTE

    img = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    center = (CANVAS // 2, CANVAS // 2)

    # Beautiful soft shadow
    shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.ellipse(
        (78 * SCALE, 88 * SCALE, 434 * SCALE, 438 * SCALE),
        fill=(32, 28, 24, 110)
    )
    img.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(14 * SCALE)))

    d = ImageDraw.Draw(img)

    # Vibrant colored outer ring
    d.ellipse(
        (68 * SCALE, 68 * SCALE, 444 * SCALE, 444 * SCALE),
        fill=palette["bg_outer"] + (255,)
    )

    # Mid-tone ring
    d.ellipse(
        (78 * SCALE, 78 * SCALE, 434 * SCALE, 434 * SCALE),
        fill=palette["bg_mid"] + (255,)
    )

    # Inner colored ring
    d.ellipse(
        (88 * SCALE, 88 * SCALE, 424 * SCALE, 424 * SCALE),
        fill=palette["bg_inner"] + (255,)
    )

    # Beautiful cream center face with gradient
    face_gradient = create_radial_fill(CANVAS, palette)
    face_mask = Image.new("L", (CANVAS, CANVAS), 0)
    ImageDraw.Draw(face_mask).ellipse(
        (100 * SCALE, 100 * SCALE, 412 * SCALE, 412 * SCALE),
        fill=255
    )
    img.alpha_composite(Image.composite(face_gradient, Image.new("RGBA", img.size, (0, 0, 0, 0)), face_mask))

    # Refined borders
    d = ImageDraw.Draw(img)

    # Deep outer border
    d.ellipse(
        (68 * SCALE, 68 * SCALE, 444 * SCALE, 444 * SCALE),
        outline=palette["border_dark"] + (255,),
        width=6 * SCALE
    )

    # Subtle highlight ring
    d.ellipse(
        (82 * SCALE, 82 * SCALE, 430 * SCALE, 430 * SCALE),
        outline=palette["border_light"] + (80,),
        width=2 * SCALE
    )

    # Inner decorative ring
    d.ellipse(
        (112 * SCALE, 112 * SCALE, 400 * SCALE, 400 * SCALE),
        outline=palette["ring"] + (95,),
        width=3 * SCALE
    )

    # Beautiful character - larger and bolder
    glyph_font = text_font(235 * SCALE)
    centered_text(d, center, glyph, glyph_font, palette["text"], palette["text_shadow"])

    # Polished highlight for premium look
    highlight = Image.new("RGBA", img.size, (0, 0, 0, 0))
    hd = ImageDraw.Draw(highlight)

    # Top-left shine
    hd.ellipse(
        (125 * SCALE, 95 * SCALE, 295 * SCALE, 185 * SCALE),
        fill=(255, 255, 255, 42)
    )

    # Rim gloss
    hd.arc(
        (76 * SCALE, 76 * SCALE, 436 * SCALE, 436 * SCALE),
        195, 320,
        fill=(255, 255, 255, 65),
        width=5 * SCALE
    )

    img.alpha_composite(highlight.filter(ImageFilter.GaussianBlur(9 * SCALE)))

    # Downsample with premium quality
    return img.resize((SIZE, SIZE), Image.Resampling.LANCZOS)


def render_all_pieces() -> None:
    """Generate all piece images."""
    PIECE_DIR.mkdir(parents=True, exist_ok=True)
    for name, (side, glyph) in PIECES.items():
        path = PIECE_DIR / f"{name}.png"
        render_piece(side, glyph).save(path, optimize=True)
        print(path)


def main() -> None:
    render_all_pieces()


if __name__ == "__main__":
    main()
