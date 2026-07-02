# Xiangqi AI Web App

This document covers the runnable web frontend/backend app.

## Run

Start the real Pikafish-backed server:

```bash
python3 -m web.backend.server
```

Shortcut:

```bash
make run
```

Open:

```text
http://127.0.0.1:8080/
```

For fast UI/testing without launching Pikafish, use fake engine mode:

```bash
XIANGQI_FAKE_ENGINE=1 python3 -m web.backend.server
```

Shortcut:

```bash
make run-fake
```

## API

### `GET /api/state`

Returns the initial board, side to move, and asset paths.

### `GET /api/health`

Returns a lightweight health payload with engine mode:

```json
{
  "ok": true,
  "engine": "pikafish",
  "version": "0.1"
}
```

### `POST /api/position`

Request:

```json
{
  "moves": ["h2e2", "h9g7"]
}
```

Returns the current pieces, side to move, Chinese move text, and UCI move rows.

### `POST /api/analyze`

Request:

```json
{
  "moves": ["h2e2"],
  "limit": { "mode": "movetime", "value": 1000 },
  "multipv": 5
}
```

Search limits map directly to Pikafish UCI commands:

- `{ "mode": "movetime", "value": 1000 }` -> `go movetime 1000`
- `{ "mode": "depth", "value": 16 }` -> `go depth 16`

Response includes:

- `bestmove`: UCI best move
- `bestmove_cn`: Chinese notation for the best move
- `lines`: MultiPV lines with score, WDL, UCI PV, and Chinese PV

## Frontend Behavior

- Board pieces are rendered from `/api/position`.
- Human moves are sent as UCI coordinates.
- AI analysis refreshes after every move and is independent from move execution.
- `本步 AI` uses the current analysis best move to play one move for the current side.
- `自动代走` waits the configured `代走间隔`, then checks whether the current side is AI before playing the current analysis best move. When two AI sides play continuously, this is the minimum delay between two delegated moves.
- AI search controls show the exact `go ...` command used by the backend.
- AI analysis supports full-panel notation switching:
  - `中文`: user-facing Chinese move notation.
  - `UCI`: engine coordinates.
- The frontend includes a PWA manifest and service worker for mobile migration
  preparation.

## Tests

Run:

```bash
python3 -m unittest discover -s tests -v
```

Shortcut:

```bash
make test
```

The tests cover:

- UCI move application and side-to-move counting.
- Chinese notation generation.
- Pikafish info-line parsing.
- Search limit clamping.
- API smoke tests in fake engine mode.

## Current Limitations

- Legal move generation covers piece movement, blocking, palace/river limits,
  flying general, and self-check filtering. Tournament rules such as repetition
  and perpetual chase/check are not implemented yet.
- Chinese notation handles normal single-piece notation. Ambiguous same-file
  piece notation can be refined later.
- Mobile migration should reuse the backend API and the same board coordinate
  model.
