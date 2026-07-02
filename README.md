# Chinese Chess AI

This repository contains the current frontend preview assets for a Xiangqi AI
app and a local Pikafish engine build.

## Structure

```text
assets/
  board.png              # latest board image
  pieces/*.png           # latest red/black piece images
  ui-preview.png         # latest desktop frontend preview screenshot
engines/
  pikafish-avxvnni       # Pikafish Linux x86-64 AVX-VNNI binary
  pikafish.nnue          # matching NNUE network
frontend-preview/
  index.html             # responsive UI preview
tools/asset-generation/
  render_xiangqi_board.py
  render_xiangqi_pieces.py
```

## Frontend Preview

Run a local static server from the repository root:

```bash
python3 -m http.server 8000
```

Open:

```text
http://127.0.0.1:8000/frontend-preview/index.html
```

Refresh the desktop screenshot:

```bash
npx playwright screenshot --viewport-size=1440,960 \
  http://127.0.0.1:8000/frontend-preview/index.html \
  assets/ui-preview.png
```

## Regenerate Assets

```bash
python3 tools/asset-generation/render_xiangqi_board.py
python3 tools/asset-generation/render_xiangqi_pieces.py
```

Board coordinates follow Pikafish/UCI notation:

- Files: `a` through `i`, left to right
- Ranks: `0` at the red side bottom, `9` at the black side top
- Example: `c3c4` moves from file `c`, rank `3` to file `c`, rank `4`

Piece filenames use side and role names, for example `red_king.png`,
`black_cannon.png`, and `red_pawn.png`.

## Pikafish

- Engine: `Pikafish dev-20260628-553282ed`
- Source commit: `553282edc90181f1f420a210d55eb67f9f14c9e9`
- Build arch: `x86-64-avxvnni`
- NNUE SHA-256: `a2f41d4d0b9f59c5b5ecb3ca129fe24e3a722ea2f00ee252ae14d5dc08899f6a`

Run:

```bash
./engines/pikafish-avxvnni
```

The engine uses UCI. Keep `pikafish.nnue` next to the binary unless you set the
`EvalFile` UCI option to another path.
