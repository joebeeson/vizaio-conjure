# vizaio-conjure

[![CI](https://github.com/joebeeson/vizaio-conjure/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/joebeeson/vizaio-conjure/actions/workflows/ci.yml)
[![Prek](https://github.com/joebeeson/vizaio-conjure/actions/workflows/prek.yml/badge.svg?branch=main)](https://github.com/joebeeson/vizaio-conjure/actions/workflows/prek.yml)
[![Latest release](https://img.shields.io/github/v/release/joebeeson/vizaio-conjure?sort=semver)](https://github.com/joebeeson/vizaio-conjure/releases)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Developer-friendly VIZIO Conjure URL launching built on the upstream
[`vizaio`](https://github.com/raman325/vizaio) SmartCast client.

## Milestone 1

The first milestone serves a LAN-reachable HTML page and launches it through
the established Conjure launcher configuration: app `17`, namespace `4`.

```powershell
uv sync --extra dev
just serve
```

From another terminal, set a paired token without putting it in the command
line or repository:

```powershell
$env:VIZAIO_AUTH = "..."
uv run vizaio-conjure launch http://HOST:8765/ --host TV_HOST:7345
```

## Pairing and saved devices

The pairing PIN is used only for the short-lived TV pairing challenge. It is
never written to disk. The resulting auth token is stored through Python's
[`keyring`](https://pypi.org/project/keyring/) library, using the operating
system credential store, while the local profile file contains only the TV
host and pairing identity.

Pair a TV interactively:

```powershell
uv run vizaio-conjure discover
uv run vizaio-conjure pair TV_HOST:7345 --name living-room
uv run vizaio-conjure devices list
uv run vizaio-conjure devices test living-room
uv run vizaio-conjure launch http://HOST:8765/ --device living-room
```

Discovery uses the upstream SSDP and optional Zeroconf adapters. It may not
cross a routed network boundary, so explicit hostnames and IP addresses remain
supported. Install the optional discovery dependency for Zeroconf results:

```powershell
uv tool install "vizaio-conjure[discovery]"
```

Use `devices remove NAME` to delete both the profile metadata and its keyring
credential. Pairing uses a stable, installation-specific device identity so it
does not reuse a generic identity belonging to another integration.

For a no-device validation:

```powershell
uv run vizaio-conjure launch http://example.test/ --dry-run
```

## Namespace ergonomics

The known Conjure namespace is available as `VizioNamespace.CONJURE`, while
raw integer namespaces remain supported for future firmware or undocumented
applications:

```python
from vizaio_conjure import ConjureTarget, VizioNamespace

ConjureTarget("http://host:8765/", name_space=VizioNamespace.CONJURE)
ConjureTarget("http://host:8765/", name_space="CONJURE")
ConjureTarget("http://host:8765/", name_space=9)
```

This project deliberately does not implement the internal app-3001 route or
privileged Conjure surfaces.

## Development and release

Run `uv sync --extra dev` followed by `just check`. The CI workflow tests
Python 3.12, 3.13, and 3.14, publishes coverage and JUnit artifacts, runs
Ruff and Pyrefly as separate quality checks, and builds distributions before a
merge is considered ready. Tagged releases create GitHub release artifacts;
PyPI publication remains disabled until Trusted Publishing is configured.

See [docs/releasing.md](docs/releasing.md) for the release checklist.
