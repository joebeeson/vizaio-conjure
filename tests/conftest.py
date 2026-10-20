from pathlib import Path

import pytest


@pytest.fixture
def smoke_page() -> Path:
    """Return the checked-in smoke page used by server and browser tests."""

    return Path(__file__).parents[1] / "examples" / "smoke" / "index.html"
