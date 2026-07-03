# Architecture

## Modules

```text
web/backend/server.py   HTTP API and static file server
web/backend/engine.py   Pikafish UCI adapter and fake test engine
web/backend/xiangqi.py  Board state, notation, legal move generation
web/frontend/app.js     Browser state, board interaction, AI workflow
web/frontend/style.css  Responsive app layout
android/app/            Native offline Android APK
```

## Data Flow

1. Browser loads `/`.
2. Frontend calls `/api/position` with the current UCI move list.
3. Backend rebuilds board state from `startpos + moves`.
4. Backend returns pieces, side to move, legal moves, game-over state, and move
   rows in Chinese/UCI. It also returns `positionId`, a stable identity for the
   current move list.
5. Frontend renders board pieces and legal target hints.
6. Frontend calls `/api/analyze` with `moves`, `multipv`, and search limit.
7. Backend sends `position startpos moves ...` and `go ...` to Pikafish.
8. Backend parses `bestmove`, `score`, `wdl`, and `pv`, then returns both UCI
   and Chinese notation. The frontend discards analysis whose `positionId` no
   longer matches the current position.

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

The primary mobile target is now a native offline APK under `android/`.
The responsive web app remains useful for desktop and browser-based preview.

The Android APK keeps the same core model as the web app:

- Board state: UCI move list.
- Engine protocol: UCI `position startpos moves ...` and `go ...`.
- Display notation: Chinese and UCI.
- Delegated move safety: only play a bestmove after the current position and
  local legal-move list still match.

The APK is self-contained:

- `android/app/src/main/jniLibs/arm64-v8a/libpikafish.so` is Pikafish
  dev-20260628 rebuilt for Android arm64.
- `android/app/src/main/assets/pikafish.nnue` is copied to app-private storage
  and passed to Pikafish as `EvalFile`.
- `MainActivity.java` owns the native board UI, engine process, AI toggles,
  auto delegated moves, WDL/score/PV parsing, and Chinese/UCI switching.
