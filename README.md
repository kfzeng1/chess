# Chinese Chess Engine

This repository contains a local Linux x86-64 AVX-VNNI build of Pikafish and
its matching NNUE network.

## Files

- `engines/pikafish-avxvnni`: Pikafish engine binary
- `engines/pikafish.nnue`: NNUE evaluation network

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
