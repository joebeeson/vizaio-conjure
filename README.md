# vizaio-conjure

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
