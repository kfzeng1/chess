# Mobile / PWA Notes

The current mobile target is a responsive PWA-style web app. It uses the same
Python backend and Pikafish API as the desktop web UI.

## Current Mobile Web State

- The board is first in the narrow-screen layout.
- Controls move below the board and use larger touch targets.
- AI analysis and move history stay below controls.
- The development audit panel is hidden on narrow screens.
- `manifest.webmanifest` and `service-worker.js` are present.
- A Playwright mobile viewport test covers the 390px layout, horizontal
  overflow, board size, and key control visibility.

## Recommended Path

1. Keep `web/backend` as the local/network API during development.
2. Keep the current responsive `web/frontend` as the shared UI baseline.
3. Ship the responsive web app as the first mobile version.
4. If native packaging is needed later, wrap the frontend with Capacitor and
   point it at the same API contract.

## API Contract To Preserve

- `GET /api/state`
- `POST /api/position`
- `POST /api/analyze`

The frontend already models moves as UCI strings and receives both Chinese and
UCI notation from the backend. A mobile client should keep that model.

## Mobile UX Risks

- The board must remain the first screen and must not shrink below usable touch
  size.
- AI analysis should stay below the board and controls on narrow screens.
- Long engine searches need visible thinking state and cancellation later.
- Full Xiangqi move legality should be centralized before a native release.

## Current PWA Support

- Installable manifest is present.
- Static shell is cached by the service worker.
- API calls are not cached, so analysis remains live.

## Verify Mobile Layout

```bash
npm run test:frontend
```

The frontend tests automatically start the app in fake-engine mode if needed.
