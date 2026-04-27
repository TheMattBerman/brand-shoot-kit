# Examples

Each folder contains a `config.json` input for `scripts/create-shoot-packet.py`.
`scout-samples/` contains offline scout fixtures for deterministic smoke tests.
`golden-runs/` contains deterministic dry-run bundle outputs built by `scripts/build-golden-runs.sh`.

Generate a sample packet:

```bash
./scripts/create-shoot-packet.py --config examples/skincare-serum/config.json --out examples/skincare-serum/packet
```

Generate from a scout fixture:

```bash
./scripts/run-brand-shoot.py --scout-json examples/scout-samples/skincare-serum-scout.json --out output/example-from-scout
```
