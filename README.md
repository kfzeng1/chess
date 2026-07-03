# Chinese Chess AI Android

This branch contains the offline personal-use Android APK for the Xiangqi AI
app, bundled board/piece assets, the Android Pikafish engine, and a Linux
Pikafish smoke test for the shared Java engine parser.

## Structure

```text
android/
  app/                   # native offline Android APK
assets/
  board.png              # source board asset
  pieces/*.png           # source red/black piece assets
docs/
  ARCHITECTURE.md        # shared architecture notes
  MOBILE_MIGRATION.md    # Android APK and mobile notes
  WEB_TO_ANDROID_PARITY.md # web UI/API parity checklist for APK behavior
engines/
  pikafish-avxvnni       # Linux test binary for parser smoke tests
  pikafish.nnue          # matching NNUE network
tools/
  android-engine-test/   # Java CLI smoke test using the Linux engine
  asset-generation/      # board and piece render scripts
Makefile                 # Android build and test commands
```

## Build APK

```bash
make apk-debug
```

Output:

```text
android/app/build/outputs/apk/debug/app-debug.apk
```

The APK is offline: no browser, network, Python backend, or web server is
required once installed.

## Test

Build the APK:

```bash
make apk-debug
```

Run the Android Java engine parser smoke test with the Linux Pikafish binary:

```bash
make test-android-engine
```

The local emulator is usually `x86_64`, while the packaged APK engine is
`arm64-v8a/libpikafish.so`. Use the emulator for layout checks and an arm64
phone for full APK engine runtime checks.

## APK Features

- Native Java UI with board, pieces, side drawers, and mobile-first layout.
- Local Pikafish dev-20260628-553282ed engine bundled for Android arm64.
- Red/black AI toggles, manual `本步 AI`, and automatic delegated moves.
- Red/black independent AI strength controls: `go movetime <ms>` and
  `go depth <plies>`.
- WDL percentage display, red/black clocks, MultiPV recommendations, Chinese/UCI
  notation switching, audit entries, mismatch alerts, and rollback protection.

More details:

- [docs/MOBILE_MIGRATION.md](docs/MOBILE_MIGRATION.md)
- [docs/WEB_TO_ANDROID_PARITY.md](docs/WEB_TO_ANDROID_PARITY.md)
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

## Assets

Regenerate source assets:

```bash
python3 tools/asset-generation/render_xiangqi_board.py
python3 tools/asset-generation/render_xiangqi_pieces.py
```

Android runtime assets are copied into `android/app/src/main/res/drawable-nodpi/`
and `android/app/src/main/assets/`.
