# Mobile Migration Notes

The web app is structured to support a mobile migration without rewriting the
backend.

## Recommended Path

1. Keep `web/backend` as the local/network API during development.
2. Keep the current responsive `web/frontend` as the shared UI baseline.
3. First ship as a PWA:
   - `manifest.webmanifest`
   - `service-worker.js`
   - responsive board and panels
4. If native packaging is needed later, wrap the frontend with Capacitor and
   point it at the same API contract.

## API Contract To Preserve

- `GET /api/state`
- `POST /api/position`
- `POST /api/analyze`

The frontend already models moves as UCI strings and receives both Chinese and
UCI notation from the backend. A mobile client should keep that model.

## Mobile UX Risks

- The board must remain the first screen.
- AI analysis should stay below the board on narrow screens.
- Long engine searches need visible thinking state and cancellation later.
- Full Xiangqi move legality should be centralized before a native release.

## Current PWA Support

- Installable manifest is present.
- Static shell is cached by the service worker.
- API calls are not cached, so analysis remains live.
