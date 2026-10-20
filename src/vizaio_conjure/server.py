"""Minimal static server used by the first Conjure smoke test."""

from __future__ import annotations

import functools
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


def serve_directory(path: str | Path, *, bind: str = "0.0.0.0", port: int = 8765) -> None:
    """Serve ``path`` until interrupted."""

    directory = Path(path).expanduser().resolve()
    if not directory.is_dir():
        raise ValueError(f"directory does not exist: {directory}")
    handler = functools.partial(SimpleHTTPRequestHandler, directory=str(directory))
    server = ThreadingHTTPServer((bind, port), handler)
    print(f"Serving {directory} at http://{bind}:{port}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
