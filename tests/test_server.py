from pathlib import Path

import pytest

from vizaio_conjure.server import serve_directory


def test_missing_directory_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="directory does not exist"):
        serve_directory(tmp_path / "missing")
