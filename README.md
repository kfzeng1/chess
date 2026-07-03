# Chinese Chess AI

This repository contains a runnable Xiangqi AI web app, an offline personal-use
Android APK, board/piece assets, and local Pikafish engine builds.

## Structure

```text
assets/
  board.png              # latest board image
  pieces/*.png           # latest red/black piece images
  ui-preview.png         # latest desktop web app screenshot
android/
  app/                   # native offline Android APK
docs/
  ARCHITECTURE.md        # module and data-flow notes
  MOBILE_MIGRATION.md    # Android APK and mobile notes
  WEB_APP.md             # web app API and run notes
engines/
  pikafish-avxvnni       # Pikafish Linux x86-64 AVX-VNNI binary
  pikafish.nnue          # matching NNUE network
tests/
  frontend_mismatch.spec.js
  test_backend.py
playwright.config.js      # starts the fake-engine server for frontend tests
tools/asset-generation/
  render_xiangqi_board.py
  render_xiangqi_pieces.py
web/
  backend/               # Python stdlib API server and Pikafish adapter
  frontend/              # HTML/CSS/JS web app
Makefile                 # common run/test/screenshot commands
```

## Offline Android APK

The native APK lives under `android/`. It is intended for personal offline use:
no browser, no network, and no Python backend are required on the phone.

Build:

```bash
make apk-debug
```

Output:

```text
android/app/build/outputs/apk/debug/app-debug.apk
```

The APK currently includes:

- `lib/arm64-v8a/libpikafish.so`: Pikafish dev-20260628-553282ed rebuilt with
  Android NDK for arm64.
- `assets/pikafish.nnue`: matching NNUE network.
- Native Java UI with board, pieces, red/black AI toggles, automatic delegated
  moves, manual `本步 AI`, WDL/score/PV display, and Chinese/UCI notation
  switching.

The debug APK is unsigned for store distribution but installable for personal
testing after enabling Android debug/unknown-source installation.

## Web App

The runnable web app lives under `web/`.

```bash
python3 -m web.backend.server
```

or:

```bash
make run
```

For testing from a phone on the same LAN:

```bash
make run-lan
```

Then open `http://<your-computer-ip>:8080/` on the phone.

Open:

```text
http://127.0.0.1:8080/
```

Fast test mode without launching Pikafish:

```bash
XIANGQI_FAKE_ENGINE=1 python3 -m web.backend.server
```

or:

```bash
make run-fake
```

LAN fake-engine mode:

```bash
make run-fake-lan
```

Refresh the desktop screenshot:

```bash
npx playwright screenshot --viewport-size=1440,960 \
  http://127.0.0.1:8080/ \
  assets/ui-preview.png
```

Quick mobile viewport check:

```bash
make screenshot-mobile
```

This writes mobile screenshots for 390px portrait, 360px portrait, and landscape
phone viewports to `/tmp/xiangqi-mobile-*.png`.

Run tests:

```bash
make test
npm run test:frontend
make apk-debug
```

`npm run test:frontend` starts a fake-engine web server automatically through
Playwright when port 8080 is not already running.

Remove generated local files:

```bash
make clean
```

More details: [docs/WEB_APP.md](docs/WEB_APP.md).
Architecture notes: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).
Mobile migration notes: [docs/MOBILE_MIGRATION.md](docs/MOBILE_MIGRATION.md).

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
- Desktop build arch: `x86-64-avxvnni`
- Android build arch: `armv8` / `arm64-v8a`
- NNUE SHA-256: `a2f41d4d0b9f59c5b5ecb3ca129fe24e3a722ea2f00ee252ae14d5dc08899f6a`

Run:

```bash
./engines/pikafish-avxvnni
```

The engine uses UCI. Keep `pikafish.nnue` next to the binary unless you set the
`EvalFile` UCI option to another path.

Android engine rebuild command used locally:

```bash
PATH=/home/zkf/Android/Sdk/ndk/29.0.13599879/toolchains/llvm/prebuilt/linux-x86_64/bin:$PATH \
  make -C /tmp/Pikafish/src -j2 build ARCH=armv8 COMP=ndk
```
