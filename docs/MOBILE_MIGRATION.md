# Offline Android APK Notes

The primary mobile target is a personal-use offline Android APK. It does not
depend on a browser, network access, or the Python web backend once installed.

## Current APK State

- Native Java app under `android/app`, split into a UI layer and a local APK
  backend layer.
- `MainActivity` owns screen layout and user interaction.
- `backend/ApkBackend` owns local analysis requests and engine lifecycle.
- `engine/` owns Pikafish UCI startup, MultiPV parsing, score/WDL normalization,
  and analysis result models.
- `core/` owns Xiangqi board state, legal moves, and Chinese notation.
- `ui/BoardView` owns board rendering and touch hit-testing.
- Board and piece assets are bundled from the latest PNG assets.
- Pikafish dev-20260628-553282ed is rebuilt for Android arm64 and bundled as
  `lib/arm64-v8a/libpikafish.so`.
- `pikafish.nnue` is bundled as an asset, copied to app-private storage on
  first use, and passed to Pikafish via `EvalFile`.
- The app starts a local UCI engine process with `ProcessBuilder`.
- AI analysis parses `bestmove`, `score`, `wdl`, `depth`, `nodes`, `nps`, `time`,
  and up to 5 MultiPV lines.
- The UI supports red/black AI toggles, automatic delegated moves, manual
  `本步 AI`, delegated-move delay, WDL/score/PV display, and Chinese/UCI
  notation switching.
- Red and black AI strength controls match the web frontend. Each side can use
  time mode (`go movetime <milliseconds>`) or depth mode (`go depth <plies>`),
  with the command shown directly in the configuration drawer.
- Web-parity behavior includes live red/black clocks, WDL percentage display,
  protected control changes while analysis is running, 0.5s undo analysis
  debounce, mismatch alerts with rollback, in-app audit entries, and
  recommendation cards with score and WDL.

## Build

```bash
make apk-debug
```

Output:

```text
android/app/build/outputs/apk/debug/app-debug.apk
```

The debug APK is installable for personal testing. It is not a release-signed
store build.

## Engine Rebuild

The bundled Android engine was built from Pikafish commit:

```text
553282edc90181f1f420a210d55eb67f9f14c9e9
```

Build command used locally:

```bash
PATH=/home/zkf/Android/Sdk/ndk/29.0.13599879/toolchains/llvm/prebuilt/linux-x86_64/bin:$PATH \
  make -C /tmp/Pikafish/src -j2 build ARCH=armv8 COMP=ndk
```

The resulting ARM64 executable is stored in:

```text
android/app/src/main/jniLibs/arm64-v8a/libpikafish.so
```

## Web Parity

The APK keeps the same core behavior as the web client:

- Moves are represented as UCI strings.
- Each position can be analyzed independently.
- Analysis follows the web backend model: result lines contain `multipv`,
  `bestmove`, `score`, `wdl`, `pv`, and generated Chinese PV text.
- Score and WDL are normalized to red-side perspective, matching the web
  backend.
- Red/black search limits use the same defaults and ranges as the web UI:
  red starts at `go movetime 1000`, black starts at `go depth 16`, time ranges
  from 0.1s to 30s, and depth ranges from 1 to 30.
- `本步 AI` plays the current best move for the side to move.
- `自动代走` only plays after analysis is ready and the configured minimum delay
  has elapsed.
- During the delay, changing red/black AI settings or disabling automatic
  delegated moves affects the next decision.
- Chinese and UCI notation can be switched in the analysis panel.
- The analysis panel mirrors the web information model: mainline depth/nps/nodes,
  up to 5 MultiPV recommendations, score, WDL, audit count, and move history.

## Engine Parser Test

The emulator available locally is `x86_64`, so it cannot execute the bundled
Android `arm64-v8a/libpikafish.so`. To test the shared Android Java engine
parser without an arm64 phone, run the Linux Pikafish binary through a CLI smoke
test:

```bash
make test-android-engine
```

This compiles the APK `core/` and `engine/` Java packages with `javac`, starts
`engines/pikafish-avxvnni`, and verifies both `go depth ...` and
`go movetime ...` requests, MultiPV parsing, bestmove parsing, score text, and
WDL shape.

## Remaining Gaps

- APK legal-move generation covers normal movement, blocking, flying general,
  and self-check filtering, but tournament repetition/perpetual-check rules are
  still not implemented.
- Release signing, app icon, and device-install automation can be added later.

## Web Preview

The responsive web frontend remains useful for desktop and browser preview:

```bash
make run-fake-lan
```

Then open `http://<computer-ip>:8080/` on a phone connected to the same LAN.
This is no longer the primary mobile delivery target.
