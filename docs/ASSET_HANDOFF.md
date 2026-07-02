# Xiangqi Asset Handoff

This document is for the next AI or designer who will replace the current
Xiangqi board and piece assets.

## Current Status

The current assets are functional drafts only. Visual quality is not acceptable
for the final product.

Known issues:

- Board is too flat and generic.
- Wood texture and bevel treatment feel artificial.
- Piece design is not polished enough for a production game UI.
- Red and black pieces are readable, but still lack a coherent premium style.
- Typography is serviceable but not distinctive.
- The overall set does not yet feel like a high-quality web/mobile game asset.

Treat the current files as placeholders and coordinate references, not as final
art direction.

## Directory Layout

- `assets/current-draft/board.png`
  Current board draft, transparent PNG, `1800x2000`.
- `assets/current-draft/pieces/*.png`
  Current individual piece drafts, transparent PNG, `512x512`.
- `assets/reference-previews/pieces-preview.png`
  Preview sheet for all current piece drafts.
- `assets/reference-previews/start-position-preview.png`
  Board plus pieces in start position.
- `tools/asset-generation/render_xiangqi_board.py`
  Pillow script that generated the current board draft.
- `tools/asset-generation/render_xiangqi_pieces.py`
  Pillow script that generated the current piece drafts and previews.

## Coordinate System

Use Pikafish/UCI coordinates:

- Files are `a` through `i`, left to right.
- Ranks are `0` through `9`.
- Red side is bottom. Red bottom row is rank `0`.
- Black side is top. Black bottom-from-black-perspective row is rank `9`.
- Example move `c3c4` means from file `c`, rank `3` to file `c`, rank `4`.

Board grid parameters used by the current drafts:

```text
Image size: 1800x2000
Grid left: 278
Grid top: 298
Cell size: 156
Grid right: 1526
Grid bottom: 1702
```

These are not mandatory for the redesign, but any new board and preview tooling
must expose equivalent constants so the frontend can map UCI coordinates to
screen positions reliably.

## Required Asset Set

Board:

- Transparent PNG preferred.
- Minimum size: `1800x2000`.
- Must have enough margin for coordinate labels.
- Coordinate labels must not be covered by pieces in the start position.
- Board must support red side at bottom.

Pieces:

- 14 individual transparent PNG files.
- Minimum size: `512x512`.
- Red and black must be visually distinct at small sizes.
- Pieces must read clearly at around `96px` to `140px` displayed size.
- Use consistent lighting, bevel, shadow, and typography across all pieces.

Required filenames:

```text
red_king.png
red_advisor.png
red_bishop.png
red_rook.png
red_knight.png
red_cannon.png
red_pawn.png
black_king.png
black_advisor.png
black_bishop.png
black_rook.png
black_knight.png
black_cannon.png
black_pawn.png
```

Current glyph mapping:

```text
red: 帅 仕 相 车 马 炮 兵
black: 将 士 象 车 马 炮 卒
```

If using traditional glyphs, update the frontend mapping and preview notes.

## Recommended Redesign Direction

Do not continue the current pseudo-3D button look. Better directions:

- Clean high-end digital board with restrained wood, parchment, or lacquer.
- Pieces should feel deliberate and iconic, not generated from generic gradients.
- Consider either:
  - flat premium tokens with subtle shadows, or
  - realistic lacquer/ivory tokens with strong material consistency.
- Keep red/black contrast obvious.
- Prefer a readable CJK serif or calligraphic font with full glyph coverage.
- Test against both light and dark page backgrounds.

## Verification Checklist

Before replacing the draft assets, verify:

- All 14 piece files exist.
- All piece files are transparent RGBA PNGs.
- Board is transparent RGBA PNG.
- Start-position preview has no coordinate overlap.
- Red/black pieces are distinguishable at mobile size.
- Piece glyphs remain legible at `96px`.
- UCI coordinate mapping works for examples like `a0`, `e0`, `c3`, `c4`, `e9`.

## Current Regeneration Commands

These regenerate the current draft only:

```bash
python3 tools/asset-generation/render_xiangqi_board.py
python3 tools/asset-generation/render_xiangqi_pieces.py
```

If new artwork is created manually or with another tool, either replace these
scripts or add a new documented pipeline.
