from pathlib import Path


def test_smoke_page_includes_remote_event_monitor() -> None:
    page = Path(__file__).parents[1] / "examples" / "smoke" / "index.html"
    body = page.read_text(encoding="utf-8")

    assert 'id="remote-status"' in body
    assert 'id="remote-log"' in body
    assert '"keydown"' in body
    assert '"keyup"' in body
    assert '"keypress"' in body
    assert "preventDefault" not in body
