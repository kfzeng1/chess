# Web to Android Parity Notes

This document treats the web app as the reference implementation for the
offline Android APK.

## Web UI Reference

Top bar:
- Brand mark and title.
- Mobile drawer buttons: `配置` opens the left control panel, `分析` opens the
  right analysis panel.
- Engine pill shows ready/thinking/error state.

Board area:
- Current side text, move count, and thinking state.
- WDL row with red win, draw, and black win. Web converts Pikafish WDL values
  from 0-1000 into percentages.
- Board with large transparent square targets, selected marker, legal-move
  hints, and last-move source/target markers.
- Mobile quick actions: new game, undo one ply, flip board.
- Mobile delegated actions: automatic delegated move toggle and manual
  `本步 AI`.
- Four status boxes: current side, move count, red clock, black clock.

Left control panel:
- Red/black player mode segmented controls: human or AI.
- Delegated-move minimum delay, 0-5s in 0.5s steps.
- Red/black AI search cards. Each side independently supports time mode
  (`go movetime <ms>`) and depth mode (`go depth <plies>`).

Right analysis panel:
- Notation mode switch: Chinese or UCI.
- Main line summary with depth and nps.
- Up to 5 recommendation cards, each with rank, best move, PV, score, and WDL.
- Engine note explaining bestmove, pv, score, and WDL.
- Audit log with mismatch count.
- Move history in the selected notation.

## Web API Reference

`GET /api/state` returns the initial board, legal moves, side to move, and
position id.

`POST /api/position` accepts `moves` and returns:
- `pieces`
- `sideToMove`
- `positionId`
- `legalMoves`
- `gameOver`
- `inCheck`
- Chinese and UCI move rows

`POST /api/analyze` accepts:
- `moves`
- `positionId`
- `limit`: `{ "mode": "movetime" | "depth", "value": number }`
- `multipv`: usually `5`

It returns:
- `sideToMove`
- `positionId`
- `limit.command`
- `bestmove`
- `bestmove_cn`
- `lines[]` with `multipv`, `bestmove`, `pv`, `pv_cn`, `score`, `wdl`,
  `depth`, `nodes`, `nps`, and `timeMs`.

`POST /api/log` records local audit events. The APK does not need the HTTP
endpoint, but it should keep equivalent in-app audit state.

## Behavioral Rules

- Every new position is analyzed independently; analysis is not cached.
- A normal move clears the current analysis, syncs the new position, analyzes
  it, then schedules auto delegation if appropriate.
- `本步 AI` is a delegated move for the current side. If analysis is in flight,
  it waits until that analysis completes before acting.
- `自动代走` only moves after analysis is complete and the configured minimum
  delay has elapsed. At the end of the delay it rechecks generation, side to
  move, auto mode, and whether the side is still AI.
- Control changes, AI mode changes, search limit changes, and manual AI are
  protected actions: if analysis is running, they apply after the analysis
  completes.
- New game resets immediately.
- Undo removes one ply. Multiple undo taps debounce analysis; the final undo
  position is analyzed after 0.5s.
- Flip only changes board orientation. It must not change game state.
- A stale analysis result is discarded. A positionId or bestmove mismatch turns
  auto delegation off, restores the checked position when needed, records an
  audit entry, and shows an alert.

## APK Parity Checklist

- Native UI keeps the same mobile layout and drawer model as the web mobile UI.
- Red/black AI strength controls match web defaults and ranges.
- WDL values are displayed as percentages.
- Clocks tick for the side to move and reset on new game.
- Move count/status box uses the same move-count value as web.
- Analysis panel shows depth, nps, nodes, recommendation WDL, audit, and
  selected-notation history.
- Protected actions and undo debounce follow web behavior.
- Engine parser is tested with the Linux Pikafish binary via
  `make test-android-engine`.
