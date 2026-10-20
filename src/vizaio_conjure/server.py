"""Minimal static server used by the first Conjure smoke test."""

from __future__ import annotations

import functools
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


def create_server(
    path: str | Path, *, bind: str = "0.0.0.0", port: int = 8765
) -> ThreadingHTTPServer:
    """Build a static server without starting its event loop."""

    directory = Path(path).expanduser().resolve()
    if not directory.is_dir():
        raise ValueError(f"directory does not exist: {directory}")
    handler = functools.partial(SimpleHTTPRequestHandler, directory=str(directory))
    return ThreadingHTTPServer((bind, port), handler)


def serve_directory(path: str | Path, *, bind: str = "0.0.0.0", port: int = 8765) -> None:
    """Serve ``path`` until interrupted."""

    server = create_server(path, bind=bind, port=port)
    directory = Path(path).expanduser().resolve()
    actual_port = server.server_address[1]
    print(f"Serving {directory} at http://{bind}:{actual_port}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
