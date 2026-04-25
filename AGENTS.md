# Agent Instructions

## Project

Python library and CLI for WaterFurnace / GeoStar geothermal heat pump systems
via the Symphony WebSocket API. Published on PyPI as `waterfurnace`.

## Structure

```
waterfurnace/
  waterfurnace.py   # core library: WaterFurnace, GeoStar, WFEnergyReading classes
  cli.py            # Click CLI entry point
  __init__.py       # exposes public API, version from package metadata
tests/
  conftest.py       # shared fixtures, mocked websocket and HTTP
  test_symphony.py  # core library tests
  test_write.py     # write command tests (set_mode, set_cooling_setpoint, etc.)
  test_waterfurnace.py  # CLI tests
  test_timeout.py   # timeout/reconnect behavior
pyproject.toml      # version, dependencies, build config
tox.ini             # test environments (py310–py314, lint)
Makefile            # convenience targets
```

## Rules

Before every commit, run tests and linting and confirm both pass:

```bash
pytest
black --check --target-version py313 waterfurnace tests
```

## Install for development

```bash
pip install -e ".[dev]"
```

## Run tests

```bash
pytest                  # single Python version
tox                     # all supported versions + lint (py310–py314)
```

## Lint / formatting

```bash
black --check --target-version py313 waterfurnace tests   # check
black --target-version py313 waterfurnace tests           # fix
```

## Release

Releases are triggered by pushing to `main` with an updated version in
`pyproject.toml`. GitHub Actions runs tests, builds, publishes to PyPI, and
creates a GitHub release.

The interactive release helper handles version bump, changelog prompt, commit,
and push:

```bash
make release
```

Manual steps if needed:
1. Update `version` in `pyproject.toml`
2. Add a `## X.Y.Z (YYYY-MM-DD)` section to `CHANGELOG.md`
3. Commit both files and push to `main`

Version follows semver. The version in `pyproject.toml` is the single source
of truth — `__init__.py` reads it from installed package metadata automatically.
