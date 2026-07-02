# Architecture

## Modules

```text
web/backend/server.py   HTTP API and static file server
web/backend/engine.py   Pikafish UCI adapter and fake test engine
web/backend/xiangqi.py  Board state, notation, legal move generation
web/frontend/app.js     Browser state, board interaction, AI workflow
web/frontend/style.css  Responsive app layout
```

## Data Flow

1. Browser loads `/`.
2. Frontend calls `/api/position` with the current UCI move list.
3. Backend rebuilds board state from `startpos + moves`.
4. Backend returns pieces, side to move, legal moves, game-over state, and move
   rows in Chinese/UCI.
5. Frontend renders board pieces and legal target hints.
6. Frontend calls `/api/analyze` with `moves`, `multipv`, and search limit.
7. Backend sends `position startpos moves ...` and `go ...` to Pikafish.
8. Backend parses `bestmove`, `score`, `wdl`, and `pv`, then returns both UCI
   and Chinese notation.

## Search Limits

Frontend search controls map directly to UCI:

- Time mode: `go movetime <milliseconds>`
- Depth mode: `go depth <plies>`

The UI stores separate red/black search settings. Pikafish itself is still one
engine process; per-side settings only affect the `go` command used for that
side's turn.

## Legal Moves

`xiangqi.py` generates legal moves server-side. It covers:

- Rook, cannon, knight, bishop, advisor, king, pawn movement.
- Blocking rules.
- Palace and river restrictions.
- Flying general.
- Self-check filtering.

Still pending:

- Repetition/perpetual check/perpetual chase adjudication.
- More complete Chinese notation for ambiguous same-file pieces.

## Mobile Direction

The current frontend is a PWA-ready responsive app. A native shell should keep
the same API contract and move model:

- Board state: UCI move list.
- Display notation: backend returns Chinese and UCI.
- AI search: frontend sends explicit UCI search limits.
