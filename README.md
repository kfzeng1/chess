# Chinese Chess Engine

This repository contains a local Linux x86-64 AVX-VNNI build of Pikafish and
its matching NNUE network.

## Files

- `engines/pikafish-avxvnni`: Pikafish engine binary
- `engines/pikafish.nnue`: NNUE evaluation network
- `assets/current-draft/board.png`: current low-quality board draft
- `assets/current-draft/pieces/*.png`: current low-quality piece drafts
- `assets/reference-previews/pieces-preview.png`: piece sheet preview
- `assets/reference-previews/start-position-preview.png`: board and pieces start-position preview
- `tools/asset-generation/render_xiangqi_board.py`: board rendering script
- `tools/asset-generation/render_xiangqi_pieces.py`: piece rendering script
- `docs/ASSET_HANDOFF.md`: handoff notes for replacing the current draft assets

## Assets

The current assets are placeholders and are not production quality. See
`docs/ASSET_HANDOFF.md` before replacing or redesigning them.

Regenerate the current draft board with:

```bash
python3 tools/asset-generation/render_xiangqi_board.py
```

Regenerate current draft pieces and previews with:

```bash
python3 tools/asset-generation/render_xiangqi_pieces.py
```

Board coordinates follow Pikafish/UCI notation:

- Files: `a` through `i`, left to right
- Ranks: `0` at the red side bottom, `9` at the black side top
- Example: `c3c4` means move from file `c`, rank `3` to file `c`, rank `4`

Piece filenames use side and role names, for example `red_king.png`,
`black_cannon.png`, and `red_pawn.png`.

## Version

- Engine: `Pikafish dev-20260628-553282ed`
- Source commit: `553282edc90181f1f420a210d55eb67f9f14c9e9`
- Build arch: `x86-64-avxvnni`
- NNUE SHA-256: `a2f41d4d0b9f59c5b5ecb3ca129fe24e3a722ea2f00ee252ae14d5dc08899f6a`

## Run

```bash
./engines/pikafish-avxvnni
```

The engine uses UCI. Keep `pikafish.nnue` next to the binary unless you set the
`EvalFile` UCI option to another path.

## Source

Pikafish source: https://github.com/official-pikafish/Pikafish
Pikafish networks: https://github.com/official-pikafish/Networks
