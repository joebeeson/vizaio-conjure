from pathlib import Path
from threading import Thread
from urllib.request import urlopen

import pytest

from vizaio_conjure.server import create_server, serve_directory


def test_missing_directory_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="directory does not exist"):
        serve_directory(tmp_path / "missing")


def test_smoke_page_is_served(tmp_path: Path) -> None:
    (tmp_path / "index.html").write_text("<h1>CONJURE OK</h1>", encoding="utf-8")
    server = create_server(tmp_path, bind="127.0.0.1", port=0)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        port = server.server_address[1]
        with urlopen(f"http://127.0.0.1:{port}/", timeout=2) as response:
            body = response.read().decode("utf-8")
        assert response.status == 200
        assert "CONJURE OK" in body
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
